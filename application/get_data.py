from sqlalchemy import create_engine
from sqlalchemy import text
import pandas as pd
import geopandas as gpd
import json
from shapely import wkb

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import postgis_conn_uri


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
    gdf = gpd.GeoDataFrame.from_postgis(con=engine,sql=f"select geometry2 as geometry,customers_cnt_home from public.all_data_by_zids", geom_col='geometry')
    return json.loads(gdf.to_json()),gdf


def get_points(type_='МФЦ'):
    """

    """
    if type_ == 'МФЦ':
        sql = f"""select name
                , point_lat, point_lon
                , address_name, pol_15min
                , okrug_name, sum_prop_home as customers_cnt_home
                from public.mfc_info"""
        table_name = "public.mfc_info"
        gdf = gpd.GeoDataFrame.from_postgis(con=engine,
                                        sql=text(sql), geom_col='pol_15min').reset_index()
        geo_json = json.loads(gdf.to_json())    
        return gdf, geo_json
    elif type_ == 'Школы':
        table_name = "public.school_info"
    elif type_ == 'Детские сады':
        table_name = "public.kindergarden_info"

    sql = f"""select name
                , point_lat, point_lon
                , address_name, pol_15min
                , okrug_name, population as customers_cnt_home
                from {table_name} """
    gdf = gpd.GeoDataFrame.from_postgis(con=engine,
                                        sql=text(sql), geom_col='pol_15min').reset_index()
    geo_json = json.loads(gdf.to_json())    
    return gdf, geo_json

def get_optimization_result():
    """
    Запуск и рассчёт оптимизации
    :return изохрону лучшего варианта размещения
    """
    sql = """
        select i.center, i.pol_15min, i.customers_cnt_home
        from optimizer.combinator_results r
        left join public.izochrones_by_walk i on i.zid = r.ezid
        where 1=1
            and experiment_ts  = '2021-10-17 11:58:29.613143'
            and iteration = 8433
            limit 1
    """    
    gdf = gpd.GeoDataFrame.from_postgis(con=engine,
                                        sql=text(sql), geom_col='pol_15min').reset_index()
    geo_json = json.loads(gdf.to_json())   
    center_point = wkb.loads(gdf['center'].iloc[0], hex=True)                                     
    return gdf , geo_json, center_point

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
    {'label': 'Детские сады', 'value': 2}]


# дефолтные значения
dafault_okrug_idx = 2
# default_okrug = administrative_list[dafault_okrug_idx]['label']
default_infra = infrastructure_list[0]['label']

