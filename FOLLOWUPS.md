# To circle back on

Sources that exist and could not be used yet, and what would unblock each.
Newest findings first within a group. SOURCES.md has the addresses.

## Needs someone to ask

- **Maricopa County, Arizona: food permits** (105,000, with positions; all
  of Phoenix). The layer's terms say county internal use only, and that
  outside use needs written authorization from the county GIS office.
  Ask for it.
- **Virginia Beach business licenses** (42,000). The terms were not read
  in full; read them, and ask if they are unclear.
- **Indiana alcohol licenses**: sold per record. **Utah DOPL lists** and
  **Oregon Board of Pharmacy**: paid list services. Ask whether a free
  copy is possible for an open dataset.
- **Georgia child care (DECAL)**: the export button needs the site's own
  token. Ask for a file.

## The site turns the project's fetches away

Nothing is done to get around these. They may open up, or answer a request.

- **Massachusetts ABCC** active retail licenses (.xls): "Not allowed" on
  the second fetch.
- **Michigan MLCC** weekly license spreadsheet: 403.
- **Virginia ABC** license search: 403.
- **Arizona DLLC** license query: challenge page.
- **Alaska AMCO** and Alaska business license downloads: 403.
- **Kansas Department of Agriculture**, **Rhode Island DOH lists**,
  **Colorado DORA roster generator**, **New Hampshire liquor**: 403.

## Stale, check again later

- **Albuquerque business registrations**: export stopped at 2025-08-30.
- **Anchorage food inspections**: stopped advancing in May 2026.
- **Arizona child care layer**: last run February 2025 (used, with that date).
- **Maryland child care**: May 2024 snapshot. **Kentucky child care**:
  layer stops at exactly 2,001 rows.
- **Colorado tobacco licenses**: one unexpired row of 4,910.
- **Hawaii food establishments**: 2011 and 2020 files.
- **Kansas City, Providence, Baltimore** city files: years old.
- **Sioux Falls alcohol licenses**: no dates in the layer at all.
- **Southern Nevada restaurant inspections**: rows have no names.
- **Newark, New Jersey open data portal**: answered 503 throughout.
- **Ohio liquor permit lookup**: connection resets.

## Search forms not crawled yet

- **Pennsylvania's local health departments** (Philadelphia, Allegheny,
  Chester, Erie and about a hundred more). The state lookup has a
  jurisdiction list for them; the reader only gets the Department of
  Agriculture's 43,000 establishments so far. Philadelphia box: 200 rows.
- **South Dakota inside Sioux Falls** is the city's own list (already read);
  the state list has almost nothing there, as expected.
- **Wyoming food inspections** (`wda.safefoodinspection.com`): the same
  system as eight states already read, but every search answers with a
  server error. Try again later.
- **Georgia restaurants** (`ga.healthinspections.us`): an open data feed,
  five establishments a request, so several thousand requests. Fits the
  slow workflow.
- **Kentucky restaurants**, **Illinois counties**, **Salt Lake County** on
  `public.cdpehs.com` (the same vendor as North Carolina, different pages).
- **Alabama, Mississippi, Oklahoma, Maine** state restaurant score sites.
- **Minnesota AGED** liquor license lookup (a JavaScript app).
- **Illinois ILCC** license lookup (a Salesforce site).
- **Anchorage** and **Columbus**-style county portals (one request lists
  every facility, but dates need a request per facility).
- **Missouri professional registration downloads** (moved to a Salesforce page).
- **South Carolina, Louisiana, Mississippi** alcohol license searches.

## Closed portals (403 or a challenge page), nothing to do but ask

- **inspections.myhealthdepartment.com**: Tennessee and Virginia
  restaurants, Hawaii, Oregon, Cuyahoga County, El Paso and Weld County
  CO, Orange County CA and more.
- **Riverside, Santa Clara, St. Louis County, Baltimore County, Louisiana,
  Rhode Island, New Hampshire** restaurant lookups.

## Held signals waiting for enough months to test

- Records that vanish from a register between runs (`vanished.csv`).
- Missouri "out of business" alcohol licenses, Colorado expired and
  surrendered licenses.
- Pennsylvania licenses in safekeeping. First look, Philadelphia box: of
  23 that matched a place, other sources called 3 closed and 9 open.
- California delinquent salon and repair shop licenses (not collected yet).

## Low priority, known to work

- **Clinical laboratories** (CMS CLIA, 300,000 rows, no positions).
