#!/usr/bin/env python3
"""Pennsylvania Department of Revenue: retail sales tax licenses.

rev_pa  a current retail sales license at a Pennsylvania address, open as of
        the day the dataset was last updated. The trade name is used; the
        legal name, often a person, is not read.

Wholesale licenses, transient vendors, promoters and exemption certificates
are left out. The file has no trade classification, so it holds people who
sell from home along with shops: rows are evidence for places that are
already listed, and nothing here creates a place. Account numbers are
masked in the file, so a row's id is a hash of its name and address. Rows
without a position go to the Census geocoder.

Public domain, as stated on the dataset.
https://data.pa.gov/d/ugeq-ckxd
"""
import datetime
import hashlib
import json
import os
import sys
import urllib.parse

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from evidence import Writer, address, get

VIEW = "https://data.pa.gov/api/views/ugeq-ckxd.json"
ROWS = "https://data.pa.gov/resource/ugeq-ckxd.json"
PAGE = 50000
FIELDS = "trade_name,street_address,city,postal_code,georeferenced_latitude_longitude_points"


def main():
    today = datetime.date.today().isoformat()
    updated = datetime.datetime.fromtimestamp(
        json.loads(get(VIEW))["rowsUpdatedAt"], datetime.timezone.utc).date().isoformat()
    out = Writer("rev_pa")
    seen, offset = set(), 0
    while True:
        q = {"$select": FIELDS,
             "$where": "license_type = 'Sales License/Retail' AND state = 'PA' AND expiration_date > '%s'" % today,
             "$limit": PAGE, "$offset": offset, "$order": ":id"}
        rows = json.loads(get(ROWS + "?" + urllib.parse.urlencode(q)))
        for r in rows:
            name, street = (r.get("trade_name") or "").strip(), (r.get("street_address") or "").strip()
            if not name or not street:
                out.drop("no trade name or street")
                continue
            key = hashlib.sha1(("%s|%s|%s" % (name, street, r.get("postal_code"))).upper().encode()).hexdigest()[:16]
            if key in seen:
                continue
            seen.add(key)
            lng, lat = (r.get("georeferenced_latitude_longitude_points") or {}).get("coordinates") or (None, None)
            out.row("rev_pa", key, name,
                    address(street, (r.get("city") or "").upper(), "PA %s" % (r.get("postal_code") or "")[:5]),
                    lat, lng, "open", updated)
        offset += len(rows)
        if len(rows) < PAGE:
            break
    out.close(geocode=True)


if __name__ == "__main__":
    main()
