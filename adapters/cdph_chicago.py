#!/usr/bin/env python3
"""Chicago Department of Public Health: food inspections.

cdph_chicago      a licensed food business whose newest inspection was a
                  pass, a conditional pass or a fail: open as of that day,
                  because an inspector got in.
cdph_chicago_oob  newest inspection result "Out of Business": closed on the
                  day of that visit.

"No Entry", "Not Ready" and "Business Not Located" say nothing either way
and are skipped. Only inspections from the last five years are read.
Positions come with the data.

City of Chicago Data Portal, see its Terms of Use.
https://data.cityofchicago.org/d/4ijn-s7e5
"""
import datetime
import json
import os
import sys
import urllib.parse

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from evidence import Writer, address, get

ROWS = "https://data.cityofchicago.org/resource/4ijn-s7e5.json"
PAGE = 50000
OPEN = {"Pass", "Pass w/ Conditions", "Fail"}
CLOSED = {"Out of Business"}


def main():
    since = (datetime.date.today() - datetime.timedelta(days=5 * 365)).isoformat()
    newest, offset = {}, 0
    while True:
        q = {"$select": "license_,dba_name,aka_name,address,zip,inspection_date,results,latitude,longitude",
             "$where": "inspection_date > '%s' AND license_ IS NOT NULL" % since,
             "$order": "inspection_id", "$limit": PAGE, "$offset": offset}
        rows = json.loads(get(ROWS + "?" + urllib.parse.urlencode(q)))
        for r in rows:
            if r.get("results") not in OPEN | CLOSED or r.get("license_") in (None, "0"):
                continue
            k = r["license_"]
            if r["inspection_date"] > newest.get(k, {"inspection_date": ""})["inspection_date"]:
                newest[k] = r
        offset += len(rows)
        if len(rows) < PAGE:
            break
    out = Writer("cdph_chicago")
    for lic, r in newest.items():
        closed = r["results"] in CLOSED
        out.row("cdph_chicago_oob" if closed else "cdph_chicago", lic, r.get("aka_name") or r.get("dba_name"),
                address((r.get("address") or "").strip(), "CHICAGO", "IL %s" % (r.get("zip") or "")[:5]),
                r.get("latitude"), r.get("longitude"), "closed" if closed else "open", r["inspection_date"][:10])
    out.close()


if __name__ == "__main__":
    main()
