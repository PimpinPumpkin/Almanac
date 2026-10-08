#!/usr/bin/env python3
"""State food inspection lookups that run on the same "Food Safety" system.

foodsafety_<st>  a food establishment, open as of the day of its most
                 recent inspection.

One source per state: Alaska, Arkansas, Iowa, Kansas, North Dakota,
Pennsylvania, South Dakota, Vermont. (Wyoming runs the same system but its
search answers with a server error; it is on the follow-up list.) Each state offers a search
page and no file. The page is asked county by county and its result pages
read, fifteen establishments a page, two seconds apart. A search shows at
most 500 establishments, so a county that hits the limit is asked again
by inspection date, the last two years split in halves until each piece
fits. That is thousands
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
import hashlib
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
}
M = "ctl00$MainContent$"
HIDDEN = re.compile(r'<input type="hidden" name="([^"]+)"[^>]*value="([^"]*)"')
SELECT = r'<select name="%s".*?</select>'
OPTION = re.compile(r'<option(?: selected="selected")? value="([^"]*)"[^>]*>([^<]*)')
FOUND = re.compile(r"(\d+) record\(s\) found")
# one establishment: name, address line and most recent inspection date
ROW = re.compile(
    r'<tr class="Grid(?:Alt)?Item"[^>]*>\s*<td width="20%">\s*(.*?)<BR><div[^>]*>(.*?)</div>.*?</td>'
    r'<td align="center" width="10%">(\d\d/\d\d/\d{4})</td>', re.S | re.I)
# a search never returns more than this many establishments
CAP = 500
PER_PAGE = 15


def options(page, name):
    m = re.search(SELECT % re.escape(name), page, re.S)
    return [(v, html.unescape(t).strip()) for v, t in OPTION.findall(m.group(0))] if m else []


FIELD = re.compile(r'<(input|select)([^>]*name="(ctl00\$MainContent\$[^"]+)"[^>]*)>(.*?</select>)?', re.S)
CHOSEN = re.compile(r'<option selected="selected" value="([^"]*)"')
FIRST = re.compile(r'<option value="([^"]*)"')


def form_for(page, state_id, county_id):
    """The search form as the page shows it, with the state and county filled in. The states run
    different versions of the system with different fields, so the form is read off the page."""
    form = {k: html.unescape(v) for k, v in HIDDEN.findall(page)}
    for tag, attrs, name, body in FIELD.findall(page):
        if name in form:
            continue
        if tag == "select":
            chosen = CHOSEN.search(body) or FIRST.search(body)
            form[name] = html.unescape(chosen.group(1)) if chosen else ""
        elif 'type="checkbox"' in attrs:
            if 'checked="checked"' in attrs:
                form[name] = "on"
        elif 'type="text"' in attrs:
            form[name] = ""
    form.pop(M + "chkDisplayMap", None)
    form.pop(M + "chkRadius", None)
    form.update({"__EVENTTARGET": "", "__EVENTARGUMENT": "", M + "hfUseRadius": "false",
                 M + "wucStateCountiesFS$ddlState": state_id, M + "wucStateCountiesFS$ddlCounty": county_id})
    if M + "wucStateCountiesFS$ddlCountyGroup" in form:
        form[M + "wucStateCountiesFS$ddlCountyGroup"] = ""
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
    today = datetime.date.today()
    newest = {}
    expected = read = 0

    def search(county_id, begin, end):
        """Read one county's establishments inspected between two days (or ever, with no days given).
        A search that hits the cap is split in two and asked again."""
        nonlocal expected, read
        form = form_for(site.fetch(path).decode("utf-8", "replace"), state_id, county_id)
        form[M + "btnSearch"] = "Search"
        if begin:
            form[M + "dteInspectionBeginDate$txtDate"] = begin.strftime("%m/%d/%Y")
            form[M + "dteInspectionEndDate$txtDate"] = end.strftime("%m/%d/%Y")
        page = site.fetch(path, form=form).decode("utf-8", "replace")
        found = FOUND.search(page)
        found = int(found.group(1)) if found else 0
        if found >= CAP:
            if not begin:
                begin, end = today - datetime.timedelta(days=730), today
            if (end - begin).days >= 1:
                middle = begin + (end - begin) // 2
                search(county_id, begin, middle)
                search(county_id, middle + datetime.timedelta(days=1), end)
                return
        expected += found
        page_no = 1
        while True:
            rows = ROW.findall(page)
            for name, where, when in rows:
                read += 1
                name = html.unescape(re.sub(r"<[^>]+>", " ", name)).strip()
                where = " ".join(html.unescape(re.sub(r"<[^>]+>", " ", where)).split())
                when = datetime.datetime.strptime(when, "%m/%d/%Y").date().isoformat()
                key = hashlib.sha1(("%s|%s" % (name, where)).upper().encode()).hexdigest()[:16]
                if key not in newest or when > newest[key][0]:
                    newest[key] = (when, name, where)
            page_no += 1
            if not rows or "Page$%d" % page_no not in page:
                break
            form = form_for(page, state_id, county_id)
            if begin:
                form[M + "dteInspectionBeginDate$txtDate"] = begin.strftime("%m/%d/%Y")
                form[M + "dteInspectionEndDate$txtDate"] = end.strftime("%m/%d/%Y")
            form.update({"__EVENTTARGET": M + "gvInspections", "__EVENTARGUMENT": "Page$%d" % page_no})
            page = site.fetch(path, form=form).decode("utf-8", "replace")

    for county_id, county in counties:
        search(county_id, None, None)
    # some establishments have never been inspected and show no date; they are not counted as read
    if not read or read < expected * 0.6:
        # the layout changed or the site cut the crawl short: keep the last file
        raise SystemExit("%s: read %d of the %d establishments the site reported" % (source, read, expected))
    out = Writer(source)
    for key, (when, name, where) in newest.items():
        place = street_city(where)
        if not place or place[2] != st:
            out.drop("no usable address")
            continue
        out.row(source, key, name, address(place[0], place[1], "%s %s" % (st, place[3])), None, None, "open", when)
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
