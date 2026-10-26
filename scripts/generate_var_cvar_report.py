"""
Generate Historical VaR (95%) and CVaR (95%) report for all 40 mutual fund schemes.
"""

from pathlib import Path
import pandas as pd
import numpy as np

def generate_var_cvar_report():
    base_dir = Path(__file__).resolve().parent.parent
    nav_path = base_dir / "data" / "processed" / "clean_nav_history.csv"
    fund_path = base_dir / "data" / "processed" / "clean_fund_master.csv"
    perf_path = base_dir / "data" / "processed" / "clean_scheme_performance.csv"
    
    df_nav = pd.read_csv(nav_path)
    df_funds = pd.read_csv(fund_path)
    df_perf = pd.read_csv(perf_path)
    
    df_nav['date'] = pd.to_datetime(df_nav['date'])
    df_nav = df_nav.sort_values(['amfi_code', 'date'])
    
    # Calculate daily returns
    df_nav['daily_return'] = df_nav.groupby('amfi_code')['nav'].pct_change()
    
    results = []
    for amfi_code, group in df_nav.groupby('amfi_code'):
        returns = group['daily_return'].dropna()
        
        # Historical VaR (95%) = 5th percentile of daily return distribution
        var_95 = float(np.percentile(returns, 5))
        
        # CVaR (95%) = mean of returns below VaR threshold
        tail_returns = returns[returns < var_95]
        cvar_95 = float(tail_returns.mean()) if len(tail_returns) > 0 else var_95
        
        # Metadata
        fund_row = df_funds[df_funds['amfi_code'] == amfi_code].iloc[0]
        perf_row = df_perf[df_perf['amfi_code'] == amfi_code].iloc[0] if len(df_perf[df_perf['amfi_code'] == amfi_code]) > 0 else None
        
        results.append({
            'amfi_code': amfi_code,
            'scheme_name': fund_row['scheme_name'],
            'fund_house': fund_row['fund_house'],
            'category': fund_row['category'],
            'sub_category': fund_row['sub_category'],
            'plan': fund_row['plan'],
            'risk_grade': perf_row['risk_grade'] if perf_row is not None else fund_row.get('risk_category', 'N/A'),
            'total_observations': len(returns),
            'mean_daily_return_pct': round(float(returns.mean() * 100), 4),
            'std_daily_return_pct': round(float(returns.std() * 100), 4),
            'annualized_volatility_pct': round(float(returns.std() * np.sqrt(252) * 100), 2),
            'var_95_pct': round(var_95 * 100, 4),
            'cvar_95_pct': round(cvar_95 * 100, 4),
            'var_95_loss_pct': round(abs(var_95) * 100, 4),
            'cvar_95_loss_pct': round(abs(cvar_95) * 100, 4),
            'var_95_raw': round(var_95, 6),
            'cvar_95_raw': round(cvar_95, 6),
            'sharpe_ratio': perf_row['sharpe_ratio'] if perf_row is not None else np.nan,
            'return_3yr_pct': perf_row['return_3yr_pct'] if perf_row is not None else np.nan
        })
        
    df_report = pd.DataFrame(results)
    # Sort by risk (lowest 5th percentile return = highest risk)
    df_report = df_report.sort_values(by='var_95_pct', ascending=True).reset_index(drop=True)
    
    # Save output to root and reports directory
    out_root = base_dir / "var_cvar_report.csv"
    out_reports = base_dir / "reports" / "var_cvar_report.csv"
    
    df_report.to_csv(out_root, index=False)
    df_report.to_csv(out_reports, index=False)
    
    print(f"Successfully generated VaR/CVaR report for {len(df_report)} schemes.")
    print(f"Saved to: {out_root}")
    print(f"Saved to: {out_reports}")
    return df_report

if __name__ == "__main__":
    generate_var_cvar_report()
