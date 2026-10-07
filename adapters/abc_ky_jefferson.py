#!/usr/bin/env python3
"""Kentucky ABC licenses in Jefferson County (Louisville).

abc_ky_jefferson  an active state alcohol license for a retail premises in
                  Jefferson County, open as of the day the layer was last
                  edited. Positions come with the data.

Supplier, storage, transport, shipper, caterer, sampling, auction and
tobacco licenses are left out, as are supplements to another license. The
layer covers one county; Kentucky's statewide list is not published as data.

Louisville Metro Open Data. https://data.louisvilleky.gov
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from arcgis import edited, features
from evidence import Writer, address

LAYER = "https://services1.arcgis.com/79kfd2K6fskCAkyg/arcgis/rest/services/ABC_State_ActiveLicenses/FeatureServer/0"
NOT_A_PREMISES = ("supplier", "storage", "transporter", "shipper", "caterer", "sampling", "auction", "tobacco",
                  "supplemental", "special sunday", "extended hours", "wholesaler", "bottling", "temporary",
                  "vintage", "in-room")


def main():
    as_of = edited(LAYER)
    out = Writer("abc_ky_jefferson")
    seen = set()
    for a, (lat, lng) in features(LAYER, where="Status = 'Active'"):
        if any(word in (a.get("LicenseType") or "").lower() for word in NOT_A_PREMISES):
            out.drop("not a retail premises license")
            continue
        # one site holds several licenses
        if a.get("SiteID") in seen:
            continue
        seen.add(a.get("SiteID"))
        out.row("abc_ky_jefferson", a.get("SiteID"), a.get("DBA") or a.get("Licensee"),
                address(a.get("PremisesStreet"), a.get("PremisesCityState")),
                lat, lng, "open", as_of)
    out.close()


if __name__ == "__main__":
    main()
