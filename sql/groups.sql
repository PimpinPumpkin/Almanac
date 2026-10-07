-- One coarse vocabulary for every place: Overture's top-level category groups.
-- An Overture row brings its own group. Everything else (OSM tags,
-- AllThePlaces tags, the coarse categories of places minted from registers)
-- is mapped onto the same thirteen names here.
create or replace macro group_of(category) as
  case
    when category is null then null
    -- places minted from registers
    when category in ('bank') then 'services_and_business'
    when category in ('grocery_or_convenience_store', 'food_store') then 'shopping'
    when category in ('licensed_premises', 'restaurant', 'food_service') then 'food_and_drink'
    when category in ('vehicle_repair_or_dealer') then 'services_and_business'
    when category in ('salon_or_barber_shop') then 'lifestyle_services'
    -- OSM style key=value, from OSM and AllThePlaces
    when category in ('amenity=restaurant', 'amenity=fast_food', 'amenity=cafe', 'amenity=bar', 'amenity=pub',
                      'amenity=ice_cream', 'amenity=food_court', 'amenity=biergarten', 'craft=brewery',
                      'craft=winery', 'craft=distillery') then 'food_and_drink'
    when category in ('amenity=pharmacy', 'amenity=clinic', 'amenity=doctors', 'amenity=dentist',
                      'amenity=hospital', 'amenity=veterinary') or category like 'healthcare=%' then 'health_care'
    when category in ('amenity=school', 'amenity=college', 'amenity=university', 'amenity=kindergarten',
                      'amenity=library', 'amenity=childcare', 'amenity=language_school', 'amenity=music_school',
                      'amenity=driving_school') then 'education'
    when category = 'amenity=place_of_worship' or category like 'historic=%'
         or category in ('tourism=artwork', 'tourism=attraction', 'tourism=viewpoint') then 'cultural_and_historic'
    when category in ('amenity=fuel', 'amenity=car_rental', 'amenity=car_wash', 'amenity=bus_station',
                      'amenity=ferry_terminal', 'amenity=taxi', 'amenity=boat_rental', 'tourism=information')
      then 'travel_and_transportation'
    when category in ('amenity=police', 'amenity=fire_station', 'amenity=townhall', 'amenity=courthouse',
                      'amenity=community_centre', 'amenity=social_facility', 'amenity=embassy',
                      'amenity=social_centre', 'amenity=prison', 'amenity=public_building', 'office=government',
                      'office=diplomatic', 'office=ngo', 'office=association', 'office=political_party')
      then 'community_and_government'
    when category in ('amenity=cinema', 'amenity=theatre', 'amenity=nightclub', 'amenity=arts_centre',
                      'amenity=events_venue', 'amenity=casino', 'tourism=museum', 'tourism=gallery',
                      'tourism=zoo', 'tourism=aquarium', 'tourism=theme_park') then 'arts_and_entertainment'
    when category in ('tourism=hotel', 'tourism=motel', 'tourism=hostel', 'tourism=guest_house',
                      'tourism=apartment', 'tourism=camp_site', 'tourism=caravan_site', 'tourism=chalet')
      then 'lodging'
    when category in ('shop=hairdresser', 'shop=beauty', 'shop=massage', 'shop=tattoo', 'shop=laundry',
                      'shop=dry_cleaning', 'shop=cosmetics') then 'lifestyle_services'
    when category in ('shop=car_repair', 'shop=funeral_directors', 'shop=travel_agency', 'shop=copyshop',
                      'shop=storage_rental', 'shop=locksmith', 'shop=tailor', 'amenity=bank', 'amenity=atm',
                      'amenity=post_office', 'amenity=bureau_de_change', 'amenity=money_transfer')
         or category like 'office=%' or category like 'craft=%' then 'services_and_business'
    when category like 'shop=%' or category = 'amenity=marketplace' then 'shopping'
    when category like 'leisure=%' then 'sports_and_recreation'
    else null
  end;

-- The second level of the same vocabulary: Overture's subgroups (about 110
-- of them). Overture rows carry their own. This maps the commonest OSM tags
-- and register categories onto them, in Overture's own terms: a cafe is a
-- casual_eatery, a pharmacy a specialty_store, a car repair shop a
-- vehicle_service. A tag that is not listed gets no subgroup.
create or replace macro subgroup_of(category) as
  case
    when category in ('bank', 'amenity=bank', 'amenity=atm', 'amenity=bureau_de_change', 'amenity=money_transfer') then 'financial_service'
    when category in ('restaurant', 'food_service', 'amenity=restaurant', 'amenity=food_court') then 'restaurant'
    when category in ('amenity=fast_food', 'amenity=ice_cream', 'shop=bakery') then 'casual_eatery'
    when category = 'amenity=cafe' then 'non_alcoholic_beverage_venue'
    when category in ('licensed_premises', 'amenity=bar', 'amenity=pub', 'amenity=biergarten', 'craft=brewery',
                      'craft=winery', 'craft=distillery') then 'alcoholic_beverage_venue'
    when category in ('grocery_or_convenience_store', 'food_store', 'shop=supermarket', 'shop=greengrocer',
                      'shop=butcher', 'shop=alcohol', 'shop=wine', 'shop=beverages', 'shop=tobacco',
                      'shop=deli', 'shop=seafood', 'shop=confectionery') then 'food_and_beverage_store'
    when category = 'shop=convenience' then 'convenience_store'
    when category = 'shop=department_store' then 'department_store'
    when category in ('shop=clothes', 'shop=shoes', 'shop=jewelry', 'shop=fashion_accessories', 'shop=bag') then 'fashion_and_apparel_store'
    when category in ('shop=car', 'shop=motorcycle', 'shop=trailer', 'shop=caravan') then 'vehicle_dealer'
    when category in ('amenity=pharmacy', 'shop=chemist', 'shop=hardware', 'shop=florist', 'shop=pet', 'shop=books',
                      'shop=furniture', 'shop=electronics', 'shop=mobile_phone', 'shop=gift', 'shop=sports',
                      'shop=bicycle', 'shop=toys', 'shop=optician', 'shop=doityourself') then 'specialty_store'
    when category in ('salon_or_barber_shop', 'shop=hairdresser', 'shop=beauty', 'shop=massage', 'shop=tattoo',
                      'shop=cosmetics') then 'personal_or_beauty_service'
    when category in ('shop=laundry', 'shop=dry_cleaning') then 'laundry_service'
    when category in ('vehicle_repair_or_dealer', 'shop=car_repair', 'shop=tyres', 'amenity=car_wash') then 'vehicle_service'
    when category = 'amenity=fuel' then 'fueling_station'
    when category in ('amenity=parking') then 'parking'
    when category in ('amenity=bus_station', 'amenity=ferry_terminal', 'amenity=taxi', 'amenity=car_rental') then 'ground_transport_facility_or_service'
    when category = 'amenity=hospital' then 'hospital'
    when category in ('amenity=clinic', 'amenity=doctors', 'amenity=dentist') then 'outpatient_care_facility'
    when category = 'amenity=veterinary' then 'animal_or_pet_service'
    when category in ('amenity=school', 'amenity=college', 'amenity=university', 'amenity=kindergarten',
                      'amenity=language_school', 'amenity=music_school') then 'place_of_learning'
    when category = 'amenity=library' then 'library'
    when category = 'amenity=childcare' then 'family_service'
    when category = 'amenity=place_of_worship' then 'place_of_worship'
    when category like 'historic=%' then 'historic_site'
    when category in ('tourism=hotel', 'tourism=motel') then 'hotel'
    when category = 'tourism=museum' then 'museum'
    when category = 'amenity=cinema' then 'movie_theater'
    when category in ('amenity=theatre', 'amenity=arts_centre') then 'performing_arts_venue'
    when category in ('amenity=townhall', 'amenity=courthouse', 'amenity=embassy', 'office=government', 'office=diplomatic') then 'government_office'
    when category in ('amenity=community_centre', 'amenity=social_facility', 'amenity=social_centre') then 'social_or_community_service'
    when category = 'amenity=post_office' then 'shipping_or_delivery_service'
    when category in ('leisure=park', 'leisure=playground', 'leisure=dog_park', 'leisure=garden') then 'park'
    when category in ('leisure=fitness_centre', 'leisure=sports_centre', 'leisure=stadium') then 'sport_or_fitness_facility'
    else null
  end;
