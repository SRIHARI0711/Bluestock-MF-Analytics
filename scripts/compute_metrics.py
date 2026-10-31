#!/usr/bin/env python3
"""
Bluestock Mutual Fund Analytics — Performance & Risk Metrics Engine
====================================================================
Computes quantitative performance metrics across all funds:
- Annualized CAGR using trading days (252 / n_trading_days)
- Annualized Standard Deviation (volatility)
- Sharpe Ratio (Rf = 6.5%)
- Downside Deviation & Sortino Ratio
- Maximum Drawdown (MDD)
- Alpha & Beta via OLS regression against Nifty 50 benchmark
- Historical Value at Risk (VaR 95%, 99%) & Conditional VaR (CVaR / Expected Shortfall)

Generates:
1. reports/fund_scorecard.csv & data/processed/fund_scorecard.csv
2. reports/alpha_beta.csv & data/processed/alpha_beta.csv
3. reports/var_cvar_report.csv & data/processed/var_cvar_report.csv
"""

from pathlib import Path
import warnings
import numpy as np
import pandas as pd
from scipy import stats

warnings.filterwarnings("ignore")

# Define paths using pathlib
BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"
REPORTS_DIR = BASE_DIR / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

RISK_FREE_RATE = 0.065  # 6.5% annual risk-free rate (RBI 91-day T-bill reference)
TRADING_DAYS_PER_YEAR = 252


def compute_metrics():
    print("=" * 80)
    print("BLUESTOCK MF ANALYTICS — PERFORMANCE & RISK METRICS CALCULATION")
    print("=" * 80)

    # 1. Load Cleaned Datasets
    fund_master_path = PROCESSED_DIR / "clean_fund_master.csv"
    nav_history_path = PROCESSED_DIR / "clean_nav_history.csv"
    benchmark_path = PROCESSED_DIR / "clean_benchmark_indices.csv"
    perf_path = PROCESSED_DIR / "clean_scheme_performance.csv"

    if not nav_history_path.exists():
        raise FileNotFoundError(f"NAV history not found: {nav_history_path}")

    funds_df = pd.read_csv(fund_master_path) if fund_master_path.exists() else pd.DataFrame()
    nav_df = pd.read_csv(nav_history_path)
    benchmark_df = pd.read_csv(benchmark_path) if benchmark_path.exists() else pd.DataFrame()
    orig_perf_df = pd.read_csv(perf_path) if perf_path.exists() else pd.DataFrame()

    nav_df["date"] = pd.to_datetime(nav_df["date"])
    nav_df["amfi_code"] = nav_df["amfi_code"].astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
    nav_df = nav_df.sort_values(["amfi_code", "date"]).reset_index(drop=True)

    # Prepare Benchmark (Nifty 50)
    bench_returns = None
    if not benchmark_df.empty and "date" in benchmark_df.columns:
        benchmark_df["date"] = pd.to_datetime(benchmark_df["date"])
        # Find nifty 50 or broad market column
        nifty_col = None
        for col in ["nifty_50", "NIFTY 50", "nifty50", "Nifty 50", "close", "nav"]:
            if col in benchmark_df.columns:
                nifty_col = col
                break
        if nifty_col is None:
            # pick first numeric column
            num_cols = benchmark_df.select_dtypes(include=[np.number]).columns
            if len(num_cols) > 0:
                nifty_col = num_cols[0]

        if nifty_col:
            bench_clean = benchmark_df[["date", nifty_col]].dropna().sort_values("date")
            bench_clean = bench_clean.drop_duplicates(subset=["date"])
            bench_clean["bench_ret"] = bench_clean[nifty_col].pct_change()
            bench_returns = bench_clean.set_index("date")["bench_ret"]

    # Fund Master lookup map
    scheme_info = {}
    if not funds_df.empty and "amfi_code" in funds_df.columns:
        funds_df["amfi_code"] = funds_df["amfi_code"].astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
        for _, row in funds_df.iterrows():
            scheme_info[row["amfi_code"]] = {
                "scheme_name": row.get("scheme_name", "Unknown Scheme"),
                "fund_house": row.get("fund_house", "Unknown AMC"),
                "category": row.get("category", "Equity"),
                "sub_category": row.get("sub_category", "Large Cap"),
                "expense_ratio_pct": row.get("expense_ratio_pct", np.nan),
            }

    # Scheme performance existing metadata map (for AUM, ratings)
    perf_info = {}
    if not orig_perf_df.empty and "amfi_code" in orig_perf_df.columns:
        orig_perf_df["amfi_code"] = orig_perf_df["amfi_code"].astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
        for _, row in orig_perf_df.iterrows():
            perf_info[row["amfi_code"]] = {
                "aum_crore": row.get("aum_crore", np.nan),
                "morningstar_rating": row.get("morningstar_rating", np.nan),
                "risk_grade": row.get("risk_grade", "Moderate"),
            }

    scorecard_list = []
    alpha_beta_list = []
    var_cvar_list = []

    daily_rf = (1 + RISK_FREE_RATE) ** (1 / TRADING_DAYS_PER_YEAR) - 1

    for amfi_code, group in nav_df.groupby("amfi_code"):
        group = group.sort_values("date").reset_index(drop=True)
        n_obs = len(group)
        if n_obs < 30:
            continue

        navs = group["nav"].values
        dates = group["date"].values
        daily_ret = np.diff(navs) / navs[:-1]
        group_dates = dates[1:]

        # 1. Trading-Day Based CAGR Calculations
        # 1-Year (last 252 trading days)
        if n_obs >= 253:
            ret_1y = (navs[-1] / navs[-253]) ** (TRADING_DAYS_PER_YEAR / 252) - 1
            ret_1y_pct = round(ret_1y * 100, 2)
        else:
            ret_1y = (navs[-1] / navs[0]) ** (TRADING_DAYS_PER_YEAR / n_obs) - 1
            ret_1y_pct = round(ret_1y * 100, 2)

        # 3-Year (last 756 trading days)
        if n_obs >= 757:
            ret_3y = (navs[-1] / navs[-757]) ** (TRADING_DAYS_PER_YEAR / 756) - 1
            ret_3y_pct = round(ret_3y * 100, 2)
        else:
            ret_3y = (navs[-1] / navs[0]) ** (TRADING_DAYS_PER_YEAR / n_obs) - 1
            ret_3y_pct = round(ret_3y * 100, 2)

        # 5-Year (last 1260 trading days)
        if n_obs >= 1261:
            ret_5y = (navs[-1] / navs[-1261]) ** (TRADING_DAYS_PER_YEAR / 1260) - 1
            ret_5y_pct = round(ret_5y * 100, 2)
        else:
            ret_5y = (navs[-1] / navs[0]) ** (TRADING_DAYS_PER_YEAR / n_obs) - 1
            ret_5y_pct = round(ret_5y * 100, 2)

        # 2. Risk Metrics (Annualized Volatility, Downside Volatility)
        daily_std = np.std(daily_ret, ddof=1)
        ann_vol = daily_std * np.sqrt(TRADING_DAYS_PER_YEAR)
        ann_vol_pct = round(ann_vol * 100, 2)

        # Downside Deviation (semi-variance relative to Rf)
        downside_diff = np.minimum(0, daily_ret - daily_rf)
        downside_std = np.sqrt(np.mean(downside_diff ** 2)) * np.sqrt(TRADING_DAYS_PER_YEAR)

        # Overall Annualized Return (Geometric CAGR over full history using trading days)
        full_cagr = (navs[-1] / navs[0]) ** (TRADING_DAYS_PER_YEAR / n_obs) - 1

        # Sharpe & Sortino Ratios
        sharpe = (full_cagr - RISK_FREE_RATE) / ann_vol if ann_vol > 0 else 0.0
        sortino = (full_cagr - RISK_FREE_RATE) / downside_std if downside_std > 0 else 0.0

        # Maximum Drawdown (MDD)
        peak = np.maximum.accumulate(navs)
        drawdowns = (navs - peak) / peak
        max_drawdown = np.min(drawdowns)
        max_drawdown_pct = round(max_drawdown * 100, 2)

        # 3. Value at Risk (VaR) & CVaR (Historical)
        var_95 = -np.percentile(daily_ret, 5)
        var_99 = -np.percentile(daily_ret, 1)
        tail_95 = daily_ret[daily_ret <= -var_95]
        cvar_95 = -np.mean(tail_95) if len(tail_95) > 0 else var_95
        tail_99 = daily_ret[daily_ret <= -var_99]
        cvar_99 = -np.mean(tail_99) if len(tail_99) > 0 else var_99

        # 4. Alpha & Beta against Benchmark
        alpha_val = 0.0
        beta_val = 1.0
        r_squared = 0.0
        p_value = 0.0

        if bench_returns is not None:
            fund_series = pd.Series(daily_ret, index=group_dates)
            merged = pd.concat([fund_series.rename("fund"), bench_returns.rename("bench")], axis=1).dropna()
            if len(merged) >= 30:
                slope, intercept, r_val, p_val, std_err = stats.linregress(merged["bench"], merged["fund"])
                beta_val = round(slope, 3)
                r_squared = round(r_val ** 2, 3)
                p_value = round(p_val, 5)

                # Jensen's Alpha (Annualized)
                # alpha = CAGR_fund - [Rf + Beta * (CAGR_bench - Rf)]
                bench_comp = (1 + merged["bench"]).prod() ** (TRADING_DAYS_PER_YEAR / len(merged)) - 1
                alpha_ann = full_cagr - (RISK_FREE_RATE + beta_val * (bench_comp - RISK_FREE_RATE))
                alpha_val = round(alpha_ann * 100, 2)

        meta = scheme_info.get(amfi_code, {})
        p_meta = perf_info.get(amfi_code, {})

        scheme_name = meta.get("scheme_name", f"Scheme {amfi_code}")
        fund_house = meta.get("fund_house", "Mutual Fund")
        category = meta.get("category", "Equity")
        aum_crore = p_meta.get("aum_crore", 5000.0)
        risk_grade = p_meta.get("risk_grade", "Moderate")
        m_rating = p_meta.get("morningstar_rating", 3)
        exp_ratio = meta.get("expense_ratio_pct", 1.25)

        # Build Scorecard Record
        scorecard_list.append({
            "amfi_code": amfi_code,
            "scheme_name": scheme_name,
            "fund_house": fund_house,
            "category": category,
            "cagr_1yr_pct": ret_1y_pct,
            "cagr_3yr_pct": ret_3y_pct,
            "cagr_5yr_pct": ret_5y_pct,
            "ann_volatility_pct": ann_vol_pct,
            "sharpe_ratio": round(sharpe, 2),
            "sortino_ratio": round(sortino, 2),
            "max_drawdown_pct": max_drawdown_pct,
            "var_95_pct": round(var_95 * 100, 2),
            "cvar_95_pct": round(cvar_95 * 100, 2),
            "alpha_pct": alpha_val,
            "beta": beta_val,
            "aum_crore": aum_crore,
            "expense_ratio_pct": exp_ratio,
            "risk_grade": risk_grade,
            "morningstar_rating": m_rating,
        })

        # Build Alpha/Beta Record
        alpha_beta_list.append({
            "amfi_code": amfi_code,
            "scheme_name": scheme_name,
            "category": category,
            "alpha": alpha_val,
            "beta": beta_val,
            "r_squared": r_squared,
            "p_value": p_value,
            "sharpe_ratio": round(sharpe, 2),
            "benchmark_index": "NIFTY 50 TRI",
        })

        # Build VaR/CVaR Record
        var_cvar_list.append({
            "amfi_code": amfi_code,
            "scheme_name": scheme_name,
            "category": category,
            "daily_var_95_pct": round(var_95 * 100, 2),
            "daily_cvar_95_pct": round(cvar_95 * 100, 2),
            "daily_var_99_pct": round(var_99 * 100, 2),
            "daily_cvar_99_pct": round(cvar_99 * 100, 2),
            "ann_volatility_pct": ann_vol_pct,
            "max_drawdown_pct": max_drawdown_pct,
        })

    # Save outputs to both reports/ and data/processed/
    df_scorecard = pd.DataFrame(scorecard_list)
    df_alpha_beta = pd.DataFrame(alpha_beta_list)
    df_var_cvar = pd.DataFrame(var_cvar_list)

    df_scorecard.to_csv(REPORTS_DIR / "fund_scorecard.csv", index=False)
    df_scorecard.to_csv(PROCESSED_DIR / "fund_scorecard.csv", index=False)
    print(f"Saved fund_scorecard.csv ({len(df_scorecard)} schemes)")

    df_alpha_beta.to_csv(REPORTS_DIR / "alpha_beta.csv", index=False)
    df_alpha_beta.to_csv(PROCESSED_DIR / "alpha_beta.csv", index=False)
    print(f"Saved alpha_beta.csv ({len(df_alpha_beta)} schemes)")

    df_var_cvar.to_csv(REPORTS_DIR / "var_cvar_report.csv", index=False)
    df_var_cvar.to_csv(PROCESSED_DIR / "var_cvar_report.csv", index=False)
    print(f"Saved var_cvar_report.csv ({len(df_var_cvar)} schemes)")

    print("=" * 80)
    print("METRICS COMPUTATION COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    compute_metrics()
