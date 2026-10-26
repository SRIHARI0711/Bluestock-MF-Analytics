import pandas as pd
import numpy as np

df_tx = pd.read_csv('data/processed/clean_investor_transactions.csv')
df_funds = pd.read_csv('data/processed/clean_fund_master.csv')
fund_map = df_funds.set_index('amfi_code')['scheme_name'].to_dict()

df_tx['transaction_date'] = pd.to_datetime(df_tx['transaction_date'])

# Task 3: Cohort analysis
first_tx = df_tx.groupby('investor_id')['transaction_date'].min().rename('first_tx_date').reset_index()
first_tx['cohort_year'] = first_tx['first_tx_date'].dt.year
df_tx = df_tx.merge(first_tx[['investor_id', 'cohort_year']], on='investor_id')

print("=== COHORT ANALYSIS RESULTS ===")
cohort_summary = []
for cohort in sorted(df_tx['cohort_year'].unique()):
    sub = df_tx[df_tx['cohort_year'] == cohort]
    sip_sub = sub[sub['transaction_type'] == 'SIP']
    invest_sub = sub[sub['transaction_type'].isin(['SIP', 'Lumpsum'])]
    redemp_sub = sub[sub['transaction_type'] == 'Redemption']
    
    avg_sip_txn = sip_sub['amount_inr'].mean()
    total_sip = sip_sub['amount_inr'].sum()
    total_lump = sub[sub['transaction_type'] == 'Lumpsum']['amount_inr'].sum()
    total_gross_invested = invest_sub['amount_inr'].sum()
    total_redemption = redemp_sub['amount_inr'].sum()
    net_invested = total_gross_invested - total_redemption
    
    # Top fund preference (by total invested amount or count)
    top_fund_amt_code = invest_sub.groupby('amfi_code')['amount_inr'].sum().idxmax()
    top_fund_amt_val = invest_sub.groupby('amfi_code')['amount_inr'].sum().max()
    top_fund_cnt_code = invest_sub.groupby('amfi_code')['amount_inr'].count().idxmax()
    top_fund_cnt_val = invest_sub.groupby('amfi_code')['amount_inr'].count().max()
    
    cohort_summary.append({
        'cohort_year': cohort,
        'investor_count': sub['investor_id'].nunique(),
        'total_transactions': len(sub),
        'sip_transactions': len(sip_sub),
        'avg_sip_amount': round(avg_sip_txn, 2),
        'total_sip_invested': round(total_sip, 2),
        'total_lumpsum_invested': round(total_lump, 2),
        'total_invested': round(total_gross_invested, 2),
        'net_invested': round(net_invested, 2),
        'top_fund_code': top_fund_amt_code,
        'top_fund_name': fund_map.get(top_fund_amt_code, 'Unknown'),
        'top_fund_invested_amount': round(top_fund_amt_val, 2),
        'top_fund_by_count': fund_map.get(top_fund_cnt_code, 'Unknown'),
        'top_fund_txn_count': top_fund_cnt_val
    })

df_cohort = pd.DataFrame(cohort_summary)
print(df_cohort.to_string())

# Task 4: SIP continuity analysis
print("\n=== SIP CONTINUITY ANALYSIS ===")
sip_df = df_tx[df_tx['transaction_type'] == 'SIP'].sort_values(['investor_id', 'transaction_date'])
sip_counts = sip_df.groupby('investor_id')['transaction_date'].count()
investors_6plus = sip_counts[sip_counts >= 6].index

print(f"Total investors with SIPs: {sip_df['investor_id'].nunique()}")
print(f"Investors with 6+ SIP transactions: {len(investors_6plus)}")

# Calculate gap between consecutive SIP transactions
sip_6p = sip_df[sip_df['investor_id'].isin(investors_6plus)].copy()
sip_6p['prev_date'] = sip_6p.groupby('investor_id')['transaction_date'].shift(1)
sip_6p['date_diff_days'] = (sip_6p['transaction_date'] - sip_6p['prev_date']).dt.days

# Drop first transaction per investor (where prev_date is NaT)
gaps = sip_6p.dropna(subset=['date_diff_days'])

# Compute average gap per investor
investor_gaps = gaps.groupby('investor_id')['date_diff_days'].mean().reset_index()
investor_gaps.columns = ['investor_id', 'avg_gap_days']
investor_gaps['is_at_risk'] = investor_gaps['avg_gap_days'] > 35

at_risk_count = investor_gaps['is_at_risk'].sum()
total_evaluated = len(investor_gaps)
print(f"Evaluated investors (6+ SIPs): {total_evaluated}")
print(f"At-risk investors (avg gap > 35 days): {at_risk_count} ({at_risk_count / total_evaluated * 100:.2f}%)")
print(f"Normal investors (avg gap <= 35 days): {total_evaluated - at_risk_count} ({(total_evaluated - at_risk_count) / total_evaluated * 100:.2f}%)")
print(f"Overall average gap across investors: {investor_gaps['avg_gap_days'].mean():.2f} days")
print(f"Min avg gap: {investor_gaps['avg_gap_days'].min():.2f}, Max avg gap: {investor_gaps['avg_gap_days'].max():.2f}")
