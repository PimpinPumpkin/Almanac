#!/usr/bin/env python3
"""Minnesota Department of Agriculture: retail food handler licenses.

mda_mn_food  a grocery, convenience store, bakery, meat market or other
             retail food handler holding an unexpired license, open as of
             the day the list was read.

Restaurants are licensed by the health department or by cities and are not
in this list. No positions; addresses go to the Census geocoder.

Minnesota public record. No license stated.
https://www2.mda.state.mn.us/webapp/lis/default.jsp
"""
import csv
import datetime
import io
import os
import re
import sys
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from evidence import UA, Writer, address

URL = "https://www2.mda.state.mn.us/webapp/lis/LisResults.jsp"
# the license lookup's own "download as text" button, for unexpired retail food handler licenses in every county
FORM = {"license": "", "compname": "", "city": "", "countycode": "****", "lictype": "110", "unexpiredonly": "Y",
        "holderonly": "Y", "sortorder": "1", "cmd": "Download As Text"}


def main():
    today = datetime.date.today().isoformat()
    req = urllib.request.Request(URL, data=urllib.parse.urlencode(FORM).encode(), headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=300) as r:
        text = r.read().decode("cp1252", "replace")
    out = Writer("mda_mn_food")
    for r in csv.DictReader(io.StringIO(text.lstrip())):
        if r.get("STATE") != "MN" or (r.get("EXPIRES") or "9999") < today:
            continue
        # "ALDI INC MINNESOTA DBA  ALDI FOODS #04": the trading name follows DBA
        name = re.split(r"\s+DBA\s+", r.get("NAME") or "", flags=re.I)[-1]
        out.row("mda_mn_food", r.get("LICENSE"), name,
                address(r.get("ADDRESS1"), r.get("CITY"), "MN %s" % (r.get("ZIP") or "")[:5]),
                None, None, "open", today)
    out.close(geocode=True)


if __name__ == "__main__":
    main()
