-- Core layer: Overture + AllThePlaces + evidence that does not come from OSM.
-- Nothing in this file may read an OSM-derived table; that is what keeps the
-- core layer free of ODbL terms. Inputs (made by build.sh): ovt, atp,
-- fsq_closed, register (evidence rows inside the region), params.

create or replace table ovt_n as
  select 'ovt:' || id as id, * exclude (id), norm_name(name) as nn, house_number(address) as hn
  from ovt;

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
  select id as place_id, 'overture' as source, substr(id, 5) as source_id,
         'self' as rule, 0.0 as dist, 1.0 as sim from ovt_n
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
         list_contains(o.datasets, 'Foursquare') as has_fsq
  from ovt_n o left join atp_fill f on f.place_id = o.id
  union all
  select a.id, a.name, nullif(a.category, ''), nullif(a.brand, ''), nullif(a.brand_wikidata, ''),
         nullif(a.address, ''), nullif(a.city, ''), nullif(a.region, ''), nullif(a.postcode, ''),
         nullif(a.phone, ''), nullif(a.website, ''), a.lat, a.lng, null, a.nn, a.hn, false
  from atp_n a
  where a.id not in (select atp_id from atp_match);

-- Evidence. Every row: place_id, source, source_id, state, date, rule, dist,
-- plus the name and address the source used, kept for review.

-- Registers and other located records, through the matcher.
create or replace table register_n as
  select source || ':' || source_id as id, *, norm_name(name) as nn, house_number(address) as hn
  from register;

create or replace macro matched_evidence(places) as table (
  select p.a_id as place_id, r.source, r.source_id, r.state, r.date, p.rule, p.dist,
         r.name as ev_name, r.address as ev_address
  from match_pairs(places, 'register_n') p join register_n r on r.id = p.b_id
  -- a shared house number may hit every listing of the place; without one, only the nearest
  qualify p.rule = 'number'
       or (max(p.rule = 'number') over (partition by p.b_id) = false
           and row_number() over (partition by p.b_id order by p.sim desc, p.dist) = 1)
);

create or replace table core_evidence as
  -- Foursquare's own closing date, joined on the Foursquare id Overture carries
  select o.id as place_id, 'fsq_closed' as source, f.fsq_place_id as source_id, 'closed' as state,
         f.date_closed as date, 'id' as rule, 0.0 as dist, f.name as ev_name, f.address as ev_address
  from ovt_n o join fsq_closed f on f.fsq_place_id = o.fsq_id
  where f.date_closed is not null
  union all
  -- present in the chain's own store locator on the day it was collected
  select m.place_id, 'atp', a.id, 'open', a.collected, m.rule, m.dist, a.name, a.address
  from core_member m join atp_n a on a.id = 'atp:' || m.source_id
  where m.source = 'atp' and a.end_date is null and a.collected is not null
  union all
  select * from matched_evidence('core_place');

create or replace table core_status as
  select * from status_of('core_evidence', (select build_date from params), (select recent_days from params));
