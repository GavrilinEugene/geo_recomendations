import pandas as pd
import geopandas as gpd
import requests
import os
import geojson
from tqdm import tqdm
from shapely.geometry import Polygon
from utils import save_pickle, load_pickle

#mapbox key for isochrones
token = 'pk.eyJ1IjoiZXZnZW5paWdhdnJpbGluIiwiYSI6ImNrMG50N3ptdjAzNW8zbm8wZzVmaXpzcWoifQ.LMSJohnSoBN-6YlAgKPO0w'

def get_isochrone(coord, kind = 'driving', minutes = '5,10,15,20'):
    """
    
    """
    request = f'https://api.mapbox.com/isochrone/v1/mapbox/{kind}/{coord.x},{coord.y}?contours_minutes={minutes}&polygons=true&access_token={token}'
    r = requests.get(request)  
    return geojson.loads(r.content)

def run(sample = 20):

    # собираем сетку данных, определяем центры квадратов
    df_home_job = pd.read_csv("data/raw/01_CLocation_July.csv")
    df_shape = gpd.read_file("data/raw/fishnet2021/fishnet2021.shp")
    df_home_job.rename(columns={'zid': 'cell_zid'}, inplace=True)

    df_home_job = pd.merge(df_home_job, df_shape, on = ['cell_zid'])
    df_home_job['center'] = df_home_job['geometry'].map(lambda poly: poly.centroid)

    isochrone_file_path = f"data/precessed/isochrones_walk_{sample}.pkl"
    if os.path.exists(isochrone_file_path):
        isochrones_walk = {}
        # isochrones_walk = load_pickle(isochrone_file_path)
    else:
        print("empty")
        isochrones_walk = {}

    # выгружаем изохроны из мапбокса
    if sample != -1:
        df_home_job = df_home_job.head(20)
    for idx, row in tqdm(df_home_job.iterrows(), total=len(df_home_job)):
        if row['cell_zid'] in isochrones_walk.keys():
            if 'features' in isochrones_walk[row['cell_zid']].keys():
                continue
        isochrones_walk[row['cell_zid']] = get_isochrone(row['center'], kind = 'walking')
        if idx %100 == 0:
            save_pickle(isochrones_walk, isochrone_file_path)
    save_pickle(isochrones_walk, isochrone_file_path)

    l_isochrones = []
    for zid in isochrones_walk.keys():
        l_isochrones.append((zid, 'pol_5min', Polygon(isochrones_walk[zid]['features'][3]['geometry']['coordinates'][0])))
        l_isochrones.append((zid,'pol_10min',Polygon(isochrones_walk[zid]['features'][2]['geometry']['coordinates'][0])))
        l_isochrones.append((zid,'pol_15min',Polygon(isochrones_walk[zid]['features'][1]['geometry']['coordinates'][0])))
        l_isochrones.append((zid,'pol_20min',Polygon(isochrones_walk[zid]['features'][0]['geometry']['coordinates'][0])))

    df = pd.DataFrame(l_isochrones, columns = ['zid', 'kind', 'geometry'])
    df['geometry'] = df['geometry'].astype(str)

    df_home_job.rename(columns = {'cell_zid': 'zid'}, inplace=True)
    df.rename(columns = {'geometry': "isochrone"}, inplace=True)
    df = pd.merge(df_home_job, df, how = 'left', on = 'zid')
    df = pd.pivot_table(df, index = 'zid', columns = 'kind', values = 'isochrone', aggfunc=max).reset_index()
    df.to_csv("data/precessed/izochrones_2.csv", sep = ';', index = None)


if __name__ == '__main__':
    run()    