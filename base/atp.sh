#!/usr/bin/env bash
# AllThePlaces, newest run, US brand locations -> $CACHE/atp/us.parquet (once per run)
# and the slice inside a region box -> $OUT/atp.parquet
source "$(dirname "$0")/../lib/common.sh"
region "$1"

RUN="${ATP_RUN:-$(curl -fsS -A "$UA" https://data.alltheplaces.xyz/runs/latest.json | jq -r .run_id)}"
ZIP="$CACHE/atp/$RUN.zip"
US="$CACHE/atp/us-$RUN.parquet"

if [ ! -s "$US" ]; then
  fetch "https://alltheplaces-data.openaddresses.io/runs/$RUN/output.zip" "$ZIP"
  python3 "$ROOT/base/atp.py" "$ZIP" | duck -c "
    copy (
      select * from read_csv('/dev/stdin', header = true, all_varchar = true, strict_mode = false)
      -- a spider can list a store twice
      qualify row_number() over (partition by spider, ref, lat, lng) = 1
    ) to '$US.part' (format parquet, compression zstd);"
  mv "$US.part" "$US"
fi
echo "$RUN" > "$OUT/atp.run"
STATE_FILTER=""
[ -n "${STATE:-}" ] && STATE_FILTER="and coalesce(nullif(region, ''), '$STATE') = '$STATE'"

duck -c "
  copy (
    select spider || '/' || coalesce(nullif(ref, ''), lat || ',' || lng) as atp_id,
           * exclude (lat, lng, collected, end_date),
           try_cast(collected as date) as collected, nullif(end_date, '') as end_date,
           lat::double as lat, lng::double as lng
    from '$US'
    where lat::double between $S and $N and lng::double between $W and $E
      -- machines, boxes and agents inside other stores are not places here
      and coalesce(category, '') not in (
        'amenity=atm', 'amenity=bicycle_rental', 'amenity=charging_station', 'amenity=public_bookcase',
        'amenity=post_box', 'amenity=parcel_locker', 'amenity=vending_machine', 'amenity=money_transfer',
        'amenity=parking', 'amenity=yes')
      $STATE_FILTER
  ) to '$OUT/atp.parquet' (format parquet, compression zstd);"
