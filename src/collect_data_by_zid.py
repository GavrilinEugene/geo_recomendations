#!/usr/bin/env python
# coding: utf-8

import pandas as pd
import geopandas as gpd
import json
import warnings
import csv
import sys

from shapely import wkt
from sqlalchemy import create_engine
from io import StringIO

from utils import wkb_hexer,psql_insert_copy
import argparse

warnings.filterwarnings("ignore")

sys.path.append('../src/')

def run(args):

    print(args)
    login = args.login
    password = args.password
    s = args.serv
    #население
    df_home_job = pd.read_csv("../data/raw/01_CLocation_July.csv")
    df_shape = gpd.read_file("../data/raw/fishnet2021/fishnet2021.shp")
    df_home_job.rename(columns={'zid': 'cell_zid'}, inplace=True)
    df_home_job = pd.merge(df_home_job, df_shape, on = ['cell_zid'])
    gdf_home_job = gpd.GeoDataFrame(df_home_job)
    gdf_home_job.head()

    #адм районы
    df_adm = gpd.read_file("../data/raw/admzones2021/admzones2021.shp")
    df_adm = df_adm[['adm_name', 'okrug_name', 'sub_ter', 'geometry']]
    df_adm = gpd.GeoDataFrame(df_adm)
    df3 = gpd.sjoin(df_adm, gdf_home_job, how='inner', op='intersects')
    df3 = df3[['cell_zid', 'adm_name', 'okrug_name', 'sub_ter', 'geometry','customers_cnt_home',
               'customers_cnt_job','customers_cnt_day','customers_cnt_move']]
    df3 = df3.drop_duplicates(subset = ['cell_zid'],keep = 'last')
    df3['geometry'] = df3['geometry'].apply(wkb_hexer)
    df3 = df3.merge(gdf_home_job[['cell_zid','geometry']].rename(columns={'geometry':'geometry2'}),on = 'cell_zid',how = 'left')
    df3['geometry2'] = df3['geometry2'].apply(wkb_hexer)
    engine = create_engine(f'postgresql://{login}:{password}@{s}:25432/postgis')
    c = engine.connect()
    conn = c.connection
    df3.to_sql('all_data_by_zids', engine, method=psql_insert_copy)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='desc')
    parser.add_argument('-l', '--login', default='1')
    parser.add_argument('-p', '--password', default='2')
    parser.add_argument('-s', '--serv', default='3')
    args = parser.parse_args()
    run(args)
