"""Geocode a small, one-time list of verified business addresses.

This script follows the public Nominatim policy: one thread, at most one
request per second, an identifying User-Agent, and local result caching.
It is not intended for repeated or large-scale bulk geocoding.
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd
import requests

from config import RAW_DIR


NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = (
    "lisbon-coworking-capstone/0.1 "
    "(educational one-time address verification; contact: repository owner)"
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--collection-date",
        default=date.today().isoformat(),
        help="Discovery snapshot date in YYYY-MM-DD format.",
    )
    args = parser.parse_args()
    collection_date = date.fromisoformat(args.collection_date).isoformat()

    input_path = RAW_DIR / f"manual_discovery_{collection_date}.csv"
    output_path = RAW_DIR / f"nominatim_geocoding_{collection_date}.json"
    if output_path.exists():
        raise FileExistsError(f"Geocoding cache already exists: {output_path}")

    candidates = pd.read_csv(input_path)
    results: list[dict] = []
    for row_number, row in candidates.iterrows():
        response = requests.get(
            NOMINATIM_URL,
            params={
                "q": row["address"],
                "format": "jsonv2",
                "limit": 1,
                "countrycodes": "pt",
                "addressdetails": 1,
            },
            headers={"User-Agent": USER_AGENT},
            timeout=60,
        )
        response.raise_for_status()
        matches = response.json()
        results.append(
            {
                "row_number": int(row_number),
                "coworking_name": row["coworking_name"],
                "query_address": row["address"],
                "request_timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "result": matches[0] if matches else None,
            }
        )
        print(
            f"{row_number + 1:02d}/{len(candidates)} "
            f"{row['coworking_name']}: {'matched' if matches else 'no match'}"
        )
        if row_number < len(candidates) - 1:
            time.sleep(1.1)

    output_path.write_text(
        json.dumps(results, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Saved {len(results)} cached geocoding responses to {output_path}")


if __name__ == "__main__":
    main()
