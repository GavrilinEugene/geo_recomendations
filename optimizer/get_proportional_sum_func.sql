create function get_total_proportional4(zids integer[], kind_of_entity character varying) returns SETOF bigint
    language sql
as
$$
with
all_areas as (
    select  i.izid izid, i.ezid ezid, i.customers_cnt_home
    from optimizer.point_in_polygons_intersections i
    where i.ezid in ( select zid from optimizer.entity e where e.kind = kind_of_entity
                    union all
                    select unnest(zids)))
select sum(customers_cnt_home)::bigint from (
    select izid, max(customers_cnt_home) customers_cnt_home
    from all_areas
    group by izid
) q;
$$;
