#!/usr/bin/env python3
"""Florida DBPR, Alcoholic Beverages and Tobacco: retail beverage licenses.

abt_fl  a current retail beverage license (profession 4006, primary status
        20), open as of the day the file was read. The trade name (DBA) is
        used when there is one.

Caterer licenses are left out, as are the other professions in the file
(tobacco permits, wholesalers, manufacturers). The file has no positions;
addresses go to the Census geocoder.

Florida public record; the download page states no license.
https://www2.myfloridalicense.com/alcoholic-beverages-and-tobacco/public-records/
"""
import csv
import datetime
import io
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from evidence import Writer, address, get

URL = "https://www2.myfloridalicense.com/sto/file_download/extracts/bd400lic.csv"
# columns; the statewide file has no header row
PROFESSION, OWNER, SERIES, DBA, STREET, CITY, STATE, ZIP, LICENSE, STATUS = 1, 2, 3, 12, 13, 16, 17, 18, 20, 21
RETAIL_BEVERAGE, CURRENT = "4006", "20"
NO_PREMISES = {"13CT"}


def main():
    today = datetime.date.today().isoformat()
    out = Writer("abt_fl")
    for r in csv.reader(io.StringIO(get(URL).decode("latin-1"))):
        if len(r) <= STATUS or r[PROFESSION] != RETAIL_BEVERAGE:
            continue
        if r[STATUS] != CURRENT or r[STATE] != "FL":
            out.drop("not a current Florida license")
            continue
        if r[SERIES] in NO_PREMISES:
            out.drop("caterer")
            continue
        out.row("abt_fl", r[LICENSE], r[DBA] or r[OWNER],
                address(r[STREET], r[CITY], "FL %s" % r[ZIP][:5]), None, None, "open", today)
    out.close(geocode=True)


if __name__ == "__main__":
    main()
