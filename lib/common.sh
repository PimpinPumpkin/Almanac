# Shared settings for every script. Source this, do not run it.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA="${ALMANAC_DATA:-$ROOT/data}"
CACHE="$DATA/cache"
mkdir -p "$CACHE"

# Every fetch identifies itself. Set ALMANAC_CONTACT to a URL or address
# so a source operator can reach whoever runs the build.
UA="VelaAlmanac/0.1 (open US places dataset build; https://github.com/PimpinPumpkin/vela-almanac${ALMANAC_CONTACT:+; $ALMANAC_CONTACT})"
export UA DATA CACHE ROOT

# fetch URL OUT: download once, keep the cached copy on later runs.
fetch() {
  local url="$1" out="$2"
  if [ -s "$out" ]; then return 0; fi
  mkdir -p "$(dirname "$out")"
  # download servers answer 502 or 504 now and then when many jobs ask at once
  curl -fL --retry 8 --retry-delay 30 --retry-all-errors -sS -A "$UA" -o "$out.part" "$url"
  mv "$out.part" "$out"
}

# duck: DuckDB with the extensions loaded and the User-Agent set on http reads.
duck() {
  duckdb -cmd "load httpfs; load spatial; create or replace temporary secret ua (type http, extra_http_headers map{'User-Agent': '$UA'});" "$@"
}

# region NAME: load one row of regions.tsv into REGION, S, W, N, E, OSM_EXTRACTS, STATE,
# COUNTRY (US when blank) and OUT.
# STATE is empty for a plain box. When set, build.sh clips every input to
# that state's outline, since a state's bounding box spills into its neighbors.
region() {
  local row
  row="$(awk -F'\t' -v r="$1" '$1==r' "$ROOT/regions.tsv")"
  [ -n "$row" ] || { echo "unknown region: $1" >&2; exit 1; }
  IFS=$'\t' read -r REGION S W N E OSM_EXTRACTS STATE COUNTRY <<<"$row"
  COUNTRY="${COUNTRY:-US}"
  [ "$STATE" = - ] && STATE=""
  OUT="$DATA/$REGION"
  mkdir -p "$OUT"
  export REGION S W N E OSM_EXTRACTS STATE COUNTRY OUT
}

# state_outlines: Census cartographic boundaries (1:500,000), public domain,
# as $CACHE/census/states.parquet with columns state (postal code) and wkb.
state_outlines() {
  local zip="$CACHE/census/cb_2023_us_state_500k.zip" out="$CACHE/census/states.parquet"
  [ -s "$out" ] && return 0
  fetch https://www2.census.gov/geo/tiger/GENZ2023/shp/cb_2023_us_state_500k.zip "$zip"
  duck -c "copy (select STUSPS as state, st_aswkb(geom) as wkb from st_read('/vsizip/$zip'))
           to '$out' (format parquet);" >/dev/null
}
