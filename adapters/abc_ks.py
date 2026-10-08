#!/usr/bin/env python3
"""Kansas Alcoholic Beverage Control: licensee search.

abc_ks  premises holding a current on-premise, retailer, microbrewery,
        microdistillery or farm winery license, open as of the day the
        search was run.

The division offers a search form, not a file. The form is asked once per
license group for all counties and its result pages (500 rows each) are
read: about twenty requests, two seconds apart. Distributors,
manufacturers, suppliers, caterers and temporary permits are left out.
The owner and process agent columns are not read. No positions; addresses
go to the Census geocoder.

Kansas public record. No license stated. robots.txt allows the page.
https://www.kdor.ks.gov/apps/liquorlicensee/LiquorLicenseeSearch.aspx
"""
import datetime
import html
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from crawl import Site
from evidence import Writer, address

PAGE = "/apps/liquorlicensee/LiquorLicenseeSearch.aspx"
GROUPS = {"8": "On Premise", "10": "Retailer", "5": "Microbrewery", "6": "Microdistillery", "3": "Farm Winery"}
HIDDEN = re.compile(r'<input type="hidden" name="([^"]+)"[^>]*value="([^"]*)"')
ROW = re.compile(r"<tr[^>]*>(.*?)</tr>", re.S)
CELL = re.compile(r"<t[dh][^>]*>(.*?)</t[dh]>", re.S)
PAGER = re.compile(r"Page\$(\d+)")
SELECT = re.compile(r'<select name="([^"]+)"[^>]*>(.*?)</select>', re.S)
CHOSEN = re.compile(r'<option selected="selected" value="([^"]*)"')
OPTION = re.compile(r'<option value="([^"]*)"')
# "810 Bridge Street Humboldt, KS 66748": the town follows the last street word, direction or unit
PLACE = re.compile(
    r"^(.*\b(?:street|st|avenue|ave|road|rd|drive|dr|boulevard|blvd|highway|hwy|lane|ln|way|court|ct|place|pl|"
    r"terrace|ter|parkway|pkwy|circle|cir|trail|trl|plaza|square|broadway|main|north|south|east|west|n|s|e|w|"
    r"(?:suite|ste|unit|#)\s*[\w-]+|\d+)\.?)\s+([A-Za-z][A-Za-z .'-]+?),\s*KS\s+(\d{5})", re.I)


def cells(row):
    return [html.unescape(re.sub(r"<[^>]+>", "", c)).strip() for c in CELL.findall(row)]


def main():
    today = datetime.date.today()
    site = Site("https://www.kdor.ks.gov")
    out = Writer("abc_ks")
    seen = set()
    for group in GROUPS:
        form = dict(HIDDEN.findall(site.fetch(PAGE).decode("utf-8", "replace")))
        form = {k: html.unescape(v) for k, v in form.items()}
        form.update({"__EVENTTARGET": "ctl00$cphBody$btnSearch", "__EVENTARGUMENT": "",
                     "ctl00$cphBody$ddlLicGroup": group, "ctl00$cphBody$ddlLicClass": "None",
                     "ctl00$cphBody$ddlCounty": "All", "ctl00$cphBody$txtCity": "", "ctl00$cphBody$txtDba": ""})
        page_no = 1
        while True:
            page = site.fetch(PAGE, form=form).decode("utf-8", "replace")
            head = None
            for row in ROW.findall(page):
                c = cells(row)
                if "Business Name" in c:
                    head = {name: c.index(name) for name in ("Business Name", "Address", "License Type", "License Number", "License Effective To")}
                    continue
                if not head or len(c) <= max(head.values()) or "caterer" == c[head["License Type"]].lower():
                    continue
                try:
                    if datetime.datetime.strptime(c[head["License Effective To"]], "%m/%d/%Y").date() < today:
                        out.drop("expired")
                        continue
                except ValueError:
                    pass
                m = PLACE.match(c[head["Address"]])
                if not m:
                    out.drop("no usable address")
                    continue
                key = (c[head["Business Name"]].upper(), c[head["Address"]].upper())
                if key in seen:
                    continue
                seen.add(key)
                out.row("abc_ks", c[head["License Number"]], c[head["Business Name"]],
                        address(m.group(1), m.group(2), "KS %s" % m.group(3)), None, None, "open", today.isoformat())
            page_no += 1
            if str(page_no) not in PAGER.findall(page):
                break
            # the next page is asked for with the form exactly as the result page shows it
            form = {k: html.unescape(v) for k, v in HIDDEN.findall(page)}
            for name, body in SELECT.findall(page):
                chosen = CHOSEN.search(body) or OPTION.search(body)
                form[name] = html.unescape(chosen.group(1)) if chosen else ""
            form.update({"__EVENTTARGET": "ctl00$cphBody$gvLicense", "__EVENTARGUMENT": "Page$%d" % page_no,
                         "ctl00$cphBody$txtCity": "", "ctl00$cphBody$txtDba": ""})
    if len(seen) < 1500:
        raise SystemExit("abc_ks: only %d premises; the form may have changed" % len(seen))
    out.close(geocode=True)


if __name__ == "__main__":
    main()
