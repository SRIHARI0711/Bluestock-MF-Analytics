# 📈 Bonus Challenge B4 — Markowitz Efficient Frontier Portfolio Optimisation (+10 Marks)

## 📌 Overview
This module applies Modern Portfolio Theory (MPT) across 5 selected flagship mutual funds to identify the optimal risk-return tradeoff:
- **Simulation:** 50,000 Dirichlet Monte Carlo portfolio allocations.
- **Optimization:** Sequential Least Squares Programming (SLSQP) constrained optimization:
  - $\sum w_i = 1$ (Full investment)
  - $0 \le w_i \le 1$ (No short-selling)

---

## 🎯 Key Optimization Portfolios Identified

### 1. Maximum Sharpe Ratio (Tangency) Portfolio
- **Objective:** Maximizes $\frac{\mathbb{E}[R_p] - R_f}{\sigma_p}$ where $R_f = 6.5\%$.
- **Performance:** Expected Return = **24.2%**, Volatility = **8.8%**, **Sharpe Ratio = 2.01**.
- **Asset Allocation:**
  - **SBI Bluechip Fund:** 38.12%
  - **HDFC Mid-Cap Opportunities Fund:** 24.68%
  - **Axis Midcap Fund:** 20.07%
  - **DSP Small Cap Fund:** 17.13%
  - **HDFC Top 100 Fund:** 0.00%

### 2. Minimum Variance Portfolio
- **Objective:** Minimizes total portfolio variance $\mathbf{w}^T \mathbf{\Sigma} \mathbf{w}$.
- **Performance:** Expected Return = **18.3%**, Volatility = **7.5%**, **Sharpe Ratio = 1.57**.

---

## 🚀 Execution

```bash
python bonus_challenges/B4_markowitz_efficient_frontier/markowitz_efficient_frontier.py
```

---

## 📁 Artifacts Included in this Folder
- [`markowitz_efficient_frontier.py`](file:///bonus_challenges/B4_markowitz_efficient_frontier/markowitz_efficient_frontier.py): Standalone portfolio optimization script.
- [`markowitz_efficient_frontier.png`](file:///bonus_challenges/B4_markowitz_efficient_frontier/markowitz_efficient_frontier.png): Efficient Frontier scatter plot with color-coded Sharpe ratios, individual fund markers, Tangency portfolio (*), Minimum Variance portfolio (P), and Capital Market Line (CML).
- [`markowitz_portfolio_weights.csv`](file:///bonus_challenges/B4_markowitz_efficient_frontier/markowitz_portfolio_weights.csv): Optimal portfolio asset allocation weights table.
