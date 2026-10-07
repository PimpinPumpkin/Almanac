#!/usr/bin/env python3
"""District of Columbia: Basic Business Licenses.

bbl_dc  an active license for premises in DC that carries a trade name and
        is not a housing rental, open as of the day the data was refreshed.

Most rows in this dataset are rentals or sole proprietors under their own
names. Only rows with a trade name are read, and only the trade name, the
premises address: never the owner, agent or billing fields. Nothing here
creates a place. Addresses go to the Census geocoder.

CC-BY-4.0, as stated on opendata.dc.gov. Attribution is in NOTICE.
https://opendata.dc.gov (Basic Business Licenses)
"""
import datetime
import json
import os
import sys
import urllib.parse

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from evidence import Writer, get

LAYER = "https://maps2.dcgis.dc.gov/dcgis/rest/services/FEEDS/DCRA/FeatureServer/0"
PAGE = 2000
WHERE = ("LICENSESTATUS = 'Active' AND PREMISEINDC = 'Yes' AND ENTITYTRADENAME IS NOT NULL "
         "AND CATEGORYSERVICETYPE NOT IN ('Housing and Lodging Services', 'Short Term/Vacation Rental')")


def main():
    out = Writer("bbl_dc")
    seen, offset = set(), 0
    while True:
        q = {"where": WHERE, "outFields": "CUSTOMERNUMBER,ENTITYTRADENAME,PREMISEADDRESS,DATAREFRESHEDON",
             "orderByFields": "OBJECTID", "returnGeometry": "false", "resultOffset": offset, "resultRecordCount": PAGE, "f": "json"}
        feats = json.loads(get(LAYER + "/query?" + urllib.parse.urlencode(q))).get("features", [])
        for f in feats:
            a = f["attributes"]
            name = (a.get("ENTITYTRADENAME") or "").strip()
            # "916 G ST NW, Washington, DC, 20001, USA" -> "916 G ST NW, Washington, DC 20001"
            parts = [p.strip() for p in (a.get("PREMISEADDRESS") or "").split(",")]
            if len(parts) < 4 or not name:
                out.drop("no trade name or address")
                continue
            where = "%s, %s, %s %s" % (parts[0], parts[1], parts[2], parts[3][:5])
            # one business holds a license per activity
            if (name.upper(), where.upper()) in seen:
                continue
            seen.add((name.upper(), where.upper()))
            day = datetime.datetime.fromtimestamp(a["DATAREFRESHEDON"] / 1000, datetime.timezone.utc).date().isoformat()
            out.row("bbl_dc", a["CUSTOMERNUMBER"], name, where.upper(), None, None, "open", day)
        offset += len(feats)
        if len(feats) < PAGE:
            break
    out.close(geocode=True)


if __name__ == "__main__":
    main()
