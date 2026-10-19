
# BlueStock Mutual Fund Analytics — Data Dictionary

## 1. Project Overview

This project analyses mutual fund NAV history, investor transactions,
scheme performance and fund-house assets under management.

Database: `bluestock_mf.db`
Database engine: SQLite
Data processing: Python, Pandas and SQLAlchemy

## 2. Source and Processed Datasets

| Source CSV | Processed CSV | Description |
|---|---|---|
| 01_fund_master.csv | clean_fund_master.csv | Fund and scheme attributes |
| 02_nav_history.csv | clean_nav_history.csv | Historical NAV observations |
| 03_aum_by_fund_house.csv | clean_aum_by_fund_house.csv | AUM by fund house and date |
| 04_monthly_sip_inflows.csv | clean_monthly_sip_inflows.csv | Monthly SIP industry metrics |
| 05_category_inflows.csv | clean_category_inflows.csv | Net inflows by category and month |
| 06_industry_folio_count.csv | clean_industry_folio_count.csv | Industry folio counts |
| 07_scheme_performance.csv | clean_scheme_performance.csv | Returns and risk metrics |
| 08_investor_transactions.csv | clean_investor_transactions.csv | Investor transaction records |
| 09_portfolio_holdings.csv | clean_portfolio_holdings.csv | Scheme portfolio holdings |
| 10_benchmark_indices.csv | clean_benchmark_indices.csv | Benchmark index closing values |

## 3. Database Tables

### dim_fund

Purpose: Stores the descriptive attributes of each mutual fund scheme.

| Column | SQLite type | Definition |
|---|---|---|
| fund_key | INTEGER | Surrogate primary key |
| amfi_code | TEXT | Unique AMFI scheme identifier |
| fund_house | TEXT | Asset management company |
| scheme_name | TEXT | Mutual fund scheme name |
| category | TEXT | Broad fund category |
| sub_category | TEXT | More specific category |
| plan | TEXT | Plan type, such as Direct or Regular |
| launch_date | TEXT | Scheme launch date, YYYY-MM-DD |
| benchmark | TEXT | Scheme benchmark index |
| expense_ratio_pct | REAL | Expense ratio in percentage points |
| exit_load_pct | REAL | Exit load in percentage points |
| min_sip_amount | REAL | Minimum SIP investment amount |
| min_lumpsum_amount | REAL | Minimum lump-sum investment amount |
| fund_manager | TEXT | Named fund manager |
| risk_category | TEXT | Source-provided risk category |
| sebi_category_code | TEXT | Source-provided SEBI category code |

Primary key: fund_key
Unique key: amfi_code
Source: clean_fund_master.csv

### dim_date

Purpose: Provides date attributes for time-based analysis.

| Column | SQLite type | Definition |
|---|---|---|
| date_key | INTEGER | Date identifier in YYYYMMDD format |
| full_date | TEXT | Calendar date in YYYY-MM-DD format |
| year | INTEGER | Calendar year |
| month | INTEGER | Calendar month number |
| quarter | INTEGER | Calendar quarter |
| month_name | TEXT | Full month name |
| year_month | TEXT | Year and month in YYYY-MM format |

Primary key: date_key
Unique key: full_date
Source: Dates extracted from NAV, transactions and AUM data.

### fact_nav

Purpose: Stores historical NAV observations for each scheme.

| Column | SQLite type | Definition |
|---|---|---|
| nav_key | INTEGER | Surrogate primary key |
| fund_key | INTEGER | Reference to dim_fund |
| date_key | INTEGER | Reference to dim_date |
| nav | REAL | Net asset value per unit |

Primary key: nav_key
Foreign keys: fund_key, date_key
Business key: fund_key + date_key
Source: clean_nav_history.csv

### fact_transactions

Purpose: Stores investor transactions.

| Column | SQLite type | Definition |
|---|---|---|
| transaction_key | INTEGER | Surrogate primary key |
| investor_id | TEXT | Investor identifier |
| fund_key | INTEGER | Reference to dim_fund |
| date_key | INTEGER | Reference to dim_date |
| transaction_type | TEXT | SIP, Lumpsum or Redemption |
| amount_inr | REAL | Transaction amount in INR |
| state | TEXT | Investor state |
| city | TEXT | Investor city |
| city_tier | TEXT | Source-provided city tier |
| age_group | TEXT | Source-provided age group |
| gender | TEXT | Source-provided gender |
| annual_income_lakh | REAL | Annual income in lakh INR |
| payment_mode | TEXT | Payment method |
| kyc_status | TEXT | Verified or Pending |

Primary key: transaction_key
Foreign keys: fund_key, date_key
Source: clean_investor_transactions.csv

### fact_performance

Purpose: Stores scheme-level performance and risk measurements.

| Column | SQLite type | Definition |
|---|---|---|
| performance_key | INTEGER | Surrogate primary key |
| fund_key | INTEGER | Reference to dim_fund |
| return_1yr_pct | REAL | One-year return percentage |
| return_3yr_pct | REAL | Three-year return percentage |
| return_5yr_pct | REAL | Five-year return percentage |
| benchmark_3yr_pct | REAL | Three-year benchmark return |
| alpha | REAL | Source-provided alpha metric |
| beta | REAL | Source-provided beta metric |
| sharpe_ratio | REAL | Source-provided Sharpe ratio |
| sortino_ratio | REAL | Source-provided Sortino ratio |
| std_dev_ann_pct | REAL | Annualised standard deviation percentage |
| max_drawdown_pct | REAL | Maximum drawdown percentage |
| aum_crore | REAL | Scheme AUM in crore INR |
| expense_ratio_pct | REAL | Expense ratio in percentage points |
| morningstar_rating | REAL | Source-provided rating |
| risk_grade | TEXT | Source-provided risk grade |

Primary key: performance_key
Foreign key: fund_key
Unique key: fund_key
Source: clean_scheme_performance.csv

### fact_aum

Purpose: Stores fund-house-level AUM observations.

| Column | SQLite type | Definition |
|---|---|---|
| aum_key | INTEGER | Surrogate primary key |
| date_key | INTEGER | Reference to dim_date |
| fund_house | TEXT | Asset management company |
| aum_lakh_crore | REAL | AUM in lakh crore INR |
| aum_crore | REAL | AUM in crore INR |
| num_schemes | INTEGER | Number of schemes reported |

Primary key: aum_key
Foreign key: date_key
Business key: date_key + fund_house
Source: clean_aum_by_fund_house.csv

## 4. Data Quality Rules

- NAV must be greater than zero.
- Transaction amounts must be greater than zero.
- Transaction types must be SIP, Lumpsum or Redemption.
- KYC statuses must be Verified or Pending.
- Fund master AMFI codes must be unique.
- NAV records must be unique per fund and date.
- AUM records must be unique per date and fund house.
- Invalid or anomalous performance values must be investigated.
- Missing SIP YoY growth values must not automatically be treated as zero.

## 5. Data Not Yet Loaded into SQLite

These cleaned datasets currently remain CSV files rather than
dedicated SQLite tables:

- clean_monthly_sip_inflows.csv
- clean_category_inflows.csv
- clean_industry_folio_count.csv
- clean_portfolio_holdings.csv
- clean_benchmark_indices.csv

They can be incorporated into an expanded schema if required.

## 6. Limitations

- NAV percentage change is not the same as total investor return.
- Transaction-level SIP totals are not the same as industry-wide SIP inflows.
- AUM by fund house is aggregated data and must not be treated as
  individual-scheme AUM.
- The database contains the source observations and does not
  automatically generate NAV observations for holidays or weekends.
  