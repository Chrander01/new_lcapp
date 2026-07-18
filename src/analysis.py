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


# Monte Carlo simulated portfolios
temp = _fetch_csv('temp.csv')
# Drop the CSV's saved row index and the raw portfolio weight vectors;
# the Monte Carlo scatter only plots returns, vols, and Sharpe ratios
temp = temp.drop(columns=['Unnamed: 0', 'weights'])
ef_csv = _fetch_csv('efport.csv')                 # efficient frontier points
ef_csv['targetrets'] = ef_csv['targetrets'].replace(5.79, 6.0)
efport = ef_csv
# Drop the CSV's saved row index and the pre-baked surplus columns for
# fixed discount rates; all unused — the app computes arithmetic surplus
# dynamically from the user's input
efport = efport.drop(columns=['Unnamed: 0',
                              'arithmetic surplus',
                              'arithmetic surplus 2',
                              'arithmetic surplus 3'])
# 1-year EF return simulations
df_combined = _fetch_csv('df_combined.csv')
# 5-year EF return simulations
df_combined_10 = _fetch_csv('df_combined_10.csv')
# Drop the CSVs' saved row indexes; unused
df_combined = df_combined.drop(columns=['Unnamed: 0'])
df_combined_10 = df_combined_10.drop(columns=['Unnamed: 0'])
# liability PDF traced across the EF
bins_df = _fetch_csv('bins_df.csv')

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
# rows are Cash Flow and Standard Deviation. These are the defaults for
# the editable Step 1 table; liability.py Monte Carlos the IRR of
# whatever the user enters there.
df_lirr = pd.DataFrame({
    '': ['Cash Flow', 'Standard Deviation'],
    'Starting Wealth': ['$1,000,000', '0%'],
    'Cash Outflow Yr 1': ['-$50,000', '25%'],
    'Cash Outflow Yr 2': ['-$50,000', '25%'],
    'Cash Outflow Yr 3': ['-$50,000', '25%'],
    'Cash Outflow Yr 4': ['-$50,000', '25%'],
    'Wealth Bequest Yr 5': ['-$1,050,000', '25%'],
})

############## SURPLUS CALCULATION ###############


# Correlation between portfolio (EF) returns and the liability. At 1.0 the
# surplus std dev collapses to |ef_vols - liability_std|; below 1.0 the full
# two-asset formula applies and the std dev can no longer reach zero.
ASSET_LIABILITY_CORR = 0.90


def update_mean(input_value, input_std, input_corr=ASSET_LIABILITY_CORR):
    """Build the surplus table for one liability assumption.

    input_value: mean liability discount rate (IRR), in percent.
    input_std:   liability standard deviation (sigma), in percent.
    input_corr:  correlation between EF portfolio returns and the
                 liability, used in the surplus std dev formula.

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

    # The standard two-asset variance formula σₐ² + σᵦ² − 2ρσₐσᵦ. With ρ = 1
    # it algebraically collapses to |ef_vols − input_std|; with ρ < 1 it keeps
    # a floor of input_std·√(1−ρ²) at ef_vols = ρ·input_std.
    surplus_stddev = np.sqrt(
        (ef_vols/100)**2 + (input_std/100)**2
        - 2*input_corr*ef_vols/100*input_std/100)

    out = pd.DataFrame({'targetvols': ef_vols})
    out['ef_returns'] = ef_rets
    out['Arithmetic Mean Surplus'] = ef_rets - float(input_value)
    out['Mean Surplus (Long-term compounded EF - compounded Liab Discount Rate)'] = annualized_surplus/100
    out['Surplus Std Dev = sqrt(ef_vols^2 + liability_std^2 - 2 x Corr x ef_vols x liability_std)'] = surplus_stddev
    # The column bottoms out where the portfolio vol nearly equals
    # Corr x sigma input, and grows as vol moves away from it in either
    # direction. So BE Surplus_95% is 1.65 standard deviations of surplus
    # risk — the buffer the portfolio must clear at 95% confidence — and
    # it's why the risk-adjusted optimum lands near the frontier point
    # whose volatility matches the liability's.
    out['BE Surplus_95% (Surplus Std Dev x z-score)'] = z * \
        out['Surplus Std Dev = sqrt(ef_vols^2 + liability_std^2 - 2 x Corr x ef_vols x liability_std)']
    out['Risk Premium (BE Surplus_95% - Mean Surplus)'] = (
        out['BE Surplus_95% (Surplus Std Dev x z-score)'] - out['Mean Surplus (Long-term compounded EF - compounded Liab Discount Rate)'])
    out['Risk Adjusted Surplus (Mean Surplus - Risk Premium)'] = (
        out['Mean Surplus (Long-term compounded EF - compounded Liab Discount Rate)']
        - out['Risk Premium (BE Surplus_95% - Mean Surplus)'])
    out['Output BE (95% BE x 100)'] = out['BE Surplus_95% (Surplus Std Dev x z-score)']*100
    out['Output Mean Surplus (x 100)'] = out['Mean Surplus (Long-term compounded EF - compounded Liab Discount Rate)']*100
    out['Output Risk Premium (x 100)'] = (
        out['Risk Premium (BE Surplus_95% - Mean Surplus)']*100)
    out['Output Risk Adjusted Surplus (x 100)'] = (
        out['Mean Surplus (Long-term compounded EF - compounded Liab Discount Rate)']*100
        - out['Risk Premium (BE Surplus_95% - Mean Surplus)']*100)

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

    s_curve = pd.DataFrame({'targetrets': mean_surplus_z['Output Risk Adjusted Surplus (x 100)'],
                            'targetvols': mean_surplus_z['targetvols'],
                            'type': 'risk adjusted surplus'})

    # Optimal portfolio = the efficient-frontier point whose volatility
    # maximizes risk-adjusted surplus
    best = mean_surplus_z.loc[mean_surplus_z['Output Risk Adjusted Surplus (x 100)'].idxmax(
    )]
    optimized_surplus = float(best['Output Risk Adjusted Surplus (x 100)'])
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

    # Overlay the compounded-and-annualized mean surplus and the risk premium
    # (the 95% confidence buffer in excess of the mean surplus), both in
    # percent, dashed to set them apart from the primary curves
    figure.add_scatter(x=mean_surplus_z['targetvols'],
                       y=mean_surplus_z['Output Mean Surplus (x 100)'],
                       mode='lines', name='Mean Surplus over Time Horizon',
                       line=dict(color='crimson', dash='dash'))
    figure.add_scatter(x=mean_surplus_z['targetvols'],
                       y=mean_surplus_z['Output Risk Premium (x 100)'],
                       mode='lines', name='Risk Premium',
                       line=dict(color='teal', dash='dash'))

    ef_text = "Efficient Frontier* (µ="+str(optimized_ret) + \
        "%, σ="+str(optimized_vol)+"%)"
    # All labels except the Efficient Frontier's sit at the right end of
    # their curve (this figure's legend is hidden, so each curve is
    # identified by an annotation instead)
    right_edge = mean_surplus_z.iloc[-1]
    right_vol = float(right_edge['targetvols'])
    right_ret = float(efport['targetrets'].iloc[-1])
    annotations = [
        dict(x=optimized_vol, y=optimized_ret, text=ef_text,
             yanchor='bottom', yshift=10, font=dict(size=11, color='blue')),
        dict(x=right_vol,
             y=float(right_edge['Output Risk Adjusted Surplus (x 100)']),
             text='<b>Optimized Risk-Adjusted Surplus</b>',
             xanchor='right', yanchor='bottom', yshift=3,
             font=dict(size=11, color='forestgreen')),
        dict(x=right_vol, y=value, text='Mean Liability Discount Rate',
             xanchor='right', yanchor='bottom', yshift=3,
             font=dict(size=10, color='orange')),
        dict(x=right_vol, y=right_ret-value, text='Arithmetic Mean Surplus',
             xanchor='right', yanchor='bottom', yshift=3,
             font=dict(size=10, color='limegreen')),
        dict(x=right_vol,
             y=float(right_edge['Output Mean Surplus (x 100)']),
             text='Mean Surplus over Time Horizon',
             xanchor='right', yanchor='bottom', yshift=3,
             font=dict(size=10, color='crimson')),
        dict(x=right_vol,
             y=float(right_edge['Output Risk Premium (x 100)']),
             text='Risk Premium',
             xanchor='right', yanchor='bottom', yshift=3,
             font=dict(size=10, color='teal')),
    ]
    for ann in annotations:
        figure.add_annotation(showarrow=False, arrowhead=1, **ann)
    figure.update_layout(legend=dict(
        yanchor="bottom", y=0.01, xanchor="left", x=0.15))

    # --- Implied utility figure (lower half of the frontier, through ~12% vol)
    utility_df = pd.DataFrame(
        mean_surplus_z['Arithmetic Mean Surplus'].loc[0:12])
    utility_df['Output Risk Adjusted Surplus (x 100)'] = mean_surplus_z[
        'Output Risk Adjusted Surplus (x 100)'].loc[0:12]
    data = px.line(utility_df, x='Arithmetic Mean Surplus', y='Output Risk Adjusted Surplus (x 100)',
                   line_shape='spline', title='Implied Investor Utility Function')
    data.update_traces(showlegend=True, name='Implied Utility Function')
    data.update_layout(legend=dict(
        yanchor="bottom", y=0.01, xanchor="right", x=0.99))

    return figure, data
