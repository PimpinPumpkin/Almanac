#!/usr/bin/env python3
"""Texas Department of Licensing and Regulation: salon and barber shop licenses.

tdlr_tx  a licensed establishment (full service salon or barber shop, nail,
         esthetician and eyelash salons) whose license has not expired, open
         as of the day the dataset was last updated.

The dataset is mostly licenses held by people (operators, electricians,
technicians). Only establishment licenses are read, and only the business
name and business address. The position in the file is the city's center,
so addresses go to the Census geocoder.

Neither the dataset nor data.texas.gov states a license. Texas public record.
https://data.texas.gov/d/7358-krk7
"""
import datetime
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from evidence import Writer, address
from socrata import rows, updated

HOST, DATASET = "data.texas.gov", "7358-krk7"
CITY_ZIP = re.compile(r"^(.*?)\s+TX\s+(\d{5})")


def main():
    today = datetime.date.today()
    as_of = updated(HOST, DATASET)
    out = Writer("tdlr_tx")
    for r in rows(HOST, DATASET, where="license_type like '%Establishment'",
                  select="license_number,business_name,business_address_line1,business_city_state_zip,"
                         "license_expiration_date_mmddccyy"):
        try:
            expires = datetime.datetime.strptime(r.get("license_expiration_date_mmddccyy") or "", "%m/%d/%Y").date()
        except ValueError:
            out.drop("no expiration date")
            continue
        if expires < today:
            out.drop("license expired")
            continue
        m = CITY_ZIP.match(r.get("business_city_state_zip") or "")
        if not m:
            out.drop("address not in Texas")
            continue
        out.row("tdlr_tx", r["license_number"], r.get("business_name"),
                address(r.get("business_address_line1"), m.group(1), "TX %s" % m.group(2)),
                None, None, "open", as_of)
    out.close(geocode=True)


if __name__ == "__main__":
    main()
