#!/usr/bin/env bash
# Foursquare OS Places rows that carry date_closed -> $CACHE/fsq/closed-<release>.parquet
# One pass over the release, US only, cached. The anonymous mirror stops at
# 2025-02-06. Newer releases need a Foursquare token: set FSQ_PLACES_GLOB to a
# glob DuckDB can read (after configuring credentials) and FSQ_RELEASE to its date.
source "$(dirname "$0")/../lib/common.sh"

# FSQ_COUNTRY picks the country, US by default. The US file keeps the short name.
FSQ_RELEASE="${FSQ_RELEASE:-2025-02-06}"
FSQ_COUNTRY="${FSQ_COUNTRY:-US}"
if [ "$FSQ_COUNTRY" = US ]; then
  OUTFILE="$CACHE/fsq/closed-$FSQ_RELEASE.parquet"
else
  OUTFILE="$CACHE/fsq/closed-$FSQ_RELEASE-$FSQ_COUNTRY.parquet"
fi
[ -s "$OUTFILE" ] && exit 0
mkdir -p "$CACHE/fsq"

if [ -n "${FSQ_PLACES_GLOB:-}" ]; then
  FILES="'$FSQ_PLACES_GLOB'"
else
  FILES="$(seq 0 80 | sed "s|.*|'https://data.source.coop/fused/fsq-os-places/$FSQ_RELEASE/places/&.parquet'|" | paste -sd, -)"
fi

duck <<SQL
copy (
  select fsq_place_id, name, address, locality as city, region, postcode,
         latitude as lat, longitude as lng,
         try_cast(date_closed as date) as date_closed
  from read_parquet([$FILES])
  where country = '$FSQ_COUNTRY' and date_closed is not null
) to '$OUTFILE.part' (format parquet, compression zstd);
SQL
mv "$OUTFILE.part" "$OUTFILE"
