#!/usr/bin/env python3
"""Delaware Division of Revenue: state business licenses.

biz_de  a Delaware business with a current license in a storefront trade
        (retail, restaurants, general services, lodging, vehicle dealers and
        the like), open as of the day the dataset was last updated.

Every business trading in Delaware needs one of these, which makes it the
widest register for the state's small shops. Contractors, lessors,
wholesalers, sales representatives and other trades without a shop front
are left out. Many licensees are one person working from home, so rows are
evidence for places that are already listed; nothing here creates a place.
Addresses go to the Census geocoder (the position in the file is only
approximate).

Public domain, as stated on the dataset.
https://data.delaware.gov/d/5zy2-grhr
"""
import datetime
import json
import os
import sys
import urllib.parse

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from evidence import Writer, address, get

VIEW = "https://data.delaware.gov/api/views/5zy2-grhr.json"
ROWS = "https://data.delaware.gov/resource/5zy2-grhr.json"
PAGE = 50000
STOREFRONT = ("RETAILER", "GENERAL SERVICES", "GROCERY", "HOTEL", "MOTEL", "MOTOR VEHICLE DEALER",
              "TOBACCO RETAILER", "CIGARETTE", "FINANCE", "TRAVEL AGENCY")
NOT_A_SHOP = ("TRANSIENT",)
FIELDS = "license_number,business_name,trade_name,category,current_license_valid_to,address_1,city,zip"


def main():
    today = datetime.date.today().isoformat()
    updated = datetime.datetime.fromtimestamp(
        json.loads(get(VIEW))["rowsUpdatedAt"], datetime.timezone.utc).date().isoformat()
    out = Writer("biz_de")
    seen, offset = set(), 0
    while True:
        q = {"$select": FIELDS, "$where": "state = 'DE' AND current_license_valid_to >= '%s'" % today,
             "$limit": PAGE, "$offset": offset, "$order": "license_number"}
        rows = json.loads(get(ROWS + "?" + urllib.parse.urlencode(q)))
        for r in rows:
            kind = (r.get("category") or "").upper()
            if not kind.startswith(STOREFRONT) or any(w in kind for w in NOT_A_SHOP):
                out.drop("not a storefront trade")
                continue
            # one business holds a license per trade; one row per business and address is enough
            k = (r.get("trade_name"), r.get("address_1"))
            if k in seen:
                continue
            seen.add(k)
            out.row("biz_de", r["license_number"], r.get("trade_name") or r.get("business_name"),
                    address(r.get("address_1"), (r.get("city") or "").upper(), "DE %s" % (r.get("zip") or "")[:5]),
                    None, None, "open", updated)
        offset += len(rows)
        if len(rows) < PAGE:
            break
    out.close(geocode=True)


if __name__ == "__main__":
    main()
