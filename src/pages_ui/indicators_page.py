"""
Trang: Chi so kinh te (US & VN) - line chart + metric card so lieu moi nhat.
"""

from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st

from src.db import load_indicators, get_last_update_info
from src.indicators_config import INDICATORS, get_indicator_by_key

KEY_TO_NAME = {ind["key"]: ind["name"] for ind in INDICATORS}
NAME_TO_KEY = {ind["name"]: ind["key"] for ind in INDICATORS}

# Mau co dinh theo tung chi so (khong theo thu tu chon) - de doi lua chon o
# sidebar khong lam doi mau cua cac chi so con lai dang hien thi.
CATEGORICAL_PALETTE = [
    "#2a78d6",  # blue
    "#eb6834",  # orange
    "#1baf7a",  # aqua
    "#eda100",  # yellow
    "#e87ba4",  # magenta
    "#008300",  # green
    "#4a3aa7",  # violet
    "#e34948",  # red
]
NAME_TO_COLOR = {ind["name"]: CATEGORICAL_PALETTE[i % len(CATEGORICAL_PALETTE)] for i, ind in enumerate(INDICATORS)}

CHART_GRID_COLOR = "#e1e0d9"
CHART_AXIS_COLOR = "#898781"
DELTA_GOOD_COLOR = "#006300"


def render() -> None:
    # ------------------------------------------------------------ sidebar --
    st.sidebar.caption("Theo doi chi so kinh te vi mo: My & Viet Nam")

    grouped_options = []
    for country in ["US", "VN"]:
        grouped_options += [ind["name"] for ind in INDICATORS if ind["country"] == country]

    default_selection = grouped_options[:3] if len(grouped_options) >= 3 else grouped_options

    selected_names = st.sidebar.multiselect(
        "Chon chi so",
        options=grouped_options,
        default=default_selection,
    )
    selected_keys = [NAME_TO_KEY[name] for name in selected_names]

    today = date.today()
    default_start = date(today.year - 10, 1, 1)

    date_range = st.sidebar.date_input(
        "Khoang thoi gian",
        value=(default_start, today),
        max_value=today,
    )

    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date, end_date = default_start, today

    st.sidebar.divider()
    if st.sidebar.button("🔄 Refresh du lieu tu nguon", width="stretch"):
        st.sidebar.info("Chay lenh sau trong terminal roi bam Rerun:\n\npython src/update_data.py")

    # -------------------------------------------------------------- main --
    st.markdown("### 📊 Chi so kinh te")
    st.caption("Nguon du lieu: FRED (US) & World Bank (VN)")

    if not selected_keys:
        st.info("Chon it nhat 1 chi so o sidebar de xem du lieu.")
        return

    df = load_indicators(
        selected_keys,
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d"),
    )

    if df.empty:
        st.warning(
            "Chua co du lieu cho lua chon nay. Hay chay `python src/update_data.py` "
            "de fetch du lieu tu FRED / World Bank truoc."
        )
        return

    df["indicator_name"] = df["indicator_id"].map(KEY_TO_NAME)

    # ------------------------------------------------------- metric cards --
    cols = st.columns(min(len(selected_keys), 4) or 1)
    for i, key in enumerate(selected_keys):
        ind_cfg = get_indicator_by_key(key)
        sub = df[df["indicator_id"] == key].sort_values("date")
        if sub.empty:
            continue

        latest = sub.iloc[-1]
        prev_value = sub.iloc[-2]["value"] if len(sub) >= 2 else None

        pct_change = None
        if prev_value not in (None, 0) and not pd.isna(prev_value) and not pd.isna(latest["value"]):
            pct_change = (latest["value"] - prev_value) / prev_value * 100

        unit = ind_cfg.get("unit", "")
        value_display = f"{latest['value']:,.2f}" if not pd.isna(latest["value"]) else "N/A"

        with cols[i % len(cols)]:
            with st.container(border=True):
                st.metric(
                    label=f"{ind_cfg['name']} ({ind_cfg['country']})",
                    value=f"{value_display} {unit}".strip(),
                    delta=f"{pct_change:+.2f}% vs ky truoc" if pct_change is not None else None,
                )
                st.caption(f"Cap nhat: {latest['date'].strftime('%Y-%m-%d')}")

    st.write("")

    # ------------------------------------------------------------- chart --
    with st.container(border=True):
        st.markdown("**Bieu do theo thoi gian**")

        fig = px.line(
            df,
            x="date",
            y="value",
            color="indicator_name",
            facet_row="indicator_name",
            color_discrete_map=NAME_TO_COLOR,
            labels={"date": "Ngay", "value": "Gia tri", "indicator_name": "Chi so"},
            height=260 * len(selected_keys),
            template="plotly_white",
        )
        fig.update_traces(line_width=2, hovertemplate="%{x|%Y-%m-%d}: %{y:,.2f}<extra></extra>")
        fig.update_yaxes(matches=None, gridcolor=CHART_GRID_COLOR, zeroline=False)
        fig.update_xaxes(gridcolor=CHART_GRID_COLOR, linecolor=CHART_AXIS_COLOR)
        fig.for_each_yaxis(lambda axis: axis.update(title=""))
        fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1], font=dict(size=13)))
        fig.update_layout(
            showlegend=False,
            margin=dict(t=30, b=20, l=10, r=10),
            plot_bgcolor="#fcfcfb",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#0b0b0b"),
        )

        st.plotly_chart(fig, use_container_width=True)

    # --------------------------------------------------- detail table -----
    with st.expander("📋 Xem bang so lieu chi tiet"):
        rows = []
        for key in selected_keys:
            ind_cfg = get_indicator_by_key(key)
            sub = df[df["indicator_id"] == key].sort_values("date")
            if sub.empty:
                continue

            latest = sub.iloc[-1]
            prev_value = sub.iloc[-2]["value"] if len(sub) >= 2 else None

            pct_change = None
            if prev_value not in (None, 0) and not pd.isna(prev_value) and not pd.isna(latest["value"]):
                pct_change = (latest["value"] - prev_value) / prev_value * 100

            rows.append(
                {
                    "Chi so": ind_cfg["name"],
                    "Quoc gia": ind_cfg["country"],
                    "Ngay moi nhat": latest["date"].strftime("%Y-%m-%d"),
                    "Gia tri": round(latest["value"], 4) if not pd.isna(latest["value"]) else None,
                    "Don vi": ind_cfg.get("unit", ""),
                    "% thay doi vs ky truoc": round(pct_change, 2) if pct_change is not None else None,
                }
            )

        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    with st.expander("Trang thai du lieu trong DB"):
        st.dataframe(get_last_update_info(), use_container_width=True, hide_index=True)
