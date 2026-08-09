"""
Khai bao danh sach cac chi so kinh te vi mo can theo doi.

Moi indicator la 1 dict:
    key      : dinh danh noi bo, dung lam indicator_id trong DB
    source   : "fred" hoac "worldbank"
    code     : ma chi so tai nguon du lieu
    name     : ten hien thi tren UI
    unit     : don vi (hien thi tren chart/bang, khong bat buoc)
    country  : "US" hoac "VN" (de nhom/hien thi)
"""

INDICATORS = [
    {
        "key": "US_CPI",
        "source": "fred",
        "code": "CPIAUCSL",
        "name": "US CPI",
        "unit": "Index",
        "country": "US",
    },
    {
        "key": "US_FED_RATE",
        "source": "fred",
        "code": "FEDFUNDS",
        "name": "Fed Funds Rate",
        "unit": "%",
        "country": "US",
    },
    {
        "key": "US_UNEMP",
        "source": "fred",
        "code": "UNRATE",
        "name": "US Unemployment",
        "unit": "%",
        "country": "US",
    },
    {
        "key": "US_GDP",
        "source": "fred",
        "code": "GDP",
        "name": "US GDP",
        "unit": "Billion USD",
        "country": "US",
    },
    {
        "key": "VN_GDP",
        "source": "worldbank",
        "code": "NY.GDP.MKTP.KD.ZG",
        "name": "VN GDP Growth",
        "unit": "%",
        "country": "VN",
    },
    {
        "key": "VN_CPI",
        "source": "worldbank",
        "code": "FP.CPI.TOTL.ZG",
        "name": "VN Inflation",
        "unit": "%",
        "country": "VN",
    },
    {
        "key": "VN_FDI",
        "source": "worldbank",
        "code": "BX.KLT.DINV.WD.GD.ZS",
        "name": "VN FDI (%GDP)",
        "unit": "% GDP",
        "country": "VN",
    },
]


def get_indicator_by_key(key: str) -> dict | None:
    """Tra ve config cua 1 indicator theo key, None neu khong tim thay."""
    for ind in INDICATORS:
        if ind["key"] == key:
            return ind
    return None
