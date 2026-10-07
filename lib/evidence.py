"""Shared pieces for evidence adapters.

Every adapter writes one CSV with the same eight columns:
source, source_id, name, address, lat, lng, state, date
state is open or closed. date is ISO (YYYY-MM-DD) and means "open as of" or
"closed on". lat and lng may be blank when the address ends in a ZIP code;
such rows are matched by address. Rows with neither, or with no date or
name, are dropped and counted.
"""
import csv
import os
import re
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.environ.get("ALMANAC_DATA", os.path.join(ROOT, "data"))
CACHE = os.path.join(DATA, "cache")
EVIDENCE = os.path.join(CACHE, "evidence")

_contact = os.environ.get("ALMANAC_CONTACT")
UA = "VelaAlmanac/0.1 (open US places dataset build; https://github.com/PimpinPumpkin/vela-almanac%s)" % (
    "; " + _contact if _contact else "")

COLUMNS = ["source", "source_id", "name", "address", "lat", "lng", "state", "date"]


def get(url, tries=4):
    """Fetch a URL with the project User-Agent. Returns bytes."""
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.read()
        except Exception as e:  # network errors are retried, then raised
            if getattr(e, "code", None) == 404 or attempt == tries - 1:
                raise
            print("retry %s: %s" % (url[:80], e), file=sys.stderr)
            time.sleep(5 * (attempt + 1))


def download(url, path):
    """Fetch a URL to a file once; later runs reuse the file."""
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return path
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path + ".part", "wb") as f:
        f.write(get(url))
    os.replace(path + ".part", path)
    return path


def address(*parts):
    return ", ".join(p.strip() for p in parts if p and p.strip())


class Writer:
    """Writes evidence rows, dropping and counting the unusable ones."""

    def __init__(self, name):
        os.makedirs(EVIDENCE, exist_ok=True)
        self.path = os.path.join(EVIDENCE, name + ".csv")
        self.f = open(self.path + ".part", "w", newline="")
        self.w = csv.writer(self.f)
        self.w.writerow(COLUMNS)
        self.kept = {}
        self.dropped = {}

    def drop(self, why):
        self.dropped[why] = self.dropped.get(why, 0) + 1

    def row(self, source, source_id, name, addr, lat, lng, state, date):
        if lat in (None, "") and lng in (None, ""):
            if not re.search(r"\d{5}(-\d{4})?\s*$", addr or ""):
                return self.drop("no position and no ZIP")
            lat = lng = ""
        else:
            try:
                lat, lng = "%.6f" % float(lat), "%.6f" % float(lng)
            except (TypeError, ValueError):
                return self.drop("no position")
            if not (17 < float(lat) < 72 and -180 < float(lng) < -64):
                return self.drop("no position")
        if not date or len(date) != 10:
            return self.drop("no date")
        if not name:
            return self.drop("no name")
        self.w.writerow([source, source_id, name.strip(), addr, lat, lng, state, date])
        key = (source, state)
        self.kept[key] = self.kept.get(key, 0) + 1

    def close(self):
        self.f.close()
        os.replace(self.path + ".part", self.path)
        for (source, state), n in sorted(self.kept.items()):
            print("%s %s: %d" % (source, state, n))
        for why, n in sorted(self.dropped.items()):
            print("dropped, %s: %d" % (why, n))
