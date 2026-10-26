import pandas as pd
import numpy as np

df_funds = pd.read_csv('data/processed/clean_fund_master.csv')
df_perf = pd.read_csv('data/processed/clean_scheme_performance.csv')
df_nav = pd.read_csv('data/processed/clean_nav_history.csv')
df_tx = pd.read_csv('data/processed/clean_investor_transactions.csv')
df_hold = pd.read_csv('data/processed/clean_portfolio_holdings.csv')

print("=== CATEGORIES IN FUND MASTER ===")
print(df_funds['category'].value_counts())

print("\n=== TOP 10 FUNDS BY AUM ===")
merged = df_perf.merge(df_funds[['amfi_code', 'sub_category']], on='amfi_code')
top_aum = merged.sort_values(by='aum_crore', ascending=False)
for _, r in top_aum.head(10).iterrows():
    print(f"{r['amfi_code']} | {r['category']} - {r['sub_category']} | {r['fund_house']} | {r['scheme_name']} | AUM: {r['aum_crore']}")

print("\n=== TOP FUNDS PER BROAD CATEGORY ===")
for cat, grp in merged.groupby('category'):
    top_f = grp.sort_values(by='aum_crore', ascending=False).iloc[0]
    print(f"{cat}: {top_f['amfi_code']} - {top_f['scheme_name']} ({top_f['fund_house']}, AUM={top_f['aum_crore']})")

print("\n=== TRANSACTION DETAILS ===")
df_tx['transaction_date'] = pd.to_datetime(df_tx['transaction_date'])
print(f"Transaction date range: {df_tx['transaction_date'].min()} to {df_tx['transaction_date'].max()}")
print(f"Transaction types: {df_tx['transaction_type'].value_counts().to_dict()}")
print(f"Unique investors: {df_tx['investor_id'].nunique()}")

print("\n=== PORTFOLIO HOLDINGS DETAILS ===")
print(f"Unique schemes with holdings: {df_hold['amfi_code'].nunique()}")
print(f"Holdings sectors: {df_hold['sector'].value_counts().to_dict()}")
print("Schemes in holdings vs categories:")
hold_funds = df_funds[df_funds['amfi_code'].isin(df_hold['amfi_code'].unique())]
print(hold_funds[['amfi_code', 'scheme_name', 'category', 'sub_category']])
