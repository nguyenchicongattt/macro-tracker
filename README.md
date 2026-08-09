# Macro Tracker

Web app cá nhân theo dõi các chỉ số kinh tế vĩ mô của **Mỹ (trọng tâm)** và **Việt Nam** (dữ liệu từ **FRED** và **World Bank API**), kèm trang lọc **tin tức kinh tế 3 sao** (High impact, nguồn ForexFactory).

## Cấu trúc thư mục

```
macro/
├── data/
│   └── macro.db                  # SQLite DB (indicators + news_events), fetch boi update_data.py
├── src/
│   ├── fetchers/
│   │   ├── fred_client.py        # US indicators
│   │   ├── worldbank_client.py   # VN indicators
│   │   └── forexfactory_client.py# lich kinh te (economic calendar)
│   ├── pages_ui/
│   │   ├── indicators_page.py    # trang chi so (chart + metric cards)
│   │   └── news_page.py          # trang tin tuc 3 sao
│   ├── analysis/                 # de trong, danh cho tinh nang sau (YoY%, forecast, correlation)
│   ├── db.py
│   ├── indicators_config.py
│   └── update_data.py            # fetch dinh ky: indicators + news, luu SQLite
├── .github/workflows/update-data.yml  # GitHub Actions - fetch tu dong hang ngay
├── .streamlit/config.toml        # theme
├── app.py                        # entrypoint (router giua 2 trang)
├── .env / .env.example
├── requirements.txt
└── README.md
```

## 1. Cài đặt (chạy local)

```bash
pip install -r requirements.txt
```

## 2. Lấy FRED API key

1. Đăng ký key miễn phí tại: https://fred.stlouisfed.org/docs/api/api_key.html
2. Copy `.env.example` thành `.env` và điền key vào:

```
FRED_API_KEY=your_fred_api_key_here
```

World Bank và ForexFactory không cần key.

## 3. Fetch dữ liệu vào SQLite

```bash
python src/update_data.py
```

Fetch toàn bộ chỉ số trong `src/indicators_config.py` (US: CPI, Fed Funds Rate, Unemployment, GDP; VN: GDP Growth, Inflation, FDI) **và** lịch kinh tế 7 ngày tới từ ForexFactory, lưu vào `data/macro.db`.

Tin tức kinh tế đã lên lịch trước nên **không fetch mỗi lần mở trang** — chỉ cần chạy lại lệnh trên định kỳ (tay, cron, Task Scheduler, hoặc GitHub Actions — xem phần Deploy).

## 4. Chạy app

```bash
streamlit run app.py
```

Mở http://localhost:8501. Sidebar có menu chuyển 2 trang:
- **📊 Chỉ số kinh tế**: chọn chỉ số + khoảng thời gian, xem line chart + metric card giá trị mới nhất.
- **📰 Tin tức 3 sao**: lọc sự kiện High impact trong 1/3/7 ngày tới, lọc thêm theo quốc gia.

## 5. Deploy lên Streamlit Community Cloud (miễn phí, chạy 24/7 dạng "ngủ khi rảnh")

1. Push code lên GitHub (repo public để dùng free tier không giới hạn).
2. Vào https://share.streamlit.io → **New app** → chọn repo, branch `main`, main file `app.py` → **Deploy**.
3. App không cần secret nào (không gọi FRED/API trực tiếp lúc runtime, chỉ đọc SQLite).
4. Vì ổ đĩa Streamlit Cloud là **ephemeral** (mất khi container restart), `.github/workflows/update-data.yml` sẽ tự chạy hàng ngày (00:00 UTC), fetch dữ liệu mới và **commit lại `data/macro.db`** vào repo → Streamlit Cloud tự động redeploy với data mới.
5. Cần thêm 1 secret cho GitHub Actions (không phải cho Streamlit Cloud): vào repo → **Settings → Secrets and variables → Actions → New repository secret** → tên `FRED_API_KEY`, giá trị là key thật của bạn.

Muốn chạy tay ngay không đợi lịch: vào tab **Actions** trên GitHub → chọn workflow "Update macro data" → **Run workflow**.

## Thêm chỉ số / nguồn dữ liệu mới

- Thêm chỉ số mới → sửa `src/indicators_config.py`
- Thêm nguồn dữ liệu mới → thêm file trong `src/fetchers/`
- Thêm tính toán (YoY%, MoM%, z-score, moving average) → đặt trong `src/analysis/`
- Thêm trang UI mới → thêm file trong `src/pages_ui/`, đăng ký trong `PAGES` ở `app.py`

## Lưu ý kỹ thuật

- Dữ liệu World Bank (VN) theo **năm**, dữ liệu FRED (US) theo **tháng/quý** — khi so sánh VN vs US cần resample hoặc chỉ so sánh theo năm.
- ForexFactory chỉ có feed "thisweek" (không có "nextweek"/"lastweek" — đã test, trả 404), tự cover từ hôm nay đến hết tuần hiện tại (~5-7 ngày).
- `.env` không commit lên git (đã có trong `.gitignore`). `data/macro.db` **có** commit (cần thiết để Streamlit Cloud có sẵn dữ liệu).
