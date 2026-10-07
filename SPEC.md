# Vela Almanac spec

Version 0.1. This describes what the code in this repo does today. Where a
choice is still open it says so.

## 1. What a place is

One row per physical place a person could walk into or stand in front of: a
shop, a restaurant, a bank branch, a school, a park, a monument. Not a
machine or a box (ATMs, bike share docks, parcel lockers, charging points,
bus stops), and not an agent counter inside another store.

## 2. Layers and build order

The build order is fixed by licensing (section 8), not by convenience.

1. **Overture places** is the spine. Duplicate listings inside Overture are
   merged first (section 6), then every remaining row is a place.
2. **AllThePlaces** rows (brand lineage only) join the Overture place they
   match, or become new places.
3. Evidence that does not come from OSM is attached. The result is the
   **core layer**.
4. **OpenStreetMap** named features join the core place they match, or become
   new places. OSM evidence is attached. The result is the **full layer**.

Nothing made in steps 1 to 3 reads OSM data. A place keeps the same id in
both layers.

## 3. Place schema

Both layers have the same columns.

| column | type | notes |
| --- | --- | --- |
| id | string | stable id, section 4 |
| name | string | from the anchor source |
| category | string | Overture taxonomy term, or an OSM style `key=value` for AllThePlaces and OSM rows. Not harmonized yet. |
| brand, brand_wikidata | string | |
| address, city, region, postcode | string | address is the street line |
| phone, website | string | |
| status | string | open, closed or unknown, section 7 |
| status_date | date | date of the evidence that decided the status |
| status_source | string | source of that evidence |
| open_score | double | rough chance the place is open on the build date, 0 to 1, section 7 |
| missing_license | boolean | true for a bar in a state with a complete license list when no active license matched it. Null where the question does not apply. Section 7. |
| overture_status | string | Overture's own operating_status, carried as is. It has no date and does not feed status. |
| sources | list of {source, id} | every source row this place was built from |
| licenses | list of string | licenses of everything that touched the row |
| evidence | list of {source, source_id, state, date, rule, dist_m} | every evidence record, newest first |
| lat, lng | double | plain columns so row group statistics work |
| geometry | point | GeoParquet, WGS 84 |

Attributes come from the anchor source. Gaps (phone, website, brand, address)
are filled from one matched AllThePlaces row, then one matched OSM row.

## 4. Stable ids

An id is the id of the source row the place is anchored on, with a prefix:

- `ovt:<Overture id>` for every place with an Overture row. Overture ids
  (GERS) are stable across Overture releases.
- `atp:<spider>/<ref>` for a place only AllThePlaces has. `ref` is the
  chain's own store number.
- `osm:<n|w|r><OSM id>` for a place only OSM has.
- `alm:<hash of source and source_id>` is reserved for places minted from a
  register row. Nothing mints these yet.

Nothing is renumbered between builds, so a reader can diff two monthly files
on `id`. When Overture listings are merged as duplicates, the smallest id of
the group is the place id and the others stay in `sources`.

Measured on Overture alone, District of Columbia box, release 2026-08-19.0
against 2026-09-23.1: 76,147 of 78,098 ids carried over (97.5%), 1,951
disappeared, 18,041 were new.

Known gap: when a place that was `atp:` or `osm:` last month gains an
Overture match this month, its id becomes the `ovt:` one. The old id is
still in the row's `sources`, so a reader can follow the change. If this
churn turns out to matter, the fix is for the build to read the previous
file and keep the old id. It is not built because the churn has not been
measured; the second monthly build will measure it.

## 5. Evidence format

Every adapter writes one CSV with exactly these columns:

| column | meaning |
| --- | --- |
| source | adapter and list, for example `fdic_history` |
| source_id | the register's own id for the record |
| name | the name the public would see on the building |
| address | street line, city, state and ZIP in one string, street number first |
| lat, lng | WGS 84. May be blank when the address ends in a ZIP code; the record is then matched by address. |
| state | `open` or `closed` |
| date | ISO date. For open: the day the source says the place was operating. For closed: the day it closed. |

Rules for adapters:

- One file per source in `adapters/`, no shared state, standard library only.
- One current state per `source_id`. If the register has a history, emit the
  newest state.
- Rows with no date or no name, or with neither a position nor a ZIP code,
  are dropped and counted.
- If the register uses a legal name the public never sees, the adapter maps
  it (see `TRADE_NAMES` in `adapters/fdic.py`). The matcher stays generic.
- A record is evidence only if it says something about the premises. A
  record that only says something about paperwork is not (see SNAP end dates
  in section 9).

Signals that arrive by id rather than by position (Foursquare closing dates,
OSM tags, AllThePlaces rows) use the same evidence shape inside the build
but skip the matcher.

## 6. Entity matching

One matcher, `match_pairs` in `sql/lib.sql`, is used for AllThePlaces to
Overture, OSM to core, and evidence to places.

**Name.** Lowercase, strip accents and punctuation, `&` becomes `and`. Then
drop legal words (the, inc, llc, ltd, corp, company, co, national
association, na, branch) and trailing store numbers. Every spelling of
"credit union" (FCU, Federal Credit Union) becomes one word, so a credit
union matches itself and not the agency it is named after.

**House number.** The leading digits of the street line.

**Name similarity.**

| value | when |
| --- | --- |
| 1.0 | normalized names are identical |
| 0.9 | the shorter name, at least 4 letters, is the leading words of the longer: "giant" and "giant food" |
| Jaro-Winkler | otherwise, on the names with spaces removed. Counts only at 0.95 or more. |
| 0 | one side is an ATM and the other is not |

**Rules.** A pair matches under the first rule it passes.

| rule | house numbers | distance | name |
| --- | --- | --- | --- |
| number | equal | up to 250 m | 1.0, 0.9, or Jaro-Winkler from 0.95 |
| near | missing on one or both sides | up to 60 m | same |
| spot | present and different | up to 30 m | 1.0 only |

| address | equal | none: same ZIP code and same first word of the street name | same as number |

The `address` rule is only for records that have no position (CMS, NPPES,
IRS). Chains repeat names, so the name alone never matches. Two branches of a
chain across the street from each other have different house numbers and
fail `number`; they are more than 30 m apart or fail `spot`.

**Who gets the match.**

- Base merge: each incoming row joins the single best place (rule order
  number, near, spot; then similarity; then distance). A place can absorb
  several rows.
- Evidence: a `number` match applies to every place that passes, because
  the base has duplicate listings of the same shop. Without a `number`
  match, only the best single place gets the record.

**Duplicates inside Overture.** The same matcher runs Overture against
itself, but only the strictest case merges: same house number, within
250 m, identical normalized name. In the District of Columbia box that
merges 303 of 94,188 rows; 40 merged pairs were read and all 40 are the same
business (often a store and the money transfer counter inside it). The
looser cases are rejected, section 9.

**Join shape.** Candidates come from a grid hash join: cells are 0.004
degrees of latitude by 0.008 of longitude, one side is copied into its nine
neighbor cells, and the join is an equality on the cell. No distance
predicate, OR, or correlated subquery is used to find candidates.

**Tests.** `tests/match_test.sql` holds 25 invented pairs, plus 5 for the address rule, one per case the
rules are meant to accept or refuse. Run `duckdb < tests/match_test.sql`.

**Measured.** 40 matched pairs per rule were read in the District of
Columbia box, fewer where a rule has fewer than 40. "Right" means the two
rows are the same place.

| match | rule | right | notes |
| --- | --- | --- | --- |
| AllThePlaces to Overture | number | 39 of 40 | the miss joined a hospital department to its parent listing |
| | near | 38 of 40 | both misses are library rows listed under the parent institution's name |
| | spot | 12 of 14 | one store that moved across the street, one doubtful pair |
| OSM to core | number | 40 of 40 | |
| | near | 38 of 40 | both misses are part and whole (a dog park in a park, a clinic in a health department) |
| | spot | 40 of 40 | |
| FDIC closings to places | number | 40 of 40 (DC), 38 of 40 (Sacramento) | Sacramento misses: an office tower named after the bank, and a wealth advisor listing |
| | near, spot | 6 of 6 | |
| FDIC open branches | number | 39 of 40 | the miss is a loan officer's listing at the branch |
| | near, spot | 12 of 12 | |
| SNAP authorized stores | number | 40 of 40 | |
| | near, spot | 19 of 19 | |
| NCES schools | number | 39 of 40 | the miss is a school's aquatic center |
| | near | 12 of 12 | |
| CMS hospitals | address | 10 of 15 | all 10 hospitals are right; the other 5 rows are the hospital's gift shop, emergency room or a department sharing its name and address |
| NPPES organizations | address | 37 of 40 | the 3 misses are hospital departments |
| IRS exempt organizations | address | 36 of 40 | the 4 misses are a related body at the same address, such as a foundation arm |
| California alcohol licenses | address | 40 of 40 (Sacramento) | finds a place for 25% of licenses; the address rule is strict |
| DC alcohol licenses, active | number | 40 of 40 | finds a place for 77% of licenses |
| | spot | 20 of 20 | |
| DC alcohol license cancellations | number | 40 of 40 | |
| NCUA credit union offices | address | 38 of 40 | both misses are a church's credit union landing on the church |
| OSM lifecycle features to places | all | 40 of 40 (DC), 36 of 36 (Sacramento) | |

## 7. Status rules

Evidence is a list of dated open and closed records per place.

- **closed**: the place has a closed record with a date, and no open record
  dated after it. Any open record counts, whatever its source. The newest
  closed record supplies `status_date` and `status_source`.
- **open**: the newest record is open and is dated within 730 days of the
  build date.
- **unknown**: everything else. That includes places with no evidence, which
  is most of them, and places whose only evidence is an old open record.

Closed does not expire. A place closed in 2014 with nothing newer stays
closed.

A closed record that a newer open record overrode stays in `evidence`, so
the conflict is visible. Overture's confidence, update_time and
operating_status are never evidence: none carries a date of observation.

### Open score

`open_score` puts every place on one scale, including the ones with no
evidence. It is a rule of thumb with stated parts, not a fitted model.

| case | score |
| --- | --- |
| status is closed | 0.10 |
| newest evidence is open | 0.97 x 0.90 ^ years since that date, never below 0.75 |
| newest evidence is open but it overrode an older closing record | 0.80 x 0.90 ^ years, never below 0.50 |
| no evidence, Overture says permanently_closed | 0.30 |
| no evidence, `missing_license` is true | 0.30 |
| no evidence otherwise | 0.75 |

The 0.90 a year assumes about one business in ten closes each year. The
0.30 comes from this build: of places Overture marks permanently_closed that
OSM can speak to, 7 were surveyed open and 20 were tagged closed.

Check, all four test regions: the score from the core layer, which has seen
no OSM data, against what OSM says about the same place.

| OSM says | places | mean core score | scored 0.30 or less | scored 0.80 or more |
| --- | ---: | ---: | ---: | ---: |
| closed (lifecycle tag) | 338 | 0.64 | 65 | 12 |
| open (surveyed in the last 2 years) | 2,771 | 0.82 | 11 | 861 |

So a low score is rarely wrong about an open place (11 of 2,771), but the
core layer only catches 65 of 338 known closures. The score is honest about
what the evidence says and no better than the evidence. The 0.75 for no
evidence is likely low: among places with no core evidence that OSM can
speak to, 1,899 were surveyed open and 261 tagged closed (88% open), though
mappers survey open places more readily than they tag closed ones.

### Missing license

A bar cannot trade without an alcohol license, so in a state whose active
license list is complete, a bar that matches no license is suspect. Tested
in the District of Columbia, the one test area with such a list and with
positions on it.

| bars in DC | places | another source says open | another source says closed |
| --- | ---: | ---: | ---: |
| matched an active license | 228 | 32 | 3 |
| matched none | 560 | 17 | 131 |

Among the bars another source can speak to, no license means closed 89% of
the time. It is still not used as a closed verdict, for two reasons. The 17
open ones are real bars the matcher missed: the license is under another
trade name, or the bar sits inside a hotel or restaurant that holds the
license. And a sample of 40 unmatched bars with no other evidence held
several that looked like going concerns of that kind, so the true error
rate is likely higher than the 11% measured. Checking for another license
at the same address did not separate the two groups (bars with one: 9 open,
85 closed).

So the result is a flag and a lower score, not a status: `missing_license`
is true and `open_score` is 0.30 when there is no other evidence. In DC
that covers 390 bars. Restaurants and liquor stores are left alone: a
restaurant can run without a license, and liquor stores showed no signal
(2 open, 2 closed). California is not on the list because its licenses are
matched by address and only a quarter find their place.

### Evidence sources in this version

| source | state | date used | how it attaches |
| --- | --- | --- | --- |
| fsq_closed | closed | Foursquare `date_closed` | Foursquare id carried in the Overture row |
| osm_lifecycle | closed | `end_date` tag if it parses, else the feature's last edit (an upper bound) | the OSM feature's own merge |
| wikidata_p576 | closed | P576 value | `wikidata` tag on a merged OSM feature, offices excluded |
| fdic_history | closed | effective date of change code 721 | matcher |
| fdic_locations | open | run date of the list | matcher |
| snap_current | open | last data edit of the layer | matcher |
| snap_history | open | last day the file covers, open-ended authorizations only | matcher |
| nces_schools | open | June 30 of the school year the file covers | matcher |
| cms_hospitals | open | the dataset's modified date | matcher, by address |
| nppes_orgs | open | later of last update and certification date | matcher, by address |
| abc_ca | open | the export's Updated date | matcher, by address |
| abca_dc_active | open | day the layer was last loaded | matcher |
| abca_dc_cancelled | closed | day the layer was last loaded (an upper bound) | matcher; restaurants, taverns, nightclubs and clubs only |
| ncua_branches | open | the quarter's cycle date | matcher, by address |
| irs_eo | open | last day of the month the newest return covers | matcher, by address |
| atp | open | day the spider collected the chain's locator | the AllThePlaces row's own merge |
| osm_check_date | open | `check_date` or `survey:date` tag | the OSM feature's own merge |

A current list can be stale. CMS still lists United Medical Center in
Washington as of 2026-07, and OSM tags it disused with an edit dated
2026-05. The list is newer, so the place comes out open, and the closing
record stays visible in `evidence`. One case in ten hospitals read; watch
this as more lists are added.

The ATP and OSM check_date rows were not in the brief. Being listed in a chain's own locator on
a known day, and a mapper's dated survey tag, are both dated records of
life, and both come for free with the base layer. Absence from a locator is
still not evidence of anything.

## 8. Licensing

| source | license | consequence |
| --- | --- | --- |
| Overture places | CDLA-Permissive-2.0 (rows from Foursquare are Apache-2.0) | attribution |
| AllThePlaces | CC0-1.0 | none |
| Foursquare OS Places | Apache-2.0 | keep the notice, see NOTICE |
| FDIC, USDA | US federal work, public domain | none |
| Wikidata | CC0-1.0 | none |
| OpenStreetMap | ODbL-1.0 | attribution and share-alike on any derived database |

A table that contains OSM-derived rows, or values computed from OSM, is an
ODbL derived database. That reaches further than the OSM-only rows: a core
place whose status was decided by an OSM lifecycle tag, or whose phone was
filled from OSM, is OSM-derived too.

**Decision: copyleft, with separable layers.**

- The code is AGPL-3.0-or-later.
- `places-<region>.parquet` is the core plus OSM. It must be under the ODbL.
- `core-<region>.parquet` is built without reading OSM. Its inputs are all
  permissive, so its license is a choice, and the choice is the ODbL as
  well, so that anything built on the Almanac stays open.
- The core layer is still built separately. That keeps the choice open: a
  file with no OSM in it can be offered under other terms later, a file
  with OSM in it never can.
- Every row carries `sources` and `licenses`, the licenses of the inputs
  that touched it.

Open point: whether the Wikidata P576 signal belongs in the core layer.
Wikidata is CC0, but the link from place to item comes from an OSM tag, so
for now it sits in the full layer only.

`SOURCES.md` records each source's license and URL. Sources with no stated
license (many city feeds) get an entry that says so before any adapter for
them is merged.

## 9. Rejected rules

Measured in the District of Columbia box unless noted. "Independent" means
evidence from a different source for the same place.

| rule | result | why it is out |
| --- | --- | --- |
| SNAP End Date means closed | 499 places matched. Independent evidence said still open 98 times, closed 27 times. | An ended authorization is a change of owner or a store leaving the program far more often than a closing. The adapter reads these rows and emits nothing. |
| Foursquare `date_closed` matched by name and position, for rows Overture does not link by id | 2,142 places matched. Independent: open 101, closed 129. | Foursquare often closes one of its own duplicate records for a place that is still there. Joined by id the same field is good: open 6, closed 33. |
| Jaro-Winkler from 0.93 | 10 pairs read between 0.93 and 0.95: 2 wrong ("Embassy of Albania" and "Embassy of Mali"), 1 doubtful. 30 read at 0.95 and up: none wrong. | Threshold raised to 0.95. |
| Name contained anywhere in the longer name | Joined a shop to the mall it is named after, and a department to its hospital. | Only leading words count now. |
| A bank branch record matching the bank's ATM | 3 of 40 FDIC closings landed on an ATM or mortgage desk listing. | A name with ATM on one side only never matches. |
| Wikidata P576 on offices | 4 hits across two boxes, 2 of them a company merger date on an office building. | Skipped when the OSM feature is `office=*`. The 2 that remain (a hospital, a school) are right. |
| Merging Overture duplicates on anything looser than an identical name | Same house number with a leading-words or near-spelling match: about 10 of 21 read were a part and its whole (a gift shop and its hospital, two advisors at one bank). No house number: mostly junk pages sharing a point. Different numbers within 30 m: 13 pairs, several wrong. | Only same number plus identical name merges. |
| DC alcohol license cancellation means closed, for every license type | 283 places matched. Independent: open 18, closed 60. The open ones were grocery stores, hotels and places that had swapped one license for another. | Kept only for restaurants, taverns, nightclubs and clubs, and skipped when the same trade name has an active license at the address. After that: open 8, closed 54, in line with the Foursquare and OSM signals. |
| Overture operating_status as a closed verdict | 6,175 rows say permanently_closed, nearly all from one supplier, with no date. Where this build has dated evidence for them: closed 31, open 12. | No date, and wrong too often. Carried as `overture_status`, never used. |

Carried over from earlier work and not retested: website liveness, and
"missing from the chain's locator means closed".

## 10. Publishing

Per region: `core-<region>.parquet`, `places-<region>.parquet`, and
`manifest-<region>.json`. A real release has one region per state plus DC.

- GeoParquet, zstd, rows in Hilbert order, 20,000 rows per row group.
- `lat` and `lng` are ordinary double columns. A reader filtering
  `lat between .. and lng between ..` skips row groups by statistics, which
  works over HTTP range requests with DuckDB, pyarrow or GDAL. Prune on
  those, not on the geometry.
- The manifest lists the build date, the box, each source's release, and for
  each file its row count, size, license and SHA-256. It also carries the
  credit, so it travels with the data:

  | field | value |
  | --- | --- |
  | dataset | `Vela Almanac` |
  | license | `ODbL-1.0` |
  | credit | the credit line a reuser must show, as in NOTICE |
  | notice | URL of the NOTICE file with the source notices |
  | region, build_date, bbox | what was built and when |
  | sources | the release of each base source |
  | files | name, layer, license, rows, bytes, sha256 per file |
- First host: GitHub release assets, one release per monthly build. The
  largest state should come out near 200 MB, well under the 2 GB cap
  (Kentucky is 25 MB for 247,000 places).

State builds are clipped to the Census state outline (cartographic
boundary file, 1:500,000, public domain). The outline is generalized, so a
row just outside it is kept when its own address names the state and it is
within about 5 km.
