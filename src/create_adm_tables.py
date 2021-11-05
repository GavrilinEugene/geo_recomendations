import os
import pandas as pd
import geopandas as gpd
from shapely.ops import cascaded_union

from sqlalchemy import create_engine
from utils import *
import argparse

"""
данный файл собирает создаёт пару таблиц с административным делением и численностью населения в БД
"""

LOCATIONS_GRID = os.path.join(os.getcwd(), "data/raw/01_CLocation_July.csv")
LOCATIONS_SHAPE = os.path.join(os.getcwd(), "data/raw/fishnet2021/fishnet2021.shp")
LOCATIONS_ADM = os.path.join(os.getcwd(), "data/raw/admzones2021/admzones2021.shp")

def run(args):

    login = args.login
    password = args.password
    host = args.serv
    port  = args.port
    engine = create_engine(f'postgresql://{login}:{password}@{host}:{port}/postgis')

    # регионы
    df_adm = gpd.read_file(LOCATIONS_ADM)
    df_adm = df_adm[['adm_name', 'okrug_name', 'sub_ter', 'geometry']]
    df_adm = gpd.GeoDataFrame(df_adm)

    # население
    df_home_job = pd.read_csv(LOCATIONS_GRID)
    df_shape = gpd.read_file(LOCATIONS_SHAPE)
    df_home_job.rename(columns={'zid': 'cell_zid'}, inplace=True)
    df_home_job = pd.merge(df_home_job, df_shape, on = ['cell_zid'])
    gdf_home_job = gpd.GeoDataFrame(df_home_job)

    # собираем фрейм cell_zid|регион|геометрия
    df_join = gpd.sjoin(df_adm, gdf_home_job, how='inner', op='intersects')
    df_adm_region = df_join[['cell_zid', 'adm_name', 'okrug_name', 'sub_ter']]
    drop_table(engine, 'public', 'adm_regions')
    df_adm_region.to_sql('adm_regions', engine, method=psql_insert_copy)
    print("adm_regions создана")

    # собираем фрейм adm_region|геометрия
    dfa_adm_group = df_join[['cell_zid', 'adm_name', 'okrug_name', 'sub_ter', 'geometry']]
    dfa_adm_group = dfa_adm_group.drop_duplicates(subset = ['cell_zid'])
    dfa_adm_group = dfa_adm_group.drop_duplicates(subset = ['adm_name'])[['adm_name', 'okrug_name', 'sub_ter', 'geometry']]
    dfa_adm_group = dfa_adm_group[dfa_adm_group['sub_ter']!='Московская область']
    df_all_reg = dfa_adm_group.copy()
    dfa_adm_group['geometry'] = dfa_adm_group['geometry'].apply(wkb_hexer)

    drop_table(engine, 'public', 'adm_regions_with_geometry')
    dfa_adm_group.to_sql('adm_regions_with_geometry', engine, method=psql_insert_copy)
    print("adm_regions_with_geometry создана")

    # собираем фрейм okrug_name|геометрия
    df_all_reg = df_all_reg.groupby(['okrug_name'])['geometry'].apply(lambda x: cascaded_union(x)).reset_index()

    combined = cascaded_union(df_all_reg['geometry'])
    combined_new = cascaded_union(df_all_reg[df_all_reg['okrug_name'].isin(['Троицкий административный округ',
                                                          'Новомосковский административный округ'])]['geometry'])
    combined_old = cascaded_union(df_all_reg[~df_all_reg['okrug_name'].isin(['Троицкий административный округ',
                                                            'Новомосковский административный округ', 'Все'])]['geometry'])

    df_all_reg.loc[df_all_reg.index.max()+1] = ['Все', combined]
    df_all_reg.loc[df_all_reg.index.max()+1] = ['Новая Москва', combined_new]
    df_all_reg.loc[df_all_reg.index.max()+1] = ['Старая Москва', combined_old]
    df_all_reg['index'] = [3,4,5,6,7,8,9,10,11,12,13,14,0,1,2]
    df_all_reg = df_all_reg.sort_values(by = ['index'])

    drop_table(engine, 'public', 'okrug_name_with_geometry')
    df_all_reg['geometry'] = df_all_reg['geometry'].apply(wkb_hexer)
    df_all_reg.to_sql('okrug_name_with_geometry', engine, method=psql_insert_copy)
    print("okrug_name_with_geometry создана")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='desc')
    parser.add_argument('-l', '--login', default='1')
    parser.add_argument('-p', '--password', default='2')
    parser.add_argument('-s', '--serv', default='3')
    parser.add_argument('-port', '--port', default='25432')
    args = parser.parse_args()
    run(args)    