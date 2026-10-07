#!/usr/bin/env bash
# Fetch everything that is the same for every state, once: ./prepare.sh
# The register files, the Foursquare closing dates, the AllThePlaces US file
# and the state outlines all land under data/cache. build.sh then finds them
# there. The scheduled build runs this in one job and hands the result to
# the per-state jobs.
source "$(dirname "$0")/lib/common.sh"
cd "$ROOT"
for adapter in adapters/*.py; do
  echo "== $adapter"
  python3 "$adapter"
done
echo "== foursquare closing dates"; signals/fsq_closed.sh >/dev/null
echo "== alltheplaces";             base/atp.sh us >/dev/null
echo "== state outlines";           state_outlines
du -sh "$CACHE/evidence" "$CACHE/fsq" "$CACHE"/atp/us-*.parquet "$CACHE/census/states.parquet"
