#!/usr/bin/env python3
"""New York Agriculture and Markets: food safety inspections of retail food stores.

agm_ny  a grocery, deli, bakery or other retail food store, open as of its
        newest inspection in the file. An inspector was in the store that
        day. Positions come with the data. The owner's name is not read.

OPEN-NY Terms of Use (see SOURCES.md).
https://data.ny.gov/d/d6dy-3h7r
"""
import hashlib
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from evidence import Writer, address
from socrata import point, rows

HOST, DATASET = "data.ny.gov", "d6dy-3h7r"


def main():
    newest = {}
    for r in rows(HOST, DATASET, select="trade_name,street,city,zipcode,inspection_date,georeference",
                  where="statecode = 'NY'"):
        k = ((r.get("trade_name") or "").upper(), (r.get("street") or "").upper(), r.get("zipcode"))
        if (r.get("inspection_date") or "") > newest.get(k, {}).get("inspection_date", ""):
            newest[k] = r
    out = Writer("agm_ny")
    for k, r in newest.items():
        lat, lng = point(r.get("georeference"))
        out.row("agm_ny", hashlib.sha1("|".join(map(str, k)).encode()).hexdigest()[:16], r.get("trade_name"),
                address(r.get("street"), r.get("city"), "NY %s" % (r.get("zipcode") or "")[:5]),
                lat, lng, "open", r["inspection_date"][:10])
    out.close()


if __name__ == "__main__":
    main()
