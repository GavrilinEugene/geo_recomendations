with recursive filter as (
    select distinct cell_zid from all_data_by_zids dz
    where okrug_name = 'Северо-Западный административный округ'
),
t as (
select experiment_ts, iteration, count_of_new_entities,
       sum(sum_prop_home) total_prop_sum,
       max(case when kind like 'new%' then ezid end) zid,
       max(case when kind like 'new%' then sum_prop_home end) new_obj_sum
from optimizer.combinator_results cr join filter f on f.cell_zid = cr.ezid
where 1=1
  and count_of_new_entities = 1
  and kind in ('clinic', 'new_clinic')
group by experiment_ts, iteration, count_of_new_entities
having max(case when kind like 'new%' then ezid end) is not null
order by sum(sum_prop_home) desc
limit 10
)
,t2 as (
         select t.zid::int zid, iw.center from t
             join izochrones_by_walk iw
                 on (t.zid = iw.zid)
),
cte (zid, center, iteration, zid_list, multi_point) as (
    select zid, center, 1::bigint iteration, array [zid] zid_list, center multi_point
    from t2
    union all
    select distinct on (l.zid, r.multi_point) l.zid, l.center, iteration + 1 iteration,
                        r.zid_list | array [l.zid]  as zid_list,
                    st_union(l.center, r.multi_point) multi_point
    from t2 l
    join cte r on l.zid > r.zid
    where 1=1
    and r.iteration < 10
    and l.zid > r.zid
    and not l.zid=any(r.zid_list)
    and st_distance(l.center, r.center, false)  > 2500
    and st_distance(l.center, r.multi_point, false) between 2000 and 150000 / r.iteration -- верхняя граница применима только если точек много
)
select zid_list, now() ts, 'clinic' kind, 'Северо-Западный административный округ' okrug from cte;