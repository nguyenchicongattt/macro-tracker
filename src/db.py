"""
Ghi/doc SQLite cho Macro Tracker.

Schema (long-format):
    data_points(indicator_id TEXT, date TEXT, value REAL)
    UNIQUE(indicator_id, date) -> cho phep upsert khi fetch lai du lieu.

    news_events(title, country, date, impact, stars, forecast, previous, fetched_at)
    UNIQUE(title, country, date) -> lich kinh te (ForexFactory), fetch dinh ky
    boi update_data.py - tin tuc da len lich truoc nen KHONG can goi API moi
    lan xem trang, chi doc lai tu bang nay.

date luu dang chuoi ISO "YYYY-MM-DD" de de sort/filter va tuong thich
ca du lieu thang (FRED) lan du lieu nam (World Bank, luu la "YYYY-01-01").
"""

import sqlite3
from pathlib import Path

import pandas as pd

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "macro.db"


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_db() -> None:
    """Tao cac bang neu chua ton tai."""
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS data_points (
                indicator_id TEXT NOT NULL,
                date         TEXT NOT NULL,
                value        REAL,
                PRIMARY KEY (indicator_id, date)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS news_events (
                title      TEXT NOT NULL,
                country    TEXT NOT NULL,
                date       TEXT NOT NULL,
                impact     TEXT,
                stars      INTEGER,
                forecast   TEXT,
                previous   TEXT,
                fetched_at TEXT,
                PRIMARY KEY (title, country, date)
            )
            """
        )
        conn.commit()


def upsert_news_events(df: pd.DataFrame, fetched_at: str) -> int:
    """
    Luu DataFrame su kien lich kinh te (tu forexfactory_client.fetch_calendar)
    vao DB. Ghi de neu (title, country, date) da ton tai. Tra ve so dong da ghi.
    """
    if df is None or df.empty:
        return 0

    rows = [
        (
            row.title,
            row.country,
            pd.Timestamp(row.date).isoformat(),
            row.impact,
            int(row.stars),
            row.forecast,
            row.previous,
            fetched_at,
        )
        for row in df.itertuples(index=False)
    ]

    with get_connection() as conn:
        conn.executemany(
            """
            INSERT INTO news_events (title, country, date, impact, stars, forecast, previous, fetched_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(title, country, date) DO UPDATE SET
                impact     = excluded.impact,
                stars      = excluded.stars,
                forecast   = excluded.forecast,
                previous   = excluded.previous,
                fetched_at = excluded.fetched_at
            """,
            rows,
        )
        conn.commit()

    return len(rows)


def load_news_events(start_date: str | None = None, end_date: str | None = None) -> pd.DataFrame:
    """Doc lai lich kinh te da luu, tra ve DataFrame sort theo date tang dan."""
    query = "SELECT title, country, date, impact, stars, forecast, previous, fetched_at FROM news_events WHERE 1=1"
    params: list = []

    if start_date:
        query += " AND date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND date <= ?"
        params.append(end_date)

    query += " ORDER BY date ASC"

    with get_connection() as conn:
        df = pd.read_sql_query(query, conn, params=params)

    if not df.empty:
        df["date"] = pd.to_datetime(df["date"], utc=True)
        df["fetched_at"] = pd.to_datetime(df["fetched_at"], utc=True)

    return df


def upsert_series(indicator_id: str, series: pd.Series) -> int:
    """
    Luu 1 pandas Series (index = date, value = so lieu) vao DB cho 1 indicator.
    Ghi de neu (indicator_id, date) da ton tai. Tra ve so dong da ghi.
    """
    if series is None or series.empty:
        return 0

    rows = [
        (indicator_id, pd.Timestamp(idx).strftime("%Y-%m-%d"), None if pd.isna(val) else float(val))
        for idx, val in series.items()
    ]

    with get_connection() as conn:
        conn.executemany(
            """
            INSERT INTO data_points (indicator_id, date, value)
            VALUES (?, ?, ?)
            ON CONFLICT(indicator_id, date) DO UPDATE SET value = excluded.value
            """,
            rows,
        )
        conn.commit()

    return len(rows)


def load_indicator(indicator_id: str, start_date: str | None = None, end_date: str | None = None) -> pd.DataFrame:
    """Doc du lieu cua 1 indicator, tra ve DataFrame [date, value] sort theo date tang dan."""
    query = "SELECT date, value FROM data_points WHERE indicator_id = ?"
    params: list = [indicator_id]

    if start_date:
        query += " AND date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND date <= ?"
        params.append(end_date)

    query += " ORDER BY date ASC"

    with get_connection() as conn:
        df = pd.read_sql_query(query, conn, params=params, parse_dates=["date"])

    return df


def load_indicators(indicator_ids: list[str], start_date: str | None = None, end_date: str | None = None) -> pd.DataFrame:
    """
    Doc du lieu cho nhieu indicator cung luc.
    Tra ve DataFrame dang long: [indicator_id, date, value].
    """
    if not indicator_ids:
        return pd.DataFrame(columns=["indicator_id", "date", "value"])

    placeholders = ",".join("?" for _ in indicator_ids)
    query = f"SELECT indicator_id, date, value FROM data_points WHERE indicator_id IN ({placeholders})"
    params: list = list(indicator_ids)

    if start_date:
        query += " AND date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND date <= ?"
        params.append(end_date)

    query += " ORDER BY indicator_id ASC, date ASC"

    with get_connection() as conn:
        df = pd.read_sql_query(query, conn, params=params, parse_dates=["date"])

    return df


def get_last_update_info() -> pd.DataFrame:
    """Tra ve DataFrame [indicator_id, last_date, n_points] - dung de kiem tra tinh trang du lieu."""
    query = """
        SELECT indicator_id, MAX(date) AS last_date, COUNT(*) AS n_points
        FROM data_points
        GROUP BY indicator_id
    """
    with get_connection() as conn:
        return pd.read_sql_query(query, conn)
