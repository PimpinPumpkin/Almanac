#!/usr/bin/env python3
"""Missouri Division of Alcohol and Tobacco Control: alcohol licenses.

atc_mo      an active license for a Missouri premises (by the drink, package
            sales, microbrewery, winery), open as of the day the dataset was
            last updated.
The state also lists licenses "Out of Business" with a date, which is the
kind of record this project wants. It is not used yet: the list only
reaches back a few weeks (59 premises statewide, 3 in a Kansas City box),
too few to put through the independent check. It needs the list kept from
month to month first (ROADMAP.md, section 4).

Solicitors, direct shippers, caterers, temporary licenses and licenses for
boats and rail cars are left out. The active list repeats each license once
per manager and names that person; only the business fields are read. No
positions; addresses go to the Census geocoder.

Neither dataset states a license. Missouri public record.
https://data.mo.gov/d/yyhn-562y (out of business: nytw-fmz3)
"""
import datetime
import json
import os
import sys
import urllib.parse

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from evidence import Writer, address, get

HOST = "https://data.mo.gov"
ACTIVE = "yyhn-562y"
PAGE = 50000
NOT_A_PREMISES = ("solicitor", "shipper", "caterer", "temporary", "boat", "railroad", "state fair")


def rows(dataset, select):
    offset = 0
    while True:
        q = {"$select": select, "$limit": PAGE, "$offset": offset, "$order": ":id"}
        page = json.loads(get("%s/resource/%s.json?%s" % (HOST, dataset, urllib.parse.urlencode(q))))
        yield from page
        offset += len(page)
        if len(page) < PAGE:
            return


def main():
    updated = datetime.datetime.fromtimestamp(
        json.loads(get("%s/api/views/%s.json" % (HOST, ACTIVE)))["rowsUpdatedAt"],
        datetime.timezone.utc).date().isoformat()
    out = Writer("atc_mo")
    seen = set()
    for r in rows(ACTIVE, "primary_license,primary_type,dbaname,licensee,street_number,street,city,state,zipcode"):
        number = r.get("primary_license")
        if number in seen or r.get("state") != "Missouri":
            continue
        seen.add(number)
        if any(word in (r.get("primary_type") or "").lower() for word in NOT_A_PREMISES):
            out.drop("not a premises license")
            continue
        street = ("%s %s" % (r.get("street_number") or "", r.get("street") or "")).strip()
        out.row("atc_mo", number, (r.get("dbaname") or r.get("licensee") or "").strip(),
                address(street, (r.get("city") or "").upper(), "MO %s" % (r.get("zipcode") or "")[:5]),
                None, None, "open", updated)
    out.close(geocode=True)


if __name__ == "__main__":
    main()
