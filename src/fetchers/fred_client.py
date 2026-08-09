"""
Goi FRED API (qua thu vien fredapi), tra ve pandas Series.
Can bien moi truong FRED_API_KEY (xem README.md).
"""

import os

import pandas as pd
from dotenv import load_dotenv
from fredapi import Fred

load_dotenv()

_fred_instance: Fred | None = None


def _get_client() -> Fred:
    global _fred_instance
    if _fred_instance is None:
        api_key = os.getenv("FRED_API_KEY")
        if not api_key:
            raise RuntimeError(
                "Thieu FRED_API_KEY. Tao file .env tu .env.example va dien API key "
                "(lay tai https://fred.stlouisfed.org/docs/api/api_key.html)."
            )
        _fred_instance = Fred(api_key=api_key)
    return _fred_instance


def fetch_series(code: str) -> pd.Series:
    """
    Fetch 1 chi so tu FRED theo ma series (vd: CPIAUCSL, FEDFUNDS, UNRATE, GDP).
    Tra ve pandas Series voi index la DatetimeIndex.
    """
    client = _get_client()
    series = client.get_series(code)
    series.name = code
    series.index.name = "date"
    return series.dropna()
