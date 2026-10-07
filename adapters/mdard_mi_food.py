#!/usr/bin/env python3
"""Michigan Department of Agriculture and Rural Development: food service
licenses.

mdard_mi_food  a restaurant or other fixed food service establishment with
               an active license, open as of the day the layer was read.
               Positions come with the data.

These are the licenses local health departments issue for restaurants.
Mobile units, temporary events and vending are left out. Retail food
stores are not in this list. The organization columns are not read.

Michigan public record. No license stated.
https://gisagomdard.state.mi.us/arcgis/rest/services/MDARD/RestaurantsCommissariesOpenData/FeatureServer/0
"""
import datetime
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from arcgis import day, edited, features
from evidence import Writer, address

LAYER = "https://gisagomdard.state.mi.us/arcgis/rest/services/MDARD/RestaurantsCommissariesOpenData/FeatureServer/0"
NOT_FIXED = ("mobile", "temporary", "transitory", "vending", "special")


def main():
    as_of = edited(LAYER) or datetime.date.today().isoformat()
    out = Writer("mdard_mi_food")
    for a, (lat, lng) in features(LAYER, where="CurrentLicenseStatus = 'Active'",
                                  fields="Licensekey,LicensetypeName,LocationName,AddressLine1,City,Zip,LocationLatitude,LocationLongitude"):
        if any(k in (a.get("LicensetypeName") or "").lower() for k in NOT_FIXED):
            out.drop("not a fixed establishment")
            continue
        out.row("mdard_mi_food", a.get("Licensekey"), a.get("LocationName"),
                address(a.get("AddressLine1"), a.get("City"), "MI %s" % str(a.get("Zip") or "")[:5]),
                lat or a.get("LocationLatitude"), lng or a.get("LocationLongitude"), "open", as_of)
    out.close()


if __name__ == "__main__":
    main()
