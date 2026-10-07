#!/usr/bin/env python3
"""Wisconsin Department of Revenue: retail alcohol beverage licenses.

dor_wi_liquor  a retail license (Class A, B or C) that has not expired,
               open as of the day its record was last updated.

Municipal clerks report these to the state once a year, so a record can be
months old; its own update date is used, not today's. The agent's name is
not read. The file has no license numbers, so a row's id is a hash of its
name and address. No positions; addresses go to the Census geocoder.

Wisconsin public record. No license stated.
https://www.revenue.wi.gov/Pages/OnlineServices/retail-alcohol-beverage-license-search.aspx
"""
import csv
import hashlib
import io
import datetime
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from evidence import Writer, address, get

URL = ("https://ww2.revenue.wi.gov/WebServicesPublicWeb/rest/liquor/all?search=&city=&rn_low=0&rn_high=2147483647"
       "&sort=0&AB=0&AC=0&AL=0&BB=0&BL=0&CW=0&csv=true")


def main():
    today = datetime.date.today().isoformat()
    out = Writer("dor_wi_liquor")
    seen = set()
    for r in csv.DictReader(io.StringIO(get(URL).decode("cp1252", "replace"))):
        if (r.get("Expiration") or "") < today or r.get("State") != "WI":
            out.drop("expired or not in Wisconsin")
            continue
        name = (r.get("BusinessName") or r.get("LegalName") or "").strip()
        where = address(r.get("BusinessAddress"), r.get("City"), "WI %s" % (r.get("Zip") or "")[:5])
        key = hashlib.sha1(("%s|%s" % (name, where)).upper().encode()).hexdigest()[:16]
        if key in seen:
            continue
        seen.add(key)
        out.row("dor_wi_liquor", key, name, where, None, None, "open", (r.get("LastUpdated") or "")[:10])
    out.close(geocode=True)


if __name__ == "__main__":
    main()
