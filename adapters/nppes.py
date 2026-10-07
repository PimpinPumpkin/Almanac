#!/usr/bin/env python3
"""NPPES (National Provider Identifier registry): health care organizations.

nppes_orgs  organizations (entity type 2) that are not deactivated, at their
            practice location, open as of the later of Last Update Date and
            Certification Date. Either date means someone at the organization
            touched the record that day.

Individual clinicians (entity type 1) are left out. Records are rarely
deactivated when a practice closes, so there is no closed evidence here, and
an old date means little. The file has addresses but no positions.

The monthly file is about 1.2 GB zipped and 12 GB inside; it is read as a
stream and never unpacked to disk.

Public domain (US federal government work).
https://download.cms.gov/nppes/NPI_Files.html
"""
import csv
import io
import os
import re
import sys
import urllib.parse
import zipfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from evidence import CACHE, Writer, address, download, get

INDEX = "https://download.cms.gov/nppes/NPI_Files.html"
DBA = "3"


def mdy(s):
    """05/15/2025 -> 2025-05-15, blank -> ''"""
    return "%s-%s-%s" % (s[6:10], s[0:2], s[3:5]) if len(s) == 10 else ""


def main():
    page = get(INDEX).decode("utf-8", "replace")
    # the monthly file is named for its month; weekly files carry dates instead
    link = re.search(r"NPPES_Data_Dissemination_[A-Za-z]+_\d{4}(_V2)?\.zip", page)
    if not link:
        raise SystemExit("monthly file link not found on " + INDEX)
    url = urllib.parse.urljoin(INDEX, link.group(0))
    path = download(url, os.path.join(CACHE, "nppes", os.path.basename(url)))

    out = Writer("nppes")
    with zipfile.ZipFile(path) as z:
        member = next(n for n in z.namelist() if n.startswith("npidata_pfile") and "fileheader" not in n)
        with z.open(member) as raw:
            f = io.TextIOWrapper(raw, encoding="utf-8", errors="replace", newline="")
            head = next(csv.reader([f.readline()]))
            col = {name: i for i, name in enumerate(head)}
            c_type = col["Entity Type Code"]
            c_legal = col["Provider Organization Name (Legal Business Name)"]
            c_other = col["Provider Other Organization Name"]
            c_other_type = col["Provider Other Organization Name Type Code"]
            c_street = col["Provider First Line Business Practice Location Address"]
            c_city = col["Provider Business Practice Location Address City Name"]
            c_state = col["Provider Business Practice Location Address State Name"]
            c_zip = col["Provider Business Practice Location Address Postal Code"]
            c_country = col["Provider Business Practice Location Address Country Code (If outside U.S.)"]
            c_update = col["Last Update Date"]
            c_gone = col["NPI Deactivation Date"]
            c_back = col["NPI Reactivation Date"]
            c_cert = col["Certification Date"]
            # screen on the second field before the costly parse of 330 columns
            for line in f:
                if '","2",' not in line[:20]:
                    continue
                r = next(csv.reader([line]))
                if r[c_type] != "2" or r[c_country] not in ("US", ""):
                    continue
                if r[c_gone] and not r[c_back]:
                    out.drop("deactivated")
                    continue
                name = r[c_other] if r[c_other_type] == DBA and r[c_other] else r[c_legal]
                date = max(mdy(r[c_update]), mdy(r[c_cert]))
                out.row("nppes_orgs", r[0], name,
                        address(r[c_street], r[c_city], "%s %s" % (r[c_state], r[c_zip][:5])),
                        None, None, "open", date)
    out.close()


if __name__ == "__main__":
    main()
