#!/usr/bin/env python3
"""
Bonus Challenge B4: Markowitz Efficient Frontier Portfolio Optimisation
========================================================================
Constructs the Markowitz Efficient Frontier for 5 selected equity funds,
identifies the Maximum Sharpe Ratio (Tangency) and Minimum Variance (MV)
portfolios via Monte Carlo Dirichlet simulation and SLSQP optimization.

Usage:
  python bonus_challenges/B4_markowitz_efficient_frontier/markowitz_efficient_frontier.py
"""

from pathlib import Path
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.optimize import minimize

warnings.filterwarnings("ignore")

# ─── Path Resolution ──────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parents[1]
if not (BASE_DIR / "data").exists():
    for p in Path(__file__).resolve().parents:
        if (p / "data").exists():
            BASE_DIR = p
            break

PROCESSED = BASE_DIR / "data" / "processed"
REPORTS = BASE_DIR / "reports"
REPORTS.mkdir(parents=True, exist_ok=True)

RISK_FREE_RATE = 0.065       # 6.5% annual
TRADING_DAYS = 252

FRONTIER_FUNDS = [
    "HDFC Top 100 Fund - Regular Plan - Growth",
    "HDFC Mid-Cap Opportunities Fund - Regular - Growth",
    "SBI Bluechip Fund - Regular Plan - Growth",
    "DSP Small Cap Fund - Regular - Growth",
    "Axis Midcap Fund - Regular - Growth",
]


def load_nav_pivoted(funds_filter=None):
    nav = pd.read_csv(PROCESSED / "clean_nav_history.csv", parse_dates=["date"])
    master = pd.read_csv(PROCESSED / "clean_fund_master.csv")
    master["amfi_code"] = master["amfi_code"].astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
    nav["amfi_code"] = nav["amfi_code"].astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
    nav = nav.merge(master[["amfi_code", "scheme_name"]], on="amfi_code", how="left")
    nav = nav.dropna(subset=["scheme_name"])
    if funds_filter:
        nav = nav[nav["scheme_name"].isin(funds_filter)]
    pivot = (nav.sort_values("date")
                .pivot_table(index="date", columns="scheme_name", values="nav", aggfunc="last"))
    pivot.columns.name = None
    pivot = pivot.ffill().dropna()
    return pivot


def run_markowitz_frontier():
    print("=" * 70)
    print("BONUS B4 — MARKOWITZ EFFICIENT FRONTIER (5 FUNDS, 50K SIMULATIONS)")
    print("=" * 70)

    pivot = load_nav_pivoted(funds_filter=FRONTIER_FUNDS)
    available = [f for f in FRONTIER_FUNDS if f in pivot.columns]
    if len(available) < 2:
        print("Using top-5 funds by history length.")
        nav_all = pd.read_csv(PROCESSED / "clean_nav_history.csv", parse_dates=["date"])
        master = pd.read_csv(PROCESSED / "clean_fund_master.csv")
        master["amfi_code"] = master["amfi_code"].astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
        nav_all["amfi_code"] = nav_all["amfi_code"].astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
        nav_all = nav_all.merge(master[["amfi_code", "scheme_name"]], on="amfi_code", how="left")
        top5 = (nav_all.groupby("scheme_name")["date"].count()
                .sort_values(ascending=False).head(5).index.tolist())
        pivot = load_nav_pivoted(funds_filter=top5)
        available = pivot.columns.tolist()

    pivot = pivot[available].copy()
    print(f"Funds analyzed: {available}")

    log_rets = np.log(pivot / pivot.shift(1)).dropna()
    mu_daily = log_rets.mean().values
    cov_daily = log_rets.cov().values
    n_assets = len(available)

    mu_ann = mu_daily * TRADING_DAYS
    cov_ann = cov_daily * TRADING_DAYS
    rf = RISK_FREE_RATE

    # 50,000 Dirichlet simulations
    N_MC = 50_000
    rng = np.random.default_rng(seed=0)
    weights_mc = rng.dirichlet(np.ones(n_assets), size=N_MC)

    port_ret = weights_mc @ mu_ann
    port_var = np.einsum("ij,jk,ik->i", weights_mc, cov_ann, weights_mc)
    port_vol = np.sqrt(port_var)
    sharpe_mc = (port_ret - rf) / port_vol

    # Maximum Sharpe Ratio Optimization
    def neg_sharpe(w):
        r = w @ mu_ann
        v = np.sqrt(w @ cov_ann @ w)
        return -(r - rf) / v

    cons = {"type": "eq", "fun": lambda w: w.sum() - 1}
    bnds = [(0.0, 1.0)] * n_assets
    w0 = np.ones(n_assets) / n_assets

    msr_res = minimize(neg_sharpe, w0, method="SLSQP", bounds=bnds, constraints=cons,
                       options={"ftol": 1e-10, "maxiter": 1000})
    w_msr = msr_res.x
    msr_ret = w_msr @ mu_ann
    msr_vol = np.sqrt(w_msr @ cov_ann @ w_msr)
    msr_sr = (msr_ret - rf) / msr_vol

    # Minimum Variance Optimization
    def port_variance(w):
        return w @ cov_ann @ w

    mv_res = minimize(port_variance, w0, method="SLSQP", bounds=bnds, constraints=cons,
                      options={"ftol": 1e-10, "maxiter": 1000})
    w_mv = mv_res.x
    mv_ret = w_mv @ mu_ann
    mv_vol = np.sqrt(w_mv @ cov_ann @ w_mv)
    mv_sr = (mv_ret - rf) / mv_vol

    # Plotting
    fig, ax = plt.subplots(figsize=(12, 7))
    sc = ax.scatter(port_vol * 100, port_ret * 100, c=sharpe_mc,
                    cmap="viridis", alpha=0.4, s=6, zorder=1)
    plt.colorbar(sc, ax=ax, label="Sharpe Ratio")

    for i, name in enumerate(available):
        a_ret = mu_ann[i]
        a_vol = np.sqrt(cov_ann[i, i])
        ax.scatter(a_vol * 100, a_ret * 100, s=120, zorder=5, marker="D",
                   color="#EF4444", edgecolors="black", lw=0.8)
        ax.annotate(name[:25], (a_vol * 100, a_ret * 100),
                    textcoords="offset points", xytext=(6, 4), fontsize=7.5)

    ax.scatter(msr_vol * 100, msr_ret * 100, s=260, marker="*",
               color="#F59E0B", edgecolors="black", lw=1, zorder=6, label=f"Max Sharpe (SR={msr_sr:.2f})")
    ax.scatter(mv_vol * 100, mv_ret * 100, s=200, marker="P",
               color="#00D4B2", edgecolors="black", lw=1, zorder=6, label=f"Min Variance (SR={mv_sr:.2f})")

    vol_range = np.linspace(0, port_vol.max() * 1.1 * 100, 200)
    cml_ret = rf * 100 + (msr_sr) * vol_range
    ax.plot(vol_range, cml_ret, color="#0A2540", lw=1.5, ls="--",
            label=f"Capital Market Line (Rf={rf:.1%})", zorder=4)

    ax.set_title("Markowitz Efficient Frontier & Capital Market Line (BlueStock MF Analytics)",
                 fontsize=13, fontweight="bold")
    ax.set_xlabel("Annualised Volatility σ (%)")
    ax.set_ylabel("Expected Annualised Return μ (%)")
    ax.set_xlim(0, port_vol.max() * 1.15 * 100)
    ax.set_ylim(rf * 100 * 0.8, max(port_ret.max() * 100, msr_ret * 100) * 1.15)
    ax.legend(loc="upper left", fontsize=9)
    ax.grid(alpha=0.3)

    plt.tight_layout()
    fig.savefig(SCRIPT_DIR / "markowitz_efficient_frontier.png", dpi=150, bbox_inches="tight")
    fig.savefig(REPORTS / "markowitz_efficient_frontier.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

    weights_df = pd.DataFrame({
        "scheme_name": available,
        "max_sharpe_weight_pct": [round(w * 100, 2) for w in w_msr],
        "min_variance_weight_pct": [round(w * 100, 2) for w in w_mv],
    })
    weights_df.to_csv(SCRIPT_DIR / "markowitz_portfolio_weights.csv", index=False)
    weights_df.to_csv(REPORTS / "markowitz_portfolio_weights.csv", index=False)

    print(f" Saved figure: {SCRIPT_DIR / 'markowitz_efficient_frontier.png'}")
    print(f" Saved weights CSV: {SCRIPT_DIR / 'markowitz_portfolio_weights.csv'}")
    print("\nOptimal Portfolio Allocations:")
    print(weights_df.to_string(index=False))


if __name__ == "__main__":
    run_markowitz_frontier()
