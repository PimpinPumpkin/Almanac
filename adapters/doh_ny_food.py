#!/usr/bin/env python3
"""New York State Department of Health: last inspection of each food service
establishment.

doh_ny_food  a restaurant, cafeteria or other food service operation, open
             as of the day of its last inspection. Positions come with the
             data.

Covers the counties whose inspections the state publishes. New York City,
Suffolk County and Erie County run their own programs and are not in it.
The operator name columns are not read. Operations whose permit has
expired, or whose name the state has marked inactive, are left out.

OPEN-NY Terms of Use. https://health.data.ny.gov/d/cnih-y5dw
"""
import datetime
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from evidence import Writer, address
from socrata import point, rows

HOST, DATASET = "health.data.ny.gov", "cnih-y5dw"


def main():
    today = datetime.date.today().isoformat()
    out = Writer("doh_ny_food")
    for r in rows(HOST, DATASET, where="permit_expiration_date IS NULL OR permit_expiration_date > '%s'" % today,
                  select="nys_health_operation_id,operation_name,facility_address,city,zip_code,date,location1"):
        # the state leaves closed operations in the file with a note in the name
        if "inactive" in (r.get("operation_name") or "").lower():
            out.drop("marked inactive")
            continue
        lat, lng = point(r.get("location1"))
        out.row("doh_ny_food", r.get("nys_health_operation_id"), r.get("operation_name"),
                address(r.get("facility_address"), r.get("city"), "NY %s" % (r.get("zip_code") or "")[:5]),
                lat, lng, "open", (r.get("date") or "")[:10])
    out.close()


if __name__ == "__main__":
    main()
