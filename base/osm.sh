#!/usr/bin/env bash
# Named OSM businesses and landmarks inside a region box -> $OUT/osm.parquet
# Keeps features closed with a lifecycle prefix (disused:shop and friends);
# those become closure evidence later.
source "$(dirname "$0")/../lib/common.sh"
region "$1"

TMP="$OUT/osm.tmp"; rm -rf "$TMP"; mkdir -p "$TMP"
PARTS=()
for ex in ${OSM_EXTRACTS//,/ }; do
  pbf="$CACHE/osm/$(basename "$ex").osm.pbf"
  case "$ex" in
    /*) url="https://download.geofabrik.de$ex-latest.osm.pbf" ;;
    *)  url="https://download.geofabrik.de/north-america/us/$ex-latest.osm.pbf" ;;
  esac
  fetch "$url" "$pbf"
  osmium fileinfo -g header.option.osmosis_replication_timestamp "$pbf" >> "$TMP/dates"
  part="$TMP/$(basename "$ex").pbf"
  osmium extract -b "$W,$S,$E,$N" -s smart "$pbf" -o "$part" --overwrite
  PARTS+=("$part")
done
sort "$TMP/dates" | head -1 | cut -c1-10 > "$OUT/osm.date"

if [ "${#PARTS[@]}" -gt 1 ]; then
  osmium merge "${PARTS[@]}" -o "$TMP/box.pbf" --overwrite
else
  mv "${PARTS[0]}" "$TMP/box.pbf"
fi

osmium tags-filter "$TMP/box.pbf" \
  nwr/amenity,shop,tourism,leisure,office,craft,healthcare,historic \
  'nwr/disused:*' 'nwr/was:*' 'nwr/abandoned:*' 'nwr/closed:*' \
  -o "$TMP/poi.pbf" --overwrite
osmium export "$TMP/poi.pbf" -f geojsonseq -x print_record_separator=false \
  -a type,id,timestamp -o "$TMP/poi.geojsonseq" --overwrite
jq -c -f "$ROOT/base/osm.jq" "$TMP/poi.geojsonseq" > "$TMP/poi.ndjson"

duck <<SQL
copy (
  with g as (
    select * exclude (geometry, edited), to_timestamp(edited)::date as edited,
           st_centroid(st_geomfromgeojson(geometry)) as c
    -- a large park or refuge outline can be tens of MB on one line
    from read_ndjson('$TMP/poi.ndjson', maximum_object_size = 1073741824, columns = {
      osm_id: 'varchar', edited: 'bigint', name: 'varchar', category: 'varchar', lifecycle: 'varchar',
      housenumber: 'varchar', street: 'varchar', city: 'varchar', region: 'varchar', postcode: 'varchar',
      phone: 'varchar', website: 'varchar', opening_hours: 'varchar', brand: 'varchar', brand_wikidata: 'varchar',
      wikidata: 'varchar', check_date: 'varchar', end_date: 'varchar', siret: 'varchar', geometry: 'json'})
  )
  select * exclude (c), st_y(c) as lat, st_x(c) as lng
  from g
  where st_x(c) between $W and $E and st_y(c) between $S and $N
  -- a way and the multipolygon built on it can both be exported; keep one
  qualify row_number() over (partition by osm_id order by edited desc) = 1
) to '$OUT/osm.parquet' (format parquet, compression zstd);
SQL
rm -rf "$TMP"
