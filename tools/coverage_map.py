#!/usr/bin/env python3
"""Draw the by-state coverage map and table from the published state files.

Reads data/out/places-<state>.parquet for every state in regions.tsv and
writes docs/coverage-light.svg, docs/coverage-dark.svg, docs/coverage.json
(read by the interactive page docs/index.html) and COVERAGE.md.
The number in each cell is the share of places in that category that have a
dated open or closed status. Run from the repo root: tools/coverage_map.py
"""
import csv
import datetime
import io
import json
import os
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.environ.get("ALMANAC_DATA", os.path.join(ROOT, "data"))

PANELS = ["fast food", "banks and credit unions", "gas stations", "grocery and convenience",
          "pharmacies", "restaurants and cafes", "bars", "hotels",
          "schools", "hospitals", "museums", "everything else"]

# The usual tile grid: one square per state, roughly where the state is.
GRID = """
AK . . . . . . . . . . ME
. . . . . . . . . . VT NH
WA ID MT ND MN IL WI MI NY RI MA
OR NV WY SD IA IN OH PA NJ CT .
CA UT CO NE MO KY WV VA MD DE .
. AZ NM KS AR TN NC SC DC . .
. . . OK LA MS AL GA . . .
HI . . TX . . . . FL . .
"""
BINS = [5, 15, 30, 45, 60]          # upper edges, percent
LABELS = ["under 5%", "5 to 15%", "15 to 30%", "30 to 45%", "45 to 60%", "60% and up"]
THEMES = {
    "light": {"surface": "#fcfcfb", "ink": "#1f1f1e", "muted": "#6b6b68", "empty": "#e4e3df",
              "ramp": ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#1c5cab", "#0d366b"],
              "on": ["#1f1f1e", "#1f1f1e", "#1f1f1e", "#ffffff", "#ffffff", "#ffffff"]},
    "dark": {"surface": "#1a1a19", "ink": "#ecebe7", "muted": "#a3a29e", "empty": "#3a3a37",
             "ramp": ["#0d366b", "#184f95", "#256abf", "#3987e5", "#86b6ef", "#cde2fb"],
             "on": ["#ecebe7", "#ecebe7", "#ffffff", "#ffffff", "#1a1a19", "#1a1a19"]},
}
CELL, GAP = 26, 2


def regions():
    out = {}
    with open(os.path.join(ROOT, "regions.tsv")) as f:
        for line in f:
            c = line.rstrip("\n").split("\t")
            if not line.startswith("#") and len(c) >= 7 and c[6]:
                out[c[0]] = c[6]
    return out


def measure():
    """{(state, bucket): (listed, pct)} plus {state: (listed, pct)} over all categories."""
    files = [(r, s) for r, s in regions().items()
             if os.path.exists(os.path.join(DATA, "out", "places-%s.parquet" % r))]
    union = " union all ".join(
        "select '%s' as st, category, status from '%s'" % (s, os.path.join(DATA, "out", "places-%s.parquet" % r))
        for r, s in files)
    sql = (".read %s\n"
           "select st, bucket(category) as b, count(*) as n, "
           "round(100.0 * count(*) filter (where status <> 'unknown') / count(*), 1) as pct "
           "from (%s) group by all;" % (os.path.join(ROOT, "sql", "buckets.sql"), union))
    res = subprocess.run(["duckdb", "-csv"], input=sql, capture_output=True, text=True, check=True).stdout
    cells, tot = {}, {}
    for r in csv.DictReader(io.StringIO(res)):
        cells[(r["st"], r["b"])] = (int(r["n"]), float(r["pct"]))
        n, hit = tot.get(r["st"], (0, 0.0))
        tot[r["st"]] = (n + int(r["n"]), hit + int(r["n"]) * float(r["pct"]) / 100)
    return cells, {s: (n, round(100 * hit / n, 1)) for s, (n, hit) in tot.items()}


def grid():
    """GRID as rows of equal length."""
    rows = [r.split() for r in GRID.strip().splitlines()]
    wide = max(len(r) for r in rows)
    return [r + ["."] * (wide - len(r)) for r in rows]


def step(pct):
    return next((i for i, edge in enumerate(BINS) if pct < edge), len(BINS))


def svg(cells, theme):
    t = THEMES[theme]
    rows = grid()
    pw, ph = len(rows[0]) * (CELL + GAP), len(rows) * (CELL + GAP)
    cols, pad, head = 3, 28, 96
    width = cols * pw + (cols + 1) * pad
    nrows = -(-len(PANELS) // cols)
    height = head + nrows * (ph + 34 + pad)
    o = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" '
         'font-family="system-ui, -apple-system, Segoe UI, Helvetica, Arial, sans-serif" role="img" '
         'aria-label="Share of places with a dated open or closed status, by state and category">'
         % (width, height, width, height),
         '<rect width="100%%" height="100%%" fill="%s"/>' % t["surface"],
         '<text x="%d" y="34" font-size="20" font-weight="600" fill="%s">Places with a dated open or closed status</text>'
         % (pad, t["ink"]),
         '<text x="%d" y="56" font-size="13" fill="%s">Share of listed places in each category, by state. '
         'Numbers are in COVERAGE.md.</text>' % (pad, t["muted"])]
    x = pad
    for i, lab in enumerate(LABELS):
        o.append('<rect x="%d" y="70" width="14" height="14" rx="3" fill="%s"/>' % (x, t["ramp"][i]))
        o.append('<text x="%d" y="82" font-size="12" fill="%s">%s</text>' % (x + 20, t["muted"], lab))
        x += 34 + 7 * len(lab)
    o.append('<rect x="%d" y="70" width="14" height="14" rx="3" fill="none" stroke="%s" stroke-width="1.5"/>'
             % (x, t["empty"]))
    o.append('<text x="%d" y="82" font-size="12" fill="%s">not built yet</text>' % (x + 20, t["muted"]))
    for k, panel in enumerate(PANELS):
        ox = pad + (k % cols) * (pw + pad)
        oy = head + (k // cols) * (ph + 34 + pad)
        o.append('<text x="%d" y="%d" font-size="14" font-weight="600" fill="%s">%s</text>'
                 % (ox, oy + 16, t["ink"], panel.capitalize()))
        for r, row in enumerate(rows):
            for c, st in enumerate(row):
                if st == ".":
                    continue
                cx, cy = ox + c * (CELL + GAP), oy + 28 + r * (CELL + GAP)
                hit = cells.get((st, panel))
                if hit is None:
                    o.append('<rect x="%d" y="%d" width="%d" height="%d" rx="4" fill="none" stroke="%s" '
                             'stroke-width="1.5"/>' % (cx, cy, CELL, CELL, t["empty"]))
                    ink = t["muted"]
                else:
                    s = step(hit[1])
                    o.append('<rect x="%d" y="%d" width="%d" height="%d" rx="4" fill="%s"><title>%s, %s: %s%% of %d</title></rect>'
                             % (cx, cy, CELL, CELL, t["ramp"][s], st, panel, hit[1], hit[0]))
                    ink = t["on"][s]
                o.append('<text x="%d" y="%d" font-size="10" text-anchor="middle" fill="%s">%s</text>'
                         % (cx + CELL // 2, cy + CELL // 2 + 4, ink, st))
    o.append("</svg>")
    return "\n".join(o) + "\n"


def table(cells, totals):
    states = sorted(totals)
    short = ["Fast food", "Banks", "Gas", "Grocery", "Pharmacy", "Restaurants", "Bars", "Hotels",
             "Schools", "Hospitals", "Museums", "Other"]
    o = ["# Coverage by state", "",
         "Share of listed places that have a dated open or closed status, by state and",
         "category. Made by `tools/coverage_map.py` from the published state files.",
         "Categories are rough buckets (`sql/buckets.sql`).", "",
         "| State | Places | All | " + " | ".join(short) + " |",
         "| --- | ---: | ---: | " + " | ".join("---:" for _ in short) + " |"]
    for s in states:
        row = ["%s%%" % cells[(s, p)][1] if (s, p) in cells else "" for p in PANELS]
        o.append("| %s | %s | %s%% | %s |" % (s, format(totals[s][0], ","), totals[s][1], " | ".join(row)))
    n = sum(v[0] for v in totals.values())
    hit = sum(v[0] * v[1] / 100 for v in totals.values())
    o += ["", "%s places in %d states; %.1f%% have a dated status." % (format(n, ","), len(states), 100 * hit / n), ""]
    return "\n".join(o)


def main():
    cells, totals = measure()
    os.makedirs(os.path.join(ROOT, "docs"), exist_ok=True)
    for theme in THEMES:
        with open(os.path.join(ROOT, "docs", "coverage-%s.svg" % theme), "w") as f:
            f.write(svg(cells, theme))
    with open(os.path.join(ROOT, "COVERAGE.md"), "w") as f:
        f.write(table(cells, totals))
    with open(os.path.join(ROOT, "docs", "coverage.json"), "w") as f:
        json.dump({
            "made": datetime.date.today().isoformat(),
            "panels": PANELS,
            "grid": grid(),
            "bins": BINS,
            "labels": LABELS,
            "states": {s: {"places": totals[s][0], "pct": totals[s][1],
                           "cats": {p: list(cells[(s, p)]) for p in PANELS if (s, p) in cells}}
                       for s in sorted(totals)},
        }, f, separators=(",", ":"))
    print("%d states" % len(totals))


if __name__ == "__main__":
    main()
