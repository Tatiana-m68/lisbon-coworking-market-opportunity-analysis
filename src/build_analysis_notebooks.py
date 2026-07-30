"""Build the cleaning, EDA and provisional decision-analysis notebooks."""

from __future__ import annotations

import textwrap
from pathlib import Path

import nbformat as nbf


PROJECT_ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_DIR = PROJECT_ROOT / "notebooks"


def markdown(text: str):
    """Create a dedented Markdown cell."""
    return nbf.v4.new_markdown_cell(textwrap.dedent(text).strip())


def code(text: str):
    """Create a dedented code cell."""
    return nbf.v4.new_code_cell(textwrap.dedent(text).strip())


def notebook(cells: list) -> nbf.NotebookNode:
    """Create a notebook with the project's standard Python kernel metadata."""
    return nbf.v4.new_notebook(
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


def build_cleaning_notebook() -> nbf.NotebookNode:
    """Create the analysis-table preparation notebook."""
    return notebook(
        [
            markdown(
                """
                # 02 Cleaning and analysis-table preparation

                This notebook validates the two processed source tables and
                creates a 24-row parish-level analysis table. A pilot commercial
                asking-rent sample is available for three priority parishes;
                the citywide output therefore remains provisional.
                """
            ),
            markdown(
                """
                ## 1. Imports and project configuration

                Project paths and reusable validation/scoring functions are
                imported from `src/`. All output paths are repository-relative.
                """
            ),
            code(
                """
                import sys
                from pathlib import Path

                import pandas as pd

                PROJECT_ROOT = Path.cwd()
                if PROJECT_ROOT.name == "notebooks":
                    PROJECT_ROOT = PROJECT_ROOT.parent
                if str(PROJECT_ROOT) not in sys.path:
                    sys.path.insert(0, str(PROJECT_ROOT))

                from src.config import (
                    COMMERCIAL_RENT_PARISH_FILE,
                    COWORKING_LOCATIONS_FILE,
                    PARISH_ANALYSIS_BASE_FILE,
                    PARISH_INDICATORS_FILE,
                    TABLES_DIR,
                )
                from src.utils import inverse_percentile_score, validate_required_columns

                TABLES_DIR.mkdir(parents=True, exist_ok=True)
                """
            ),
            markdown(
                """
                ## 2. Load and validate processed inputs

                The processed location inventory is retained as an audit table.
                The parish indicators table is the input for the decision
                analysis and must contain exactly one row per Lisbon parish.
                """
            ),
            code(
                """
                coworking = pd.read_csv(
                    COWORKING_LOCATIONS_FILE,
                    parse_dates=["collection_date"],
                )
                parish = pd.read_csv(
                    PARISH_INDICATORS_FILE,
                    parse_dates=["collection_date"],
                )
                rent = pd.read_csv(
                    COMMERCIAL_RENT_PARISH_FILE,
                    parse_dates=["collection_date"],
                )

                required_coworking = {
                    "coworking_id",
                    "parish",
                    "active_status",
                    "verification_status",
                }
                required_parish = {
                    "parish_code",
                    "parish",
                    "area_km2",
                    "working_age_population_15_64",
                    "coworking_count",
                    "coworking_per_10000_working_age",
                    "demand_proxy_score",
                    "transit_access_score",
                    "median_rent_eur_m2_month",
                    "rent_sample_size",
                }
                validate_required_columns(coworking, required_coworking)
                validate_required_columns(parish, required_parish)

                print("Coworking audit table:", coworking.shape)
                print("Parish indicator table:", parish.shape)
                print("Rent pilot summary:", rent.shape)
                print(
                    "Verified active locations:",
                    int(
                        (
                            coworking["verification_status"]
                            == "verified_official_site"
                        ).sum()
                    ),
                )
                parish.head()
                """
            ),
            markdown(
                """
                ## 3. Select analysis fields and derive competition opportunity

                Lower coworking supply per 10,000 working-age residents receives
                a higher competition-opportunity score. This is a relative
                screening measure, not proof of unmet demand.
                """
            ),
            code(
                """
                analysis_columns = [
                    "parish_code",
                    "parish",
                    "area_km2",
                    "population_total",
                    "working_age_population_15_64",
                    "working_age_population_density_km2",
                    "coworking_count",
                    "coworking_per_10000_working_age",
                    "coworking_density_km2",
                    "office_count",
                    "office_density_km2",
                    "cafe_count",
                    "cafe_density_km2",
                    "hotel_count",
                    "hotel_density_km2",
                    "municipal_higher_education_count",
                    "municipal_higher_education_density_km2",
                    "municipal_metro_station_count",
                    "municipal_metro_station_density_km2",
                    "bus_tram_stop_count",
                    "bus_tram_stop_density_km2",
                    "demand_proxy_score",
                    "transit_access_score",
                    "median_rent_eur_m2_month",
                    "rent_sample_size",
                    "rent_coverage_flag",
                    "population_reference_year",
                    "collection_date",
                ]

                analysis = parish[analysis_columns].copy()
                analysis["competition_opportunity_score"] = inverse_percentile_score(
                    analysis["coworking_per_10000_working_age"]
                )
                usable_rent = rent[
                    rent["rent_coverage_flag"].isin(
                        ["target_met", "usable_low_coverage"]
                    )
                ][
                    [
                        "parish",
                        "median_rent_eur_m2_month",
                        "rent_sample_size",
                        "rent_coverage_flag",
                    ]
                ]
                analysis = analysis.drop(
                    columns=[
                        "median_rent_eur_m2_month",
                        "rent_sample_size",
                        "rent_coverage_flag",
                    ]
                ).merge(
                    usable_rent,
                    on="parish",
                    how="left",
                    validate="one_to_one",
                )
                analysis["rent_sample_size"] = (
                    analysis["rent_sample_size"].fillna(0).astype(int)
                )
                analysis["rent_coverage_flag"] = analysis[
                    "rent_coverage_flag"
                ].fillna("not_collected")
                analysis["analysis_status"] = "provisional_partial_rent"
                analysis = analysis.sort_values("parish").reset_index(drop=True)
                analysis.head()
                """
            ),
            markdown(
                """
                ## 4. Quality checks

                The base table must contain all 24 parishes, reconcile to 48
                verified active locations and have complete core analysis
                fields. The pilot rent medians must be available only where at
                least five distinct building observations support them.
                """
            ),
            code(
                """
                core_columns = [
                    "parish_code",
                    "parish",
                    "working_age_population_15_64",
                    "coworking_count",
                    "demand_proxy_score",
                    "transit_access_score",
                    "competition_opportunity_score",
                ]

                assert len(analysis) == 24
                assert analysis["parish"].nunique() == 24
                assert analysis["parish_code"].nunique() == 24
                assert int(analysis["coworking_count"].sum()) == 48
                assert not analysis[core_columns].isna().any().any()
                assert analysis[
                    [
                        "demand_proxy_score",
                        "transit_access_score",
                        "competition_opportunity_score",
                    ]
                ].apply(lambda column: column.between(0, 100).all()).all()
                assert analysis["median_rent_eur_m2_month"].notna().sum() == 3
                assert analysis.loc[
                    analysis["median_rent_eur_m2_month"].notna(),
                    "rent_sample_size",
                ].ge(5).all()

                quality_summary = pd.DataFrame(
                    {
                        "check": [
                            "row_count",
                            "unique_parishes",
                            "verified_coworking_total",
                            "core_missing_values",
                            "rent_values_available",
                        ],
                        "value": [
                            len(analysis),
                            analysis["parish"].nunique(),
                            int(analysis["coworking_count"].sum()),
                            int(analysis[core_columns].isna().sum().sum()),
                            int(analysis["median_rent_eur_m2_month"].notna().sum()),
                        ],
                    }
                )
                quality_summary
                """
            ),
            markdown(
                """
                ## 5. Export the base analysis table

                The CSV is the common source for EDA, provisional scoring and
                the future BI dashboard. A separate quality summary makes the
                checkpoint easy to audit.
                """
            ),
            code(
                """
                quality_path = TABLES_DIR / "parish_analysis_quality_summary.csv"
                analysis.to_csv(PARISH_ANALYSIS_BASE_FILE, index=False)
                quality_summary.to_csv(quality_path, index=False)

                print(
                    "Saved analysis table:",
                    PARISH_ANALYSIS_BASE_FILE.relative_to(PROJECT_ROOT),
                )
                print("Saved quality summary:", quality_path.relative_to(PROJECT_ROOT))
                print("Analysis table shape:", analysis.shape)
                """
            ),
            markdown(
                """
                ## 6. Cleaning outcome

                The analysis base contains 24 unique parishes and reconciles to
                48 verified active coworking locations. Demand, accessibility
                and competition components are complete. Rent is usable for
                Areeiro, Arroios and Campolide only; missing rent elsewhere is
                not treated as zero.
                """
            ),
        ]
    )


def build_eda_notebook() -> nbf.NotebookNode:
    """Create the full parish-level exploratory analysis notebook."""
    return notebook(
        [
            markdown(
                """
                # 03 Parish-level exploratory data analysis

                This notebook compares coworking supply, demand proxies and
                public-transport accessibility across all 24 Lisbon parishes.
                It exports reusable figures and BI-ready summary tables.
                """
            ),
            markdown("## 1. Imports and data loading"),
            code(
                """
                import sys
                from pathlib import Path

                import matplotlib.pyplot as plt
                import pandas as pd
                import seaborn as sns

                PROJECT_ROOT = Path.cwd()
                if PROJECT_ROOT.name == "notebooks":
                    PROJECT_ROOT = PROJECT_ROOT.parent
                if str(PROJECT_ROOT) not in sys.path:
                    sys.path.insert(0, str(PROJECT_ROOT))

                from src.config import FIGURES_DIR, PARISH_ANALYSIS_BASE_FILE, TABLES_DIR
                from src.utils import save_figure

                sns.set_theme(style="whitegrid", context="notebook")
                FIGURES_DIR.mkdir(parents=True, exist_ok=True)
                TABLES_DIR.mkdir(parents=True, exist_ok=True)

                df = pd.read_csv(
                    PARISH_ANALYSIS_BASE_FILE,
                    parse_dates=["collection_date"],
                )
                print("Analysis table shape:", df.shape)
                df.head()
                """
            ),
            markdown(
                """
                ## 2. Coverage, missingness and descriptive statistics

                Rent is the only intentionally incomplete analysis component.
                The pilot covers three priority parishes. All demand,
                accessibility and competition fields remain complete.
                """
            ),
            code(
                """
                missing = (
                    df.isna()
                    .sum()
                    .rename("missing_count")
                    .to_frame()
                    .assign(
                        missing_percent=lambda table: (
                            table["missing_count"] / len(df) * 100
                        ).round(2)
                    )
                )
                display(missing[missing["missing_count"] > 0])

                metric_columns = [
                    "working_age_population_15_64",
                    "coworking_count",
                    "coworking_per_10000_working_age",
                    "demand_proxy_score",
                    "transit_access_score",
                    "competition_opportunity_score",
                ]
                eda_summary = (
                    df[metric_columns]
                    .describe()
                    .T
                    .rename_axis("metric")
                    .reset_index()
                )
                display(eda_summary)
                """
            ),
            markdown("## 3. Coworking supply across all 24 parishes"),
            code(
                """
                supply = df.sort_values(
                    ["coworking_count", "parish"],
                    ascending=[True, True],
                )
                zero_supply = (
                    df.loc[
                        df["coworking_count"].eq(0),
                        [
                            "parish",
                            "working_age_population_15_64",
                            "demand_proxy_score",
                            "transit_access_score",
                            "competition_opportunity_score",
                        ],
                    ]
                    .sort_values("demand_proxy_score", ascending=False)
                    .reset_index(drop=True)
                )

                fig, ax = plt.subplots(figsize=(10, 9))
                sns.barplot(
                    data=supply,
                    x="coworking_count",
                    y="parish",
                    color="#2A9D8F",
                    ax=ax,
                )
                ax.set_title("Verified active coworking locations across Lisbon parishes")
                ax.set_xlabel("Number of locations")
                ax.set_ylabel("Parish")
                ax.set_xlim(left=0)
                fig.tight_layout()
                supply_path = FIGURES_DIR / "02_coworking_supply_all_parishes.png"
                save_figure(fig, supply_path)
                plt.show()

                display(zero_supply)
                """
            ),
            markdown(
                """
                ## 4. Demand versus observed competition

                The upper-right area combines stronger demand proxies with
                lower observed coworking supply per working-age resident.
                Labels highlight the strongest zero-supply candidates rather
                than every parish.
                """
            ),
            code(
                """
                fig, ax = plt.subplots(figsize=(10, 7))
                sns.scatterplot(
                    data=df,
                    x="demand_proxy_score",
                    y="competition_opportunity_score",
                    size="working_age_population_15_64",
                    hue="coworking_count",
                    palette="viridis_r",
                    sizes=(60, 450),
                    ax=ax,
                )
                label_rows = (
                    df[df["coworking_count"].eq(0)]
                    .nlargest(3, "demand_proxy_score")
                )
                label_offsets = {
                    "Areeiro": (6, 7),
                    "Penha de França": (6, -13),
                    "Misericórdia": (-82, 7),
                }
                for row in label_rows.itertuples():
                    ax.annotate(
                        row.parish,
                        (row.demand_proxy_score, row.competition_opportunity_score),
                        xytext=label_offsets.get(row.parish, (5, 5)),
                        textcoords="offset points",
                        fontsize=9,
                    )
                ax.axvline(df["demand_proxy_score"].median(), color="grey", ls="--")
                ax.axhline(
                    df["competition_opportunity_score"].median(),
                    color="grey",
                    ls="--",
                )
                ax.set_title("Demand proxy versus competition opportunity")
                ax.set_xlabel("Demand proxy score (0-100)")
                ax.set_ylabel("Competition opportunity score (0-100)")
                ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left")
                fig.tight_layout()
                demand_path = FIGURES_DIR / "03_demand_vs_competition.png"
                save_figure(fig, demand_path)
                plt.show()
                """
            ),
            markdown("## 5. Accessibility versus demand"),
            code(
                """
                fig, ax = plt.subplots(figsize=(10, 7))
                sns.scatterplot(
                    data=df,
                    x="transit_access_score",
                    y="demand_proxy_score",
                    size="coworking_count",
                    hue="competition_opportunity_score",
                    palette="mako",
                    sizes=(70, 450),
                    ax=ax,
                )
                ax.set_title("Accessibility and demand across Lisbon parishes")
                ax.set_xlabel("Transit access score (0-100)")
                ax.set_ylabel("Demand proxy score (0-100)")
                ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left")
                fig.tight_layout()
                access_path = FIGURES_DIR / "04_accessibility_vs_demand.png"
                save_figure(fig, access_path)
                plt.show()
                """
            ),
            markdown(
                """
                ## 6. Correlation structure

                With only 24 parishes, correlations are descriptive and should
                not be interpreted as causal evidence.
                """
            ),
            code(
                """
                correlation_columns = [
                    "working_age_population_density_km2",
                    "office_density_km2",
                    "cafe_density_km2",
                    "hotel_density_km2",
                    "municipal_higher_education_density_km2",
                    "municipal_metro_station_density_km2",
                    "bus_tram_stop_density_km2",
                    "coworking_density_km2",
                    "demand_proxy_score",
                    "transit_access_score",
                ]
                correlation = df[correlation_columns].corr()

                fig, ax = plt.subplots(figsize=(11, 9))
                sns.heatmap(
                    correlation,
                    cmap="vlag",
                    center=0,
                    vmin=-1,
                    vmax=1,
                    square=True,
                    linewidths=0.5,
                    ax=ax,
                )
                ax.set_title("Correlation matrix of parish-level indicators")
                fig.tight_layout()
                correlation_path = FIGURES_DIR / "05_indicator_correlation_heatmap.png"
                save_figure(fig, correlation_path)
                plt.show()
                """
            ),
            markdown("## 7. Pilot commercial asking-rent comparison"),
            code(
                """
                rent_pilot = (
                    df.loc[
                        df["median_rent_eur_m2_month"].notna(),
                        [
                            "parish",
                            "median_rent_eur_m2_month",
                            "rent_sample_size",
                            "rent_coverage_flag",
                        ],
                    ]
                    .sort_values("median_rent_eur_m2_month")
                    .reset_index(drop=True)
                )

                fig, ax = plt.subplots(figsize=(8, 5))
                sns.barplot(
                    data=rent_pilot,
                    x="median_rent_eur_m2_month",
                    y="parish",
                    color="#F4A261",
                    ax=ax,
                )
                ax.set_title("Pilot median office asking rent by parish")
                ax.set_xlabel("Median asking rent (EUR/m²/month)")
                ax.set_ylabel("Parish")
                fig.tight_layout()
                rent_path = FIGURES_DIR / "08_pilot_commercial_rent.png"
                save_figure(fig, rent_path)
                plt.show()

                display(rent_pilot)
                """
            ),
            markdown("## 8. Export EDA tables and key observations"),
            code(
                """
                eda_summary_path = TABLES_DIR / "parish_eda_summary.csv"
                zero_supply_path = TABLES_DIR / "zero_coworking_parishes.csv"
                rent_pilot_path = TABLES_DIR / "commercial_rent_pilot.csv"
                eda_summary.to_csv(eda_summary_path, index=False)
                zero_supply.to_csv(zero_supply_path, index=False)
                rent_pilot.to_csv(rent_pilot_path, index=False)

                highest_supply = df.nlargest(3, "coworking_count")[
                    ["parish", "coworking_count"]
                ]
                strongest_zero_supply = zero_supply.head(3)[
                    ["parish", "demand_proxy_score", "transit_access_score"]
                ]

                print("Parishes with the most verified coworking locations:")
                display(highest_supply)
                print("Highest-demand parishes with zero verified locations:")
                display(strongest_zero_supply)
                print("Zero-coworking parishes:", len(zero_supply))
                print("Rent coverage:", int(df["median_rent_eur_m2_month"].notna().sum()), "/ 24")
                print("Saved:", eda_summary_path.relative_to(PROJECT_ROOT))
                print("Saved:", zero_supply_path.relative_to(PROJECT_ROOT))
                print("Saved:", rent_pilot_path.relative_to(PROJECT_ROOT))
                """
            ),
            markdown(
                """
                ## 8. EDA interpretation

                The analysis reveals substantial geographic concentration:
                several parishes have no verified active coworking locations,
                while a small group contains most observed supply. Demand and
                transit signals vary independently enough to justify a
                multi-component decision model. Rent is usable for three
                priority parishes but not citywide, so the main ranking remains
                provisional.
                """
            ),
        ]
    )


def build_deeper_analysis_notebook() -> nbf.NotebookNode:
    """Create the provisional score and sensitivity-analysis notebook."""
    return notebook(
        [
            markdown(
                """
                # 04 Provisional opportunity analysis

                This notebook creates a transparent no-rent screening score
                from demand, accessibility and competition opportunity. The
                result is provisional and must be recalculated after commercial
                asking-rent data is added.
                """
            ),
            markdown("## 1. Imports, constants and data loading"),
            code(
                """
                import sys
                from pathlib import Path

                import matplotlib.pyplot as plt
                import numpy as np
                import pandas as pd
                import seaborn as sns

                PROJECT_ROOT = Path.cwd()
                if PROJECT_ROOT.name == "notebooks":
                    PROJECT_ROOT = PROJECT_ROOT.parent
                if str(PROJECT_ROOT) not in sys.path:
                    sys.path.insert(0, str(PROJECT_ROOT))

                from src.config import (
                    FINAL_WEIGHTS,
                    FIGURES_DIR,
                    PARISH_ANALYSIS_BASE_FILE,
                    PROVISIONAL_WEIGHTS,
                    RANDOM_STATE,
                    SENSITIVITY_ITERATIONS,
                    TABLES_DIR,
                )
                from src.utils import inverse_percentile_score, save_figure

                sns.set_theme(style="whitegrid", context="notebook")
                df = pd.read_csv(PARISH_ANALYSIS_BASE_FILE)

                component_columns = list(PROVISIONAL_WEIGHTS)
                assert np.isclose(sum(PROVISIONAL_WEIGHTS.values()), 1.0)
                assert not df[component_columns].isna().any().any()
                PROVISIONAL_WEIGHTS
                """
            ),
            markdown(
                """
                ## 2. Base provisional score

                The planned demand, accessibility and competition weights are
                renormalised after excluding the unavailable rent component.
                No fitted model or hidden optimisation is used.
                """
            ),
            code(
                """
                ranking = df[
                    [
                        "parish",
                        "coworking_count",
                        "working_age_population_15_64",
                        *component_columns,
                    ]
                ].copy()

                ranking["provisional_opportunity_score"] = sum(
                    ranking[column] * weight
                    for column, weight in PROVISIONAL_WEIGHTS.items()
                ).round(2)
                ranking["provisional_rank"] = (
                    ranking["provisional_opportunity_score"]
                    .rank(method="min", ascending=False)
                    .astype(int)
                )
                ranking = ranking.sort_values(
                    ["provisional_rank", "parish"]
                ).reset_index(drop=True)
                ranking.head(10)
                """
            ),
            markdown("## 3. Documented weighting scenarios"),
            code(
                """
                scenarios = {
                    "balanced_no_rent": PROVISIONAL_WEIGHTS,
                    "demand_led": {
                        "demand_proxy_score": 0.55,
                        "transit_access_score": 0.20,
                        "competition_opportunity_score": 0.25,
                    },
                    "accessibility_led": {
                        "demand_proxy_score": 0.25,
                        "transit_access_score": 0.50,
                        "competition_opportunity_score": 0.25,
                    },
                    "competition_led": {
                        "demand_proxy_score": 0.25,
                        "transit_access_score": 0.20,
                        "competition_opportunity_score": 0.55,
                    },
                }

                scenario_output = df[["parish", *component_columns]].copy()
                for scenario_name, weights in scenarios.items():
                    assert np.isclose(sum(weights.values()), 1.0)
                    score_column = f"{scenario_name}_score"
                    rank_column = f"{scenario_name}_rank"
                    scenario_output[score_column] = sum(
                        scenario_output[column] * weight
                        for column, weight in weights.items()
                    ).round(2)
                    scenario_output[rank_column] = (
                        scenario_output[score_column]
                        .rank(method="min", ascending=False)
                        .astype(int)
                    )

                scenario_output.sort_values("balanced_no_rent_rank").head(10)
                """
            ),
            markdown(
                """
                ## 4. Monte Carlo weight sensitivity

                Five thousand plausible weight combinations are drawn around
                the documented base weights with `random_state=42`. Stability
                is reported as the share of simulations in which each parish
                appears first or in the top three.
                """
            ),
            code(
                """
                rng = np.random.default_rng(RANDOM_STATE)
                base_weight_vector = np.array(
                    [PROVISIONAL_WEIGHTS[column] for column in component_columns]
                )
                sampled_weights = rng.dirichlet(
                    base_weight_vector * 40,
                    size=SENSITIVITY_ITERATIONS,
                )
                component_matrix = df[component_columns].to_numpy()
                simulation_scores = component_matrix @ sampled_weights.T

                order = np.argsort(-simulation_scores, axis=0)
                simulation_ranks = np.empty_like(order)
                simulation_ranks[order, np.arange(SENSITIVITY_ITERATIONS)] = (
                    np.arange(1, len(df) + 1)[:, None]
                )

                sensitivity = pd.DataFrame(
                    {
                        "parish": df["parish"],
                        "top1_share": (simulation_ranks == 1).mean(axis=1),
                        "top3_share": (simulation_ranks <= 3).mean(axis=1),
                        "median_rank": np.median(simulation_ranks, axis=1),
                        "best_rank": simulation_ranks.min(axis=1),
                        "worst_rank": simulation_ranks.max(axis=1),
                    }
                )
                sensitivity[["top1_share", "top3_share"]] = (
                    sensitivity[["top1_share", "top3_share"]] * 100
                ).round(2)
                sensitivity = sensitivity.sort_values(
                    ["top3_share", "top1_share"],
                    ascending=False,
                ).reset_index(drop=True)
                sensitivity.head(10)
                """
            ),
            markdown("## 5. Rent-inclusive pilot for the three covered parishes"),
            code(
                """
                rent_pilot = df[
                    df["median_rent_eur_m2_month"].notna()
                ][
                    [
                        "parish",
                        *component_columns,
                        "median_rent_eur_m2_month",
                        "rent_sample_size",
                    ]
                ].copy()
                rent_pilot["rent_opportunity_score"] = inverse_percentile_score(
                    rent_pilot["median_rent_eur_m2_month"]
                )
                rent_pilot["pilot_opportunity_score"] = sum(
                    rent_pilot[column] * weight
                    for column, weight in FINAL_WEIGHTS.items()
                ).round(2)
                rent_pilot["pilot_rank"] = (
                    rent_pilot["pilot_opportunity_score"]
                    .rank(method="min", ascending=False)
                    .astype(int)
                )
                rent_pilot = rent_pilot.sort_values(
                    ["pilot_rank", "parish"]
                ).reset_index(drop=True)

                assert len(rent_pilot) == 3
                assert rent_pilot["rent_sample_size"].ge(5).all()
                display(rent_pilot)
                """
            ),
            markdown("## 6. Export rankings and sensitivity results"),
            code(
                """
                ranking = ranking.merge(
                    sensitivity,
                    on="parish",
                    how="left",
                    validate="one_to_one",
                )
                ranking_path = TABLES_DIR / "provisional_opportunity_ranking.csv"
                scenario_path = TABLES_DIR / "provisional_opportunity_scenarios.csv"
                sensitivity_path = TABLES_DIR / "provisional_score_sensitivity.csv"
                rent_pilot_path = TABLES_DIR / "rent_inclusive_pilot_ranking.csv"

                ranking.to_csv(ranking_path, index=False)
                scenario_output.to_csv(scenario_path, index=False)
                sensitivity.to_csv(sensitivity_path, index=False)
                rent_pilot.to_csv(rent_pilot_path, index=False)

                print("Saved:", ranking_path.relative_to(PROJECT_ROOT))
                print("Saved:", scenario_path.relative_to(PROJECT_ROOT))
                print("Saved:", sensitivity_path.relative_to(PROJECT_ROOT))
                print("Saved:", rent_pilot_path.relative_to(PROJECT_ROOT))
                """
            ),
            markdown("## 7. Decision-facing figures"),
            code(
                """
                chart_data = ranking.nlargest(
                    12,
                    "provisional_opportunity_score",
                ).sort_values("provisional_opportunity_score")

                fig, ax = plt.subplots(figsize=(10, 7))
                sns.barplot(
                    data=chart_data,
                    x="provisional_opportunity_score",
                    y="parish",
                    color="#E76F51",
                    ax=ax,
                )
                ax.set_title("Provisional parish opportunity ranking (rent excluded)")
                ax.set_xlabel("Provisional opportunity score (0-100)")
                ax.set_ylabel("Parish")
                fig.tight_layout()
                ranking_figure = FIGURES_DIR / "06_provisional_opportunity_ranking.png"
                save_figure(fig, ranking_figure)
                plt.show()

                stability_data = (
                    sensitivity[sensitivity["top3_share"].gt(0)]
                    .sort_values("top3_share")
                )
                fig, ax = plt.subplots(figsize=(10, 6))
                sns.barplot(
                    data=stability_data,
                    x="top3_share",
                    y="parish",
                    color="#457B9D",
                    ax=ax,
                )
                ax.set_title(
                    "Top-three stability across provisional weight simulations"
                )
                ax.set_xlabel("Share of simulations in top three (%)")
                ax.set_ylabel("Parish")
                ax.set_xlim(0, 100)
                fig.tight_layout()
                stability_figure = FIGURES_DIR / "07_provisional_top3_stability.png"
                save_figure(fig, stability_figure)
                plt.show()
                """
            ),
            markdown("## 8. Provisional conclusion and limitation"),
            code(
                """
                display(
                    ranking.head(3)[
                        [
                            "parish",
                            "provisional_opportunity_score",
                            "provisional_rank",
                            "top3_share",
                            "median_rank",
                        ]
                    ]
                )
                print(
                    "The citywide shortlist remains provisional. A separate "
                    "rent-inclusive comparison is available for the three "
                    "parishes with sufficient pilot coverage."
                )
                """
            ),
            markdown(
                """
                The provisional shortlist is useful for directing the next
                research effort, but it is not a final expansion decision.
                Commercial asking rent must be extended to all candidate
                parishes, and site availability and local due diligence must be
                added before the final recommendation.
                """
            ),
        ]
    )


def main() -> None:
    """Write the three analysis notebooks."""
    NOTEBOOK_DIR.mkdir(parents=True, exist_ok=True)
    outputs = {
        "02_cleaning.ipynb": build_cleaning_notebook(),
        "03_eda.ipynb": build_eda_notebook(),
        "04_deeper_analysis.ipynb": build_deeper_analysis_notebook(),
    }
    for filename, generated_notebook in outputs.items():
        output_path = NOTEBOOK_DIR / filename
        nbf.write(generated_notebook, output_path)
        print(f"Wrote {output_path.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
