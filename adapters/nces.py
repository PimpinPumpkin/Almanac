#!/usr/bin/env python3
"""NCES public school locations (EDGE geocodes), as open evidence.

nces_schools  every public school in the newest EDGE geocode file, open as of
              the last day of the school year the file covers (June 30).

The file lists schools that operated in that school year. It does not say
which have closed since, so there is no closed evidence here.

Public domain (US federal government work).
https://nces.ed.gov/programs/edge/Geographic/SchoolLocations
"""
import datetime
import io
import os
import sys
import zipfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from evidence import CACHE, Writer, address, download

BASE = "https://nces.ed.gov/programs/edge/data/EDGE_GEOCODE_PUBLICSCH_%s.zip"
# columns of the pipe-delimited text file, which has no header row
ID, NAME, STREET, CITY, STATE, ZIP, LAT, LON = 0, 2, 4, 5, 6, 7, 12, 13


def newest():
    """Try this school year's file, then earlier ones: 2526, 2425, ..."""
    year = datetime.date.today().year % 100
    for end in range(year + 1, year - 3, -1):
        tag = "%02d%02d" % (end - 1, end)
        try:
            return tag, download(BASE % tag, os.path.join(CACHE, "nces", "EDGE_GEOCODE_PUBLICSCH_%s.zip" % tag))
        except Exception:
            continue
    raise SystemExit("no EDGE public school file found")


def main():
    tag, path = newest()
    as_of = "20%s-06-30" % tag[2:]
    out = Writer("nces")
    with zipfile.ZipFile(path) as z:
        member = next(n for n in z.namelist() if n.upper().endswith(".TXT"))
        with z.open(member) as f:
            for line in io.TextIOWrapper(f, encoding="utf-8", errors="replace"):
                c = line.rstrip("\r\n").split("|")
                if len(c) <= LON or not c[ID][:2].isdigit():
                    continue
                out.row("nces_schools", c[ID], c[NAME],
                        address(c[STREET], c[CITY], "%s %s" % (c[STATE], c[ZIP][:5])),
                        c[LAT], c[LON], "open", as_of)
    out.close()


if __name__ == "__main__":
    main()
