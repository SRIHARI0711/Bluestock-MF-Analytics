# 🌐 Bonus Challenge B2 — Interactive Streamlit Web Application (+10 Marks)

## 📌 Overview
An institutional, multi-page interactive web application built with **Streamlit** and **Plotly** as an alternative to Microsoft Power BI.

### 📑 4 Specialized Application Pages:
1. **🏭 Industry Overview:**
   - Total Mutual Fund AUM KPI cards (₹ Lakh Crore).
   - Monthly SIP inflow trends & growth trajectory.
   - Asset Under Management distribution across AMCs and asset classes.
2. **📈 Fund Performance & Risk:**
   - Multi-fund NAV history comparisons with normalized rebasing (Base 100).
   - Risk-Return scatter plots (Annualized Volatility vs. 3-Year CAGR).
   - Sharpe Ratio, Sortino Ratio, and Alpha/Beta leaderboards.
3. **👥 Investor Analytics:**
   - Demographics analysis: Age brackets, gender distribution, investment modes (SIP vs. Lumpsum).
   - Geographic penetration: T30 vs. B30 city tier contribution and state-wise transaction volumes.
4. **🎯 Fund Recommender Engine:**
   - Algorithmic matching based on investor risk appetite (Conservative, Moderate, Aggressive).
   - Dynamic filtering by minimum AUM and asset categories.
   - Instant CSV export of custom-recommended portfolios.

---

## 🚀 How to Run the Web App

From the project root:
```bash
streamlit run bonus_challenges/B2_streamlit_web_app/streamlit_app.py
```

Or directly from this folder:
```bash
streamlit run streamlit_app.py
```
The browser will automatically open at `http://localhost:8501`.
