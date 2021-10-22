import pandas as pd
import geopandas as gpd
from shapely.ops import cascaded_union
import csv
from io import StringIO
from sqlalchemy import create_engine
import argparse

"""
данный файл собирает создаёт пару таблиц с административным делением и численностью населения в postgress
"""


def psql_insert_copy(table, conn, keys, data_iter):
    # gets a DBAPI connection that can provide a cursor
    dbapi_conn = conn.connection
    with dbapi_conn.cursor() as cur:
        s_buf = StringIO()
        writer = csv.writer(s_buf)
        writer.writerows(data_iter)
        s_buf.seek(0)

        columns = ', '.join('"{}"'.format(k) for k in keys)
        if table.schema:
            table_name = '{}.{}'.format(table.schema, table.name)
        else:
            table_name = table.name

        sql = 'COPY {} ({}) FROM STDIN WITH CSV'.format(
            table_name, columns)
        cur.copy_expert(sql=sql, file=s_buf)

def wkb_hexer(line):
    """string -> postgis geometry hex"""
    return line.wkb_hex


def drop_table(engine, table_name):
    try:
        c = engine.connect()
        # conn = c.connection
        c.execute(f"drop table {table_name}")
    except:
        pass

def run(args):

    print(args)
    login = args.login
    password = args.password
    s = args.server

    # регионы
    df_adm = gpd.read_file("data/raw/admzones2021/admzones2021.shp")
    df_adm = df_adm[['adm_name', 'okrug_name', 'sub_ter', 'geometry']]
    df_adm = gpd.GeoDataFrame(df_adm)

    # население
    df_home_job = pd.read_csv("data/raw/01_CLocation_July.csv")
    df_shape = gpd.read_file("data/raw/fishnet2021/fishnet2021.shp")
    df_home_job.rename(columns={'zid': 'cell_zid'}, inplace=True)
    df_home_job = pd.merge(df_home_job, df_shape, on = ['cell_zid'])
    gdf_home_job = gpd.GeoDataFrame(df_home_job)

    #
    df3 = gpd.sjoin(df_adm, gdf_home_job, how='inner', op='intersects')
    df3 = df3[['cell_zid', 'adm_name', 'okrug_name', 'sub_ter', 'geometry']]
    df3 = df3.drop_duplicates(subset = ['cell_zid'])
    df4 = df3.drop_duplicates(subset = ['adm_name'])[['adm_name', 'okrug_name', 'sub_ter', 'geometry']]
    df4 = df4[df4['sub_ter']!='Московская область']
    df_all_reg = df4.copy()
    df4['geometry'] = df4['geometry'].apply(wkb_hexer)

    engine = create_engine(f'postgresql://{login}:{password}@{s}:25432/postgis')
    drop_table(engine, 'public.adm_regions_with_geometry')
    df4.to_sql('adm_regions_with_geometry', engine, method=psql_insert_copy)

    df_all_reg = df_all_reg.groupby(['okrug_name'])['geometry'].apply(lambda x: cascaded_union(x)).reset_index()

    combined = cascaded_union(df_all_reg['geometry'])
    combined_new = cascaded_union(df_all_reg[df_all_reg['okrug_name'].isin(['Троицкий административный округ',
                                                          'Новомосковский административный округ'])]['geometry'])
    combined_old = cascaded_union(df_all_reg[~df_all_reg['okrug_name'].isin(['Троицкий административный округ',
                                                            'Новомосковский административный округ', 'Все'])]['geometry'])

    df_all_reg.loc[df_all_reg.index.max()+1] = ['Все', combined]
    df_all_reg.loc[df_all_reg.index.max()+1] = ['Новая Москва', combined_new]
    df_all_reg.loc[df_all_reg.index.max()+1] = ['Старая Москва', combined_old]
    combined_old['index'] = [3,4,5,6,7,8,9,10,11,12,13,14,0,1,2]
    combined_old = combined_old.sort_values(by = ['index'])

    drop_table(engine, 'public.okrug_name_with_geometry')
    df_all_reg['geometry'] = df_all_reg['geometry'].apply(wkb_hexer)
    df_all_reg.to_sql('okrug_name_with_geometry', engine, method=psql_insert_copy)

if __name__ == '__main__':
    

    parser = argparse.ArgumentParser(description='desc')
    parser.add_argument('-l', '--login', default='1')
    parser.add_argument('-p', '--password', default='2')
    parser.add_argument('-s', '--serv', default='3')
    args = parser.parse_args()
    run(args)    