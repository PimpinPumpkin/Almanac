-- What changed between two builds. Run by the scheduled build:
--   duckdb -c "set variable prev = 'prev'; set variable cur = 'data/out';" < tools/changes.sql
-- Reads status-*.parquet from both folders and writes changes.parquet and a
-- one-line-per-kind summary in the current folder.
create table old as select *, regexp_extract(filename, 'status-(.*)\.parquet', 1) as region
  from read_parquet(getvariable('prev') || '/status-*.parquet', filename = true);
create table new as select *, regexp_extract(filename, 'status-(.*)\.parquet', 1) as region
  from read_parquet(getvariable('cur') || '/status-*.parquet', filename = true);

create table changes as
  select coalesce(n.region, o.region) as region, coalesce(n.id, o.id) as id,
         case
           when o.id is null then 'appeared'
           when n.id is null then 'vanished'
           when o.status <> 'closed' and n.status = 'closed' then 'closed'
           when o.status = 'closed' and n.status = 'open' then 'reopened'
           when o.status = 'unknown' and n.status = 'open' then 'confirmed_open'
           when o.status = 'open' and n.status = 'unknown' then 'went_quiet'
           when o.status = 'closed' and n.status = 'unknown' then 'closure_withdrawn'
         end as change,
         o.status as old_status, n.status as new_status,
         n.status_date, n.status_source
  from new n full outer join old o on o.id = n.id and o.region = n.region
  where o.id is null or n.id is null or o.status <> n.status;

copy (select * from changes order by region, change, id)
  to (getvariable('cur') || '/changes.parquet') (format parquet, compression zstd);
copy (select change, count(*) as places from changes group by 1 order by 2 desc)
  to (getvariable('cur') || '/changes-summary.csv') (header);
