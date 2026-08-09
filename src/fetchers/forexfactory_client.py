"""
Lay lich tin tuc kinh te (economic calendar) tu ForexFactory - feed khong chinh
thuc, mien phi, khong can API key.

Tin tuc kinh te da len lich truoc (khong phat sinh bat ngo trong ngay), nen
KHONG fetch moi lan xem trang - chi fetch dinh ky boi update_data.py va luu
vao SQLite (xem src/db.py: upsert_news_events/load_news_events). Ham o day
chi co nhiem vu goi API 1 lan khi update_data.py chay, giong contract cua
fred_client.fetch_series / worldbank_client.fetch_series (raise loi cho
script goi xu ly, khong tu fallback).

Nguon: https://nfs.faireconomy.media/ff_calendar_thisweek.json
Feed nay CHI co ban "thisweek" (da test truc tiep: "nextweek"/"lastweek" tra
ve 404, khong ton tai) va tu dong cover tu hom nay den het tuan hien tai
(thuong ~5-7 ngay tuy ngay fetch). Vi tin tuc da len lich truoc, fetch lai
moi ngay/moi tuan bang update_data.py la du - "thisweek" luon phan anh dung
tuan hien hanh tai thoi diem goi.
"""

import time

import requests
import pandas as pd

BASE_URL = "https://nfs.faireconomy.media/ff_calendar_{period}.json"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}
MAX_RETRIES = 2
RETRY_BACKOFF_SECONDS = 2
RETRYABLE_STATUS = {429, 500, 502, 503, 504}

# ForexFactory dung icon "bars" (do/vang/xam) the hien muc do anh huong,
# cong dong trader hay goi la "sao": High = 3 sao, Medium = 2 sao, Low = 1 sao.
IMPACT_TO_STARS = {"High": 3, "Medium": 2, "Low": 1, "Holiday": 0}


def _fetch_period(period: str) -> list:
    """Goi API 1 lan, retry co backoff neu gap loi tam thoi (429/5xx)."""
    url = BASE_URL.format(period=period)
    last_exc: Exception | None = None

    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else None
            if status not in RETRYABLE_STATUS or attempt == MAX_RETRIES:
                raise
            last_exc = exc
        except requests.exceptions.RequestException as exc:
            if attempt == MAX_RETRIES:
                raise
            last_exc = exc

        time.sleep(RETRY_BACKOFF_SECONDS * (attempt + 1))

    raise last_exc  # khong bao gio toi day, de thoa man type-checker


def fetch_calendar(days_ahead: int = 7) -> pd.DataFrame:
    """
    Fetch lich kinh te tu hom nay den `days_ahead` ngay toi (toi da ~ het tuan
    hien tai - gioi han cua nguon "thisweek", xem docstring dau file).
    Tra ve DataFrame cot: date (tz UTC), title, country, impact, stars, forecast, previous.
    """
    raw = list(_fetch_period("thisweek"))

    columns = ["date", "title", "country", "impact", "stars", "forecast", "previous"]
    if not raw:
        return pd.DataFrame(columns=columns)

    df = pd.DataFrame(raw)
    df["date"] = pd.to_datetime(df["date"], utc=True, errors="coerce")
    df = df.dropna(subset=["date"])
    df["stars"] = df["impact"].map(IMPACT_TO_STARS).fillna(0).astype(int)

    today = pd.Timestamp.now(tz="UTC").normalize()
    end = today + pd.Timedelta(days=days_ahead)
    df = df[(df["date"] >= today) & (df["date"] <= end)]

    df = df.sort_values("date").drop_duplicates(subset=["title", "country", "date"]).reset_index(drop=True)

    return df[columns]
