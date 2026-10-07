-- Coverage by category across every built region, for the README table.
-- Run: duckdb < sql/coverage.sql
-- The buckets are a rough reading of Overture taxonomy terms and OSM tags;
-- categories are not harmonized yet (SPEC.md section 3).
create macro bucket(c) as case
  when c in ('bar', 'pub', 'sports_bar', 'cocktail_bar', 'wine_bar', 'dive_bar', 'lounge', 'brewery', 'beer_bar',
             'irish_pub', 'gay_bar', 'night_club', 'dance_club', 'amenity=bar', 'amenity=pub', 'amenity=nightclub') then 'bars'
  when c in ('bank', 'credit_union', 'bank_or_credit_union', 'amenity=bank') then 'banks and credit unions'
  when c in ('gas_station', 'fuel_station', 'amenity=fuel') then 'gas stations'
  when c like '%ev_charging%' or c = 'amenity=charging_station' then 'ev chargers'
  when c in ('grocery_store', 'supermarket', 'convenience_store', 'shop=supermarket', 'shop=convenience', 'shop=grocery') then 'grocery and convenience'
  when c in ('fast_food_restaurant', 'amenity=fast_food') then 'fast food'
  when c like '%restaurant%' or c in ('cafe', 'coffee_shop', 'amenity=cafe', 'diner', 'bakery', 'sandwich_shop') then 'restaurants and cafes'
  when c like '%museum%' then 'museums'
  when c in ('park', 'leisure=park', 'dog_park', 'playground', 'national_park', 'state_park') then 'parks'
  when c in ('pharmacy', 'amenity=pharmacy') then 'pharmacies'
  when c in ('hotel', 'motel', 'tourism=hotel', 'tourism=motel') then 'hotels'
  when c like '%school%' then 'schools'
  when c in ('hospital', 'amenity=hospital') then 'hospitals'
  else 'everything else' end;

select bucket(category) as category, count(*) as listed,
       round(100.0 * count(*) filter (where status <> 'unknown') / count(*), 1) as pct_with_status,
       count(*) filter (where status = 'open') as open,
       count(*) filter (where status = 'closed') as closed,
       round(100.0 * count(*) filter (where len(evidence) > 0) / count(*), 1) as pct_any_evidence
from read_parquet('data/out/places-*.parquet')
group by 1 order by pct_with_status desc;
select count(*) total, round(100.0*count(*) filter (where status<>'unknown')/count(*),1) pct from read_parquet('data/out/places-*.parquet');
