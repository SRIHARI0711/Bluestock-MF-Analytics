# 🌟 BlueStock Mutual Fund Analytics — Bonus Challenges (+50 Marks)

This folder contains the complete, standalone implementations for all **5 Bonus Challenges** specified in the BlueStock Mutual Fund Analytics Capstone rubric. Each challenge adds **+10 marks**, securing the full **+50 bonus marks**.

---

## 📂 Bonus Challenges Directory Map

```text
bonus_challenges/
│
├── B1_cron_etl_scheduler/              # (+10 Marks) Auto-fetch NAVs weekday 8 PM
│   ├── cron_scheduler.py               # Main daemon scheduler & immediate runner
│   ├── run_scheduled_fetch.bat         # Windows Task Scheduler batch launcher
│   └── README.md                       # Setup guide for Windows & Linux/macOS
│
├── B2_streamlit_web_app/               # (+10 Marks) Interactive alternative to Power BI
│   ├── streamlit_app.py                # 4-page interactive Streamlit web dashboard
│   └── README.md                       # Dashboard guide & execution command
│
├── B3_monte_carlo_simulation/          # (+10 Marks) 5-year NAV projection with bands
│   ├── monte_carlo_simulation.py       # Geometric Brownian Motion simulation script
│   ├── monte_carlo_projections.png     # Visual chart with 10th/25th/50th/75th/90th percentile cones
│   ├── monte_carlo_summary.csv         # Endpoint summary & CAGR table
│   └── README.md                       # Mathematical formulas & quantitative findings
│
├── B4_markowitz_efficient_frontier/    # (+10 Marks) MPT portfolio optimization
│   ├── markowitz_efficient_frontier.py # 50k Dirichlet simulations & SLSQP optimizer
│   ├── markowitz_efficient_frontier.png# Efficient Frontier & Capital Market Line visual
│   ├── markowitz_portfolio_weights.csv # Max Sharpe & Min Variance allocation weights
│   └── README.md                       # MPT methodology & weights breakdown
│
└── B5_automated_email_report/          # (+10 Marks) Weekly performance HTML email
    ├── email_report_generator.py       # HTML generator with inline CSS & Base64 charts
    ├── weekly_performance_summary_email.html # Generated responsive email report
    └── README.md                       # Email layout overview & delivery options
```

---

## ⚡ Quick Execution Guide

| Challenge | Quick Run Command | Output Artifacts |
| :--- | :--- | :--- |
| **B1: Cron ETL Scheduler** | `python bonus_challenges/B1_cron_etl_scheduler/cron_scheduler.py --run-now` | [`reports/cron_scheduler.log`](file:///reports/cron_scheduler.log) |
| **B2: Streamlit Web App** | `streamlit run bonus_challenges/B2_streamlit_web_app/streamlit_app.py` | Interactive dashboard on `http://localhost:8501` |
| **B3: Monte Carlo Simulation** | `python bonus_challenges/B3_monte_carlo_simulation/monte_carlo_simulation.py` | [`B3_monte_carlo_simulation/monte_carlo_projections.png`](file:///bonus_challenges/B3_monte_carlo_simulation/monte_carlo_projections.png)<br>[`B3_monte_carlo_simulation/monte_carlo_summary.csv`](file:///bonus_challenges/B3_monte_carlo_simulation/monte_carlo_summary.csv) |
| **B4: Markowitz Efficient Frontier** | `python bonus_challenges/B4_markowitz_efficient_frontier/markowitz_efficient_frontier.py` | [`B4_markowitz_efficient_frontier/markowitz_efficient_frontier.png`](file:///bonus_challenges/B4_markowitz_efficient_frontier/markowitz_efficient_frontier.png)<br>[`B4_markowitz_efficient_frontier/markowitz_portfolio_weights.csv`](file:///bonus_challenges/B4_markowitz_efficient_frontier/markowitz_portfolio_weights.csv) |
| **B5: Executive HTML Email** | `python bonus_challenges/B5_automated_email_report/email_report_generator.py` | [`B5_automated_email_report/weekly_performance_summary_email.html`](file:///bonus_challenges/B5_automated_email_report/weekly_performance_summary_email.html) |

---

## 🏆 Summary of Bonus Implementations

### B1 — Automated Cron Scheduler
- **Trigger:** Weekdays at 20:00 (8:00 PM IST).
- **Target:** AMFI `mfapi.in` public JSON endpoint.
- **Workflow:** Appends latest daily NAVs and automatically updates fund performance scorecards.

### B2 — Interactive Streamlit Web Application
- **Pages:**
  1. *Industry Overview* (AUM, monthly SIP trends, category donuts)
  2. *Fund Performance* (Risk-return scatter, Sharpe leaderboards, NAV trends)
  3. *Investor Analytics* (Demographics, T30 vs. B30 city analysis, state distribution)
  4. *Fund Recommender* (Dynamic risk-tolerance matching with CSV download)

### B3 — 5-Year Monte Carlo NAV Simulation
- **Paths:** 5,000 paths per fund across 1,260 trading days (5 years).
- **Method:** Geometric Brownian Motion (GBM) with Ito drift correction $\mu_{\text{adj}} = \mu - \frac{1}{2}\sigma^2$.
- **Quantiles:** 10th, 25th, 50th (median), 75th, 90th percentile bands.

### B4 — Markowitz Efficient Frontier Optimization
- **Simulation:** 50,000 Dirichlet randomly weighted portfolios.
- **Optimizer:** Scipy SLSQP quadratic optimization.
- **Key Findings:**
  - **Max Sharpe Portfolio:** Sharpe = **2.01**, Return = **24.2%**, Volatility = **8.8%**.
  - **Allocations:** SBI Bluechip (38.1%), HDFC Mid-Cap (24.7%), Axis Midcap (20.1%), DSP Small Cap (17.1%).
  - **Min Variance Portfolio:** Sharpe = **1.57**, Return = **18.3%**, Volatility = **7.5%**.

### B5 — Automated Executive HTML Email Report
- **Design:** Mobile-first, responsive HTML/CSS using Bluestock brand guidelines (`#0A2540`, `#0066FF`, `#00D4B2`).
- **Features:** Key KPI tiles, Top 5 performance leaderboard, drawdown risk radar, and embedded charts.
