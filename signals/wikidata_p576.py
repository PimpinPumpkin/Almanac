#!/usr/bin/env python3
"""Wikidata P576 (dissolved, abolished or demolished date) for a list of items.

Reads QIDs on stdin, one per line. Writes CSV qid,date on stdout for the
items that have the property. Uses the public SPARQL endpoint, no key.
Wikidata is CC0.
"""
import json
import os
import re
import sys
import urllib.parse

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import urllib.request

from evidence import UA

ENDPOINT = "https://query.wikidata.org/sparql"
BATCH = 300


def ask(qids):
    query = "SELECT ?i ?d WHERE { VALUES ?i { %s } ?i wdt:P576 ?d }" % " ".join("wd:" + q for q in qids)
    req = urllib.request.Request(
        ENDPOINT, data=urllib.parse.urlencode({"query": query}).encode(),
        headers={"User-Agent": UA, "Accept": "application/sparql-results+json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)["results"]["bindings"]


def main():
    qids = sorted({q.strip() for q in sys.stdin if q.strip().startswith("Q") and q.strip()[1:].isdigit()})
    print("qid,date")
    for i in range(0, len(qids), BATCH):
        for b in ask(qids[i:i + BATCH]):
            date = b["d"]["value"][:10]
            # "unknown value" comes back as a URL, and BCE dates start with a minus
            if re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
                print("%s,%s" % (b["i"]["value"].rsplit("/", 1)[1], date))


if __name__ == "__main__":
    main()
