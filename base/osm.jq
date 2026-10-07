# One OSM feature from `osmium export` -> one flat row.
# A feature is live when it has a main key (amenity, shop, ...), and closed
# when the only main key it has sits behind a lifecycle prefix.
def mainkeys: ["amenity","shop","tourism","leisure","office","craft","healthcare","historic"];
def prefixes: ["disused","was","abandoned","closed"];
def dull: ["parking","parking_space","parking_entrance","bench","bicycle_parking","bicycle_rental",
           "bus_stop","waste_basket","toilets","drinking_water","shelter","post_box","telephone","vending_machine",
           "recycling","pitch","swimming_pool","playground","picnic_table","information","yes","no"];

.properties as $p
| (first(mainkeys[] | select($p[.] != null)) // null) as $live
| (first(prefixes[] as $x | mainkeys[] | select($p[$x + ":" + .] != null) | [$x, .]) // null) as $dead
| (if $live then {key: $live, value: $p[$live], prefix: null}
   elif $dead then {key: $dead[1], value: $p[$dead[0] + ":" + $dead[1]], prefix: $dead[0]}
   else empty end) as $k
| ($p.name // (if $k.prefix then ($p[$k.prefix + ":name"] // $p.old_name) else null end)) as $name
| select($name != null)
| select($k.value as $v | dull | index($v) | not)
| {
    osm_id: ($p["@type"][0:1] + ($p["@id"] | tostring)),
    edited: $p["@timestamp"],
    name: $name,
    category: ($k.key + "=" + $k.value),
    lifecycle: $k.prefix,
    housenumber: $p["addr:housenumber"],
    street: $p["addr:street"],
    city: $p["addr:city"],
    region: $p["addr:state"],
    postcode: $p["addr:postcode"],
    phone: ($p.phone // $p["contact:phone"]),
    website: ($p.website // $p["contact:website"]),
    brand: $p.brand,
    brand_wikidata: $p["brand:wikidata"],
    wikidata: $p.wikidata,
    check_date: ($p.check_date // $p["survey:date"]),
    end_date: $p.end_date,
    siret: $p["ref:FR:SIRET"],
    geometry: .geometry
  }
