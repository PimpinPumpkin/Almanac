#!/usr/bin/env python3
"""Washington Department of Children, Youth, and Families: licensed child
care centers and school-age programs.

childcare_wa  a center or program whose operating status is active, open as
              of the day the dataset was last updated.

The list holds centers only, not family homes. The contact person, phone
and email columns are not read. Positions in the file are zero; addresses
go to the Census geocoder.

Washington public record. No license stated.
https://data.wa.gov/d/was8-3ni8
"""
import datetime
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from evidence import Writer, address
from socrata import point, rows, updated

HOST, DATASET = "data.wa.gov", "was8-3ni8"


def main():
    as_of = updated(HOST, DATASET)
    out = Writer("childcare_wa")
    for r in rows(HOST, DATASET, where="latestoperatingstatus = 'Active'",
                  select="wacompassid,providername,doingbusinessas,physicalstreetaddress,physicalcity,physicalzip"):
        out.row("childcare_wa", r.get("wacompassid"), r.get("doingbusinessas") or r.get("providername"),
                address(r.get("physicalstreetaddress"), r.get("physicalcity"), "WA %s" % (r.get("physicalzip") or "")[:5]),
                None, None, "open", as_of)
    out.close(geocode=True)


if __name__ == "__main__":
    main()
