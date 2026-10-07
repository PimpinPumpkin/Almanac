#!/usr/bin/env python3
"""City of Seattle: active business license locations.

biz_seattle  an active business location in a storefront trade (retail,
             food and lodging, repair and personal services, recreation),
             open as of the day the layer was last edited. Positions come
             with the data.

Every business working in Seattle holds one of these, so the file is full
of contractors, consultants and people working from home. Only storefront
trades are read (by industry code), only the trade name and location
address, never the contact fields, and nothing here creates a place.

City of Seattle Open Data. https://data.seattle.gov
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from arcgis import edited, features
from evidence import Writer

LAYER = "https://services.arcgis.com/ZOyb2t4B0UYuYNYH/arcgis/rest/services/Seattle_Business_License/FeatureServer/0"
# NAICS sectors: 44-45 retail, 71 recreation, 72 food and lodging, 81 repair and personal services
WHERE = ("BUSLIC_STATUS_TYPE = 'ACTIVE' AND (BUSLIC_NAICS_CODE LIKE '44%' OR BUSLIC_NAICS_CODE LIKE '45%' "
         "OR BUSLIC_NAICS_CODE LIKE '71%' OR BUSLIC_NAICS_CODE LIKE '72%' OR BUSLIC_NAICS_CODE LIKE '81%') "
         "AND BUSLIC_NAICS_CODE NOT LIKE '454%'")


def main():
    as_of = edited(LAYER)
    out = Writer("biz_seattle")
    for a, (lat, lng) in features(LAYER, where=WHERE,
                                  fields="BUSLIC_LOCATION_ID,BUSLIC_TRADE_NAME,BUSLIC_LOCATION_ADRS_TEXT"):
        # "4310 FREMONT AVE N, SEATTLE, WA 98103-7224" -> zip cut to five digits
        where = (a.get("BUSLIC_LOCATION_ADRS_TEXT") or "").strip().split("-")[0]
        out.row("biz_seattle", a["BUSLIC_LOCATION_ID"], a.get("BUSLIC_TRADE_NAME"), where, lat, lng, "open", as_of)
    out.close()


if __name__ == "__main__":
    main()
