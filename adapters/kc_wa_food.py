#!/usr/bin/env python3
"""King County, Washington (Seattle and around): food establishment inspections.

kc_wa_food  one row per food business inspected in the last three years,
            open as of its newest inspection. An inspector was in the place
            that day.

The "closed business" flag in the data means a temporary health closure and
is not used. No positions; addresses go to the Census geocoder.

Public domain, as stated on the dataset.
https://data.kingcounty.gov/d/r878-4sxa
"""
import datetime
import json
import os
import sys
import urllib.parse

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from evidence import Writer, address, get

ROWS = "https://data.kingcounty.gov/resource/r878-4sxa.json"
PAGE = 50000


def main():
    since = (datetime.date.today() - datetime.timedelta(days=3 * 365)).isoformat()
    out = Writer("kc_wa_food")
    seen, offset = set(), 0
    while True:
        q = {"$select": "business_id,name,address,city,zip_code,max(inspection_date) as last",
             "$where": "inspection_date > '%s'" % since,
             "$group": "business_id,name,address,city,zip_code",
             "$order": "business_id", "$limit": PAGE, "$offset": offset}
        rows = json.loads(get(ROWS + "?" + urllib.parse.urlencode(q)))
        for r in rows:
            if r.get("business_id") in seen:
                continue
            seen.add(r.get("business_id"))
            # the unit follows a comma: "116 SW 148TH ST, D-190"
            street = (r.get("address") or "").split(",")[0].strip()
            out.row("kc_wa_food", r.get("business_id"), r.get("name"),
                    address(street, (r.get("city") or "").upper(), "WA %s" % (r.get("zip_code") or "")[:5]),
                    None, None, "open", (r.get("last") or "")[:10])
        offset += len(rows)
        if len(rows) < PAGE:
            break
    out.close(geocode=True)


if __name__ == "__main__":
    main()
