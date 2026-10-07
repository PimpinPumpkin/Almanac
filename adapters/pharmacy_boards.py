#!/usr/bin/env python3
"""State boards of pharmacy: licensed pharmacies in Texas and Ohio.

bop_tx  an active community pharmacy in Texas, open as of the day the file
        was read
bop_oh  an active pharmacy in Ohio (the board's "terminal distributor"
        licenses whose category is a pharmacy), open as of the day the
        file was read

Hospital, clinic, mail order and out-of-state licenses are left out. The
pharmacist-in-charge and responsible person columns are not read. No
positions; addresses go to the Census geocoder.

State public records. No license stated.
https://www.pharmacy.texas.gov/dbsearch/tables.asp
https://www.pharmacy.ohio.gov/licensing/rosterrequests
"""
import csv
import datetime
import io
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from evidence import Writer, address, get
from xlsx import rows

TX = "https://www.pharmacy.texas.gov/downloads/phydsk.csv"
OH = "https://www.pharmacy.ohio.gov/licensing/rosterrequests.aspx?listid=7"


def main():
    today = datetime.date.today().isoformat()
    out = Writer("pharmacy_boards")
    for r in csv.DictReader(io.StringIO(get(TX).decode("cp1252", "replace"))):
        if r.get("STATE") != "TX" or r.get("LIC_STATUS") != "Active" or r.get("CLASS") != "Community Pharmacy":
            continue
        out.row("bop_tx", r.get("LIC_NBR"), r.get("PHARMACY_NAME"),
                address(r.get("ADDRESS1"), r.get("CITY"), "TX %s" % (r.get("ZIP") or "")[:5]), None, None, "open", today)

    table = rows(get(OH))
    head = next(table)
    col = {name: head.index(name) for name in (
        "LicenseNumber", "LicenseType", "LicenseTypeSubCategory", "LicenseStatus", "BusinessName", "DoingBusinessAs",
        "LocationStreetAddress", "LocationCity", "LocationState", "LocationZip")}
    for r in table:
        r = r + [""] * (len(head) - len(r))
        kind = (r[col["LicenseType"]] + " " + r[col["LicenseTypeSubCategory"]]).lower()
        if r[col["LocationState"]] not in ("OH", "Ohio") or r[col["LicenseStatus"]] != "Active":
            continue
        if "pharmacy" not in kind or any(k in kind for k in ("non-resident", "mail order", "hospital", "institution")):
            out.drop("Ohio license that is not a retail pharmacy")
            continue
        out.row("bop_oh", r[col["LicenseNumber"]], r[col["DoingBusinessAs"]] or r[col["BusinessName"]],
                address(r[col["LocationStreetAddress"]], r[col["LocationCity"]], "OH %s" % r[col["LocationZip"]][:5]),
                None, None, "open", today)
    out.close(geocode=True)


if __name__ == "__main__":
    main()
