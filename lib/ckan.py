"""Rows and dates from open data portals that run on CKAN."""
import csv
import io
import json

from evidence import get


def rows(host, resource):
    """Every row of a datastore resource, as dicts."""
    text = get("https://%s/datastore/dump/%s?bom=True" % (host, resource)).decode("utf-8-sig", "replace")
    return csv.DictReader(io.StringIO(text))


def modified(host, resource):
    """The day the resource was last changed, as an ISO date."""
    meta = json.loads(get("https://%s/api/3/action/resource_show?id=%s" % (host, resource)))["result"]
    return (meta.get("last_modified") or meta.get("metadata_modified") or meta["created"])[:10]
