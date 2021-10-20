from dash import html, dcc
import mydcc
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from get_data import administrative_list, infrastructure_list
from get_data import default_infra, dafault_okrug_idx
from map_layout import update_map_data


def create_administrative_selector():
    """

    """
    return html.Div([
        html.P(
            'Административный округ:',
        ),
        dcc.Dropdown(
            id='okrug_name_selector',
            options=administrative_list,
            value=dafault_okrug_idx,
            className="dcc_control"
        )
    ],
        className='eight columns',
    )


def create_infrustructure_selector():
    """

    """
    return html.Div([
        html.P(
            'Тип инфраструктуры:',
        ),
        dcc.Dropdown(
            id='infrastructure_name_selector',
            options=infrastructure_list,
            value=0,
            className="dcc_control"
        )
    ],
        className='eight columns',
    )


def get_layout():
    
    return html.Div(
        [
            dcc.Store(id='aggregate_data'),
            # content
            html.Div(
                [
                    # контроллеры и аналитика
                    html.Div(
                        [
                            # controllers
                            html.Div(
                                [
                                    # filter by region
                                    create_administrative_selector(),
                                ],
                                className='row',
                            ),
                            html.Div(
                                [
                                    # filter by infrastructure
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
                                marks={i: i for i in range(1, 11, 1)}
                            ),
                            html.Div(
                                [
                                    html.Button(
                                        'Запустить поиск локаций', id='generate_button', n_clicks=0, className="eight columns"),
                                ],
                                className="row"
                            ),
                        ],
                        className='pretty_container four columns',
                    ),
                    # карта
                    html.Div([
                        mydcc.Listener_mapbox(id="listener", aim='city_map'),
                        dcc.Graph(id='city_map', figure=update_map_data(
                            administrative_list[dafault_okrug_idx]['label'], default_infra))
                    ],
                        className='pretty_container nine columns'
                    ),
                ],
                className='row'
            ),

            # hidden button with hotkey to be able handle click events on the map
            html.Div(
                [
                    html.Button('selector_button', id='mouse_hidden_button',
                                accessKey='i', n_clicks=0, hidden='HIDDEN')
                ], style={'display': 'none'}
            ),
        ],
        id="mainContainer",
        style={
            "display": "flex",
            "flex-direction": "column"
        }
    )
