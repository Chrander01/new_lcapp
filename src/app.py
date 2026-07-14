
import numpy as np
from dash import Dash, html, dcc, callback, Output, Input
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
import plotly.graph_objects as go
from dash import dash_table as dt

from io import StringIO
import requests
url = 'https://raw.githubusercontent.com/Chrander01/csv/main/FF_Daily.csv'
url_text = requests.get(url).text
c = pd.read_csv(StringIO(url_text))
test_fig = px.scatter(x=c['Date'], y=c['RF'])

url_temp = 'https://raw.githubusercontent.com/Chrander01/csv/main/temp.csv'
url_text_temp = requests.get(url_temp).text
temp = pd.read_csv(StringIO(url_text_temp))

url_efport = 'https://raw.githubusercontent.com/Chrander01/csv/main/efport.csv'
url_text_efport = requests.get(url_efport).text
efport = pd.read_csv(StringIO(url_text_efport))

url_df_combined = 'https://raw.githubusercontent.com/Chrander01/csv/main/df_combined.csv'
url_text_df_combined = requests.get(url_df_combined).text
df_combined = pd.read_csv(StringIO(url_text_df_combined))

url_df_combined_10 = 'https://raw.githubusercontent.com/Chrander01/csv/main/df_combined_10.csv'
url_text_df_combined_10 = requests.get(url_df_combined_10).text
df_combined_10 = pd.read_csv(StringIO(url_text_df_combined_10))

# url_utility_df = 'https://raw.githubusercontent.com/Chrander01/csv/main/utility_df.csv'
# url_text_utility_df = requests.get(url_utility_df).text
# utility_df = pd.read_csv(StringIO(url_text_utility_df))

# url_s_combined = 'https://raw.githubusercontent.com/Chrander01/csv/main/s_combined.csv'
# url_text_s_combined = requests.get(url_s_combined).text
# s_combined = pd.read_csv(StringIO(url_text_s_combined))

# url_combined_df = 'https://raw.githubusercontent.com/Chrander01/csv/main/combined_df.csv'
# url_text_combined_df = requests.get(url_combined_df).text
# combined_df = pd.read_csv(StringIO(url_text_combined_df))

url_bins_df = 'https://raw.githubusercontent.com/Chrander01/csv/main/bins_df.csv'
url_text_bins_df = requests.get(url_bins_df).text
bins_df = pd.read_csv(StringIO(url_text_bins_df))

rows = ['Cash Flow', 'Standard Deviation']
w_0 = ['$1,000,000', "0%"]
cf_1 = ['-$50,000', "25%"]
cf_2 = ['-$50,000', "25%"]
cf_3 = ['-$50,000', "25%"]
cf_4 = ['-$50,000', "25%"]
cf_5 = ['-$1,050,000', "25%"]
df_lirr = pd.DataFrame(data=rows, columns=[''])
df_lirr['Starting Wealth'] = w_0
df_lirr['Cash Outflow Yr 1'] = cf_1
df_lirr['Cash Outflow Yr 2'] = cf_2
df_lirr['Cash Outflow Yr 3'] = cf_3
df_lirr['Cash Outflow Yr 4'] = cf_4
df_lirr['Wealth Bequest Yr 5'] = cf_5

dash_liab_table = dt.DataTable(df_lirr.to_dict(
    'records'), [{"name": i, "id": i} for i in df_lirr.columns])


t_l_irr = ['5']
t_l_stddev = ['6']
df_lirr_output = pd.DataFrame(
    data=t_l_irr, columns=['Liability Discount Rate (%)'])
df_lirr_output['Liability Standard Deviation (σ)'] = t_l_stddev

dash_lirr_table = dt.DataTable(df_lirr_output.to_dict(
    'records'), [{"name": i, "id": i} for i in df_lirr_output.columns])


############## FUNCTION INPUTS ##################

assetport = efport

loc_df = []
for i in range(0, 11):
    loc_df.append(efport['targetrets'].iloc[i*2])

############## FUNCTION ##################


def update_mean(input_value, input_std):
    mean_irr_df = input_value  # MEAN LIABILITY IRR; expects percent; no need for decimal
    sd_irr_df = input_std  # expects percent; no need for decimal
    time_horizon = 5.0
    mean_irr_full_horizon = (1+mean_irr_df/100)**time_horizon-1
    sd_irr_time_horizon = sd_irr_df/100*np.sqrt(time_horizon)

    loc_df_time = []
    for i in range(0, 10):
        loc_df_time.append((1+loc_df[i]/100)**time_horizon-1)

    # FULL TIME HORIZON

    # (1) Taking each full horizon efficient frontier IRR minus the mean liability IRR

    surplus_mean = []
    for i in range(0, 10):
        surplus_mean.append(loc_df_time[i]-float(mean_irr_full_horizon))

    # (2) Annualizing the result from above

    surplus_mean_1 = []

    for i in range(0, 10):    # Times 100 here changes the presentation to be in percent
        surplus_mean_1.append(((1+surplus_mean[i])**(1/time_horizon)-1)*100)

    # Table output of the previous calculations

    mean_surplus_curve = pd.DataFrame(surplus_mean_1, columns=['targetrets'])

    # Returning the volatility squared = variance for each point on the efficient frontier

    a_vol = []
    for i in range(0, 10):
        a_vol.append(efport['targetvols'].iloc[i*2])

    # Adding EF vol and surplus type to the table of surplus results

    mean_surplus_curve['targetvols'] = a_vol
    mean_surplus_curve['type'] = 'mean_surplus'

    mean_surplus_z = pd.DataFrame(mean_surplus_curve['targetrets'])

    surplus_stddev_decimal = []
    surplus_stddev = []

    l_vol = sd_irr_df

    for i in range(0, 10):
        surplus_stddev.append(
            np.sqrt((a_vol[i]/100)**2 + (l_vol/100)**2 - 2*1*a_vol[i]/100*l_vol/100)*100)
        surplus_stddev_decimal.append(
            np.sqrt((a_vol[i]/100)**2 + (l_vol/100)**2 - 2*1*a_vol[i]/100*l_vol/100))

    mean_surplus_z['Surplus Std Dev'] = surplus_stddev_decimal
    mean_surplus_z['Mean Surplus'] = mean_surplus_z['targetrets']/100

    mean_l_irr = float(mean_irr_df)

    assetport['arithmetic surplus'] = assetport['targetrets']-mean_l_irr

    arith_surplus_values = []

    for i in range(0, 11):
        arith_surplus_values.append(assetport['arithmetic surplus'].iloc[i*2])

    arith_surplus_vols = []

    for i in range(0, 11):
        arith_surplus_vols.append(assetport['targetvols'].iloc[i*2])

    arith_surplus_df = pd.DataFrame(
        arith_surplus_values, columns=['targetrets'])

    arith_surplus_df['targetvols'] = arith_surplus_vols
    arith_surplus_df['type'] = 'Arithmetic Mean Surplus'

    z = 1.65

    # (0-mean_surplus_z['targetrets'].loc[0])/mean_surplus_z['Surplus Std Dev'].loc[0] = 1.65
    z_scores_surplus = []

    for i in range(0, 10):
        z_scores_surplus.append(z*mean_surplus_z['Surplus Std Dev'].loc[i])

    mean_surplus_z['targetvols'] = a_vol
    mean_surplus_z['BE Surplus_95%'] = z_scores_surplus
    # 95% Risk Premium Calculation ***
    mean_surplus_z['Risk Premium'] = mean_surplus_z['BE Surplus_95%'] - \
        mean_surplus_z['Mean Surplus']
    mean_surplus_z['BE Output'] = mean_surplus_z['BE Surplus_95%']*100
    mean_surplus_z['Risk Premium Output'] = mean_surplus_z['Risk Premium']*100
    mean_surplus_z['Risk Adjusted Surplus'] = (
        mean_surplus_z['Mean Surplus']*100 - mean_surplus_z['Risk Premium']*100)
    mean_surplus_z['Mean Surplus Output'] = mean_surplus_z['Mean Surplus']*100
    arith_surplus_df = arith_surplus_df.loc[0:9]
    mean_surplus_z['Arithmetic Mean Surplus'] = arith_surplus_df['targetrets']

    return mean_surplus_z


mean_surplus_z = update_mean(5.03, 6.06)

s_curve = pd.DataFrame(mean_surplus_z['Risk Adjusted Surplus'])
s_curve.rename(columns={'Risk Adjusted Surplus': 'targetrets'}, inplace=True)
s_curve['targetvols'] = mean_surplus_z['targetvols']
s_curve['type'] = 'risk adjusted surplus'

s_combined = s_curve

l_curve = pd.DataFrame(efport['targetvols'])
# l_curve['targetrets'] = float(mean_irr_df)
l_curve['type'] = 'mean liability'

combined_df = pd.concat(
    [efport.loc[0:18], l_curve.loc[0:18]], ignore_index=True, sort=False)


utility_df = pd.DataFrame(mean_surplus_z['Arithmetic Mean Surplus'].loc[0:6])
utility_df['Risk Adjusted Surplus'] = mean_surplus_z['Risk Adjusted Surplus'].loc[0:6]

################## RUN FUNCTION ############################

# mean_surplus_z = update_mean(5.03)
# mean_surplus_z

################## PLOTS ###################################
# Plot simulated portfolio
fig_mc = px.scatter(
    temp, x='port_vols', y='port_rets', color='sharpe_ratio',
    labels={'port_vols': 'Expected Volatility',
            'port_rets': 'Expected Return', 'sharpe_ratio': 'Sharpe Ratio'},
    title="Monte Carlo Simulated Portfolio"
).update_traces(mode='markers', marker=dict(symbol='cross'))

# Plot max sharpe
# fig_mc.add_scatter(
# mode='markers',
# x=[temp.iloc[temp.sharpe_ratio.idxmax()]['port_vols']],
# y=[temp.iloc[temp.sharpe_ratio.idxmax()]['port_rets']],
# marker=dict(color='Red', size=20, symbol='star'),
# name='Max Sharpe'
# ).update(layout_showlegend=False)

# Show spikes
fig_mc.update_xaxes(showspikes=True)
fig_mc.update_yaxes(showspikes=True)

# Plot efficient frontier portfolio
fig_ef = px.scatter(
    efport, x='targetvols', y='targetrets',  color='targetsharpe',
    labels={'targetrets': 'Expected Return',
            'targetvols': 'Expected Volatility', 'targetsharpe': 'Sharpe Ratio'},
    title="Efficient Frontier Portfolio"
).update_traces(mode='markers', marker=dict(symbol='cross'))

# Show spikes
fig_ef.update_xaxes(showspikes=True)
fig_ef.update_yaxes(showspikes=True)

vol_list = [0.,  1.15714286,  2.31428571,  3.47142857,  4.62857143,
            5.78571429,  6.94285714,  8.1,  9.25714286, 10.41428571,
            11.57142857, 12.72857143, 13.88571429, 15.04285714, 16.2,
            17.35714286, 18.51428571, 19.67142857, 20.82857143, 21.98571429,
            23.14285714, 24.3]
bin_yaxis_values = [-0.11405089, -0.0967508, -0.0794507, -0.06215061, -0.04485051,
                    -0.02755042, -0.01025033,  0.00704977,  0.02434986,  0.04164995,
                    0.05895005,  0.07625014,  0.09355023,  0.11085033,  0.12815042,
                    0.14545051,  0.16275061,  0.1800507,  0.1973508,  0.21465089,
                    0.23195098]
surf_fig = go.Figure(data=[go.Surface(z=bins_df.values, x=vol_list,
                                      y=bin_yaxis_values)])

surf_fig.update_layout(scene=dict(
    xaxis=dict(
        title=dict(
            text='Volatility'
        )
    ),
    yaxis=dict(
        title=dict(
            text='Return'
        )
    ),
    zaxis=dict(
        title=dict(
            text=''
        )
    ),
))

surf_fig.update_layout(title='Tracing the Liability PDF across the Efficient Frontier', autosize=True,
                       scene={
                           "zaxis": {"nticks": 4},
                           'camera_eye': {"x": 1.0, "y": -1.0, "z": 1.5},
                           "aspectratio": {"x": 1, "y": 1, "z": 0.2}
                       })


fig_utility = px.line(utility_df, x='Arithmetic Mean Surplus', y='Risk Adjusted Surplus',
                      line_shape='spline', title='Implied Investor Utility Function')
fig_utility.update_layout(yaxis_range=[-8, 2])
fig_utility.update_layout(xaxis_range=[-1, 2])
fig_utility['data'][0]['showlegend'] = True
fig_utility['data'][0]['name'] = 'Implied Utility Function'
fig_utility.update_layout(legend=dict(
    yanchor="bottom", y=0.01, xanchor="right", x=0.99))

df_combined['r'] = df_combined['r']/100
fig_efpx_10 = px.scatter(df_combined_10, x='x', y='r',
                         title="5-Year Efficient Frontier (i.e., Time Horizon-Adjusted)", color='Z', template='simple_white')
fig_efpx_10.update(layout_coloraxis_showscale=False)
fig_efpx_10.add_scatter(x=[0, 10], y=[0, 0], name='Zero Return Level')

fig_efpx = px.scatter(df_combined, x='x', y='r',
                      title="1-Year Efficient Frontier", color='Z', template='simple_white')
fig_efpx.update(layout_coloraxis_showscale=False)
fig_efpx.add_scatter(x=[0, 10], y=[0, 0], name='Zero Return Level')


app = Dash(__name__, external_stylesheets=[
           dbc.themes.FLATLY], title="Surplus App")

# Declare server for Heroku deployment. Needed for Procfile.
server = app.server

# assume you have a "long-form" data frame
# see https://plotly.com/python/px-arguments/ for more options
# df = pd.DataFrame({
#    "Fruit": ["Apples", "Oranges", "Bananas", "Apples", "Oranges", "Bananas"],
#    "Amount": [4, 1, 2, 2, 4, 5],
#    "City": ["SF", "SF", "SF", "Montreal", "Montreal", "Montreal"]
# })

# fig = px.bar(df, x="Fruit", y="Amount", color="City", barmode="group")


def drawText2(title_inp, text_inp, text2_inp):
    children = [html.H5(title_inp, className='fw-bold')]
    if text_inp:
        children.append(html.P(text_inp))
    if text2_inp:
        children.append(html.P(text2_inp, className='text-muted small mb-0'))
    return html.Div(children, className='mb-3')


p_title1 = "Extending Sharpe and Tint (1990) Surplus Optimization to GBI"
p_title2 = "Research article at SSRN: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4357369"
p_title3 = "© 2024 VS Quantitative Solutions LLC, All Rights Reserved."

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
        drawText2(p_title1, "", ""),
    ], width=12),
], className='mb-4')

page_ef = html.Div([
    html.H3(children='Efficient Frontier',
            style=PAGE_HEADER_STYLE),
    html.P("This web application illustrates the calculations in practice of using a new goals-based investing model.",
           style={'textAlign': 'left', 'color': 'grey', 'paddingLeft': '15px'}),
    html.Hr(className='mt-2 mb-4'),
    paper_attribution,
    dbc.Row([
        dbc.Col([
            dcc.Graph(figure=fig_mc)
        ], width=6),
        dbc.Col([
            drawText2('Markowitz Mean-Variance Analysis',
                      'Using Monte Carlo to simulate random portfolio weights, this graph shows various risk and return combinations that can be achieved. They are shown here primarily to illustrate the starting point after which the liabilities and surlus are introduced. The investor could of course use their own desired asset return assumptions to represent the market portfolios available.',
                      '')
        ], width=6),
    ], align='center', className='mb-4'),
    dbc.Row([
        dbc.Col([
            dcc.Graph(figure=fig_ef)
        ], width=6),
        dbc.Col([
            drawText2('Efficient Frontier', 'This grapht then shows the efficient frontier of possible returns, which "dominates" all others.',
                      '')
        ], width=6),
    ], align='center'),
])

page_liability = html.Div([
    html.H3(children='Tracing the Liability Distribution',
            style=PAGE_HEADER_STYLE),
    html.P("This web application illustrates the calculations in practice of using a new goals-based investing model.",
           style={'textAlign': 'left', 'color': 'grey', 'paddingLeft': '15px'}),
    html.Hr(className='mt-2 mb-4'),
    paper_attribution,
    dbc.Row([dash_liab_table], className='mb-4'),
    dbc.Row([
        dbc.Col([dash_lirr_table], width=6),
        dbc.Col([
            html.I(children='<-- These become the inputs that flow through to the first tab', className='text-muted', style={
                'textAlign': 'left'})])
    ], className='mb-4'),
    dbc.Row([
        dbc.Col([
            dcc.Graph(figure=surf_fig),
            html.P('Notes: n=2,000; probability distribution of present value discount rate of liabilities based on annual cashflows and residual value above.', className='text-muted small'),
        ], width=6),
        dbc.Col([
            drawText2('Tracing the Liability Probability Densities using Monte Carlo', 'The implied discount rate of the stated values above has a mean of ~.05 and a standard deviation of ~.06. These values were chosen for simplicity to illustrate that expected increases of .05 every year will clearly lead to an average expected return starting today of .05. The individual yearly standard deviations of .25 result in a combined standard deviation (relative to starting wealth) of .06 as stated. Correlation between assets and liabilities is set to 1.0 to reflect that an investor will increase or decrease future spending outlays based on actual asset returns. The probability distribution of the liability is traced out using Monte Carlo. The surface to the left reflects the fact that this distribution is constant across the efficient frontier. So while asset volatility fluctuates, liability volatility is constant across the range of the efficient frontier.',
                      '')
        ], width=6),
    ], align='center', className='mb-4'),
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
            html.H5('Time Horizon Impacts on Efficient Frontier', className='fw-bold'),
            html.P('The duration of liabilities is matched to the duration of the assets. In this case, we are using an equivalent total of 5 years for each. This has an important impact on the efficient frontier given an increased time horizon has the effect of increasing the probability of a positive outcome over the total period. This can be observed, visually, by the amount of observations that land above the point of zero returns as the time horizon increases (i.e., in the graph on the right). This is also an area where the model complexity could be increased in order to more realistically match time horizon effects. For example, a weighting of the dollar duration of liabilities might be more precise or even more interestingly, multi-period optimizations, such as dynamic programming. However, this paper focuses on the methodology of combining asset and liability returns rather than fine tuning the liability calculations. In addition, there has been substantial research in the fields of dynamic programming that could likely be applied to extend this model.'),
        ], width=12),
    ]),
])

page_surplus = html.Div([
    html.H3(children='Surplus Optimization along Efficient Frontier',
            style=PAGE_HEADER_STYLE),
    html.P("This web application illustrates the calculations in practice of using a new goals-based investing model.",
           style={'textAlign': 'left', 'color': 'grey', 'paddingLeft': '15px'}),
    html.Hr(className='mt-2 mb-4'),
    paper_attribution,
    dbc.Row([
        dbc.Col([
            html.P('Discount Rate at which Future Spending Liabilities = PV of Current Net Assets (%)',
                   className='small text-muted mb-1', style={'textAlign': 'left'}),
            dcc.Dropdown([float(5.0), float(6.0), float(7.0)], float(5.0),
                         id='dropdown-selection')], width=4),

        dbc.Col([
            html.P('Spending Flexibility of Liabilities (σ) using Goal Ranges & Monte Carlo (next page)',
                   className='small text-muted mb-1', style={'textAlign': 'left'}),
            dcc.Dropdown([float(5.0), float(6.0), float(10.0)], float(6.0),
                         id='dropdown-selection2')], width=4),
    ], align='left', className='mb-4'),
    dbc.Row([
        dbc.Col([
            dcc.Graph(id='graph-content'),
            html.P('Notes: *Nearest discrete portfolio; n=2,000; z-score = 1.65, equating to 95% probability of surplus value; time horizon = 5 years; correlation(assets, liabilities) = 1.0', className='text-muted small'),
        ], width=6),
        dbc.Col([
            html.H5('Surplus Optimization on the Efficient Frontier', className='fw-bold'),
            html.P('The mean liability and risk-adjusted surplus curves are plotted against a typical efficient frontier. This allows you see, visually, where optimal surplus intersects with the efficient frontier--and therefore, identifies the optimal portfolio (i.e., optimal asset allocation).'),
            html.P('The mean liability discount rate is the rate (i.e., the expected value, E(x)) at which future spending equals the current value of net assets. In other words, it is the return that would need to be generated in order to satisfy future liabilities (spending goals).'),
            html.P(
                'A full probability density function is traced out via Monte Carlo (details on next tab) to represent these future liabilities--which provides both this mean, but also the standard deviation of the discount rate that equates to future spending liabilties.'),
            html.P('Using this probability distribution for future liabilities, we can then calculate a risk-adjusted surplus value that not only subtracts future spending from future asset returns, but also incorporates risk, which is mediated by the standard deviation of liabilities (i.e., spending flexibility), a correlation term of 1.0, and a z-score for surplus, which represents the probability threshold that surplus will equal at least zero (i.e., set to 0.95 or 0.99 certainty). These additional paramters are what create the dynamic shape (and importantly, the assymetric risk profile) of both risk-adjusted surplus and the utility function calculations below. The risk-adjusted surplus computation is an extension of concepts developed by Sharpe and Tint (1990) and is described in detail in the accompanying research article.'),
            html.P('The highest risk-adjusted surplus reflects the optimal portfolio, which takes into account both stochastic return and stochastic future liabilities in a single-period setting--inputs are ideally revised until optimal surplus equals zero at a prescribed z-score.'),
        ], width=6),
    ], align='center', className='mb-4'),
    dbc.Row([
        dbc.Col([
            dcc.Graph(id='graph-content2')
        ], width=6),
        dbc.Col([
            drawText2('Implied (Idiosyncratic) Investor Utility Function', "After a model for risk-adjusted surplus was formulated, it eventually became apparent that it could be plotted against a simple arithmetic mean surplus value to arrive at a direct measure an investor's idiosyncratic utility function. In the author's opinion, this is an improved and more direct measure of utility, rather than typical, stylized approaches or approaches that infer utility based on a presumed value of its first derivative. The resulting utility function is very comparable to the shape of traditional, stylized utility functions once you disregard results that exceed the optimized surplus level. Interesting shape dynamics (i.e., convex, concave, kinked, etc.) can also be observed as assumptions are changed.",
                      '')
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
        html.H2("GBI Surplus Optimization", className="display-6"),
        html.Hr(),
        html.P(
            "Investor Surplus Optimization and Idiosyncratic Utility Curves (Beta Version)", className="lead"
        ),
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
            html.P(p_title3, className='small mb-1',
                   style={'color': '#B0BEC5'}),
            html.A("Research article at SSRN",
                   href='https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4357369', target="_blank",
                   style={'fontSize': '0.75rem', 'textDecoration': 'none', 'color': '#ECF0F1'}),
        ], style={'marginTop': 'auto'}),
    ],
    style=SIDEBAR_STYLE,
)

content = html.Div(id="page-content", style=CONTENT_STYLE)

app.layout = html.Div([dcc.Location(id="url"), sidebar, content])


@ app.callback(Output("page-content", "children"), [Input("url", "pathname")])
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


@ app.callback([
    Output('graph-content', 'figure'),
    Output('graph-content2', 'figure')],
    [Input('dropdown-selection', 'value'),
     Input('dropdown-selection2', 'value')]
)
def update_graph(value, s_value):
    mean_surplus_z = update_mean(value, s_value)
    s_curve = pd.DataFrame(mean_surplus_z['Risk Adjusted Surplus'])
    s_curve.rename(
        columns={'Risk Adjusted Surplus': 'targetrets'}, inplace=True)
    s_curve['targetvols'] = mean_surplus_z['targetvols']
    s_curve['type'] = 'risk adjusted surplus'

    s_combined = s_curve

    l_curve = pd.DataFrame(efport['targetvols'])
    l_curve['targetrets'] = float(value)
    l_curve['type'] = 'mean liability'

    ############################################# NEW ####################################################

    combined_df = pd.concat(
        [efport.loc[0:18], l_curve.loc[0:18]], ignore_index=True, sort=False)

    ####################################### OPTIMIZED POINT ##############################################

    optimized_surplus = max(mean_surplus_z['Risk Adjusted Surplus'])
    row_index = mean_surplus_z.index.get_loc(
        mean_surplus_z[mean_surplus_z['Risk Adjusted Surplus'] == optimized_surplus].index[0])
    optimized_vol = mean_surplus_z['targetvols'].iloc[row_index]
    optimized_surplus = float(optimized_surplus)
    row_index2 = combined_df.index.get_loc(
        combined_df[combined_df['targetvols'] == optimized_vol].index[0])
    optimized_ret = combined_df['targetrets'].iloc[row_index2]
    optimized_ret = float(optimized_ret)
    optimized_vol = float(optimized_vol)

    o_rets = [optimized_surplus, optimized_ret]
    o_line = pd.DataFrame(o_rets, columns=['targetrets'])
    o_line['targetvols'] = optimized_vol
    o_line['type'] = 'optimized volatility (nearest discrete portfolio)'

    ################################################ NEW #################################################

    arith_surplus_values = []

    for i in range(0, 11):
        arith_surplus_values.append(assetport['arithmetic surplus'].iloc[i*2])

    arith_surplus_vols = []

    for i in range(0, 11):
        arith_surplus_vols.append(assetport['targetvols'].iloc[i*2])

    arith_surplus_df = pd.DataFrame(
        arith_surplus_values, columns=['targetrets'])

    arith_surplus_df['targetvols'] = arith_surplus_vols
    arith_surplus_df['type'] = 'Arithmetic Mean Surplus'

    arith_surplus_df = arith_surplus_df.loc[0:9]

    utility_df = pd.DataFrame(
        mean_surplus_z['Arithmetic Mean Surplus'].loc[0:6])
    utility_df['Risk Adjusted Surplus'] = mean_surplus_z['Risk Adjusted Surplus'].loc[0:6]
    data = px.line(utility_df, x='Arithmetic Mean Surplus', y='Risk Adjusted Surplus',
                   line_shape='spline', title='Implied Investor Utility Function')
    data['data'][0]['showlegend'] = True
    data['data'][0]['name'] = 'Implied Utility Function'
    data.update_layout(legend=dict(
        yanchor="bottom", y=0.01, xanchor="right", x=0.99))
    dff = combined_df
    dff2 = s_combined
    dff_graph = pd.concat([dff, dff2])
    dff3 = o_line
    dff_graph = pd.concat([dff_graph, o_line])
    ml_line = pd.DataFrame(efport['targetrets'].loc[0:18] - value)
    ml_line['targetvols'] = efport['targetvols']
    ml_line['type'] = 'arithmetic mean surplus'
    dff_graph = pd.concat([dff_graph, ml_line])

    ef_text = "Efficient Frontier* (µ="+str(optimized_ret) + \
        "%, σ="+str(optimized_vol)+"%)"

    figure = px.line(dff_graph, y='targetrets',
                     x='targetvols', color='type', title='Optimizing Risk-Adjusted Surplus vs. Efficient Frontier', color_discrete_sequence=["blue", "orange", "forestgreen", "lightslategrey", "limegreen"])

    # Plot max sharpe
    figure.add_scatter(
        mode='markers',
        x=[optimized_vol],
        y=[optimized_ret],
        marker=dict(color='blue', size=8, symbol='diamond'),
        name='Optimized EF Portfolio').update(layout_showlegend=False)
    figure.add_scatter(
        mode='markers',
        x=[optimized_vol],
        y=[optimized_surplus],
        marker=dict(color='forestgreen', size=8, symbol='diamond'),
        name='Optimized Risk-Adjusted Surplus (nearest discrete portfolio)').update(layout_showlegend=False)

    figure.add_annotation(x=optimized_vol, y=optimized_ret,
                          text=ef_text,
                          yanchor='bottom',
                          # xanchor='left',
                          yshift=10,
                          showarrow=False,
                          arrowhead=1,
                          font=dict(
                              # family="Courier New, monospace",
                              size=11,
                              color="blue"
                          ),)
    figure.add_annotation(x=optimized_vol, y=optimized_surplus,
                          text="<b>Optimized Risk-Adjusted Surplus</b>",
                          yanchor='middle',
                          xanchor='left',
                          xshift=20,
                          yshift=-3,
                          showarrow=False,
                          arrowhead=1,
                          font=dict(
                              # family="Courier New, monospace",
                              size=11,
                              color="forestgreen"
                          ),)
    figure.add_annotation(x=optimized_vol, y=value,
                          text="Mean Liability Discount Rate",
                          yanchor='bottom',
                          xanchor='left',
                          xshift=50,
                          showarrow=False,
                          arrowhead=1,
                          font=dict(
                              # family="Courier New, monospace",
                              size=10,
                              color="orange"
                          ),)
    figure.add_annotation(x=optimized_vol, y=optimized_ret-value,
                          text="Arithmetic Mean Surplus",
                          yanchor='bottom',
                          xanchor='left',
                          xshift=3,
                          yshift=13,
                          showarrow=False,
                          arrowhead=1,
                          font=dict(
                              # family="Courier New, monospace",
                              size=10,
                              color="limegreen"
                          ),)
    figure.update_layout(legend=dict(
        yanchor="bottom", y=0.01, xanchor="left", x=0.15))
    return figure, data


if __name__ == "__main__":
    app.run_server(port=8891)
