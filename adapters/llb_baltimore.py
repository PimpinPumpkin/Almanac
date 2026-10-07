#!/usr/bin/env python3
"""Baltimore City Board of Liquor License Commissioners: liquor licenses.

llb_baltimore  a license renewed for the newest license year in the table,
               open as of the day that license began.

The table keeps one row per license per year. Only the newest year is
read, and only the trade name and address, not the licensee's name. No
positions; addresses go to the Census geocoder.

City of Baltimore Open Data. No license stated.
https://services1.arcgis.com/UWYHeuuJISiGmgXx/arcgis/rest/services/LIquor_Licenses/FeatureServer/0
"""
import datetime
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from arcgis import day, edited, features
from evidence import Writer, address

LAYER = "https://services1.arcgis.com/UWYHeuuJISiGmgXx/arcgis/rest/services/LIquor_Licenses/FeatureServer/0"


def main():
    rows = [a for a, _ in features(LAYER, where="LicenseStatus = 'Renewed' AND LicenseYear >= %d" % (datetime.date.today().year - 2),
                                   fields="LLKey,LicenseYear,LicenseDate,TradeName,CorpName,AddrStreet,AddrZip", geometry=False)]
    year = max(a["LicenseYear"] for a in rows)
    out = Writer("llb_baltimore")
    seen = set()
    for a in rows:
        if a["LicenseYear"] != year or a["LLKey"] in seen or not a.get("LicenseDate"):
            continue
        seen.add(a["LLKey"])
        out.row("llb_baltimore", a["LLKey"], a.get("TradeName") or a.get("CorpName"),
                address(a.get("AddrStreet"), "BALTIMORE", "MD %s" % str(a.get("AddrZip") or "")[:5]),
                None, None, "open", day(a["LicenseDate"]))
    out.close(geocode=True)


if __name__ == "__main__":
    main()
