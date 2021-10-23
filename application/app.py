from config import loading_style
import get_data as gd
from analytics_layout import update_analytics_figure
from map_layout import update_map_data
from dash.dependencies import Input, Output, State
from dash import html, dcc
import dash
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def create_administrative_selector():
    """
    Создание выпадающего списка для выбора административного региона
    """
    return html.Div([
        html.P(
            'Административный округ:',
        ),
        dcc.Dropdown(
            id='okrug_name_selector',
            options=gd.administrative_list,
            value=gd.dafault_okrug_idx,
            className="dcc_control"
        )
    ],
        className='eight columns',
    )


def create_infrustructure_selector():
    """
    Создание выпадающего списка для выбора типа инфраструктуры
    """
    return html.Div([
        html.P(
            'Тип инфраструктуры:',
        ),
        dcc.Dropdown(
            id='infrastructure_name_selector',
            options=gd.infrastructure_list,
            value=0,
            className="dcc_control"
        )
    ],
        className='eight columns',
    )


# иницаилизация
geo_map_fig, first_analytics = update_map_data(
    gd.administrative_list[gd.dafault_okrug_idx]['label'], gd.default_infra, infra_n_value=gd.default_infra_n_value)
analytics_fig = update_analytics_figure(first_analytics)


app = dash.Dash(__name__)
app.title = 'geoRecomendations'
server = app.server

app.layout = html.Div(
    [
        dcc.Store(id='aggregate_data'),
        # весь контент
        html.Div(
            [
                # контроллеры и аналитика
                html.Div(
                    [
                        html.Div(
                            [
                                # фильтр по региону
                                create_administrative_selector(),
                            ],
                            className='row',
                        ),
                        html.Div(
                            [
                                # фильтр по инфраструктуре
                                create_infrustructure_selector(),
                            ],
                            className='row',
                        ),
                        html.Div(
                            [
                                html.P('Новых объектов инфраструктуры:')
                            ],
                            className="row"
                        ),
                        dcc.Slider(
                            id='infrastructure_n_selector',
                            min=1,
                            max=10,
                            value=1,
                            marks={i: i for i in range(1, 11, 1)},
                            className="dcc_control"
                        ),
                        html.Div(
                            [
                                html.Button(
                                    'Запустить поиск локаций', id='generate_button', n_clicks=0, className="eight columns"),
                            ],
                            className="row"
                        ),
                        html.Div(
                            [
                                dcc.Graph(id='analytics_graph',
                                          figure=analytics_fig)
                            ],
                            className="pretty_container"
                        ),
                    ],
                    className='pretty_container four columns',
                ),
                # карта
                html.Div([
                    html.Div([dcc.Graph(id='city_map', figure=geo_map_fig, style={'flex-grow': '1'}),
                              dcc.Loading(
                        id='loading', parent_style=loading_style)
                    ], style={'position': 'relative', 'display': 'flex','justify-content': 'center'})
                ],
                    className='pretty_container nine columns'
                ),
            ],
            className='row'
        )
    ],
    id="mainContainer",
    style={
        "display": "flex",
        "flex-direction": "column"
    }
)


@app.callback([Output('city_map', 'figure'),
               Output('analytics_graph', 'figure'),
               Output('loading', 'parent_style')],
              [Input('okrug_name_selector', 'value'),
               Input('infrastructure_name_selector', 'value'),
               Input('generate_button', 'n_clicks')],
              State('infrastructure_n_selector', 'value')
              )
def update_output(okrug_name_index, infra_name_index, geterator_button_click, infra_n_value):
    """
    Callback обновления карты и блока статистики

    :param okrug_name_index: текущий индекс выбранного округа города
    :param infra_name_index: текущий индекс выбранной инфраструктуры
    :param geterator_button_click: состояние нажатия кнопки генерации
    :param infra_n_value: текущее число запрашиваемых новых инфраструктурных объектов 
    """

    new_loading_style = loading_style

    trigger = dash.callback_context.triggered[0]
    run_optinization = False
    if trigger is not None and trigger['prop_id'].split('.')[0] == 'generate_button':
        run_optinization = True

    new_adm_layer = gd.administrative_list[okrug_name_index]['label']

    new_infra_name = gd.infrastructure_list[infra_name_index]['label']
    figure, analytics_data = update_map_data(
        new_adm_layer, new_infra_name, infra_n_value, run_optinization)

    analytics_figure = update_analytics_figure(analytics_data)
    return figure, analytics_figure, new_loading_style


if __name__ == '__main__':
    app.run_server(host='localhost', port=5055)
