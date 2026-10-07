#!/usr/bin/env python3
"""Connecticut Department of Motor Vehicles: licensed dealers and repairers.

dmv_ct  an unexpired license for a new or used car dealer, a general
        repairer or a recycler at a Connecticut address, open as of the day
        the dataset was last updated.

Leasing companies, manufacturers and registration-only licenses are left
out. A license has one row for each name it trades under, and some of
those names are people: every name is a row of its own, rows are evidence
for places that are already listed, and nothing here creates a place. Rows
without a position go to the Census geocoder.

Public domain, as stated on the dataset.
https://data.ct.gov/d/apne-w8c6
"""
import datetime
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from evidence import Writer, address
from socrata import point, rows, updated

HOST, DATASET = "data.ct.gov", "apne-w8c6"


def main():
    today = datetime.date.today().isoformat()
    as_of = updated(HOST, DATASET)
    out = Writer("dmv_ct")
    where = ("state = 'CT' AND license_type IN ('GENERAL REPAIRER', 'NEW DEALER', 'USED DEALER', 'RECYCLER') "
             "AND license_expiration > '%s'" % today)
    seen = {}
    for r in rows(HOST, DATASET, where=where, order="license_num, business_name"):
        name = (r.get("business_name") or "").strip()
        if name.upper().startswith("DBA "):
            name = name[4:]
        n = seen[r.get("license_num")] = seen.get(r.get("license_num"), 0) + 1
        lat, lng = point(r.get("geocoded_column"))
        # "RT 32" with the street address in the note
        street = r.get("note") if (r.get("note") or "")[:1].isdigit() else r.get("business_address")
        out.row("dmv_ct", "%s-%d" % (r.get("license_num"), n), name,
                address(street, r.get("city"), "CT %s" % (r.get("zip_code") or "")[:5]), lat, lng, "open", as_of)
    out.close(geocode=True)


if __name__ == "__main__":
    main()
