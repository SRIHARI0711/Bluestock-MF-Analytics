
-- =========================================================
-- Query 1: Top 5 fund houses by latest available AUM
-- =========================================================
WITH latest_aum AS (
    SELECT MAX(date_key) AS latest_date_key
    FROM fact_aum
)
SELECT
    a.fund_house,
    a.aum_crore,
    a.num_schemes,
    d.full_date AS report_date
FROM fact_aum a
JOIN dim_date d ON a.date_key = d.date_key
JOIN latest_aum l ON a.date_key = l.latest_date_key
ORDER BY a.aum_crore DESC
LIMIT 5;


-- =========================================================
-- Query 2: Average NAV per month for each fund
-- =========================================================
SELECT
    f.scheme_name,
    d.year_month,
    ROUND(AVG(n.nav), 4) AS average_nav
FROM fact_nav n
JOIN dim_fund f ON n.fund_key = f.fund_key
JOIN dim_date d ON n.date_key = d.date_key
GROUP BY f.scheme_name, d.year_month
ORDER BY f.scheme_name, d.year_month;


-- =========================================================
-- Query 3: SIP inflow year-over-year growth
-- Note: transaction data does not contain a separate
-- monthly industry-wide SIP inflow measure.
-- =========================================================
WITH annual_sip AS (
    SELECT
        d.year,
        SUM(t.amount_inr) AS sip_amount_inr
    FROM fact_transactions t
    JOIN dim_date d ON t.date_key = d.date_key
    WHERE t.transaction_type = 'SIP'
    GROUP BY d.year
)
SELECT
    year,
    ROUND(sip_amount_inr, 2) AS sip_amount_inr,
    ROUND(
        100.0 * (
            sip_amount_inr -
            LAG(sip_amount_inr) OVER (ORDER BY year)
        ) / NULLIF(
            LAG(sip_amount_inr) OVER (ORDER BY year), 0
        ),
        2
    ) AS yoy_growth_pct
FROM annual_sip
ORDER BY year;


-- =========================================================
-- Query 4: Transaction count and value by state
-- =========================================================
SELECT
    state,
    COUNT(*) AS transaction_count,
    ROUND(SUM(amount_inr), 2) AS total_amount_inr,
    ROUND(AVG(amount_inr), 2) AS average_amount_inr
FROM fact_transactions
GROUP BY state
ORDER BY total_amount_inr DESC;


-- =========================================================
-- Query 5: Funds with expense ratio below 1%
-- =========================================================
SELECT
    f.amfi_code,
    f.scheme_name,
    f.fund_house,
    f.plan,
    f.expense_ratio_pct
FROM dim_fund f
WHERE f.expense_ratio_pct < 1.0
ORDER BY f.expense_ratio_pct ASC;


-- =========================================================
-- Query 6: Transaction distribution by type
-- =========================================================
SELECT
    transaction_type,
    COUNT(*) AS transaction_count,
    ROUND(SUM(amount_inr), 2) AS total_amount_inr
FROM fact_transactions
GROUP BY transaction_type
ORDER BY total_amount_inr DESC;


-- =========================================================
-- Query 7: Top 10 funds by five-year return
-- =========================================================
SELECT
    f.scheme_name,
    f.fund_house,
    p.return_5yr_pct,
    p.sharpe_ratio,
    p.risk_grade
FROM fact_performance p
JOIN dim_fund f ON p.fund_key = f.fund_key
WHERE p.return_5yr_pct IS NOT NULL
ORDER BY p.return_5yr_pct DESC
LIMIT 10;


-- =========================================================
-- Query 8: Average transaction amount by KYC status
-- =========================================================
SELECT
    kyc_status,
    COUNT(*) AS transaction_count,
    ROUND(AVG(amount_inr), 2) AS average_amount_inr,
    ROUND(SUM(amount_inr), 2) AS total_amount_inr
FROM fact_transactions
GROUP BY kyc_status
ORDER BY total_amount_inr DESC;


-- =========================================================
-- Query 9: Fund NAV change from first to last observation
-- =========================================================
WITH ranked_nav AS (
    SELECT
        n.fund_key,
        n.nav,
        d.full_date,
        ROW_NUMBER() OVER (
            PARTITION BY n.fund_key
            ORDER BY d.full_date ASC
        ) AS first_rank,
        ROW_NUMBER() OVER (
            PARTITION BY n.fund_key
            ORDER BY d.full_date DESC
        ) AS last_rank
    FROM fact_nav n
    JOIN dim_date d ON n.date_key = d.date_key
),
first_nav AS (
    SELECT fund_key, nav, full_date
    FROM ranked_nav
    WHERE first_rank = 1
),
last_nav AS (
    SELECT fund_key, nav, full_date
    FROM ranked_nav
    WHERE last_rank = 1
)
SELECT
    f.scheme_name,
    fn.full_date AS first_date,
    fn.nav AS first_nav,
    ln.full_date AS latest_date,
    ln.nav AS latest_nav,
    ROUND(
        100.0 * (ln.nav - fn.nav) / NULLIF(fn.nav, 0), 2
    ) AS cumulative_nav_change_pct
FROM first_nav fn
JOIN last_nav ln ON fn.fund_key = ln.fund_key
JOIN dim_fund f ON f.fund_key = fn.fund_key
ORDER BY cumulative_nav_change_pct DESC;


-- =========================================================
-- Query 10: Fund risk and return comparison
-- =========================================================
SELECT
    f.scheme_name,
    p.return_3yr_pct,
    p.benchmark_3yr_pct,
    p.alpha,
    p.beta,
    p.sharpe_ratio,
    p.std_dev_ann_pct,
    p.max_drawdown_pct
FROM fact_performance p
JOIN dim_fund f ON p.fund_key = f.fund_key
ORDER BY p.sharpe_ratio DESC;
