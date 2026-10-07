#!/usr/bin/env python3
"""New Jersey Division of Alcoholic Beverage Control: retail licenses.

abc_nj  a retail license that is in use, open as of the first day of the
        month of the report.

New Jersey licenses can sit unused for years ("pocket licenses"). The
report gives those an inactivity start date, and they are not read. The
licensee's name is not read. No positions; addresses go to the Census
geocoder.

New Jersey public record. No license stated.
https://www.njoag.gov/about/divisions-and-offices/division-of-alcoholic-beverage-control-home/licensing-bureau-applications-and-information/licensing-reports/
"""
import datetime
import urllib.parse
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from evidence import Writer, address, get

from xlsx import rows

PAGE = ("https://www.njoag.gov/about/divisions-and-offices/division-of-alcoholic-beverage-control-home/"
        "licensing-bureau-applications-and-information/licensing-reports/")
LINK = re.compile(r'href="([^"]*/(\d{4})/(\d{2})/RETAIL-LICENSE-REPORT[^"]*\.xlsx)"', re.I)
PLACE = re.compile(r"^(.*?)\s*\n\s*(.*?),\s*NJ\s+(\d{5})", re.S)


def main():
    found = sorted(LINK.findall(get(PAGE).decode("utf-8", "replace")), key=lambda m: (m[1], m[2]))
    if not found:
        raise SystemExit("abc_nj: no retail license report linked from the reports page")
    link, year, month = found[-1]
    as_of = "%s-%s-01" % (year, month)
    out = Writer("abc_nj")
    table = rows(get(urllib.parse.urljoin(PAGE, link)))
    for r in table:
        if r and r[0] == "License Number":
            break
    for r in table:
        r = r + [""] * (7 - len(r))
        if r[4]:
            out.drop("inactive license")
            continue
        m = PLACE.match(r[6])
        if not m:
            out.drop("no usable address")
            continue
        out.row("abc_nj", r[0], r[2], address(m.group(1), m.group(2), "NJ %s" % m.group(3)), None, None, "open", as_of)
    out.close(geocode=True)


if __name__ == "__main__":
    main()
