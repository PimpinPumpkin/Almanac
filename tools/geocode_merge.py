#!/usr/bin/env python3
"""Merge geocoder answer files.

  geocode_merge.py <out> <in> [<in> ...]           every answer from the inputs, once each
  geocode_merge.py --new <out> <before> <after>    the answers in <after> that <before> lacks

The answers file is CSV with quoted addresses, so it is read and written as
CSV: sorting or joining it as plain lines damages it.
"""
import csv
import os
import sys


def read(path):
    rows = {}
    if os.path.exists(path):
        with open(path, newline="") as f:
            for row in csv.reader(f):
                if len(row) == 3:
                    rows[row[0]] = row
    return rows


def main():
    args = sys.argv[1:]
    if args[0] == "--new":
        out, before, after = args[1:4]
        seen = read(before)
        rows = [r for a, r in read(after).items() if a not in seen]
    else:
        out, merged = args[0], {}
        for path in args[1:]:
            merged.update(read(path))
        rows = list(merged.values())
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out + ".part", "w", newline="") as f:
        csv.writer(f).writerows(rows)
    os.replace(out + ".part", out)
    print("%d answers written to %s" % (len(rows), out))


if __name__ == "__main__":
    main()
