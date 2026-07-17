"""Data loading and surplus-optimization analysis for the Surplus App.

Everything in this module is data work: fetching the source CSVs,
defining the liability assumptions, and computing the surplus tables
and figures that the Dash app (app.py) displays.
"""

from io import StringIO

import numpy as np
import pandas as pd
import plotly.express as px
import requests

################## SOURCE DATA ###################

_CSV_BASE = 'https://raw.githubusercontent.com/Chrander01/csv/main'


def _fetch_csv(name):
    return pd.read_csv(StringIO(requests.get(f'{_CSV_BASE}/{name}').text))


temp = _fetch_csv('temp.csv')                     # Monte Carlo simulated portfolios
# Drop the CSV's saved row index and the raw portfolio weight vectors;
# the Monte Carlo scatter only plots returns, vols, and Sharpe ratios
temp = temp.drop(columns=['Unnamed: 0', 'weights'])
efport = _fetch_csv('efport.csv')                 # efficient frontier points
# Drop the CSV's saved row index and the pre-baked surplus columns for
# fixed discount rates; all unused — the app computes arithmetic surplus
# dynamically from the user's input
efport = efport.drop(columns=['Unnamed: 0',
                              'arithmetic surplus',
                              'arithmetic surplus 2',
                              'arithmetic surplus 3'])
df_combined = _fetch_csv('df_combined.csv')       # 1-year EF return simulations
df_combined_10 = _fetch_csv('df_combined_10.csv')  # 5-year EF return simulations
# Drop the CSVs' saved row indexes; unused
df_combined = df_combined.drop(columns=['Unnamed: 0'])
df_combined_10 = df_combined_10.drop(columns=['Unnamed: 0'])
bins_df = _fetch_csv('bins_df.csv')               # liability PDF traced across the EF

df_combined['r'] = df_combined['r']/100

# Axis coordinates for bins_df: volatility (x) and return-bin midpoints (y)
# of the liability probability-density surface
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

############ LIABILITY ASSUMPTIONS ###############

# Cash flow schedule and per-year spending flexibility (Step 1 page table);
# rows are Cash Flow and Standard Deviation
df_lirr = pd.DataFrame({
    '': ['Cash Flow', 'Standard Deviation'],
    'Starting Wealth': ['$1,000,000', '0%'],
    'Cash Outflow Yr 1': ['-$50,000', '25%'],
    'Cash Outflow Yr 2': ['-$50,000', '25%'],
    'Cash Outflow Yr 3': ['-$50,000', '25%'],
    'Cash Outflow Yr 4': ['-$50,000', '25%'],
    'Wealth Bequest Yr 5': ['-$1,050,000', '25%'],
})

# The discount rate / sigma implied by the schedule above
df_lirr_output = pd.DataFrame({
    'Liability Discount Rate (%)': ['5'],
    'Liability Standard Deviation (σ)': ['6'],
})

############## SURPLUS CALCULATION ###############


def update_mean(input_value, input_std):
    """Build the surplus table for one liability assumption.

    input_value: mean liability discount rate (IRR), in percent.
    input_std:   liability standard deviation (sigma), in percent.

    Returns one row per efficient-frontier point, with risk-adjusted
    surplus and its components. All values are in percent unless a
    column name says otherwise.
    """
    time_horizon = 5.0
    z = 1.65  # z-score for a 95% probability threshold on surplus

    # The full efficient frontier (percent units)
    ef_rets = efport['targetrets'].reset_index(drop=True)
    ef_vols = efport['targetvols'].reset_index(drop=True)

    # Surplus over the full horizon (EF return minus liability IRR, both
    # compounded to the horizon), then annualized back to percent
    mean_irr_full_horizon = (1+input_value/100)**time_horizon-1
    ef_rets_full_horizon = (1+ef_rets/100)**time_horizon-1
    surplus_mean = ef_rets_full_horizon - float(mean_irr_full_horizon)
    annualized_surplus = ((1+surplus_mean)**(1/time_horizon)-1)*100

    # Std dev of surplus: combines asset and liability vol at correlation 1.0
    surplus_stddev = np.sqrt(
        (ef_vols/100)**2 + (input_std/100)**2 - 2*1*ef_vols/100*input_std/100)

    out = pd.DataFrame({'targetrets': annualized_surplus})
    out['Surplus Std Dev'] = surplus_stddev
    out['Mean Surplus'] = out['targetrets']/100
    out['targetvols'] = ef_vols
    out['BE Surplus_95%'] = z*out['Surplus Std Dev']
    out['Risk Premium'] = out['BE Surplus_95%'] - out['Mean Surplus']
    out['BE Output'] = out['BE Surplus_95%']*100
    out['Risk Premium Output'] = out['Risk Premium']*100
    out['Risk Adjusted Surplus'] = (
        out['Mean Surplus']*100 - out['Risk Premium']*100)
    out['Mean Surplus Output'] = out['Mean Surplus']*100
    out['Arithmetic Mean Surplus'] = ef_rets - float(input_value)

    return out


def update_graph(value, s_value):
    """Rebuild the two Outputs-page figures for the selected liability
    discount rate (value, %) and spending flexibility (s_value, sigma %)."""
    mean_surplus_z = update_mean(value, s_value)

    # --- Curves to plot, in color order: efficient frontier (blue),
    # mean liability (orange), risk-adjusted surplus (forestgreen),
    # optimized-vol marker line (lightslategrey), arithmetic surplus (limegreen)
    l_curve = pd.DataFrame({'targetvols': efport['targetvols'],
                            'targetrets': float(value),
                            'type': 'mean liability'})
    combined_df = pd.concat(
        [efport, l_curve], ignore_index=True, sort=False)

    s_curve = pd.DataFrame({'targetrets': mean_surplus_z['Risk Adjusted Surplus'],
                            'targetvols': mean_surplus_z['targetvols'],
                            'type': 'risk adjusted surplus'})

    # Optimal portfolio = the efficient-frontier point whose volatility
    # maximizes risk-adjusted surplus
    best = mean_surplus_z.loc[mean_surplus_z['Risk Adjusted Surplus'].idxmax()]
    optimized_surplus = float(best['Risk Adjusted Surplus'])
    optimized_vol = float(best['targetvols'])
    optimized_ret = float(
        efport.loc[efport['targetvols'] == optimized_vol, 'targetrets'].iloc[0])

    # Vertical segment connecting the optimized surplus to the EF portfolio
    o_line = pd.DataFrame({'targetrets': [optimized_surplus, optimized_ret],
                           'targetvols': optimized_vol,
                           'type': 'optimized volatility (nearest discrete portfolio)'})

    ml_line = pd.DataFrame({'targetrets': efport['targetrets'] - value,
                            'targetvols': efport['targetvols'],
                            'type': 'arithmetic mean surplus'})

    dff_graph = pd.concat([combined_df, s_curve, o_line, ml_line])

    # --- Main surplus-optimization figure
    figure = px.line(
        dff_graph, y='targetrets', x='targetvols', color='type',
        title='Optimizing Risk-Adjusted Surplus vs. Efficient Frontier',
        color_discrete_sequence=["blue", "orange", "forestgreen",
                                 "lightslategrey", "limegreen"])

    figure.add_scatter(
        mode='markers', x=[optimized_vol], y=[optimized_ret],
        marker=dict(color='blue', size=8, symbol='diamond'),
        name='Optimized EF Portfolio').update(layout_showlegend=False)
    figure.add_scatter(
        mode='markers', x=[optimized_vol], y=[optimized_surplus],
        marker=dict(color='forestgreen', size=8, symbol='diamond'),
        name='Optimized Risk-Adjusted Surplus (nearest discrete portfolio)'
    ).update(layout_showlegend=False)

    ef_text = "Efficient Frontier* (µ="+str(optimized_ret) + \
        "%, σ="+str(optimized_vol)+"%)"
    annotations = [
        dict(y=optimized_ret, text=ef_text,
             yanchor='bottom', yshift=10, font=dict(size=11, color='blue')),
        dict(y=optimized_surplus, text='<b>Optimized Risk-Adjusted Surplus</b>',
             yanchor='middle', xanchor='left', xshift=20, yshift=-3,
             font=dict(size=11, color='forestgreen')),
        dict(y=value, text='Mean Liability Discount Rate',
             yanchor='bottom', xanchor='left', xshift=50,
             font=dict(size=10, color='orange')),
        dict(y=optimized_ret-value, text='Arithmetic Mean Surplus',
             yanchor='bottom', xanchor='left', xshift=3, yshift=13,
             font=dict(size=10, color='limegreen')),
    ]
    for ann in annotations:
        figure.add_annotation(x=optimized_vol, showarrow=False,
                              arrowhead=1, **ann)
    figure.update_layout(legend=dict(
        yanchor="bottom", y=0.01, xanchor="left", x=0.15))

    # --- Implied utility figure (lower half of the frontier, through ~12% vol)
    utility_df = pd.DataFrame(
        mean_surplus_z['Arithmetic Mean Surplus'].loc[0:12])
    utility_df['Risk Adjusted Surplus'] = mean_surplus_z['Risk Adjusted Surplus'].loc[0:12]
    data = px.line(utility_df, x='Arithmetic Mean Surplus', y='Risk Adjusted Surplus',
                   line_shape='spline', title='Implied Investor Utility Function')
    data.update_traces(showlegend=True, name='Implied Utility Function')
    data.update_layout(legend=dict(
        yanchor="bottom", y=0.01, xanchor="right", x=0.99))

    return figure, data
