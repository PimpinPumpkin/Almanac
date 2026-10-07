"""Paging and metadata for open data portals that run on Socrata."""
import datetime
import json
import urllib.parse

from evidence import get

PAGE = 50000


def rows(host, dataset, **soql):
    """Every row of a query. Keyword names are SoQL clauses without the $: select, where, group, order."""
    offset = 0
    soql.setdefault("order", ":id")
    while True:
        q = {"$" + k: v for k, v in soql.items()}
        q.update({"$limit": PAGE, "$offset": offset})
        page = json.loads(get("https://%s/resource/%s.json?%s" % (host, dataset, urllib.parse.urlencode(q))))
        yield from page
        offset += len(page)
        if len(page) < PAGE:
            return


def updated(host, dataset):
    """The day the dataset's rows were last updated, as an ISO date."""
    meta = json.loads(get("https://%s/api/views/%s.json" % (host, dataset)))
    return datetime.datetime.fromtimestamp(meta["rowsUpdatedAt"], datetime.timezone.utc).date().isoformat()


def point(value):
    """(lat, lng) from a Socrata point or location field, or (None, None)."""
    if isinstance(value, dict):
        if value.get("coordinates"):
            return value["coordinates"][1], value["coordinates"][0]
        if value.get("latitude"):
            return value["latitude"], value["longitude"]
    return None, None
