#!/usr/bin/env python3
"""Oklahoma ABLE Commission: licensees by license type.

able_ok  premises holding a mixed beverage, beer and wine, retail spirits,
         retail beer, retail wine, brew pub or hotel beverage license that
         has not expired, open as of the day the lists were read.

The commission posts one list per license type each month. Wholesalers,
manufacturers, caterers and the other types are not read. No positions;
addresses go to the Census geocoder.

Oklahoma public record. No license stated.
https://oklahoma.gov/able-commission/brand-registration/brand-registration-reports/listing-of-licensees-by-license-type.html
"""
import datetime
import html
import os
import quopri
import re
import sys
import urllib.parse

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from evidence import Writer, address, get
from xlsx import day, rows

PAGE = ("https://oklahoma.gov/able-commission/brand-registration/brand-registration-reports/"
        "listing-of-licensees-by-license-type.html")
KINDS = ("Mixed_Beverage", "Beer_and_Wine", "Retail_Spirits_Store", "Retail_Beer", "Retail_Wine", "Brew_Pub",
         "Hotel_Beverage")
LINK = re.compile(r'href="([^"]*/(?:%s)_Licensee_List\.xlsx?)"' % "|".join(KINDS), re.I)
ROW = re.compile(r"<tr[^>]*>(.*?)</tr>", re.S | re.I)
CELL = re.compile(r"<t[dh][^>]*>(.*?)</t[dh]>", re.S | re.I)


def table(data):
    """Rows of one list. Some are real spreadsheets; most are a web page saved with an .xls name."""
    if data[:2] == b"PK":
        return rows(data)
    text = quopri.decodestring(data).decode("utf-8", "replace")
    return ([html.unescape(re.sub(r"<[^>]+>", "", c)).strip() for c in CELL.findall(r)] for r in ROW.findall(text))


def main():
    today = datetime.date.today().isoformat()
    links = sorted(set(LINK.findall(get(PAGE).decode("utf-8", "replace"))))
    if len(links) < 4:
        raise SystemExit("able_ok: expected the monthly lists, found %d links" % len(links))
    out = Writer("able_ok")
    seen = set()
    for link in links:
        col = None
        for r in table(get(urllib.parse.urljoin(PAGE, link))):
            if col is None:
                if "DBA NAME" in r:
                    # the street column is named differently from list to list
                    r = ["FULL ADDRESS" if c == "STREET NBR" else c for c in r]
                    col = {name: r.index(name) for name in ("License #", "DBA NAME", "FULL ADDRESS", "CITY", "STATE", "ZIP", "DATE EXPIRATION")}
                continue
            if len(r) <= max(col.values()) or r[col["STATE"]] != "OK":
                continue
            expires = r[col["DATE EXPIRATION"]]
            expires = day(expires) if re.fullmatch(r"[\d.]+", expires) else expires[:10]
            if expires and expires < today and re.fullmatch(r"\d{4}-\d\d-\d\d", expires):
                out.drop("expired")
                continue
            # a bar can hold more than one type of license
            key = (r[col["DBA NAME"]].upper(), r[col["FULL ADDRESS"]].upper())
            if key in seen:
                continue
            seen.add(key)
            out.row("able_ok", r[col["License #"]], r[col["DBA NAME"]],
                    address(r[col["FULL ADDRESS"]], r[col["CITY"]], "OK %s" % r[col["ZIP"]][:5]),
                    None, None, "open", today)
    out.close(geocode=True)


if __name__ == "__main__":
    main()
