#!/usr/bin/env python3
"""City of Las Vegas: active business licenses.

biz_lasvegas  an active license for a business inside the city limits, open
              as of the day the layer was last edited.

Every business in the city holds one. Contractors, consultants, real estate
agents, home and mobile businesses, landlords and machine operators are
left out, only the business name and address are read (not the owner or the
phone number), and nothing here creates a place. The list also marks
105,000 licenses "Closed" but gives no date for it, so those are not used.
No positions; addresses go to the Census geocoder.

City of Las Vegas Open Data. No license stated.
https://opendataportal-lasvegas.opendata.arcgis.com
"""
import datetime
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from arcgis import day, edited, features
from evidence import Writer, address

LAYER = "https://services1.arcgis.com/F1v0ufATbBQScMtY/arcgis/rest/services/Business_Licenses_OpenData/FeatureServer/0"
NOT_A_SHOP = ("contractor", "real estate", "consulting", "apartment", "residential", "mobile", "independent",
              "coin amusement", "automated teller", "public utility", "promoter", "wire service", "rent or lease",
              "home ", "peddler", "solicitor", "transportation", "delivery")


def main():
    as_of = edited(LAYER)
    out = Writer("biz_lasvegas")
    seen = set()
    for a, _ in features(LAYER, where="Status = 'Active' AND Within_City_Limits = 'Inside'",
                         fields="License__,Business_Name,Type_of_Business,Address,Zip_Code", geometry=False):
        kind = (a.get("Type_of_Business") or "").lower()
        if any(k in kind for k in NOT_A_SHOP):
            out.drop("not a shop-front trade")
            continue
        # one license per line of business at the same counter
        key = ((a.get("Business_Name") or "").upper(), a.get("Address"))
        if key in seen:
            continue
        seen.add(key)
        out.row("biz_lasvegas", a.get("License__"), a.get("Business_Name"),
                address(a.get("Address"), "LAS VEGAS", "NV %s" % str(a.get("Zip_Code") or "")[:5]),
                None, None, "open", as_of)
    out.close(geocode=True)


if __name__ == "__main__":
    main()
