#!/usr/bin/env python3
"""Washington Department of Licensing: vehicle and vessel dealer licenses.

dol_wa  an active dealer license (cars, motorcycles and other vehicles,
        boats, off-road vehicles, snowmobiles, manufactured homes and
        trailers, and their branch lots), open as of the day the dataset
        was last updated.

Transporters, for-hire and limousine carriers, tow operators, wholesalers,
wreckers and manufacturers are left out: they are not shops. Only the
location's name and address are read. No positions; addresses go to the
Census geocoder.

Open Database License, as stated on the dataset.
https://data.wa.gov/d/ucdg-xgbj
"""
import datetime
import hashlib
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from evidence import Writer, address
from socrata import point, rows, updated

HOST, DATASET = "data.wa.gov", "ucdg-xgbj"


def main():
    as_of = updated(HOST, DATASET)
    out = Writer("dol_wa")
    where = ("license_status = 'Active' AND location_state = 'WA' AND license_type like '%Dealer%' "
             "AND license_type not like '%Wholesaler%'")
    for r in rows(HOST, DATASET, where=where,
                  select="license_type,license_number,location_name,location_street,location_city,location_postal_code"):
        # a license number covers every lot of the same dealer
        lot = hashlib.sha1((r.get("location_street") or "").upper().encode()).hexdigest()[:8]
        out.row("dol_wa", "%s-%s-%s" % (r.get("license_type"), r.get("license_number"), lot), r.get("location_name"),
                address(r.get("location_street"), r.get("location_city"), "WA %s" % (r.get("location_postal_code") or "")[:5]),
                None, None, "open", as_of)
    out.close(geocode=True)


if __name__ == "__main__":
    main()
