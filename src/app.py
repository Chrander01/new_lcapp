"""Dash app for the Surplus App: figures, layout, and callbacks.

All data loading and surplus calculations live in analysis.py; this
module only builds what the user sees.
"""

from dash import Dash, html, dcc, Output, Input
from dash import dash_table as dt
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go

from analysis import (bins_df, bin_yaxis_values, df_combined, df_combined_10,
                      df_lirr, df_lirr_output, efport, temp, update_graph,
                      vol_list)
import content as txt

app = Dash(__name__, external_stylesheets=[
           dbc.themes.FLATLY], title="Surplus App")

# Declare server for Heroku deployment. Needed for Procfile.
server = app.server

################## STATIC FIGURES ###################

# Monte Carlo simulated portfolios, colored by Sharpe ratio (Step 2 page)
fig_mc = px.scatter(
    temp, x='port_vols', y='port_rets', color='sharpe_ratio',
    labels={'port_vols': 'Expected Volatility',
            'port_rets': 'Expected Return', 'sharpe_ratio': 'Sharpe Ratio'},
    title="Monte Carlo Simulated Portfolio"
).update_traces(mode='markers', marker=dict(symbol='cross'))
fig_mc.update_xaxes(showspikes=True)
fig_mc.update_yaxes(showspikes=True)

# The efficient frontier itself, colored by Sharpe ratio (Step 2 page)
fig_ef = px.scatter(
    efport, x='targetvols', y='targetrets',  color='targetsharpe',
    labels={'targetrets': 'Expected Return',
            'targetvols': 'Expected Volatility', 'targetsharpe': 'Sharpe Ratio'},
    title="Efficient Frontier Portfolio"
).update_traces(mode='markers', marker=dict(symbol='cross'))
fig_ef.update_xaxes(showspikes=True)
fig_ef.update_yaxes(showspikes=True)

# 3D surface: liability probability density traced across the frontier (Step 1 page)
surf_fig = go.Figure(data=[go.Surface(z=bins_df.values, x=vol_list,
                                      y=bin_yaxis_values)])
surf_fig.update_layout(
    title='Tracing the Liability PDF across the Efficient Frontier',
    autosize=True,
    scene=dict(
        xaxis=dict(title=dict(text='Volatility')),
        yaxis=dict(title=dict(text='Return')),
        zaxis=dict(title=dict(text=''), nticks=4),
        camera_eye=dict(x=1.0, y=-1.0, z=1.5),
        aspectratio=dict(x=1, y=1, z=0.2),
    ),
)


def _horizon_scatter(df, title):
    """Simulated-return scatter with a zero-return reference line (Step 1 page)."""
    fig = px.scatter(df, x='x', y='r', title=title,
                     color='Z', template='simple_white')
    fig.update(layout_coloraxis_showscale=False)
    fig.add_scatter(x=[0, 10], y=[0, 0], name='Zero Return Level')
    return fig


fig_efpx = _horizon_scatter(df_combined, "1-Year Efficient Frontier")
fig_efpx_10 = _horizon_scatter(
    df_combined_10, "5-Year Efficient Frontier (i.e., Time Horizon-Adjusted)")

################## DATA TABLES ###################

# shared DataTable styling so tables blend into the surrounding Bootstrap
# typography instead of using dash_table's default monospace grid look
TABLE_STYLE_TABLE = {
    'overflowX': 'auto',
    'width': '100%',
}
# narrower tables don't need horizontal scroll
TABLE_STYLE_TABLE_NO_SCROLL = {
    'width': '100%',
}
TABLE_STYLE_CELL = {
    'fontFamily': 'inherit',
    'fontSize': '0.9rem',
    'textAlign': 'center',
    'padding': '8px 12px',
    'border': 'none',
    'borderBottom': '1px solid #E9ECEF',
}
TABLE_STYLE_HEADER = {
    'backgroundColor': 'transparent',
    'borderBottom': '2px solid #2C3E50',
    'fontFamily': 'inherit',
    'fontSize': '0.9rem',
    'fontWeight': 'bold',
    'textAlign': 'center',
}

dash_liab_table = dt.DataTable(
    df_lirr.to_dict('records'),
    [{"name": i, "id": i} for i in df_lirr.columns],
    id='dash-liab-table',
    style_table=TABLE_STYLE_TABLE,
    style_cell=TABLE_STYLE_CELL,
    style_header=TABLE_STYLE_HEADER,
    style_cell_conditional=[
        {'if': {'column_id': ''}, 'textAlign': 'left', 'fontWeight': 'bold'},
    ],
)

dash_lirr_table = dt.DataTable(
    df_lirr_output.to_dict('records'),
    [{"name": i, "id": i} for i in df_lirr_output.columns],
    style_table=TABLE_STYLE_TABLE_NO_SCROLL,
    style_cell=TABLE_STYLE_CELL,
    style_header=TABLE_STYLE_HEADER,
)

################## LAYOUT ###################


def drawText2(title_inp, text_inp, text2_inp):
    children = [html.H5(title_inp, className='fw-bold')]
    if text_inp:
        children.append(html.P(text_inp))
    if text2_inp:
        children.append(html.P(text2_inp, className='text-muted small mb-0'))
    return html.Div(children, className='mb-3')


# style for page headers: left-aligned with a left accent border matching the
# sidebar nav pills' active color, for contrast against the white page background
PAGE_HEADER_STYLE = {
    "textAlign": "left",
    "borderLeft": "5px solid #2C3E50",
    "paddingLeft": "15px",
    "fontWeight": "bold",
}

paper_attribution = dbc.Row([
    dbc.Col([
        drawText2(txt.paper_title, "", ""),
    ], width=12),
], className='mb-4')

page_ef = html.Div([
    html.H3(children=txt.ef_header,
            style=PAGE_HEADER_STYLE),
    html.P(txt.app_intro,
           style={'textAlign': 'left', 'color': 'grey', 'paddingLeft': '15px'}),
    html.Hr(className='mt-2 mb-4'),
    paper_attribution,
    dbc.Row([
        dbc.Col([
            dcc.Graph(figure=fig_mc)
        ], width=6),
        dbc.Col([
            drawText2(txt.ef_markowitz_title, txt.ef_markowitz_body, '')
        ], width=6),
    ], align='center', className='mb-4'),
    dbc.Row([
        dbc.Col([
            dcc.Graph(figure=fig_ef)
        ], width=6),
        dbc.Col([
            drawText2(txt.ef_frontier_title, txt.ef_frontier_body, '')
        ], width=6),
    ], align='center'),
])

page_liability = html.Div([
    html.H3(children=txt.liability_header,
            style=PAGE_HEADER_STYLE),
    html.P(txt.app_intro,
           style={'textAlign': 'left', 'color': 'grey', 'paddingLeft': '15px'}),
    html.Hr(className='mt-2 mb-4'),
    paper_attribution,
    dbc.Row([
        dbc.Col([dash_liab_table], width=12),
    ], className='mb-4'),
    dbc.Row([
        dbc.Col([dash_lirr_table], width=6),
        dbc.Col([
            html.I(children=txt.liability_table_hint, className='text-muted', style={
                'textAlign': 'left'})])
    ], className='mb-4'),
    dbc.Row([
        dbc.Col([
            dcc.Graph(figure=fig_efpx)
        ], width=6),
        dbc.Col([
            dcc.Graph(figure=fig_efpx_10)
        ], width=6),
    ], align='center', className='mb-4'),
    dbc.Row([
        dbc.Col([
            html.H5(txt.liability_horizon_title, className='fw-bold'),
            html.P(txt.liability_horizon_body),
        ], width=12),
    ], className='mb-4'),
    dbc.Row([
        dbc.Col([
            dcc.Graph(figure=surf_fig),
            html.P(txt.liability_surface_notes, className='text-muted small'),
        ], width=6),
        dbc.Col([
            drawText2(txt.liability_tracing_title, txt.liability_tracing_body, '')
        ], width=6),
    ], align='center'),
])

page_surplus = html.Div([
    html.H3(children=txt.outputs_header,
            style=PAGE_HEADER_STYLE),
    html.P(txt.app_intro,
           style={'textAlign': 'left', 'color': 'grey', 'paddingLeft': '15px'}),
    html.Hr(className='mt-2 mb-4'),
    paper_attribution,
    dbc.Row([
        dbc.Col([
            html.P(txt.outputs_dropdown1_label,
                   className='small text-muted mb-1', style={'textAlign': 'left'}),
            dcc.Dropdown([float(x) for x in [2, 3, 4, 5, 6, 7]], float(3.0),
                         id='dropdown-selection')], width=4),

        dbc.Col([
            html.P(txt.outputs_dropdown2_label,
                   className='small text-muted mb-1', style={'textAlign': 'left'}),
            dcc.Dropdown([float(x) for x in [5.13, 7.19, 9.6, 12.14, 14.75, 20.08]], float(5.13),
                         id='dropdown-selection2')], width=4),
    ], align='left', className='mb-4'),
    dbc.Row([
        dbc.Col([
            dcc.Graph(id='graph-content'),
            html.P(txt.outputs_chart_notes, className='text-muted small'),
        ], width=6),
        dbc.Col([
            html.H5(txt.outputs_opt_title, className='fw-bold'),
            html.P(txt.outputs_opt_p1),
            html.P(txt.outputs_opt_p2),
            html.P(txt.outputs_opt_p3),
            html.P(txt.outputs_opt_p4),
            html.P(txt.outputs_opt_p5),
        ], width=6),
    ], align='center', className='mb-4'),
    dbc.Row([
        dbc.Col([
            dcc.Graph(id='graph-content2')
        ], width=6),
        dbc.Col([
            drawText2(txt.outputs_utility_title, txt.outputs_utility_body, '')
        ], width=6),
    ], align='center'),
])


# the style arguments for the sidebar. We use position:fixed and a fixed width
SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "16rem",
    "padding": "2rem 1rem",
    "background-color": "#2C3E50",
    "color": "#ECF0F1",
    "display": "flex",
    "flexDirection": "column",
}

# the styles for the main content position it to the right of the sidebar and
# add some padding.
CONTENT_STYLE = {
    "margin-left": "18rem",
    "margin-right": "2rem",
    "padding": "2rem 1rem",
}

sidebar = html.Div(
    [
        html.H2(txt.sidebar_title, className="display-6"),
        html.Hr(),
        html.P(txt.sidebar_lead, className="lead"),
        dbc.Nav(
            [
                dbc.NavLink("Outputs: Surplus Optimization & Utility Function",
                            href="/", active="exact"),
                dbc.NavLink("Step 1. Define Liability Assumptions & Time Horizon",
                            href="/page-1", active="exact"),
                dbc.NavLink("Step 2. Define Underlying Efficient Frontier Assumptions",
                            href="/page-2", active="exact"),
            ],
            vertical=True,
            pills=True,
            style={
                "--bs-nav-link-color": "#ECF0F1",
                "--bs-nav-link-hover-color": "#FFFFFF",
                "--bs-nav-pills-link-active-bg": "#3498DB",
                "--bs-nav-pills-link-active-color": "#FFFFFF",
            },
        ),
        html.Div([
            html.Hr(),
            html.P(txt.copyright_notice, className='small mb-1',
                   style={'color': '#B0BEC5'}),
            html.A(txt.ssrn_link_text,
                   href=txt.ssrn_url, target="_blank",
                   style={'fontSize': '0.75rem', 'textDecoration': 'none', 'color': '#ECF0F1'}),
        ], style={'marginTop': 'auto'}),
    ],
    style=SIDEBAR_STYLE,
)

content = html.Div(id="page-content", style=CONTENT_STYLE)

app.layout = html.Div([dcc.Location(id="url"), sidebar, content])

################## CALLBACKS ###################


@app.callback(Output("page-content", "children"), [Input("url", "pathname")])
def render_page_content(pathname):
    if pathname == "/":
        return page_surplus
    elif pathname == "/page-1":
        return page_liability
    elif pathname == "/page-2":
        return page_ef
    # If the user tries to reach a different page, return a 404 message
    return html.Div(
        [
            html.H1("404: Not found", className="text-danger"),
            html.Hr(),
            html.P(f"The pathname {pathname} was not recognised..."),
        ],
        className="p-3 bg-light rounded-3",
    )


app.callback(
    [Output('graph-content', 'figure'),
     Output('graph-content2', 'figure')],
    [Input('dropdown-selection', 'value'),
     Input('dropdown-selection2', 'value')]
)(update_graph)


if __name__ == "__main__":
    app.run_server(port=8891)
