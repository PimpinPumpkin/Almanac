-- Final tables in the published shape. See SPEC.md for the columns.

create or replace macro license_of(source) as
  case
    when source = 'overture' then 'CDLA-Permissive-2.0'
    when source in ('fsq', 'fsq_closed') then 'Apache-2.0'
    when source in ('atp', 'wikidata_p576') then 'CC0-1.0'
    when source like 'osm%' then 'ODbL-1.0'
    when source like 'fdic%' or source like 'snap%' then 'US-public-domain'
  end;

create or replace macro published(place, member, status) as table (
  with m as (
    select place_id,
           list(struct_pack(source, id := source_id) order by source, source_id) as sources,
           list(distinct license_of(source)) as member_licenses
    from query_table(member) group by place_id
  )
  select p.id, p.name, p.category, p.brand, p.brand_wikidata,
         p.address, p.city, p.region, p.postcode, p.phone, p.website,
         coalesce(s.status, 'unknown') as status, s.status_date, s.status_source,
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
);

create or replace table out_core as
  select * from published('core_place', 'core_member', 'core_status');

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
  select * from published('full_place', 'full_member', 'full_status');
