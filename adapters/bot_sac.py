#!/usr/bin/env python3
"""City of Sacramento: Business Operation Tax accounts.

bot_sac  an account with status Active at a Sacramento address, open as of
         the day the layer was last edited.

The city also records a close date for closed accounts, but it is not
emitted. Tested in the Sacramento box on places with no brand and no active
account under the same name: other evidence said still open 33 times and
closed 33.

Every business in the city holds one of these, including people who work
from home, so nothing here creates a place. The owner and mailing fields
are not read. No positions; addresses go to the Census geocoder.

City of Sacramento Open Data. https://data.cityofsacramento.org
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from arcgis import edited, features
from evidence import Writer, address

LAYER = ("https://services5.arcgis.com/54falWtcpty3V47Z/arcgis/rest/services/"
         "account_data_with_header_NEW/FeatureServer/0")
FIELDS = ("Account_Number,Business_Name,Location_Street_Number,Location_Direction,Location_Street_Name,"
          "Location_Street_Type,Location_City,Location_Zip_code")


def main():
    as_of = edited(LAYER)
    out = Writer("bot_sac")
    for a, _ in features(LAYER, where="Current_License_Status = 'Active' AND Location_State = 'CA'",
                         fields=FIELDS, geometry=False):
        street = " ".join(str(a.get(k) or "").strip() for k in
                          ("Location_Street_Number", "Location_Direction", "Location_Street_Name", "Location_Street_Type"))
        out.row("bot_sac", a["Account_Number"], a.get("Business_Name"),
                address(" ".join(street.split()), (a.get("Location_City") or "").upper(),
                        "CA %s" % (a.get("Location_Zip_code") or "")[:5]),
                None, None, "open", as_of)
    out.close(geocode=True)


if __name__ == "__main__":
    main()
