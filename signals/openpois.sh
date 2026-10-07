#!/usr/bin/env bash
# OpenPOIs rows inside a region box -> $OUT/openpois.parquet
#
# OpenPOIs (Henry Spatial Analysis) conflates OSM and Overture for the US and
# publishes two things this project does not compute itself:
#   - events from OSM's edit history matched to Overture places: a feature
#     that was deleted, lost its main tag, or was renamed to something else
#   - a calibrated confidence that each place exists and is open
# Read in place over HTTP, pruned on the bbox column.
#
# Data under the ODbL. https://github.com/henryspatialanalysis/openpois
source "$(dirname "$0")/../lib/common.sh"
region "$1"

BUCKET=https://s3.us-west-2.amazonaws.com/us-west-2.opendata.source.coop
PREFIX=henryspatialanalysis/openpois/latest
curl -fsS -A "$UA" "$BUCKET/$PREFIX/README.md" | sed -n '1s/^# OpenPOIs //p' > "$OUT/openpois.version"
# The partition folders have a literal % in their names, which a URL must escape.
FILES="$(curl -fsS -A "$UA" "$BUCKET/?list-type=2&prefix=$PREFIX/conflated-parquet/" \
  | tr '<' '\n' | sed -n 's|^Key>\(.*parquet\)$|\1|p' | sed 's/%/%25/g' \
  | sed "s|.*|'$BUCKET/&'|" | paste -sd, -)"
[ -n "$FILES" ] || { echo "no OpenPOIs files found" >&2; exit 1; }

duck <<SQL
copy (
  select overture_id, osm_type, osm_id, conf_mean,
         shadow_event_type as event, shadow_event_timestamp::date as event_date
  from read_parquet([$FILES])
  where bbox.xmin >= $W and bbox.xmax <= $E and bbox.ymin >= $S and bbox.ymax <= $N
) to '$OUT/openpois.parquet' (format parquet, compression zstd);
SQL
