"""Dash app for the Surplus App: figures, layout, and callbacks.

All data loading and surplus calculations live in analysis.py; this
module only builds what the user sees.
"""

from dash import Dash, html, dcc, Output, Input, State, ctx, no_update
from dash import dash_table as dt
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go

from analysis import (bins_df, bin_yaxis_values, df_combined, df_combined_10,
                      df_lirr, efport, temp, update_graph, vol_list)
from liability import (IRR_MEAN_COL, IRR_STD_COL, format_table_records,
                       irr_output_records, table_irr)
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

# Default liability schedule and its Monte Carlo IRR; these seed the two
# liability stores (and so the Outputs page) until the user commits an
# edited schedule with the Calculate button
DEFAULT_LIAB_ROWS = df_lirr.to_dict('records')
DEFAULT_LIAB_IRR, DEFAULT_LIAB_SIGMA = table_irr(DEFAULT_LIAB_ROWS)

# Editable: the user can overwrite any cash flow or standard deviation
# (the row-label column stays fixed), then commit with Calculate. The
# table has no persistence of its own — it is refilled from the
# liability-inputs-store whenever the page mounts, so uncommitted edits
# are discarded on navigation and the committed schedule is always the
# one driving the model.
dash_liab_table = dt.DataTable(
    DEFAULT_LIAB_ROWS,
    [{"name": i, "id": i, "editable": i != ''} for i in df_lirr.columns],
    id='dash-liab-table',
    editable=True,
    style_table=TABLE_STYLE_TABLE,
    style_cell=TABLE_STYLE_CELL,
    style_header=TABLE_STYLE_HEADER,
    style_cell_conditional=[
        {'if': {'column_id': ''}, 'textAlign': 'left', 'fontWeight': 'bold'},
    ],
    # Editable cells get a form-field look (bordered, tinted, text cursor)
    # so it's obvious they are inputs, unlike the flat read-only tables
    style_data_conditional=[
        {'if': {'column_editable': True},
         'backgroundColor': '#F0F7FC',
         'border': '1px solid #B8D4E8',
         'cursor': 'text'},
    ],
)

# The discount rate / sigma implied by the schedule above, via Monte
# Carlo IRR; refreshed by the update_liability_irr callback on every edit
dash_lirr_table = dt.DataTable(
    irr_output_records(DEFAULT_LIAB_IRR, DEFAULT_LIAB_SIGMA),
    [{"name": i, "id": i} for i in (IRR_MEAN_COL, IRR_STD_COL)],
    id='dash-lirr-table',
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
        dbc.Col([
            html.P(txt.liability_edit_hint,
                   className='small text-muted mb-2',
                   style={'textAlign': 'left'}),
            dash_liab_table,
            dbc.Button(txt.liability_calc_label, id='calc-liab-button',
                       color='primary', size='sm',
                       className='mt-2 me-2'),
            dbc.Button(txt.liability_reset_label, id='reset-liab-button',
                       color='primary', size='sm', className='mt-2'),
        ], width=12),
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
            drawText2(txt.liability_tracing_title,
                      txt.liability_tracing_body, '')
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
            html.P(txt.outputs_inputs_label,
                   className='small text-muted mb-1', style={'textAlign': 'left'}),
            html.Div(id='outputs-liability-display', className='fw-bold'),
        ], width=8),
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

# The two liability stores live in the root layout so they survive page
# navigation and are the single source of truth for the whole model:
#   liability-inputs-store — the committed cash-flow schedule (the Step 1
#     table is refilled from it on every page mount; Calculate and Reset
#     are the only writers, so stale or half-finished edits never leak)
#   liability-store — the simulated IRR mean/sigma of that schedule,
#     which drives the Outputs-page surplus figures
app.layout = html.Div([
    dcc.Location(id="url"),
    dcc.Store(id='liability-inputs-store', data=DEFAULT_LIAB_ROWS),
    dcc.Store(id='liability-store',
              data={'irr': DEFAULT_LIAB_IRR, 'sigma': DEFAULT_LIAB_SIGMA}),
    sidebar,
    content,
])

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


@app.callback(Output('dash-liab-table', 'data'),
              Input('liability-inputs-store', 'data'))
def load_liability_table(rows):
    """Fill the Step 1 table from the committed schedule whenever the
    page mounts or the schedule changes (Calculate/Reset), discarding
    any on-screen edits that were never calculated."""
    return rows


@app.callback(Output('dash-liab-table', 'data', allow_duplicate=True),
              Input('dash-liab-table', 'data'),
              prevent_initial_call=True)
def format_liability_table(rows):
    """Snap each accepted edit to the default currency/percent style
    (e.g. '60000' -> '$60,000', '30' -> '30%'). Unparseable cells are
    left as typed, and returning no_update when nothing changed stops
    this self-referencing callback from cycling."""
    formatted = format_table_records(rows)
    if formatted == rows:
        return no_update
    return formatted


@app.callback([Output('liability-inputs-store', 'data'),
               Output('dash-lirr-table', 'data'),
               Output('liability-store', 'data')],
              [Input('calc-liab-button', 'n_clicks'),
               Input('reset-liab-button', 'n_clicks')],
              State('dash-liab-table', 'data'),
              prevent_initial_call=True)
def commit_liability_inputs(_calc, _reset, rows):
    """Calculate commits the on-screen schedule and re-runs the Monte
    Carlo IRR; Reset commits the default schedule instead. Committing
    updates the inputs store (refilling the table, which flushes any
    stale edits), the Step 1 output table, and the liability store that
    drives the Outputs-page figures.

    Unparseable values (e.g. '-$' or '2%x') leave everything unchanged.
    """
    if ctx.triggered_id == 'reset-liab-button':
        rows = DEFAULT_LIAB_ROWS
    try:
        mean_irr, std_irr = table_irr(rows)
    except (ValueError, TypeError, IndexError, KeyError):
        return no_update, no_update, no_update
    # Store the normalized style even if the user hits Calculate before
    # the format_liability_table round-trip lands
    return (format_table_records(rows), irr_output_records(mean_irr, std_irr),
            {'irr': mean_irr, 'sigma': std_irr})


@app.callback([Output('graph-content', 'figure'),
               Output('graph-content2', 'figure')],
              Input('liability-store', 'data'))
def update_surplus_graphs(liability):
    """Drive the Outputs-page figures from the simulated liability IRR."""
    return update_graph(liability['irr'], liability['sigma'])


@app.callback(Output('outputs-liability-display', 'children'),
              Input('liability-store', 'data'))
def show_liability_inputs(liability):
    return (f"Liability Discount Rate (Mean IRR): {liability['irr']:.2f}%"
            f"  |  Spending Flexibility (σ): {liability['sigma']:.2f}%")


if __name__ == "__main__":
    app.run_server(port=8891)
