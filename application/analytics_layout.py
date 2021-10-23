import os
import numpy as np
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import plotly.graph_objs as go


def update_analytics_figure(analytics_data):
    """
    Обновление графика аналитики (отчёт)

    :param analytics_data - аналитические данные от опимизатора
    """

    fig = go.Figure()
    
    total_poputaliton = analytics_data['total_population']
    values = [analytics_data.get('current_infrastructure')]
    for idx in range(1, 11):
        if analytics_data.get(idx, 0) != 0:
            values.append(analytics_data.get(idx) + analytics_data.get('current_infrastructure'))

    widths = np.array([1] * len(values))
    ratios = np.around(values / total_poputaliton * 100, 0)
    delta = np.around(values / values[0] * 100 - 100, 0)

    fig.add_trace(go.Bar(
        y=np.cumsum(widths)-widths,
        width=widths,
        x=values,
        offset=0,
        customdata = np.transpose([ratios, delta]),
        texttemplate="%{customdata[0]}% (+%{customdata[1]}%)",
        textposition="inside",
        textangle=0,
        marker=dict(color = ratios,
                     colorscale='ylgn', line_width = 2, opacity=0.6),
        textfont_color="black",
        orientation='h'
    ))

    fig.update_yaxes(range=[0,len(values)])
    fig.update_xaxes(range=[0,total_poputaliton])

    labels = [f"+{idx}" for idx in range(0, len(values))]

    fig.update_yaxes(
        tickvals=np.cumsum(widths)-widths/2,
        ticktext= labels
    )

    fig.update_layout(
        title_text="Анализ покрытия инфраструктурой",
        barmode="stack",
        xaxis=dict(
                title=f'население региона: {round(total_poputaliton)} человек',
                titlefont_size=16,
                tickfont_size=14,
            ),
        yaxis=dict(
                title='Число новых объектов инфраструктуры',
                titlefont_size=16,
                tickfont_size=14,
            ), 
        margin=dict(l=0, r=0, b=0, t=50),
        plot_bgcolor ="rgba(0, 0, 0, 0)",
        paper_bgcolor ="rgba(0, 0, 0, 0)" 
    )
    return fig
