#!/usr/bin/env python3
"""Pennsylvania Department of Revenue: tobacco products tax licenses.

rev_pa_tobacco  a current retail cigarette or tobacco license at a
                Pennsylvania address, open as of the day the dataset was
                last updated. The trade name is used; the legal name, often
                a person, is not read.

Wholesalers, manufacturers and vending machine licenses are left out.
Account numbers are masked in the file, so a row's id is a hash of its name
and address. Rows without a position go to the Census geocoder.

Public domain, as stated on the dataset.
https://data.pa.gov/d/ut72-sft8
"""
import datetime
import hashlib
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from evidence import Writer, address
from socrata import point, rows, updated

HOST, DATASET = "data.pa.gov", "ut72-sft8"


def main():
    today = datetime.date.today().isoformat()
    as_of = updated(HOST, DATASET)
    out = Writer("rev_pa_tobacco")
    seen = set()
    for r in rows(HOST, DATASET,
                  where="license_type like '%%Retail%%' AND state = 'PA' AND expiration_date > '%s'" % today,
                  select="trade_name,street_address,city,postal_code,georeferenced_latitude_longitude"):
        name, street = (r.get("trade_name") or "").strip(), (r.get("street_address") or "").strip()
        if not name or not street:
            out.drop("no trade name or street")
            continue
        key = hashlib.sha1(("%s|%s|%s" % (name, street, r.get("postal_code"))).upper().encode()).hexdigest()[:16]
        if key in seen:
            continue
        seen.add(key)
        lat, lng = point(r.get("georeferenced_latitude_longitude"))
        out.row("rev_pa_tobacco", key, name,
                address(street, (r.get("city") or "").upper(), "PA %s" % (r.get("postal_code") or "")[:5]),
                lat, lng, "open", as_of)
    out.close(geocode=True)


if __name__ == "__main__":
    main()
