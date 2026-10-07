-- status_of('evidence table'): one row per place that has any evidence.
--   closed   there is a closed record, and no open record dated after it
--   open     the newest record is open and dated within recent_days of the build
--   unknown  the newest record is open but stale
-- Places with no evidence at all are unknown and do not appear here.
create or replace macro status_of(ev, build_date, recent_days) as table (
  with e as (select * from query_table(ev)),
  agg as (
    select place_id,
           max(date) filter (where state = 'closed') as closed_date,
           max(date) filter (where state = 'open') as open_date,
           arg_max(source, date) filter (where state = 'closed') as closed_source,
           arg_max(source, date) filter (where state = 'open') as open_source,
           list(struct_pack(source, source_id, state, date, rule, dist_m := dist)
                order by date desc, source) as evidence
    from e group by place_id
  )
  select place_id,
         case
           when closed_date is not null and (open_date is null or open_date <= closed_date) then 'closed'
           when open_date >= build_date - recent_days then 'open'
           else 'unknown'
         end as status,
         case when closed_date is not null and (open_date is null or open_date <= closed_date)
              then closed_date else open_date end as status_date,
         case when closed_date is not null and (open_date is null or open_date <= closed_date)
              then closed_source else open_source end as status_source,
         -- a closed record that newer open evidence overrode; kept visible for review
         closed_date is not null and open_date > closed_date as conflict,
         evidence
  from agg
);
