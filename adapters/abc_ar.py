#!/usr/bin/env python3
"""Arkansas Alcoholic Beverage Control: monthly permit list.

abc_ar  premises holding an active retail alcohol permit (liquor store,
        beer or wine retailer, restaurant, private club, hotel), open as of
        the first day of the month of the list. The trading name is used
        when there is one.

The list also holds tobacco-only permits and wholesalers, which are left
out. The owner's name and phone are not read. No positions; addresses go to
the Census geocoder.

Arkansas public record. No license stated.
https://www.dfa.arkansas.gov/office/alcohol-beverage-control/permit-changes/
"""
import urllib.error
import datetime
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from evidence import Writer, address, get

from xlsx import rows

URL = "https://www.dfa.arkansas.gov/wp-content/uploads/FullPermit%04d%02d.xlsx"
ACTIVE = re.compile(r"(LIQUOR|BEER|WINE|MIXED DRINK|RESTAURANT|PRIVATE CLUB|HOTEL)[^()]*-Active\(", re.I)
NOT_RETAIL = re.compile(r"^(WHOLESALE|MANUFACTUR|DISTRIBUT)", re.I)


def newest():
    """The newest monthly file, looking back from this month."""
    day = datetime.date.today().replace(day=1)
    for _ in range(6):
        try:
            return get(URL % (day.year, day.month), tries=1), day.isoformat()
        except urllib.error.HTTPError:
            day = (day - datetime.timedelta(days=1)).replace(day=1)
    raise SystemExit("abc_ar: no monthly permit file in the last six months")


def main():
    data, as_of = newest()
    table = rows(data)
    head = next(table)
    col = {name: head.index(name) for name in (
        "Permit Number", "Permit Suffix", "Company", "Alias", "Permit Type", "Business Physical Address", "City", "Zip")}
    out = Writer("abc_ar")
    for r in table:
        r = r + [""] * (len(head) - len(r))
        kind = r[col["Permit Type"]]
        if not ACTIVE.search(kind) or NOT_RETAIL.match(kind):
            out.drop("no active retail alcohol permit")
            continue
        out.row("abc_ar", "%s-%s" % (r[col["Permit Number"]], r[col["Permit Suffix"]]),
                r[col["Alias"]] or r[col["Company"]],
                address(r[col["Business Physical Address"]], r[col["City"]], "AR %s" % r[col["Zip"]][:5]),
                None, None, "open", as_of)
    out.close(geocode=True)


if __name__ == "__main__":
    main()
