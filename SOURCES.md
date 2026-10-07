# Sources

Every source the build reads, with its license and where it is fetched from.
All are anonymous and keyless. A source is added here before its importer or
adapter is merged. If a source states no license, the entry says so.

## Base layer

### Overture Maps, places theme
- License: CDLA-Permissive-2.0. Rows that came from Foursquare are Apache-2.0
  (each row's `sources` says which).
- Fetched from: `https://overturemaps-us-west-2.s3.amazonaws.com/release/<release>/theme=places/type=place/`
- Docs: https://docs.overturemaps.org/
- Attribution: Overture Maps Foundation, overturemaps.org.
- Used for: the spine of the place table.

### OpenStreetMap, via Geofabrik state extracts
- License: ODbL-1.0. Share-alike. Anything derived from it is in the full
  layer only.
- Fetched from: `https://download.geofabrik.de/north-america/us/<state>-latest.osm.pbf`
- Attribution: (c) OpenStreetMap contributors, https://www.openstreetmap.org/copyright
- Used for: named businesses and landmarks, lifecycle tags (closed),
  `check_date` tags (open), `wikidata` links.

### AllThePlaces
- License: CC0-1.0.
- Fetched from: `https://data.alltheplaces.xyz/runs/latest.json`, then the
  run's `output.zip`. The `parquet_url` in that file returns 404 as of
  2026-10; the zip is what works.
- Site: https://www.alltheplaces.xyz/
- Used for: chain locations (brand lineage spiders only), and open evidence
  dated the day the spider ran.

## Evidence

### Foursquare OS Places
- License: Apache-2.0. See NOTICE.
- Fetched from: `https://data.source.coop/fused/fsq-os-places/2025-02-06/places/<0..80>.parquet`
  (an anonymous mirror of the 2025-02-06 release).
- Newer releases need a Foursquare account. `signals/fsq_closed.sh` takes
  `FSQ_PLACES_GLOB` and `FSQ_RELEASE` for that; no token is stored in the repo.
- Used for: `date_closed`, joined on the Foursquare id Overture carries.

### Wikidata
- License: CC0-1.0.
- Fetched from: `https://query.wikidata.org/sparql`
- Used for: P576 on items linked from OSM features.

### FDIC BankFind Suite
- License: US federal government work, public domain.
- Fetched from: `https://api.fdic.gov/banks/locations` and
  `https://api.fdic.gov/banks/history` (change code 721, branch closing).
- Docs: https://api.fdic.gov/banks/docs/
- Used for: open bank branches, dated branch closings.

### USDA SNAP retailer data
- License: US federal government work, public domain.
- Fetched from: the historical file linked on
  https://www.fns.usda.gov/snap/retailer/historical-data and the live layer at
  `https://services1.arcgis.com/RLQu0rK7h4kbsBq5/arcgis/rest/services/snap_retailer_location_data/FeatureServer/0`
- Used for: stores currently authorized (open). End dates are not used; see
  SPEC.md section 9.

### CMS Hospital General Information
- License: US federal government work, public domain.
- Fetched from: the CSV named in
  `https://data.cms.gov/provider-data/api/1/metastore/schemas/dataset/items/xubh-q36u`
- Used for: Medicare-registered hospitals (open). No positions; matched by address.

### NCES public school locations (EDGE geocodes)
- License: US federal government work, public domain.
- Fetched from: `https://nces.ed.gov/programs/edge/data/EDGE_GEOCODE_PUBLICSCH_<years>.zip`
- Used for: public schools that operated in the file's school year (open).

### NPPES, the National Provider Identifier registry
- License: US federal government work, public domain.
- Fetched from: the monthly file linked on https://download.cms.gov/nppes/NPI_Files.html
- Used for: health care organizations (open, dated by the last update or
  certification). No positions; matched by address.

### IRS Exempt Organizations Business Master File
- License: US federal government work, public domain.
- Fetched from: `https://www.irs.gov/pub/irs-soi/eo1.csv` to `eo4.csv`
- Used for: nonprofits that filed a return (open, dated by the tax period).
  No positions; matched by address.

### US Census cartographic boundary file, states
- License: US federal government work, public domain.
- Fetched from: `https://www2.census.gov/geo/tiger/GENZ2023/shp/cb_2023_us_state_500k.zip`
- Used for: clipping state builds to the state outline. Not evidence.

## Not used yet

Survey of what comes next, in order. None of these has been fetched or
checked by this project.

- NCUA credit union branches: federal, public domain.
- State alcohol license lists (California, Texas, New York, Colorado,
  Missouri, Oregon) and Florida restaurant and hotel licenses: license terms
  to be read per state.
- Health inspections and city business licenses: many city portals state no
  license. Each one gets an entry here saying what it states before it is used.
- OpenPOIs (https://github.com/henryspatialanalysis/openpois): data under the
  ODbL. Its per-place confidence, modeled from OSM edit history, is a
  candidate input to `open_score`.
