#!/usr/bin/env python3
"""USDA SNAP retailers: stores authorized to take SNAP, as open evidence.

snap_current  the live retailer locator layer, open as of its last data edit.
snap_history  the historical file, only stores whose newest authorization
              period has no end date: open as of the last day the file covers.

Ended authorizations are read but not emitted. An End Date is not a closing
date: a store can leave the program and keep trading, and a change of owner
ends one Record ID and starts another at the same address. Measured in the
District of Columbia box, 499 places matched an ended authorization; where
an independent source also had a view, it said "still open" 98 times and
"closed" 27 times. See SPEC.md, rejected rules.

Public domain (US federal government work).
https://www.fns.usda.gov/snap/retailer/historical-data
"""
import csv
import datetime
import io
import json
import os
import re
import sys
import urllib.parse
import zipfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from evidence import CACHE, Writer, address, download, get

PAGE_URL = "https://www.fns.usda.gov/snap/retailer/historical-data"
LAYER = ("https://services1.arcgis.com/RLQu0rK7h4kbsBq5/arcgis/rest/services/"
         "snap_retailer_location_data/FeatureServer/0")


def mdy(s):
    """5/8/2006 -> 2006-05-08, blank -> None"""
    s = (s or "").strip()
    if not s:
        return None
    m, d, y = s.split("/")
    return "%04d-%02d-%02d" % (int(y), int(m), int(d))


def history(out):
    page = get(PAGE_URL).decode("utf-8", "replace")
    link = re.search(r'href="([^"]*snap-retailer-locator-data\d{4}-(\d{4})\.zip)"', page)
    if not link:
        raise SystemExit("historical zip link not found on " + PAGE_URL)
    url = urllib.parse.urljoin(PAGE_URL, link.group(1))
    as_of = "%s-12-31" % link.group(2)
    path = download(url, os.path.join(CACHE, "snap", os.path.basename(url)))

    newest = {}
    with zipfile.ZipFile(path) as z:
        with z.open(z.namelist()[0]) as f:
            for r in csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig")):
                start = mdy(r["Authorization Date"]) or ""
                rid = r["Record ID"]
                if rid not in newest or start > newest[rid][0]:
                    newest[rid] = (start, r)

    for rid, (start, r) in newest.items():
        if mdy(r["End Date"]):
            out.drop("authorization ended (not evidence, see docstring)")
            continue
        street = ("%s %s" % (r["Street Number"].strip(), r["Street Name"].strip())).strip()
        out.row("snap_history", rid, r["Store Name"],
                address(street, r["City"], "%s %s" % (r["State"].strip(), r["Zip Code"].strip())),
                r["Latitude"], r["Longitude"],
                "open", as_of)


def current(out):
    info = json.loads(get(LAYER + "?f=json"))
    edited = datetime.datetime.fromtimestamp(
        info["editingInfo"]["dataLastEditDate"] / 1000, datetime.timezone.utc).date().isoformat()
    size = info["maxRecordCount"]
    offset = 0
    while True:
        q = {"where": "1=1", "orderByFields": "ObjectId", "outSR": 4326, "f": "json",
             "outFields": "Record_ID,Store_Name,Store_Street_Address,City,State,Zip_Code,Latitude,Longitude",
             "returnGeometry": "false", "resultOffset": offset, "resultRecordCount": size}
        body = json.loads(get(LAYER + "/query?" + urllib.parse.urlencode(q)))
        feats = body.get("features", [])
        for f in feats:
            a = f["attributes"]
            out.row("snap_current", a["Record_ID"], a["Store_Name"],
                    address(a["Store_Street_Address"], a["City"], "%s %s" % (a["State"] or "", a["Zip_Code"] or "")),
                    a["Latitude"], a["Longitude"], "open", edited)
        offset += len(feats)
        if not feats or not body.get("exceededTransferLimit"):
            return


def main():
    out = Writer("snap")
    history(out)
    current(out)
    out.close()


if __name__ == "__main__":
    main()
