# Almanac

An open table of places in the United States, with dated evidence of whether
each one is still open.

Three open datasets already list most US places. Almanac merges them and adds
the part none of them has: for each place, the records that say it was open
or closed on a specific day, and where each record came from.

## Coverage by state

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/coverage-dark.svg">
  <img alt="Share of places with a dated open or closed status, by state and category" src="docs/coverage-light.svg">
</picture>

Interactive version, with the numbers on hover:
https://pimpinpumpkin.github.io/Almanac/ . The same numbers as a table are
in [COVERAGE.md](COVERAGE.md). Both are made by `tools/coverage_map.py`.

## Coverage by category

What Almanac lists today, how much of it has a dated open or closed record,
and which public register can close the gap. Counts are from the four test
regions (a District of Columbia box, a Sacramento box, Delaware and
Kentucky), 480,000 places in all.

| Category | Listed | Has a dated status | What it comes from, and what comes next | Can it be complete? |
| --- | ---: | ---: | --- | --- |
| Fast food and chain restaurants | 3,736 | 66% | Chain store locators (built) | Yes, for chains with a locator |
| Banks and credit unions | 4,603 | 52% | FDIC branches and closings, NCUA credit union offices (built) | Yes |
| Gas stations | 4,566 | 45% | Chain locators (built). Next: underground storage tank registries | Mostly |
| Grocery and convenience stores | 5,964 | 39% | SNAP authorized stores, chain locators (built) | Mostly |
| Pharmacies | 1,848 | 32% | Chain locators, NPPES (built). Next: state pharmacy boards | Mostly |
| Schools | 11,116 | 21% | NCES public schools (built). The category also holds preschools, private and trade schools, which NCES public data does not cover | Public schools yes |
| Restaurants and cafes, independent | 29,539 | 25% | Foursquare closing dates, OSM, alcohol licenses in California and DC (built). Next: more state license lists, health inspections | State by state, never everywhere |
| Hotels | 2,571 | 20% | Chain locators (built). Next: state lodging licenses where published | Chains yes, independents patchy |
| Museums | 999 | 11% | IRS exempt organizations (built) | Partly |
| Hospitals | 1,441 | 11% | CMS hospitals, NPPES (built). The category also holds departments and clinics listed as hospitals | Real hospitals yes |
| Bars | 3,535 | 20% | Foursquare, OSM, alcohol licenses in California and DC (built). Next: more state license lists | Where the state publishes its list, about half today. See below |
| Everything else | 403,680 | 6% | Salons, repair shops, offices, clinics, churches. NPPES and IRS exempt organizations (built). Next: state professional and repair licenses | No. This is the long tail |
| EV chargers | 614 | 3% | Not handled yet. The federal station list needs a free API key | Yes, if a key is allowed |
| Parks | 6,122 | 0.2% | OSM. Parks rarely close, so a listing is most of the job | Listing yes, status not needed |

Across all 480,000 places, 9.1% have a dated status. The table is made by
`duckdb < sql/coverage.sql`.

Bars and restaurants are low in the table because two of the four regions
(Delaware, Kentucky) have no license list yet. Where there is one, it helps
but does not finish the job: inside the District of Columbia, with the full
license list loaded, 49% of bars and 42% of restaurants have a status. Most
of the rest are bar listings that match no license at all. Those get a low
`open_score` and a `missing_license` flag, not a closed status (SPEC.md
section 7).

"Next" sources are a plan. None has been fetched or checked yet.

Status: first milestone. It builds test regions end to end. Nothing is
published yet.

## What it is

- **Base layer**, imported: Overture Maps places, OpenStreetMap named
  businesses and landmarks, AllThePlaces chain locations.
- **Evidence layer**: public records that say a specific place was open or
  closed on a specific date. Today: Foursquare closing dates, OSM lifecycle
  tags and survey dates, Wikidata dissolution dates, FDIC bank branches and
  branch closings, USDA SNAP authorized stores, CMS hospitals, NCES public
  schools, NPPES health care organizations, IRS exempt organizations, alcohol
  licenses in California and the District of Columbia, and presence in a
  chain's own store locator.
- **Output**: one row per place with a stable id, merged attributes, every
  source id it was built from, a status of open, closed or unknown with
  the date and source of the evidence that decided it, and an `open_score`
  from 0 to 1 for every place.

## What it is not

- Not a new survey. Every fact comes from a source listed in `SOURCES.md`.
- Not complete on status. Most places have no dated evidence and are
  `unknown`. In the District of Columbia test box, 11% of places get a
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
adapters/           one file per register: fdic, ncua, snap, cms, nces, nppes,
                    irs, abc_ca, abca_dc
sql/                lib.sql (matcher), core.sql, full.sql, status.sql, publish.sql
tests/              matcher threshold tests
reports/            numbers from the last build of each region
tools/              coverage_map.py, which draws the by-state map and table
docs/               the map, and the interactive page served by GitHub Pages
build_all.sh        build every state in regions.tsv
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
fetches about 5 GB (AllThePlaces is 2.6 GB and NPPES 1.2 GB of that). After that a region
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

Copyleft throughout.

- **Code**: GNU Affero General Public License, version 3 or later. See
  `LICENSE`.
- **Data**: both published files are under the Open Database License 1.0.
  If you publish a database built from them, it has to be under the ODbL
  too. The full file has to be, because it contains OpenStreetMap data. The
  core file is built from permissive inputs only and is placed under the
  ODbL by choice.

Attribution for every input is in `NOTICE`. Per-source terms are in
`SOURCES.md` and `SPEC.md` section 8.
