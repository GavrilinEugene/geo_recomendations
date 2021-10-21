import plotly.graph_objs as go
import os
import numpy as np
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def update_analytics_figure(analytics_data, infra_n_value):
    """
    Обновление графика аналитики (отчёт)

    :param analytics_data - аналитические данные от опимизатора
    :param infra_n_value - текущее число новых инфраструктурных объектов
    """

    fig = go.Figure()
    

    total_poputaliton = analytics_data['total_population']
    values = [analytics_data.get('current_infrastructure')]
    for idx in range(1, 11):
        if analytics_data.get(idx, 0) != 0:
            values.append(analytics_data.get(idx) + analytics_data.get('current_infrastructure'))

    widths = np.array([1] * len(values))
            
    fig.add_trace(go.Bar(
        x=np.cumsum(widths)-widths,
        width=widths,
        y=values,
        offset=0,
        textposition="inside",
        textangle=0,
        textfont_color="white",
    ))

    fig.update_xaxes(range=[0,len(values)])
    fig.update_yaxes(range=[0,total_poputaliton])

    labels = ['текущее число']
    for idx in range(1, len(values)):
        labels.append(f"+{idx}")

    fig.update_xaxes(
        tickvals=np.cumsum(widths)-widths/2,
        ticktext= labels
    )

    fig.update_layout(
        title_text="Анализ покрытия инфраструктурой",
        barmode="stack",
        yaxis=dict(
                title='население региона',
                titlefont_size=16,
                tickfont_size=14,
            ),
        xaxis=dict(
                title='Число новых объектов инфраструктуры',
                titlefont_size=16,
                tickfont_size=14,
            ),    
    )
    return fig
