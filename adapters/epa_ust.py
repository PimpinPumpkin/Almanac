#!/usr/bin/env python3
"""EPA UST Finder: sites with underground fuel tanks in use, mostly gas stations.

epa_ust_open  a facility with at least one tank in use, open as of the day
              the layer was last edited. The registry gives the name on the
              sign and the street address ("Speedway #9562").

Tank removals are read but not emitted as closures. A site whose last tank
was pulled is very often still trading: tanks get replaced under a new
facility record, and many sites are hospitals, depots and stores that only
ever had a generator or fleet tank. Measured in Kentucky, 1,153 places
matched such a site; other evidence said open 353 times and closed 15.

The national layer is compiled from state registries and is refreshed
rarely (the edit date says when), so these rows age.

Public domain (US federal government work). EPA Office of Underground
Storage Tanks and Office of Research and Development, with ASTSWMO.
https://www.epa.gov/ust/ust-finder
"""
import datetime
import json
import os
import sys
import urllib.parse

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from evidence import Writer, get

BASE = ("https://services.arcgis.com/cJ9YHowT8TU7DUyn/arcgis/rest/services/"
        "UST_Finder_Feature_Layer_2/FeatureServer")
FACILITIES = 0
PAGE = 2000


def query(layer, **params):
    """Every row of a query, following the layer's paging."""
    offset = 0
    while True:
        q = dict(params, f="json", resultOffset=offset, resultRecordCount=PAGE)
        body = json.loads(get("%s/%d/query?%s" % (BASE, layer, urllib.parse.urlencode(q))))
        if "error" in body:
            raise SystemExit("UST Finder: %s" % body["error"])
        rows = [f["attributes"] for f in body.get("features", [])]
        yield from rows
        offset += len(rows)
        if not rows or not body.get("exceededTransferLimit"):
            return


def main():
    info = json.loads(get("%s/%d?f=json" % (BASE, FACILITIES)))
    edited = datetime.datetime.fromtimestamp(
        info["editingInfo"]["dataLastEditDate"] / 1000, datetime.timezone.utc).date().isoformat()
    states = [r["State"] for r in query(FACILITIES, where="1=1", outFields="State",
                                        returnDistinctValues="true", returnGeometry="false",
                                        orderByFields="State") if r.get("State")]
    out = Writer("epa_ust")
    for state in states:
        where = "State='%s' AND Open_USTs > 0" % state.replace("'", "''")
        for r in query(FACILITIES, where=where, returnGeometry="false", orderByFields="OBJECTID",
                       outFields="Facility_ID,Name,Address,Latitude,Longitude"):
            # the address ends ", ST 12345 US"
            addr = (r.get("Address") or "").rsplit(" US", 1)[0]
            out.row("epa_ust_open", r["Facility_ID"], r.get("Name"), addr,
                    r.get("Latitude"), r.get("Longitude"), "open", edited)
    out.close()


if __name__ == "__main__":
    main()
