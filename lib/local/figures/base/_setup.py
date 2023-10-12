import plotly.graph_objects as go

# legacy

def Render(fig: go.Figure, bounds=None, bg_col="white"):
    BORDER=0
    if bounds is None:
        xr = [0, 10]
        yr = [0, 10]
    elif isinstance(bounds, float) or isinstance(bounds, int):
        xr, yr = ((-bounds, bounds), (-bounds, bounds))
    else:
        xr, yr = bounds[:2], bounds[2:]

    fig.update_layout(
        xaxis={
            'range': xr,
            'showticklabels': False,
            'showgrid': False,
            'zeroline': False,
        },
        yaxis={
            'range': yr,
            'showticklabels': False,
            'showgrid': False,
            'zeroline': False,
            'scaleanchor': 'x',
            'scaleratio': 1,
        },
        margin={'l': BORDER, 'r': BORDER, 'b': BORDER, 't': BORDER},
        paper_bgcolor=bg_col,
        plot_bgcolor=bg_col,
        dragmode='pan',
        showlegend=False
    )
    return fig

def ShowPlot(fig: go.Figure, scroll_zoom=False, bg_col="white"):
    fig.update_layout(
        xaxis={
            # 'showticklabels': False,
            'showgrid': False,
            # 'zeroline': False,
        },
        yaxis={
            # 'showticklabels': False,
            'showgrid': False,
            # 'zeroline': False,
            # 'scaleanchor': 'x',
            # 'scaleratio': 1,
        },
        plot_bgcolor=bg_col,
        paper_bgcolor=bg_col,
        # font_color=_theme.primary(0.8),
        # dragmode='pan',
        # showlegend=False
    )
    fig.show(config=dict(
        scrollZoom=scroll_zoom
    ))
    return fig
