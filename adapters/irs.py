#!/usr/bin/env python3
"""IRS Exempt Organizations Business Master File: nonprofits that filed a return.

irs_eo  one row per organization that has a TAX_PERIOD, the month its newest
        return covers. Filing a return is a dated sign of life; the row is
        open as of the last day of that month.

Organizations with no tax period (most churches, which do not file) are left
out. The address is the one on the return, often a mailing address, so only
part of the file will find a place. Matched by address; the file has no
positions.

Public domain (US federal government work).
https://www.irs.gov/charities-non-profits/exempt-organizations-business-master-file-extract-eo-bmf
"""
import calendar
import csv
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from evidence import CACHE, Writer, address, download

FILES = ["eo1", "eo2", "eo3", "eo4"]
URL = "https://www.irs.gov/pub/irs-soi/%s.csv"


def month_end(yyyymm):
    y, m = int(yyyymm[:4]), int(yyyymm[4:6])
    return "%04d-%02d-%02d" % (y, m, calendar.monthrange(y, m)[1])


def main():
    out = Writer("irs")
    for name in FILES:
        path = download(URL % name, os.path.join(CACHE, "irs", name + ".csv"))
        with open(path, newline="", encoding="latin-1") as f:
            for r in csv.DictReader(f):
                period = (r.get("TAX_PERIOD") or "").strip()
                if len(period) != 6 or not period.isdigit() or not 1 <= int(period[4:]) <= 12:
                    out.drop("no tax period")
                    continue
                if r["STREET"].upper().startswith(("PO BOX", "P O BOX")):
                    out.drop("PO box")
                    continue
                out.row("irs_eo", r["EIN"], r["NAME"],
                        address(r["STREET"], r["CITY"], "%s %s" % (r["STATE"], r["ZIP"][:5])),
                        None, None, "open", month_end(period))
    out.close()


if __name__ == "__main__":
    main()
