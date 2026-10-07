#!/usr/bin/env python3
"""City and County of Denver: active business licenses.

biz_denver  an active license for a shop-front business (retail food and
            combined food and liquor, tobacco and marijuana stores, repair
            garages, lodging, body art, kennels, dry cleaners and the like),
            open as of the layer's report date.

Four in five rows of this dataset are residential and short-term rental
licenses, which are not read. No usable positions; addresses go to the
Census geocoder.

City and County of Denver Open Data. https://opendata-geospatialdenver.hub.arcgis.com
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from arcgis import day, features
from evidence import Writer, address

LAYER = "https://services1.arcgis.com/zdB7qR0BtYrg0Xpl/arcgis/rest/services/ODC_active_business_licenses/FeatureServer/42"
KINDS = ("Retail Food", "Combined License", "Retail Tobacco Store", "Marijuana Store",
         "Garage - Repair of Motor Vehic", "Liquor", "Body Art Est - Permanent", "Kennel", "Second Hand Dealer",
         "Massage Business", "Lodging Facility", "Dry Cleaning Establishment", "Amusement Facility - Permanent",
         "Pawnbroker")


def main():
    out = Writer("biz_denver")
    seen = set()
    kinds = ", ".join("'%s'" % k for k in KINDS)
    for a, _ in features(LAYER, where="LICENSE_STATUS LIKE 'License Issued%%' AND LICENSE_TYPE IN (%s)" % kinds,
                         fields="BFN,TRADE_NAME,ENTITY_NAME,AddressNoUnit,ZIP,REPORT_DATE", geometry=False):
        name = (a.get("TRADE_NAME") or a.get("ENTITY_NAME") or "").strip()
        street = (a.get("AddressNoUnit") or "").strip()
        # one business holds several licenses at an address
        if (name.upper(), street) in seen:
            continue
        seen.add((name.upper(), street))
        out.row("biz_denver", a["BFN"], name, address(street, "DENVER", "CO %s" % str(a.get("ZIP") or "")[:5]),
                None, None, "open", day(int(a["REPORT_DATE"])))
    out.close(geocode=True)


if __name__ == "__main__":
    main()
