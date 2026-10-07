#!/usr/bin/env python3
"""Chicago Department of Business Affairs and Consumer Protection: business licenses.

bacp_chicago            a business site in Chicago with an issued license that
                        has not expired, open as of the day the dataset was
                        last updated.
bacp_chicago_cancelled  a site whose newest license record is a cancellation
                        from the last five years, closed on the day the
                        status changed. The matcher applies it to places
                        with no brand only.

Licenses with no fixed shop are left out (peddlers, raffles, special events,
valet operators, shared housing and shared kitchen users, pharmaceutical
representatives). The legal name is not read, only the trade name. Many
licensees work from home, so nothing here creates a place. Positions come
with the data.

City of Chicago Data Portal, see its Terms of Use.
https://data.cityofchicago.org/d/r5kz-chrr
"""
import datetime
import json
import os
import sys
import urllib.parse

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from evidence import Writer, address, get

VIEW = "https://data.cityofchicago.org/api/views/r5kz-chrr.json"
ROWS = "https://data.cityofchicago.org/resource/r5kz-chrr.json"
PAGE = 50000
NO_SHOP = ("peddler", "raffle", "special event", "valet", "shared housing", "shared kitchen",
           "pharmaceutical representative", "itinerant", "home occupation")
FIELDS = ("account_number,site_number,doing_business_as_name,address,zip_code,license_description,"
          "business_activity,license_status,expiration_date,license_status_change_date,latitude,longitude")


def main():
    today = datetime.date.today()
    since = (today - datetime.timedelta(days=5 * 365)).isoformat()
    updated = datetime.datetime.fromtimestamp(
        json.loads(get(VIEW))["rowsUpdatedAt"], datetime.timezone.utc).date().isoformat()
    live, cancelled, offset = {}, {}, 0
    while True:
        q = {"$select": FIELDS,
             "$where": "city = 'CHICAGO' AND ((license_status = 'AAI' AND expiration_date > '%s') OR "
                       "(license_status = 'AAC' AND license_status_change_date > '%s'))" % (today.isoformat(), since),
             "$limit": PAGE, "$offset": offset, "$order": "id"}
        rows = json.loads(get(ROWS + "?" + urllib.parse.urlencode(q)))
        for r in rows:
            kind = ("%s %s" % (r.get("license_description") or "", r.get("business_activity") or "")).lower()
            if any(word in kind for word in NO_SHOP):
                continue
            site = "%s-%s" % (r.get("account_number"), r.get("site_number"))
            if r["license_status"] == "AAI":
                live[site] = r
            elif (r.get("license_status_change_date") or "") > (cancelled.get(site) or {}).get("license_status_change_date", ""):
                cancelled[site] = r
        offset += len(rows)
        if len(rows) < PAGE:
            break

    out = Writer("bacp_chicago")

    def emit(source, site, r, state, date):
        out.row(source, site, r.get("doing_business_as_name"),
                address((r.get("address") or "").strip(), "CHICAGO", "IL %s" % (r.get("zip_code") or "")[:5]),
                r.get("latitude"), r.get("longitude"), state, date)

    for site, r in live.items():
        emit("bacp_chicago", site, r, "open", updated)
    for site, r in cancelled.items():
        if site not in live:
            emit("bacp_chicago_cancelled", site, r, "closed", r["license_status_change_date"][:10])
    out.close()


if __name__ == "__main__":
    main()
