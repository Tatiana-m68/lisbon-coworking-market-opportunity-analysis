# Lisbon Coworking Market Opportunity Analysis

## Overview
This project helps an Expansion Director narrow the search for one new coworking location from Lisbon municipality's 24 civil parishes to three areas for closer local analysis. It compares demand proxies, public-transport accessibility, observed coworking competition and commercial asking-rent value using public, legally accessible data.

## Problem statement
A coworking company plans to open one new Lisbon location but lacks a consistent evidence base for narrowing its search. A poor search area could combine weak demand, strong competition, poor accessibility or unsustainable occupancy costs. The analysis identifies three parishes where the company can compare real property offers and local business conditions in parallel.

## Project goal
Build a transparent and reproducible parish-level comparison and recommend a three-parish shortlist for further due diligence by August 2026.

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
commercial asking-rent coverage limited to the provisional top-ten candidates.

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

## Deliverables
- A cleaned, documented coworking-location dataset and a 24-row parish indicators table.
- Reproducible collection, cleaning and EDA notebooks with reusable Python functions in `src/`.
- Decision-facing visualisations and a transparent Opportunity Score with sensitivity analysis.
- A clear three-area shortlist supported by final decision-facing charts; a BI dashboard remains a final presentation deliverable.

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
   including the ten-candidate rent sample.
4. `04_deeper_analysis.ipynb` - creates a provisional citywide score,
   documented scenarios, reproducible sensitivity results and a separate
   rent-inclusive comparison of the ten covered candidates.
5. `05_insights_recommendations.ipynb` - tests four-component weight
   sensitivity and documents a close three-parish shortlist with
   due-diligence actions.
6. `06_final_charts.ipynb` - exports the final decision-facing ranking and
   rent/score trade-off charts.

`01_data_collection.ipynb` documents the saved source snapshots, validates the
current competitor inventory and records the offline rebuild order.
See [`docs/methodology.md`](docs/methodology.md) for scoring assumptions and
interpretation limits.

## Success criteria
- At least 90% coverage of coworking locations found across two independent public discovery sources.
- At least 95% completeness for parish, coordinates, active status and source URL.
- All 24 Lisbon parishes represented, including zero-count parishes.
- Target at least 10 valid rent listings per parish; flag any parish with fewer than five.
- A three-area shortlist supported by evidence, trade-offs and next steps.
- Each shortlisted parish remains in the top three in at least 70% of documented weighting scenarios.
- A non-technical stakeholder can understand the decision and rationale in five minutes or less.

## Key findings
The frozen initial MVP contains 48 locations. A targeted competitor audit on
13 August 2026 expanded the current verified-active inventory to 67 locations
with complete coordinates and official-parish assignments. Only Olivais has no
verified active location under the current method; this means "none found",
not proven absence.

The provisional no-rent model is an intermediate screen used to select ten
candidates for rent analysis. The expanded rent sample contains 191 unique listings, reduced to
148 building observations; the minimum usable coverage is met for all ten
provisional top-ten candidates.
In the rent-inclusive shortlist, the candidate order is recalculated using the
planned demand, accessibility, competition and affordability weights.
The three highest scores are separated by only 1.35 points. Across 5,000
four-component weight simulations, Areeiro, Lumiar and Arroios each remain in
the top three in more than 77% of runs. The screening recommendation is
therefore a close three-area shortlist rather than a strict internal ranking.
It is not a final
lease or investment decision because citywide rent coverage, available sites
and local due diligence are still incomplete.

## Business recommendations

### 1. Study the lower-cost Lumiar case

**Situation:** Lumiar combines good transit access (67.50), one verified
competitor and the strongest rent opportunity among the final three.
**Complication:** Its demand score (43.33) is relatively weak and the area has
a more residential profile. **Resolution:** Study daytime worker and student
demand around Lumiar and Quinta das Conchas metro stations over two weeks, and
use the findings when comparing suitable commercial spaces.
Evidence:
`reports/figures/09_recommendation_component_profiles.png` and
`reports/tables/recommendation_evidence.csv`.

### 2. Test whether Arroios has an underserved segment

**Situation:** Arroios has the strongest demand (94.17) and transit (95.00)
signals among the final three, with a pilot median rent of EUR 17.50/m²/month.
**Complication:** Eight verified active locations create substantial
competition. **Resolution:** Map competitor capacity, prices and customer
segments over two weeks, then use any clear market gap when comparing real
property offers across the shortlist.
Evidence:
`reports/figures/10_rent_inclusive_shortlist.png` and
`reports/tables/final_shortlist.csv`.

### 3. Compare live sites in balanced Areeiro

**Situation:** Areeiro combines strong demand (85.42), good transit (73.33),
two verified competitors and a pilot median rent of EUR 17.73/m²/month.
**Complication:** It is neither the cheapest nor the lowest-competition option.
**Resolution:** Run a four-week search for suitable commercial spaces near
Areeiro, Alameda and Roma-Areeiro, and compare real offers, lease terms and
competitor positioning with the other shortlisted areas. Evidence:
`reports/figures/11_score_vs_asking_rent.png` and
`reports/tables/recommendation_evidence.csv`.

## BI dashboard and final figures
If Tableau or Power BI is used, working files will be stored in `reports/bi_exports/`. Final shareable charts and dashboard exports will be stored in `reports/figures/`. Relative data paths will point to `data/processed/`.

## Current status
The repository structure and core documentation are complete. The project now
has linked processed tables, raw source snapshots, reproducible collection
scripts and automated quality reports. The parish table covers all 24
freguesias and uses official census, higher-education and metro data alongside
documented OSM proxies. Manual coworking candidate verification is complete.
The initial EDA runs reproducibly and exports its frozen MVP chart and
parish-level coworking summary table directly from the notebook.
The cleaning, parish-level EDA and provisional deeper-analysis notebooks are
now implemented and run from top to bottom. They generate a 24-row base
analysis table, ten additional figures, recommendation tables and two
reproducible 5,000-run weight sensitivity analyses. A terms-compliant
commercial asking-rent sample is now integrated for the provisional top-ten
candidates.
The collection-orchestration, recommendation and final chart notebooks are
implemented, and a clean local clone reproduces notebooks 01-06. Remaining
work is the required one-page BI dashboard. The separate 8-slide presentation is
maintained outside this public repository.

## Known blockers and risks
- Public directories and map data can omit new locations or retain outdated ones.
- Asking-rent coverage is sufficient for the top-ten candidates but may not represent all available properties.
- The Opportunity Score can create false precision unless weights and data coverage are tested transparently.

## Next steps
1. Build the required one-page Tableau/Power BI dashboard from the exported CSV files.
2. Complete the final handoff after the dashboard is ready.
