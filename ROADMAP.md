# Roadmap

What gets built next, in order, and what counts as done. The aim is the
coverage and freshness people expect from a commercial map, from open
sources only, United States first.

Where things stand (build of 2026-10-07): 19.4 million places, 9.4% with a
dated status. Banks 67%, chain restaurants 62%, gas stations 48%, grocery
45%, independent restaurants 22%, bars 14%, everything else 6%.

## How every item is done

These rules do not change from item to item.

1. Fetch the source first and read its real layout. Record its license and
   URL in SOURCES.md before any code is merged.
2. One adapter per source, emitting the evidence format in SPEC.md section 5.
3. Build the test regions and read 40 matches per rule. Write the count in
   SPEC.md.
4. A closure signal must also pass the independent check: where another
   source can speak, it must agree far more often than not. The ones that
   failed so far (SNAP end dates, French register closures, tank removals,
   Foursquare by name) all looked reasonable before they were measured.
5. A rule that is wrong more than rarely is removed and written down with
   its numbers in SPEC.md section 9.
6. Tests pass, docs match the code, the change is pushed, and the monthly
   build stays green.

## 1. United States: licensed categories

The categories where a register can make coverage complete.

- **1.1 State alcohol license lists.** One adapter per state. Done:
  California, Colorado, DC, Florida, Missouri, New York, Oregon, Texas. Then Colorado,
  Missouri, Oregon, Washington, Pennsylvania, Illinois, and on through
  every state that publishes one. Done for a state when its bars pass 40%
  with a status.
- **1.2 Missing license flag** for each of those states whose list has
  positions (today: DC and New York).
- **1.3 Restaurant inspections.** Done: Florida (Jacksonville restaurants
  went to 31% with a status), New York City, and Chicago (56% in the test
  box, with an "out of business" result that works as a closure for
  independents), King County, Washington (52% in a Seattle box), Delaware,
  Montgomery County, Maryland, and New York's retail food stores.
  Next New York State, Los Angeles County, then other large cities.
  Target: independent restaurants from 18% to 40% in covered areas.
- **1.4 Fuel.** Use the tank registry's "temporarily out of service" count
  to lower the score of mothballed stations. EV chargers from the federal
  station list (needs a key, see the last section).
- **1.5 Lodging, pharmacies, child care.** State license lists where
  published, Florida's hotel and restaurant licenses first.

## 2. United States: the long tail

Salons, repair shops, small retail. 84% of all rows, 6% with a status.

- **2.1 Auto repair registrations.** Done: New York (repair shops,
  inspection stations, dealers). Next California, Florida, Michigan.
- **2.2 Cosmetology and barber shop licenses.** Done: New York and Texas
  (Houston nail salons went from 7% with a status to 52%). Next: state by
  state.
- **2.3 Sales tax permit lists.** Done: Texas, the biggest long-tail source
  so far. In a Houston box a quarter of auto repair, clothing, furniture
  and jewelry stores now have a status. Also done: Delaware's business
  license list, which took the whole state from 8% of places with a status
  to 19%, Pennsylvania's retail sales licenses, and Chicago's business
  licenses, whose cancellations also work as closures, and city business
  licenses for DC, Philadelphia, Sacramento, Seattle and Denver. Next: any other state
  that publishes active permits or licenses.
- **2.4 State inspection and emissions station lists.**
- **2.5 Geocode the address-only registers.** Done for California and Texas
  licenses with the Census geocoder: California went from 25% of licenses
  finding a place to 61%. Still to do: the federal address-only registers
  (NPPES, IRS, CMS, NCUA), and a way to pin a geocoded point to the right
  building so these registers can add missing places.

Done when "everything else" passes 15% in states with two or more of these.

## 3. Quality

- **3.1 One category vocabulary.** First step done: every row has a
  `category_group`, one of Overture's thirteen top-level groups. Still to
  do: a finer shared list (restaurant, bar, bank, salon) below the groups.
- **3.2 Trade name aliases.** About a third of unmatched DC licenses are the
  same place under a longer or shorter name. Learn aliases from the pairs
  that share an exact address.
- **3.3 Score calibration.** Build a labeled set (places with both a
  register verdict and an independent one) and fit `open_score` to it
  instead of the current rule of thumb.
- **3.4 Names and categories for places minted from registers.** Done for
  names and streets: title case, store numbers stripped. Still to do: carry
  the register's own business type.
- **3.5 Duplicates inside Overture** beyond exact name matches.

## 4. Operations

- **4.1 Monthly change file.** Built: each release compares its status
  files with the release before and publishes `changes.parquet`. It first
  produces something at the second release that has status files. That is
  also what will measure id churn.
- **4.2 Tests on every push.** Done: matcher tests, a syntax check of every
  script, and a check that every adapter is documented.
- **4.3 Failures.** Done: a state whose build fails is tried once more,
  and the release notes name any state left out. A source whose adapter
  fails keeps last run's file, so one portal being down does not stop the
  build.
- **4.4 Source watch.** Done: each build compares every register file with
  the one before. A file that lost more than half its rows is not used
  (last run's is), a file that moved by more than a fifth is flagged, and
  the list rides along as `source-watch.txt` and in the release notes.
  Still to do: notice a layout change that keeps the row count.

- **4.5 Held records.** Done for Missouri's "out of business" list and
  Colorado's expired and surrendered list: each
  build adds the current list to a file that rides along as a release
  asset (`held.tar.gz`), unused until there is enough to test. Next:
  Florida's weekly emergency closures, and the test itself once a few months have piled up.

## 5. Readers

Work in this repo that makes the files easier to consume. Changes to Vela
itself happen in Vela.

- **5.1 Region ids in the manifest.** Done: each region carries its country,
  its ISO 3166-2 code and the names of the OSM extracts it was built from.
- **5.2 A small status file per state.** Done: `status-<region>.parquet`.

## 6. Other countries

- **6.1 France, whole country.** Regions, a full SIRENE run, license check.
- **6.2 United Kingdom.** Food hygiene ratings, then Companies House.
- **6.3 Addresses where the number follows the street**, which unlocks
  Germany, Spain and Italy for the global signals.
- **6.4 Canada**, province by province.

Each country starts with the global signals alone, then gains registers.

## 7. Contributions

- **7.1 A simple way for a map user to confirm a place** that lands in
  OpenStreetMap as a survey date or a closure tag, and so in the next build.
- **7.2 Owner updates**, if 7.1 proves people use it.

## 8. Hours, popularity, reviews

Asked for by the owner on 2026-10-07.

- **8.1 Hours from what is already open.** Done: `opening_hours` from
  AllThePlaces and OSM, with its source and date.
- **8.2 Hours from places' own websites, without crawling.** Common Crawl
  and Web Data Commons publish the schema.org markup found on the public
  web. Take LocalBusiness records with opening hours and match them to
  places by website and address. Measure how many are right against OSM
  and AllThePlaces hours for the same place before using them.
- **8.3 A crawler of our own** for the websites Overture lists, reading
  only schema.org markup, obeying robots.txt, a few pages per site per
  month. Only if 8.2 leaves a large gap, because it is the first part of
  this project that would not be a bulk download.
- **8.4 Popularity.** No open source has foot traffic. A stand-in can be
  built from what is open: how many sources list the place, Wikipedia page
  views for places with an article, how often mappers touch it. To be
  tested before it is called popularity.
- **8.5 Reviews.** A separate project. Mangrove (open reviews, CC BY) is
  the only open review set found so far and it is small. Nothing here
  until the owner decides where reviews would be stored.
- **8.6 Owners keeping their own listing current.** Open question. The
  cheapest form is 7.2: an owner edits OSM, or their own site's markup,
  and the next build picks it up.

## Standing decisions

Set by the owner on 2026-10-06.

- **Test areas.** The fixed ones (a District of Columbia box, Sacramento and
  Davis, Delaware, Kentucky, Paris) plus, for any other state, a box around
  that state's largest city.
- **Keys.** None for now. Sources that need a key wait.
- **Licenses.** Public domain, CC0, ODbL, CC BY and open government
  licences (Licence Ouverte, OGL) may be added without asking, credited in
  NOTICE. US state and local public records that state no license may also
  be added, marked `none-stated` on every row they touch. Anything else
  with no stated license is asked about first.
- **Order.** Section 1 first.
- **New York outside the city.** Buffalo is the test area for sources that
  leave New York City out (2026-10-07).
- **Git history** stays as it is; no rewrite (2026-10-07).

## What needs the owner

Everything above can proceed without asking, except these.

- **Keys and accounts**, if that decision is revisited, and where a key
  would be stored.
- **License calls** outside the list above.
- **Anything that costs money or needs a server** beyond GitHub Actions and
  release storage.
- **Speaking for the project**: contacting another project or a data owner.
- **Deleting a release.**
- **A source or rule that fails in a way the rules above do not settle.**
