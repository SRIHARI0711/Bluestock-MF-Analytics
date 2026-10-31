#!/usr/bin/env python3
"""
Bluestock Mutual Fund Analytics — Streamlit Web Dashboard (Bonus B2)
====================================================================
Interactive multi-page web application as an alternative to Power BI.

Run with:
    streamlit run dashboard/streamlit_app.py

Pages:
  1. 🏭 Industry Overview    — AUM, SIP trends, category flows, folio counts
  2. 📈 Fund Performance     — Scorecards, Sharpe/Sortino, CAGR comparison
  3. 👥 Investor Analytics   — Demographic segmentation, state/tier breakdown
  4. 🎯 Fund Recommender     — Risk-based fund selection engine
"""

import sys
from pathlib import Path
import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ─── Path Setup ───────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED = BASE_DIR / "data" / "processed"
REPORTS   = BASE_DIR / "reports"

sys.path.insert(0, str(BASE_DIR))

# ─── Bluestock Brand Palette ──────────────────────────────────────────────────
NAVY   = "#0A2540"
CYAN   = "#00D4B2"
BLUE   = "#0066FF"
GREEN  = "#10B981"
RED    = "#EF4444"
AMBER  = "#F59E0B"
PURPLE = "#6366F1"

st.set_page_config(
    page_title="Bluestock MF Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
  .stMetric label  { font-size: 0.78rem; color: #64748B; }
  .stMetric value  { font-size: 1.6rem; font-weight: 700; }
  [data-testid="stSidebar"] { background: #0A2540; }
  [data-testid="stSidebar"] * { color: #E2E8F0 !important; }
  .hero-banner {
    background: linear-gradient(90deg, #0A2540, #0066FF);
    padding: 18px 28px; border-radius: 10px; margin-bottom: 20px;
  }
  .hero-banner h2 { color: white; margin: 0; }
  .hero-banner p  { color: #CBD5E1; margin: 4px 0 0; }
  .insight-card {
    background:#F4F6F9; border-left:4px solid #00D4B2;
    padding:12px 16px; border-radius:6px; margin-bottom:10px;
  }
</style>
""", unsafe_allow_html=True)

# ─── Data Loaders (cached) ────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_fund_master():
    return pd.read_csv(PROCESSED / "clean_fund_master.csv")

@st.cache_data(show_spinner=False)
def load_scorecard():
    p = REPORTS / "fund_scorecard.csv"
    if p.exists():
        return pd.read_csv(p)
    return pd.read_csv(PROCESSED / "clean_scheme_performance.csv")

@st.cache_data(show_spinner=False)
def load_nav():
    df = pd.read_csv(PROCESSED / "clean_nav_history.csv", parse_dates=["date"])
    return df

@st.cache_data(show_spinner=False)
def load_transactions():
    df = pd.read_csv(PROCESSED / "clean_investor_transactions.csv", parse_dates=["transaction_date"])
    return df

@st.cache_data(show_spinner=False)
def load_aum():
    df = pd.read_csv(PROCESSED / "clean_aum_by_fund_house.csv", parse_dates=["date"])
    return df

@st.cache_data(show_spinner=False)
def load_sip():
    return pd.read_csv(PROCESSED / "clean_monthly_sip_inflows.csv")

@st.cache_data(show_spinner=False)
def load_category():
    return pd.read_csv(PROCESSED / "clean_category_inflows.csv")

@st.cache_data(show_spinner=False)
def load_folio():
    return pd.read_csv(PROCESSED / "clean_industry_folio_count.csv")

# ─── Sidebar Navigation ───────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📊 Bluestock MF Analytics")
    st.markdown("---")
    page = st.radio(
        "Navigate to",
        ["🏭 Industry Overview", "📈 Fund Performance", "👥 Investor Analytics", "🎯 Fund Recommender"],
        label_visibility="collapsed",
    )
    st.markdown("---")
    st.markdown("**About**")
    st.markdown("Capstone Project — BlueStock Internship  \n40 Funds · 46K NAV Records  \n32K Transactions · Live mfapi.in")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1: INDUSTRY OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════
if page == "🏭 Industry Overview":
    st.markdown("""<div class="hero-banner"><h2>🏭 Industry Overview</h2>
    <p>AUM by fund house, SIP inflow trends, category flows & folio growth</p></div>""",
    unsafe_allow_html=True)

    aum_df = load_aum()
    sip_df = load_sip()
    cat_df = load_category()
    folio_df = load_folio()

    # ── Slicers ──
    col1, col2 = st.columns(2)
    with col1:
        fund_houses = ["All"] + sorted(aum_df["fund_house"].unique().tolist())
        selected_fh = st.selectbox("🏦 Filter by Fund House", fund_houses)
    with col2:
        if "date" in aum_df.columns:
            years = ["All"] + sorted(aum_df["date"].dt.year.dropna().unique().astype(str).tolist())
        else:
            years = ["All"]
        selected_year = st.selectbox("📅 Filter by Year", years)

    # Filter
    aum_filtered = aum_df.copy()
    if selected_fh != "All":
        aum_filtered = aum_filtered[aum_filtered["fund_house"] == selected_fh]
    if selected_year != "All" and "date" in aum_filtered.columns:
        aum_filtered = aum_filtered[aum_filtered["date"].dt.year.astype(str) == selected_year]

    # ── KPI Cards ──
    st.markdown("### 🔑 Key Industry Metrics")
    k1, k2, k3, k4 = st.columns(4)
    latest_aum = aum_df.sort_values("date").groupby("fund_house").last()["aum_crore"].sum() if "aum_crore" in aum_df.columns else 0
    k1.metric("Total Industry AUM", f"₹{latest_aum/1e5:.1f}L Cr")
    k2.metric("Fund Houses Tracked", str(aum_df["fund_house"].nunique()))
    sip_latest = pd.to_numeric(sip_df.iloc[-1, 1], errors="coerce") if len(sip_df) > 0 else 0
    k3.metric("Latest Monthly SIP", f"₹{sip_latest/1e2:.0f} Cr" if sip_latest else "N/A")
    folio_total = pd.to_numeric(folio_df.iloc[-1].get("total_folios", folio_df.iloc[-1, 1]), errors="coerce") if len(folio_df) > 0 else 0
    k4.metric("Total Folios", f"{folio_total/1e7:.1f}Cr" if folio_total > 1e6 else str(folio_total))

    st.markdown("---")

    # ── AUM by Fund House Bar Chart ──
    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown("#### AUM by Fund House (₹ Crore)")
        latest_date = aum_df["date"].max() if "date" in aum_df.columns else None
        aum_latest = aum_df[aum_df["date"] == latest_date] if latest_date else aum_df
        aum_bar = aum_latest.groupby("fund_house")["aum_crore"].sum().sort_values(ascending=True)
        fig = px.bar(
            aum_bar.reset_index(), x="aum_crore", y="fund_house", orientation="h",
            color_discrete_sequence=[BLUE], labels={"aum_crore": "AUM (₹ Cr)", "fund_house": ""},
        )
        fig.update_layout(plot_bgcolor="white", height=400, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        st.markdown("#### Monthly SIP Inflows Trend (₹ Cr)")
        if len(sip_df) > 0:
            sip_plot = sip_df.copy()
            sip_plot.columns = [c.lower().strip() for c in sip_plot.columns]
            date_col = next((c for c in sip_plot.columns if "month" in c or "date" in c), sip_plot.columns[0])
            val_col = next((c for c in sip_plot.columns if "inflow" in c or "amount" in c or "sip" in c), sip_plot.columns[1])
            sip_plot[val_col] = pd.to_numeric(sip_plot[val_col], errors="coerce")
            fig2 = px.line(sip_plot.dropna(), x=date_col, y=val_col, markers=True,
                          color_discrete_sequence=[CYAN],
                          labels={date_col: "Month", val_col: "SIP Inflows (₹ Cr)"})
            fig2.update_layout(plot_bgcolor="white", height=400, margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("SIP inflow data not available.")

    # Category Inflows Breakdown
    st.markdown("#### Category-wise Inflow Distribution")
    if len(cat_df) > 0:
        cat_plot = cat_df.copy()
        cat_plot.columns = [c.lower().strip() for c in cat_plot.columns]
        cat_col = next((c for c in cat_plot.columns if "category" in c or "type" in c), cat_plot.columns[0])
        val_col = next((c for c in cat_plot.columns if "inflow" in c or "amount" in c or "net" in c), cat_plot.columns[-1])
        cat_plot[val_col] = pd.to_numeric(cat_plot[val_col], errors="coerce")
        latest_cat = cat_plot.dropna(subset=[val_col])
        fig3 = px.pie(latest_cat.groupby(cat_col)[val_col].sum().reset_index(),
                      names=cat_col, values=val_col, hole=0.4,
                      color_discrete_sequence=px.colors.qualitative.Bold)
        fig3.update_layout(height=350, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig3, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2: FUND PERFORMANCE
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📈 Fund Performance":
    st.markdown("""<div class="hero-banner"><h2>📈 Fund Performance Dashboard</h2>
    <p>Sharpe Ratio · CAGR · Alpha/Beta · Risk-Return Analysis</p></div>""",
    unsafe_allow_html=True)

    scorecard = load_scorecard()
    fund_master = load_fund_master()
    nav_df = load_nav()

    # ── Slicers ──
    col1, col2, col3 = st.columns(3)
    with col1:
        cats = ["All"] + sorted(scorecard["category"].dropna().unique().tolist()) if "category" in scorecard.columns else ["All"]
        sel_cat = st.selectbox("📁 Category", cats)
    with col2:
        risk_grades = ["All"] + sorted(scorecard["risk_grade"].dropna().unique().tolist()) if "risk_grade" in scorecard.columns else ["All"]
        sel_risk = st.selectbox("⚠️ Risk Grade", risk_grades)
    with col3:
        min_sharpe = st.slider("📐 Min Sharpe Ratio", float(scorecard["sharpe_ratio"].min() if "sharpe_ratio" in scorecard.columns else 0),
                               float(scorecard["sharpe_ratio"].max() if "sharpe_ratio" in scorecard.columns else 3), 0.0)

    # Filter
    df = scorecard.copy()
    if sel_cat != "All" and "category" in df.columns:
        df = df[df["category"] == sel_cat]
    if sel_risk != "All" and "risk_grade" in df.columns:
        df = df[df["risk_grade"] == sel_risk]
    if "sharpe_ratio" in df.columns:
        df = df[df["sharpe_ratio"] >= min_sharpe]

    # ── KPI Cards ──
    st.markdown("### Filtered Fund Statistics")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Funds Shown", str(len(df)))
    k2.metric("Avg Sharpe Ratio", f"{df['sharpe_ratio'].mean():.2f}" if "sharpe_ratio" in df.columns else "N/A")
    k3.metric("Avg 3Y CAGR", f"{df['cagr_3yr_pct'].mean():.1f}%" if "cagr_3yr_pct" in df.columns else "N/A")
    k4.metric("Avg Max Drawdown", f"{df['max_drawdown_pct'].mean():.1f}%" if "max_drawdown_pct" in df.columns else "N/A")

    st.markdown("---")
    col_l, col_r = st.columns(2)

    with col_l:
        # Risk-Return Scatter
        st.markdown("#### Risk-Return Scatter Plot")
        if all(c in df.columns for c in ["ann_volatility_pct", "cagr_3yr_pct", "sharpe_ratio"]):
            fig = px.scatter(df.dropna(subset=["ann_volatility_pct", "cagr_3yr_pct"]),
                x="ann_volatility_pct", y="cagr_3yr_pct",
                size="sharpe_ratio", color="risk_grade" if "risk_grade" in df.columns else None,
                hover_name="scheme_name" if "scheme_name" in df.columns else None,
                labels={"ann_volatility_pct": "Annualized Volatility (%)", "cagr_3yr_pct": "3Y CAGR (%)"},
                color_discrete_map={"Low": GREEN, "Moderate": AMBER, "High": RED})
            fig.update_layout(plot_bgcolor="white", height=380)
            st.plotly_chart(fig, use_container_width=True)

    with col_r:
        # Top Funds by Sharpe
        st.markdown("#### Top 10 Funds by Sharpe Ratio")
        if "sharpe_ratio" in df.columns and "scheme_name" in df.columns:
            top10 = df.nlargest(10, "sharpe_ratio")[["scheme_name", "sharpe_ratio", "cagr_3yr_pct", "risk_grade"]]
            top10["scheme_name"] = top10["scheme_name"].str[:35]
            fig2 = px.bar(top10, x="sharpe_ratio", y="scheme_name", orientation="h",
                         color="risk_grade" if "risk_grade" in top10.columns else None,
                         color_discrete_map={"Low": GREEN, "Moderate": AMBER, "High": RED},
                         labels={"sharpe_ratio": "Sharpe Ratio", "scheme_name": ""})
            fig2.update_layout(plot_bgcolor="white", height=380, showlegend=False)
            st.plotly_chart(fig2, use_container_width=True)

    # ── Full Scorecard Table ──
    st.markdown("#### 📋 Full Fund Scorecard")
    display_cols = [c for c in ["scheme_name", "category", "cagr_1yr_pct", "cagr_3yr_pct", "sharpe_ratio",
                                "sortino_ratio", "max_drawdown_pct", "var_95_pct", "risk_grade", "morningstar_rating"]
                    if c in df.columns]
    st.dataframe(df[display_cols].reset_index(drop=True), use_container_width=True, height=350)

    # ── NAV Trend Comparison ──
    st.markdown("#### 📉 NAV Trend Comparison (Select Funds)")
    fund_names = nav_df.merge(fund_master[["amfi_code", "scheme_name"]], on="amfi_code", how="left")["scheme_name"].dropna().unique().tolist()
    selected_funds = st.multiselect("Select funds to compare", sorted(fund_names), default=sorted(fund_names)[:3])
    if selected_funds:
        nav_merged = nav_df.merge(fund_master[["amfi_code", "scheme_name"]], on="amfi_code", how="left")
        nav_sel = nav_merged[nav_merged["scheme_name"].isin(selected_funds)]
        fig3 = px.line(nav_sel, x="date", y="nav", color="scheme_name",
                       labels={"date": "Date", "nav": "NAV (₹)", "scheme_name": "Fund"})
        fig3.update_layout(plot_bgcolor="white", height=350, legend=dict(orientation="h", y=-0.25))
        st.plotly_chart(fig3, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 3: INVESTOR ANALYTICS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "👥 Investor Analytics":
    st.markdown("""<div class="hero-banner"><h2>👥 Investor Analytics</h2>
    <p>Demographic segmentation · State-wise flows · City tier analysis · Transaction patterns</p></div>""",
    unsafe_allow_html=True)

    tx = load_transactions()

    # ── Slicers ──
    col1, col2, col3 = st.columns(3)
    with col1:
        tx_types = ["All"] + sorted(tx["transaction_type"].dropna().unique().tolist()) if "transaction_type" in tx.columns else ["All"]
        sel_tx = st.selectbox("💳 Transaction Type", tx_types)
    with col2:
        age_grps = ["All"] + sorted(tx["age_group"].dropna().unique().tolist()) if "age_group" in tx.columns else ["All"]
        sel_age = st.selectbox("🎂 Age Group", age_grps)
    with col3:
        genders = ["All"] + sorted(tx["gender"].dropna().unique().tolist()) if "gender" in tx.columns else ["All"]
        sel_gender = st.selectbox("🧑 Gender", genders)

    # Filter
    df = tx.copy()
    if sel_tx != "All" and "transaction_type" in df.columns:
        df = df[df["transaction_type"] == sel_tx]
    if sel_age != "All" and "age_group" in df.columns:
        df = df[df["age_group"] == sel_age]
    if sel_gender != "All" and "gender" in df.columns:
        df = df[df["gender"] == sel_gender]

    # ── KPI Cards ──
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Transactions", f"{len(df):,}")
    k2.metric("Unique Investors", f"{df['investor_id'].nunique():,}" if "investor_id" in df.columns else "N/A")
    k3.metric("Total Volume", f"₹{df['amount_inr'].sum()/1e7:.1f}Cr" if "amount_inr" in df.columns else "N/A")
    k4.metric("Avg Ticket Size", f"₹{df['amount_inr'].mean():,.0f}" if "amount_inr" in df.columns else "N/A")

    st.markdown("---")
    col_l, col_r = st.columns(2)

    with col_l:
        # State-wise inflows
        st.markdown("#### State-wise Transaction Volume")
        if "state" in df.columns and "amount_inr" in df.columns:
            state_vol = df.groupby("state")["amount_inr"].sum().sort_values(ascending=False).head(15)
            fig = px.bar(state_vol.reset_index(), x="state", y="amount_inr",
                        color_discrete_sequence=[BLUE],
                        labels={"state": "State", "amount_inr": "Amount (₹)"})
            fig.update_layout(plot_bgcolor="white", height=350, xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)

    with col_r:
        # Age group breakdown
        st.markdown("#### Age Group & Gender Distribution")
        if "age_group" in df.columns and "gender" in df.columns:
            age_gen = df.groupby(["age_group", "gender"])["amount_inr"].sum().reset_index()
            fig2 = px.bar(age_gen, x="age_group", y="amount_inr", color="gender",
                          barmode="group", color_discrete_sequence=[BLUE, CYAN],
                          labels={"age_group": "Age Group", "amount_inr": "Amount (₹)"})
            fig2.update_layout(plot_bgcolor="white", height=350)
            st.plotly_chart(fig2, use_container_width=True)

    # City tier breakdown
    st.markdown("#### T30 vs B30 City Tier Analysis")
    if "city_tier" in df.columns and "amount_inr" in df.columns:
        tier_df = df.groupby("city_tier").agg(
            total_amount=("amount_inr", "sum"),
            transactions=("amount_inr", "count"),
            avg_ticket=("amount_inr", "mean")
        ).reset_index()
        fig3 = px.pie(tier_df, names="city_tier", values="total_amount", hole=0.45,
                     color_discrete_sequence=[BLUE, CYAN, GREEN, AMBER])
        fig3.update_layout(height=300)
        st.plotly_chart(fig3, use_container_width=True)
        st.dataframe(tier_df, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 4: FUND RECOMMENDER
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🎯 Fund Recommender":
    st.markdown("""<div class="hero-banner"><h2>🎯 AI-Powered Fund Recommender</h2>
    <p>Risk-appetite based fund selection using Sharpe-optimal algorithmic matching</p></div>""",
    unsafe_allow_html=True)

    scorecard = load_scorecard()

    st.markdown("### Investor Preference Profile")
    col1, col2, col3 = st.columns(3)
    with col1:
        risk_appetite = st.selectbox("⚠️ Risk Appetite", ["Low", "Moderate", "High"])
    with col2:
        investment_horizon = st.selectbox("⏳ Investment Horizon", ["Short (< 1 yr)", "Medium (1–3 yr)", "Long (3+ yr)"])
    with col3:
        top_n = st.slider("🔢 Number of Recommendations", 3, 10, 5)

    # Optional Filters
    with st.expander("⚙️ Advanced Filters"):
        col_a, col_b = st.columns(2)
        with col_a:
            categories = ["All"] + sorted(scorecard["category"].dropna().unique().tolist()) if "category" in scorecard.columns else ["All"]
            sel_cat = st.multiselect("Fund Categories", options=[c for c in categories if c != "All"])
        with col_b:
            min_aum = st.number_input("Min AUM (₹ Crore)", min_value=0, value=0, step=500)

    # Recommendation Logic
    if st.button("🚀 Get Fund Recommendations", type="primary"):
        df = scorecard.copy()

        # Risk filter
        if "risk_grade" in df.columns:
            df = df[df["risk_grade"].str.lower() == risk_appetite.lower()]

        # Category filter
        if sel_cat and "category" in df.columns:
            df = df[df["category"].isin(sel_cat)]

        # AUM filter
        if min_aum > 0 and "aum_crore" in df.columns:
            df = df[df["aum_crore"] >= min_aum]

        # Sort by Sharpe Ratio
        if "sharpe_ratio" in df.columns:
            df = df.sort_values("sharpe_ratio", ascending=False)

        result = df.head(top_n).reset_index(drop=True)

        if result.empty:
            st.warning("No funds match the selected criteria. Try adjusting your filters.")
        else:
            st.markdown(f"### 🏆 Top {len(result)} Recommendations for **{risk_appetite} Risk** Investors")
            
            for i, row in result.iterrows():
                with st.container():
                    st.markdown(f"""
                    <div class="insight-card">
                    <strong>#{i+1} — {row.get('scheme_name', 'Fund')}</strong><br>
                    <small>{row.get('fund_house', '')} | {row.get('category', '')} | {row.get('risk_grade', '')} Risk</small>
                    </div>
                    """, unsafe_allow_html=True)
                    c1, c2, c3, c4, c5 = st.columns(5)
                    c1.metric("Sharpe", f"{row.get('sharpe_ratio', 0):.2f}")
                    c2.metric("3Y CAGR", f"{row.get('cagr_3yr_pct', 0):.1f}%")
                    c3.metric("1Y CAGR", f"{row.get('cagr_1yr_pct', 0):.1f}%")
                    c4.metric("Max DD", f"{row.get('max_drawdown_pct', 0):.1f}%")
                    c5.metric("⭐ Rating", str(row.get('morningstar_rating', 'N/A')))

            # Comparison bar chart
            if "sharpe_ratio" in result.columns:
                fig = px.bar(result, x="sharpe_ratio",
                            y=result["scheme_name"].str[:35] if "scheme_name" in result.columns else result.index,
                            orientation="h", color="cagr_3yr_pct" if "cagr_3yr_pct" in result.columns else None,
                            color_continuous_scale="Viridis",
                            labels={"sharpe_ratio": "Sharpe Ratio", "y": ""},
                            title="Recommended Funds — Sharpe Ratio Comparison")
                fig.update_layout(plot_bgcolor="white", height=350)
                st.plotly_chart(fig, use_container_width=True)

            # Download button
            csv_out = result.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Download Recommendations CSV", csv_out, "recommendations.csv", "text/csv")
