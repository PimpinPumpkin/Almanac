#!/usr/bin/env python3
"""State child care licensing layers: licensed child care centers.

childcare_<state>  a licensed child care center, open as of the day the
                   layer was last edited, or the day it was read when the
                   layer does not say.

One source per state: Arizona, California, Delaware, Massachusetts,
Michigan, Minnesota, New Jersey, Tennessee, Vermont, Wisconsin. Positions
come with the data. Every layer also lists family child care homes, which
are people's houses under people's names; only centers are read. Contact,
owner, director, phone and email columns are not read.

California's layer is CC BY (California Department of Social Services).
The others state no license. Layer addresses are in SOURCES.md.
"""
import datetime
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from arcgis import day, edited, features
from evidence import Writer, address

# state: layer, filter for centers, then the id, name, street, city and ZIP fields, then a date field if the rows carry one
LAYERS = {
    "AZ": ("https://services1.arcgis.com/mpVYz37anSdrK4d8/arcgis/rest/services/AZLicensedFacilities/FeatureServer/17",
           "TYPE = 'Child Care Center' AND OPERATION_STATUS = 'Active'",
           "LICENSE_NUMBER", "FACILITY_NAME", "ADDRESS", "CITY", "ZIP", "RUN_DATE"),
    "CA": ("https://services.arcgis.com/XLPEppdz2H9dOiqp/arcgis/rest/services/CDSS_CCL_Facilities/FeatureServer/0",
           # status 3 is "licensed"
           "STATUS = 3 AND (FAC_TYPE_DESC LIKE 'DAY CARE CENTER%' OR FAC_TYPE_DESC LIKE 'INFANT CENTER%' "
           "OR FAC_TYPE_DESC LIKE 'SCHOOL-AGE%')",
           "FAC_NBR", "NAME", "RES_STREET_ADDR", "RES_CITY", "RES_ZIP_CODE", None),
    "DE": ("https://enterprise.firstmap.delaware.gov/arcgis/rest/services/Society/DE_ChildCareCenters/FeatureServer/0",
           "RSR_TYPE_T = 'Licensed Child Care Center'",
           "RSR_RSRC_I", "RSR_RESO_1", "ADR_STREET", "ADR_CITYNA", "ZIPCODE", None),
    "MA": ("https://services1.arcgis.com/hGdibHYSPO59RG1h/arcgis/rest/services/Licensed_Child_Care_Programs/FeatureServer/0",
           "PROG_TYPE = 'Center-based Care' AND LICENSED_STATUS = 'Current'",
           "PROV_NUM", "PROG_NAME", "ADDRESS", "CITY", "ZIPCODE", None),
    "MI": ("https://utility.arcgis.com/usrsvcs/servers/a79c3b0caedf412599085941e2af91d4/rest/services/CSS/CSS_LARA/MapServer/5",
           "FacilityType = 'Center'",
           "LicenseNumber", "FacilityName", "StreetAddress", "City", "ZIPCode", None),
    "MN": ("https://enterprise.gisdata.mn.gov/aghost/rest/services/us_mn_state_mngeo/econ_child_care/FeatureServer/0",
           "license_type IN ('Child Care Center', 'Certified Child Care Center')",
           "license_number", "name_of_program", "addressline1", "city", "zip", None),
    "NJ": ("https://mapsdep.nj.gov/arcgis/rest/services/Features/Structures/MapServer/4",
           "1=1", "center_id", "center_name", "address", "city", "zip", None),
    "TN": ("https://services1.arcgis.com/YuVBSS7Y1of2Qud1/arcgis/rest/services/Active_ChildCare_Locations/FeatureServer/0",
           "Child_Care_Type IN ('Child Care Center', 'Drop-in Child Care Center') AND Provider_Status = 'Active'",
           "Provider_ID", "Provider_Name", "Street_Address", "City", "Zip", None),
    "VT": ("https://services.arcgis.com/YKJ5JtnaPQ2jDbX8/arcgis/rest/services/Vermont%20Child%20Care%20Provider%20Data/FeatureServer/0",
           "provider_program_type IN ('CBCCPP', 'Afterschool Child Care Program')",
           "provider_id", "provider_name", "address_1", "provider_town", "zip_code", None),
    "WI": ("https://dhsgis.wi.gov/server/rest/services/DHS_DCF/Child_Care/MapServer/0",
           "CategoryType IN ('LICENSED GROUP', 'PUBLIC SCHOOL PROGRAM')",
           "FacilityNumber", "FacilityName", "LocationLineAddress1", "City", "ZipCode", None),
}


def text(v):
    return "" if v is None else str(v).strip()


def main():
    today = datetime.date.today().isoformat()
    out = Writer("childcare_centers")
    failed = []
    for state, (layer, where, key, name, street, city, zip_code, dated) in sorted(LAYERS.items()):
        source = "childcare_" + state.lower()
        fields = ",".join(f for f in (key, name, street, city, zip_code, dated) if f)
        try:
            as_of = edited(layer) or today
            for a, (lat, lng) in features(layer, where=where, fields=fields):
                when = day(a[dated]) if dated and a.get(dated) else as_of
                out.row(source, text(a.get(key)).split(".")[0], text(a.get(name)),
                        address(text(a.get(street)), text(a.get(city)), "%s %s" % (state, text(a.get(zip_code))[:5])),
                        lat, lng, "open", when)
        except (Exception, SystemExit) as e:
            failed.append("%s: %s" % (state, e))
    if failed:
        # leave last run's file in place rather than publish some states and drop others
        raise SystemExit("childcare_centers, layers that failed: " + "; ".join(failed))
    out.close()


if __name__ == "__main__":
    main()
