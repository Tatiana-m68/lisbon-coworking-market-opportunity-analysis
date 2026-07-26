"""Build the frozen MVP dataset and initial EDA notebook."""

from __future__ import annotations

import csv
import textwrap
from pathlib import Path

import nbformat as nbf


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = PROJECT_ROOT / "data" / "processed" / "coworking_locations.csv"
MVP_FILENAME = "coworking_locations_mvp_2026-07-25.csv"
MVP_PATH = PROJECT_ROOT / "data" / "raw" / MVP_FILENAME
NOTEBOOK_PATH = PROJECT_ROOT / "notebooks" / "01_eda.ipynb"

MVP_FIELDS = [
    "coworking_id",
    "coworking_name",
    "latitude",
    "longitude",
    "parish",
    "active_status",
    "source_url",
    "collection_date",
    "source_type",
    "verification_status",
]


def build_mvp_dataset() -> int:
    """Freeze the verified-active subset as the raw initial-analysis snapshot."""
    with SOURCE_PATH.open(encoding="utf-8-sig", newline="") as source_file:
        rows = [
            row
            for row in csv.DictReader(source_file)
            if row["active_status"] == "active"
            and row["verification_status"] == "verified_official_site"
        ]

    if len(rows) != 48:
        raise ValueError(f"Expected 48 verified active locations, found {len(rows)}")
    if len({row["coworking_id"] for row in rows}) != len(rows):
        raise ValueError("coworking_id must be unique in the MVP dataset")

    MVP_PATH.parent.mkdir(parents=True, exist_ok=True)
    with MVP_PATH.open("w", encoding="utf-8", newline="") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=MVP_FIELDS)
        writer.writeheader()
        writer.writerows({field: row[field] for field in MVP_FIELDS} for row in rows)
    return len(rows)


def markdown(text: str):
    return nbf.v4.new_markdown_cell(textwrap.dedent(text).strip())


def code(text: str):
    return nbf.v4.new_code_cell(textwrap.dedent(text).strip())


def build_notebook() -> None:
    """Create the reproducible initial EDA notebook."""
    cells = [
        markdown(
            """
            # Initial EDA: verified coworking locations in Lisbon

            This notebook provides the initial exploratory analysis for the
            Lisbon Coworking Market Opportunity Analysis. It inspects a frozen MVP
            snapshot containing confirmed active coworking locations. The
            original discovery and verification history remains in the wider
            project datasets; this checkpoint focuses on a small, reproducible
            table suitable for initial exploratory data analysis.
            """
        ),
        markdown(
            """
            ## 1. Imports and data loading

            The CSV is loaded with a path relative to this notebook. The raw
            checkpoint file is read only and is not overwritten.
            """
        ),
        code(
            f"""
            from pathlib import Path

            import matplotlib.pyplot as plt
            import pandas as pd
            import seaborn as sns

            sns.set_theme(style="whitegrid")

            PROJECT_ROOT = Path.cwd()
            if PROJECT_ROOT.name == "notebooks":
                PROJECT_ROOT = PROJECT_ROOT.parent

            DATA_PATH = PROJECT_ROOT / "data" / "raw" / "{MVP_FILENAME}"
            FIGURES_DIR = PROJECT_ROOT / "reports" / "figures"
            TABLES_DIR = PROJECT_ROOT / "reports" / "tables"
            FIGURE_PATH = FIGURES_DIR / "01_coworking_locations_by_parish.png"
            TABLE_PATH = TABLES_DIR / "coworking_locations_by_parish.csv"

            FIGURES_DIR.mkdir(parents=True, exist_ok=True)
            TABLES_DIR.mkdir(parents=True, exist_ok=True)

            df = pd.read_csv(DATA_PATH, parse_dates=["collection_date"])
            """
        ),
        markdown(
            """
            ## 2. Basic structure

            First, check the number of rows and columns, column names, data
            types, and a small sample. Latitude and longitude should be numeric;
            identifiers and descriptive fields should remain text.
            """
        ),
        code(
            """
            print(f"Shape: {df.shape}")
            print("\\nColumns:")
            print(df.columns.tolist())
            print("\\nData types:")
            print(df.dtypes)
            df.head(5)
            """
        ),
        markdown(
            """
            ## 3. Missing values and critical-column validation

            For this checkpoint, `coworking_id`, `coworking_name`,
            `active_status`, and `source_url` are critical. None of them should
            be completely empty. Missing coordinates or parish values are kept
            visible so they can be resolved in the next cleaning step.
            """
        ),
        code(
            """
            critical_columns = [
                "coworking_id",
                "coworking_name",
                "active_status",
                "source_url",
            ]

            missing_summary = (
                df.isna()
                .sum()
                .rename("missing_count")
                .to_frame()
                .assign(missing_percent=lambda x: (x["missing_count"] / len(df) * 100).round(2))
            )
            display(missing_summary)

            completely_empty_critical = [
                column for column in critical_columns if df[column].isna().all()
            ]
            print("Completely empty critical columns:", completely_empty_critical)
            assert not completely_empty_critical
            """
        ),
        markdown(
            """
            ## 4. Descriptive statistics and category counts

            Descriptive statistics summarise numeric coverage. Value counts show
            how locations are distributed across parishes and source types.
            """
        ),
        code(
            """
            display(df.describe(include="all").T)
            display(df["parish"].value_counts(dropna=False).rename("location_count").to_frame())
            display(df["source_type"].value_counts(dropna=False).rename("location_count").to_frame())
            """
        ),
        markdown(
            """
            ## 5. Duplicate checks

            Exact duplicate rows and repeated IDs would invalidate location
            counts. A second check flags records sharing the same name and
            coordinates, which can reveal branches imported twice.
            """
        ),
        code(
            """
            exact_duplicate_rows = int(df.duplicated().sum())
            duplicate_ids = int(df["coworking_id"].duplicated().sum())
            duplicate_name_coordinates = int(
                df.duplicated(subset=["coworking_name", "latitude", "longitude"]).sum()
            )

            print("Exact duplicate rows:", exact_duplicate_rows)
            print("Duplicate coworking IDs:", duplicate_ids)
            print("Duplicate name-coordinate combinations:", duplicate_name_coordinates)
            """
        ),
        markdown(
            """
            ## 6. Simple visualisation

            The chart is an initial view of observed coworking competition by
            parish. It is not yet an opportunity ranking: population, transport,
            rents, and other demand indicators will be joined later. The chart
            is exported by code as a PNG file in `reports/figures/`.
            """
        ),
        code(
            """
            parish_counts = (
                df["parish"]
                .fillna("Parish not yet assigned")
                .value_counts()
                .sort_values(ascending=True)
            )

            fig, ax = plt.subplots(figsize=(10, 7))
            sns.barplot(
                x=parish_counts.values,
                y=parish_counts.index,
                color="#2A9D8F",
                ax=ax,
            )
            ax.set_title("Verified active coworking locations by Lisbon parish")
            ax.set_xlabel("Number of locations")
            ax.set_ylabel("Parish")
            fig.tight_layout()
            fig.savefig(FIGURE_PATH, dpi=150, bbox_inches="tight")
            plt.show()

            print(f"Saved chart: {FIGURE_PATH.relative_to(PROJECT_ROOT)}")
            """
        ),
        markdown(
            """
            ## 7. BI-ready summary table

            The parish counts behind the chart are exported as a tidy CSV file
            with one row per represented parish. This file can be imported into
            Power BI or Tableau without copying values manually.
            """
        ),
        code(
            """
            parish_summary = (
                df.groupby("parish", as_index=False)
                .agg(coworking_location_count=("coworking_id", "nunique"))
                .sort_values(
                    ["coworking_location_count", "parish"],
                    ascending=[False, True],
                )
                .reset_index(drop=True)
            )

            parish_summary.to_csv(TABLE_PATH, index=False)
            display(parish_summary)
            print(f"Saved summary table: {TABLE_PATH.relative_to(PROJECT_ROOT)}")
            """
        ),
        markdown(
            """
            ## 8. Initial data-quality observations

            1. The checkpoint contains **48 confirmed active locations**, and
               all critical identification and source fields are populated.
            2. **Latitude, longitude, and parish are complete for all 48
               locations** after address verification and geocoding against
               official operator information and OpenStreetMap building points.
            3. There are **no exact duplicate rows and no duplicate IDs** in
               this frozen snapshot. Name-and-coordinate matches are also
               checked because the same operator can legitimately have several
               Lisbon branches.
            4. `active_status` and `verification_status` have one value by
               design: this MVP is a verified-active analysis subset, not the
               full candidate history. Closed and excluded candidates remain in
               the processed audit table.

            The next technical step is to join these complete location counts
            to the 24-row parish indicators table and continue the full EDA.
            """
        ),
    ]

    notebook = nbf.v4.new_notebook(
        cells=cells,
        metadata={
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "version": "3"},
        },
    )
    NOTEBOOK_PATH.parent.mkdir(parents=True, exist_ok=True)
    nbf.write(notebook, NOTEBOOK_PATH)


if __name__ == "__main__":
    count = build_mvp_dataset()
    build_notebook()
    print(f"Wrote {count} rows to {MVP_PATH}")
    print(f"Wrote notebook to {NOTEBOOK_PATH}")
