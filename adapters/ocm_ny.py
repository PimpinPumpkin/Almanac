#!/usr/bin/env python3
"""New York Office of Cannabis Management: licensed retail dispensaries.

ocm_ny  a retail dispensary whose license is active and whose operational
        status is active, open as of the day the dataset was last updated.

The state marks a licensed shop that has not opened yet as
"Non-Operational"; those rows are not read. Growers, processors and
distributors are left out, and the contact name column is not read. No
positions; addresses go to the Census geocoder.

OPEN-NY Terms of Use. https://data.ny.gov/d/jskf-tt3q
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from evidence import Writer, address
from socrata import rows, updated

HOST, DATASET = "data.ny.gov", "jskf-tt3q"


def main():
    as_of = updated(HOST, DATASET)
    out = Writer("ocm_ny")
    where = ("license_type like '%Retail%' AND license_status = 'Active' AND operational_status = 'Active' "
             "AND state = 'NY' AND address_line_1 IS NOT NULL")
    for r in rows(HOST, DATASET, where=where,
                  select="license_number,entity_name,dba,address_line_1,city,zip_code"):
        out.row("ocm_ny", r.get("license_number"), r.get("dba") or r.get("entity_name"),
                address(r.get("address_line_1"), r.get("city"), "NY %s" % (r.get("zip_code") or "")[:5]),
                None, None, "open", as_of)
    out.close(geocode=True)


if __name__ == "__main__":
    main()
