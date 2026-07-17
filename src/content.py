"""All user-facing text for the Surplus App, grouped by page.

Edit the strings here to change what the app says; app.py decides
where and how each one is displayed.
"""

# ---------- Shared across pages ----------

app_intro = "This web application illustrates the calculations in practice of using a new goals-based investing model."

paper_title = "Extending Sharpe and Tint (1990) Surplus Optimization to GBI"
copyright_notice = "© 2024-2026 VS Quantitative Solutions LLC, All Rights Reserved."
ssrn_url = 'https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4357369'
ssrn_link_text = "Research article at SSRN"

# ---------- Sidebar ----------

sidebar_title = "GBI Surplus Optimization"
sidebar_lead = "Investor Surplus Optimization and Idiosyncratic Utility Curves (Beta Version)"

# ---------- Outputs page ("/") ----------

outputs_header = 'Surplus Optimization along Efficient Frontier'

outputs_dropdown1_label = 'Discount Rate at which Future Spending Liabilities = PV of Current Net Assets (%)'
outputs_dropdown2_label = 'Spending Flexibility of Liabilities (σ) using Goal Ranges & Monte Carlo (next page)'

outputs_chart_notes = 'Notes: *Nearest discrete portfolio; n=2,000; z-score = 1.65, equating to 95% probability of surplus value; time horizon = 5 years; correlation(assets, liabilities) = 1.0'

outputs_opt_title = 'Surplus Optimization on the Efficient Frontier'
outputs_opt_p1 = 'The mean liability and risk-adjusted surplus curves are plotted against a typical efficient frontier. This allows you to see, visually, where optimal surplus intersects with the efficient frontier--and therefore, identifies the optimal portfolio (i.e., optimal asset allocation).'
outputs_opt_p2 = 'The mean liability discount rate is the rate (i.e., the expected value, E(x)) at which future spending equals the current value of net assets. In other words, it is the return that would need to be generated in order to satisfy future liabilities (spending goals).'
outputs_opt_p3 = 'A full probability density function is traced out via Monte Carlo (details on next tab) to represent these future liabilities--which provides both this mean, but also the standard deviation of the discount rate that equates to future spending liabilities.'
outputs_opt_p4 = 'Using this probability distribution for future liabilities, we can then calculate a risk-adjusted surplus value that not only subtracts future spending from future asset returns, but also incorporates risk, which is mediated by the standard deviation of liabilities (i.e., spending flexibility), a correlation term of 1.0, and a z-score for surplus, which represents the probability threshold that surplus will equal at least zero (i.e., set to 0.95 or 0.99 certainty). These additional parameters are what create the dynamic shape (and importantly, the asymmetric risk profile) of both risk-adjusted surplus and the utility function calculations below. The risk-adjusted surplus computation is an extension of concepts developed by Sharpe and Tint (1990) and is described in detail in the accompanying research article.'
outputs_opt_p5 = 'The highest risk-adjusted surplus reflects the optimal portfolio, which takes into account both stochastic return and stochastic future liabilities in a single-period setting--inputs are ideally revised until optimal surplus equals zero at a prescribed z-score.'

outputs_utility_title = 'Implied (Idiosyncratic) Investor Utility Function'
outputs_utility_body = "After a model for risk-adjusted surplus was formulated, it eventually became apparent that it could be plotted against a simple arithmetic mean surplus value to arrive at a direct measure an investor's idiosyncratic utility function. In the author's opinion, this is an improved and more direct measure of utility, rather than typical, stylized approaches or approaches that infer utility based on a presumed value of its first derivative. The resulting utility function is very comparable to the shape of traditional, stylized utility functions once you disregard results that exceed the optimized surplus level. Interesting shape dynamics (i.e., convex, concave, kinked, etc.) can also be observed as assumptions are changed."

# ---------- Step 1: liability page ("/page-1") ----------

liability_header = 'Tracing the Liability Distribution'

liability_table_hint = '<-- These become the inputs that flow through to the first tab'

liability_horizon_title = 'Time Horizon Impacts on Efficient Frontier'
liability_horizon_body = 'The duration of liabilities is matched to the duration of the assets. In this case, we are using an equivalent total of 5 years for each. This has an important impact on the efficient frontier given an increased time horizon has the effect of increasing the probability of a positive outcome over the total period. This can be observed, visually, by the amount of observations that land above the point of zero returns as the time horizon increases (i.e., in the graph on the right). This is also an area where the model complexity could be increased in order to more realistically match time horizon effects. For example, a weighting of the dollar duration of liabilities might be more precise or even more interestingly, multi-period optimizations, such as dynamic programming. However, this paper focuses on the methodology of combining asset and liability returns rather than fine tuning the liability calculations. In addition, there has been substantial research in the fields of dynamic programming that could likely be applied to extend this model.'

liability_surface_notes = 'Notes: n=2,000; probability distribution of present value discount rate of liabilities based on annual cashflows and residual value above.'

liability_tracing_title = 'Tracing the Liability Probability Densities using Monte Carlo'
liability_tracing_body = 'The implied discount rate of the stated values above has a mean of ~.05 and a standard deviation of ~.06. These values were chosen for simplicity to illustrate that expected increases of .05 every year will clearly lead to an average expected return starting today of .05. The individual yearly standard deviations of .25 result in a combined standard deviation (relative to starting wealth) of .06 as stated. Correlation between assets and liabilities is set to 1.0 to reflect that an investor will increase or decrease future spending outlays based on actual asset returns. The probability distribution of the liability is traced out using Monte Carlo. The surface to the left reflects the fact that this distribution is constant across the efficient frontier. So while asset volatility fluctuates, liability volatility is constant across the range of the efficient frontier.'

# ---------- Step 2: efficient frontier page ("/page-2") ----------

ef_header = 'Efficient Frontier'

ef_markowitz_title = 'Markowitz Mean-Variance Analysis'
ef_markowitz_body = 'Using Monte Carlo to simulate random portfolio weights, this graph shows various risk and return combinations that can be achieved. They are shown here primarily to illustrate the starting point after which the liabilities and surplus are introduced. The investor could of course use their own desired asset return assumptions to represent the market portfolios available.'

ef_frontier_title = 'Efficient Frontier'
ef_frontier_body = 'This graph then shows the efficient frontier of possible returns, which "dominates" all others.'
