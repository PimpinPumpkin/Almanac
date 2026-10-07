#!/usr/bin/env python3
"""City of Boston: food establishment licenses and inspections, and
Licensing Board licenses.

isd_boston_food        an active food establishment license, open as of the
                       day the list was last changed. Positions come with
                       the data.
isd_boston_inspection  a licensed food establishment, open as of the day of
                       its newest inspection.
lb_boston              an active Licensing Board license (alcohol, common
                       victualler, lodging and the like), open as of the day
                       the list was last changed. No usable positions;
                       addresses go to the Census geocoder.

The owner, applicant, manager and phone columns are not read.

Open Data Commons Public Domain Dedication and License, as stated on each
dataset. https://data.boston.gov
"""
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from ckan import modified, rows
from evidence import Writer, address

HOST = "data.boston.gov"
FOOD = "f1e13724-284d-478c-b8bc-ef042aa5b70b"
INSPECTIONS = "4582bec6-2b4f-4f9e-bc55-cbaa73117f4c"
BOARD = "04dc653b-1789-4374-9669-b07df7233344"
POINT = re.compile(r"\(\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*\)")


def where(r):
    # "417-  Washington ST" and "224  BOSTON ST"
    street = re.sub(r"\s+", " ", re.sub(r"^(\d+)-\s", r"\1 ", (r.get("address") or "").strip()))
    return address(street, (r.get("city") or "").upper(), "MA %s" % (r.get("zip") or "")[:5])


def main():
    out = Writer("boston_ma")
    as_of = modified(HOST, FOOD)
    seen = set()
    for r in rows(HOST, FOOD):
        if r.get("licstatus") != "Active":
            continue
        # no license number in this list; the city's property id and the name stand in
        key = "%s-%s" % (r.get("property_id"), re.sub(r"\W+", "", (r.get("businessname") or "").upper()))
        if key in seen:
            continue
        seen.add(key)
        out.row("isd_boston_food", key, r.get("dbaname") or r.get("businessname"), where(r),
                r.get("latitude"), r.get("longitude"), "open", as_of)

    newest = {}
    for r in rows(HOST, INSPECTIONS):
        day = (r.get("resultdttm") or "")[:10]
        if r.get("licstatus") != "Active" or not day:
            continue
        if r["licenseno"] not in newest or day > newest[r["licenseno"]][0]:
            newest[r["licenseno"]] = (day, r)
    for license_no, (day, r) in newest.items():
        m = POINT.search(r.get("location") or "")
        lat, lng = (m.group(1), m.group(2)) if m else (None, None)
        out.row("isd_boston_inspection", license_no, r.get("dbaname") or r.get("businessname"), where(r),
                lat, lng, "open", day)

    as_of = modified(HOST, BOARD)
    for r in rows(HOST, BOARD):
        if r.get("status") != "Active":
            continue
        out.row("lb_boston", r.get("license_num"), r.get("dba_name") or r.get("business_name"), where(r),
                None, None, "open", as_of)
    out.close(geocode=True)


if __name__ == "__main__":
    main()
