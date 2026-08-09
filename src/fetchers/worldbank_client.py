"""
Goi World Bank API (qua thu vien wbgapi), tra ve pandas Series.
Khong can API key.
"""

import pandas as pd
import wbgapi as wb


def fetch_series(code: str, country: str = "VNM") -> pd.Series:
    """
    Fetch 1 chi so tu World Bank cho 1 quoc gia (mac dinh VNM = Viet Nam).
    Du lieu World Bank theo nam -> date duoc chuan hoa ve "YYYY-01-01".
    Tra ve pandas Series voi index la DatetimeIndex.
    """
    rows = wb.data.fetch(code, economy=country)

    data = {}
    for row in rows:
        value = row.get("value")
        if value is None:
            continue
        year_digits = "".join(ch for ch in str(row["time"]) if ch.isdigit())
        if not year_digits:
            continue
        data[pd.Timestamp(year=int(year_digits), month=1, day=1)] = float(value)

    series = pd.Series(data).sort_index()
    series.name = code
    series.index.name = "date"
    return series
