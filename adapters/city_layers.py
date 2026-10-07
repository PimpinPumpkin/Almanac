#!/usr/bin/env python3
"""City license and inspection layers for six more cities.

phx_liquor   Phoenix: an active liquor license inside the city
nash_beer    Nashville: an issued beer permit
mke_food     Milwaukee: an unexpired food dealer license
mke_liquor   Milwaukee: an unexpired alcohol license
anc_liquor   Anchorage: a liquor license good for this year or later
sux_food     Sioux Falls: a food site, dated by its newest inspection
hsv_liquor   Huntsville: an active alcohol license renewed for this year
det_biz      Detroit: an unexpired city business license
det_liquor   Detroit: an active state liquor license in the city

All are open as of the day the layer was last edited (the day it was read
when the layer does not say), except Sioux Falls, which carries inspection
dates. Positions come with the data. Agent, owner and licensee columns are
not read.

Milwaukee's data is CC BY (City of Milwaukee). The others state no
license. Layer addresses are in SOURCES.md.
"""
import datetime
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from arcgis import day, edited, features
from evidence import Writer, address

TODAY = datetime.date.today()
NOW_MS = int(datetime.datetime(TODAY.year, TODAY.month, TODAY.day).timestamp() * 1000)
MKE = "https://milwaukeemaps.milwaukee.gov/arcgis/rest/services/regulation/license/MapServer/"
DET = "https://services2.arcgis.com/qvkbeam7Wirps6zC/arcgis/rest/services/"

# source: layers, filter, id fields, name fields (first one filled wins), street, city (a field or a fixed name),
# state, ZIP field, and a date field when the rows carry their own
SOURCES = {
    "phx_liquor": (["https://maps.phoenix.gov/pub/rest/services/Public/LIQUOR_RACMap/MapServer/%d" % i for i in range(14)],
                   "LICENSE_STATUS = 'ACTIVE' AND JURISDICTION = 'INSIDE PHOENIX'",
                   ("STATE_LICENSE", "ACCOUNT_ID"), ("BUSINESS_NAME",), "BUSINESS_ADDRESS", "=PHOENIX", "AZ", "ZIP_CODE", None),
    "nash_beer": (["https://services2.arcgis.com/HdTo6HJqh92wn4D8/arcgis/rest/services/Beer_Permit_Locations_Feature_Layer_view/FeatureServer/0"],
                  "Status = 'ISSUED'", ("Permit__",), ("Business_Name",), "Address", "City", "TN", "ZIP", None),
    "mke_food": ([MKE + "9"], "EXPIRATION_DATE > timestamp '%s 00:00:00'" % TODAY.isoformat(),
                 ("LICENSE_ID",), ("TRADE_NAME", "CORP_NAME"), "ENTITY_ADDRESS", "=MILWAUKEE", "WI", None, None),
    "mke_liquor": ([MKE + "0"], "EXPIRATION_DATE > timestamp '%s 00:00:00'" % TODAY.isoformat(),
                   ("LICENSE_ID",), ("TRADE_NAME", "CORP_NAME"), "ENTITY_ADDRESS", "=MILWAUKEE", "WI", None, None),
    "anc_liquor": (["https://services2.arcgis.com/Ce3DhLRthdwbHlfF/arcgis/rest/services/LiquorLicenses_Hosted/FeatureServer/0"],
                   "ExpirationYear >= '%d'" % TODAY.year,
                   ("LicenseNumber",), ("Establishment",), "ServiceLocation", "=ANCHORAGE", "AK", None, None),
    "sux_food": (["https://gis.siouxfalls.gov/arcgis/rest/services/Data/Safety/MapServer/17"],
                 "SITE_TYPE <> 'MOB'", ("SITE_INV",), ("SITE_NAME",), "FULL_ADDRESS", "=SIOUX FALLS", "SD", None, "INSP_DATE1"),
    "hsv_liquor": (["https://maps.huntsvilleal.gov/server/rest/services/Licenses/AlcoholBeverageLicenses/MapServer/0"],
                   "Status = 'ACTIVE' AND LastBusYear >= %d" % TODAY.year,
                   ("LocationID", "SchID"), ("LocDBA", "BusinessName"), "address_full", "MailCity", "AL", "ZipCode", None),
    "det_biz": ([DET + "bseed_active_business_licenses/FeatureServer/0"], "expiration_date >= '%s'" % TODAY.isoformat(),
                ("record_id",), ("business_name",), "address", "=DETROIT", "MI", "zip_code", None),
    "det_liquor": ([DET + "Liquor_Licenses/FeatureServer/0"], "status = 'Active'",
                   ("address_id", "type"), ("dba", "account_name"), "street_address", "=DETROIT", "MI", "zip_code", None),
}


def text(v):
    return "" if v is None else " ".join(str(v).split())


def main():
    out = Writer("city_layers")
    failed = []
    for source, (layers, where, ids, names, street, city, state, zip_field, dated) in sorted(SOURCES.items()):
        fields = ",".join(f for f in ids + names + (street, zip_field, dated, None if city.startswith("=") else city) if f)
        try:
            for layer in layers:
                as_of = edited(layer) or TODAY.isoformat()
                for a, (lat, lng) in features(layer, where=where, fields=fields):
                    name = next((text(a.get(n)) for n in names if text(a.get(n))), "")
                    town = city[1:] if city.startswith("=") else text(a.get(city))
                    when = day(a[dated]) if dated and isinstance(a.get(dated), (int, float)) else as_of
                    out.row(source, "-".join(text(a.get(i)) for i in ids), name,
                            address(text(a.get(street)), town, ("%s %s" % (state, text(a.get(zip_field))[:5])).strip()),
                            lat, lng, "open", when)
        except (Exception, SystemExit) as e:
            failed.append("%s: %s" % (source, e))
    if failed:
        # leave last run's file in place rather than publish some cities and drop others
        raise SystemExit("city_layers, sources that failed: " + "; ".join(failed))
    out.close()


if __name__ == "__main__":
    main()
