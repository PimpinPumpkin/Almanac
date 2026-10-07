#!/usr/bin/env python3
"""Oregon Liquor and Cannabis Commission: liquor licenses.

olcc_or  a license that has not expired, for a premises (on-premises and
         off-premises sales, brewery public houses, wineries with tasting,
         distillery tasting rooms, clubs): open as of the day the dataset
         was last updated.

Expired licenses are in the file with their expiry dates, back to 2009, but
are not emitted. Tested in a Portland box on expired on-premises licenses,
places with no brand, no live license under the same name at the address:
other evidence said still open 6 times and closed 26. Three of the six were
bars a mapper saw trading months after the expiry date.

Certificates of approval, shippers, wholesalers, warehouses and industrial
authorities are left out. No positions; addresses go to the Census geocoder.

Neither the dataset nor data.oregon.gov states a license. Oregon public record.
https://data.oregon.gov/d/srxe-qkm2
"""
import datetime
import json
import os
import re
import sys
import urllib.parse

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from evidence import Writer, address, get

HOST = "https://data.oregon.gov"
DATASET = "srxe-qkm2"
PAGE = 50000
NOT_A_PREMISES = ("certificate", "shipper", "wholesale", "warehouse", "industrial", "non-consumption")
TAIL = re.compile(r"\s+OR\s+(\d{5})(-\d{4})?\s*$")


def split(r):
    """'31 NW 1ST AVE PORTLAND OR  97209-4001' -> ('31 NW 1ST AVE', 'PORTLAND', '97209')"""
    full, city = (r.get("physical_address") or "").strip(), (r.get("city") or "").strip().upper()
    m = TAIL.search(full)
    if not m:
        return None
    street = full[:m.start()].strip()
    if city and street.upper().endswith(city):
        street = street[:-len(city)].strip()
    return street, city, m.group(1)


def main():
    updated = datetime.datetime.fromtimestamp(
        json.loads(get("%s/api/views/%s.json" % (HOST, DATASET)))["rowsUpdatedAt"],
        datetime.timezone.utc).date().isoformat()
    out = Writer("olcc_or")
    offset = 0
    while True:
        q = {"$where": "license_expired = 'No'", "$limit": PAGE, "$offset": offset, "$order": ":id"}
        page = json.loads(get("%s/resource/%s.json?%s" % (HOST, DATASET, urllib.parse.urlencode(q))))
        for r in page:
            if not r.get("license_number"):
                out.drop("no license number")
                continue
            if any(word in (r.get("license_type") or "").lower() for word in NOT_A_PREMISES):
                out.drop("not a premises license")
                continue
            parts = split(r)
            if not parts:
                out.drop("address not in Oregon")
                continue
            out.row("olcc_or", r["license_number"], r.get("trade_name") or r.get("licensee_name"),
                    address(parts[0], parts[1], "OR %s" % parts[2]), None, None, "open", updated)
        offset += len(page)
        if len(page) < PAGE:
            break
    out.close(geocode=True)


if __name__ == "__main__":
    main()
