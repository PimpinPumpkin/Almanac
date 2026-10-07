#!/usr/bin/env python3
"""Texas Comptroller: active cigarette, tobacco and e-cigarette retailers.

cpa_tx_tobacco  an outlet with an active retailer permit, open as of the
                day the dataset was last updated.

Only the outlet's name and address are read, not the taxpayer's. No
positions; addresses go to the Census geocoder.

Set CPA_TX_CITY to read one city only (for testing).

Public domain, as stated on the dataset.
https://data.texas.gov/d/n4rp-ar9b
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from evidence import Writer, address
from socrata import rows, updated

HOST, DATASET = "data.texas.gov", "n4rp-ar9b"


def main():
    as_of = updated(HOST, DATASET)
    where = "state = 'TX'"
    if os.environ.get("CPA_TX_CITY"):
        where += " AND city = '%s'" % os.environ["CPA_TX_CITY"].upper().replace("'", "''")
    out = Writer("cpa_tx_tobacco")
    seen = set()
    for r in rows(HOST, DATASET, where=where, select="tp_id,loc_nr,out_name,address,city,zip"):
        # one row per permit type at the same outlet
        key = "%s-%s" % (r.get("tp_id"), r.get("loc_nr"))
        if key in seen:
            continue
        seen.add(key)
        out.row("cpa_tx_tobacco", key, r.get("out_name"),
                address(r.get("address"), r.get("city"), "TX %s" % (r.get("zip") or "")[:5]),
                None, None, "open", as_of)
    out.close(geocode=True)


if __name__ == "__main__":
    main()
