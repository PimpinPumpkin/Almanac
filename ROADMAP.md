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
  California, Colorado, DC, Florida, New York, Texas. Then Colorado,
  Missouri, Oregon, Washington, Pennsylvania, Illinois, and on through
  every state that publishes one. Done for a state when its bars pass 40%
  with a status.
- **1.2 Missing license flag** for each of those states whose list has
  positions (today: DC and New York).
- **1.3 Restaurant inspections.** Done: Florida (Jacksonville restaurants
  went to 31% with a status), New York City, and Chicago (56% in the test
  box, with an "out of business" result that works as a closure for
  independents). Next New York State, Los Angeles County, King County,
  then other large cities.
  Target: independent restaurants from 18% to 40% in covered areas.
- **1.4 Fuel.** Use the tank registry's "temporarily out of service" count
  to lower the score of mothballed stations. EV chargers from the federal
  station list (needs a key, see the last section).
- **1.5 Lodging, pharmacies, child care.** State license lists where
  published, Florida's hotel and restaurant licenses first.

## 2. United States: the long tail

Salons, repair shops, small retail. 84% of all rows, 6% with a status.

- **2.1 Auto repair registrations**: California, New York, Florida, Michigan.
- **2.2 Cosmetology and barber shop licenses**, state by state.
- **2.3 Sales tax permit lists** where a state publishes active permits
  (Texas does).
- **2.4 State inspection and emissions station lists.**
- **2.5 Geocode the address-only registers.** Done for California and Texas
  licenses with the Census geocoder: California went from 25% of licenses
  finding a place to 61%. Still to do: the federal address-only registers
  (NPPES, IRS, CMS, NCUA), and a way to pin a geocoded point to the right
  building so these registers can add missing places.

Done when "everything else" passes 15% in states with two or more of these.

## 3. Quality

- **3.1 One category vocabulary.** Today a row carries an Overture term or
  an OSM tag. A reader needs one list.
- **3.2 Trade name aliases.** About a third of unmatched DC licenses are the
  same place under a longer or shorter name. Learn aliases from the pairs
  that share an exact address.
- **3.3 Score calibration.** Build a labeled set (places with both a
  register verdict and an independent one) and fit `open_score` to it
  instead of the current rule of thumb.
- **3.4 Names and categories for places minted from registers.** Title case,
  strip store numbers, and carry the register's own business type.
- **3.5 Duplicates inside Overture** beyond exact name matches.

## 4. Operations

- **4.1 Monthly change file.** For each release: places that opened, closed,
  appeared or vanished since the last one. This is also what measures id
  churn, due at the second monthly build.
- **4.2 Tests on every push**, not only before a build.
- **4.3 A failed state retries on its own** and the release notes say which
  states, if any, are a month old.
- **4.4 Source watch.** The build reports when a source's layout or row
  count shifts by more than a set amount, so a silent upstream change does
  not ship.

## 5. Readers

Work in this repo that makes the files easier to consume. Changes to Vela
itself happen in Vela.

- **5.1 Region ids in the manifest** that match the reader's region catalog.
- **5.2 A small status file per state** (id, status, date, source, score)
  for readers that only need to join on Overture id.

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

## What needs the owner

Everything above can proceed without asking, except these.

- **Keys and accounts**, if that decision is revisited, and where a key
  would be stored.
- **License calls** outside the list above.
- **Anything that costs money or needs a server** beyond GitHub Actions and
  release storage.
- **Speaking for the project**: contacting another project or a data owner.
- **Rewriting git history** or deleting a release.
- **A source or rule that fails in a way the rules above do not settle.**
