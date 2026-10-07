#!/usr/bin/env python3
"""South Carolina retail food establishment inspections ("Food Grades").

dph_sc_food  a permitted retail food establishment, open as of the day of
             its newest inspection. Positions come with the data.

The tables behind the state's food grades map: the inspection table gives
each active permit's newest inspection, the facility layer gives its
position. The data runs some months behind, and each row is dated by its
own inspection, never later.

South Carolina public record. No license stated.
https://dataviz.dph.sc.gov/foodgrades/
"""
import datetime
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from arcgis import day, edited, features
from evidence import Writer, address

BASE = "https://services5.arcgis.com/G4BLIH7rTQoIjCFv/arcgis/rest/services/Restaurants/FeatureServer/"
PLACES, INSPECTIONS = BASE + "0", BASE + "4"


def main():
    where = {a["PERMIT_ID"]: pos for a, pos in features(PLACES, fields="PERMIT_ID")}
    newest = {}
    for a, _ in features(INSPECTIONS, where="Active = 'True'",
                         fields="PERMIT_ID,FACILITY,ADDRESS,CITY,ZIPCODE,INSP_DATE", geometry=False):
        when, key = a.get("INSP_DATE"), a.get("PERMIT_ID")
        if when and (key not in newest or when > newest[key][0]):
            newest[key] = (when, a)
    out = Writer("dph_sc_food")
    for key, (when, a) in newest.items():
        lat, lng = where.get(key, (None, None))
        out.row("dph_sc_food", key, a.get("FACILITY"),
                address(a.get("ADDRESS"), a.get("CITY"), "SC %s" % str(a.get("ZIPCODE") or "")[:5]),
                lat, lng, "open", day(when))
    out.close()


if __name__ == "__main__":
    main()
