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


def get_administrative_area_list(column='okrug_name'):
    """

    """
    df = pd.read_sql(
        con=engine, sql=f"select distinct {column} from public.adm_regions where {column} is not null")
    df['value'] = df.index
    list_names = []
    for _, row in df.iterrows():
        list_names.append({'label': row[column],
                           'value': row['value']})
    return list_names


def get_administrative_area_polygon():
    """

    """
    gdf = gpd.GeoDataFrame.from_postgis(
        con=engine, sql=f"select * from public.okrug_name_with_geometry", geom_col='geometry')
    return json.loads(gdf.to_json())


def get_administrative_area_center(filter_name):

    gdf = gpd.GeoDataFrame.from_postgis(con=engine,
                                        sql=f"""select ST_CEntroid(geometry) as geometry from public.okrug_name_with_geometry
                                        where okrug_name = '{filter_name}'""", geom_col='geometry')
    return gdf.iloc[0]['geometry']


def get_points(type_='МФЦ'):
    """

    """
    print(type_)
    if type_ == 'МФЦ':
        sql = f"""select name, point_lat, point_lon, address_name
             from public.fixed_points
             where name = 'Мои документы, центр государственных услуг' """
    elif type_ == 'Школы':
        sql = """
            select name, point_lat, point_lon, address_name
            from public.fixed_points a
            where 1 = 1
                AND type NOT IN ('attraction', 'station', 'street', 'parking', 'adm_div', 'building')
                AND (lower(name) LIKE '%лицей%' OR lower(name) LIKE '%гимназия%' OR lower(name) LIKE '%общеобразовательная%школа%')
                AND lower(name) NOT LIKE '%магазин%'
                AND lower(name) NOT LIKE '%журнал%'
                AND lower(name) NOT LIKE '%ветеринар%'
                AND lower(name) NOT LIKE '%автошкола%'
                AND lower(name) NOT LIKE '%автолицей%' 
            """
    elif type_ == 'Детские сады':
        sql = """
            SELECT name, point_lat, point_lon, address_name
            from public.fixed_points a
            where 1 = 1
                AND type NOT IN ('attraction', 'station', 'street', 'parking', 'adm_div', 'building')
                AND (lower(name) LIKE '%ясли%' OR lower(name) LIKE '%детский%сад%')
                AND lower(name) NOT LIKE '%магазин%'
                AND lower(name) NOT LIKE '%журнал%'
                AND lower(name) NOT LIKE '%ветеринар%'
            """
    df = pd.read_sql(con=engine, sql=text(sql))
    return df


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

engine = create_connection()
administrative_list = get_administrative_area_list("okrug_name")
infrastructure_list = [
    {'label': 'МФЦ', 'value': 0},
    {'label': 'Школы', 'value': 1},
    {'label': 'Детские сады', 'value': 2}]

default_okrug = administrative_list[0]['label']
default_infra = infrastructure_list[0]['label']
