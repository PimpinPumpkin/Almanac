#!/usr/bin/env python3
"""New York City DOHMH: restaurant inspection results.

dohmh_nyc  one row per restaurant, open as of its newest inspection. An
           inspector was in the place that day. Positions come with the data.

Restaurants not yet inspected carry a placeholder date of 1900 and are left
out. The dataset drops a restaurant once it goes out of business, so there
is no closed evidence here.

NYC Open Data. https://data.cityofnewyork.us/d/43nn-pn8j
"""
import json
import os
import sys
import urllib.parse

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from evidence import Writer, address, get

ROWS = "https://data.cityofnewyork.us/resource/43nn-pn8j.json"
PAGE = 50000


def main():
    out = Writer("dohmh_nyc")
    offset = 0
    while True:
        q = {"$select": "camis,dba,building,street,boro,zipcode,latitude,longitude,max(inspection_date) as last",
             "$group": "camis,dba,building,street,boro,zipcode,latitude,longitude",
             "$having": "max(inspection_date) > '2000-01-01'",
             "$order": "camis", "$limit": PAGE, "$offset": offset}
        rows = json.loads(get(ROWS + "?" + urllib.parse.urlencode(q)))
        for r in rows:
            lat, lng = r.get("latitude"), r.get("longitude")
            if lat in (None, "0", "0.0"):
                lat = lng = None
            street = ("%s %s" % (r.get("building") or "", r.get("street") or "")).strip()
            out.row("dohmh_nyc", r["camis"], r.get("dba"),
                    address(street, (r.get("boro") or "").upper(), "NY %s" % (r.get("zipcode") or "")[:5]),
                    lat, lng, "open", (r.get("last") or "")[:10])
        offset += len(rows)
        if len(rows) < PAGE:
            break
    out.close()


if __name__ == "__main__":
    main()
