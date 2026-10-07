#!/usr/bin/env python3
"""AllThePlaces run archive -> CSV on stdout, US brand locations only.

The archive holds one GeoJSON file per spider, one feature per line. Only
spiders in the brand lineage are read; the government and infrastructure
spiders list things like bus stops that are not places in this dataset's
sense. Lines are screened by coordinates with a regex before JSON parsing.
"""
import csv
import json
import re
import sys
import zipfile

HEAD = re.compile(rb'"spider:collection_time":\s*"(\d{4}-\d{2}-\d{2})')
POINT = re.compile(rb'"type":\s*"Point",\s*"coordinates":\s*\[(-?[\d.]+),\s*(-?[\d.]+)\]')
MAIN = ("amenity", "shop", "tourism", "leisure", "office", "craft", "healthcare")
COLUMNS = ["spider", "ref", "name", "branch", "brand", "brand_wikidata", "category", "address",
           "housenumber", "city", "region", "postcode", "phone", "website", "collected",
           "end_date", "lat", "lng"]


def main(path):
    out = csv.writer(sys.stdout)
    out.writerow(COLUMNS)
    with zipfile.ZipFile(path) as z:
        for member in z.namelist():
            if not member.endswith(".geojson"):
                continue
            with z.open(member) as f:
                head = f.readline()
                if b'"S_ATP_BRANDS"' not in head:
                    continue
                m = HEAD.search(head)
                collected = m.group(1).decode() if m else ""
                for line in f:
                    m = POINT.search(line)
                    if not m:
                        continue
                    lng, lat = float(m.group(1)), float(m.group(2))
                    if not (17 < lat < 72 and -180 < lng < -64):
                        continue
                    try:
                        p = json.loads(line.rstrip().rstrip(b","))["properties"]
                    except ValueError:
                        continue
                    if p.get("addr:country") not in (None, "US"):
                        continue
                    name = p.get("name") or p.get("brand")
                    if not name:
                        continue
                    category = next(("%s=%s" % (k, p[k]) for k in MAIN if p.get(k)), "")
                    street = p.get("addr:street_address") or " ".join(
                        x for x in (p.get("addr:housenumber"), p.get("addr:street")) if x) or p.get("addr:full") or ""
                    out.writerow([
                        p.get("@spider", ""), p.get("ref", ""), name, p.get("branch", ""), p.get("brand", ""),
                        p.get("brand:wikidata", ""), category, street, p.get("addr:housenumber", ""),
                        p.get("addr:city", ""), p.get("addr:state", ""), p.get("addr:postcode", ""),
                        p.get("phone", ""), p.get("website", ""), collected, p.get("end_date", ""),
                        "%.6f" % lat, "%.6f" % lng])


if __name__ == "__main__":
    main(sys.argv[1])
