import os
import requests
from bs4 import BeautifulSoup
import json
import pandas as pd
from sqlalchemy import create_engine
import argparse

from tqdm import tqdm
from utils import flatten_json, save_table_no_geom

"""
данный файл собирает геоданные по москве с 2gis.ru по апи ключу
Реализован метод получения имён рубрик и метод запроса данных по этим рубрикам

Выгруженные данные хранятся в папке /data/processed.csv.zip
"""


def get_rubric_list(key):
    """
        получение списка рубрик
    """
    r = requests.get(
        f"https://catalog.api.2gis.com/2.0/catalog/rubric/list?key={key}&region_id=1&fields=items.rubrics")
    rubric_list = []
    rubrics = json.loads(r.text)
    for idx in range(0, len(rubrics['result']['items'])):
        large_rubric = rubrics['result']['items'][idx]
        for rubric in large_rubric['rubrics']:
            rubric_list.append(rubric['name'])
    return rubric_list


def collect_data(city, rubric, key):
    """
        Сбор данных с географической привязкой по имени города и рубрики
        :param city: город
        :param rubric: рубрика объектов из get_rubric_list
    """
    def _return_with_check(rubric_items):
        if len(rubric_items) > 0:
            return pd.concat(rubric_items, 0)
        return None

    rubric_items = []
    for page in range(1, 250):
        gis_request = f"""https://catalog.api.2gis.com/3.0/items?q={city} {rubric}&page={page}&page_size=50&fields=items.point,items.adm_div&key={key}"""
        r = requests.get(gis_request)
        if r.ok == True:
            soup = BeautifulSoup(r.text, "lxml")
            try:
                content = json.loads(soup.text)
                if content['meta']['code'] == 404:
                    return _return_with_check(rubric_items)

                df = pd.DataFrame([flatten_json(x)
                                  for x in content['result']['items']])
                rubric_items.append(df)
            except Exception as e:
                return _return_with_check(rubric_items)
    return pd.concat(rubric_items, 0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='desc')
    parser.add_argument('-l', '--login', default='1')
    parser.add_argument('-p', '--password', default='2')
    parser.add_argument('-s', '--serv', default='3')
    parser.add_argument('-port', '--port', default='25432')
    parser.add_argument('-key', '--api-key', default ='demo')
    args = parser.parse_args()

    login = args.login
    password = args.password
    host = args.serv
    port = args.port

    key = args.key
    rubric_list = get_rubric_list(key)
    print("Всего рубрик:" , len(rubric_list))

    # пример данных, на которых потом дальше будем работать
    rubric_list = [x for x in rubric_list if 'школ' in str.lower(x)
                or 'мфц' in str.lower(x) 
                or 'поликлиник' in str.lower(x)
                or 'больниц' in str.lower(x)]

    rubric_list = ['платёжные терминалы']                

    # собираем данные по каждой рубрике отдельно
    dict_rubrics = {}
    for rubric in tqdm(rubric_list):
        if rubric in dict_rubrics.keys():
            continue
        df = collect_data('Москва', rubric, key)
        df = df[~df['point_lat'].isna()]
        dict_rubrics[rubric] = df
        rubric = rubric.replace('/', '').lower()

    # собираем массив данных воедино
    list_df_rubrics = []
    for key, value in dict_rubrics.items():
        df_ = dict_rubrics[key]
        df_['rubric'] = key.replace('/', '').lower()
        list_df_rubrics.append(df_)
    df_full = pd.concat(list_df_rubrics, 0)

    # сохраняем данные
    output_file_name = 'gis_fixed_points'
    space = 'public'
    output_file_path = os.path.join(os.getcwd(), 'data/{output_file_name}.csv')
    df_full.to_csv(output_file_path, sep=';', index=None)
    print(f"Данные по инфраструктуре сохранены в {output_file_path}")
    engine = create_engine(f'postgresql://{login}:{password}@{host}:{port}/postgis')
    save_table_no_geom(df_full, engine, space, output_file_name)
    print(f"Данные по инфраструктуре сохранены в бд {space}.{output_file_name}")
