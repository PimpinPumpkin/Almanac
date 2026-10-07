#!/usr/bin/env python3
"""Columbus Public Health, Ohio: inspected restaurants and markets.

cph_columbus_food  a restaurant, market, bar, bakery or other licensed food
                   business whose permit has not run out, open as of the day
                   the layer was read. Positions come with the data.

Mobile units and vending are left out.

City of Columbus GIS. No license stated.
https://maps2.columbus.gov/arcgis/rest/services/Schemas/Health/MapServer/3
"""
import datetime
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from arcgis import day, edited, features
from evidence import Writer, address

LAYER = "https://maps2.columbus.gov/arcgis/rest/services/Schemas/Health/MapServer/3"


def main():
    today = datetime.date.today()
    cutoff = int(datetime.datetime(today.year, today.month, today.day).timestamp() * 1000)
    out = Writer("cph_columbus_food")
    for a, (lat, lng) in features(LAYER, fields="FACILITY_ID,BUSINESS_NAME,SITE_ADDRESS,CITY,ZIP,BUS_TYPE_DESCR,PERMIT_TO_DATE"):
        if (a.get("BUS_TYPE_DESCR") or "").startswith(("MOBILE", "VENDING")):
            out.drop("mobile or vending")
            continue
        if not a.get("PERMIT_TO_DATE") or a["PERMIT_TO_DATE"] < cutoff:
            out.drop("permit ran out")
            continue
        out.row("cph_columbus_food", a.get("FACILITY_ID"), a.get("BUSINESS_NAME"),
                address(a.get("SITE_ADDRESS"), a.get("CITY"), "OH %s" % str(a.get("ZIP") or "")[:5]),
                lat, lng, "open", today.isoformat())
    out.close()


if __name__ == "__main__":
    main()
