#!/usr/bin/env bash
# Print a fixed sample of matched pairs for one rule so a person can read them.
#   ./review.sh REGION merge atp|osm RULE [N]
#   ./review.sh REGION evidence SOURCE STATE RULE [N]
# The sample is ordered by a hash of the ids, so it is the same every run.
source "$(dirname "$0")/lib/common.sh"
region "$1"; kind="$2"
DB="$OUT/build.duckdb"
if [ "$kind" = merge ]; then
  layer="$3"; rule="$4"; n="${5:-40}"
  if [ "$layer" = atp ]; then m=atp_match; t=atp_n; k=atp_id; p=core_place; else m=osm_match; t=osm_n; k=osm_id; p=core_place; fi
  duckdb -readonly "$DB" -c ".mode list" -c ".separator ' | '" -c "
    select m.dist, m.sim, p.name, coalesce(p.address, '-'), '<>', b.name, coalesce(b.address, '-')
    from $m m join $p p on p.id = m.place_id join $t b on b.id = m.$k
    where m.rule = '$rule' order by hash(m.$k) limit $n"
else
  source_="$3"; state="$4"; rule="$5"; n="${6:-40}"
  duckdb -readonly "$DB" -c ".mode list" -c ".separator ' | '" -c "
    select e.dist, e.date, p.name, coalesce(p.address, '-'), '<>', e.ev_name, coalesce(e.ev_address, '-')
    from full_evidence e join full_place p on p.id = e.place_id
    where e.source = '$source_' and e.state = '$state' and e.rule = '$rule'
    order by hash(e.source_id || e.place_id) limit $n"
fi
