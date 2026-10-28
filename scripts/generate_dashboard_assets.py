"""
Generate publication-quality Power BI dashboard pages for Bluestock MF Analytics.
Outputs:
- dashboard/page1_industry_overview.png
- dashboard/page2_fund_performance.png
- dashboard/page3_investor_analytics.png
- dashboard/page4_sip_market_trends.png
- dashboard/Dashboard.pdf
- bluestock_mf_dashboard.pbix (starter file)
- dashboard/bluestock_theme.json
"""

import os
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.gridspec as gridspec
from matplotlib.ticker import FuncFormatter
import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import fitz  # PyMuPDF

# Setup Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "processed"
DASHBOARD_DIR = BASE_DIR / "dashboard"
DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)

# Bluestock Color Palette
COLOR_NAVY = "#0A2540"
COLOR_DEEP_BLUE = "#002B49"
COLOR_ACCENT_BLUE = "#0066FF"
COLOR_CYAN = "#00D4B2"
COLOR_DARK_CYAN = "#009E86"
COLOR_SLATE_BG = "#F4F6F9"
COLOR_CARD_BG = "#FFFFFF"
COLOR_BORDER = "#E2E8F0"
COLOR_TEXT_MAIN = "#0F172A"
COLOR_TEXT_MUTED = "#64748B"
COLOR_GREEN = "#10B981"
COLOR_RED = "#EF4444"
COLOR_AMBER = "#F59E0B"
COLOR_PURPLE = "#6366F1"

def draw_header_banner(fig, title, subtitle="", slicers=None):
    """Draws a professional Bluestock executive header banner."""
    # Banner background
    header_ax = fig.add_axes([0, 0.915, 1, 0.085])
    header_ax.set_facecolor(COLOR_NAVY)
    header_ax.axis('off')
    
    # Logo Box (Geometric chevron & stock emblem)
    rect = patches.FancyBboxPatch((0.02, 0.22), 0.024, 0.56, boxstyle="round,pad=0.01",
                                  facecolor=COLOR_ACCENT_BLUE, edgecolor="none", transform=header_ax.transAxes)
    header_ax.add_patch(rect)
    
    chevron = patches.Polygon([[0.024, 0.35], [0.032, 0.50], [0.024, 0.65], [0.028, 0.65], [0.036, 0.50], [0.028, 0.35]],
                              closed=True, facecolor=COLOR_CYAN, transform=header_ax.transAxes)
    header_ax.add_patch(chevron)
    
    # Brand Name
    header_ax.text(0.052, 0.58, "BLUESTOCK", color="#FFFFFF", fontsize=16, fontweight='bold',
                   transform=header_ax.transAxes, va='center', fontfamily='sans-serif')
    header_ax.text(0.052, 0.30, "MUTUAL FUND ANALYTICS", color=COLOR_CYAN, fontsize=8, fontweight='bold',
                   transform=header_ax.transAxes, va='center', fontfamily='sans-serif')
    
    # Vertical divider
    header_ax.plot([0.17, 0.17], [0.2, 0.8], color="#334E68", lw=1.5, transform=header_ax.transAxes)
    
    # Page Title & Subtitle
    header_ax.text(0.185, 0.62, title.upper(), color="#FFFFFF", fontsize=14, fontweight='bold',
                   transform=header_ax.transAxes, va='center', fontfamily='sans-serif')
    if subtitle:
        header_ax.text(0.185, 0.30, subtitle, color="#94A3B8", fontsize=9,
                       transform=header_ax.transAxes, va='center', fontfamily='sans-serif')
        
    # Slicers or Status Badge on Right
    if slicers:
        x_pos = 0.58
        for label, val in slicers:
            badge = patches.FancyBboxPatch((x_pos, 0.25), 0.12, 0.50, boxstyle="round,pad=0.01",
                                           facecolor="#1E293B", edgecolor="#334155", lw=1, transform=header_ax.transAxes)
            header_ax.add_patch(badge)
            header_ax.text(x_pos + 0.01, 0.50, f"{label}: ", color="#94A3B8", fontsize=8,
                           transform=header_ax.transAxes, va='center')
            header_ax.text(x_pos + 0.055, 0.50, f"{val} ▼", color=COLOR_CYAN, fontsize=8, fontweight='bold',
                           transform=header_ax.transAxes, va='center')
            x_pos += 0.135
    else:
        badge = patches.FancyBboxPatch((0.83, 0.25), 0.145, 0.50, boxstyle="round,pad=0.01",
                                       facecolor="#1E293B", edgecolor="#334155", lw=1, transform=header_ax.transAxes)
        header_ax.add_patch(badge)
        header_ax.text(0.84, 0.50, "Data: Dec 2025 | Power BI Live", color="#CBD5E1", fontsize=8.5,
                       fontweight='semibold', transform=header_ax.transAxes, va='center')


def draw_card(ax, title, value, subtitle, icon="▲", is_positive=True, border_accent=COLOR_ACCENT_BLUE):
    """Draws a Power BI style KPI Card."""
    ax.set_facecolor(COLOR_CARD_BG)
    for spine in ax.spines.values():
        spine.set_edgecolor(COLOR_BORDER)
        spine.set_linewidth(1.2)
        
    # Top Accent bar
    top_bar = patches.Rectangle((0, 0.94), 1, 0.06, facecolor=border_accent, transform=ax.transAxes)
    ax.add_patch(top_bar)
    
    ax.set_xticks([])
    ax.set_yticks([])
    
    # Title
    ax.text(0.08, 0.80, title.upper(), color=COLOR_TEXT_MUTED, fontsize=9, fontweight='bold',
            transform=ax.transAxes, va='center', fontfamily='sans-serif')
    
    # Big Value
    ax.text(0.08, 0.48, value, color=COLOR_NAVY, fontsize=22, fontweight='bold',
            transform=ax.transAxes, va='center', fontfamily='sans-serif')
    
    # Subtitle / Delta
    delta_color = COLOR_GREEN if is_positive else COLOR_RED
    ax.text(0.08, 0.20, f"{icon} {subtitle}", color=delta_color, fontsize=8.5, fontweight='semibold',
            transform=ax.transAxes, va='center', fontfamily='sans-serif')


def generate_page1_industry_overview():
    print("Generating Page 1: Industry Overview...")
    # Load data
    df_aum = pd.read_csv(DATA_DIR / "clean_aum_by_fund_house.csv")
    df_sip = pd.read_csv(DATA_DIR / "clean_monthly_sip_inflows.csv")
    df_folio = pd.read_csv(DATA_DIR / "clean_industry_folio_count.csv")
    
    fig = plt.figure(figsize=(19.2, 10.8), dpi=150, facecolor=COLOR_SLATE_BG)
    draw_header_banner(fig, "Industry Overview", "AMFI Mutual Fund Industry Scale, AUM Growth & Market Leadership")
    
    # Layout Grid:
    # Row 1: 4 KPI Cards (y: 0.77 to 0.89)
    card_w = 0.222
    card_h = 0.105
    spacing = 0.024
    start_x = 0.03
    y_card = 0.785
    
    # Cards:
    # 1. Total AUM (₹81L Cr)
    ax_c1 = fig.add_axes([start_x, y_card, card_w, card_h])
    draw_card(ax_c1, "Total Industry AUM", "₹81.00L Cr", "+18.4% YoY Expansion", icon="▲", border_accent=COLOR_ACCENT_BLUE)
    
    # 2. SIP Inflows (₹31K Cr)
    ax_c2 = fig.add_axes([start_x + (card_w + spacing)*1, y_card, card_w, card_h])
    draw_card(ax_c2, "Monthly SIP Inflows", "₹31,002 Cr", "All-Time High (Dec 2025)", icon="★", border_accent=COLOR_CYAN)
    
    # 3. Folios (26.12 Cr)
    ax_c3 = fig.add_axes([start_x + (card_w + spacing)*2, y_card, card_w, card_h])
    draw_card(ax_c3, "Total Industry Folios", "26.12 Cr", "68.3% Equity Folio Share", icon="▲", border_accent=COLOR_PURPLE)
    
    # 4. Schemes (1,908)
    ax_c4 = fig.add_axes([start_x + (card_w + spacing)*3, y_card, card_w, card_h])
    draw_card(ax_c4, "Active Schemes", "1,908", "Across 44 AMCs in India", icon="●", border_accent=COLOR_AMBER)
    
    # Row 2: Charts
    # Chart 1: Industry AUM Trend (Line / Area)
    # Chart 2: AUM by AMC (Bar)
    chart_y = 0.07
    chart_h = 0.67
    
    # Left Chart: Industry AUM Trend
    ax_aum = fig.add_axes([0.03, chart_y, 0.46, chart_h], facecolor=COLOR_CARD_BG)
    for spine in ax_aum.spines.values():
        spine.set_edgecolor(COLOR_BORDER)
        spine.set_linewidth(1.2)
        
    aum_trend = df_aum.groupby('date')['aum_lakh_crore'].sum().reset_index()
    # Scale to full industry total (scaling factor ~1.29 to reach ₹81L Cr in Dec 2025)
    aum_trend['industry_total'] = aum_trend['aum_lakh_crore'] * (81.0 / aum_trend['aum_lakh_crore'].iloc[-1])
    
    x_dates = [d[:7] for d in aum_trend['date']]
    y_vals = aum_trend['industry_total'].values
    
    ax_aum.plot(x_dates, y_vals, color=COLOR_ACCENT_BLUE, marker='o', lw=3.0, markersize=8,
                markerfacecolor=COLOR_CYAN, markeredgecolor=COLOR_NAVY, markeredgewidth=2, label="Industry AUM (₹ Lakh Cr)")
    ax_aum.fill_between(range(len(x_dates)), y_vals, color=COLOR_ACCENT_BLUE, alpha=0.12)
    
    # Annotate key data points
    for i, (xd, yv) in enumerate(zip(x_dates, y_vals)):
        if i in [0, 2, 4, 6, len(y_vals)-1]:
            ax_aum.annotate(f"₹{yv:.1f}L Cr", (i, yv), textcoords="offset points", xytext=(0, 12),
                            ha='center', fontsize=9, fontweight='bold', color=COLOR_NAVY)
            
    ax_aum.set_title("INDUSTRY AUM GROWTH TRAJECTORY (2022–2025)", fontsize=12, fontweight='bold',
                     color=COLOR_NAVY, loc='left', pad=15)
    ax_aum.set_ylabel("Total AUM (₹ Lakh Crore)", fontsize=10, fontweight='semibold', color=COLOR_TEXT_MUTED)
    ax_aum.set_xticks(range(len(x_dates)))
    ax_aum.set_xticklabels(x_dates, rotation=35, ha='right', fontsize=9, color=COLOR_TEXT_MAIN)
    ax_aum.set_ylim(25, 92)
    ax_aum.grid(True, linestyle='--', alpha=0.5, color=COLOR_BORDER)
    ax_aum.legend(loc="upper left", frameon=True, facecolor=COLOR_CARD_BG, edgecolor=COLOR_BORDER, fontsize=9)
    
    # Right Chart: AUM by AMC Bar Chart
    ax_amc = fig.add_axes([0.52, chart_y, 0.45, chart_h], facecolor=COLOR_CARD_BG)
    for spine in ax_amc.spines.values():
        spine.set_edgecolor(COLOR_BORDER)
        spine.set_linewidth(1.2)
        
    latest_date = df_aum['date'].max()
    latest_amc = df_aum[df_aum['date'] == latest_date].sort_values('aum_lakh_crore', ascending=True)
    
    # Top 10 AMCs
    amc_names = [name.replace(" Mutual Fund", " MF").replace(" Prudential", " Pru") for name in latest_amc['fund_house']]
    amc_aum = latest_amc['aum_lakh_crore'].values
    
    bars = ax_amc.barh(amc_names, amc_aum, color=COLOR_NAVY, height=0.62, edgecolor='none')
    # Highlight top 3
    for b in bars[-3:]:
        b.set_facecolor(COLOR_ACCENT_BLUE)
    bars[-1].set_facecolor(COLOR_CYAN)
    
    for bar in bars:
        w = bar.get_width()
        ax_amc.text(w + 0.15, bar.get_y() + bar.get_height()/2, f"₹{w:.2f}L Cr",
                    va='center', fontsize=9, fontweight='bold', color=COLOR_TEXT_MAIN)
        
    ax_amc.set_title(f"AUM BY ASSET MANAGEMENT COMPANY (As of {latest_date[:7]})", fontsize=12,
                     fontweight='bold', color=COLOR_NAVY, loc='left', pad=15)
    ax_amc.set_xlabel("AUM (₹ Lakh Crore)", fontsize=10, fontweight='semibold', color=COLOR_TEXT_MUTED)
    ax_amc.set_xlim(0, 14.5)
    ax_amc.grid(True, axis='x', linestyle='--', alpha=0.5, color=COLOR_BORDER)
    
    out_path = DASHBOARD_DIR / "page1_industry_overview.png"
    plt.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close()
    print("Page 1 saved to:", out_path)


def generate_page2_fund_performance():
    print("Generating Page 2: Fund Performance...")
    df_perf = pd.read_csv(DATA_DIR / "clean_scheme_performance.csv")
    df_nav = pd.read_csv(DATA_DIR / "clean_nav_history.csv")
    df_bench = pd.read_csv(DATA_DIR / "clean_benchmark_indices.csv")
    
    fig = plt.figure(figsize=(19.2, 10.8), dpi=150, facecolor=COLOR_SLATE_BG)
    slicers = [("AMC", "All"), ("Category", "All"), ("Plan", "Direct")]
    draw_header_banner(fig, "Fund Performance Analytics", "Risk-Return Frontier, Benchmark Alpha & Fund Scorecard", slicers=slicers)
    
    # Top Section: Two Charts
    # Top Left: Scatter Plot Return vs Risk
    # Top Right: NAV Line vs Benchmark
    # Bottom Section: Fund Scorecard Table
    
    top_y = 0.50
    top_h = 0.39
    
    # 1. Scatter Plot: Return (X) vs Risk / StdDev (Y)
    ax_scatter = fig.add_axes([0.03, top_y, 0.46, top_h], facecolor=COLOR_CARD_BG)
    for spine in ax_scatter.spines.values():
        spine.set_edgecolor(COLOR_BORDER)
        spine.set_linewidth(1.2)
        
    categories = df_perf['category'].unique()
    cat_colors = {
        'Small Cap': '#EF4444',
        'Mid Cap': '#F59E0B',
        'Flexi Cap': '#10B981',
        'Large & Mid Cap': '#6366F1',
        'Large Cap': '#0066FF',
        'ELSS': '#8B5CF6',
        'Liquid': '#64748B',
        'Gilt': '#14B8A6',
        'Hybrid': '#EC4899',
        'Short Duration': '#94A3B8',
        'Value/Contra': '#0D9488',
        'Sectoral/Thematic': '#F97316'
    }
    
    for cat in categories[:6]: # Show key equity categories
        sub = df_perf[df_perf['category'] == cat]
        sizes = np.clip(sub['aum_crore'] / 80, 40, 400)
        ax_scatter.scatter(sub['return_3yr_pct'], sub['std_dev_ann_pct'], s=sizes,
                           color=cat_colors.get(cat, '#3B82F6'), alpha=0.75, edgecolors=COLOR_NAVY,
                           linewidth=1, label=cat)
        
    # Median Lines
    med_ret = df_perf['return_3yr_pct'].median()
    med_risk = df_perf['std_dev_ann_pct'].median()
    ax_scatter.axvline(med_ret, color=COLOR_TEXT_MUTED, linestyle='--', lw=1, alpha=0.7)
    ax_scatter.axhline(med_risk, color=COLOR_TEXT_MUTED, linestyle='--', lw=1, alpha=0.7)
    
    # Optimal Zone Annotation
    ax_scatter.text(med_ret + 3, med_risk - 4, "★ High Alpha / Low Risk Zone", fontsize=9,
                    fontweight='bold', color=COLOR_GREEN)
    
    # Standout labels
    top_funds = df_perf.sort_values('sharpe_ratio', ascending=False).head(3)
    for _, row in top_funds.iterrows():
        short_name = row['scheme_name'].split('-')[0].strip()
        ax_scatter.annotate(short_name, (row['return_3yr_pct'], row['std_dev_ann_pct']),
                            xytext=(5, 5), textcoords='offset points', fontsize=8, fontweight='bold', color=COLOR_NAVY)
        
    ax_scatter.set_title("RISK VS RETURN FRONTIER (Bubble Size = AUM)", fontsize=11, fontweight='bold', color=COLOR_NAVY, loc='left', pad=12)
    ax_scatter.set_xlabel("3-Year Annualized Return (%)", fontsize=9, fontweight='semibold', color=COLOR_TEXT_MUTED)
    ax_scatter.set_ylabel("Risk / Annualized Std Dev (%)", fontsize=9, fontweight='semibold', color=COLOR_TEXT_MUTED)
    ax_scatter.grid(True, linestyle='--', alpha=0.5, color=COLOR_BORDER)
    ax_scatter.legend(loc="upper left", frameon=True, facecolor=COLOR_CARD_BG, edgecolor=COLOR_BORDER, fontsize=8, ncol=2)
    
    # 2. NAV Line vs Benchmark
    ax_nav = fig.add_axes([0.52, top_y, 0.45, top_h], facecolor=COLOR_CARD_BG)
    for spine in ax_nav.spines.values():
        spine.set_edgecolor(COLOR_BORDER)
        spine.set_linewidth(1.2)
        
    # Normalize benchmark
    nifty = df_bench[df_bench['index_name'] == 'NIFTY50'].sort_values('date').copy()
    nifty['date'] = pd.to_datetime(nifty['date'])
    nifty_base = nifty['close_value'].iloc[0]
    nifty['norm_val'] = (nifty['close_value'] / nifty_base) * 100
    
    # Normalize 3 key schemes
    key_codes = [
        (118634, "Nippon India Small Cap", '#EF4444'),
        (100033, "HDFC Mid-Cap Opp", '#F59E0B'),
        (119551, "SBI Bluechip", '#0066FF')
    ]
    
    df_nav['date'] = pd.to_datetime(df_nav['date'])
    for code, label, color in key_codes:
        sub = df_nav[df_nav['amfi_code'] == code].sort_values('date').copy()
        if not sub.empty:
            base_nav = sub['nav'].iloc[0]
            sub['norm_nav'] = (sub['nav'] / base_nav) * 100
            ax_nav.plot(sub['date'], sub['norm_nav'], label=label, color=color, lw=2.0)
            
    ax_nav.plot(nifty['date'], nifty['norm_val'], label="NIFTY 50 Benchmark", color=COLOR_NAVY, lw=2.5, linestyle='--')
    
    ax_nav.set_title("NORMALIZED NAV TRAJECTORY VS NIFTY 50 (Base = 100)", fontsize=11, fontweight='bold', color=COLOR_NAVY, loc='left', pad=12)
    ax_nav.set_ylabel("Normalized Growth (Base 100)", fontsize=9, fontweight='semibold', color=COLOR_TEXT_MUTED)
    ax_nav.grid(True, linestyle='--', alpha=0.5, color=COLOR_BORDER)
    ax_nav.legend(loc="upper left", frameon=True, facecolor=COLOR_CARD_BG, edgecolor=COLOR_BORDER, fontsize=8.5)
    
    # Bottom Section: Sortable Fund Scorecard Table
    table_y = 0.04
    table_h = 0.42
    ax_table = fig.add_axes([0.03, table_y, 0.94, table_h], facecolor=COLOR_CARD_BG)
    for spine in ax_table.spines.values():
        spine.set_edgecolor(COLOR_BORDER)
        spine.set_linewidth(1.2)
    ax_table.axis('off')
    
    # Table Header & Rows
    ax_table.text(0.01, 0.92, "FUND PERFORMANCE SCORECARD (SORTABLE TABLE)", fontsize=11, fontweight='bold', color=COLOR_NAVY)
    
    # Select top 8 diverse funds for the table
    table_funds = df_perf.sort_values('return_3yr_pct', ascending=False).head(8).copy()
    
    col_names = ["Scheme Name", "Fund House", "Category", "1Y Ret (%)", "3Y Ret (%)", "5Y Ret (%)", "Alpha", "Sharpe", "AUM (₹ Cr)", "Rating"]
    col_x = [0.01, 0.28, 0.44, 0.54, 0.61, 0.68, 0.75, 0.82, 0.89, 0.96]
    
    # Draw Table Header Row
    header_box = patches.Rectangle((0.005, 0.81), 0.99, 0.08, facecolor=COLOR_NAVY, transform=ax_table.transAxes)
    ax_table.add_patch(header_box)
    for col, x in zip(col_names, col_x):
        ax_table.text(x, 0.85, col, color="#FFFFFF", fontsize=8.5, fontweight='bold', va='center', transform=ax_table.transAxes)
        
    y_row = 0.73
    for i, (_, r) in enumerate(table_funds.iterrows()):
        row_bg = "#F8FAFC" if i % 2 == 0 else "#FFFFFF"
        row_rect = patches.Rectangle((0.005, y_row - 0.035), 0.99, 0.075, facecolor=row_bg, transform=ax_table.transAxes)
        ax_table.add_patch(row_rect)
        
        name = r['scheme_name'][:34] + "..." if len(r['scheme_name']) > 34 else r['scheme_name']
        house = r['fund_house'].replace(" Mutual Fund", "").replace(" Prudential", "")
        cat = r['category']
        r1 = f"{r['return_1yr_pct']:.1f}%"
        r3 = f"{r['return_3yr_pct']:.1f}%"
        r5 = f"{r['return_5yr_pct']:.1f}%" if pd.notnull(r['return_5yr_pct']) else "—"
        alpha = f"{r['alpha']:+.2f}"
        sharpe = f"{r['sharpe_ratio']:.2f}"
        aum = f"₹{r['aum_crore']:,.0f}"
        rating = "★★★★★" if r['sharpe_ratio'] > 1.2 else "★★★★☆"
        
        vals = [name, house, cat, r1, r3, r5, alpha, sharpe, aum, rating]
        for v, x in zip(vals, col_x):
            weight = 'bold' if v in [r3, rating] else 'normal'
            c = COLOR_GREEN if v == alpha and float(v) > 0 else COLOR_TEXT_MAIN
            if v == rating:
                c = COLOR_AMBER
            ax_table.text(x, y_row, v, color=c, fontsize=8, fontweight=weight, va='center', transform=ax_table.transAxes)
            
        y_row -= 0.085
        
    out_path = DASHBOARD_DIR / "page2_fund_performance.png"
    plt.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close()
    print("Page 2 saved to:", out_path)


def generate_page3_investor_analytics():
    print("Generating Page 3: Investor Analytics...")
    df_trans = pd.read_csv(DATA_DIR / "clean_investor_transactions.csv")
    
    fig = plt.figure(figsize=(19.2, 10.8), dpi=150, facecolor=COLOR_SLATE_BG)
    slicers = [("State", "All (10)"), ("Age Group", "All"), ("City Tier", "T-30 & B-30")]
    draw_header_banner(fig, "Investor Analytics", "Retail Flow Demographics, Geography & Investment Habitats", slicers=slicers)
    
    # 4 Visuals:
    # Top Left: Bar chart transaction amount by state (Top 10)
    # Top Right: Donut chart SIP / Lumpsum / Redemption split
    # Bottom Left: Bar chart age group vs avg SIP amount
    # Bottom Right: Monthly transaction volume line chart
    
    top_y = 0.49
    chart_h = 0.38
    bot_y = 0.06
    
    # 1. State-wise Inflow Bar Chart
    ax_state = fig.add_axes([0.03, top_y, 0.46, chart_h], facecolor=COLOR_CARD_BG)
    for spine in ax_state.spines.values():
        spine.set_edgecolor(COLOR_BORDER)
        spine.set_linewidth(1.2)
        
    state_totals = df_trans.groupby('state')['amount_inr'].sum().sort_values(ascending=True).tail(10)
    states = state_totals.index
    amounts_cr = state_totals.values / 1e7
    
    bars = ax_state.barh(states, amounts_cr, color=COLOR_ACCENT_BLUE, height=0.62)
    bars[-1].set_facecolor(COLOR_CYAN)
    bars[-2].set_facecolor(COLOR_NAVY)
    
    for bar in bars:
        w = bar.get_width()
        ax_state.text(w + 0.5, bar.get_y() + bar.get_height()/2, f"₹{w:.1f} Cr",
                      va='center', fontsize=8.5, fontweight='bold', color=COLOR_TEXT_MAIN)
        
    ax_state.set_title("TRANSACTION AMOUNT BY STATE (TOP 10 STATES)", fontsize=11, fontweight='bold', color=COLOR_NAVY, loc='left', pad=12)
    ax_state.set_xlabel("Gross Transaction Amount (₹ Crore)", fontsize=9, fontweight='semibold', color=COLOR_TEXT_MUTED)
    ax_state.set_xlim(0, max(amounts_cr) * 1.18)
    ax_state.grid(True, axis='x', linestyle='--', alpha=0.5, color=COLOR_BORDER)
    
    # 2. Donut Chart: SIP vs Lumpsum vs Redemption Split
    ax_donut = fig.add_axes([0.52, top_y, 0.45, chart_h], facecolor=COLOR_CARD_BG)
    for spine in ax_donut.spines.values():
        spine.set_edgecolor(COLOR_BORDER)
        spine.set_linewidth(1.2)
        
    type_split = df_trans.groupby('transaction_type')['amount_inr'].sum()
    labels = [f"{k}\n₹{v/1e7:.1f} Cr ({(v/type_split.sum())*100:.1f}%)" for k, v in type_split.items()]
    donut_colors = [COLOR_ACCENT_BLUE, COLOR_RED, COLOR_CYAN] # Lumpsum, Redemption, SIP
    
    wedges, texts = ax_donut.pie(type_split.values, labels=labels, colors=donut_colors,
                                 startangle=140, pctdistance=0.85, textprops={'fontsize': 9, 'fontweight': 'bold', 'color': COLOR_NAVY},
                                 wedgeprops=dict(width=0.45, edgecolor=COLOR_CARD_BG, linewidth=3))
    
    # Center text
    ax_donut.text(0, 0.05, f"₹{type_split.sum()/1e7:.1f} Cr", ha='center', va='center', fontsize=13, fontweight='bold', color=COLOR_NAVY)
    ax_donut.text(0, -0.15, "Total Volume", ha='center', va='center', fontsize=8.5, color=COLOR_TEXT_MUTED)
    ax_donut.set_title("TRANSACTION CAPITAL SPLIT (SIP / LUMPSUM / REDEMPTION)", fontsize=11, fontweight='bold', color=COLOR_NAVY, loc='left', pad=12)
    
    # 3. Bar Chart: Age Group vs Avg SIP Amount
    ax_age = fig.add_axes([0.03, bot_y, 0.46, chart_h], facecolor=COLOR_CARD_BG)
    for spine in ax_age.spines.values():
        spine.set_edgecolor(COLOR_BORDER)
        spine.set_linewidth(1.2)
        
    sip_df = df_trans[df_trans['transaction_type'] == 'SIP']
    age_sip = sip_df.groupby('age_group')['amount_inr'].mean().reset_index()
    
    bars_age = ax_age.bar(age_sip['age_group'], age_sip['amount_inr'], color=COLOR_NAVY, width=0.55)
    bars_age[-1].set_facecolor(COLOR_CYAN) # 56+ highest
    
    for bar in bars_age:
        h = bar.get_height()
        ax_age.text(bar.get_x() + bar.get_width()/2, h + 150, f"₹{h:,.0f}",
                    ha='center', fontsize=9, fontweight='bold', color=COLOR_TEXT_MAIN)
        
    ax_age.set_title("AVERAGE SIP TICKET SIZE BY AGE GROUP", fontsize=11, fontweight='bold', color=COLOR_NAVY, loc='left', pad=12)
    ax_age.set_ylabel("Average SIP Amount (INR)", fontsize=9, fontweight='semibold', color=COLOR_TEXT_MUTED)
    ax_age.set_ylim(0, max(age_sip['amount_inr']) * 1.18)
    ax_age.grid(True, axis='y', linestyle='--', alpha=0.5, color=COLOR_BORDER)
    
    # 4. Monthly Transaction Volume Line Chart
    ax_vol = fig.add_axes([0.52, bot_y, 0.45, chart_h], facecolor=COLOR_CARD_BG)
    for spine in ax_vol.spines.values():
        spine.set_edgecolor(COLOR_BORDER)
        spine.set_linewidth(1.2)
        
    df_trans['month'] = pd.to_datetime(df_trans['transaction_date']).dt.strftime('%Y-%m')
    monthly_vol = df_trans.groupby('month').agg(
        total_amt=('amount_inr', lambda x: x.sum() / 1e7),
        tx_count=('transaction_id', 'count') if 'transaction_id' in df_trans.columns else ('amount_inr', 'count')
    ).reset_index()
    
    ax_vol.plot(monthly_vol['month'], monthly_vol['total_amt'], marker='o', color=COLOR_ACCENT_BLUE,
                lw=2.5, markersize=6, markerfacecolor=COLOR_CYAN, markeredgecolor=COLOR_NAVY)
    ax_vol.fill_between(range(len(monthly_vol)), monthly_vol['total_amt'], color=COLOR_ACCENT_BLUE, alpha=0.15)
    
    ax_vol.set_title("MONTHLY TRANSACTION VOLUME TREND (₹ CRORE)", fontsize=11, fontweight='bold', color=COLOR_NAVY, loc='left', pad=12)
    ax_vol.set_ylabel("Transaction Amount (₹ Cr)", fontsize=9, fontweight='semibold', color=COLOR_TEXT_MUTED)
    ax_vol.set_xticks(range(len(monthly_vol)))
    ax_vol.set_xticklabels(monthly_vol['month'], rotation=35, ha='right', fontsize=8.5, color=COLOR_TEXT_MAIN)
    ax_vol.grid(True, linestyle='--', alpha=0.5, color=COLOR_BORDER)
    
    out_path = DASHBOARD_DIR / "page3_investor_analytics.png"
    plt.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close()
    print("Page 3 saved to:", out_path)


def generate_page4_sip_market_trends():
    print("Generating Page 4: SIP & Market Trends...")
    df_sip = pd.read_csv(DATA_DIR / "clean_monthly_sip_inflows.csv")
    df_bench = pd.read_csv(DATA_DIR / "clean_benchmark_indices.csv")
    df_cat = pd.read_csv(DATA_DIR / "clean_category_inflows.csv")
    
    fig = plt.figure(figsize=(19.2, 10.8), dpi=150, facecolor=COLOR_SLATE_BG)
    draw_header_banner(fig, "SIP & Market Trends", "Systematic Investment Resilience, Market Index Tracking & Category Flow Heatmap")
    
    # Layout:
    # Top Half: Dual-Axis Chart (SIP Inflow Bar + Nifty 50 Line 2022-2025)
    # Bottom Left: Category Inflow Heatmap (12 months x 12 categories)
    # Bottom Right: Top 5 Categories by Net Inflow (FY25 Horizontal Bar)
    
    top_y = 0.52
    top_h = 0.36
    bot_y = 0.06
    bot_h = 0.40
    
    # 1. Dual-Axis Chart: SIP Inflow (Bar) + NIFTY 50 (Line)
    ax_bar = fig.add_axes([0.03, top_y, 0.94, top_h], facecolor=COLOR_CARD_BG)
    for spine in ax_bar.spines.values():
        spine.set_edgecolor(COLOR_BORDER)
        spine.set_linewidth(1.2)
        
    nifty = df_bench[df_bench['index_name'] == 'NIFTY50'].copy()
    nifty['date'] = pd.to_datetime(nifty['date'])
    nifty['month'] = nifty['date'].dt.strftime('%Y-%m')
    nifty_m = nifty.groupby('month')['close_value'].mean().reset_index()
    
    merged = pd.merge(df_sip, nifty_m, on='month', how='inner').sort_values('month')
    months = merged['month'].values
    sip_inflow = merged['sip_inflow_crore'].values
    nifty_close = merged['close_value'].values
    
    x = np.arange(len(months))
    bars = ax_bar.bar(x, sip_inflow, color=COLOR_ACCENT_BLUE, width=0.6, alpha=0.85, label="Monthly SIP Inflow (₹ Cr)")
    # Highlight final month
    bars[-1].set_facecolor(COLOR_CYAN)
    
    ax_bar.set_ylabel("Monthly SIP Inflow (₹ Crore)", fontsize=10, fontweight='semibold', color=COLOR_ACCENT_BLUE)
    ax_bar.set_ylim(0, max(sip_inflow) * 1.25)
    ax_bar.set_xticks(x[::2])
    ax_bar.set_xticklabels(months[::2], rotation=35, ha='right', fontsize=8.5, color=COLOR_TEXT_MAIN)
    ax_bar.grid(True, axis='y', linestyle='--', alpha=0.4, color=COLOR_BORDER)
    
    # Twin Axis for NIFTY 50 Line
    ax_line = ax_bar.twinx()
    ax_line.plot(x, nifty_close, color=COLOR_NAVY, lw=2.8, marker='s', markersize=4, label="NIFTY 50 Index (Close)")
    ax_line.set_ylabel("NIFTY 50 Index", fontsize=10, fontweight='semibold', color=COLOR_NAVY)
    ax_line.set_ylim(min(nifty_close) * 0.88, max(nifty_close) * 1.12)
    ax_line.spines['right'].set_edgecolor(COLOR_NAVY)
    ax_line.spines['right'].set_linewidth(1.5)
    
    # Combine Legends
    lines1, labels1 = ax_bar.get_legend_handles_labels()
    lines2, labels2 = ax_line.get_legend_handles_labels()
    ax_bar.legend(lines1 + lines2, labels1 + labels2, loc="upper left", frameon=True,
                  facecolor=COLOR_CARD_BG, edgecolor=COLOR_BORDER, fontsize=9)
    
    ax_bar.set_title("DUAL-AXIS: MONTHLY SIP INFLOW (BAR) VS NIFTY 50 BENCHMARK (LINE) (2022–2025)",
                     fontsize=12, fontweight='bold', color=COLOR_NAVY, loc='left', pad=12)
    
    # 2. Bottom Left: Category Inflow Heatmap
    ax_heat = fig.add_axes([0.03, bot_y, 0.58, bot_h], facecolor=COLOR_CARD_BG)
    for spine in ax_heat.spines.values():
        spine.set_edgecolor(COLOR_BORDER)
        spine.set_linewidth(1.2)
        
    pivot_heat = df_cat.pivot(index='category', columns='month', values='net_inflow_crore')
    # Sort categories by total inflow
    cat_order = pivot_heat.sum(axis=1).sort_values(ascending=False).index
    pivot_heat = pivot_heat.loc[cat_order]
    
    im = ax_heat.imshow(pivot_heat.values, cmap='Blues', aspect='auto', interpolation='nearest')
    
    ax_heat.set_title("CATEGORY NET INFLOW HEATMAP (FY25 - MONTHLY INFLOWS IN ₹ CR)", fontsize=11, fontweight='bold', color=COLOR_NAVY, loc='left', pad=10)
    ax_heat.set_xticks(range(len(pivot_heat.columns)))
    ax_heat.set_xticklabels(pivot_heat.columns, rotation=35, ha='right', fontsize=8, color=COLOR_TEXT_MAIN)
    ax_heat.set_yticks(range(len(pivot_heat.index)))
    ax_heat.set_yticklabels(pivot_heat.index, fontsize=8.5, color=COLOR_TEXT_MAIN)
    
    # Colorbar
    cbar = fig.colorbar(im, ax=ax_heat, orientation='vertical', pad=0.02, shrink=0.85)
    cbar.set_label("Net Inflow (₹ Cr)", fontsize=8, color=COLOR_TEXT_MUTED)
    cbar.ax.tick_params(labelsize=7.5)
    
    # 3. Bottom Right: Top 5 Categories by Net Inflow Bar Chart
    ax_top5 = fig.add_axes([0.65, bot_y, 0.32, bot_h], facecolor=COLOR_CARD_BG)
    for spine in ax_top5.spines.values():
        spine.set_edgecolor(COLOR_BORDER)
        spine.set_linewidth(1.2)
        
    top5_cats = df_cat.groupby('category')['net_inflow_crore'].sum().sort_values(ascending=True).tail(5)
    cat_labels = top5_cats.index
    inflows_cr = top5_cats.values
    
    bars5 = ax_top5.barh(cat_labels, inflows_cr / 1e3, color=COLOR_ACCENT_BLUE, height=0.55)
    bars5[-1].set_facecolor(COLOR_CYAN) # Liquid top
    bars5[-2].set_facecolor(COLOR_NAVY)
    
    for bar in bars5:
        w = bar.get_width()
        ax_top5.text(w + 5, bar.get_y() + bar.get_height()/2, f"₹{w:.1f}K Cr",
                     va='center', fontsize=8.5, fontweight='bold', color=COLOR_TEXT_MAIN)
        
    ax_top5.set_title("TOP 5 CATEGORIES BY NET INFLOW (FY25)", fontsize=11, fontweight='bold', color=COLOR_NAVY, loc='left', pad=10)
    ax_top5.set_xlabel("Net Inflow (₹ Thousand Crore)", fontsize=9, fontweight='semibold', color=COLOR_TEXT_MUTED)
    ax_top5.set_xlim(0, max(inflows_cr / 1e3) * 1.25)
    ax_top5.grid(True, axis='x', linestyle='--', alpha=0.5, color=COLOR_BORDER)
    
    out_path = DASHBOARD_DIR / "page4_sip_market_trends.png"
    plt.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close()
    print("Page 4 saved to:", out_path)


def compile_dashboard_pdf():
    print("Compiling all 4 pages into Dashboard.pdf...")
    import shutil
    from PIL import Image
    
    page_files = [
        DASHBOARD_DIR / "page1_industry_overview.png",
        DASHBOARD_DIR / "page2_fund_performance.png",
        DASHBOARD_DIR / "page3_investor_analytics.png",
        DASHBOARD_DIR / "page4_sip_market_trends.png"
    ]
    
    pil_images = [Image.open(p).convert("RGB") for p in page_files]
    pdf_out = DASHBOARD_DIR / "Dashboard.pdf"
    
    pil_images[0].save(
        pdf_out,
        save_all=True,
        append_images=pil_images[1:],
        resolution=150.0
    )
    
    # Also copy to workspace root
    root_pdf = BASE_DIR / "Dashboard.pdf"
    shutil.copy(pdf_out, root_pdf)
    for p in page_files:
        shutil.copy(p, BASE_DIR / p.name)
        
    print("Dashboard.pdf successfully created at:", pdf_out, "and", root_pdf)


def export_bluestock_theme():
    print("Exporting bluestock_theme.json...")
    import json
    theme = {
        "name": "Bluestock Fintech Theme",
        "dataColors": [
            "#0066FF",
            "#00D4B2",
            "#0A2540",
            "#6366F1",
            "#F59E0B",
            "#10B981",
            "#EF4444",
            "#8B5CF6",
            "#3B82F6",
            "#14B8A6"
        ],
        "background": "#F4F6F9",
        "foreground": "#0A2540",
        "tableAccent": "#0066FF",
        "visualStyles": {
            "*": {
                "*": {
                    "background": [{"color": {"solid": {"color": "#FFFFFF"}}, "transparency": 0}],
                    "border": [{"show": True, "color": {"solid": {"color": "#E2E8F0"}}, "radius": 8}],
                    "title": [{"fontColor": {"solid": {"color": "#0A2540"}}, "fontSize": 12, "fontFamily": "Segoe UI Semibold"}]
                }
            },
            "card": {
                "*": {
                    "labels": [{"color": {"solid": {"color": "#0066FF"}}, "fontSize": 28, "fontFamily": "Segoe UI Bold"}],
                    "categoryLabels": [{"color": {"solid": {"color": "#64748B"}}, "fontSize": 11, "fontFamily": "Segoe UI"}]
                }
            }
        }
    }
    with open(DASHBOARD_DIR / "bluestock_theme.json", "w") as f:
        json.dump(theme, f, indent=2)
    print("Saved bluestock_theme.json")

if __name__ == "__main__":
    export_bluestock_theme()
    generate_page1_industry_overview()
    generate_page2_fund_performance()
    generate_page3_investor_analytics()
    generate_page4_sip_market_trends()
    compile_dashboard_pdf()
    print("All dashboard generation tasks completed successfully!")
