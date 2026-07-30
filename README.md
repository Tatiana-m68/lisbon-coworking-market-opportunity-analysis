# Lisbon Coworking Market Opportunity Analysis

## Overview
This project supports an Expansion Director deciding which of Lisbon municipality's 24 civil parishes should advance to site-level due diligence for one new coworking location. It compares demand proxies, public-transport accessibility, observed coworking competition and commercial asking-rent value using public, legally accessible data.

## Problem statement
A coworking company plans to open one new Lisbon location but lacks a consistent evidence base for selecting the parish in which to begin site-level due diligence. A poor choice could combine weak demand, strong competition, poor accessibility or unsustainable occupancy costs.

## Project goal
Build a transparent and reproducible parish-level comparison and recommend one priority parish plus two alternatives for further due diligence by August 2026.

## Dataset
The project uses two linked analysis tables:
- `coworking_locations.csv`: one row per observed coworking location.
- `parish_indicators.csv`: one row per Lisbon civil parish.

The initial EDA dataset is
`data/raw/coworking_locations_mvp_2026-07-25.csv`. It contains 48 rows and 10
columns: identifier, name, coordinates, parish, activity status, source URL,
collection date, source type and verification status. It is a frozen subset of
locations confirmed as active from official operator pages.

Sources include documented OpenStreetMap/Overpass queries, current official
operator websites, official Lisbon parish boundaries, Lisboa Aberta and INE
Census 2021. See [`docs/data_dictionary.md`](docs/data_dictionary.md),
[`docs/source_plan.md`](docs/source_plan.md), and
[`docs/coworking_collection_method.md`](docs/coworking_collection_method.md).
The commercial asking-rent pilot is documented in
[`docs/commercial_rent_collection_method.md`](docs/commercial_rent_collection_method.md).

The project scope is Lisbon municipality's 24 civil parishes. Coworking-location
collection started on 24 July 2026. The current candidate inventory combines
OpenStreetMap/Overpass, current official operator websites, and official Lisbon
parish boundaries. Every source snapshot and collection date is retained. See
[`docs/coworking_collection_method.md`](docs/coworking_collection_method.md).
Known limitations are possible omissions from public discovery sources and
commercial asking-rent coverage limited to three priority parishes.

## Target audience
The primary user is an Expansion Director or market-development manager at a
coworking operator. Secondary users include commercial real-estate analysts and
local economic-development teams that need a transparent parish-level view of
Lisbon's coworking supply and market signals.

## Key analysis questions
- Which Lisbon parishes have relatively strong demand and accessibility but limited verified coworking supply?
- How concentrated is confirmed active coworking competition across the 24 parishes?
- Which parishes offer the strongest balance between demand proxies, transport access and commercial asking-rent value?
- How sensitive is the shortlist to alternative weights in the Opportunity Score?
- Which data gaps or local risks require site-level due diligence before an expansion decision?

## Planned deliverables
- A cleaned, documented coworking-location dataset and a 24-row parish indicators table.
- Reproducible collection, cleaning and EDA notebooks with reusable Python functions in `src/`.
- Decision-facing visualisations and a transparent Opportunity Score with sensitivity analysis.
- A concise report or dashboard recommending one priority parish and two alternatives.

## Setup
Use Python 3.11 or 3.12 with the pinned project dependencies. Newer Python
versions may require newer scientific-library releases than those recorded for
this project environment.

Clone the repository from GitHub using the URL available under the repository's
**Code** button. Then open a terminal in the cloned project folder and run:

```bash
cd coworking_lisbon_analysis
python -m venv .venv
source .venv/bin/activate  # Mac/Linux
# .venv\Scripts\activate   # Windows
pip install -r requirements.txt
jupyter lab
```

## Project structure
```text
coworking_lisbon_analysis/
├── data/
│   ├── raw/             # immutable source snapshots
│   ├── processed/       # cleaned, analysis-ready files
│   └── external/        # third-party reference data
├── notebooks/           # numbered execution sequence
├── src/                 # reusable functions, paths and constants
├── reports/
│   ├── figures/         # final numbered PNG/PDF/SVG exports
│   ├── tables/          # notebook-generated summary CSV exports
│   └── bi_exports/      # Tableau/Power BI working files, if used
├── docs/
│   ├── project_brief.md
│   ├── source_plan.md
│   ├── data_dictionary.md
│   └── methodology.md
├── requirements.txt     # pinned Python dependencies
├── TASK_LIST.md
└── README.md
```

## How to run
To reproduce the initial checkpoint, open `notebooks/01_eda.ipynb` and run all
cells from top to bottom. This run generates
`reports/figures/01_coworking_locations_by_parish.png` and
`reports/tables/coworking_locations_by_parish.csv`.

The implemented parish-analysis sequence is:

1. `./.venv/bin/python -m src.prepare_commercial_rent` - validates the raw rent
   pilot and creates listing-, building- and parish-level processed tables.
2. `02_cleaning.ipynb` - validates processed inputs and creates
   `data/processed/parish_analysis_base.csv`.
3. `03_eda.ipynb` - compares all 24 parishes and exports EDA figures/tables,
   including the three-parish rent pilot.
4. `04_deeper_analysis.ipynb` - creates a provisional citywide score,
   documented scenarios, reproducible sensitivity results and a separate
   rent-inclusive comparison of the three covered parishes.

The workflow will later be completed with `01_data_collection.ipynb`,
`05_insights_recommendations.ipynb`, and `06_final_charts.ipynb`.
See [`docs/methodology.md`](docs/methodology.md) for scoring assumptions and
interpretation limits.

## Success criteria
- At least 90% coverage of coworking locations found across two independent public discovery sources.
- At least 95% completeness for parish, coordinates, active status and source URL.
- All 24 Lisbon parishes represented, including zero-count parishes.
- Target at least 10 valid rent listings per parish; flag any parish with fewer than five.
- One priority parish and two alternatives supported by 3-5 evidence points, trade-offs and next steps.
- Recommended parish remains in the top three in at least 70% of documented weighting scenarios.
- A non-technical stakeholder can understand the decision and rationale in five minutes or less.

## Key findings
The verified-active MVP contains 48 coworking locations with complete
coordinates and parish assignments. Ten of Lisbon's 24 parishes have no
verified active coworking location in the current dataset. Santo António,
Arroios and Santa Maria Maior together contain 22 of the 48 verified locations.

The provisional citywide model ranks Areeiro first, followed by Campolide and
Arroios. Areeiro appears in the top three in 100% of the documented weight
simulations. The rent pilot contains 60 listings, reduced to 41 building
observations; the 10-building target is met for all three priority parishes.
Their median asking rents are EUR 17.50–20.01 per m² per month. In the
rent-inclusive pilot, Areeiro remains first, followed by Arroios and Campolide.
This is not the final recommendation because citywide rent coverage, available
sites and local due diligence are still incomplete.

## BI dashboard and final figures
If Tableau or Power BI is used, working files will be stored in `reports/bi_exports/`. Final shareable charts and dashboard exports will be stored in `reports/figures/`. Relative data paths will point to `data/processed/`.

## Current status
The repository structure and core documentation are complete. The project now
has linked processed tables, raw source snapshots, reproducible collection
scripts and automated quality reports. The parish table covers all 24
freguesias and uses official census, higher-education and metro data alongside
documented OSM proxies. Manual coworking candidate verification is complete.
The initial EDA runs reproducibly and exports its chart and 14-row
parish-level coworking summary table directly from the notebook.
The cleaning, parish-level EDA and provisional deeper-analysis notebooks are
now implemented and run from top to bottom. They generate a 24-row base
analysis table, seven additional figures, eight additional summary/scenario
tables and a 5,000-run weight sensitivity analysis. A terms-compliant
commercial asking-rent pilot is now integrated for the current top-three
parishes.
The final rent-inclusive opportunity score and recommendation remain deferred
until comparable rent coverage is extended to the remaining serious
candidates.

## Known blockers and risks
- Public directories and map data can omit new locations or retain outdated ones.
- Asking-rent coverage is sufficient for only three priority parishes and may not represent all available properties.
- The Opportunity Score can create false precision unless weights and data coverage are tested transparently.

## Next steps
1. Extend the same commercial-rent method to the remaining serious candidate parishes.
2. Add the final recommendation notebook with evidence, trade-offs and due-diligence actions.
3. Create the final decision-facing charts or dashboard and run the full reproducibility audit.
