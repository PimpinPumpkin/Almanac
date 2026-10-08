#!/usr/bin/env python3
"""Tennessee Department of Agriculture: retail food establishments.

tda_tn_food  a grocery, convenience store, market or other retail food
             store whose license is current, open as of the day the list
             was read.

The department offers a paged public list, fifteen stores a page, and no
file. The pages are read in order, two seconds apart: about 660 requests.
The site's robots.txt disallows the whole site; the owner of this project
decided on 2026-10-07 to read public registers like this one anyway.
Restaurants are licensed by the health department and are not in this
list. No positions; addresses go to the Census geocoder.

Tennessee public record. No license stated.
https://tnlcp.lcp.tracefirst.com/public_weblinks/food-safety-retail
"""
import datetime
import html
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from crawl import Site
from evidence import Writer, address

LIST = "/public_weblinks/food-safety-retail?page=%d"
TOTAL = re.compile(r"of\s+(?:<b>)?([\d,]+)(?:</b>)?\s+in total")
# one store: license, name, address, county, then a small table of program and status, then its record link
STORE = re.compile(
    r"<tr>\s*<td>\s*([^<]*?)\s*</td>\s*<td>([^<]*)</td>\s*<td>([^<]*)</td>\s*<td>[^<]*</td>\s*<td>\s*<table.*?"
    r"<tbody>(.*?)</tbody>.*?public_program_participations/(\d+)", re.S)
PLACE = re.compile(r"^(.*?),\s*([^,]+),\s*[^,]*,\s*TN,\s*(\d{5})")
PER_PAGE = 15


def main():
    today = datetime.date.today().isoformat()
    site = Site("https://tnlcp.lcp.tracefirst.com", robots=False)
    out = Writer("tda_tn_food")
    page_no, pages, found = 1, 1, 0
    while page_no <= pages:
        page = site.fetch(LIST % page_no).decode("utf-8", "replace")
        if page_no == 1:
            total = TOTAL.search(page.replace("&nbsp;", " "))
            if not total:
                raise SystemExit("tda_tn_food: the list no longer says how long it is")
            pages = -(-int(total.group(1).replace(",", "")) // PER_PAGE)
        for license_no, name, where, status, record in STORE.findall(page):
            found += 1
            if "Current" not in status:
                out.drop("license not current")
                continue
            m = PLACE.match(html.unescape(where).strip())
            if not m:
                out.drop("no usable address")
                continue
            out.row("tda_tn_food", record, html.unescape(name).strip(),
                    address(m.group(1), m.group(2), "TN %s" % m.group(3)), None, None, "open", today)
        page_no += 1
    if found < pages * PER_PAGE * 0.8:
        raise SystemExit("tda_tn_food: read %d stores from %d pages; the page layout may have changed" % (found, pages))
    out.close(geocode=True)


if __name__ == "__main__":
    main()
