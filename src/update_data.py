"""
Script fetch toan bo chi so trong indicators_config.py va luu vao SQLite.

Chay tay:
    python src/update_data.py

Co the dat lich chay dinh ky bang cron job / Task Scheduler / GitHub Actions.
"""

import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.db import init_db, upsert_series, upsert_news_events  # noqa: E402
from src.fetchers.fred_client import fetch_series as fetch_fred  # noqa: E402
from src.fetchers.worldbank_client import fetch_series as fetch_wb  # noqa: E402
from src.fetchers.forexfactory_client import fetch_calendar  # noqa: E402
from src.indicators_config import INDICATORS  # noqa: E402

# Nguon ForexFactory "thisweek" chi cover toi da ~het tuan hien tai (da test:
# khong co ban "nextweek"). Chay update_data.py hang ngay/hang tuan se tu
# dong lay lai dung tuan hien hanh moi lan.
NEWS_DAYS_AHEAD = 7


def update_indicator(indicator: dict) -> None:
    key = indicator["key"]
    source = indicator["source"]
    code = indicator["code"]

    print(f"[{key}] fetching from {source} ({code}) ...", end=" ")

    try:
        if source == "fred":
            series = fetch_fred(code)
        elif source == "worldbank":
            series = fetch_wb(code)
        else:
            print(f"SKIP - unknown source '{source}'")
            return

        n_rows = upsert_series(key, series)
        print(f"OK - {n_rows} data points saved")

    except Exception as exc:  # noqa: BLE001 - script muc dich log loi va tiep tuc chi so khac
        print(f"FAILED - {exc}")


def update_news() -> None:
    print(f"[NEWS] fetching economic calendar from forexfactory ({NEWS_DAYS_AHEAD}d ahead) ...", end=" ")

    try:
        df = fetch_calendar(days_ahead=NEWS_DAYS_AHEAD)
        fetched_at = datetime.now(timezone.utc).isoformat()
        n_rows = upsert_news_events(df, fetched_at)
        print(f"OK - {n_rows} events saved")

    except Exception as exc:  # noqa: BLE001 - script muc dich log loi va tiep tuc, khong crash
        print(f"FAILED - {exc}")


def main() -> None:
    init_db()
    print(f"Updating {len(INDICATORS)} indicators into database...\n")

    start = time.time()
    for indicator in INDICATORS:
        update_indicator(indicator)

    update_news()

    elapsed = time.time() - start
    print(f"\nDone in {elapsed:.1f}s")


if __name__ == "__main__":
    main()
