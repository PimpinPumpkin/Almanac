#!/usr/bin/env python3
"""CMS Hospital General Information: Medicare-registered hospitals, as open evidence.

cms_hospitals  every hospital in the file, open as of the dataset's
               "modified" date. The file has addresses but no positions, so
               rows are matched by address.

Public domain (US federal government work).
https://data.cms.gov/provider-data/dataset/xubh-q36u
"""
import csv
import io
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from evidence import Writer, address, get

META = "https://data.cms.gov/provider-data/api/1/metastore/schemas/dataset/items/xubh-q36u"


def main():
    meta = json.loads(get(META))
    as_of = meta["modified"][:10]
    url = meta["distribution"][0]["downloadURL"]
    out = Writer("cms")
    for r in csv.DictReader(io.StringIO(get(url).decode("utf-8-sig"))):
        out.row("cms_hospitals", r["Facility ID"], r["Facility Name"],
                address(r["Address"], r["City/Town"], "%s %s" % (r["State"], r["ZIP Code"][:5])),
                None, None, "open", as_of)
    out.close(geocode=True)


if __name__ == "__main__":
    main()
