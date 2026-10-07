-- Core layer: Overture + AllThePlaces + evidence that does not come from OSM.
-- Nothing in this file may read an OSM-derived table; that is what keeps the
-- core layer free of ODbL terms. Inputs (made by build.sh): ovt, atp,
-- fsq_closed, register (evidence rows inside the region), params.

create or replace table ovt_all as
  select 'ovt:' || id as id, * exclude (id), norm_name(name) as nn, house_number(address) as hn
  from ovt;

-- Duplicate listings inside Overture. Only the strictest case merges: same
-- house number, within 250 m, identical normalized name. Looser pairs were
-- read and are mostly a part and its whole (a gift shop and its hospital),
-- see SPEC.md section 9. Groups are closed over chains of pairs by passing
-- the smallest id along the pairs three times; the smallest id is kept.
create or replace table ovt_pair as
  select a_id, b_id from match_pairs('ovt_all', 'ovt_all')
  where a_id <> b_id and rule = 'number' and sim = 1.0;

create or replace table ovt_canon as
  with l0 as (select id, id as c from ovt_all),
  l1 as (select l.id, least(l.c, coalesce(min(n.c), l.c)) as c
         from l0 l left join ovt_pair p on p.a_id = l.id left join l0 n on n.id = p.b_id group by l.id, l.c),
  l2 as (select l.id, least(l.c, coalesce(min(n.c), l.c)) as c
         from l1 l left join ovt_pair p on p.a_id = l.id left join l1 n on n.id = p.b_id group by l.id, l.c),
  l3 as (select l.id, least(l.c, coalesce(min(n.c), l.c)) as c
         from l2 l left join ovt_pair p on p.a_id = l.id left join l2 n on n.id = p.b_id group by l.id, l.c)
  select id, c as place_id from l3;

-- One row per Overture place: the kept listing, gaps filled from its duplicates.
create or replace table ovt_n as
  with fill as (
    select k.place_id,
           any_value(o.category) as category, any_value(o.brand) as brand,
           any_value(o.brand_wikidata) as brand_wikidata, any_value(o.postcode) as postcode,
           any_value(o.phone) as phone, any_value(o.website) as website,
           bool_or(list_contains(o.datasets, 'Foursquare')) as has_fsq,
           -- closed only if every listing says so
           case when bool_and(o.operating_status = 'permanently_closed') then 'permanently_closed'
                else any_value(nullif(o.operating_status, 'permanently_closed')) end as operating_status
    from ovt_canon k join ovt_all o on o.id = k.id group by k.place_id
  )
  select o.* replace (
           coalesce(o.category, f.category) as category, coalesce(o.brand, f.brand) as brand,
           coalesce(o.brand_wikidata, f.brand_wikidata) as brand_wikidata,
           coalesce(o.postcode, f.postcode) as postcode, coalesce(o.phone, f.phone) as phone,
           coalesce(o.website, f.website) as website, f.operating_status as operating_status),
         f.has_fsq
  from ovt_all o join fill f on f.place_id = o.id;

create or replace table atp_n as
  select 'atp:' || atp_id as id, * exclude (atp_id, housenumber),
         norm_name(name) as nn,
         coalesce(house_number(housenumber), house_number(address)) as hn
  from atp;

-- Each AllThePlaces row joins the one Overture place it matches best.
create or replace table atp_match as
  select a_id as place_id, b_id as atp_id, rule, dist, sim
  from match_pairs('ovt_n', 'atp_n')
  qualify row_number() over (
    partition by b_id
    order by case rule when 'number' then 1 when 'near' then 2 else 3 end, sim desc, dist) = 1;

create or replace table core_member as
  select place_id, 'overture' as source, substr(id, 5) as source_id,
         case when id = place_id then 'self' else 'duplicate' end as rule, 0.0 as dist, 1.0 as sim
  from ovt_canon
  union all
  select coalesce(m.place_id, a.id), 'atp', substr(a.id, 5),
         coalesce(m.rule, 'self'), coalesce(m.dist, 0.0), coalesce(m.sim, 1.0)
  from atp_n a left join atp_match m on m.atp_id = a.id;

-- One AllThePlaces row per Overture place fills attribute gaps.
create or replace table atp_fill as
  select m.place_id, a.*
  from atp_match m join atp_n a on a.id = m.atp_id
  qualify row_number() over (partition by m.place_id order by m.dist) = 1;

create or replace table core_place as
  select *, zip5(postcode) as zip, street_key(address) as sk from (
  select o.id, o.name, o.category,
         coalesce(o.brand, nullif(f.brand, '')) as brand,
         coalesce(o.brand_wikidata, nullif(f.brand_wikidata, '')) as brand_wikidata,
         coalesce(o.address, nullif(f.address, '')) as address,
         coalesce(o.city, nullif(f.city, '')) as city,
         coalesce(o.region, nullif(f.region, '')) as region,
         coalesce(o.postcode, nullif(f.postcode, '')) as postcode,
         coalesce(o.phone, nullif(f.phone, '')) as phone,
         coalesce(o.website, nullif(f.website, '')) as website,
         o.lat, o.lng, o.operating_status as overture_status,
         o.nn, coalesce(o.hn, f.hn) as hn,
         o.has_fsq
  from ovt_n o left join atp_fill f on f.place_id = o.id
  union all
  select a.id, a.name, nullif(a.category, ''), nullif(a.brand, ''), nullif(a.brand_wikidata, ''),
         nullif(a.address, ''), nullif(a.city, ''), nullif(a.region, ''), nullif(a.postcode, ''),
         nullif(a.phone, ''), nullif(a.website, ''), a.lat, a.lng, null, a.nn, a.hn, false
  from atp_n a
  where a.id not in (select atp_id from atp_match)
  );

-- Evidence. Every row: place_id, source, source_id, state, date, rule, dist,
-- plus the name and address the source used, kept for review.

-- Registers and other located records, through the matcher.
create or replace table register_n as
  select source || ':' || source_id as id, *, norm_name(name) as nn, house_number(address) as hn,
         zip5(address) as zip, street_key(address) as sk
  from register;
create or replace table register_pos as select * from register_n where lat is not null;
create or replace table register_addr as select * from register_n where lat is null;

create or replace macro matched_evidence(places) as table (
  select m.a_id as place_id, r.source, r.source_id, r.state, r.date, m.rule, m.dist,
         r.name as ev_name, r.address as ev_address
  from (
    select * from match_pairs(places, 'register_pos')
    -- a shared house number may hit every listing of the place; without one, only the nearest
    qualify rule = 'number'
         or (max(rule = 'number') over (partition by b_id) = false
             and row_number() over (partition by b_id order by sim desc, dist) = 1)
    union all
    select * from match_address(places, 'register_addr')
  ) m join register_n r on r.id = m.b_id
);

create or replace table core_evidence as
  -- Foursquare's own closing date, joined on the Foursquare id Overture carries
  select k.place_id, 'fsq_closed' as source, f.fsq_place_id as source_id, 'closed' as state,
         f.date_closed as date, 'id' as rule, 0.0 as dist, f.name as ev_name, f.address as ev_address
  from ovt_all o join ovt_canon k on k.id = o.id join fsq_closed f on f.fsq_place_id = o.fsq_id
  -- An id outlives the business: Overture can keep the row and rename it for
  -- the next tenant. The closure applies only while the names still agree.
  where f.date_closed is not null and same_name(f.name, o.name)
  union all
  -- present in the chain's own store locator on the day it was collected
  select m.place_id, 'atp', a.id, 'open', a.collected, m.rule, m.dist, a.name, a.address
  from core_member m join atp_n a on a.id = 'atp:' || m.source_id
  where m.source = 'atp' and a.end_date is null and a.collected is not null
  union all
  select * from matched_evidence('core_place');

-- Closures that only hold for independents. When a chain outlet's license or
-- permit ends, the outlet usually carries on under a new franchisee, so
-- these sources do not close a place that carries a brand.
create or replace table independents_only as
  select * from (values ('cdph_chicago_oob'), ('abca_dc_cancelled'), ('bacp_chicago_cancelled')) t(source);
delete from core_evidence
  where source in (select source from independents_only)
    and place_id in (select id from core_place where brand is not null);

-- Places minted from a register. Some registers list the storefront itself:
-- a bank branch, a store authorized for SNAP, a licensed premises. A row
-- from one of those becomes a new place when it is open, has a position,
-- matched nothing, and no listed place within 80 m has a name anywhere near
-- its own (the matcher's near misses are mostly the same place under a
-- longer name, and must not be added twice).
create or replace table storefront_source as
  select * from (values
    ('fdic_locations', 'bank'),
    ('snap_current', 'grocery_or_convenience_store'),
    ('abca_dc_active', 'licensed_premises'),
    ('sla_ny', 'licensed_premises'),
    ('dohmh_nyc', 'restaurant'),
    ('cdph_chicago', 'food_service'),
    ('dmv_ny', 'vehicle_repair_or_dealer'),
    ('dos_ny_salons', 'salon_or_barber_shop'),
    ('agm_ny', 'food_store'),
    ('dph_de', 'restaurant')) t(source, category);

create or replace table born as
  with unmatched as (
    select r.*, s.category
    from register_pos r join storefront_source s using (source)
    where r.state = 'open'
      and not exists (select 1 from core_evidence e where e.source = r.source and e.source_id = r.source_id)
      -- a license held for a premises that has no name yet
      and r.name not ilike 'tbd%'
      -- a name that ends in a legal form is the company, not the sign on the door
      and not regexp_matches(lower(r.name), '\b(inc|incorporated|corp|corporation|llc|lp|llp|ltd)\.?\s*[0-9]*$')
  ),
  lookalike as (
    select distinct u.id
    from (select *, cell_y(lat) as cy, cell_x(lng) as cx from unmatched) u
    join (select p.nn, p.hn, p.lat, p.lng, cell_y(p.lat) + dy.d as cy, cell_x(p.lng) + dx.d as cx
          from core_place p, (values (-1), (0), (1)) dy(d), (values (-1), (0), (1)) dx(d)) p
      on p.cy = u.cy and p.cx = u.cx
    where (dist_m(u.lat, u.lng, p.lat, p.lng) <= 200 and name_sim(u.nn, p.nn) >= 0.9)
       or (dist_m(u.lat, u.lng, p.lat, p.lng) <= 80
      and (jaro_winkler_similarity(u.nn, p.nn) >= 0.7
           -- same door and same first word: "Silk Lounge" and "Silk Restaurant and Lounge"
           or (u.hn = p.hn and split_part(u.nn, ' ', 1) = split_part(p.nn, ' ', 1))))
  )
  select 'alm:' || u.source || '/' || u.source_id as place_id, u.*
  from unmatched u
  where u.id not in (select id from lookalike)
  -- one register can list a premises twice, and two registers can list the same shop
  qualify row_number() over (partition by u.nn, u.hn, cell_y(u.lat), cell_x(u.lng) order by u.source, u.source_id) = 1;

insert into core_place
  select place_id, name, category, null, null,
         split_part(address, ', ', 1), nullif(split_part(address, ', ', 2), ''),
         nullif(regexp_extract(address, ', ([A-Z]{2}) [0-9]{5}', 1), ''), zip, null, null,
         lat, lng, null, nn, hn, false, zip, sk
  from born;
insert into core_member
  select place_id, source, source_id, 'self', 0.0, 1.0 from born;
insert into core_evidence
  select place_id, source, source_id, state, date, 'self', 0.0, name, address from born;

create or replace table core_status as
  select * from status_of('core_evidence', (select build_date from params), (select recent_days from params));
