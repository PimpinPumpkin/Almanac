#!/usr/bin/env python3
"""City of Minneapolis: food inspections and liquor licenses.

mpls_food    a licensed food facility, open as of the day of its newest
             inspection.
mpls_liquor  an approved on-sale or off-sale liquor license, open as of the
             day the layer was last edited.

Positions come with the data.

City of Minneapolis Open Data. https://opendata.minneapolismn.gov
"""
import datetime
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from arcgis import day, edited, features
from evidence import Writer, address

BASE = "https://services.arcgis.com/afSMGVsC7QlRK1kZ/arcgis/rest/services/"
FOOD = BASE + "Food_Inspections/FeatureServer/0"
LIQUOR = (BASE + "On_Sale_Liquor/FeatureServer/0", BASE + "Off_Sale_Liquor/FeatureServer/0")


def main():
    out = Writer("minneapolis_mn")
    newest = {}
    # one row per violation; keep the newest inspection of each facility
    for a, pos in features(FOOD, fields="HealthFacilityIDNumber,BusinessName,FullAddress,City,ZipCode,DateOfInspection"):
        when, key = a.get("DateOfInspection"), a.get("HealthFacilityIDNumber")
        if when and (key not in newest or when > newest[key][0]):
            newest[key] = (when, a, pos)
    for key, (when, a, (lat, lng)) in newest.items():
        out.row("mpls_food", key, a.get("BusinessName"),
                address(a.get("FullAddress"), (a.get("City") or "").upper(), "MN %s" % str(a.get("ZipCode") or "")[:5]),
                lat, lng, "open", day(when))
    for layer in LIQUOR:
        as_of = edited(layer)
        for a, (lat, lng) in features(layer, where="licenseStatus IN ('Approved', 'Active')",
                                      fields="licenseNumber,licenseName,address"):
            out.row("mpls_liquor", a.get("licenseNumber"), a.get("licenseName"),
                    address(a.get("address"), "MINNEAPOLIS", "MN"), lat, lng, "open", as_of)
    out.close()


if __name__ == "__main__":
    main()
