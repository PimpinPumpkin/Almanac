# Almanac

An open table of places in the United States, with dated evidence of whether
each one is still open.

Three open datasets already list most US places. Almanac merges them and adds
the part none of them has: for each place, the records that say it was open
or closed on a specific day, and where each record came from.

Status: first milestone. It builds test regions end to end. Nothing is
published yet.

## What it is

- **Base layer**, imported: Overture Maps places, OpenStreetMap named
  businesses and landmarks, AllThePlaces chain locations.
- **Evidence layer**: public records that say a specific place was open or
  closed on a specific date. Today: Foursquare closing dates, OSM lifecycle
  tags and survey dates, Wikidata dissolution dates, FDIC bank branches and
  branch closings, USDA SNAP authorized stores, and presence in a chain's own
  store locator.
- **Output**: one row per place with a stable id, merged attributes, every
  source id it was built from, and a status of open, closed or unknown with
  the date and source of the evidence that decided it.

## What it is not

- Not a new survey. Every fact comes from a source listed in `SOURCES.md`.
- Not complete on status. Most places have no dated evidence and are
  `unknown`. In the District of Columbia test box, 6.6% of places get a
  status. `unknown` means nobody has said, not "probably open".
- Not a source of new places from registers. A bank branch or licensed
  premises that the base layer lacks is not added yet.
- Not tied to any app. Readers fetch the published files. Nothing here
  imports code from a reader.

## Layout

```
build.sh            build one region end to end
stats.sh            print the numbers for a built region
review.sh           print a fixed sample of matches for a person to read
regions.tsv         region boxes and which OSM extracts cover them
base/               importers: overture.sh, atp.sh + atp.py, osm.sh + osm.jq
signals/            closing signals joined by id: fsq_closed.sh, wikidata_p576.py
adapters/           one file per register: fdic.py, snap.py
sql/                lib.sql (matcher), core.sql, full.sql, status.sql, publish.sql
tests/              matcher threshold tests
reports/            numbers from the last build of each test region
```

## Build

Needs `duckdb` (built and tested with 1.5.4, with the httpfs and spatial extensions),
`osmium`, `jq`, `curl` and Python 3. No keys, no accounts.

```
duckdb -c "install httpfs; install spatial;"
duckdb < tests/match_test.sql
./build.sh dc-box
./stats.sh dc-box
./review.sh dc-box evidence fdic_history closed number
```

Downloads are cached under `data/`, which is not in git. The first build
fetches about 3.5 GB (AllThePlaces is 2.6 GB of that). After that a region
the size of Kentucky builds in about 35 seconds.

Every fetch sends `User-Agent: Almanac/0.1 (open US places dataset build)`.
Set `ALMANAC_CONTACT` to a URL or address to append a way to reach you.

## Output

`data/out/core-<region>.parquet`, `data/out/places-<region>.parquet` and
`data/out/manifest-<region>.json`. See `SPEC.md` for the columns, the
matching rules and their measured accuracy, the status rules, and the rules
that were tried and thrown out.

Reading a box out of a published file:

```sql
select id, name, status, status_date, status_source
from 'places-kentucky.parquet'
where lat between 38.0 and 38.1 and lng between -84.6 and -84.4;
```

## Licenses

The data files carry the licenses of their inputs. The core file is
permissive (CDLA-Permissive-2.0, Apache-2.0, CC0). The full file contains
OpenStreetMap data and is under the ODbL. Details in `SPEC.md` section 8,
`SOURCES.md` and `NOTICE`.

The code in this repo has no license yet.
