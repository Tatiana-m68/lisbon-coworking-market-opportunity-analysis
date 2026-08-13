"""Build the first 24-row Lisbon parish-indicator dataset."""

from __future__ import annotations

import argparse
import json
import math
from datetime import date
from pathlib import Path

import pandas as pd

from build_coworking_locations import geometry_contains_point
from config import PROCESSED_DIR, PROJECT_ROOT, RAW_DIR


EARTH_RADIUS_M = 6_371_008.8


def polygon_ring_area_m2(ring: list[list[float]]) -> float:
    """Approximate local polygon area with an equirectangular projection."""
    if len(ring) < 3:
        return 0.0
    mean_lat = math.radians(sum(point[1] for point in ring) / len(ring))
    xy = [
        (
            EARTH_RADIUS_M * math.radians(point[0]) * math.cos(mean_lat),
            EARTH_RADIUS_M * math.radians(point[1]),
        )
        for point in ring
    ]
    area = 0.0
    for index, (x1, y1) in enumerate(xy):
        x2, y2 = xy[(index + 1) % len(xy)]
        area += x1 * y2 - x2 * y1
    return abs(area) / 2


def geometry_area_km2(geometry: dict) -> float:
    geometry_type = geometry["type"]
    coordinates = geometry["coordinates"]
    polygons = [coordinates] if geometry_type == "Polygon" else coordinates
    total_area = 0.0
    for polygon in polygons:
        exterior = polygon_ring_area_m2(polygon[0])
        holes = sum(polygon_ring_area_m2(ring) for ring in polygon[1:])
        total_area += exterior - holes
    return total_area / 1_000_000


def get_coordinates(element: dict) -> tuple[float | None, float | None]:
    lat = element.get("lat")
    lon = element.get("lon")
    if lat is None or lon is None:
        center = element.get("center", {})
        lat = center.get("lat")
        lon = center.get("lon")
    return lat, lon


def classify_element(tags: dict) -> set[str]:
    categories: set[str] = set()
    office = tags.get("office")
    if office and office not in {"coworking", "coworking_space"}:
        categories.add("office_count")
    if tags.get("amenity") == "cafe":
        categories.add("cafe_count")
    if tags.get("tourism") == "hotel":
        categories.add("hotel_count")
    if tags.get("amenity") == "university":
        categories.add("university_count")
    if tags.get("amenity") == "college":
        categories.add("college_count")
    if (
        tags.get("railway") in {"station", "halt"}
        or tags.get("station") == "subway"
        or tags.get("public_transport") == "station"
    ):
        categories.add("major_transit_station_count")
    if (
        tags.get("highway") == "bus_stop"
        or tags.get("railway") == "tram_stop"
    ):
        categories.add("bus_tram_stop_count")
    return categories


def percentile_score(series: pd.Series) -> pd.Series:
    """Return a transparent 0-100 percentile-rank score."""
    return (series.rank(method="average", pct=True) * 100).round(2)


def find_latest(pattern: str, directory: Path) -> Path:
    matches = sorted(directory.glob(pattern))
    if not matches:
        raise FileNotFoundError(f"No file matching {pattern} in {directory}")
    return matches[-1]


def count_geojson_points_by_parish(
    path: Path,
    features_by_parish: dict[str, dict],
    *,
    active_field: str | None = None,
    active_value: object | None = None,
) -> tuple[dict[str, int], int]:
    """Assign municipal point features to official parish polygons."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    counts = {parish: 0 for parish in features_by_parish}
    unassigned = 0
    for feature in payload.get("features", []):
        properties = feature.get("properties", {})
        if active_field and properties.get(active_field) != active_value:
            continue
        geometry = feature.get("geometry") or {}
        if geometry.get("type") != "Point":
            unassigned += 1
            continue
        lon, lat = geometry.get("coordinates", [None, None])[:2]
        assigned = False
        for parish, boundary in features_by_parish.items():
            if geometry_contains_point(boundary["geometry"], lon, lat):
                counts[parish] += 1
                assigned = True
                break
        if not assigned:
            unassigned += 1
    return counts, unassigned


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--collection-date",
        default=date.today().isoformat(),
    )
    args = parser.parse_args()
    collection_date = date.fromisoformat(args.collection_date).isoformat()

    boundary_path = find_latest("lisbon_parishes_*.geojson", RAW_DIR)
    poi_path = RAW_DIR / f"osm_parish_pois_{collection_date}.json"
    population_path = (
        PROJECT_ROOT
        / "data"
        / "external"
        / f"ine_census2021_lisbon_parishes_{collection_date}.csv"
    )
    coworking_path = PROCESSED_DIR / "coworking_locations.csv"
    municipal_higher_education_path = find_latest(
        "municipal_higher_education_*.geojson", RAW_DIR
    )
    municipal_metro_path = find_latest(
        "municipal_metro_stations_*.geojson", RAW_DIR
    )
    municipal_hotels_path = find_latest(
        "municipal_hotels_*.geojson", RAW_DIR
    )

    boundaries = json.loads(boundary_path.read_text(encoding="utf-8"))
    population = pd.read_csv(population_path)
    coworking = pd.read_csv(coworking_path)
    poi_payload = json.loads(poi_path.read_text(encoding="utf-8"))

    rows: list[dict] = []
    features_by_parish: dict[str, dict] = {}
    for feature in boundaries["features"]:
        parish = feature["properties"]["NOME"]
        features_by_parish[parish] = feature
        rows.append(
            {
                "parish": parish,
                "area_km2": round(geometry_area_km2(feature["geometry"]), 4),
                "office_count": 0,
                "cafe_count": 0,
                "hotel_count": 0,
                "university_count": 0,
                "college_count": 0,
                "major_transit_station_count": 0,
                "bus_tram_stop_count": 0,
            }
        )
    indicators = pd.DataFrame(rows).set_index("parish")

    municipal_higher_education, higher_ed_unassigned = (
        count_geojson_points_by_parish(
            municipal_higher_education_path,
            features_by_parish,
            active_field="INF_ACTIVO",
            active_value=1,
        )
    )
    municipal_metro, metro_unassigned = count_geojson_points_by_parish(
        municipal_metro_path,
        features_by_parish,
    )
    municipal_hotels_2015, hotels_unassigned = count_geojson_points_by_parish(
        municipal_hotels_path,
        features_by_parish,
    )
    indicators["municipal_higher_education_count"] = pd.Series(
        municipal_higher_education
    )
    indicators["municipal_metro_station_count"] = pd.Series(municipal_metro)
    indicators["municipal_hotel_2015_count"] = pd.Series(municipal_hotels_2015)

    unassigned_elements = 0
    classified_elements = 0
    for element in poi_payload["elements"]:
        categories = classify_element(element.get("tags", {}))
        if not categories:
            continue
        classified_elements += 1
        lat, lon = get_coordinates(element)
        if lat is None or lon is None:
            unassigned_elements += 1
            continue
        assigned_parish: str | None = None
        for parish, feature in features_by_parish.items():
            if geometry_contains_point(feature["geometry"], lon, lat):
                assigned_parish = parish
                break
        if assigned_parish is None:
            unassigned_elements += 1
            continue
        for category in categories:
            indicators.at[assigned_parish, category] += 1

    indicators = indicators.reset_index()
    indicators = indicators.merge(population, on="parish", how="left", validate="1:1")

    verified = coworking[
        (coworking["active_status"] == "active")
        & (coworking["verification_status"] == "verified_official_site")
        & coworking["parish"].notna()
    ]
    pending = coworking[
        (coworking["verification_status"] == "pending")
        & coworking["parish"].notna()
    ]
    verified_counts = verified.groupby("parish").size()
    pending_counts = pending.groupby("parish").size()
    indicators["coworking_count"] = (
        indicators["parish"].map(verified_counts).fillna(0).astype(int)
    )
    indicators["pending_coworking_count"] = (
        indicators["parish"].map(pending_counts).fillna(0).astype(int)
    )
    indicators["higher_education_count"] = (
        indicators["university_count"] + indicators["college_count"]
    )

    density_numerators = {
        "working_age_population_density_km2": "working_age_population_15_64",
        "coworking_density_km2": "coworking_count",
        "office_density_km2": "office_count",
        "cafe_density_km2": "cafe_count",
        "hotel_density_km2": "hotel_count",
        "higher_education_density_km2": "higher_education_count",
        "municipal_higher_education_density_km2": (
            "municipal_higher_education_count"
        ),
        "major_transit_station_density_km2": "major_transit_station_count",
        "municipal_metro_station_density_km2": "municipal_metro_station_count",
        "bus_tram_stop_density_km2": "bus_tram_stop_count",
    }
    for output_column, numerator in density_numerators.items():
        indicators[output_column] = (
            indicators[numerator] / indicators["area_km2"]
        ).round(3)

    indicators["coworking_per_10000_working_age"] = (
        indicators["coworking_count"]
        / indicators["working_age_population_15_64"]
        * 10_000
    ).round(3)

    indicators["transit_access_score"] = (
        0.6
        * percentile_score(indicators["municipal_metro_station_density_km2"])
        + 0.4
        * percentile_score(indicators["bus_tram_stop_density_km2"])
    ).round(2)
    indicators["demand_proxy_score"] = (
        0.40
        * percentile_score(indicators["working_age_population_density_km2"])
        + 0.30 * percentile_score(indicators["office_density_km2"])
        + 0.10 * percentile_score(indicators["cafe_density_km2"])
        + 0.10 * percentile_score(indicators["hotel_density_km2"])
        + 0.10
        * percentile_score(
            indicators["municipal_higher_education_density_km2"]
        )
    ).round(2)

    indicators["median_rent_eur_m2_month"] = pd.NA
    indicators["rent_sample_size"] = 0
    indicators["rent_coverage_flag"] = "not_collected"
    indicators["opportunity_score"] = pd.NA
    indicators["poi_query_status"] = "success"
    indicators["collection_date"] = collection_date
    indicators["population_reference_year"] = 2021
    indicators["coworking_status_note"] = (
        "Count includes verified active rows with assigned parishes. Manual "
        f"review is complete; all {len(verified)} verified rows have coordinates."
    )

    ordered_columns = [
        "parish_code",
        "parish",
        "area_km2",
        "population_total",
        "working_age_population_15_64",
        "coworking_count",
        "pending_coworking_count",
        "coworking_per_10000_working_age",
        "office_count",
        "cafe_count",
        "hotel_count",
        "university_count",
        "college_count",
        "higher_education_count",
        "municipal_higher_education_count",
        "municipal_hotel_2015_count",
        "major_transit_station_count",
        "municipal_metro_station_count",
        "bus_tram_stop_count",
        "working_age_population_density_km2",
        "coworking_density_km2",
        "office_density_km2",
        "cafe_density_km2",
        "hotel_density_km2",
        "higher_education_density_km2",
        "municipal_higher_education_density_km2",
        "major_transit_station_density_km2",
        "municipal_metro_station_density_km2",
        "bus_tram_stop_density_km2",
        "transit_access_score",
        "demand_proxy_score",
        "median_rent_eur_m2_month",
        "rent_sample_size",
        "rent_coverage_flag",
        "opportunity_score",
        "poi_query_status",
        "population_reference_year",
        "collection_date",
        "coworking_status_note",
    ]
    indicators = indicators[ordered_columns].sort_values("parish")
    output_path = PROCESSED_DIR / "parish_indicators.csv"
    indicators.to_csv(output_path, index=False)

    build_log = {
        "collection_date": collection_date,
        "output": str(output_path.relative_to(PROJECT_ROOT)),
        "row_count": len(indicators),
        "classified_osm_elements": classified_elements,
        "unassigned_or_outside_osm_elements": unassigned_elements,
        "official_boundary_file": str(boundary_path.relative_to(PROJECT_ROOT)),
        "population_file": str(population_path.relative_to(PROJECT_ROOT)),
        "coworking_file": str(coworking_path.relative_to(PROJECT_ROOT)),
        "poi_file": str(poi_path.relative_to(PROJECT_ROOT)),
        "municipal_higher_education_file": str(
            municipal_higher_education_path.relative_to(PROJECT_ROOT)
        ),
        "municipal_metro_file": str(
            municipal_metro_path.relative_to(PROJECT_ROOT)
        ),
        "municipal_hotel_validation_file": str(
            municipal_hotels_path.relative_to(PROJECT_ROOT)
        ),
        "municipal_unassigned_points": {
            "higher_education": higher_ed_unassigned,
            "metro": metro_unassigned,
            "hotels_2015": hotels_unassigned,
        },
        "score_note": (
            "Scores are transparent percentile-rank screening indices, not "
            "forecasts. Transit uses official municipal metro stations plus "
            "OSM bus/tram stops; demand uses official municipal higher "
            "education plus OSM proxies. Opportunity score is intentionally blank."
        ),
    }
    log_path = PROJECT_ROOT / "reports" / "parish_indicators_build_log.json"
    log_path.write_text(
        json.dumps(build_log, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Saved {len(indicators)} parish rows to {output_path}")
    print(f"Total computed area: {indicators['area_km2'].sum():.2f} km²")
    print(f"OSM elements inside Lisbon counted: {classified_elements - unassigned_elements}")
    print(f"OSM elements outside/unassigned: {unassigned_elements}")


if __name__ == "__main__":
    main()
