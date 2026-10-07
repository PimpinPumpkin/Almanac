#!/usr/bin/env bash
# Overture places inside a region box -> $OUT/overture.parquet
# The newest release is found by listing the public bucket. Reads are pruned
# on the bbox struct, which has row group statistics.
source "$(dirname "$0")/../lib/common.sh"
region "$1"

BUCKET=https://overturemaps-us-west-2.s3.amazonaws.com
RELEASE="${OVERTURE_RELEASE:-$(curl -fsS -A "$UA" "$BUCKET/?list-type=2&prefix=release/&delimiter=/" \
  | tr '<' '\n' | sed -n 's|^Prefix>release/\(.*\)/$|\1|p' | sort | tail -1)}"
FILES="$(curl -fsS -A "$UA" "$BUCKET/?list-type=2&prefix=release/$RELEASE/theme=places/type=place/" \
  | tr '<' '\n' | sed -n "s|^Key>\(.*parquet\)$|'$BUCKET/\1'|p" | paste -sd, -)"
[ -n "$FILES" ] || { echo "no Overture place files for $RELEASE" >&2; exit 1; }
echo "$RELEASE" > "$OUT/overture.release"

duck <<SQL
copy (
  select
    id,
    names."primary" as name,
    coalesce(taxonomy."primary", basic_category) as category,
    brand.names."primary" as brand,
    brand.wikidata as brand_wikidata,
    addresses[1].freeform as address,
    addresses[1].locality as city,
    addresses[1].region as region,
    addresses[1].postcode as postcode,
    phones[1] as phone,
    websites[1] as website,
    confidence,
    operating_status,
    list_filter(sources, lambda s: lower(s.dataset) = 'foursquare')[1].record_id as fsq_id,
    list_distinct(list_transform(sources, lambda s: s.dataset)) as datasets,
    st_y(geometry) as lat,
    st_x(geometry) as lng
  from read_parquet([$FILES])
  where bbox.xmin >= $W and bbox.xmax <= $E and bbox.ymin >= $S and bbox.ymax <= $N
    and names."primary" is not null
    and (addresses[1].country = '$COUNTRY' or addresses[1].country is null)
) to '$OUT/overture.parquet' (format parquet, compression zstd);
SQL
