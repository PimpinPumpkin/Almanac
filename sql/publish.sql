-- Final tables in the published shape. See SPEC.md for the columns.

create or replace macro license_of(source) as
  case
    when source = 'overture' then 'CDLA-Permissive-2.0'
    when source in ('fsq', 'fsq_closed') then 'Apache-2.0'
    when source in ('atp', 'wikidata_p576') then 'CC0-1.0'
    when source like 'osm%' then 'ODbL-1.0'
    when source like 'abca_dc%' or source = 'bbl_dc' then 'CC-BY-4.0'
    when source in ('abc_ca', 'tabc_tx', 'dbpr_fl_food', 'abt_fl', 'atc_mo', 'olcc_or', 'tdlr_tx',
                    'bot_sac', 'emd_sac', 'lou_food', 'abc_ky_jefferson', 'li_phl') then 'none-stated'
    when source in ('sla_ny', 'dmv_ny', 'dos_ny_salons', 'agm_ny') then 'OPEN-NY-terms'
    when source in ('dohmh_nyc', 'dcwp_nyc') then 'NYC-Open-Data-terms'
    when source like 'cdph_chicago%' or source like 'bacp_chicago%' then 'Chicago-Data-Portal-terms'
    when source = 'sirene' then 'etalab-2.0'
    -- everything else is a US federal register
    else 'US-public-domain'
  end;

-- open_score: a rough chance, 0 to 1, that the place is open on the build date.
-- It is a rule of thumb, not a fitted model. The parts:
--   closed                        0.10  (a closing record is wrong about 1 time in 8
--                                        where a second source can check it)
--   newest evidence is open       0.97 * 0.90 ^ years since that date
--                                        (about 1 business in 10 closes each year)
--   same, but it overrode an
--   older closing record          0.80 * 0.90 ^ years
--   no evidence                   0.75, or 0.30 when Overture says permanently_closed
--                                 or when missing_license is true, or OpenPOIs'
--                                 confidence when that is 0.80 or more
-- A stale open record never scores below the no-evidence value.
create or replace macro open_score(status, status_date, conflict, overture_status, missing_license, conf, build_date) as
  round(case
    when status = 'closed' then 0.10
    when status_date is not null then greatest(
      case when conflict then 0.80 else 0.97 end * pow(0.90, greatest(build_date - status_date, 0) / 365.25),
      case when conflict then 0.50 else 0.75 end)
    when overture_status = 'permanently_closed' or missing_license then 0.30
    when conf >= 0.80 then conf
    else 0.75
  end, 2);

-- States whose active alcohol license list is complete and carries positions,
-- so that finding no license for a bar means something. See SPEC.md section 7.
create or replace table license_list as
  select * from (values ('DC', 'abca_dc_active'), ('NY', 'sla_ny')) t(region, source);

create or replace macro published(place, member, status, conf) as table (
  with m as (
    select place_id,
           list(struct_pack(source, id := source_id) order by source, source_id) as sources,
           list(distinct license_of(source)) as member_licenses
    from query_table(member) group by place_id
  )
  select p.id, p.name, p.category,
         coalesce(og.category_group, group_of(p.category)) as category_group,
         p.brand, p.brand_wikidata,
         p.address, p.city, p.region, p.postcode, p.phone, p.website,
         coalesce(s.status, 'unknown') as status, s.status_date, s.status_source,
         open_score(coalesce(s.status, 'unknown'), s.status_date, coalesce(s.conflict, false),
                    p.overture_status, coalesce(ml.missing, false), cf.conf, (select build_date from params)) as open_score,
         round(cf.conf, 2) as openpois_conf,
         ml.missing as missing_license,
         p.overture_status,
         m.sources,
         list_sort(list_distinct(
           m.member_licenses
           || case when p.has_fsq then ['Apache-2.0'] else [] end
           || coalesce(list_transform(s.evidence, lambda e: license_of(e.source)), []))) as licenses,
         coalesce(s.evidence, []) as evidence,
         p.lat, p.lng,
         st_point(p.lng, p.lat) as geometry
  from query_table(place) p
  join m on m.place_id = p.id
  left join query_table(status) s on s.place_id = p.id
  left join query_table(conf) cf on cf.place_id = p.id
  left join ovt_all og on og.id = p.id
  -- true: a bar in a state with a license list, and no active license matched it.
  -- null: the question does not apply to this place.
  left join (
    select p2.id, not exists (
             select 1 from query_table(status) s2, unnest(s2.evidence) as u(e)
             where s2.place_id = p2.id and u.e.source = l.source) as missing
    from query_table(place) p2 join license_list l on l.region = p2.region
    where needs_alcohol_license(p2.category)
  ) ml on ml.id = p.id
);

create or replace table out_core as
  select * from published('core_place', 'core_member', 'core_status', 'core_conf');

-- The full layer: core places with OSM folded in, then the places only OSM has.
create or replace table full_place as
  select c.* replace (
           coalesce(c.phone, f.phone) as phone,
           coalesce(c.website, f.website) as website,
           coalesce(c.brand, f.brand) as brand,
           coalesce(c.brand_wikidata, f.brand_wikidata) as brand_wikidata,
           coalesce(c.address, f.address) as address)
  from core_place c left join osm_fill f on f.place_id = c.id
  union all
  select * from osm_only;

create or replace table full_member as
  select * from core_member union all select * from osm_member;

create or replace table out_full as
  select * from published('full_place', 'full_member', 'full_status', 'full_conf');
