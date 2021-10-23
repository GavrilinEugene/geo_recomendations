import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import dash
from dash.dependencies import Input, Output, State

# внутренние импорты
from layout import get_layout
from map_layout import update_map_data
from analytics_layout import update_analytics_figure
from get_data import administrative_list, infrastructure_list


app = dash.Dash(__name__)
app.title = 'geoRecomendations'
server = app.server

app.layout = get_layout()


@app.callback([Output('city_map', 'figure'), Output('analytics_graph', 'figure')],
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

    trigger = dash.callback_context.triggered[0]
    run_optinization = False
    if trigger is not None and trigger['prop_id'].split('.')[0] == 'generate_button':
        run_optinization = True

    new_adm_layer = administrative_list[okrug_name_index]['label']

    new_infra_name = infrastructure_list[infra_name_index]['label']
    figure, analytics_data = update_map_data(new_adm_layer, new_infra_name, infra_n_value, run_optinization)

    analytics_figure = update_analytics_figure(analytics_data)
    return figure, analytics_figure


if __name__ == '__main__':
    app.run_server(host='localhost', port=5055)
