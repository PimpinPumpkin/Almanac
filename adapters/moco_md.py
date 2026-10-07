#!/usr/bin/env python3
"""Montgomery County, Maryland: food inspections.

moco_md  a food business, open as of its newest inspection that ended in a
         pass or a fail. An inspector was in the place that day. No usable
         position per business; addresses go to the Census geocoder.

Public domain, as stated on the dataset.
https://data.montgomerycountymd.gov/d/dkrp-gr48
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from evidence import Writer, address
from socrata import rows

HOST, DATASET = "data.montgomerycountymd.gov", "dkrp-gr48"


def main():
    out = Writer("moco_md")
    seen = set()
    for r in rows(HOST, DATASET, select="registration_number,business_name,address,city,zip,max(inspection_start_date) as last",
                  where="status in ('Pass', 'Fail') AND state = 'MD'",
                  group="registration_number,business_name,address,city,zip", order="registration_number"):
        if r.get("registration_number") in seen:
            continue
        seen.add(r.get("registration_number"))
        out.row("moco_md", r.get("registration_number"), r.get("business_name"),
                address(r.get("address"), (r.get("city") or "").upper(), "MD %s" % (r.get("zip") or "")[:5]),
                None, None, "open", (r.get("last") or "")[:10])
    out.close(geocode=True)


if __name__ == "__main__":
    main()
