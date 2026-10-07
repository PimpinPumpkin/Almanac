-- Coverage by category across every built region, for the README table.
-- Run: duckdb < sql/coverage.sql
.read sql/buckets.sql

select bucket(category) as category, count(*) as listed,
       round(100.0 * count(*) filter (where status <> 'unknown') / count(*), 1) as pct_with_status,
       count(*) filter (where status = 'open') as open,
       count(*) filter (where status = 'closed') as closed,
       round(100.0 * count(*) filter (where len(evidence) > 0) / count(*), 1) as pct_any_evidence
from read_parquet('data/out/places-*.parquet')
group by 1 order by pct_with_status desc;
select count(*) total, round(100.0*count(*) filter (where status<>'unknown')/count(*),1) pct from read_parquet('data/out/places-*.parquet');
