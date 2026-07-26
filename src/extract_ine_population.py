"""Extract Lisbon parish aggregates from the official INE Census 2021 workbook."""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

import pandas as pd

from config import PROJECT_ROOT


INE_SOURCE_URL = (
    "https://mapas.ine.pt/download/2021FicheiroSintese/"
    "FS2021SubSeccaoTot.zip"
)
USE_COLUMNS = [
    "MUNICIPIO",
    "MUNICIPIO DSG",
    "FREGUESIA",
    "FREGUESIA DSG",
    "SECCAO",
    "SUBSECCAO",
    "N_INDIVIDUOS",
    "N_INDIVIDUOS_0_14",
    "N_INDIVIDUOS_15_24",
    "N_INDIVIDUOS_25_64",
    "N_INDIVIDUOS_65_OU_MAIS",
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("workbook", type=Path)
    parser.add_argument(
        "--collection-date",
        default=date.today().isoformat(),
    )
    args = parser.parse_args()
    collection_date = date.fromisoformat(args.collection_date).isoformat()

    dataframe = pd.read_excel(
        args.workbook,
        header=1,
        usecols=USE_COLUMNS,
    )
    parish_rows = dataframe[
        (dataframe["MUNICIPIO"] == 1106)
        & dataframe["FREGUESIA"].notna()
        & dataframe["SECCAO"].isna()
        & dataframe["SUBSECCAO"].isna()
    ].copy()
    if len(parish_rows) != 24:
        raise ValueError(f"Expected 24 Lisbon parish rows, found {len(parish_rows)}.")

    parish_rows["working_age_population_15_64"] = (
        parish_rows["N_INDIVIDUOS_15_24"]
        + parish_rows["N_INDIVIDUOS_25_64"]
    )
    parish_rows = parish_rows.rename(
        columns={
            "FREGUESIA": "parish_code",
            "FREGUESIA DSG": "parish",
            "N_INDIVIDUOS": "population_total",
            "N_INDIVIDUOS_0_14": "population_0_14",
            "N_INDIVIDUOS_15_24": "population_15_24",
            "N_INDIVIDUOS_25_64": "population_25_64",
            "N_INDIVIDUOS_65_OU_MAIS": "population_65_plus",
        }
    )
    output_columns = [
        "parish_code",
        "parish",
        "population_total",
        "population_0_14",
        "population_15_24",
        "population_25_64",
        "working_age_population_15_64",
        "population_65_plus",
    ]
    output_dir = PROJECT_ROOT / "data" / "external"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"ine_census2021_lisbon_parishes_{collection_date}.csv"
    metadata_path = output_dir / f"ine_census2021_metadata_{collection_date}.json"
    parish_rows[output_columns].sort_values("parish").to_csv(
        output_path,
        index=False,
    )
    metadata = {
        "source": "INE, Census 2021 synthesis file - statistical subsections",
        "source_url": INE_SOURCE_URL,
        "source_workbook": args.workbook.name,
        "source_workbook_omitted_from_repository": True,
        "omission_reason": "Official source ZIP is approximately 42 MB.",
        "download_and_extraction_note": (
            "Download the ZIP from source_url, extract the XLSX, then run "
            "src/extract_ine_population.py against that workbook."
        ),
        "municipality_filter": "MUNICIPIO == 1106 (Lisboa)",
        "grain_filter": "Parish aggregate rows: SECCAO and SUBSECCAO are null",
        "row_count": len(parish_rows),
        "age_definition_note": (
            "The synthesis provides 15-24 and 25-64, not a separate 20-24 "
            "band. Therefore the reproducible measure is ages 15-64."
        ),
    }
    metadata_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Saved {len(parish_rows)} official parish population rows.")
    print(output_path)


if __name__ == "__main__":
    main()
