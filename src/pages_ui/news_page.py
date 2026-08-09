"""
Trang: Tin tuc 3 sao - doc lich kinh te da luu san trong SQLite.

Tin tuc kinh te da len lich truoc (khong phat sinh bat ngo trong ngay) nen
trang nay KHONG goi API moi lan xem - du lieu duoc fetch dinh ky boi
`python src/update_data.py` (xem src/fetchers/forexfactory_client.py) va
luu vao bang news_events, trang chi doc lai tu DB.
"""

from datetime import date, timedelta

import pandas as pd
import streamlit as st

from src.db import load_news_events

VN_TZ = "Asia/Ho_Chi_Minh"


def render() -> None:
    st.sidebar.caption("Lich kinh te muc do anh huong cao - nguon ForexFactory")

    days_ahead = st.sidebar.selectbox(
        "Xem trong",
        options=[1, 3, 7],
        index=1,
        format_func=lambda d: f"{d} ngay toi",
    )

    st.markdown("### 📰 Tin tuc 3 sao")
    st.caption("Cac su kien kinh te muc do anh huong cao (High impact)")

    today = date.today()
    end_date = today + timedelta(days=days_ahead)

    df = load_news_events(start_date=today.isoformat(), end_date=end_date.isoformat())

    if df.empty:
        st.warning(
            "Chua co du lieu tin tuc trong DB. Hay chay `python src/update_data.py` "
            "de fetch lich kinh te tu ForexFactory truoc."
        )
        return

    last_fetched = df["fetched_at"].max()
    if pd.notna(last_fetched):
        fetched_local = last_fetched.tz_convert(VN_TZ).strftime("%H:%M %d/%m/%Y")
        st.caption(f"📅 Du lieu cap nhat luc {fetched_local} (gio VN) - chay lai `update_data.py` de lay tin moi.")

    df_3star = df[df["stars"] == 3].copy()

    if df_3star.empty:
        st.info(f"Khong co tin 3 sao nao trong {days_ahead} ngay toi.")
        return

    df_3star["Thoi gian"] = df_3star["date"].dt.tz_convert(VN_TZ).dt.strftime("%d/%m %H:%M")
    df_3star["Muc do"] = "🔴 High"

    # ---------------------------------------------------------- filter ----
    all_countries = sorted(df_3star["country"].unique())
    selected_countries = st.multiselect(
        "Loc theo quoc gia",
        options=all_countries,
        default=all_countries,
    )
    df_3star = df_3star[df_3star["country"].isin(selected_countries)]

    if df_3star.empty:
        st.info("Khong co tin nao khop voi quoc gia da chon.")
        return

    # -------------------------------------------------------------- KPI ---
    kpi_cols = st.columns(3)
    with kpi_cols[0]:
        with st.container(border=True):
            st.metric("Tong tin 3 sao", len(df_3star))
    with kpi_cols[1]:
        with st.container(border=True):
            st.metric("So quoc gia lien quan", df_3star["country"].nunique())
    with kpi_cols[2]:
        with st.container(border=True):
            next_event = df_3star.iloc[0]
            st.metric("Su kien gan nhat", next_event["Thoi gian"])
            st.caption(f"{next_event['country']} - {next_event['title']}")

    st.write("")

    # ------------------------------------------------------------- table --
    with st.container(border=True):
        display_df = df_3star.rename(
            columns={
                "title": "Su kien",
                "country": "Quoc gia",
                "forecast": "Du bao",
                "previous": "Ky truoc",
            }
        )[["Thoi gian", "Quoc gia", "Muc do", "Su kien", "Du bao", "Ky truoc"]]

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Thoi gian": st.column_config.TextColumn(width="small"),
                "Quoc gia": st.column_config.TextColumn(width="small"),
                "Muc do": st.column_config.TextColumn(width="small"),
                "Su kien": st.column_config.TextColumn(width="large"),
            },
        )
