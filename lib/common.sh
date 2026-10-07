# Shared settings for every script. Source this, do not run it.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA="${ALMANAC_DATA:-$ROOT/data}"
CACHE="$DATA/cache"
mkdir -p "$CACHE"

# Every fetch identifies itself. Set ALMANAC_CONTACT to a URL or address
# so a source operator can reach whoever runs the build.
UA="Almanac/0.1 (open US places dataset build${ALMANAC_CONTACT:+; $ALMANAC_CONTACT})"
export UA DATA CACHE ROOT

# fetch URL OUT: download once, keep the cached copy on later runs.
fetch() {
  local url="$1" out="$2"
  if [ -s "$out" ]; then return 0; fi
  mkdir -p "$(dirname "$out")"
  curl -fL --retry 3 --retry-delay 5 -sS -A "$UA" -o "$out.part" "$url"
  mv "$out.part" "$out"
}

# duck: DuckDB with the extensions loaded and the User-Agent set on http reads.
duck() {
  duckdb -cmd "load httpfs; load spatial; create or replace temporary secret ua (type http, extra_http_headers map{'User-Agent': '$UA'});" "$@"
}

# region NAME: load one row of regions.tsv into REGION, S, W, N, E, OSM_EXTRACTS, STATE, OUT.
# STATE is empty for a plain box. When set, Overture and AllThePlaces rows are
# also filtered to that state code, since a state's bounding box spills into
# its neighbors.
region() {
  local row
  row="$(awk -F'\t' -v r="$1" '$1==r' "$ROOT/regions.tsv")"
  [ -n "$row" ] || { echo "unknown region: $1" >&2; exit 1; }
  IFS=$'\t' read -r REGION S W N E OSM_EXTRACTS STATE <<<"$row"
  OUT="$DATA/$REGION"
  mkdir -p "$OUT"
  export REGION S W N E OSM_EXTRACTS STATE OUT
}
