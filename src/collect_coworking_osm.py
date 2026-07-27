"""Collect immutable coworking candidates and Lisbon parish boundaries.

The script saves dated source snapshots in ``data/raw``. It does not clean,
deduplicate, or overwrite existing snapshots.
"""

from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timezone
from pathlib import Path

import requests

from config import PROJECT_ROOT, RAW_DIR


OVERPASS_URL = "https://overpass-api.de/api/interpreter"
PARISH_BOUNDARIES_URL = (
    "https://gisimage.cm-lisboa.pt/arcgis/rest/services/"
    "SMPC_GRELHA/MapServer/2/query"
)
USER_AGENT = (
    "lisbon-coworking-analysis/0.1 "
    "(educational data collection; contact: repository owner)"
)


def _write_json_once(path: Path, payload: object) -> None:
    """Write a JSON snapshot without silently replacing an existing file."""
    if path.exists():
        raise FileExistsError(
            f"Snapshot already exists: {path}. Use --collection-date for a new date."
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def collect_overpass(query_path: Path) -> dict:
    """Run the saved Overpass query and return its JSON response."""
    query = query_path.read_text(encoding="utf-8")
    response = requests.get(
        OVERPASS_URL,
        params={"data": query},
        headers={"User-Agent": USER_AGENT},
        timeout=120,
    )
    response.raise_for_status()
    payload = json.loads(response.content.decode("utf-8"))
    if "elements" not in payload:
        raise ValueError("Overpass response does not contain an elements array.")
    return payload


def collect_parish_boundaries() -> dict:
    """Download official Lisbon parish boundaries as GeoJSON."""
    response = requests.get(
        PARISH_BOUNDARIES_URL,
        params={
            "where": "1=1",
            "outFields": "*",
            "outSR": "4326",
            "f": "geojson",
        },
        headers={"User-Agent": USER_AGENT},
        timeout=120,
    )
    response.raise_for_status()
    # The ArcGIS endpoint currently omits a charset in its Content-Type header.
    # Decode explicitly so Portuguese names such as "Alcântara" are preserved.
    payload = json.loads(response.content.decode("utf-8"))
    if payload.get("type") != "FeatureCollection":
        raise ValueError("Municipal boundary response is not a GeoJSON FeatureCollection.")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--collection-date",
        default=date.today().isoformat(),
        help="Snapshot date in YYYY-MM-DD format.",
    )
    args = parser.parse_args()

    collection_date = date.fromisoformat(args.collection_date).isoformat()
    query_path = (
        PROJECT_ROOT / "src" / "queries" / "lisbon_coworking.overpassql"
    )
    osm_path = RAW_DIR / f"osm_coworking_{collection_date}.json"
    parish_path = RAW_DIR / f"lisbon_parishes_{collection_date}.geojson"
    log_path = RAW_DIR / f"collection_log_{collection_date}.json"

    osm_payload = collect_overpass(query_path)
    parish_payload = collect_parish_boundaries()
    _write_json_once(osm_path, osm_payload)
    _write_json_once(parish_path, parish_payload)

    collection_log = {
        "collection_date": collection_date,
        "collected_at_utc": datetime.now(timezone.utc).isoformat(),
        "overpass_endpoint": OVERPASS_URL,
        "overpass_query_file": str(query_path.relative_to(PROJECT_ROOT)),
        "overpass_element_count": len(osm_payload["elements"]),
        "parish_boundaries_endpoint": PARISH_BOUNDARIES_URL,
        "parish_feature_count": len(parish_payload["features"]),
        "raw_files": [
            str(osm_path.relative_to(PROJECT_ROOT)),
            str(parish_path.relative_to(PROJECT_ROOT)),
        ],
        "licence_notes": {
            "openstreetmap": "ODbL; attribution required.",
            "lisbon_parishes": "Câmara Municipal de Lisboa open-data service.",
        },
    }
    _write_json_once(log_path, collection_log)

    print(f"Saved {len(osm_payload['elements'])} OSM candidates to {osm_path}")
    print(f"Saved {len(parish_payload['features'])} parish features to {parish_path}")
    print(f"Saved collection metadata to {log_path}")


if __name__ == "__main__":
    main()
