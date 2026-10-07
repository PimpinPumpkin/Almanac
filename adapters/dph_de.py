#!/usr/bin/env python3
"""Delaware Division of Public Health: food establishment inspections.

dph_de  a restaurant or other food establishment, open as of its newest
        inspection in the file. Positions come with the data.

The file lists one row per violation found; only the place and the date are
read.

Public domain, as stated on the dataset.
https://data.delaware.gov/d/384s-wygj
"""
import hashlib
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from evidence import Writer, address
from socrata import point, rows

HOST, DATASET = "data.delaware.gov", "384s-wygj"


def main():
    newest = {}
    for r in rows(HOST, DATASET, select="restname,restaddress,restcity,restzip,insp_date,geocoded_column"):
        k = ((r.get("restname") or "").upper(), (r.get("restaddress") or "").upper())
        if (r.get("insp_date") or "") > newest.get(k, {}).get("insp_date", ""):
            newest[k] = r
    out = Writer("dph_de")
    for k, r in newest.items():
        lat, lng = point(r.get("geocoded_column"))
        out.row("dph_de", hashlib.sha1("|".join(k).encode()).hexdigest()[:16], r.get("restname"),
                address(r.get("restaddress"), (r.get("restcity") or "").upper(), "DE %s" % (r.get("restzip") or "")[:5]),
                lat, lng, "open", r["insp_date"][:10])
    out.close(geocode=True)


if __name__ == "__main__":
    main()
