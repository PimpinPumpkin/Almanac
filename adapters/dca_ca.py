#!/usr/bin/env python3
"""California Department of Consumer Affairs: licensed salons, auto repair
shops and pharmacies.

dca_ca_salon     a current establishment or barber shop license from the
                 Board of Barbering and Cosmetology
dca_ca_auto      an active automotive repair dealer registration, smog
                 check station or vehicle safety inspection station from
                 the Bureau of Automotive Repair
dca_ca_pharmacy  an active retail pharmacy permit from the Board of
                 Pharmacy

All are open as of the day the files were read. The department refreshes
the files at the start of each month and shares them from a folder whose
file names stay the same while the ids behind them change, so the folder
pages are read first.

The files are mostly individual licensees (cosmetologists, smog
inspectors, pharmacists). Only rows marked as organizations with an
establishment license type are read, and nothing here creates a place:
a salon can be one person's name. Licenses marked delinquent are left out
(they are not evidence of anything yet; see SPEC.md on ended
registrations). No positions; addresses go to the Census geocoder.

California public record ("licensee data suitable for disclosure"). No
license stated. https://www.dca.ca.gov/consumers/public_info/index.shtml
"""
import csv
import datetime
import io
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from evidence import Writer, address, get

SHARE = "oss6hf8jys2bmgxqd2gdz7w4oepm2il9"
FOLDER = "https://dca.box.com/s/%s/folder/%%s" % SHARE
FILE = "https://dca.box.com/index.php?rm=box_download_shared_file&shared_name=%s&file_id=%%s" % SHARE
LISTED = re.compile(r'"typedID":"(f_\d+)".{0,400}?"name":"([^"]+_Data\d+\.xls)"')
# folder id, source, license types read, status that means in force
BOARDS = (
    ("72554173106", "dca_ca_salon", ("Establishment", "Barber Shop", "Chain Establishment"), "Current"),
    ("72555975852", "dca_ca_auto", ("Automotive Repair Dealer", "Smog Station", "Vehicle Safety Systems Inspection Station"), "Active"),
    ("72555304900", "dca_ca_pharmacy", ("Retail Pharmacy",), "Active"),
)


def main():
    today = datetime.date.today()
    out = Writer("dca_ca")
    for folder, source, kinds, in_force in BOARDS:
        files = LISTED.findall(get(FOLDER % folder).decode("utf-8", "replace"))
        if not files:
            raise SystemExit("dca_ca: no data files listed in folder %s" % folder)
        seen = set()
        for file_id, _ in sorted(files, key=lambda f: f[1]):
            text = get(FILE % file_id).decode("utf-8", "replace")
            for r in csv.DictReader(io.StringIO(text), delimiter="\t", quoting=csv.QUOTE_NONE):
                if r.get("Indiv/Org") != "O" or not (r.get("License Type") or "").startswith(kinds):
                    continue
                if r.get("License Status") != in_force or r.get("State") != "CA":
                    out.drop("not in force, or not in California")
                    continue
                try:
                    if datetime.datetime.strptime(r.get("Expiration Date") or "", "%m-%d-%Y").date() < today:
                        out.drop("expired")
                        continue
                except ValueError:
                    pass
                name, street = (r.get("Org/Last Name") or "").strip(), (r.get("Address Line 1") or "").strip()
                # a repair shop is also its own smog station
                if (name.upper(), street.upper()) in seen:
                    continue
                seen.add((name.upper(), street.upper()))
                out.row(source, r.get("License Number"), name,
                        address(street, r.get("City"), "CA %s" % (r.get("Zip") or "")[:5]),
                        None, None, "open", today.isoformat())
    out.close(geocode=True)


if __name__ == "__main__":
    main()
