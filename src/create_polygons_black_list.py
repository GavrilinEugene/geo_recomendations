import argparse
import geopandas as gpd
import psycopg2
from sqlalchemy import create_engine
import glob
import zipfile
import os


def upload_files(file_names, args):
    """
    Загрузка файлов geojson в базу
    """

    login = args.login
    password = args.password
    host = args.serv
    port = args.port

    engine = create_engine(
        f'postgresql://{login}:{password}@{host}:{port}/postgis')
    for file in file_names:
        df = gpd.read_file(file)
        print(file, '   ', df.shape)
        df['geometry_str'] = df['geometry'].astype(str)
        df.drop(['geometry'], axis=1, inplace=True)
        base_name = os.path.basename(file)
        table_name = os.path.splitext(base_name)[0]
        df.to_sql(f'osm_{table_name}', engine,
                  if_exists='replace', index=False)


def create_table_with_bad_polygons(args):
    """
    Создание таблицы с плохими полигонами
    """

    login = args.login
    password = args.password
    host = args.serv
    port = args.port

    conn = psycopg2.connect(
        f"host={host} dbname=postgis port={port} user={login} password={password}")
    with conn.cursor() as cursor:
        sql = """
            DROP TABLE IF EXISTS public.osm_black_polygons;
            WITH aa AS 
            ( 
            select ST_GeomFromText(geometry_str,4326) geometry, 'mfc0_school0_clinic0_kindergarden0' filt from public.osm_aerodrome
            UNION
            select ST_GeomFromText(geometry_str,4326) geometry, 'mfc0_school0_clinic0_kindergarden0' filt from public.osm_allotments
            UNION
            select ST_GeomFromText(geometry_str,4326) geometry, 'mfc0_school0_clinic0_kindergarden0' filt from public.osm_cemetery
            UNION
            select ST_GeomFromText(geometry_str,4326) geometry, 'mfc1_school0_clinic0_kindergarden0' filt from public.osm_commercial
            UNION
            select ST_GeomFromText(geometry_str,4326) geometry, 'mfc0_school0_clinic0_kindergarden0' filt from public.osm_construction
            UNION
            select ST_GeomFromText(geometry_str,4326) geometry, 'mfc0_school0_clinic0_kindergarden0' filt from public.osm_farmyard
            UNION
            select ST_GeomFromText(geometry_str,4326) geometry, 'mfc0_school0_clinic0_kindergarden0' filt from public.osm_forest
            UNION
            select ST_GeomFromText(geometry_str,4326) geometry, 'mfc0_school0_clinic0_kindergarden0' filt from public.osm_greenhouse_horticulture
            UNION
            select ST_GeomFromText(geometry_str,4326) geometry, 'mfc0_school0_clinic0_kindergarden0' filt from public.osm_industrial
            UNION
            select ST_GeomFromText(geometry_str,4326) geometry, 'mfc1_school0_clinic0_kindergarden0' filt from public.osm_mall
            UNION
            select ST_GeomFromText(geometry_str,4326) geometry, 'mfc0_school0_clinic0_kindergarden0' filt from public.osm_military
            UNION
            select ST_GeomFromText(geometry_str,4326) geometry, 'mfc0_school0_clinic0_kindergarden0' filt from public.osm_park
            UNION
            select ST_GeomFromText(geometry_str,4326) geometry, 'mfc0_school0_clinic0_kindergarden0' filt from public.osm_quarry
            UNION
            select ST_GeomFromText(geometry_str,4326) geometry, 'mfc0_school0_clinic0_kindergarden0' filt from public.osm_railway
            UNION
            select ST_GeomFromText(geometry_str,4326) geometry, 'mfc1_school0_clinic0_kindergarden0' filt from public.osm_retail
            UNION
            select ST_GeomFromText(geometry_str,4326) geometry, 'mfc0_school0_clinic0_kindergarden0' filt from public.osm_water
            UNION
            select ST_GeomFromText(geometry_str,4326) geometry, 'mfc0_school0_clinic0_kindergarden0' filt from public.osm_water2
            UNION
            select ST_GeomFromText(geometry_str,4326) geometry, 'mfc0_school0_clinic0_kindergarden0' filt from public.osm_wood
            )
            SELECT * INTO public.osm_black_polygons FROM aa
            """
        cursor.execute(sql)
        conn.commit()

    with conn.cursor() as cursor:
        sql = """
            DROP TABLE IF EXISTS public.bad_zids;
            WITH not_in_izochrone AS 
            ( 
                SELECT zid, ST_SetSRID(center, 4326) as center, ST_SetSRID(geometry_base, 4326) as geometry_base,
                        'mfc0_school0_clinic0_kindergarden0' filt
                FROM public.izochrones_by_walk a
                WHERE NOT ST_Contains(ST_SetSRID(pol_15min, 4326), ST_SetSRID(center, 4326))
            )
            , in_bad_zones AS 
            (
                SELECT zid, ST_SetSRID(center, 4326) as center, ST_SetSRID(geometry_base, 4326) as geometry_base, filt
                FROM public.izochrones_by_walk a
                LEFT JOIN public.osm_black_polygons b
                    ON ST_Contains(geometry, ST_SetSRID(center, 4326))
                WHERE b.geometry IS NOT NULL
            )
            SELECT * 
            INTO public.bad_zids
            FROM 
                (SELECT * FROM not_in_izochrone
                UNION 
                SELECT * FROM in_bad_zones) T
            """
        cursor.execute(sql)
        conn.commit()

    conn.close()


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='desc')
    parser.add_argument('-l', '--login', default='1')
    parser.add_argument('-p', '--password', default='2')
    parser.add_argument('-s', '--serv', default='3')
    parser.add_argument('-port', '--port', default='25432')
    parser.add_argument('-key', '--api_key', default='demo')
    args = parser.parse_args()

    data_dir = "data/raw/bad_polygons"

    with zipfile.ZipFile(os.path.join(os.getcwd(), f"{data_dir}.zip"), 'r') as zip_ref:
        zip_ref.extractall(os.path.join(os.getcwd(), f"{data_dir}/"))

        files = glob.glob(os.path.join(os.getcwd(), f"{data_dir}/*.geojson"))

        upload_files(files, args)
        create_table_with_bad_polygons(args)
        print("Список с плохими полигонами загружен в БД")
