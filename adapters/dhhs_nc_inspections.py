#!/usr/bin/env python3
"""North Carolina environmental health inspections (all counties).

dhhs_nc_inspections  a restaurant, food stand, meat market, lodging place,
                     child care center, nursing home or hospital
                     kitchen, open as of the day of its newest inspection
                     in the last two years.

County health departments inspect; the state's vendor shows the results
through one search page per county, with a CSV button. Each county is
asked for its last two years of inspections, six months at a time: 800
requests, two seconds apart. Mobile units, push carts, pools, camps, tattoo artists and
temporary events are left out. The inspector column is not read. No
positions; addresses go to the Census geocoder.

North Carolina public record. No license stated. The site has no
robots.txt. https://public.cdpehs.com/NCENVPBL/
"""
import csv
import datetime
import html
import io
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from crawl import Site
from evidence import Writer, address

PAGE = "/NCENVPBL/ESTABLISHMENT/ShowESTABLISHMENTTablePage.aspx?ESTTST_CTY=%d"
COUNTIES = range(1, 101)
HIDDEN = re.compile(r'<input type="hidden" name="([^"]+)"[^>]*value="([^"]*)"')
# the number that starts "Establishment Type"
KEEP = {"1", "2", "14", "16", "20", "21", "23", "30", "40", "41", "42", "46"}


def main():
    today = datetime.date.today()
    # two years of inspections, asked for six months at a time: the largest counties' export fails on more
    edges = [today - datetime.timedelta(days=d) for d in (730, 548, 365, 183, -1)]
    windows = [(a.strftime("%m/%d/%Y"), b.strftime("%m/%d/%Y")) for a, b in zip(edges, edges[1:])]
    site = Site("https://public.cdpehs.com")
    newest, failed = {}, []
    for county in COUNTIES:
        for since, until in windows:
            form = {k: html.unescape(v) for k, v in HIDDEN.findall(site.fetch(PAGE % county).decode("utf-8", "replace"))}
            form.update({"ctl00$PageContent$CSVButton1.x": "8", "ctl00$PageContent$CSVButton1.y": "8",
                         "ctl00$PageContent$INSPECTION_DATEFromFilter": since,
                         "ctl00$PageContent$INSPECTION_DATEToFilter": until})
            try:
                text = site.fetch(PAGE % county, form=form, timeout=600).decode("utf-8-sig", "replace")
            except Exception:
                text = ""
            if not text.startswith('"Inspection Date"'):
                failed.append("%d %s" % (county, since))
                continue
            for r in csv.DictReader(io.StringIO(text)):
                if (r.get("Establishment Type") or "").split(" ")[0] not in KEEP:
                    continue
                try:
                    when = datetime.datetime.strptime(r["Inspection Date"], "%m/%d/%Y").date().isoformat()
                except (ValueError, KeyError):
                    continue
                key = r.get("State ID#")
                if key not in newest or when > newest[key][0]:
                    newest[key] = (when, r)
    if len(failed) > 8:
        # a county left out would look like a county that closed: keep last run's file instead
        raise SystemExit("dhhs_nc_inspections: %d county exports failed (%s ...)" % (len(failed), ", ".join(failed[:6])))
    if failed:
        print("exports that failed and were left out: %s" % ", ".join(failed), file=sys.stderr)
    out = Writer("dhhs_nc_inspections")
    for key, (when, r) in newest.items():
        out.row("dhhs_nc_inspections", key, r.get("Premises Name"),
                address(r.get("Premise Address 1"), r.get("Premise City"), "NC %s" % (r.get("Premise ZIP") or "")[:5]),
                None, None, "open", when)
    out.close(geocode=True)


if __name__ == "__main__":
    main()
