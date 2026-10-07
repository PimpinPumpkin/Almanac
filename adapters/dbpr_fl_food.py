#!/usr/bin/env python3
"""Florida DBPR: sanitation inspections of restaurants and other food service.

dbpr_fl_food  one row per licensed food service establishment inspected in
              the current fiscal year (it starts July 1), open as of its
              newest inspection. An inspector stood in the place that day.

The files hold inspections only, so there is no closed evidence here. They
have no positions; addresses go to the Census geocoder.

Florida public record; the download page states no license.
https://www2.myfloridalicense.com/hotels-restaurants/public-records/
"""
import csv
import io
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from evidence import Writer, address, get

URL = "https://www2.myfloridalicense.com/sto/file_download/extracts/%dfdinspi.csv"
DISTRICTS = range(1, 8)
# columns of the district files, which share one layout
LICENSE, NAME, STREET, CITY, ZIP, DATE = 4, 5, 6, 7, 8, 14


def iso(mdy):
    """07/15/2026 -> 2026-07-15"""
    return "%s-%s-%s" % (mdy[6:10], mdy[0:2], mdy[3:5]) if len(mdy) == 10 else ""


def main():
    newest = {}
    for d in DISTRICTS:
        rows = csv.reader(io.StringIO(get(URL % d).decode("latin-1")))
        next(rows)
        for r in rows:
            if len(r) <= DATE:
                continue
            day = iso(r[DATE].strip())
            if day > newest.get(r[LICENSE], ("",))[0]:
                newest[r[LICENSE]] = (day, r)
    out = Writer("dbpr_fl_food")
    for lic, (day, r) in newest.items():
        out.row("dbpr_fl_food", lic.strip(), r[NAME],
                address(r[STREET], r[CITY].upper(), "FL %s" % r[ZIP].strip()[:5]),
                None, None, "open", day)
    out.close(geocode=True)


if __name__ == "__main__":
    main()
