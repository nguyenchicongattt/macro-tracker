"""
Macro Tracker - Streamlit UI entrypoint (router giua cac trang)

Chay:
    streamlit run app.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st

from src.db import init_db
from src.pages_ui import indicators_page, news_page

st.set_page_config(page_title="Macro Tracker", page_icon="📈", layout="wide")
init_db()

PAGES = {
    "📊  Chi so kinh te": indicators_page.render,
    "📰  Tin tuc 3 sao": news_page.render,
}

with st.sidebar:
    st.markdown("## 📈 Macro Tracker")
    st.caption("US & Viet Nam macro dashboard")

    selected_page = st.segmented_control(
        "Menu",
        options=list(PAGES.keys()),
        default=list(PAGES.keys())[0],
        label_visibility="collapsed",
        width="stretch",
    )
    st.divider()

PAGES[selected_page or list(PAGES.keys())[0]]()
