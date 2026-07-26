"""Run reproducible quality checks for the coworking-location candidate table."""

from __future__ import annotations

import json
from datetime import datetime, timezone

import pandas as pd

from config import PROCESSED_DIR, PROJECT_ROOT


REQUIRED_COLUMNS = {
    "coworking_id",
    "coworking_name",
    "latitude",
    "longitude",
    "parish",
    "active_status",
    "source_url",
    "collection_date",
    "verification_status",
}
VALID_ACTIVE_STATUSES = {"active", "uncertain", "closed"}
VALID_PARISHES = {
    "Ajuda",
    "Alcântara",
    "Alvalade",
    "Areeiro",
    "Arroios",
    "Avenidas Novas",
    "Beato",
    "Belém",
    "Benfica",
    "Campo de Ourique",
    "Campolide",
    "Carnide",
    "Estrela",
    "Lumiar",
    "Marvila",
    "Misericórdia",
    "Olivais",
    "Parque das Nações",
    "Penha de França",
    "Santa Clara",
    "Santa Maria Maior",
    "Santo António",
    "São Domingos de Benfica",
    "São Vicente",
}


def main() -> None:
    dataset_path = PROCESSED_DIR / "coworking_locations.csv"
    output_path = PROJECT_ROOT / "reports" / "coworking_data_quality.json"
    dataframe = pd.read_csv(dataset_path)

    missing_required_columns = sorted(REQUIRED_COLUMNS - set(dataframe.columns))
    invalid_statuses = sorted(
        set(dataframe["active_status"].dropna()) - VALID_ACTIVE_STATUSES
    )
    invalid_parishes = sorted(
        set(dataframe["parish"].dropna()) - VALID_PARISHES
    )
    invalid_latitudes = int(
        (
            (~dataframe["latitude"].between(38.65, 38.85))
            & dataframe["latitude"].notna()
        ).sum()
    )
    invalid_longitudes = int(
        (
            (~dataframe["longitude"].between(-9.30, -9.00))
            & dataframe["longitude"].notna()
        ).sum()
    )

    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "dataset": str(dataset_path.relative_to(PROJECT_ROOT)),
        "row_count": len(dataframe),
        "column_count": len(dataframe.columns),
        "verified_active_count": int(
            (
                (dataframe["active_status"] == "active")
                & (dataframe["verification_status"] == "verified_official_site")
            ).sum()
        ),
        "pending_verification_count": int(
            (dataframe["verification_status"] == "pending").sum()
        ),
        "parishes_represented": int(dataframe["parish"].nunique()),
        "missingness": {
            column: int(dataframe[column].isna().sum())
            for column in REQUIRED_COLUMNS
            if column in dataframe
        },
        "duplicate_id_count": int(dataframe["coworking_id"].duplicated().sum()),
        "potential_duplicate_row_count": int(
            dataframe["duplicate_group"].notna().sum()
        ),
        "invalid_latitude_count": invalid_latitudes,
        "invalid_longitude_count": invalid_longitudes,
        "invalid_statuses": invalid_statuses,
        "invalid_parishes": invalid_parishes,
        "missing_required_columns": missing_required_columns,
        "checks_passed": bool(
            not missing_required_columns
            and not invalid_statuses
            and not invalid_parishes
            and invalid_latitudes == 0
            and invalid_longitudes == 0
            and dataframe["coworking_id"].duplicated().sum() == 0
        ),
        "important_caveat": (
            "This is a candidate inventory. Only rows with "
            "verification_status=verified_official_site are currently confirmed active."
        ),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["checks_passed"]:
        raise SystemExit("One or more structural quality checks failed.")


if __name__ == "__main__":
    main()
