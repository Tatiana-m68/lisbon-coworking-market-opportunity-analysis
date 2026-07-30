"""Prepare an auditable pilot sample of Lisbon commercial asking rents."""

from __future__ import annotations

import json

import numpy as np
import pandas as pd

from src.config import (
    COMMERCIAL_RENT_BUILDINGS_FILE,
    COMMERCIAL_RENT_LISTINGS_FILE,
    COMMERCIAL_RENT_PARISH_FILE,
    COMMERCIAL_RENT_RAW_PATTERN,
    RAW_DIR,
)


BOUNDARIES_FILE = RAW_DIR / "lisbon_parishes_2026-07-24.geojson"
MIN_LISTINGS_FOR_MEDIAN = 5
TARGET_LISTINGS_PER_PARISH = 10


def load_raw_listings() -> pd.DataFrame:
    """Flatten all saved connector snapshots without changing raw files."""
    rows = []
    raw_files = sorted(RAW_DIR.glob(COMMERCIAL_RENT_RAW_PATTERN))
    if not raw_files:
        raise FileNotFoundError("No commercial rent snapshots were found.")

    for raw_file in raw_files:
        with raw_file.open(encoding="utf-8") as file:
            payload = json.load(file)
        for search in payload["searches"]:
            for listing in search["listings"]:
                rows.append(
                    {
                        "listing_id": f"idealista_{listing['property_code']}",
                        "source_name": payload["source_name"],
                        "source_snapshot": raw_file.name,
                        "source_url": listing["source_url"],
                        "collection_date": payload["collection_date"],
                        "requested_parish": search["requested_parish"],
                        "address_or_area_text": listing["title"],
                        "property_type": listing["property_type"],
                        "property_subtype": listing["property_subtype"],
                        "monthly_rent_eur": listing["monthly_rent_eur"],
                        "area_m2": listing["area_m2"],
                        "source_rent_eur_m2_month": listing[
                            "source_price_eur_m2_month"
                        ],
                        "latitude": listing["latitude"],
                        "longitude": listing["longitude"],
                        "listing_status": listing["status"],
                    }
                )
    return (
        pd.DataFrame(rows)
        .sort_values(["listing_id", "source_snapshot", "requested_parish"])
        .drop_duplicates("listing_id", keep="first")
        .reset_index(drop=True)
    )


def point_in_ring(
    longitude: float,
    latitude: float,
    ring: list[list[float]],
) -> bool:
    """Return whether a WGS84 point lies inside one polygon ring."""
    inside = False
    previous = ring[-1]
    for current in ring:
        x1, y1 = previous
        x2, y2 = current
        crosses = (y1 > latitude) != (y2 > latitude)
        if crosses:
            boundary_x = (x2 - x1) * (latitude - y1) / (y2 - y1) + x1
            if longitude < boundary_x:
                inside = not inside
        previous = current
    return inside


def point_in_polygon(
    longitude: float,
    latitude: float,
    coordinates: list,
) -> bool:
    """Check an exterior ring and exclude any interior holes."""
    return point_in_ring(longitude, latitude, coordinates[0]) and not any(
        point_in_ring(longitude, latitude, hole)
        for hole in coordinates[1:]
    )


def find_parish(
    longitude: float,
    latitude: float,
    features: list[dict],
) -> str | None:
    """Find the official parish containing a coordinate."""
    for feature in features:
        geometry = feature["geometry"]
        polygons = (
            [geometry["coordinates"]]
            if geometry["type"] == "Polygon"
            else geometry["coordinates"]
        )
        if any(
            point_in_polygon(longitude, latitude, polygon)
            for polygon in polygons
        ):
            return feature["properties"]["NOME"]
    return None


def assign_parishes(listings: pd.DataFrame) -> pd.DataFrame:
    """Assign official parishes from coordinates and flag search mismatches."""
    with BOUNDARIES_FILE.open(encoding="utf-8") as file:
        features = json.load(file)["features"]

    assigned = listings.copy()
    assigned["parish"] = [
        find_parish(row.longitude, row.latitude, features)
        for row in assigned.itertuples()
    ]
    assigned["parish_assignment_method"] = np.where(
        assigned["parish"].notna(),
        "coordinate_within_official_boundary",
        "unresolved",
    )
    assigned["requested_parish_match"] = assigned["requested_parish"].eq(
        assigned["parish"]
    )
    return assigned


def clean_listings(listings: pd.DataFrame) -> pd.DataFrame:
    """Validate values and create transparent listing/building keys."""
    listings = listings.copy()
    listings["calculated_rent_eur_m2_month"] = (
        listings["monthly_rent_eur"] / listings["area_m2"]
    ).round(2)
    listings["rent_value_difference"] = (
        listings["calculated_rent_eur_m2_month"]
        - listings["source_rent_eur_m2_month"]
    ).abs()
    listings["valid_for_analysis"] = (
        listings["parish"].notna()
        & listings["monthly_rent_eur"].gt(0)
        & listings["area_m2"].gt(0)
        & listings["calculated_rent_eur_m2_month"].between(2, 100)
    )
    listings["building_key"] = (
        listings["parish"].fillna("unresolved")
        + "_"
        + listings["latitude"].round(4).astype(str)
        + "_"
        + listings["longitude"].round(4).astype(str)
    )
    listings["duplicate_key"] = (
        listings["building_key"]
        + "_"
        + listings["area_m2"].round(0).astype(str)
        + "_"
        + listings["monthly_rent_eur"].round(0).astype(str)
    )
    listings["verification_note"] = np.select(
        [
            listings["parish"].isna(),
            ~listings["requested_parish_match"],
            ~listings["calculated_rent_eur_m2_month"].between(2, 100),
            listings["rent_value_difference"].gt(1.0),
        ],
        [
            "Coordinate is outside or not assigned to a Lisbon parish.",
            "Spatially assigned parish differs from the search parish.",
            "Calculated unit rent is outside the plausible analysis range.",
            "Calculated unit rent differs materially from source rounding.",
        ],
        default="Passed automated coordinate and value checks.",
    )
    return listings


def aggregate_buildings(listings: pd.DataFrame) -> pd.DataFrame:
    """Reduce same-building listing concentration before parish aggregation."""
    valid = listings[listings["valid_for_analysis"]].copy()
    return (
        valid.groupby(["building_key", "parish"], as_index=False)
        .agg(
            listing_count=("listing_id", "nunique"),
            median_monthly_rent_eur=("monthly_rent_eur", "median"),
            median_area_m2=("area_m2", "median"),
            median_rent_eur_m2_month=(
                "calculated_rent_eur_m2_month",
                "median",
            ),
            latitude=("latitude", "first"),
            longitude=("longitude", "first"),
            collection_date=("collection_date", "max"),
        )
        .sort_values(["parish", "building_key"])
        .reset_index(drop=True)
    )


def aggregate_parishes(
    listings: pd.DataFrame,
    buildings: pd.DataFrame,
) -> pd.DataFrame:
    """Create coverage-aware parish medians based on unique buildings."""
    listing_counts = (
        listings[listings["valid_for_analysis"]]
        .groupby("parish")["listing_id"]
        .nunique()
        .rename("valid_listing_count")
    )
    summary = (
        buildings.groupby("parish")
        .agg(
            rent_sample_size=("building_key", "nunique"),
            median_rent_eur_m2_month=(
                "median_rent_eur_m2_month",
                "median",
            ),
            min_rent_eur_m2_month=("median_rent_eur_m2_month", "min"),
            max_rent_eur_m2_month=("median_rent_eur_m2_month", "max"),
            collection_date=("collection_date", "max"),
        )
        .join(listing_counts)
        .reset_index()
    )
    summary["rent_coverage_flag"] = np.select(
        [
            summary["rent_sample_size"].ge(TARGET_LISTINGS_PER_PARISH),
            summary["rent_sample_size"].ge(MIN_LISTINGS_FOR_MEDIAN),
        ],
        ["target_met", "usable_low_coverage"],
        default="insufficient",
    )
    numeric_columns = [
        "median_rent_eur_m2_month",
        "min_rent_eur_m2_month",
        "max_rent_eur_m2_month",
    ]
    summary[numeric_columns] = summary[numeric_columns].round(2)
    return summary.sort_values("parish").reset_index(drop=True)


def main() -> None:
    """Build processed rent tables and enforce core quality controls."""
    listings = clean_listings(assign_parishes(load_raw_listings()))
    buildings = aggregate_buildings(listings)
    parish_summary = aggregate_parishes(listings, buildings)

    assert listings["listing_id"].is_unique
    assert len(listings) >= 150
    assert listings["parish"].notna().all()
    assert listings["valid_for_analysis"].mean() >= 0.95
    target_coverage = parish_summary.set_index("parish").loc[
        [
            "Areeiro",
            "Arroios",
            "Campolide",
            "Misericórdia",
            "Lumiar",
            "Avenidas Novas",
            "Santo António",
            "Penha de França",
            "Carnide",
            "São Domingos de Benfica",
        ],
        "rent_coverage_flag",
    ]
    assert target_coverage.isin(["target_met", "usable_low_coverage"]).all()

    COMMERCIAL_RENT_LISTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    listings.to_csv(COMMERCIAL_RENT_LISTINGS_FILE, index=False)
    buildings.to_csv(COMMERCIAL_RENT_BUILDINGS_FILE, index=False)
    parish_summary.to_csv(COMMERCIAL_RENT_PARISH_FILE, index=False)

    print(f"Saved {len(listings)} listing records.")
    print(f"Reduced to {len(buildings)} unique building observations.")
    print(parish_summary.to_string(index=False))


if __name__ == "__main__":
    main()
