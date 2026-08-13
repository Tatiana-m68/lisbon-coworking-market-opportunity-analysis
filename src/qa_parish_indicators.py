"""Audit completeness, ranges, reconciliation, and coverage of parish indicators."""

from __future__ import annotations

import json
from datetime import datetime, timezone

import pandas as pd

from config import PROCESSED_DIR, PROJECT_ROOT


COUNT_COLUMNS = [
    "coworking_count",
    "pending_coworking_count",
    "office_count",
    "cafe_count",
    "hotel_count",
    "university_count",
    "college_count",
    "municipal_higher_education_count",
    "municipal_hotel_2015_count",
    "major_transit_station_count",
    "municipal_metro_station_count",
    "bus_tram_stop_count",
]
CORE_COMPLETE_COLUMNS = [
    "parish_code",
    "parish",
    "area_km2",
    "population_total",
    "working_age_population_15_64",
    *COUNT_COLUMNS,
    "transit_access_score",
    "demand_proxy_score",
]


def main() -> None:
    dataset_path = PROCESSED_DIR / "parish_indicators.csv"
    coworking_path = PROCESSED_DIR / "coworking_locations.csv"
    output_path = PROJECT_ROOT / "reports" / "parish_indicators_quality.json"
    dataframe = pd.read_csv(dataset_path)
    coworking = pd.read_csv(coworking_path)

    expected_verified_coworking = int(
        (
            (coworking["active_status"] == "active")
            & (coworking["verification_status"] == "verified_official_site")
            & coworking["parish"].notna()
        ).sum()
    )
    checks = {
        "exactly_24_rows": len(dataframe) == 24,
        "unique_parishes": dataframe["parish"].nunique() == 24,
        "unique_parish_codes": dataframe["parish_code"].nunique() == 24,
        "core_fields_complete": not dataframe[CORE_COMPLETE_COLUMNS].isna().any().any(),
        "areas_positive": bool((dataframe["area_km2"] > 0).all()),
        "population_positive": bool((dataframe["population_total"] > 0).all()),
        "working_age_not_above_total": bool(
            (
                dataframe["working_age_population_15_64"]
                <= dataframe["population_total"]
            ).all()
        ),
        "counts_non_negative": bool((dataframe[COUNT_COLUMNS] >= 0).all().all()),
        "score_ranges_valid": bool(
            dataframe["transit_access_score"].between(0, 100).all()
            and dataframe["demand_proxy_score"].between(0, 100).all()
        ),
        "verified_coworking_reconciles": (
            int(dataframe["coworking_count"].sum()) == expected_verified_coworking
        ),
        "rent_transparently_missing": bool(
            dataframe["median_rent_eur_m2_month"].isna().all()
            and (dataframe["rent_coverage_flag"] == "not_collected").all()
        ),
        "opportunity_score_deferred": bool(
            dataframe["opportunity_score"].isna().all()
        ),
    }
    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "dataset": str(dataset_path.relative_to(PROJECT_ROOT)),
        "row_count": len(dataframe),
        "column_count": len(dataframe.columns),
        "total_area_km2": round(float(dataframe["area_km2"].sum()), 2),
        "total_population_2021": int(dataframe["population_total"].sum()),
        "total_working_age_population_15_64": int(
            dataframe["working_age_population_15_64"].sum()
        ),
        "verified_coworking_count": int(dataframe["coworking_count"].sum()),
        "pending_coworking_count": int(
            dataframe["pending_coworking_count"].sum()
        ),
        "osm_totals": {
            column: int(dataframe[column].sum())
            for column in COUNT_COLUMNS
            if column not in {"coworking_count", "pending_coworking_count"}
        },
        "municipal_validation_totals": {
            "higher_education_current": int(
                dataframe["municipal_higher_education_count"].sum()
            ),
            "metro_stations_current": int(
                dataframe["municipal_metro_station_count"].sum()
            ),
            "hotels_2015_reference_only": int(
                dataframe["municipal_hotel_2015_count"].sum()
            ),
        },
        "zero_count_parishes": {
            column: int((dataframe[column] == 0).sum())
            for column in COUNT_COLUMNS
        },
        "missingness": {
            column: int(dataframe[column].isna().sum())
            for column in dataframe.columns
        },
        "checks": checks,
        "checks_passed": all(checks.values()),
        "coverage_assessment": {
            "geography": "complete_24_of_24",
            "population": "complete_24_of_24_official_census_2021",
            "osm_pois": "complete_query_but_tagging_completeness_unknown",
            "transit": (
                "official_municipal_metro_complete; "
                "osm_bus_tram_tagging_completeness_unknown"
            ),
            "higher_education": "official_municipal_points_complete",
            "hotels": (
                "osm_current_proxy_cross_checked_against_stale_2015_"
                "municipal_reference"
            ),
            "coworking": (
                "manual_candidate_review_complete; all verified locations "
                "have coordinates and parish assignments"
            ),
            "rent": "not_collected",
        },
    }
    output_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["checks_passed"]:
        raise SystemExit("Parish indicator QA failed.")


if __name__ == "__main__":
    main()
