import pandas as pd
import numpy as np

df_nav = pd.read_csv('data/processed/clean_nav_history.csv')
df_funds = pd.read_csv('data/processed/clean_fund_master.csv')

df_nav['date'] = pd.to_datetime(df_nav['date'])
df_nav = df_nav.sort_values(['amfi_code', 'date'])

# Daily returns
df_nav['return'] = df_nav.groupby('amfi_code')['nav'].pct_change()

# Select 5 key funds
# 1. SBI Bluechip (119551)
# 2. HDFC Mid-Cap Opportunities (100033)
# 3. Nippon India Small Cap (118634)
# 4. Kotak Flexicap (120843)
# 5. Mirae Asset Emerging Bluechip (148568)
key_funds = [119551, 100033, 118634, 120843, 148568]

for f in key_funds:
    fund_name = df_funds[df_funds['amfi_code'] == f]['scheme_name'].values[0]
    sub = df_nav[df_nav['amfi_code'] == f].copy()
    rolling_sharpe = (sub['return'].rolling(90).mean() / sub['return'].rolling(90).std()) * np.sqrt(252)
    print(f"Fund {f} ({fund_name}):")
    print(f"  Valid 90-day Sharpe points: {rolling_sharpe.dropna().count()}")
    print(f"  Min: {rolling_sharpe.min():.2f}, Max: {rolling_sharpe.max():.2f}, Mean: {rolling_sharpe.mean():.2f}, Latest: {rolling_sharpe.iloc[-1]:.2f}")
