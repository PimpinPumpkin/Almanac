#!/usr/bin/env python3
"""New York DMV: licensed repair shops, inspection stations and dealers.

dmv_ny  a facility whose registration has not expired, open as of the day
        the dataset was last updated. Covers repair and body shops,
        inspection stations and vehicle dealers. Positions come with the data.

The file names each facility's owner; that field is not read. Expired
registrations are skipped: there is no way to tell a closed shop from a
late renewal.

OPEN-NY Terms of Use (see SOURCES.md).
https://data.ny.gov/d/nhjr-rpi2
"""
import datetime
import json
import os
import sys
import urllib.parse

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from evidence import Writer, address, get

VIEW = "https://data.ny.gov/api/views/nhjr-rpi2.json"
ROWS = "https://data.ny.gov/resource/nhjr-rpi2.json"
PAGE = 50000
FIELDS = "facility,facility_name,facility_name_overflow,facility_street,facility_city,facility_zip_code,expiration_date,georeference"


def main():
    today = datetime.date.today()
    updated = datetime.datetime.fromtimestamp(
        json.loads(get(VIEW))["rowsUpdatedAt"], datetime.timezone.utc).date().isoformat()
    out = Writer("dmv_ny")
    seen, offset = set(), 0
    while True:
        q = {"$select": FIELDS, "$where": "facility_state = 'NY'", "$limit": PAGE, "$offset": offset,
             "$order": "facility"}
        rows = json.loads(get(ROWS + "?" + urllib.parse.urlencode(q)))
        for r in rows:
            try:
                expires = datetime.datetime.strptime(r.get("expiration_date") or "", "%m/%d/%Y").date()
            except ValueError:
                out.drop("no expiration date")
                continue
            if expires < today:
                out.drop("registration expired")
                continue
            # one facility holds several registrations (repair shop, inspection station)
            if r["facility"] in seen:
                continue
            seen.add(r["facility"])
            lng, lat = (r.get("georeference") or {}).get("coordinates") or (None, None)
            name = ("%s %s" % (r.get("facility_name") or "", r.get("facility_name_overflow") or "")).strip()
            out.row("dmv_ny", r["facility"], name,
                    address(r.get("facility_street"), r.get("facility_city"), "NY %s" % (r.get("facility_zip_code") or "")[:5]),
                    lat, lng, "open", updated)
        offset += len(rows)
        if len(rows) < PAGE:
            break
    out.close()


if __name__ == "__main__":
    main()
