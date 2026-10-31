#!/usr/bin/env python3
"""
Bluestock Mutual Fund Analytics — Simple Fund Recommender
=========================================================
Recommends top funds by Sharpe ratio within a selected risk appetite tier (Low / Moderate / High).

Usage:
    python recommender.py --risk Low
    python recommender.py --risk Moderate
    python recommender.py --risk High
    python recommender.py (prompts interactively or displays all 3 risk tiers)

Deliverable for BlueStock MF Analytics Capstone.
"""

import sys
import argparse
from pathlib import Path
import pandas as pd


def load_performance_data(data_path: str = None) -> pd.DataFrame:
    """Load scheme performance data from processed CSV."""
    if data_path is not None:
        path = Path(data_path)
    else:
        # Default locations relative to repository
        script_dir = Path(__file__).resolve().parent
        candidates = [
            script_dir / "data" / "processed" / "clean_scheme_performance.csv",
            script_dir.parent / "data" / "processed" / "clean_scheme_performance.csv",
            Path("data/processed/clean_scheme_performance.csv")
        ]
        path = None
        for cand in candidates:
            if cand.exists():
                path = cand
                break
        if path is None:
            raise FileNotFoundError("Could not locate clean_scheme_performance.csv")

    df = pd.read_csv(path)
    return df


def recommend_funds(risk_appetite: str = "Moderate", top_n: int = 3, data_path: str = None) -> pd.DataFrame:
    """
    Filter funds matching the specified risk appetite and rank them by Sharpe ratio.

    Parameters:
    -----------
    risk_appetite : str
        Target risk appetite ('Low', 'Moderate', 'High', or variations).
    top_n : int
        Number of top funds to recommend (default 3).
    data_path : str, optional
        Custom path to clean_scheme_performance.csv.

    Returns:
    --------
    pd.DataFrame : Top N funds matching risk criteria sorted by Sharpe ratio descending.
    """
    df = load_performance_data(data_path)

    # Standardize risk input
    risk_clean = str(risk_appetite).strip().lower()

    # Mapping logic for user-friendly risk tiers
    risk_mapping = {
        "low": ["Low"],
        "moderate": ["Moderate"],
        "high": ["High"],
        "very high": ["Very High"],
        "moderately high": ["Moderately High"],
        # Aggregated convenience buckets
        "conservative": ["Low"],
        "balanced": ["Moderate"],
        "aggressive": ["High", "Very High"]
    }

    matching_grades = risk_mapping.get(risk_clean, [risk_appetite.strip().title()])

    # Filter by risk grade
    filtered = df[df["risk_grade"].isin(matching_grades)].copy()

    if filtered.empty:
        # Fallback to case-insensitive partial match
        filtered = df[df["risk_grade"].str.lower() == risk_clean].copy()

    if filtered.empty:
        available = df["risk_grade"].unique().tolist()
        raise ValueError(f"No funds found for risk appetite '{risk_appetite}'. Available risk grades: {available}")

    # Sort by Sharpe Ratio descending, breaking ties with 3Y return and 1Y return
    sorted_df = filtered.sort_values(
        by=["sharpe_ratio", "return_3yr_pct", "return_1yr_pct"],
        ascending=[False, False, False]
    ).reset_index(drop=True)

    top_funds = sorted_df.head(top_n).copy()
    top_funds["rank"] = range(1, len(top_funds) + 1)

    return top_funds


def format_recommendation_table(recommendations: pd.DataFrame, risk_appetite: str) -> str:
    """Format recommendation results into an ASCII table."""
    columns_to_show = [
        ("Rank", "rank", 4),
        ("AMFI", "amfi_code", 7),
        ("Scheme Name", "scheme_name", 46),
        ("Category", "category", 12),
        ("Risk Grade", "risk_grade", 11),
        ("Sharpe", "sharpe_ratio", 8),
        ("3Y Ret (%)", "return_3yr_pct", 10),
        ("1Y Ret (%)", "return_1yr_pct", 10),
        ("AUM (Cr)", "aum_crore", 10),
        ("Fund House", "fund_house", 22),
    ]

    header_parts = []
    separator_parts = []
    for title, col, width in columns_to_show:
        header_parts.append(f"{title:<{width}}")
        separator_parts.append("-" * width)

    header_line = " | ".join(header_parts)
    sep_line = "-+-".join(separator_parts)

    rows = []
    for _, row in recommendations.iterrows():
        row_parts = []
        for title, col, width in columns_to_show:
            val = row.get(col, "")
            if isinstance(val, float):
                val_str = f"{val:.2f}"
            else:
                val_str = str(val)
            if len(val_str) > width:
                val_str = val_str[:width - 3] + "..."
            row_parts.append(f"{val_str:<{width}}")
        rows.append(" | ".join(row_parts))

    title_box = f"========================================================================================\n" \
                f" TOP {len(recommendations)} MUTUAL FUND RECOMMENDATIONS -- RISK APPETITE: {risk_appetite.upper()}\n" \
                f"========================================================================================"

    return f"\n{title_box}\n{header_line}\n{sep_line}\n" + "\n".join(rows) + f"\n{sep_line}\n"


def print_recommendation_table(recommendations: pd.DataFrame, risk_appetite: str):
    """Print the formatted recommendation table."""
    table = format_recommendation_table(recommendations, risk_appetite)
    print(table)


def main():
    parser = argparse.ArgumentParser(description="BlueStock Simple Mutual Fund Recommender")
    parser.add_argument(
        "--risk",
        "-r",
        type=str,
        default=None,
        choices=["Low", "Moderate", "High", "low", "moderate", "high"],
        help="Investor risk appetite: Low, Moderate, or High."
    )
    parser.add_argument(
        "--top",
        "-t",
        type=int,
        default=3,
        help="Number of funds to recommend (default: 3)."
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Display recommendations across all three risk categories."
    )

    args = parser.parse_args()

    # If --all or run non-interactively without --risk, display for Low, Moderate, and High
    if args.all or (args.risk is None and not sys.stdin.isatty()):
        print("\n" + "#" * 88)
        print(" BLUESTOCK MUTUAL FUND RECOMMENDER — ALL RISK TIERS")
        print("#" * 88)
        for risk in ["Low", "Moderate", "High"]:
            recs = recommend_funds(risk_appetite=risk, top_n=args.top)
            print_recommendation_table(recs, risk)
        return

    # If risk not provided on CLI, ask interactively
    risk_input = args.risk
    if risk_input is None:
        try:
            print("\nSelect Risk Appetite:")
            print("  1. Low       (Conservative — Capital preservation, liquid/debt focus)")
            print("  2. Moderate  (Balanced — Long-term growth with steady large-cap core)")
            print("  3. High      (Aggressive — Maximum capital appreciation via mid/small-caps)")
            choice = input("\nEnter choice [1-3 or Low/Moderate/High] (default: Moderate): ").strip()
            choice_map = {"1": "Low", "2": "Moderate", "3": "High"}
            risk_input = choice_map.get(choice, choice if choice else "Moderate")
        except (EOFError, KeyboardInterrupt):
            risk_input = "Moderate"

    recs = recommend_funds(risk_appetite=risk_input, top_n=args.top)
    print_recommendation_table(recs, risk_input)


if __name__ == "__main__":
    main()
