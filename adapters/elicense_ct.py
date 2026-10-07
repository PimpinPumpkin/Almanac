#!/usr/bin/env python3
"""Connecticut: state licenses and credentials (the eLicense register).

elicense_ct  an active, unexpired state license for a business with a shop
             front: liquor permits for restaurants, cafes, package stores
             and grocers, bakeries, dairy stores, frozen dessert retailers,
             pharmacies and stores selling non-prescription drugs, vapor
             dealers, lottery agents, gasoline dealers, child care centers,
             funeral homes, health clubs, kennels, grooming and pet shops,
             opticians. Open as of the day the dataset was last updated.

The register has 2.7 million rows across every credential the state
issues, most of them people or products. Only the business license types
above are read. The trading name is used when there is one. No positions;
addresses go to the Census geocoder.

Public domain, as stated on the dataset.
https://data.ct.gov/d/ngch-56tr
"""
import datetime
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from evidence import Writer, address
from socrata import rows, updated

HOST, DATASET = "data.ct.gov", "ngch-56tr"
KINDS = ("LIR", "LIP", "LGB", "LCA", "LRW", "LIC", "LIH", "LPC", "LCR", "LMB", "LFW",  # liquor
         "BAK", "RDS", "FDR", "PCY", "PME", "ECD", "LSA", "RGD",                      # food, drugs, counters
         "DCCC", "FH", "HCL", "HCM", "CKF", "GRF", "PSF", "OSP")


def main():
    today = datetime.date.today().isoformat()
    as_of = updated(HOST, DATASET)
    out = Writer("elicense_ct")
    seen = set()
    where = ("status = 'ACTIVE' AND state = 'CT' AND businessname IS NOT NULL AND credentialtype IN (%s) "
             "AND (expirationdate IS NULL OR expirationdate > '%s')" % (", ".join("'%s'" % k for k in KINDS), today))
    for r in rows(HOST, DATASET, where=where, select="credentialid,businessname,dba,address,city,zip"):
        name = (r.get("dba") or r.get("businessname") or "").strip()
        street = (r.get("address") or "").strip()
        # a shop holds several licenses (bakery, dairy, lottery) under one name
        if (name.upper(), street.upper()) in seen:
            continue
        seen.add((name.upper(), street.upper()))
        out.row("elicense_ct", r["credentialid"], name,
                address(street, (r.get("city") or "").upper(), "CT %s" % (r.get("zip") or "")[:5]),
                None, None, "open", as_of)
    out.close(geocode=True)


if __name__ == "__main__":
    main()
