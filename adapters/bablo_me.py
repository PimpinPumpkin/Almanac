#!/usr/bin/env python3
"""Maine Bureau of Alcoholic Beverages and Lottery Operations: liquor
licenses.

bablo_me  an active license for premises in Maine (restaurants, bars,
          stores, agency liquor stores, hotels, clubs, breweries with a
          tasting room), open as of the day the file was read.

Suppliers, sales representatives, shippers and caterers are left out. The
legal entity name is not read. No positions; addresses go to the Census
geocoder.

Maine public record. No license stated.
https://www.maine.gov/dafs/bablo/liquor-licensing/license-data
"""
import urllib.parse
import datetime
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from evidence import Writer, address, get

from xlsx import rows

PAGE = "https://www.maine.gov/dafs/bablo/liquor-licensing/license-data"
LINK = re.compile(r'href="([^"]*inline-files/[^"]*\.xlsx)"', re.I)
NOT_A_PLACE = ("supplier", "sales representative", "shipper", "catering", "caterer", "auxiliary", "wholesale")


def main():
    today = datetime.date.today().isoformat()
    links = LINK.findall(get(PAGE).decode("utf-8", "replace"))
    if not links:
        raise SystemExit("bablo_me: no license file linked from the license data page")
    table = rows(get(urllib.parse.urljoin(PAGE, links[0])))
    head = next(table)
    col = {name: head.index(name) for name in (
        "Premises Name", "License Number", "License Status", "Premises Type Name", "Premises Address Line 1",
        "Premises City/Town", "Premises State", "Premises Zip Code")}
    out = Writer("bablo_me")
    seen = set()
    for r in table:
        r = r + [""] * (len(head) - len(r))
        kind = r[col["Premises Type Name"]].lower()
        if r[col["License Status"]] != "Active" or any(k in kind for k in NOT_A_PLACE):
            continue
        if r[col["Premises State"]] != "ME" or not r[col["Premises Address Line 1"]]:
            out.drop("no premises address in Maine")
            continue
        # one row for each license a premises holds
        key = (r[col["Premises Name"]].upper(), r[col["Premises Address Line 1"]].upper())
        if key in seen:
            continue
        seen.add(key)
        out.row("bablo_me", r[col["License Number"]], r[col["Premises Name"]],
                address(r[col["Premises Address Line 1"]], r[col["Premises City/Town"]],
                        "ME %s" % r[col["Premises Zip Code"]][:5]), None, None, "open", today)
    out.close(geocode=True)


if __name__ == "__main__":
    main()
