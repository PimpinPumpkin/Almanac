#!/usr/bin/env python3
"""Colorado Department of Early Childhood: licensed child care facilities.

childcare_co  a licensed child care center, preschool or school-age
              program, open as of the day the dataset was last updated.

Family child care homes are left out: they are people's houses. Camps are
left out too. No positions; addresses go to the Census geocoder.

Open Data Commons Public Domain Dedication and License, as stated on the
dataset. https://data.colorado.gov/d/a9rr-k8mu
"""
import datetime
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from evidence import Writer, address
from socrata import point, rows, updated

HOST, DATASET = "data.colorado.gov", "a9rr-k8mu"


def main():
    as_of = updated(HOST, DATASET)
    out = Writer("childcare_co")
    where = "provider_service_type IN ('Child Care Center', 'Preschool Program', 'School-Age Child Care Center')"
    for r in rows(HOST, DATASET, where=where, select="provider_id,provider_name,street_address,city,zip"):
        out.row("childcare_co", r.get("provider_id"), r.get("provider_name"),
                address(r.get("street_address"), r.get("city"), "CO %s" % (r.get("zip") or "")[:5]),
                None, None, "open", as_of)
    out.close(geocode=True)


if __name__ == "__main__":
    main()
