import plotly.graph_objs as go
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from get_data import get_administrative_area_polygon, get_points, get_administrative_area_center, get_optimization_result, get_total_population,get_population_for_polygon
from config import mapbox_token


# датафрейм с границами округов
df_adm_layers = get_administrative_area_polygon()

# датафрейм с населением по округам
df_total_population = get_total_population()

# инфраструктура
dict_objects = {
    "Детские сады": get_points("Детские сады"),
    "МФЦ": get_points("МФЦ"),
    "Школы": get_points("Школы"),
}

dict_icons = {
    "МФЦ": 'town-hall',
    "Школы": 'library',
    "Детские сады": 'playground',
}


def get_map_base_layout():
    """
    Создание подложки карты
    """
    map_layout = dict(
        autosize=True,
        height=900,
        margin=dict(l=0, r=0, b=0, t=0),
        hovermode="closest",
        legend=dict(font=dict(size=14), orientation='h'),
        mapbox=dict(accesstoken=mapbox_token,
                    style="mapbox://styles/evgeniigavrilin/ckqt8rwj44po218mk2movs1ij", zoom=11)
    )
    return map_layout


def _select_infrastructure_data(current_adm_layer, df):
    """
    Агрегирование данных на административные границы

    :param current_adm_layer: текущий административный округ
    :param df: датафрейм с данными по административным округам
    """
    if current_adm_layer == 'Все':
        df_type = df
    elif current_adm_layer == 'Новая Москва':
        list_okrug = ['Троицкий административный округ','Новомосковский административный округ']
        df_type = df[df['okrug_name'].isin(list_okrug)]
    elif current_adm_layer == 'Старая Москва':
        list_okrug = ['Троицкий административный округ','Новомосковский административный округ', 'Все']
        df_type = df[~df['okrug_name'].isin(list_okrug)]
    else:        
        df_type = df[df['okrug_name'] == current_adm_layer]
    return df_type


def get_map_figure(type_, current_adm_layer, run_optinization):
    """
    Создание скатерплота с данными инфраструктуры

    :param type_: текущий тип инфраструктуры
    :param current_adm_layer: текущий административный округ
    :param run_optinization: запуск оптимизации с отрисовкой результата
    """
    analytics_data = {}
    traces = []
    
    
    
    map_layout = get_map_base_layout()
    df_objects, geo_json_infra = dict_objects.get(type_)
    
    if run_optinization == True:
        df_optimization, geo_json_opt, center_coord = get_optimization_result()
        
        traces.append(go.Choroplethmapbox(z=df_optimization['customers_cnt_home'],
                                          locations=df_optimization['index'],
                                          below=True,
                                          geojson=geo_json_opt,
                                          showscale=False,
                                        #   hoverinfo='test',
                                        #   name = 'Население',
                                          marker_line_width=0.1, marker_opacity=0.7))  
        analytics_data['optimization'] = df_optimization['customers_cnt_home'].sum()                                                                         
    else:
        center_coord = get_administrative_area_center(current_adm_layer)  
    
    # рисуем подложку с цветами по количеству проживающего населения
    geojson,gdf = get_population_for_polygon()
    traces.append(go.Choroplethmapbox(z=gdf['customers_cnt_home'],
                            locations = gdf.index, 
                            colorscale = 'ylgn',
                            colorbar = dict(thickness=20, ticklen=3),
                            below=-1,
                            geojson = geojson,
                            hoverinfo='z',
                            name = 'Население',        
                            marker_line_width=0, marker_opacity=0.3))
    

    # рисуем изохроны, которые относятся к выбранным инфраструктурам
    df_objects_type = _select_infrastructure_data(current_adm_layer, df_objects)
    df_population = _select_infrastructure_data(current_adm_layer, df_total_population)
    analytics_data['current_infrastructure'] = df_objects_type['customers_cnt_home'].sum()
    analytics_data['total_population'] = df_population['customers_cnt_home'].sum()    

    traces.append(go.Choroplethmapbox(z=df_objects_type['customers_cnt_home'],
                                          locations=df_objects_type['index'],
                                          below=True,
                                          geojson=geo_json_infra,
                                          showscale=False,
                                          name = 'Население',
                                          marker_line_width=0.1, marker_opacity=0.7))

    # рисуем выбранную инфраструктуру в выбранном районе
    traces.append(go.Scattermapbox(lat=df_objects_type.point_lat,
                                   lon=df_objects_type.point_lon,
                                   mode='markers',
                                   marker=dict(
                                       autocolorscale=False,
                                       size=16,
                                       symbol=dict_icons[type_]
                                   ),
                                   name=type_,
                                   text=df_objects['name'] + '\n' + df_objects['address_name']))


    figure = go.Figure(data=traces,layout=map_layout)  
    return figure, center_coord, analytics_data


def create_layers(current_adm_layer):
    """
    Создание подложки с административными районами

    :param current_adm_layer: текущий административный округ (выделяется красным)
    """
    for feature in df_adm_layers['features']:
        feature['properties']['line-color'] = "red" if feature['properties']['okrug_name'] == current_adm_layer else "black"
        feature['properties']['line-width'] = 1.5 if feature['properties']['okrug_name'] == current_adm_layer else 0.1
    layers = [dict(sourcetype='geojson',
                   source=feature['geometry'],
                   type='line',
                   below='traces',
                   line=dict(width=feature['properties']['line-width']),
                   color=feature['properties']['line-color'],
                   ) for feature in df_adm_layers['features']]
    return layers


def update_map_data(current_adm_layer, current_infra_name, run_optinization=False, run_human_example=False, zoom=9):
    """
    Обновление данных карты: подложки с арминистративными границами и текущими инфраструктурными объектами

    :param current_adm_layer: текущий административный округ
    :param current_infra_name: текущая инфраструктура
    :param run_optinization: запуск оптимизации с отрисовкой результата
    :param run_human_example: отрисовка результата по коодинате, которую ввёл пользователь
    :param zoom: уровень масштабирования карты
    """

    figure, center_coord, analytics_data = get_map_figure(current_infra_name, current_adm_layer, run_optinization)
    layers = create_layers(current_adm_layer)
    figure['layout']['mapbox']['layers'] = layers
    figure['layout']['mapbox']['center'] = dict(
        lat=center_coord.y, lon=center_coord.x)
    figure['layout']['mapbox']['zoom'] = zoom
    print(analytics_data)
    return figure, analytics_data
