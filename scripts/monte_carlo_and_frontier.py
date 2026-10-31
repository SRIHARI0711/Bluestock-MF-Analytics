#!/usr/bin/env python3
"""
Bonus B3: Monte Carlo NAV Projection (5-Year Simulation)
=========================================================
Simulates 5-year NAV trajectories for selected funds using
Geometric Brownian Motion calibrated to historical log-return
statistics (μ, σ). Plots 10th/25th/75th/90th percentile uncertainty bands.

Bonus B4: Markowitz Efficient Frontier Portfolio Optimisation
=============================================================
Constructs the Markowitz Efficient Frontier for 5 selected equity funds,
identifies the Maximum Sharpe Ratio (MSR) and Minimum Variance (MV)
portfolios via Monte Carlo simulation of random weight allocations.
"""

from pathlib import Path
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from scipy.optimize import minimize

warnings.filterwarnings("ignore")

# ─── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR  = Path(__file__).resolve().parent.parent
PROCESSED = BASE_DIR / "data" / "processed"
REPORTS   = BASE_DIR / "reports"
REPORTS.mkdir(parents=True, exist_ok=True)

RISK_FREE_RATE   = 0.065       # 6.5% annual
TRADING_DAYS     = 252
PROJECTION_YEARS = 5
N_SIMULATIONS    = 5_000       # Monte Carlo paths per fund

# ─── 5 representative equity funds for Frontier ───────────────────────────────
FRONTIER_FUNDS = [
    "HDFC Top 100 Fund - Regular Plan - Growth",
    "HDFC Mid-Cap Opportunities Fund - Regular - Growth",
    "SBI Bluechip Fund - Regular Plan - Growth",
    "DSP Small Cap Fund - Regular - Growth",
    "Axis Midcap Fund - Regular - Growth",
]

# ─────────────────────────────────────────────────────────────────────────────
# SHARED: load & pivot NAV data
# ─────────────────────────────────────────────────────────────────────────────
def load_nav_pivoted(funds_filter=None):
    nav = pd.read_csv(PROCESSED / "clean_nav_history.csv", parse_dates=["date"])
    master = pd.read_csv(PROCESSED / "clean_fund_master.csv")
    master["amfi_code"] = master["amfi_code"].astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
    nav["amfi_code"]    = nav["amfi_code"].astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
    nav = nav.merge(master[["amfi_code", "scheme_name"]], on="amfi_code", how="left")
    nav = nav.dropna(subset=["scheme_name"])
    if funds_filter:
        nav = nav[nav["scheme_name"].isin(funds_filter)]
    pivot = (nav.sort_values("date")
                .pivot_table(index="date", columns="scheme_name", values="nav", aggfunc="last"))
    pivot.columns.name = None
    pivot = pivot.ffill().dropna()
    return pivot


# ═════════════════════════════════════════════════════════════════════════════
# BONUS B3 — MONTE CARLO NAV PROJECTION
# ═════════════════════════════════════════════════════════════════════════════
def run_monte_carlo():
    print("=" * 70)
    print("BONUS B3 — MONTE CARLO NAV PROJECTION (5-YEAR GBM SIMULATION)")
    print("=" * 70)

    nav_all = pd.read_csv(PROCESSED / "clean_nav_history.csv", parse_dates=["date"])
    master  = pd.read_csv(PROCESSED / "clean_fund_master.csv")
    master["amfi_code"] = master["amfi_code"].astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
    nav_all["amfi_code"] = nav_all["amfi_code"].astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
    nav_all = nav_all.merge(master[["amfi_code", "scheme_name"]], on="amfi_code", how="left")

    # Pick 5 funds with longest history
    top_funds = (nav_all.groupby("scheme_name")["date"]
                 .count()
                 .sort_values(ascending=False)
                 .head(5)
                 .index.tolist())

    n_funds   = len(top_funds)
    fig, axes = plt.subplots(n_funds, 1, figsize=(14, 4 * n_funds))
    if n_funds == 1:
        axes = [axes]
    fig.suptitle("Bluestock MF Analytics — Monte Carlo NAV Projections (5 Years, 5,000 Paths)",
                 fontsize=14, fontweight="bold", y=1.01)

    mc_summary = []
    horizon_days = PROJECTION_YEARS * TRADING_DAYS

    for ax, fund_name in zip(axes, top_funds):
        series = (nav_all[nav_all["scheme_name"] == fund_name]
                  .sort_values("date")
                  .set_index("date")["nav"]
                  .dropna())

        log_rets = np.log(series / series.shift(1)).dropna()
        mu_daily  = log_rets.mean()
        sig_daily = log_rets.std(ddof=1)

        # Annualised estimates
        mu_ann  = mu_daily  * TRADING_DAYS
        sig_ann = sig_daily * np.sqrt(TRADING_DAYS)

        # GBM drift correction: μ_adj = μ - σ²/2  (ensures E[S_T] = S_0 * e^(μT))
        mu_adj = mu_daily - 0.5 * sig_daily ** 2

        S0 = float(series.iloc[-1])
        dt = 1  # 1 trading day

        rng = np.random.default_rng(seed=42)
        Z   = rng.standard_normal((horizon_days, N_SIMULATIONS))
        # Cumulative log-return path
        log_paths  = np.cumsum(mu_adj * dt + sig_daily * np.sqrt(dt) * Z, axis=0)
        price_paths = S0 * np.exp(log_paths)

        # Percentile bands
        p10 = np.percentile(price_paths, 10, axis=1)
        p25 = np.percentile(price_paths, 25, axis=1)
        p50 = np.percentile(price_paths, 50, axis=1)
        p75 = np.percentile(price_paths, 75, axis=1)
        p90 = np.percentile(price_paths, 90, axis=1)

        t = np.arange(1, horizon_days + 1) / TRADING_DAYS  # years

        ax.fill_between(t, p10, p90, alpha=0.15, color="#0066FF", label="10–90th pct")
        ax.fill_between(t, p25, p75, alpha=0.25, color="#0066FF", label="25–75th pct")
        ax.plot(t, p50, color="#0066FF", lw=2, label="Median")
        ax.axhline(S0, color="#EF4444", lw=1.2, ls="--", label=f"Current NAV ₹{S0:.1f}")
        ax.set_title(f"{fund_name[:60]}  |  μ={mu_ann:.1%}  σ={sig_ann:.1%}", fontsize=10, fontweight="bold")
        ax.set_xlabel("Years from Today")
        ax.set_ylabel("NAV (₹)")
        ax.legend(loc="upper left", fontsize=8)
        ax.grid(alpha=0.3)

        # CAGR at median endpoint
        median_end = float(p50[-1])
        cagr_median = (median_end / S0) ** (1 / PROJECTION_YEARS) - 1
        mc_summary.append({
            "scheme_name": fund_name,
            "current_nav": round(S0, 2),
            "mu_ann_pct":  round(mu_ann * 100, 2),
            "sigma_ann_pct": round(sig_ann * 100, 2),
            "median_5yr_nav": round(median_end, 2),
            "p10_5yr_nav":    round(float(p10[-1]), 2),
            "p90_5yr_nav":    round(float(p90[-1]), 2),
            "median_cagr_pct": round(cagr_median * 100, 2),
        })

    plt.tight_layout()
    out_fig = REPORTS / "monte_carlo_projections.png"
    fig.savefig(out_fig, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved Monte Carlo chart -> {out_fig.name}")

    mc_df = pd.DataFrame(mc_summary)
    mc_df.to_csv(REPORTS / "monte_carlo_summary.csv", index=False)
    print("\nMonte Carlo 5-Year Projections Summary:")
    print(mc_df.to_string(index=False))
    return mc_df


# ═════════════════════════════════════════════════════════════════════════════
# BONUS B4 — MARKOWITZ EFFICIENT FRONTIER
# ═════════════════════════════════════════════════════════════════════════════
def run_markowitz_frontier():
    print("\n" + "=" * 70)
    print("BONUS B4 — MARKOWITZ EFFICIENT FRONTIER (5 FUNDS, 50K SIMULATIONS)")
    print("=" * 70)

    pivot = load_nav_pivoted(funds_filter=FRONTIER_FUNDS)

    # Use whichever frontier funds are actually available
    available = [f for f in FRONTIER_FUNDS if f in pivot.columns]
    if len(available) < 2:
        print("Not enough frontier funds available. Using top-5 by data length.")
        nav_all = pd.read_csv(PROCESSED / "clean_nav_history.csv", parse_dates=["date"])
        master  = pd.read_csv(PROCESSED / "clean_fund_master.csv")
        master["amfi_code"] = master["amfi_code"].astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
        nav_all["amfi_code"] = nav_all["amfi_code"].astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
        nav_all = nav_all.merge(master[["amfi_code", "scheme_name"]], on="amfi_code", how="left")
        top5 = (nav_all.groupby("scheme_name")["date"].count()
                .sort_values(ascending=False).head(5).index.tolist())
        pivot = load_nav_pivoted(funds_filter=top5)
        available = pivot.columns.tolist()

    pivot = pivot[available].copy()
    print(f"Using funds: {available}")

    # Daily log-returns
    log_rets = np.log(pivot / pivot.shift(1)).dropna()
    mu_daily  = log_rets.mean().values
    cov_daily = log_rets.cov().values
    n_assets  = len(available)

    # Annualise
    mu_ann  = mu_daily  * TRADING_DAYS
    cov_ann = cov_daily * TRADING_DAYS
    rf      = RISK_FREE_RATE

    # ── Monte Carlo Random Portfolios ──
    N_MC  = 50_000
    rng   = np.random.default_rng(seed=0)
    weights_mc = rng.dirichlet(np.ones(n_assets), size=N_MC)

    port_ret = weights_mc @ mu_ann
    port_var = np.einsum("ij,jk,ik->i", weights_mc, cov_ann, weights_mc)
    port_vol = np.sqrt(port_var)
    sharpe_mc = (port_ret - rf) / port_vol

    # ── Optimise: Maximum Sharpe Ratio ──
    def neg_sharpe(w):
        r = w @ mu_ann
        v = np.sqrt(w @ cov_ann @ w)
        return -(r - rf) / v

    cons = {"type": "eq", "fun": lambda w: w.sum() - 1}
    bnds = [(0.0, 1.0)] * n_assets
    w0   = np.ones(n_assets) / n_assets

    msr_res = minimize(neg_sharpe, w0, method="SLSQP", bounds=bnds, constraints=cons,
                       options={"ftol": 1e-10, "maxiter": 1000})
    w_msr   = msr_res.x
    msr_ret = w_msr @ mu_ann
    msr_vol = np.sqrt(w_msr @ cov_ann @ w_msr)
    msr_sr  = (msr_ret - rf) / msr_vol

    # ── Optimise: Minimum Variance ──
    def port_variance(w):
        return w @ cov_ann @ w

    mv_res = minimize(port_variance, w0, method="SLSQP", bounds=bnds, constraints=cons,
                      options={"ftol": 1e-10, "maxiter": 1000})
    w_mv   = mv_res.x
    mv_ret = w_mv @ mu_ann
    mv_vol = np.sqrt(w_mv @ cov_ann @ w_mv)
    mv_sr  = (mv_ret - rf) / mv_vol

    # ── Plot ──
    fig, ax = plt.subplots(figsize=(12, 7))
    sc = ax.scatter(port_vol * 100, port_ret * 100, c=sharpe_mc,
                    cmap="viridis", alpha=0.4, s=6, zorder=1)
    plt.colorbar(sc, ax=ax, label="Sharpe Ratio")

    # Individual assets
    for i, name in enumerate(available):
        a_ret = mu_ann[i]
        a_vol = np.sqrt(cov_ann[i, i])
        ax.scatter(a_vol * 100, a_ret * 100, s=120, zorder=5, marker="D",
                   color="#EF4444", edgecolors="black", lw=0.8)
        ax.annotate(name[:25], (a_vol * 100, a_ret * 100),
                    textcoords="offset points", xytext=(6, 4), fontsize=7.5)

    # MSR portfolio
    ax.scatter(msr_vol * 100, msr_ret * 100, s=260, marker="*",
               color="#F59E0B", edgecolors="black", lw=1, zorder=6, label=f"Max Sharpe (SR={msr_sr:.2f})")
    # MV portfolio
    ax.scatter(mv_vol * 100, mv_ret * 100, s=200, marker="P",
               color="#00D4B2", edgecolors="black", lw=1, zorder=6, label=f"Min Variance (SR={mv_sr:.2f})")

    # Capital Market Line
    vol_range = np.linspace(0, port_vol.max() * 1.1 * 100, 200)
    cml_ret   = rf * 100 + (msr_sr) * vol_range
    ax.plot(vol_range, cml_ret, "k--", lw=1.5, alpha=0.6, label="Capital Market Line")

    ax.set_xlabel("Annualized Volatility (%)", fontsize=12)
    ax.set_ylabel("Annualized Return (%)", fontsize=12)
    ax.set_title("Markowitz Efficient Frontier - Bluestock MF Analytics (B4)", fontsize=14, fontweight="bold")
    ax.legend(fontsize=10)
    ax.grid(alpha=0.3)

    out_fig = REPORTS / "markowitz_efficient_frontier.png"
    fig.savefig(out_fig, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved Efficient Frontier chart -> {out_fig.name}")

    # ── Weights Table ──
    weights_df = pd.DataFrame({
        "Fund": available,
        "MSR Weight (%)": (w_msr * 100).round(2),
        "MV Weight (%)":  (w_mv  * 100).round(2),
    })
    weights_df.to_csv(REPORTS / "markowitz_portfolio_weights.csv", index=False)

    print(f"\nMaximum Sharpe Ratio Portfolio:  Return={msr_ret:.1%}  Vol={msr_vol:.1%}  Sharpe={msr_sr:.2f}")
    print(f"Minimum Variance Portfolio:      Return={mv_ret:.1%}   Vol={mv_vol:.1%}  Sharpe={mv_sr:.2f}")
    print("\nPortfolio Weights:")
    print(weights_df.to_string(index=False))
    return weights_df


if __name__ == "__main__":
    mc_results  = run_monte_carlo()
    mf_weights  = run_markowitz_frontier()
    print("\n[SUCCESS] Bonus B3 (Monte Carlo) and B4 (Markowitz Frontier) complete.")
