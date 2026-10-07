"""Paging and metadata for ArcGIS feature layers."""
import datetime
import json
import urllib.parse

from evidence import get


def info(layer):
    return json.loads(get(layer + "?f=json"))


def edited(layer):
    """The day the layer's data was last edited, as an ISO date, or None."""
    ms = (info(layer).get("editingInfo") or {}).get("dataLastEditDate")
    return day(ms) if ms else None


def day(ms):
    """Epoch milliseconds -> ISO date."""
    return datetime.datetime.fromtimestamp(ms / 1000, datetime.timezone.utc).date().isoformat()


def features(layer, where="1=1", fields="*", geometry=True):
    """Every feature of a query as (attributes, (lat, lng)). Positions are WGS 84."""
    size = info(layer).get("maxRecordCount") or 1000
    offset = 0
    while True:
        q = {"where": where, "outFields": fields, "outSR": 4326, "f": "json",
             "returnGeometry": "true" if geometry else "false",
             "resultOffset": offset, "resultRecordCount": size}
        body = json.loads(get(layer + "/query?" + urllib.parse.urlencode(q)))
        if "error" in body:
            raise SystemExit("%s: %s" % (layer, body["error"]))
        feats = body.get("features", [])
        for f in feats:
            g = f.get("geometry") or {}
            yield f["attributes"], (g.get("y"), g.get("x"))
        offset += len(feats)
        if not feats or not body.get("exceededTransferLimit"):
            return
