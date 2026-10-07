#!/usr/bin/env python3
"""NCUA quarterly call report data: credit union offices, as open evidence.

ncua_branches  every office in the branch file of the newest quarterly
               release, open as of the quarter's cycle date. Rows are matched
               by address; the file has no positions.

The file gives the credit union's short name ("JUSTICE"). "Credit Union" is
added so that it matches the credit union and not whatever it is named
after: many are named for an agency in the same building.

Public domain (US federal government work).
https://ncua.gov/analysis/credit-union-corporate-call-report-data/quarterly-data
"""
import csv
import datetime
import io
import os
import sys
import zipfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from evidence import CACHE, Writer, address, download

URL = "https://ncua.gov/files/publications/analysis/call-report-data-%04d-%02d.zip"
BRANCHES = "Credit Union Branch Information.txt"


def newest():
    """Walk back from this quarter until a release exists."""
    today = datetime.date.today()
    y, m = today.year, 3 * ((today.month - 1) // 3 + 1)
    for _ in range(6):
        try:
            return download(URL % (y, m), os.path.join(CACHE, "ncua", "call-report-data-%04d-%02d.zip" % (y, m)))
        except Exception:
            m -= 3
            if m == 0:
                y, m = y - 1, 12
    raise SystemExit("no NCUA call report release found")


def mdy(s):
    """6/30/2026 0:00:00 -> 2026-06-30"""
    m, d, y = s.split(" ")[0].split("/")
    return "%04d-%02d-%02d" % (int(y), int(m), int(d))


def main():
    out = Writer("ncua")
    with zipfile.ZipFile(newest()) as z:
        f = io.TextIOWrapper(z.open(BRANCHES), encoding="latin-1", newline="")
        for r in csv.DictReader(f):
            if r["PhysicalAddressCountry"] not in ("United States", ""):
                out.drop("outside the US")
                continue
            name = r["CU_NAME"].strip()
            if "CREDIT UNION" not in name.upper() and not name.upper().endswith((" FCU", " CU")):
                name += " Credit Union"
            # SiteId repeats across credit unions
            out.row("ncua_branches", "%s-%s" % (r["CU_NUMBER"], r["SiteId"]), name,
                    address(r["PhysicalAddressLine1"], r["PhysicalAddressCity"],
                            "%s %s" % (r["PhysicalAddressStateCode"], r["PhysicalAddressPostalCode"][:5])),
                    None, None, "open", mdy(r["CYCLE_DATE"]))
    out.close(geocode=True)


if __name__ == "__main__":
    main()
