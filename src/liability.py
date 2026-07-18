"""Monte Carlo IRR of the liability cash-flow schedule (Step 1 page).

Parses the editable liability table (currency cash flows in row 0,
per-year standard deviations in row 1), perturbs each cash flow by its
standard deviation, and solves the IRR of each simulated path. app.py
displays the mean and standard deviation of the simulated IRRs.
"""

import numpy as np

# Number of Monte Carlo cash-flow paths per recalculation
N_SIMULATIONS = 1000

# Column headers of the simulated-IRR output table
IRR_MEAN_COL = 'Liability Discount Rate (Mean IRR, %)'
IRR_STD_COL = 'Liability Standard Deviation (σ, %)'


def parse_currency(text):
    """'-$50,000' -> -50000.0 (plain numbers also accepted)."""
    return float(str(text).replace('$', '').replace(',', '').strip())


def parse_percent(text):
    """'25%' -> 0.25 (plain numbers also accepted, treated as percent)."""
    return float(str(text).replace('%', '').strip()) / 100.0


def format_currency(value):
    """-50000.0 -> '-$50,000', matching the default schedule's style."""
    sign = '-' if value < 0 else ''
    return f'{sign}${abs(value):,.0f}'


def format_percent(value):
    """0.25 -> '25%'; keeps meaningful decimals (0.0625 -> '6.25%')."""
    return f'{value * 100:g}%'


def format_table_records(table_data):
    """Snap the liability table's cells to the default currency/percent
    style, leaving the label column and any unparseable cells as typed."""
    cash_row, std_row = dict(table_data[0]), dict(table_data[1])
    for col in cash_row:
        if col == '':
            continue
        try:
            cash_row[col] = format_currency(parse_currency(cash_row[col]))
        except ValueError:
            pass
        try:
            std_row[col] = format_percent(parse_percent(std_row[col]))
        except ValueError:
            pass
    return [cash_row, std_row]


def irr(cash_flows):
    """IRR of a cash-flow series (t = 0, 1, 2, ...).

    Solves NPV = 0 as a polynomial in d = 1/(1+r) and keeps the real
    root with d > 0 whose rate is nearest zero. Returns np.nan when the
    series has no real IRR (possible for sign-flipped Monte Carlo paths).
    """
    coeffs = np.asarray(cash_flows, dtype=float)[::-1]
    roots = np.roots(coeffs)
    real = roots[np.isreal(roots)].real
    discounts = real[real > 0]
    if discounts.size == 0:
        return np.nan
    rates = 1.0 / discounts - 1.0
    return rates[np.argmin(np.abs(rates))]


def simulate_irr(cash_flows, std_devs, n_sims=N_SIMULATIONS, seed=0):
    """Monte Carlo (mean, std) of the schedule's IRR, both in percent.

    Each path scales cash flow t by (1 + sigma_t * z), z ~ N(0, 1), so a
    25% standard deviation means the flow varies by 25% of its own size.
    Paths with no real IRR are dropped. The fixed seed keeps the output
    stable across page loads for the same inputs.
    """
    cash_flows = np.asarray(cash_flows, dtype=float)
    std_devs = np.asarray(std_devs, dtype=float)
    rng = np.random.default_rng(seed)
    shocks = 1.0 + rng.standard_normal((n_sims, cash_flows.size)) * std_devs
    irrs = np.array([irr(path) for path in cash_flows * shocks])
    irrs = irrs[np.isfinite(irrs)]
    return float(np.mean(irrs)) * 100.0, float(np.std(irrs)) * 100.0


def table_irr(table_data):
    """Monte Carlo (mean, std) IRR, in percent, of the liability
    DataTable's `data` payload.

    table_data: list of row dicts keyed by column id; row 0 is Cash Flow,
    row 1 is Standard Deviation, and the '' column holds the row labels.
    """
    cash_row, std_row = table_data[0], table_data[1]
    value_cols = [col for col in cash_row if col != '']
    cash_flows = [parse_currency(cash_row[col]) for col in value_cols]
    std_devs = [parse_percent(std_row[col]) for col in value_cols]
    return simulate_irr(cash_flows, std_devs)


def irr_output_records(mean_irr, std_irr):
    """One-row records list for the Step 1 discount-rate output table."""
    return [{IRR_MEAN_COL: f'{mean_irr:.2f}', IRR_STD_COL: f'{std_irr:.2f}'}]
