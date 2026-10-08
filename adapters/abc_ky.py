#!/usr/bin/env python3
"""Kentucky Department of Alcoholic Beverage Control: all active licenses.

abc_ky  premises holding an active retail license (quota and non-quota
        retail drink and package licenses, restaurants, hotels, private
        clubs, small farm wineries, microbreweries and the like), open as
        of the day the report was run.

The department offers a report page, not a file. The report is asked for
once, for the whole state, and its own CSV export is read: four requests.
Jefferson County is left to abc_ky_jefferson, which has positions.
Distributors, transporters, storage, suppliers and temporary and special
event licenses are left out. The licensee column is not read. No
positions; addresses go to the Census geocoder.

Kentucky public record. No license stated. The site has no robots.txt.
https://abcportal.ky.gov/BelleExternal/ReportGenerator/Reports
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

EXPORT = re.compile(r'"ExportUrlBase":"([^"]+)"')
NOT_RETAIL = ("distributor", "transport", "storage", "supplier", "temporary", "special", "wholesal", "rectifier",
              "out-of-state", "out of state", "shipper", "broker", "caterer", "sampling", "auction", "bottling",
              "air ", "riverboat", "railroad", "limousine", "agent", "solicitor")
PLACE = re.compile(r"^(.*?),\s*KY\s+(\d{5})")


def main():
    today = datetime.date.today()
    site = Site("https://abcportal.ky.gov", pause=3.0)
    site.fetch("/BelleExternal/ReportGenerator/Reports")
    site.fetch("/BelleExternal/ReportGenerator/GenerateReports",
               form={"FromDate": "01/01/1950", "ToDate": today.strftime("%m/%d/%Y")}, timeout=900)
    viewer = site.fetch("/BelleExternal/ReportViewerWebForm.aspx", timeout=900).decode("utf-8", "replace")
    link = EXPORT.search(viewer)
    if not link:
        raise SystemExit("abc_ky: the report viewer gave no export address")
    text = site.fetch(link.group(1).encode().decode("unicode_escape") + "CSV", timeout=900).decode("utf-8-sig", "replace")
    # two header lines of report parameters come before the table
    text = text[text.index("SiteID,"):]
    out = Writer("abc_ky")
    seen = set()
    for r in csv.DictReader(io.StringIO(text)):
        kind = (r.get("LicenseType") or "").lower()
        if r.get("Status") != "Active" or r.get("County") == "Jefferson" or any(k in kind for k in NOT_RETAIL):
            continue
        m = PLACE.match(r.get("PremisesCityState") or "")
        if not m:
            out.drop("no usable address")
            continue
        # a bar holds a license for each kind of sale
        if r.get("SiteID") in seen:
            continue
        seen.add(r.get("SiteID"))
        out.row("abc_ky", r.get("SiteID"), r.get("DBA"),
                address(r.get("PremisesStreet"), m.group(1), "KY %s" % m.group(2)), None, None, "open", today.isoformat())
    if len(seen) < 2000:
        raise SystemExit("abc_ky: only %d premises in the statewide report" % len(seen))
    out.close(geocode=True)


if __name__ == "__main__":
    main()
