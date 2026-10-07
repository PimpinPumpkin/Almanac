#!/usr/bin/env python3
"""District of Columbia ABCA liquor licenses: active premises and cancellations.

abca_dc_active     licenses with STATUS ACTIVE, open as of the day the layer
                   was last loaded.
abca_dc_cancelled  the cancellation layer, for places that live on their
                   liquor license: restaurants, taverns, nightclubs, clubs.
                   It carries no cancellation date, so the date is the day
                   the layer was last loaded: cancelled on or before then.

A cancellation is skipped when the same trade name holds an active license
at the same address (a change of owner or license class), and for grocery
and liquor stores and hotels, which the measurements showed often carry on
or simply swap licenses. Delivery-only and other licenses with no premises
of their own are left out.

DC open data. https://opendata.dc.gov (Alcohol License Business Locations,
Alcohol License Cancellations)
"""
import datetime
import json
import os
import sys
import urllib.parse

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from evidence import Writer, address, get

BASE = ("https://maps2.dcgis.dc.gov/dcgis/rest/services/DCGIS_DATA/"
        "Business_Licensing_and_Grants_WebMercator/FeatureServer")
ACTIVE, CANCELLED = 5, 42
NO_PREMISES = {"Third-Party Delivery", "Caterer", "Solicitor", "Wholesaler", "Storage Facility",
               "Common Carrier", "Internet"}
CLOSES_WITH_LICENSE = {"Restaurant", "Tavern", "Nightclub", "Club", "Multipurpose"}


def key(a):
    return ((a.get("ADDRESS") or "").strip().upper(), (a.get("TRADE_NAME") or "").strip().upper())


def rows(layer):
    offset = 0
    while True:
        q = {"where": "1=1", "outFields": "*", "returnGeometry": "false", "orderByFields": "OBJECTID",
             "resultOffset": offset, "resultRecordCount": 2000, "f": "json"}
        feats = json.loads(get("%s/%d/query?%s" % (BASE, layer, urllib.parse.urlencode(q)))).get("features", [])
        for f in feats:
            yield f["attributes"]
        offset += len(feats)
        if len(feats) < 2000:
            return


def day(ms):
    return datetime.datetime.fromtimestamp(ms / 1000, datetime.timezone.utc).date().isoformat()


def emit(out, source, data, state, skip=()):
    loaded = day(max(a["EDITED"] for a in data if a.get("EDITED")))
    for a in data:
        kind = (a.get("TYPE") or "").strip()
        if state == "open" and a.get("STATUS") != "ACTIVE":
            out.drop("not active")
            continue
        if kind in NO_PREMISES:
            out.drop("no premises")
            continue
        if state == "closed" and kind not in CLOSES_WITH_LICENSE:
            out.drop("cancelled, but not a kind of place that closes with its license")
            continue
        if state == "closed" and key(a) in skip:
            out.drop("cancelled, but the same name has an active license there")
            continue
        out.row(source, a["LICENSE"], a.get("TRADE_NAME") or a.get("APPLICANT"),
                address(a.get("ADDRESS"), "Washington", "DC %s" % (a.get("ZIPCODE") or "")),
                a.get("LATITUDE"), a.get("LONGITUDE"), state, loaded)


def main():
    out = Writer("abca_dc")
    active = list(rows(ACTIVE))
    emit(out, "abca_dc_active", active, "open")
    live = {key(a) for a in active if a.get("STATUS") == "ACTIVE"}
    emit(out, "abca_dc_cancelled", list(rows(CANCELLED)), "closed", skip=live)
    out.close()


if __name__ == "__main__":
    main()
