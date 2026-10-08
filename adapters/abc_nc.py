#!/usr/bin/env python3
"""North Carolina ABC Commission: active retail permits.

abc_nc  premises holding an active permit to sell alcohol to the public
        (on-premises and off-premises beer and wine, mixed beverages,
        brown bagging, wine and beer shops, breweries, wineries and
        distilleries), open as of the day the search was run.

The commission offers a search form, not a file. The form is asked once
per county for active permits and its own spreadsheet export is read: 100
requests, two seconds apart. Salesmen, vendor representatives, importers,
wholesalers, shippers, carriers, caterers and one-time and special event
permits are left out. The corporation name and mailing address are not
read. No positions; addresses go to the Census geocoder.

North Carolina public record. No license stated. The site has no
robots.txt. https://abc2.nc.gov/Search/Permit
"""
import datetime
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from crawl import Site
from evidence import Writer, address
from xlsx import rows

COUNTIES = range(1, 101)
ACTIVE = "5"
# the two letters that end a permit number say what kind it is
RETAIL = {"AD", "AE", "AJ", "AK", "AL", "AM", "AN", "AO", "AP", "AQ", "AS", "AY", "AZ", "BC", "BD", "BE", "BF", "BN",
          "BO", "BP", "BT", "BU", "CD", "CF", "CW", "CY", "CZ", "DA", "DB", "DC", "DE", "DI", "DJ", "DL", "DM", "DZ", "SV"}
EXPORT = re.compile(r'href="(/Downloads/Search/Permit/[^"]+\.xlsx)"')


def main():
    today = datetime.date.today().isoformat()
    site = Site("https://abc2.nc.gov")
    out = Writer("abc_nc")
    seen, empty = set(), 0
    for county in COUNTIES:
        page = site.fetch("/Search/PermitSearch", form={
            "PermitSearchBusinessName": "", "PermitSearchPermitNumber": "", "PermitSearchAddress": "",
            "PermitSearchZip": "", "PermitSearchCounties": str(county), "PermitSearchBusinessStatus": ACTIVE,
            "PermitSearchBulkPermitType": "-1"}).decode("utf-8", "replace")
        link = EXPORT.search(page)
        if not link:
            empty += 1
            continue
        table = rows(site.fetch(link.group(1)))
        head = next(table)
        col = {name: head.index(name) for name in ("Trade Name", "Business Status", "Address", "City", "Zip", "Permit Number")}
        for r in table:
            r = r + [""] * (len(head) - len(r))
            permit = r[col["Permit Number"]]
            if r[col["Business Status"]] != "Active" or permit[-2:] not in RETAIL:
                continue
            # a bar holds a permit for each kind of drink
            key = (r[col["Trade Name"]].upper(), r[col["Address"]].upper())
            if key in seen:
                continue
            seen.add(key)
            out.row("abc_nc", permit, r[col["Trade Name"]],
                    address(r[col["Address"]], r[col["City"]], "NC %s" % r[col["Zip"]][:5]), None, None, "open", today)
    if empty > 10:
        # the form changed or the site is refusing: keep last run's file
        raise SystemExit("abc_nc: %d of %d county searches returned no export" % (empty, len(COUNTIES)))
    out.close(geocode=True)


if __name__ == "__main__":
    main()
