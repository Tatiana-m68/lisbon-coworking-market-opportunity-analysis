"""Collect official municipal datasets used to validate OSM coverage."""

from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timezone

import requests

from config import RAW_DIR


SOURCES = {
    "municipal_higher_education": (
        "https://services.arcgis.com/1dSrzEWVQn5kHHyK/arcgis/rest/services/"
        "POIEducacao/FeatureServer/0/query"
    ),
    "municipal_hotels_2015": (
        "https://services.arcgis.com/1dSrzEWVQn5kHHyK/arcgis/rest/services/"
        "Alojamento/FeatureServer/0/query"
    ),
    "municipal_metro_stations": (
        "https://services.arcgis.com/1dSrzEWVQn5kHHyK/arcgis/rest/services/"
        "POITransportes/FeatureServer/1/query"
    ),
}
USER_AGENT = (
    "lisbon-coworking-capstone/0.1 "
    "(educational coverage validation; contact: repository owner)"
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--collection-date",
        default=date.today().isoformat(),
    )
    args = parser.parse_args()
    collection_date = date.fromisoformat(args.collection_date).isoformat()

    log: dict[str, object] = {
        "collection_date": collection_date,
        "collected_at_utc": datetime.now(timezone.utc).isoformat(),
        "sources": {},
    }
    for source_name, url in SOURCES.items():
        output_path = RAW_DIR / f"{source_name}_{collection_date}.geojson"
        if output_path.exists():
            raise FileExistsError(f"Snapshot already exists: {output_path}")
        response = requests.get(
            url,
            params={"f": "geojson", "outFields": "*", "where": "1=1"},
            headers={"User-Agent": USER_AGENT},
            timeout=120,
        )
        response.raise_for_status()
        payload = json.loads(response.content.decode("utf-8"))
        if payload.get("type") != "FeatureCollection":
            raise ValueError(f"{source_name} is not a GeoJSON FeatureCollection.")
        output_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        log["sources"][source_name] = {
            "url": url,
            "feature_count": len(payload["features"]),
            "raw_file": output_path.name,
        }
        print(f"{source_name}: {len(payload['features'])} features")

    log_path = RAW_DIR / f"municipal_validation_log_{collection_date}.json"
    log_path.write_text(
        json.dumps(log, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(log_path)


if __name__ == "__main__":
    main()
