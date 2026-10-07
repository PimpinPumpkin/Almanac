#!/usr/bin/env python3
"""Douglas County Health Department, Nebraska: restaurant inspections.

dchd_omaha_food  a food establishment in Douglas County, open as of the day
                 of its newest inspection. Positions come with the data.

Douglas County, Nebraska GIS. No license stated.
https://services.arcgis.com/pDAi2YK0L0QxVJHj/arcgis/rest/services/Restaurant_Inspections/FeatureServer/14
"""
import datetime
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from arcgis import day, edited, features
from evidence import Writer, address

LAYER = "https://services.arcgis.com/pDAi2YK0L0QxVJHj/arcgis/rest/services/Restaurant_Inspections/FeatureServer/14"


def main():
    newest = {}
    for a, pos in features(LAYER, fields="permit_number,est_name,est_address,est_city,est_zip,inspection_date"):
        when = (a.get("inspection_date") or "")[:10]
        if when and (a["permit_number"] not in newest or when > newest[a["permit_number"]][0]):
            newest[a["permit_number"]] = (when, a, pos)
    out = Writer("dchd_omaha_food")
    for permit, (when, a, (lat, lng)) in newest.items():
        out.row("dchd_omaha_food", permit, a.get("est_name"),
                address(a.get("est_address"), a.get("est_city"), "NE %s" % str(a.get("est_zip") or "")[:5]),
                lat, lng, "open", when)
    out.close()


if __name__ == "__main__":
    main()
