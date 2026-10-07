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
