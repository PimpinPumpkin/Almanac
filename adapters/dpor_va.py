#!/usr/bin/env python3
"""Virginia Department of Professional and Occupational Regulation: salons,
barber shops, spas and tattoo and piercing parlors.

dpor_va  a current shop license (cosmetology, nail and waxing salons,
         barber shops, esthetics spas, tattoo parlors, body piercing
         salons), open as of the day the lists were read.

The department publishes one list of current licenses per occupation; only
the shop occupations are read, not the lists of people or schools. A shop
owned by one person can carry that person's name as its business name, so
nothing here creates a place. The individual name and email columns are
not read. No positions; addresses go to the Census geocoder.

"Provided free of charge in electronic format"; no license stated.
https://www.dpor.virginia.gov/RegulantLists
"""
import csv
import datetime
import io
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from evidence import Writer, address, get

URL = "https://www.dpor.virginia.gov/sites/default/files/Records%%20and%%20Documents/Regulant%%20List/%s__crnt.txt"
# cosmetology salon, nail salon, waxing salon, barber shop, tattoo parlor, limited tattoo parlor,
# permanent cosmetic tattoo salon, body piercing salon, esthetics spa
LISTS = ("1202", "1208", "1218", "1304", "1232", "1235", "1238", "1242", "1266")


def main():
    today = datetime.date.today()
    out = Writer("dpor_va")
    seen = set()
    for code in LISTS:
        text = get(URL % code).decode("cp1252", "replace")
        for r in csv.DictReader(io.StringIO(text), delimiter="\t", quoting=csv.QUOTE_NONE):
            if (r.get("STATE") or "").strip() != "VA":
                continue
            try:
                if datetime.datetime.strptime((r.get("EXPIRATION DATE") or "").strip(), "%m/%d/%Y").date() < today:
                    out.drop("expired")
                    continue
            except ValueError:
                pass
            name, street = (r.get("BUSINESS NAME") or "").strip(), (r.get("FIRST LINE ADDRESS") or "").strip()
            # a salon that also holds a barber shop license
            if (name.upper(), street.upper()) in seen:
                continue
            seen.add((name.upper(), street.upper()))
            out.row("dpor_va", "%s-%s" % (code, (r.get("CERTIFICATE #") or "").strip()), name,
                    address(street, r.get("CITY"), "VA %s" % (r.get("FIVE DIGIT ZIP CODE") or "").strip()[:5]),
                    None, None, "open", today.isoformat())
    out.close(geocode=True)


if __name__ == "__main__":
    main()
