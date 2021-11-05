DROP TABLE IF EXISTS public.info_kindergarden;

WITH mfc AS 
( 
    SELECT distinct 
        name, point_lat, point_lon, address_name, 
        ST_SetSRID(ST_point(point_lon, point_lat), 4326) as point_geo
    from public.fixed_points a
    where 1 = 1
------ДЕТ САДЫ  
    AND type NOT IN ('attraction', 'station', 'street', 'parking', 'adm_div', 'building')
    AND  (lower(name) LIKE '%ясли%' OR lower(name) LIKE '%детский%сад%')
    AND lower(name) NOT LIKE '%магазин%'
    AND lower(name) NOT LIKE '%журнал%'
)
, find_zid AS 
(
    SELECT mfc.*
    , zid
    , ST_SetSRID(center, 4326) center
    , ST_SetSRID(geometry_base, 4326) as geometry_base
    , ST_SetSRID(pol_15min, 4326) as pol_15min
    FROM mfc
    LEFT JOIN public.izochrones_by_walk a
    ON ST_Contains(ST_SetSRID(geometry_base, 4326), ST_SetSRID(point_geo, 4326))
    WHERE geometry_base is NOT NULL
)
, adm_zones AS 
(
    SELECT cell_zid
    , MAX(adm_name) as adm_name
    , MAX(okrug_name) AS okrug_name
    , MAX(sub_ter) sub_ter
    FROM public.adm_regions 
    GROUP BY cell_zid
)
SELECT t1.*
    , t2.adm_name
    , t2.okrug_name
    , t2.sub_ter
INTO public.info_kindergarden
FROM find_zid t1
LEFT JOIN adm_zones t2
    ON t1.zid = t2.cell_zid