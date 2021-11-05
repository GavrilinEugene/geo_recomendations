import pandas as pd
import geopandas as gpd
import os
from sqlalchemy import create_engine
from utils import wkb_hexer,psql_insert_copy,drop_table
import argparse


def create_table_all_data_by_zids(engine):
    #население
    df_home_job = pd.read_csv(os.path.join(os.getcwd(),f"data/raw/01_CLocation_July.csv"))
    df_shape = gpd.read_file(os.path.join(os.getcwd(),f"data/raw/fishnet2021/fishnet2021.shp"))
    df_home_job.rename(columns={'zid': 'cell_zid'}, inplace=True)
    df_home_job = pd.merge(df_home_job, df_shape, on = ['cell_zid'])
    gdf_home_job = gpd.GeoDataFrame(df_home_job)
    gdf_home_job.head()

    #адм районы
    df_adm = gpd.read_file(os.path.join(os.getcwd(), f"data/raw/admzones2021/admzones2021.shp"))
    df_adm = df_adm[['adm_name', 'okrug_name', 'sub_ter', 'geometry']]
    df_adm = gpd.GeoDataFrame(df_adm)
    df3 = gpd.sjoin(df_adm, gdf_home_job, how='inner', op='intersects')
    df3 = df3[['cell_zid', 'adm_name', 'okrug_name', 'sub_ter', 'geometry','customers_cnt_home',
               'customers_cnt_job','customers_cnt_day','customers_cnt_move']]
    df3 = df3.drop_duplicates(subset = ['cell_zid'],keep = 'last')
    df3['geometry'] = df3['geometry'].apply(wkb_hexer)
    df3 = df3.merge(gdf_home_job[['cell_zid','geometry']].rename(columns={'geometry':'geometry2'}),on = 'cell_zid',how = 'left')
    df3['geometry2'] = df3['geometry2'].apply(wkb_hexer)

    drop_table(engine=engine, space='public', table_name='t3')
    df3.to_sql('_all_data_by_zids', engine, method=psql_insert_copy)


def run (args):
    print('args=',args)
    login = args.login
    password = args.password
    s = args.serv
    port = args.port

    df_walking = pd.read_csv((os.path.join(os.getcwd(), f"data/processed/izochrones_walking.csv")), sep =';')
    print(df_walking.shape)
    df_driving= pd.read_csv((os.path.join(os.getcwd(), f"data/processed/izochrones_driving.csv")), sep =';')
    print(df_driving.shape)


    engine = create_engine(f'postgresql://{login}:{password}@{s}:{port}/postgis')

    c = engine.connect()
    conn = c.connection
    drop_table(engine=engine,space = 'public', table_name = '_izochrones_by_walk')
    df_walking.to_sql('_izochrones_by_walk', engine, method=psql_insert_copy)

    drop_table(engine=engine,space = 'public', table_name = '_izochrones_by_drive')
    df_driving.to_sql('_izochrones_by_drive', engine, method=psql_insert_copy)

    #создаем all_data_by_zid
    create_table_all_data_by_zids(engine = engine)


    #создаем обобщенную таблицу

    drop_table(engine=engine, space='public', table_name='t4')
    sql = """
    create table _all_data_by_zids_iso as
    select 
    all_data.*,
    iw.walking_10min,
    iw.walking_15min,
    iw.walking_20min,
    iw.walking_5min,
    id.driving_10min,
    id.driving_15min,
    id.driving_20min,
    id.driving_5min
    from _all_data_by_zids all_data  
    left join
    _izochrones_by_walk iw  -- walking_10min	walking_15min	walking_20min	walking_5min
    on all_data.cell_zid = iw.zid  
    left join
    _izochrones_by_drive id  -- 	driving_10min	driving_15min	driving_20min	driving_5min
    on all_data.cell_zid = id.zid
    """
    c.execute(sql)



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='desc')
    parser.add_argument('-l', '--login', default='1')
    parser.add_argument('-p', '--password', default='2')
    parser.add_argument('-s', '--serv', default='3')
    parser.add_argument('-port', '--port', default='25432')
    args = parser.parse_args()
    run(args)



