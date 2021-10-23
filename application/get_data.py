import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


from sqlalchemy import create_engine
from sqlalchemy import text
import pandas as pd
import geopandas as gpd
import json
from shapely import wkb
from shapely.ops import unary_union, cascaded_union

# внутренние 
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

    sql = f"""select name, zid
                , point_lat, point_lon
                , address_name, pol_15min
                , okrug_name, population as customers_cnt_home
                from {dict_rename.get(type_)} """
    gdf = gpd.GeoDataFrame.from_postgis(con=engine,
                                        sql=text(sql), geom_col='pol_15min').reset_index()
    # gdf['combined_isochrone'] = gdf.name.map(gdf.groupby(['name'])['pol_15min'].apply(lambda x: cascaded_union(x)))
    # geo_json = json.loads(gdf[['index', 'customers_cnt_home', 'combined_isochrone']].to_json())                                        
    geo_json = json.loads(gdf[['index', 'customers_cnt_home', 'pol_15min']].to_json())
    return gdf, geo_json



def get_optimization_result(current_adm_layer, n_results = 1, infra_type='МФЦ'):
    """
    получение предрассчитанных данных оптимизации

    :param current_adm_layer: текущий административный район
    :param n_results: число новых объектов
    :param infra_type: текущий вид инфраструктуры

    """
    dict_rename = {'МФЦ': "mfc",
                   'Школы': "school", 
                   'Детские сады': "kindergarden",
                   'Больницы и поликлиники': "clinic"}

    if current_adm_layer == 'Все':
        sql_filter = "location_filter = 'all'"
    elif current_adm_layer == 'Новая Москва':
        list_okrug = "'Троицкий административный округ','Новомосковский административный округ'"
        sql_filter = f"location_filter in ({list_okrug})"
    elif current_adm_layer == 'Старая Москва':
        list_okrug = "'Троицкий административный округ','Новомосковский административный округ'"  
        sql_filter = f"location_filter not in ({list_okrug})"
    else:
        sql_filter = f"location_filter = '{current_adm_layer}'"

    sql_locations = f"""
        with t as (
            select * from optimizer.coverage_report
            where kind = '{dict_rename.get(infra_type)}'
            and {sql_filter}
            and zids_len = {n_results}
        limit 1)
        select center, pol_15min_with_base
        from izochrones_by_walk iw, t
        where iw.zid = any(t.zid_list);
    """

    sql_popultaion = f"""
        select zids_len, added_coverage 
        from optimizer.coverage_report
        where kind = '{dict_rename.get(infra_type)}'
        and {sql_filter}
        and zids_len <= {n_results}
    """

    df_analytics = pd.read_sql(con = engine, sql = sql_popultaion)
    gdf = gpd.GeoDataFrame.from_postgis(con=engine,
                                        sql=text(sql_locations), geom_col='pol_15min_with_base').reset_index()
    gdf['point_lat'] = gdf['center'].apply(lambda x: wkb.loads(x, hex=True).y)
    gdf['point_lon'] = gdf['center'].apply(lambda x: wkb.loads(x, hex=True).x)
                          
    geo_json = json.loads(gdf.to_json())
    center_point = wkb.loads(gdf['center'].iloc[0], hex=True)
    return gdf, geo_json, center_point, df_analytics


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
default_infra_n_value = 1