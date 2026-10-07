#!/usr/bin/env python3
"""New York Department of Taxation and Finance: registered retail dealers of
cigarettes, tobacco and vapor products.

tax_ny_tobacco  a retail location holding a current registration, open as
                of the day the dataset was last updated. Positions come
                with the data.

Mostly convenience stores, delis, gas stations and smoke shops. The name is
the registrant's, which for a sole owner is a person: rows are evidence for
places that are already listed, and nothing here creates a place.

OPEN-NY Terms of Use. https://data.ny.gov/d/55xf-9jat
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from evidence import Writer, address
from socrata import point, rows, updated

HOST, DATASET = "data.ny.gov", "55xf-9jat"


def main():
    as_of = updated(HOST, DATASET)
    out = Writer("tax_ny_tobacco")
    seen = set()
    for r in rows(HOST, DATASET, where="phys_state_adr = 'NY'",
                  select="cor_id,cor_seq_nmbr,last_or_bus_name,phys_ln_2_adr,phys_city_adr,phys_zip_5_adr,georeference"):
        # one row each for cigarettes and vapor at the same counter
        key = "%s-%s" % (r.get("cor_id"), r.get("cor_seq_nmbr"))
        if key in seen:
            continue
        seen.add(key)
        lat, lng = point(r.get("georeference"))
        out.row("tax_ny_tobacco", key, r.get("last_or_bus_name"),
                address(r.get("phys_ln_2_adr"), r.get("phys_city_adr"), "NY %s" % (r.get("phys_zip_5_adr") or "")),
                lat, lng, "open", as_of)
    out.close()


if __name__ == "__main__":
    main()
