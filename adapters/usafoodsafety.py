#!/usr/bin/env python3
"""State food inspection lookups that run on the same "Food Safety" system.

foodsafety_<st>  a food establishment, open as of the day of its most
                 recent inspection.

One source per state: Alaska, Arkansas, Iowa, Kansas, North Dakota,
Pennsylvania, South Dakota, Vermont, Wyoming. Each state offers a search
page and no file. The page is asked county by county and its result pages
read, fifteen establishments a page, two seconds apart. That is thousands
of requests a state, so this reader runs on its own schedule, one state a
job (.github/workflows/crawl.yml), not in the monthly build.

Set FOODSAFETY_STATES to a space separated list (for example "VT SD") to
read only those; with nothing set, every state is read. Each state writes
its own file, so one state failing does not lose the others. Phone numbers
are not read. No positions; addresses go to the Census geocoder.

State public records. No license stated. None of the sites has a
robots.txt.
"""
import datetime
import html
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from crawl import Site
from evidence import Writer, address, street_city

PAGE = "Inspection/PublicInspectionSearch.aspx"
STATES = {
    "AK": ("https://adec.safefoodinspection.com", "", "Alaska"),
    "AR": ("https://foodserviceprod.adh.arkansas.gov", "Web/", "Arkansas"),
    "IA": ("https://iowa.safefoodinspection.com", "", "Iowa"),
    "KS": ("https://foodsafety.kda.ks.gov", "FoodSafety/Web/", "Kansas"),
    "ND": ("https://fims.doh.nd.gov", "Web/", "North Dakota"),
    "PA": ("https://www.pafoodsafety.pa.gov", "Web/", "Pennsylvania"),
    "SD": ("https://sddoh.safefoodinspection.com", "", "South Dakota"),
    "VT": ("https://vtdoh.safefoodinspection.com", "", "Vermont"),
    "WY": ("https://wda.safefoodinspection.com", "", "Wyoming"),
}
M = "ctl00$MainContent$"
HIDDEN = re.compile(r'<input type="hidden" name="([^"]+)"[^>]*value="([^"]*)"')
SELECT = r'<select name="%s".*?</select>'
OPTION = re.compile(r'<option(?: selected="selected")? value="([^"]*)"[^>]*>([^<]*)')
FOUND = re.compile(r"(\d+) record\(s\) found")
# one establishment: name, address line, most recent inspection date, and its key further down the row
ROW = re.compile(
    r'<tr class="Grid(?:Alt)?Item"[^>]*>\s*<td width="20%">\s*(.*?)<BR><div[^>]*>(.*?)</div>.*?</td>'
    r'<td align="center" width="10%">(\d\d/\d\d/\d{4})</td>.*?Key="(\d+)"', re.S | re.I)
PER_PAGE = 15


def options(page, name):
    m = re.search(SELECT % re.escape(name), page, re.S)
    return [(v, html.unescape(t).strip()) for v, t in OPTION.findall(m.group(0))] if m else []


def form_for(page, state_id, county_id):
    form = {k: html.unescape(v) for k, v in HIDDEN.findall(page)}
    form.update({"__EVENTTARGET": "", "__EVENTARGUMENT": "", M + "hfUseRadius": "false",
                 M + "txtEstablistmentName": "", M + "txtStreetAddress": "", M + "txtCity": "", M + "txtZip": "",
                 M + "wucStateCountiesFS$ddlState": state_id, M + "wucStateCountiesFS$ddlCountyGroup": "",
                 M + "wucStateCountiesFS$ddlCounty": county_id,
                 M + "dteInspectionBeginDate$txtDate": "", M + "dteInspectionEndDate$txtDate": ""})
    return form


def read_state(st):
    base, prefix, state_name = STATES[st]
    site = Site(base)
    path = prefix + PAGE
    source = "foodsafety_" + st.lower()
    start = site.fetch(path).decode("utf-8", "replace")
    state_id = next((v for v, t in options(start, M + "wucStateCountiesFS$ddlState") if t == state_name), None)
    counties = [(v, t) for v, t in options(start, M + "wucStateCountiesFS$ddlCounty") if v]
    if not state_id or not counties:
        raise SystemExit("%s: the search form no longer lists %s and its counties" % (source, state_name))
    out = Writer(source)
    expected = read = 0
    for county_id, county in counties:
        # a fresh form for each county, then that county's pages in order
        form = form_for(site.fetch(path).decode("utf-8", "replace"), state_id, county_id)
        form[M + "btnSearch"] = "Search"
        page_no = 1
        while True:
            page = site.fetch(path, form=form).decode("utf-8", "replace")
            if page_no == 1:
                found = FOUND.search(page)
                expected += int(found.group(1)) if found else 0
            rows = ROW.findall(page)
            for name, where, when, key in rows:
                read += 1
                place = street_city(html.unescape(re.sub(r"<[^>]+>", " ", where)))
                if not place or place[2] != st:
                    out.drop("no usable address")
                    continue
                out.row(source, key, html.unescape(re.sub(r"<[^>]+>", " ", name)).strip(),
                        address(place[0], place[1], "%s %s" % (st, place[3])), None, None, "open",
                        datetime.datetime.strptime(when, "%m/%d/%Y").date().isoformat())
            page_no += 1
            if not rows or "Page$%d" % page_no not in page:
                break
            form = form_for(page, state_id, county_id)
            form.update({"__EVENTTARGET": M + "gvInspections", "__EVENTARGUMENT": "Page$%d" % page_no})
    if expected and read < expected * 0.8:
        # the layout changed or the site cut the crawl short: keep the last file
        raise SystemExit("%s: read %d of the %d establishments the site reported" % (source, read, expected))
    out.close(geocode=True)


def main():
    wanted = os.environ.get("FOODSAFETY_STATES", "").split() or sorted(STATES)
    failed = []
    for st in wanted:
        try:
            read_state(st)
        except (Exception, SystemExit) as e:
            failed.append("%s: %s" % (st, e))
    if failed:
        raise SystemExit("usafoodsafety, states that failed: " + "; ".join(failed))


if __name__ == "__main__":
    main()
