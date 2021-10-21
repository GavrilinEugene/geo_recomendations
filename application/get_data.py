from config import postgis_conn_uri
from sqlalchemy import create_engine
from sqlalchemy import text
import pandas as pd
import geopandas as gpd
import json
from shapely import wkb

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def create_connection():
    """

    """
    return create_engine(postgis_conn_uri)


def get_administrative_area_list():
    """
    Получение списка всех округов
    """
    df = pd.read_sql(
        con=engine, sql=f"""select okrug_name, index as value
         from public.okrug_name_with_geometry 
         order by index""")
    list_names = []
    for _, row in df.iterrows():
        list_names.append({'label': row['okrug_name'],
                           'value': row['value']})
    return list_names


def get_administrative_area_polygon():
    """
    Получение списка полигонов всех округов
    """
    gdf = gpd.GeoDataFrame.from_postgis(
        con=engine, sql=f"select * from public.okrug_name_with_geometry", geom_col='geometry')
    return json.loads(gdf.to_json())


def get_administrative_area_center(filter_name):

    gdf = gpd.GeoDataFrame.from_postgis(con=engine,
                                        sql=f"""select ST_CEntroid(geometry) as geometry from public.okrug_name_with_geometry
                                        where okrug_name = '{filter_name}'""", geom_col='geometry')
    return gdf.iloc[0]['geometry']


def get_population_for_polygon():
    """
    Получение списка полигонов 500X500 с населением
    """
    gdf = gpd.GeoDataFrame.from_postgis(con=engine, sql=f"""select geometry2 as geometry,customers_cnt_home, okrug_name 
                from public.all_data_by_zids""", geom_col='geometry')
    return json.loads(gdf.to_json()), gdf


def get_points(type_):
    """
    Получение объектов инфраструктуры с честным распределением населения
    """
    dict_rename = {'МФЦ': "public.mfc_info",
                   'Школы': "public.school_info", 
                   'Детские сады': "public.kindergarden_info",
                   'Больницы и поликлиники': "public.clinics_info"}

    sql = f"""select name
                , point_lat, point_lon
                , address_name, pol_15min
                , okrug_name, population as customers_cnt_home
                from {dict_rename.get(type_)} """
    gdf = gpd.GeoDataFrame.from_postgis(con=engine,
                                        sql=text(sql), geom_col='pol_15min').reset_index()
    geo_json = json.loads(gdf.to_json())
    return gdf, geo_json


def get_optimization_result(current_adm_layer, type_='МФЦ'):
    """

    """
    dict_rename = {'МФЦ': "mfc",
                   'Школы': "school", 
                   'Детские сады': "kindergarden",
                   'Больницы и поликлиники': "clinic"}

    if current_adm_layer == 'Все':
        sql_filter = "and 1=1"
    elif current_adm_layer == 'Новая Москва':
        list_okrug = "'Троицкий административный округ','Новомосковский административный округ'"
        sql_filter = f"and dz.okrug_name in ({list_okrug})"
    elif current_adm_layer == 'Старая Москва':
        list_okrug = "'Троицкий административный округ','Новомосковский административный округ'"  
        sql_filter = f"and dz.okrug_name not in ({list_okrug})"
    else:
        sql_filter = f"and dz.okrug_name = '{current_adm_layer}'"
     
    sql = f"""
            with t as (
            select experiment_ts, iteration, count_of_new_entities,
                sum(sum_prop_home) total_prop_sum
            from optimizer.combinator_results cr
            where 1=1
            and count_of_new_entities = 1
            and kind like '%new_{dict_rename.get(type_)}' -- mfc | new_mfc
            and exists(
                select from all_data_by_zids dz
                where 1=1
                and dz.cell_zid = cr.ezid
                and cr.kind like 'new%' --- проверяем что новый в нужном районе
                {sql_filter}
                )
            group by experiment_ts, iteration, count_of_new_entities
            order by sum(sum_prop_home) desc
            limit 1
        )
        select cr.sum_prop_home as customers_cnt_home, cr.kind, ibw.center, pol_15min_with_base from optimizer.combinator_results cr
        natural join t
        left join izochrones_by_walk ibw on (ibw.zid = cr.ezid)
    """
    gdf = gpd.GeoDataFrame.from_postgis(con=engine,
                                        sql=text(sql), geom_col='pol_15min_with_base').reset_index()
    gdf = gdf[gdf['kind'] == f'new_{dict_rename.get(type_)}']
    gdf['point_lat'] = gdf['center'].apply(lambda x: wkb.loads(x, hex=True).y)
    gdf['point_lon'] = gdf['center'].apply(lambda x: wkb.loads(x, hex=True).x)                                 
    geo_json = json.loads(gdf.to_json())
    center_point = wkb.loads(gdf['center'].iloc[0], hex=True)
    return gdf, geo_json, center_point


def get_total_population():
    sql = """
        select okrug_name, sum(customers_cnt_home) as customers_cnt_home
        from public.all_data_by_zids
        where okrug_name is not null
        group by okrug_name
    """
    df = pd.read_sql(
        con=engine, sql=sql)
    return df


engine = create_connection()
administrative_list = get_administrative_area_list()
infrastructure_list = [
    {'label': 'МФЦ', 'value': 0},
    {'label': 'Школы', 'value': 1},
    {'label': 'Детские сады', 'value': 2},
    {'label': 'Больницы и поликлиники', 'value': 3}]


# дефолтные значения
dafault_okrug_idx = 2
default_infra = infrastructure_list[0]['label']