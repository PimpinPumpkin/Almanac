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

### OpenPOIs (Henry Spatial Analysis)
- License: ODbL-1.0 for the data. Full layer only.
- Fetched from: `https://s3.us-west-2.amazonaws.com/us-west-2.opendata.source.coop/henryspatialanalysis/openpois/latest/conflated-parquet/`
- Project: https://github.com/henryspatialanalysis/openpois
- Used for: OSM edit history events matched to Overture places (closed),
  and its confidence as the open score of places with no other evidence,
  when 0.80 or more. US only.

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

### EPA UST Finder
- License: US federal government work, public domain.
- Fetched from: `https://services.arcgis.com/cJ9YHowT8TU7DUyn/arcgis/rest/services/UST_Finder_Feature_Layer_2/FeatureServer`
- Used for: sites with underground fuel tanks in use (open). The layer was
  last edited in December 2024.

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

### NCUA quarterly call report data
- License: US federal government work, public domain.
- Fetched from: `https://ncua.gov/files/publications/analysis/call-report-data-<year>-<month>.zip`
- Used for: credit union offices (open, dated by the quarter). No positions;
  matched by address.

### IRS Exempt Organizations Business Master File
- License: US federal government work, public domain.
- Fetched from: `https://www.irs.gov/pub/irs-soi/eo1.csv` to `eo4.csv`
- Used for: nonprofits that filed a return (open, dated by the tax period).
  No positions; matched by address.

### California ABC daily license export
- License: none stated on the download page. California public record.
- Fetched from: `https://www.abc.ca.gov/wp-content/uploads/DailyExport-CSV.zip`,
  linked on https://www.abc.ca.gov/licensing/licensing-reports/
- Used for: active retail alcohol licenses (open), with positions from the
  Census geocoder. The file gives no date for surrenders or revocations, so
  there is no closed evidence from it.

### New York City DOHMH, restaurant inspection results
- License: none named on the dataset. NYC Open Data, a city public record;
  rows it touches are marked `NYC-Open-Data-terms`.
- Fetched from: `https://data.cityofnewyork.us/resource/43nn-pn8j.json`
- Used for: restaurants by newest inspection (open), with positions. Also
  mints missing places.

### Chicago Department of Public Health, food inspections
- License: "See Terms of Use" of the City of Chicago Data Portal; rows it
  touches are marked `Chicago-Data-Portal-terms`.
- Fetched from: `https://data.cityofchicago.org/resource/4ijn-s7e5.json`
- Used for: food businesses by newest inspection (open), and the "Out of
  Business" result (closed, places with no brand only). Positions come
  with the data. Also mints missing places.

### Colorado Liquor Enforcement Division, liquor licenses
- License: public domain, as stated on the dataset.
- Fetched from: `https://data.colorado.gov/resource/ier5-5ms2.json`
- Used for: active premises licenses (open). The list of recently expired
  and surrendered licenses is not used.

### Florida DBPR, alcoholic beverage licenses
- License: none stated on the download page. Florida public record. Rows it
  touches are marked `none-stated`.
- Fetched from: `https://www2.myfloridalicense.com/sto/file_download/extracts/bd400lic.csv`
- Used for: current retail beverage licenses (open), with positions from
  the Census geocoder.

### Florida DBPR, food service inspections
- License: none stated on the download page. Florida public record. Rows it
  touches are marked `none-stated`.
- Fetched from: `https://www2.myfloridalicense.com/sto/file_download/extracts/<1..7>fdinspi.csv`,
  linked on https://www2.myfloridalicense.com/hotels-restaurants/public-records/
- Used for: restaurants inspected in the current fiscal year (open, dated
  by the inspection), with positions from the Census geocoder.

### Texas Alcoholic Beverage Commission, license information
- License: none stated by the dataset or by data.texas.gov. Texas public
  record. Rows it touches are marked `none-stated`.
- Fetched from: `https://data.texas.gov/resource/7hf9-qc9f.json`
- Used for: active retail licenses (open). Ended licenses are not used; see
  SPEC.md section 9.

### US Census Bureau geocoder
- License: US federal government work, public domain.
- Fetched from: `https://geocoding.geo.census.gov/geocoder/locations/addressbatch`
- Used for: positions for register rows that have only an address
  (California and Texas licenses).

### New York State Liquor Authority, active licenses
- License: OPEN-NY Terms of Use (2013). Free reuse for any lawful purpose,
  no attribution or share-alike required. The license is revocable by the
  State and comes with an indemnity clause; it is not a standard open
  license.
- Fetched from: `https://data.ny.gov/resource/9s3h-dpkz.json`
- Used for: active licenses with a premises (open), with positions. Also
  mints missing places and drives the missing-license flag in New York.

### District of Columbia ABCA liquor licenses
- License: CC-BY-4.0, as stated on opendata.dc.gov. Attribution is in NOTICE.
  Open question: whether CC-BY-4.0 data may sit inside an ODbL database
  without a waiver. OpenStreetMap asks for one. Only the status and its date
  are taken from this source, not the listing itself.
- Fetched from: layers 5 (locations) and 42 (cancellations) of
  `https://maps2.dcgis.dc.gov/dcgis/rest/services/DCGIS_DATA/Business_Licensing_and_Grants_WebMercator/FeatureServer`
- Used for: active licenses (open) and cancellations (closed, for
  restaurants, taverns, nightclubs and clubs).

### France: SIRENE (INSEE)
- License: Licence Ouverte 2.0 (Etalab). Attribution: "INSEE, base Sirene",
  with the date of the file. Generally treated as compatible with the ODbL;
  not checked with a lawyer.
- Fetched from: the monthly parquet files listed at
  https://www.data.gouv.fr/datasets/base-sirene-des-entreprises-et-de-leurs-etablissements-siren-siret
  read in place over HTTP.
- Used for: active establishments (open, dated by the last change to the
  entry). Closed establishments are not used; see SPEC.md section 9.
- Privacy: only rows marked freely diffusible are read, and a sole trader's
  row only when it carries a shop sign. Nothing creates a place from it.

### US Census cartographic boundary file, states
- License: US federal government work, public domain.
- Fetched from: `https://www2.census.gov/geo/tiger/GENZ2023/shp/cb_2023_us_state_500k.zip`
- Used for: clipping state builds to the state outline. Not evidence.

## Not used yet

Survey of what comes next, in order. None of these has been fetched or
checked by this project.

- More state alcohol license lists. Found, not yet built: Oregon
  (data.oregon.gov, srxe-qkm2), Missouri (data.mo.gov, including a list of
  licenses out of business, nytw-fmz3), Washington (data.wa.gov, 9dee-kzm5).
- Florida also publishes new food licenses and changes of owner by fiscal
  year, and lodging inspections.
- Health inspections and city business licenses: many city portals state no
  license. Each one gets an entry here saying what it states before it is used.
