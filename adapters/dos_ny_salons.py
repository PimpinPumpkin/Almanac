#!/usr/bin/env python3
"""New York Department of State: licensed salons and barber shops.

dos_ny_salons  an appearance enhancement business or barber shop whose
               license has not expired, open as of the day the dataset was
               last updated. Positions come with the data.

Area renters (a person renting a chair inside a shop) are left out, and the
license holder's name is not read; only the business name is.

OPEN-NY Terms of Use (see SOURCES.md).
https://data.ny.gov/d/y3u4-jbgh
"""
import datetime
import json
import os
import sys
import urllib.parse

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from evidence import Writer, address, get

VIEW = "https://data.ny.gov/api/views/y3u4-jbgh.json"
ROWS = "https://data.ny.gov/resource/y3u4-jbgh.json"
PAGE = 50000
SHOPS = "('DOSAEBUSINESS', 'DOSBARSHOPOWNER')"
FIELDS = "license_number,business_name,business_address_1,business_city,business_zip,georeference"


def main():
    today = datetime.date.today().isoformat()
    updated = datetime.datetime.fromtimestamp(
        json.loads(get(VIEW))["rowsUpdatedAt"], datetime.timezone.utc).date().isoformat()
    out = Writer("dos_ny_salons")
    offset = 0
    while True:
        q = {"$select": FIELDS,
             "$where": "license_type in %s AND business_state = 'NY' AND license_expiration_date > '%s'" % (SHOPS, today),
             "$limit": PAGE, "$offset": offset, "$order": "license_number"}
        rows = json.loads(get(ROWS + "?" + urllib.parse.urlencode(q)))
        for r in rows:
            lng, lat = (r.get("georeference") or {}).get("coordinates") or (None, None)
            out.row("dos_ny_salons", r["license_number"], r.get("business_name"),
                    address(r.get("business_address_1"), r.get("business_city"), "NY %s" % (r.get("business_zip") or "")[:5]),
                    lat, lng, "open", updated)
        offset += len(rows)
        if len(rows) < PAGE:
            break
    out.close()


if __name__ == "__main__":
    main()
