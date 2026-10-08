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

- **Minnesota AGED** liquor license lookup.
- **Illinois ILCC** license lookup (a Salesforce site).
- **Tennessee retail food list** (657 pages; robots.txt disallows the site).
- **Restaurant inspection portals** shared by several states and counties.
- **Missouri professional registration downloads** (moved to a Salesforce page).
- **South Carolina, Louisiana, Mississippi** alcohol license searches.

## Held signals waiting for enough months to test

- Records that vanish from a register between runs (`vanished.csv`).
- Missouri "out of business" alcohol licenses, Colorado expired and
  surrendered licenses.
- Pennsylvania licenses in safekeeping. First look, Philadelphia box: of
  23 that matched a place, other sources called 3 closed and 9 open.
- California delinquent salon and repair shop licenses (not collected yet).

## Low priority, known to work

- **Clinical laboratories** (CMS CLIA, 300,000 rows, no positions).
