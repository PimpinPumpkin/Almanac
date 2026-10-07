#!/usr/bin/env python3
"""Louisville Metro, Kentucky: restaurant inspection scores.

lou_food  a food service establishment, open as of its newest inspection in
          the file. No positions; addresses go to the Census geocoder.

Louisville Metro Open Data. https://data.louisvilleky.gov
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from arcgis import features
from evidence import Writer, address

LAYER = "https://services1.arcgis.com/79kfd2K6fskCAkyg/arcgis/rest/services/FoodServiceData/FeatureServer/0"


def main():
    newest = {}
    for a, _ in features(LAYER, fields="EstablishmentID,EstablishmentName,Address,City,Zip,InspectionDate",
                         geometry=False):
        if (a.get("InspectionDate") or "") > newest.get(a["EstablishmentID"], {}).get("InspectionDate", ""):
            newest[a["EstablishmentID"]] = a
    out = Writer("lou_food")
    for eid, a in newest.items():
        out.row("lou_food", eid, a.get("EstablishmentName"),
                address(a.get("Address"), (a.get("City") or "").upper(), "KY %s" % str(a.get("Zip") or "")[:5]),
                None, None, "open", str(a["InspectionDate"])[:10])
    out.close(geocode=True)


if __name__ == "__main__":
    main()
