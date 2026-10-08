"""Positions for US addresses from the Census Bureau's batch geocoder.

Free, keyless, public domain. https://geocoding.geo.census.gov/geocoder/
Answers are kept in data/cache/geocode/census.csv so an address is only
ever asked about once; a miss is remembered too.
"""
import csv
import io
import os
import re
import sys
import time
import urllib.request
import uuid
from concurrent.futures import ThreadPoolExecutor

URL = "https://geocoding.geo.census.gov/geocoder/locations/addressbatch"
BATCH = 5000
WORKERS = 4
ADDRESS = re.compile(r"^(.*), ([^,]+), ([A-Z]{2}) (\d{5})$")


def _post(rows, ua):
    """One batch: rows are (id, street, city, state, zip). Returns {id: (lat, lng) or None}."""
    body = io.StringIO()
    csv.writer(body).writerows(rows)
    boundary = uuid.uuid4().hex
    parts = [
        '--%s\r\nContent-Disposition: form-data; name="benchmark"\r\n\r\nPublic_AR_Current\r\n' % boundary,
        '--%s\r\nContent-Disposition: form-data; name="addressFile"; filename="a.csv"\r\n'
        'Content-Type: text/csv\r\n\r\n%s\r\n' % (boundary, body.getvalue()),
        "--%s--\r\n" % boundary,
    ]
    data = "".join(parts).encode("utf-8")
    for attempt in range(4):
        try:
            req = urllib.request.Request(URL, data=data, headers={
                "User-Agent": ua, "Content-Type": "multipart/form-data; boundary=" + boundary})
            with urllib.request.urlopen(req, timeout=900) as r:
                text = r.read().decode("utf-8", "replace")
            break
        except Exception as e:
            if attempt == 3:
                print("geocoder gave up on a batch: %s" % e, file=sys.stderr)
                return {}
            time.sleep(20 * (attempt + 1))
    out = {}
    for rec in csv.reader(io.StringIO(text)):
        if len(rec) >= 6 and rec[2] == "Match" and "," in rec[5]:
            lng, lat = rec[5].split(",")
            out[rec[0]] = (lat, lng)
        elif rec:
            out[rec[0]] = None
    return out


def locate(addresses, cache_dir, ua):
    """{address: (lat, lng)} for the addresses the geocoder can place.

    An address is one string, "street, city, ST 12345". Others are skipped.
    """
    os.makedirs(cache_dir, exist_ok=True)
    path = os.path.join(cache_dir, "census.csv")
    known = {}
    if os.path.exists(path):
        bad = 0
        with open(path, newline="") as f:
            for row in csv.reader(f):
                # a line that is not address, lat, lng (a damaged cache) is dropped, not fatal
                if len(row) != 3:
                    bad += 1
                    continue
                known[row[0]] = (row[1], row[2]) if row[1] else None
        if bad:
            print("geocode cache: dropped %d damaged lines" % bad, file=sys.stderr)
            with open(path + ".part", "w", newline="") as f:
                csv.writer(f).writerows([a, pos[0] if pos else "", pos[1] if pos else ""] for a, pos in known.items())
            os.replace(path + ".part", path)
    todo = sorted({a for a in addresses if a not in known and ADDRESS.match(a)})
    batches = [todo[i:i + BATCH] for i in range(0, len(todo), BATCH)]

    def run(batch):
        rows = [(str(i),) + ADDRESS.match(a).groups() for i, a in enumerate(batch)]
        got = _post(rows, ua)
        return [(a, got[str(i)]) for i, a in enumerate(batch) if str(i) in got]

    with ThreadPoolExecutor(WORKERS) as pool, open(path, "a", newline="") as f:
        w = csv.writer(f)
        for n, result in enumerate(pool.map(run, batches), 1):
            for a, pos in result:
                known[a] = pos
                w.writerow([a, pos[0] if pos else "", pos[1] if pos else ""])
            f.flush()
            print("geocoded batch %d of %d" % (n, len(batches)), file=sys.stderr)
    return {a: known[a] for a in addresses if known.get(a)}
