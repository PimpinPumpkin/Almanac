#!/usr/bin/env python3
"""Florida DBPR: licensed salons, barbershops, veterinary premises, hotels
and restaurants.

dbpr_fl_salon       a current cosmetology salon or barbershop license
dbpr_fl_vet         a current veterinary establishment permit
dbpr_fl_lodging     a current hotel, motel or bed and breakfast license
dbpr_fl_restaurant  a current license for a restaurant with fixed premises

All are open as of the day the files were read. The salon, barber and
veterinary files are mostly people (cosmetologists, barbers,
veterinarians); only the establishment license types are read, and only
the establishment's name and street, not the owner lines. Vacation
rentals, condominiums and apartments in the lodging files are people's
homes and are not read, nor are caterers, mobile vendors and temporary
events in the restaurant files. Nothing here creates a place. No
positions; addresses go to the Census geocoder.

Florida public records; the download pages state no license.
https://www2.myfloridalicense.com/cosmetology/public-records/
https://www2.myfloridalicense.com/barbers/public-records/
https://www2.myfloridalicense.com/veterinary-medicine/public-records/
https://www2.myfloridalicense.com/hotels-restaurants/public-records/
"""
import csv
import datetime
import io
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from evidence import Writer, address, get

BASE = "https://www2.myfloridalicense.com/sto/file_download/extracts/"
# profession files have no header row: occupation, name, three address lines, city, state, zip, license, statuses, expiry
OCC, NAME, LINES, CITY, STATE, ZIP, PRIMARY, SECONDARY, EXPIRY, LICENSE = 1, 2, (5, 6, 7), 8, 9, 10, 13, 14, 17, 20
PROFESSIONS = (("COSMETOLOGYLICENSE_1.csv", {"CE"}, "dbpr_fl_salon"),
               ("lic03bb.csv", {"BS"}, "dbpr_fl_salon"),
               ("lic26vt.csv", {"VE"}, "dbpr_fl_vet"))
# hotel and restaurant files come one per district, with a header row
DISTRICTS = range(1, 8)
PREMISES = (("hrlodge%d.csv", {"HOTL", "MOTL", "BNB"}, "dbpr_fl_lodging"),
            ("hrfood%d.csv", {"SEAT", "NOST"}, "dbpr_fl_restaurant"))
CURRENT = "20"


def main():
    today = datetime.date.today()
    out = Writer("dbpr_fl_licenses")
    for name, kinds, source in PROFESSIONS:
        for r in csv.reader(io.StringIO(get(BASE + name).decode("latin-1"))):
            if len(r) <= LICENSE or r[OCC] not in kinds:
                continue
            expiry = r[EXPIRY].strip()
            if r[PRIMARY] != "C" or r[SECONDARY] not in ("A", "") or r[STATE] != "FL" or (
                    expiry and datetime.datetime.strptime(expiry, "%m/%d/%Y").date() < today):
                out.drop("not a current Florida license")
                continue
            # an owner's name sometimes sits on the line before the street
            street = next((r[i] for i in LINES if r[i][:1].isdigit()), "")
            out.row(source, r[LICENSE], r[NAME], address(street, r[CITY], "FL %s" % r[ZIP][:5]),
                    None, None, "open", today.isoformat())
    for pattern, kinds, source in PREMISES:
        for d in DISTRICTS:
            for r in csv.DictReader(io.StringIO(get(BASE + pattern % d).decode("latin-1"))):
                if r.get("Rank Code") not in kinds:
                    continue
                if r.get("Primary Status Code") != CURRENT or r.get("Location State Code") != "FL":
                    out.drop("not a current Florida license")
                    continue
                out.row(source, r["License Number"], r.get("Business Name") or r.get("Licensee Name"),
                        address(r.get("Location Street Address"), r.get("Location City"),
                                "FL %s" % (r.get("Location Zip Code") or "")[:5]),
                        None, None, "open", today.isoformat())
    out.close(geocode=True)


if __name__ == "__main__":
    main()
