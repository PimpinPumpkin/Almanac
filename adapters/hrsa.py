#!/usr/bin/env python3
"""HRSA: health center service delivery sites.

hrsa_health_centers  an active, permanent site of a federally funded health
                     center or look-alike, open as of the day the file was
                     made. Positions come with the data.

Mobile vans, seasonal and intermittent sites are left out, as are sites in
schools, which are rooms inside another place.

US government work, public domain.
https://data.hrsa.gov/data/download
"""
import csv
import datetime
import io
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from evidence import Writer, address, get

URL = "https://data.hrsa.gov/DataDownload/DD_Files/Health_Center_Service_Delivery_and_LookAlike_Sites.csv"


def main():
    out = Writer("hrsa")
    for r in csv.DictReader(io.StringIO(get(URL).decode("utf-8-sig", "replace"))):
        if r.get("Site Status Description") != "Active" or r.get("Health Center Location Type Description") != "Permanent":
            out.drop("not an active permanent site")
            continue
        if "School" in (r.get("Health Center Service Delivery Site Location Setting Description") or ""):
            out.drop("inside a school")
            continue
        try:
            made = datetime.datetime.strptime(r.get("Data Warehouse Record Create Date") or "", "%m/%d/%Y").date()
        except ValueError:
            made = datetime.date.today()
        out.row("hrsa_health_centers", r.get("BPHC Assigned Number"), r.get("Site Name"),
                address(r.get("Site Address"), r.get("Site City"),
                        "%s %s" % (r.get("Site State Abbreviation"), (r.get("Site Postal Code") or "")[:5])),
                r.get("Geocoding Artifact Address Primary Y Coordinate"),
                r.get("Geocoding Artifact Address Primary X Coordinate"), "open", made.isoformat())
    out.close()


if __name__ == "__main__":
    main()
