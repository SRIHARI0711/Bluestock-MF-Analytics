# 📧 Bonus Challenge B5 — Automated Executive HTML Email Report (+10 Marks)

## 📌 Overview
Generates an institutional, responsive HTML email briefing that delivers weekly mutual fund performance, risk metrics, and market trends directly to stakeholders and investment committees.

### 🎨 Key Email Sections:
1. **Executive KPI Tiles:**
   - Total Industry AUM (₹ Lakh Crore)
   - Monthly Systematic Investment Plan (SIP) run-rate
   - Industry-wide average Sharpe Ratio
   - Benchmark Portfolio 95% 1-Day Value at Risk (VaR)
2. **Top 5 Sharpe-Ranked Funds Leaderboard:**
   - 3-Year CAGR performance, category classification, and risk tier badges.
3. **Tail Risk & Volatility Watch:**
   - Funds with elevated Maximum Drawdowns and Value at Risk levels.
4. **Embedded Visual Scorecards:**
   - Asset allocation and return distributions embedded via Base64 for instant rendering in email clients without requiring external image downloads.

---

## 🚀 Execution & Viewing

### 1. Generate Local HTML Report
```bash
python bonus_challenges/B5_automated_email_report/email_report_generator.py
```
This generates the standalone HTML email file:
- [`weekly_performance_summary_email.html`](file:///bonus_challenges/B5_automated_email_report/weekly_performance_summary_email.html)

You can double-click or open this HTML file directly in Google Chrome, Microsoft Edge, or any web browser to preview the responsive email.

### 2. Dispatch via SMTP (Optional)
```bash
python bonus_challenges/B5_automated_email_report/email_report_generator.py --send --to your-email@example.com
```
*Note: Configured via standard environment variables `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, and `SMTP_PASS`.*
