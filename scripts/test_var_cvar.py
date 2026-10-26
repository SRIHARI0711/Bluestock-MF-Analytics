import pandas as pd
import numpy as np

df_nav = pd.read_csv('data/processed/clean_nav_history.csv')
df_funds = pd.read_csv('data/processed/clean_fund_master.csv')
df_perf = pd.read_csv('data/processed/clean_scheme_performance.csv')

df_nav['date'] = pd.to_datetime(df_nav['date'])
df_nav = df_nav.sort_values(['amfi_code', 'date'])

# Calculate daily returns
df_nav['daily_return'] = df_nav.groupby('amfi_code')['nav'].pct_change()

var_cvar_records = []
for amfi_code, group in df_nav.groupby('amfi_code'):
    returns = group['daily_return'].dropna()
    
    # Historical VaR (95%) — 5th percentile of daily return distribution
    var_95 = float(np.percentile(returns, 5))  # or returns.quantile(0.05)
    
    # CVaR (95%) — mean of returns below VaR threshold
    tail_returns = returns[returns < var_95]
    cvar_95 = float(tail_returns.mean()) if len(tail_returns) > 0 else var_95
    
    # Scheme details
    fund_info = df_funds[df_funds['amfi_code'] == amfi_code].iloc[0]
    
    var_cvar_records.append({
        'amfi_code': amfi_code,
        'scheme_name': fund_info['scheme_name'],
        'category': fund_info['category'],
        'sub_category': fund_info['sub_category'],
        'fund_house': fund_info['fund_house'],
        'plan': fund_info['plan'],
        'observations_count': len(returns),
        'mean_daily_return': returns.mean(),
        'std_daily_return': returns.std(),
        'var_95': var_95,
        'var_95_pct': var_95 * 100,
        'cvar_95': cvar_95,
        'cvar_95_pct': cvar_95 * 100,
        # Risk loss interpretation (positive loss representation)
        'var_95_loss_pct': abs(var_95) * 100,
        'cvar_95_loss_pct': abs(cvar_95) * 100
    })

var_cvar_df = pd.DataFrame(var_cvar_records)
print("=== VAR/CVAR SUMMARY (Top 5 Highest Risk/Lowest Returns at 5th percentile) ===")
print(var_cvar_df.sort_values(by='var_95', ascending=True)[['amfi_code', 'scheme_name', 'sub_category', 'var_95_pct', 'cvar_95_pct']].head(10).to_string())

print("\n=== VAR/CVAR SUMMARY (Lowest Risk / Debt Funds) ===")
print(var_cvar_df.sort_values(by='var_95', ascending=False)[['amfi_code', 'scheme_name', 'sub_category', 'var_95_pct', 'cvar_95_pct']].head(10).to_string())
