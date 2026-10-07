#!/usr/bin/env python3
"""Sacramento County Environmental Management: food facility inspections.

emd_sac  a food facility (restaurant, market, bar, food prep), open as of
         its most recent inspection. Positions come with the data.

A visit where the inspector could not get in is skipped, and so are mobile
food facilities, which have no fixed place.

Sacramento County Open Data. https://data.saccounty.gov
"""
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from arcgis import day, features
from evidence import Writer, address

LAYER = "https://services1.arcgis.com/5NARefyPVtAeuJPU/arcgis/rest/services/Food_Inspections/FeatureServer/0"
TAIL = re.compile(r"^(.*),\s*(.+?)\s+(\d{5})(-\d{4})?\s*$")


def main():
    out = Writer("emd_sac")
    for a, (lat, lng) in features(LAYER):
        if "UNABLE" in (a.get("Inspection_Type") or "") or "MOBILE" in (a.get("Description") or ""):
            out.drop("not inspected, or a mobile facility")
            continue
        m = TAIL.match(a.get("Facility_Address") or "")
        if not m or not a.get("Inspection_Date"):
            out.drop("no address or date")
            continue
        out.row("emd_sac", a["Facility_ID"], a.get("Facility_Name"),
                address(m.group(1), m.group(2).upper(), "CA %s" % m.group(3)),
                lat, lng, "open", day(int(a["Inspection_Date"])))
    out.close()


if __name__ == "__main__":
    main()
