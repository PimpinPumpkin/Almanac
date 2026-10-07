-- Matcher checks. Run: duckdb < tests/match_test.sql
-- Every row is one pair with the rule it should get (or null for no match).
-- Places are invented; coordinates sit in the District of Columbia test box.
.read sql/lib.sql
.bail on

create table cases (n int, a_name text, a_addr text, a_lat double, a_lng double,
                    b_name text, b_addr text, b_lat double, b_lng double, want text);
insert into cases values
  -- same number, name variants a register and a map would use
  (1, 'Bank of America, National Association', '1800 K St NW', 38.9022, -77.0421, 'Bank of America Financial Center', '1800 K Street Northwest', 38.9024, -77.0419, 'number'),
  (2, 'Chase Bank', '700 13th St NW', 38.8990, -77.0296, 'Chase', '700 13th St NW', 38.8991, -77.0297, 'number'),
  (3, 'SAFEWAY 1283', '1855 Wisconsin Ave NW', 38.9150, -77.0672, 'Safeway', '1855 Wisconsin Avenue Northwest', 38.9153, -77.0675, 'number'),
  (4, '7-ELEVEN 34567A', '912 New Hampshire Ave NW', 38.9015, -77.0530, '7-Eleven', '912 New Hampshire Ave NW', 38.9015, -77.0531, 'number'),
  (5, 'Whole Foods Market', '2201 I St NW', 38.9007, -77.0500, 'Wholefoods Market', '2201 I St NW', 38.9008, -77.0501, 'number'),
  -- same number but 250 m is the limit: a geocode a block off still matches, half a mile does not
  (6, 'Giant Food', '1400 7th St NW', 38.9090, -77.0220, 'Giant Food', '1400 7th St NW', 38.9108, -77.0220, 'number'),
  (7, 'Giant Food', '1400 7th St NW', 38.9090, -77.0220, 'Giant Food', '1400 7th St NE', 38.9090, -77.0120, null),
  -- same number, different business: a successor at the address must not match
  (8, 'Bank of Georgetown', '1054 31st St NW', 38.9040, -77.0610, 'Bank of America', '1054 31st St NW', 38.9040, -77.0610, null),
  (9, 'Capital Deli', '500 H St NE', 38.9000, -76.9990, 'Capitol Hill Market', '500 H St NE', 38.9000, -76.9990, null),
  -- chain twins across the street: different numbers, 40 m apart
  (10, 'Starbucks', '1801 K St NW', 38.9026, -77.0421, 'Starbucks', '1800 K St NW', 38.9022, -77.0421, null),
  -- no number on one side: close and same name matches, 100 m does not
  (11, 'Starbucks', null, 38.9022, -77.0421, 'Starbucks', '1800 K St NW', 38.9024, -77.0422, 'near'),
  (12, 'Starbucks', null, 38.9022, -77.0421, 'Starbucks', '1800 K St NW', 38.9031, -77.0421, null),
  (13, 'Chase Bank', null, 38.8990, -77.0296, 'Chase', '700 13th St NW', 38.8991, -77.0297, 'near'),
  -- numbers differ but the two points are on top of each other and the name is identical
  (14, 'Lincoln Theatre', '1215 U St NW', 38.9170, -77.0290, 'The Lincoln Theatre', '1213 U St NW', 38.9171, -77.0290, 'spot'),
  (15, 'Lincoln Theatre', '1215 U St NW', 38.9170, -77.0290, 'Lincoln Theater', '1213 U St NW', 38.9171, -77.0290, null),
  -- only leading words count: a shop named after its mall is not the mall
  (16, 'Fashion Centre at Pentagon City', '1100 S Hayes St', 38.8630, -77.0600, 'Timberland - Fashion Centre at Pentagon City', '1100 S Hayes St', 38.8632, -77.0601, null),
  (18, 'Deli', '10 Main St', 38.9000, -77.0000, 'Corner Deli and Market', '10 Main St', 38.9000, -77.0000, null),
  (19, 'George Town', '1077 Wisconsin Ave NW', 38.9050, -77.0630, 'Georgetown', '3150 M St NW', 38.9051, -77.0631, null),
  -- string similarity under 0.95 is not enough: two embassies, one street
  (20, 'Embassy of Albania', null, 38.9140, -77.0470, 'Embassy of Mali', null, 38.9141, -77.0471, null),
  (21, 'Royal Tobacco', '2604 Connecticut Ave NW', 38.9240, -77.0520, 'Royal Tobaco', '2604 Connecticut Avenue Northwest', 38.9240, -77.0521, 'number'),
  -- a branch is not the cash machine at the same address
  (22, 'Bank of America', '4301 49th St NW', 38.9450, -77.0960, 'Bank of America ATM', '4301 49th St NW', 38.9450, -77.0960, null),
  (17, 'Inn', '10 Main St', 38.9000, -77.0000, 'Capitol Inn', '10 Main St', 38.9000, -77.0000, null);

create table a as select n as id, norm_name(a_name) nn, house_number(a_addr) hn, a_lat lat, a_lng lng from cases;
create table b as select n as id, norm_name(b_name) nn, house_number(b_addr) hn, b_lat lat, b_lng lng from cases;

create table got as
  select c.n, c.a_name, c.b_name, c.want, m.rule, m.dist, m.sim
  from cases c left join (select * from match_pairs('a', 'b') where a_id = b_id) m on m.a_id = c.n;

.print failures (none is a pass):
select * from got where want is distinct from rule order by n;
select case when (select count(*) from got where want is distinct from rule) = 0
            then 'ok ' || (select count(*) from got) || ' cases'
            else error('matcher test failed') end as result;
