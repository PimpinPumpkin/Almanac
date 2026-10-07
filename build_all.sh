#!/usr/bin/env bash
# Build every state in regions.tsv, one after another: ./build_all.sh
# Keeps only the published files and the reports. The OSM extract and the
# working database of each state are deleted once it is done, so the whole
# run fits in a few GB of disk. A state that already has a manifest is skipped.
source "$(dirname "$0")/lib/common.sh"
cd "$ROOT"
mkdir -p reports
awk -F'\t' '!/^#/ && $7 != "" && $7 != "-" {print $1}' regions.tsv | while read -r r; do
  [ -s "$DATA/out/manifest-$r.json" ] && continue
  start=$(date +%s)
  if ./build.sh "$r" >"$DATA/$r.log" 2>&1; then
    ./stats.sh "$r" > "reports/$r.txt" 2>&1 || true
    echo "$r ok $(( $(date +%s) - start ))s"
  else
    echo "$r FAILED, see $DATA/$r.log"
  fi
  rm -f "$DATA/$r/build.duckdb" "$CACHE/osm/$r.osm.pbf"
done
