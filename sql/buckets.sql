-- Rough category buckets for the coverage table and map. A reading of
-- Overture taxonomy terms and OSM tags; categories are not harmonized yet
-- (SPEC.md section 3).
create or replace macro bucket(c) as case
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
