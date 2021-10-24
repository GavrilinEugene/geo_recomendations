DO
$do$
DECLARE
   iter_counter bigint := 0;
   iter_zid bigint;
   iter_pol_15min_with_base geometry;
BEGIN
    FOR iter_zid, iter_pol_15min_with_base in SELECT zid, pol_15min_with_base
        FROM optimizer.available_points LOOP
        drop table if exists iter_zids;
        create temp table iter_zids as
        select iter_zid zid, iter_pol_15min_with_base pol_15min_with_base
            union all
        select zid, pol_15min_with_base from optimizer.entity;
        iter_counter := iter_counter + 1;
        RAISE NOTICE 'The counter is %', iter_counter;
        with
        all_areas as (
            select  i.izid izid, e.zid ezid, i.customers_cnt_home
            from iter_zids e join optimizer.point_in_polygons_intersections i
                    on e.zid = i.ezid
        ),
        porportional_cnt_home as (
            select izid,
                   sum(customers_cnt_home) sum_customers_cnt_home,
                   count(distinct ezid) countd_izid,
                   customers_cnt_home / count(distinct ezid) prop_home,
                   array_agg(distinct ezid) ezid_list
            from all_areas
            group by izid, customers_cnt_home
        )
        insert into optimizer.combinator_results (ezid, sum_prop_home, iteration, experiment_ts)
        select ezid, sum(prop_home) sum_prop_home, iter_counter, now()
        from (
        select unnest(ezid_list) ezid, prop_home from porportional_cnt_home) q
        group by 1;
    END LOOP;
    return;
END
$do$
