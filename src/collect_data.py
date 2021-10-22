import requests
from bs4 import BeautifulSoup
import json
import pandas as pd

from tqdm import tqdm
from utils import flatten_json

"""
данный файл собирает геоданные по москве с тугиса по апи ключу
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
    key = 'demo'
    rubric_list = get_rubric_list(key)
    print(len(rubric_list))

    # пример
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
    l = []
    for key, value in dict_rubrics.items():
        df_ = dict_rubrics[key]
        df_['rubric'] = key.replace('/', '').lower()
        l.append(df_)
    df_full = pd.concat(l, 0)
    df_full.to_csv('data/processed_sample.csv', sep=';', index=None)
