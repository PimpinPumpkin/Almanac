#!/usr/bin/env python3
"""FDIC BankFind: bank branches open today, and branch closings with dates.

fdic_locations  every office in the current locations list, open as of the
                list's run date. Offices with no premises (cyber offices) are
                left out.
fdic_history    structure change code 721, "Branch Closing", closed on the
                effective date.

Public domain (US federal government work). https://api.fdic.gov/banks/docs/
"""
import json
import os
import sys
import urllib.parse

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from evidence import Writer, address, get

API = "https://api.fdic.gov/banks"
PAGE = 10000
CYBER_OFFICE = 13

# The register uses the legal name. Where the sign on the building says
# something else, emit the name people know. Only cases where the two share
# no leading words need a line here.
TRADE_NAMES = {
    "JPMorgan Chase Bank, National Association": "Chase Bank",
    "Manufacturers and Traders Trust Company": "M&T Bank",
    "The Huntington National Bank": "Huntington Bank",
    "Branch Banking and Trust Company": "BB&T",
}


def pages(endpoint, filters, fields, sort):
    offset = 0
    while True:
        q = {"limit": PAGE, "offset": offset, "fields": ",".join(fields),
             "sort_by": sort, "sort_order": "ASC", "format": "json"}
        if filters:
            q["filters"] = filters
        body = json.loads(get("%s/%s?%s" % (API, endpoint, urllib.parse.urlencode(q))))
        rows = [r["data"] for r in body["data"]]
        yield from rows
        offset += len(rows)
        if not rows or offset >= body["meta"]["total"]:
            return


def mdy(s):
    """10/02/2026 -> 2026-10-02"""
    m, d, y = s.split("/")
    return "%s-%s-%s" % (y, m, d)


def main():
    out = Writer("fdic")

    fields = ["UNINUM", "NAME", "ADDRESS", "CITY", "STALP", "ZIP", "LATITUDE", "LONGITUDE", "SERVTYPE", "RUNDATE"]
    for r in pages("locations", None, fields, "UNINUM"):
        if r.get("SERVTYPE") == CYBER_OFFICE:
            out.drop("cyber office")
            continue
        out.row("fdic_locations", r["UNINUM"], TRADE_NAMES.get(r.get("NAME"), r.get("NAME")),
                address(r.get("ADDRESS"), r.get("CITY"), "%s %s" % (r.get("STALP") or "", r.get("ZIP") or "")),
                r.get("LATITUDE"), r.get("LONGITUDE"), "open", mdy(r["RUNDATE"]))

    fields = ["UNINUM", "INSTNAME", "OFF_PADDR", "OFF_PCITY", "OFF_PSTALP", "OFF_PZIP5",
              "OFF_LATITUDE", "OFF_LONGITUDE", "OFF_SERVTYPE", "EFFDATE"]
    for r in pages("history", "CHANGECODE:721", fields, "TRANSNUM"):
        if r.get("OFF_SERVTYPE") == CYBER_OFFICE:
            out.drop("cyber office")
            continue
        if not r.get("OFF_LATITUDE") or not r.get("OFF_LONGITUDE"):
            out.drop("no position")
            continue
        out.row("fdic_history", r["UNINUM"], TRADE_NAMES.get(r.get("INSTNAME"), r.get("INSTNAME")),
                address(r.get("OFF_PADDR"), r.get("OFF_PCITY"),
                        "%s %s" % (r.get("OFF_PSTALP") or "", r.get("OFF_PZIP5") or "")),
                r.get("OFF_LATITUDE"), r.get("OFF_LONGITUDE"), "closed", (r.get("EFFDATE") or "")[:10])

    out.close()


if __name__ == "__main__":
    main()
