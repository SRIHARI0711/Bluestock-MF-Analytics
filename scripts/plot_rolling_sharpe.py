"""
Generate high-resolution rolling 90-day Sharpe ratio chart for 5 key mutual fund schemes.
"""

from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np

def generate_rolling_sharpe_chart():
    base_dir = Path(__file__).resolve().parent.parent
    nav_path = base_dir / "data" / "processed" / "clean_nav_history.csv"
    fund_path = base_dir / "data" / "processed" / "clean_fund_master.csv"
    
    df_nav = pd.read_csv(nav_path)
    df_funds = pd.read_csv(fund_path)
    
    df_nav['date'] = pd.to_datetime(df_nav['date'])
    df_nav = df_nav.sort_values(['amfi_code', 'date'])
    
    # Calculate daily returns
    df_nav['return'] = df_nav.groupby('amfi_code')['nav'].pct_change()
    
    # 5 Key Funds across diverse market capitalizations
    key_funds_meta = [
        {"amfi_code": 119551, "label": "SBI Bluechip (Large Cap)", "color": "#1f77b4", "linestyle": "-"},
        {"amfi_code": 100033, "label": "HDFC Mid-Cap Opportunities (Mid Cap)", "color": "#ff7f0e", "linestyle": "-"},
        {"amfi_code": 118634, "label": "Nippon India Small Cap (Small Cap)", "color": "#d62728", "linestyle": "-"},
        {"amfi_code": 120843, "label": "Kotak Flexicap (Flexi Cap)", "color": "#2ca02c", "linestyle": "-"},
        {"amfi_code": 148568, "label": "Mirae Asset Emerging Bluechip (Large & Mid)", "color": "#9467bd", "linestyle": "-"},
    ]
    
    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
    fig, ax = plt.subplots(figsize=(14, 7), dpi=300)
    
    # Plot each key fund
    for kf in key_funds_meta:
        code = kf["amfi_code"]
        sub = df_nav[df_nav['amfi_code'] == code].copy().set_index('date')
        rolling_sharpe = (sub['return'].rolling(90).mean() / sub['return'].rolling(90).std()) * np.sqrt(252)
        
        ax.plot(
            rolling_sharpe.index,
            rolling_sharpe.values,
            label=kf["label"],
            color=kf["color"],
            linewidth=2.0,
            linestyle=kf["linestyle"],
            alpha=0.9
        )
    
    # Zero line
    ax.axhline(0, color="#333333", linestyle="--", linewidth=1.2, alpha=0.7, label="Neutral Threshold (Sharpe = 0)")
    
    # Shaded risk/return zones
    ax.axhspan(2.0, 8.5, color="#2ecc71", alpha=0.08, label="Strong Risk-Adjusted Alpha (> 2.0)")
    ax.axhspan(-3.5, 0.0, color="#e74c3c", alpha=0.08, label="Negative Risk-Adjusted Zone (< 0.0)")
    
    # Formatting
    ax.set_title("90-Day Rolling Annualized Sharpe Ratio Comparison (2022 – 2026)", fontsize=16, fontweight='bold', pad=15)
    ax.set_xlabel("Date (Year-Quarter)", fontsize=12, fontweight='semibold', labelpad=10)
    ax.set_ylabel("Annualized 90-Day Sharpe Ratio (Daily Return Basis)", fontsize=12, fontweight='semibold', labelpad=10)
    
    # Date formatting
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    plt.xticks(rotation=45, ha='right', fontsize=10)
    plt.yticks(fontsize=10)
    
    ax.set_ylim(-3.5, 8.5)
    ax.grid(True, linestyle=":", alpha=0.6)
    
    # Legend
    ax.legend(loc="upper left", frameon=True, framealpha=0.95, facecolor="#ffffff", edgecolor="#cccccc", fontsize=10)
    
    # Annotations for notable regimes
    ax.annotate(
        "2022 Inflation & Rate Hike Consolidation\n(Negative / Sub-zero Sharpe)",
        xy=(pd.to_datetime("2022-06-15"), -1.8),
        xytext=(pd.to_datetime("2022-03-01"), -3.2),
        arrowprops=dict(facecolor="#c0392b", arrowstyle="->", lw=1.2),
        fontsize=9,
        fontweight='semibold',
        color="#c0392b",
        bbox=dict(boxstyle="round,pad=0.3", fc="#fdf2e9", ec="#e67e22", lw=0.8)
    )
    
    ax.annotate(
        "2023–2024 Broad Mid/Small-Cap Rally\n(Sharpe surged above 5.0 - 7.5)",
        xy=(pd.to_datetime("2023-11-15"), 6.2),
        xytext=(pd.to_datetime("2023-04-01"), 7.5),
        arrowprops=dict(facecolor="#27ae60", arrowstyle="->", lw=1.2),
        fontsize=9,
        fontweight='semibold',
        color="#27ae60",
        bbox=dict(boxstyle="round,pad=0.3", fc="#eafaf1", ec="#2ecc71", lw=0.8)
    )
    
    # Watermark / Subtitle info
    fig.text(0.99, 0.01, "Formula: [rolling_mean(90) / rolling_std(90)] × √252 | BlueStock MF Analytics",
             ha="right", fontsize=9, style="italic", color="#555555")
    
    plt.tight_layout()
    
    # Save destinations
    out_root = base_dir / "rolling_sharpe_chart.png"
    out_reports = base_dir / "reports" / "rolling_sharpe_chart.png"
    out_eda = base_dir / "reports" / "eda_charts" / "rolling_sharpe_chart.png"
    
    fig.savefig(out_root, dpi=300)
    fig.savefig(out_reports, dpi=300)
    if out_eda.parent.exists():
        fig.savefig(out_eda, dpi=300)
        
    plt.close(fig)
    print(f"Chart successfully saved to:")
    print(f"  - {out_root}")
    print(f"  - {out_reports}")

if __name__ == "__main__":
    generate_rolling_sharpe_chart()
