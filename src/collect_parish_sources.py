"""Collect immutable raw OSM inputs for the parish-indicator table."""

from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timezone
from pathlib import Path

import requests

from config import PROJECT_ROOT, RAW_DIR


OVERPASS_URL = "https://overpass-api.de/api/interpreter"
USER_AGENT = (
    "lisbon-coworking-analysis/0.1 "
    "(educational parish indicators; contact: repository owner)"
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--collection-date",
        default=date.today().isoformat(),
        help="Snapshot date in YYYY-MM-DD format.",
    )
    args = parser.parse_args()
    collection_date = date.fromisoformat(args.collection_date).isoformat()

    query_path = PROJECT_ROOT / "src" / "queries" / "lisbon_parish_pois.overpassql"
    output_path = RAW_DIR / f"osm_parish_pois_{collection_date}.json"
    log_path = RAW_DIR / f"parish_collection_log_{collection_date}.json"
    if output_path.exists() or log_path.exists():
        raise FileExistsError("Dated parish source snapshot already exists.")

    response = requests.get(
        OVERPASS_URL,
        params={"data": query_path.read_text(encoding="utf-8")},
        headers={"User-Agent": USER_AGENT},
        timeout=240,
    )
    response.raise_for_status()
    payload = json.loads(response.content.decode("utf-8"))
    if "elements" not in payload:
        raise ValueError("Overpass response has no elements array.")

    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    log = {
        "collection_date": collection_date,
        "collected_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": OVERPASS_URL,
        "query_file": str(query_path.relative_to(PROJECT_ROOT)),
        "element_count": len(payload["elements"]),
        "licence": "OpenStreetMap contributors, ODbL.",
        "scope_note": (
            "Bounding-box discovery followed by point-in-polygon filtering "
            "against official Lisbon parish boundaries."
        ),
    }
    log_path.write_text(
        json.dumps(log, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Saved {len(payload['elements'])} OSM POI/transit elements.")
    print(output_path)


if __name__ == "__main__":
    main()
