#!/usr/bin/env python3
"""
Bonus Challenge B3: Monte Carlo NAV Projection (5-Year Simulation)
==================================================================
Simulates 5-year NAV trajectories for top mutual funds using
Geometric Brownian Motion (GBM) calibrated to historical log-return
statistics (μ, σ). Plots 10th, 25th, 50th (median), 75th, and 90th
percentile uncertainty bands.

Usage:
  python bonus_challenges/B3_monte_carlo_simulation/monte_carlo_simulation.py
"""

from pathlib import Path
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

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
PROJECTION_YEARS = 5
N_SIMULATIONS = 5_000        # Monte Carlo paths per fund


def run_monte_carlo():
    print("=" * 70)
    print("BONUS B3 — MONTE CARLO NAV PROJECTION (5-YEAR GBM SIMULATION)")
    print("=" * 70)

    nav_all = pd.read_csv(PROCESSED / "clean_nav_history.csv", parse_dates=["date"])
    master = pd.read_csv(PROCESSED / "clean_fund_master.csv")
    master["amfi_code"] = master["amfi_code"].astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
    nav_all["amfi_code"] = nav_all["amfi_code"].astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
    nav_all = nav_all.merge(master[["amfi_code", "scheme_name"]], on="amfi_code", how="left")

    # Pick 5 funds with longest history
    top_funds = (nav_all.groupby("scheme_name")["date"]
                 .count()
                 .sort_values(ascending=False)
                 .head(5)
                 .index.tolist())

    n_funds = len(top_funds)
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
        mu_daily = log_rets.mean()
        sig_daily = log_rets.std(ddof=1)

        # Annualised estimates
        mu_ann = mu_daily * TRADING_DAYS
        sig_ann = sig_daily * np.sqrt(TRADING_DAYS)

        # GBM drift correction: μ_adj = μ - σ²/2 (ensures E[S_T] = S_0 * e^(μT))
        mu_adj = mu_daily - 0.5 * sig_daily ** 2

        S0 = float(series.iloc[-1])
        dt = 1  # 1 trading day

        rng = np.random.default_rng(seed=42)
        Z = rng.standard_normal((horizon_days, N_SIMULATIONS))
        log_paths = np.cumsum(mu_adj * dt + sig_daily * np.sqrt(dt) * Z, axis=0)
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

        median_end = float(p50[-1])
        cagr_median = (median_end / S0) ** (1 / PROJECTION_YEARS) - 1
        mc_summary.append({
            "scheme_name": fund_name,
            "current_nav": round(S0, 2),
            "mu_ann_pct": round(mu_ann * 100, 2),
            "sigma_ann_pct": round(sig_ann * 100, 2),
            "median_5yr_nav": round(median_end, 2),
            "p10_5yr_nav": round(float(p10[-1]), 2),
            "p90_5yr_nav": round(float(p90[-1]), 2),
            "median_cagr_pct": round(cagr_median * 100, 2),
        })

    plt.tight_layout()
    # Save to both this folder and reports directory
    fig.savefig(SCRIPT_DIR / "monte_carlo_projections.png", dpi=150, bbox_inches="tight")
    fig.savefig(REPORTS / "monte_carlo_projections.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

    summary_df = pd.DataFrame(mc_summary)
    summary_df.to_csv(SCRIPT_DIR / "monte_carlo_summary.csv", index=False)
    summary_df.to_csv(REPORTS / "monte_carlo_summary.csv", index=False)

    print(f" Saved figure: {SCRIPT_DIR / 'monte_carlo_projections.png'}")
    print(f" Saved summary CSV: {SCRIPT_DIR / 'monte_carlo_summary.csv'}")
    print(summary_df.to_string(index=False))


if __name__ == "__main__":
    run_monte_carlo()
