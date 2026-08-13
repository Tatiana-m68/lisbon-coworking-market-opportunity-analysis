"""Append verified locations from a dated competitor audit without duplicates."""

from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd

from build_coworking_locations import (
    assign_parishes,
    flag_duplicate_candidates,
    haversine_metres,
    normalize_text,
    related_names,
)
from config import PROCESSED_DIR, PROJECT_ROOT, RAW_DIR


def is_existing_location(candidate: pd.Series, locations: pd.DataFrame) -> bool:
    """Conservatively match the same operator/location already in the table."""
    candidate_name = normalize_text(candidate["coworking_name"])
    for _, existing in locations.iterrows():
        if normalize_text(existing.get("coworking_name")) == candidate_name:
            return True
        if pd.isna(existing.get("latitude")):
            continue
        distance = haversine_metres(
            float(candidate["latitude"]),
            float(candidate["longitude"]),
            float(existing["latitude"]),
            float(existing["longitude"]),
        )
        if distance <= 150 and related_names(candidate, existing):
            return True
    return False


def build_rows(audit: pd.DataFrame, audit_date: str) -> pd.DataFrame:
    rows: list[dict] = []
    for index, item in audit.iterrows():
        website = item["source_url"]
        rows.append(
            {
                "coworking_id": f"audit_{audit_date.replace('-', '')}_{index + 1:03d}",
                "coworking_name": item["coworking_name"],
                "operator": item["operator"],
                "address": item["address"],
                "latitude": float(item["latitude"]),
                "longitude": float(item["longitude"]),
                "parish": None,
                "active_status": "active",
                "source_type": "official operator website + current map audit",
                "source_url": website,
                "secondary_source_url": item["secondary_source_url"],
                "website": website,
                "website_domain": urlparse(website).netloc.lower().removeprefix("www."),
                "collection_date": item["collection_date"],
                "verification_status": "verified_official_site",
                "matched_rule": item["matched_rule"],
                "osm_type": None,
                "osm_id": None,
                "duplicate_group": None,
                "review_note": item["review_note"],
                "raw_tags": None,
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit-date", default=date.today().isoformat())
    args = parser.parse_args()
    audit_date = date.fromisoformat(args.audit_date).isoformat()

    audit_path = RAW_DIR / f"manual_competitor_audit_{audit_date}.csv"
    boundary_path = sorted(RAW_DIR.glob("lisbon_parishes_*.geojson"))[-1]
    locations_path = PROCESSED_DIR / "coworking_locations.csv"
    queue_path = PROCESSED_DIR / "coworking_verification_queue.csv"

    audit = pd.read_csv(audit_path)
    locations = pd.read_csv(locations_path)
    candidates = build_rows(audit, audit_date)
    candidates = assign_parishes(candidates, boundary_path)
    if candidates["parish"].isna().any():
        names = candidates.loc[candidates["parish"].isna(), "coworking_name"].tolist()
        raise ValueError(f"Audit rows outside official Lisbon boundaries: {names}")

    added_rows: list[pd.Series] = []
    skipped_names: list[str] = []
    for _, candidate in candidates.iterrows():
        if is_existing_location(candidate, locations):
            skipped_names.append(candidate["coworking_name"])
            continue
        locations = pd.concat([locations, candidate.to_frame().T], ignore_index=True)
        added_rows.append(candidate)

    locations["duplicate_group"] = None
    locations = flag_duplicate_candidates(locations)
    locations = locations.sort_values(
        ["parish", "coworking_name", "coworking_id"], na_position="last"
    ).reset_index(drop=True)
    locations.to_csv(locations_path, index=False)

    queue_columns = [
        "coworking_id", "coworking_name", "operator", "address", "parish",
        "matched_rule", "source_url", "website", "active_status",
        "verification_status", "duplicate_group", "review_note",
    ]
    locations[queue_columns].to_csv(queue_path, index=False)

    added = pd.DataFrame(added_rows)
    log = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "audit_date": audit_date,
        "input": str(audit_path.relative_to(PROJECT_ROOT)),
        "added_count": len(added_rows),
        "skipped_existing_count": len(skipped_names),
        "skipped_existing_names": skipped_names,
        "added_by_parish": (
            added.groupby("parish").size().sort_index().to_dict()
            if not added.empty else {}
        ),
        "method_note": (
            "Only locations with a current official operator/service page, "
            "a physical address and coordinates inside an official Lisbon "
            "parish were included. Name-and-distance checks prevented duplicates."
        ),
    }
    log_path = PROJECT_ROOT / "reports" / "coworking_competitor_audit_log.json"
    log_path.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(log, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
