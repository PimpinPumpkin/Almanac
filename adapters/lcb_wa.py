#!/usr/bin/env python3
"""Washington State Liquor and Cannabis Board: on-premises and off-premises
liquor licensees.

lcb_wa  an active, unexpired license for a bar, restaurant, tavern, store
        or other retailer, open as of the day the file was read.

The board posts two dated spreadsheets on its "frequently requested lists"
page; the newest of each is read. The licensee and mailing address columns
are not read. No positions; addresses go to the Census geocoder.

Washington public record. No license stated.
https://lcb.wa.gov/records/frequently-requested-lists
"""
import urllib.parse
import datetime
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from evidence import Writer, address, get

from xlsx import rows

PAGE = "https://lcb.wa.gov/records/frequently-requested-lists"
LINK = re.compile(r'href="([^"]*/(?:On|Off)(?:%20|\s|_)?Premise[^"]*\.xlsx)"', re.I)


def main():
    today = datetime.date.today()
    stamp = today.strftime("%Y%m%d")
    out = Writer("lcb_wa")
    seen = set()
    links = sorted(set(LINK.findall(get(PAGE).decode("utf-8", "replace"))))
    if len(links) < 2:
        raise SystemExit("lcb_wa: expected an on-premises and an off-premises file, found %d" % len(links))
    for link in links:
        table = rows(get(urllib.parse.urljoin(PAGE, link.replace(" ", "%20"))))
        head = [h.strip().lower() for h in next(table)]
        col = {name: head.index(name) for name in ("tradename", "loc address", "loc city", "loc zip", "expire date", "status")}
        number = next(i for i, h in enumerate(head) if h.startswith("license num"))
        for r in table:
            r = r + [""] * (len(head) - len(r))
            if not r[col["status"]].startswith("ACTIVE") or r[col["expire date"]] < stamp:
                out.drop("not active")
                continue
            if r[number] in seen:
                continue
            seen.add(r[number])
            out.row("lcb_wa", r[number], r[col["tradename"]],
                    address(r[col["loc address"]], r[col["loc city"]], "WA %s" % r[col["loc zip"]][:5]),
                    None, None, "open", today.isoformat())
    out.close(geocode=True)


if __name__ == "__main__":
    main()
