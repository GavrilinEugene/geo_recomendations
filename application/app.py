import dash
from dash.dependencies import Input, Output, State
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from layout import get_layout
from map_layout import update_map_data
from get_data import administrative_list, infrastructure_list


app = dash.Dash(__name__)
app.title = 'geoRecomendations'
server = app.server

app.layout = get_layout()


@app.callback(Output('mouse_hidden_button', 'children'), Input('listener', 'data'))
def update_graph(mouseData):
    print('here')
    print(mouseData)


@app.callback(Output('city_map', 'figure'),
              [Input('okrug_name_selector', 'value'),
               Input('infrastructure_name_selector', 'value'),
               Input('generate_button', 'n_clicks'),
               Input('mouse_hidden_button', 'n_clicks')], 
              [State('listener', 'data'), State('city_map', 'relayoutData'), State('infrastructure_n_selector', 'value')]
)
def update_output(okrug_name_index, infra_name_index, geterator_button_click, mouse_hidden_button_click, mouse_data, relayoutData,infra_n_value):
    """

    """

    trigger = dash.callback_context.triggered[0]
    run_optinization = False
    if trigger is not None and trigger['prop_id'].split('.')[0] == 'generate_button':
        run_optinization = True

    if trigger is not None and trigger['prop_id'].split('.')[0] == 'mouse_hidden_button':
        print(relayoutData)       

    new_adm_layer = administrative_list[okrug_name_index]['label']
    new_infra_name = infrastructure_list[infra_name_index]['label']
    figure = update_map_data(new_adm_layer, new_infra_name, run_optinization, 12)
    return figure


if __name__ == '__main__':
    app.run_server(host='localhost', port=5055)
