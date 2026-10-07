#!/usr/bin/env python3
"""Idaho State Police, Alcohol Beverage Control: retail licenses.

isp_id_liquor  an issued retail license that has not expired, open as of
               the day the file was read. The trading name is used.

The licensee's name is not read. No positions; addresses go to the Census
geocoder.

Idaho public record. No license stated.
https://apps.isp.idaho.gov/AbcReporting/
"""
import csv
import io
import datetime
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from evidence import Writer, address, get

URL = "https://apps.isp.idaho.gov/AbcReporting/license/search/csv?licenseTypes=retail&status=ISSUED"


def main():
    today = datetime.date.today()
    out = Writer("isp_id_liquor")
    for r in csv.DictReader(io.StringIO(get(URL).decode("utf-8-sig", "replace")), skipinitialspace=True):
        try:
            if datetime.datetime.strptime(r.get("Expiration") or "", "%m/%d/%Y").date() < today:
                out.drop("expired")
                continue
        except ValueError:
            pass
        out.row("isp_id_liquor", r.get("License ID"), r.get("DBA") or r.get("Licensee"),
                address(r.get("Address"), r.get("City"), "ID %s" % (r.get("Zip") or "")[:5]),
                None, None, "open", today.isoformat())
    out.close(geocode=True)


if __name__ == "__main__":
    main()
