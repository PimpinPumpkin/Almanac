#!/usr/bin/env python3
"""Pennsylvania Liquor Control Board: export of all licenses.

plcb_pa  premises with an active retail license (restaurants, hotels,
         clubs, eating places, beer distributors, breweries, wineries,
         distilleries, venues), open as of the day the export was read.

The board links a CSV of every license from its search page. Its
robots.txt disallows everything but the search pages; the owner of this
project decided on 2026-10-07 to read the export anyway, because it is the
board's own public download: two requests a month.

Licenses in "safekeeping" are held, not used: a license goes into
safekeeping when its premises stop trading, which may make it a closure
signal once it has been tested. Special occasion permits, shippers,
transporters, importers, storage and non-beverage permits are left out.
The licensee, owner and manager columns are not read. No positions;
addresses go to the Census geocoder.

Pennsylvania public record. No license stated.
https://plcbplus.pa.gov/pub/Default.aspx?PossePresentation=LicenseSearch
"""
import csv
import datetime
import io
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from crawl import Site
from evidence import Writer, address

NOT_RETAIL = ("special occasion", "shipper", "transporter", "non-beverage", "vendor permit", "grain alcohol",
              "auction", "tax-exempt", "storage", "sales permit", "bailee", "alcohol beverage", "manufacturer",
              "catering club")
PLACE = re.compile(r"^(.*),\s*([^,]+?)\s+PA\s+(\d{5})")


def main():
    today = datetime.date.today().isoformat()
    site = Site("https://plcbplus.pa.gov", robots=False)
    site.fetch("/pub/Default.aspx?PossePresentation=LicenseSearch")
    text = site.fetch("/pub/LicenseExport.aspx", timeout=900).decode("utf-8-sig", "replace")
    out, held = Writer("plcb_pa"), Writer("plcb_pa_safekeeping", held=True)
    for r in csv.DictReader(io.StringIO(text)):
        kind = (r.get("License Type") or "").lower()
        if any(k in kind for k in NOT_RETAIL) or kind == "importer":
            continue
        m = PLACE.match(r.get("Premises Address") or "")
        if not m:
            continue
        where = address(m.group(1), m.group(2), "PA %s" % m.group(3))
        if r.get("Status") == "Active":
            out.row("plcb_pa", r.get("LID"), r.get("Premises"), where, None, None, "open", today)
        elif r.get("Status") == "Safekeeping":
            held.row("plcb_pa_safekeeping", r.get("LID"), r.get("Premises"), where, None, None, "closed", today)
    if not out.kept:
        raise SystemExit("plcb_pa: the export had no active licenses")
    held.close(geocode=True)
    out.close(geocode=True)


if __name__ == "__main__":
    main()
