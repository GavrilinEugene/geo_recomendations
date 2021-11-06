import get_data as gd
from config import mapbox_token, mapbox_style
import plotly.graph_objs as go
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


# датафрейм с границами округов
df_adm_layers = gd.get_administrative_area_polygon()

# датафрейм с населением по округам
df_total_population = gd.get_total_population()

# подложка с населением
geojson, gdf_population = gd.get_population_for_polygon()

# слой с плохими полигонами
# gdf_bad_polygons, geojson_bad_poly = gd.get_bad_polygons()

# инфраструктура
dict_objects = {
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
                    style=mapbox_style, zoom=11)
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
        list_okrug = ['Троицкий административный округ',
                      'Новомосковский административный округ']
        df_type = df[df['okrug_name'].isin(list_okrug)]
    elif current_adm_layer == 'Старая Москва':
        list_okrug = ['Троицкий административный округ',
                      'Новомосковский административный округ', 'Все']
        df_type = df[~df['okrug_name'].isin(list_okrug)]
    else:
        df_type = df[df['okrug_name'] == current_adm_layer]
    return df_type


def _add_optimization_traces(traces, df_opt, geo_json_opt, infra_type):
    """
    Добавление слоёв на карту, которые связаны с оптимизацией: новые локации и изохроны
    """
    traces.append(go.Choroplethmapbox(z=df_opt['index'],
                                      locations=df_opt['index'],
                                      below=True,
                                      geojson=geo_json_opt,
                                      showscale=False,
                                      showlegend=True,
                                      legendgroup = 'output',
                                      legendgrouptitle_text = f'План для открытия',
                                      name="Области покрытия (изохроны)",
                                      colorscale=[[0, 'rgba(240,192,192,.5)'], [
                                          1, 'rgba(240,192,192,.5)']],
                                      marker=dict(
                                          line=dict(width=2.5, color='rgb(0, 51, 0)'), opacity=0.7),
                                      ))

    traces.append(go.Scattermapbox(lat=df_opt.point_lat,
                                   lon=df_opt.point_lon,
                                   below=-1,
                                   mode='markers',
                                   legendgroup = 'output',
                                   legendgrouptitle_text = f'План для открытия',
                                   marker=dict(
                                       autocolorscale=False,
                                       size=16,
                                       symbol='circle',
                                       color='rgb(244, 44, 44)'
                                   ),
                                   name=f"Новые {infra_type}",
                                   text=df_opt['index']
                                   ))


def get_map_figure(infra_type, current_adm_layer, run_optinization, infra_n_value):
    """
    Создание скатерплота с данными инфраструктуры

    :param infra_type: текущий тип инфраструктуры
    :param current_adm_layer: текущий административный округ
    :param run_optinization: запуск оптимизации с отрисовкой результата
    :param infra_n_value: числно новых объектов инфраструктуры
    """

    analytics_data = {}
    traces = []

    map_layout = get_map_base_layout()
    if dict_objects.get(infra_type, 0) == 0:
        dict_objects[infra_type] = gd.get_points(infra_type)
    df_objects, df_simple_isochrone, geo_json_union = dict_objects[infra_type]

    
    center_coord = gd.get_administrative_area_center(current_adm_layer)

    # обрезаем объекты по типу административного слоя
    df_objects_type = _select_infrastructure_data(
        current_adm_layer, df_objects)
    df_population = _select_infrastructure_data(
        current_adm_layer, df_total_population)
    df_simple_isochrone = _select_infrastructure_data(
        current_adm_layer, df_simple_isochrone)
    gdf_population_type = _select_infrastructure_data(
        current_adm_layer, gdf_population)

    # gdf_bad_polygons_layer =  _select_infrastructure_data(current_adm_layer, gdf_bad_polygons)

    # собираем текущую статистику по покрытию инфраструктурой выбранного района
    df_unique_isochrones = df_objects_type.drop_duplicates(subset=['zid'])
    analytics_data['current_infrastructure'] = df_unique_isochrones['customers_cnt_home'].sum()
    analytics_data['total_population'] = df_population['customers_cnt_home'].sum()

    # рисуем подложку с цветами по количеству проживающего населения
    traces.append(go.Choroplethmapbox(z=gdf_population_type['customers_cnt_home'],
                                      locations=gdf_population_type.index,
                                      colorscale='ylgn',
                                      below="water",
                                      geojson=geojson,
                                      marker=dict(line=dict(width=0)),
                                      showscale=False,
                                      text='<br>население в квадрате: ' +
                                            round(gdf_population_type['customers_cnt_home']).astype(str),
                                      hoverinfo = "text",
                                      name='Численность населения',
                                      showlegend=True,
                                      marker_opacity=0.7))

    # рисуем подложку с плохими полигонами
    # traces.append(go.Choroplethmapbox(z=gdf_bad_polygons_layer['bad_polygon'],
    #                                   locations=gdf_bad_polygons_layer.index,
    #                                   colorscale='RdYlGn_r',
    #                                   below="water",
    #                                   geojson=geojson_bad_poly,
    #                                   marker=dict(line=dict(width=0)),
    #                                   showscale=False,
    #                                 #   text='<br>население в квадрате: ' +
    #                                 #         round(gdf_population_type['customers_cnt_home']).astype(str),
    #                                 #   hoverinfo = "text",
    #                                   name='Плохие полигоны',
    #                                   showlegend=True,
    #                                   marker_opacity=0.7))                                      

    # изохрона под инфраструктуру
    traces.append(go.Choroplethmapbox(z=df_simple_isochrone['index'],
                                      locations=df_simple_isochrone['index'],
                                      below=True,
                                      geojson=geo_json_union,
                                      showscale=False,
                                      legendgroup = 'input',
                                      legendgrouptitle_text = f'Существующая инфраструктура',
                                      colorscale=[[0, 'rgba(231,231,231,.6)'], [
                                          1, 'rgba(231,231,231,.6)']],
                                      marker=dict(
                                          line=dict(width=1.6, color='dimgray'), opacity=0.9),
                                      name="Области покрытия (изохроны)",
                                      showlegend=True,
                                      hoverinfo='skip'
                                      ))

    # инфраструктура в выбранном районе
    traces.append(go.Scattermapbox(lat=df_objects_type.point_lat,
                                   lon=df_objects_type.point_lon,
                                   mode='markers',
                                   marker=dict(
                                       size=10,
                                       symbol='circle',
                                       color='dimgray'
                                   ),
                                   legendgroup = 'input',
                                   legendgrouptitle_text = f'Существующая инфраструктура',
                                   name=f"Текущие {infra_type}",
                                   text=df_objects_type['name'] + '<br>' +
                                   df_objects_type['address_name'] + '<br>население в пешей доступности:' +
                                   round(df_objects_type['customers_cnt_home']).astype(str)))

    if run_optinization == True:
        df_opt, geo_json_opt, _, df_opt_analytics = \
            gd.get_optimization_result(
                current_adm_layer, infra_n_value, infra_type)

        _add_optimization_traces(traces, df_opt, geo_json_opt, infra_type)

        analytics_data.update(
            dict(zip(df_opt_analytics['zids_len'], df_opt_analytics['added_coverage'])))                                   

    figure = go.Figure(data=traces, layout=map_layout)
    return figure, center_coord, analytics_data


def create_layers(current_adm_layer):
    """
    Создание подложки с административными районами

    :param current_adm_layer: текущий административный округ (выделяется красным)
    """
    for feature in df_adm_layers['features']:
        feature['properties']['line-color'] = "green" if feature['properties']['okrug_name'] == current_adm_layer else "black"
        feature['properties']['line-width'] = 2.5 if feature['properties']['okrug_name'] == current_adm_layer else 0.1
    layers = [dict(sourcetype='geojson',
                   source=feature['geometry'],
                   type='line',
                   below=-1,
                   line=dict(width=feature['properties']['line-width']),
                   color=feature['properties']['line-color'],
                   ) for feature in df_adm_layers['features']]

    return layers


def update_map_data(current_adm_layer, current_infra_name, infra_n_value, run_optinization=False, run_human_example=False, zoom=9):
    """
    Обновление данных карты: подложки с арминистративными границами и текущими инфраструктурными объектами

    :param current_adm_layer: текущий административный округ
    :param current_infra_name: текущая инфраструктура
    :param infra_n_value: текущее число новых инфраструктурных объектов
    :param run_optinization: запуск оптимизации с отрисовкой результата
    :param run_human_example: отрисовка результата по коодинате, которую ввёл пользователь
    :param zoom: уровень масштабирования карты
    """

    figure, center_coord, analytics_data = get_map_figure(
        current_infra_name, current_adm_layer, run_optinization, infra_n_value)
    layers = create_layers(current_adm_layer)
    figure['layout']['mapbox']['layers'] = layers
    figure['layout']['legend'] = dict(
                title=dict(text="Слои карты"),
                y=0.04,
                x=0.01,
                bgcolor = "white"
            )
    figure['layout']['mapbox']['center'] = dict(
        lat=center_coord.y, lon=center_coord.x)
    figure['layout']['mapbox']['zoom'] = zoom
    return figure, analytics_data
