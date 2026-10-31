#!/usr/bin/env python3
"""
Bluestock Mutual Fund Analytics — Interactive Streamlit Web Application
========================================================================
Interactive multi-page web dashboard providing executive-level exploration
of Indian mutual fund industry AUM, scheme performance scorecards, retail
investor demographics, and an algorithmic risk-calibrated fund recommender.

Usage:
    streamlit run streamlit_app.py
    # or
    streamlit run dashboard/streamlit_app.py
"""

from pathlib import Path
import subprocess
import sys

BASE_DIR = Path(__file__).resolve().parent
TARGET_APP = BASE_DIR / "dashboard" / "streamlit_app.py"

if __name__ == "__main__":
    if not TARGET_APP.exists():
        TARGET_APP = BASE_DIR / "bonus_challenges" / "B2_streamlit_web_app" / "streamlit_app.py"
    
    cmd = [sys.executable, "-m", "streamlit", "run", str(TARGET_APP)] + sys.argv[1:]
    subprocess.run(cmd)
