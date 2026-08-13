# Data Dictionary - Version 2

Latest documentation update: 30 July 2026. Fields described as proxies or
pilot samples must not be interpreted as complete business registers.

## `coworking_locations.csv`
Grain: one row per observed coworking location.

| Column | Type | Source | Description | Unit / values | Missing-value rule | Example |
|---|---|---|---|---|---|---|
| coworking_id | string | Derived | Stable deduplication identifier | Unique text | Not allowed after cleaning | cw_001 |
| coworking_name | string | OSM / verified public listing | Public business name | Text | Flag missing; do not invent | Second Home |
| operator | string | OSM / official operator site | Brand or organisation operating the location | Text | Keep null when not published | Heden |
| address | string | OSM / official operator site | Public street address | Text | Keep null and flag for verification | Rua Maria 10, Lisboa |
| latitude | float | OSM / verified listing | WGS84 latitude | Decimal degrees | Exclude from spatial analysis until resolved | 38.727 |
| longitude | float | OSM / verified listing | WGS84 longitude | Decimal degrees | Exclude from spatial analysis until resolved | -9.146 |
| parish | category | Spatial join | Official Lisbon parish | One of 24 parishes | Not allowed in analysis-ready table | Misericórdia |
| active_status | category | Manual validation | Status on collection date | active / uncertain / closed | Use uncertain when evidence conflicts | active |
| source_type | category | Collection log | Discovery/evidence channel | OpenStreetMap / official operator website / combined | Not allowed | OpenStreetMap |
| source_url | string | Source record | Primary auditable public source | URL | Not allowed for observed record | https://... |
| secondary_source_url | string | Source record | Independent corroborating source or duplicate OSM reference | URL(s) | Keep null until available | https://... |
| website | string | Public listing | Current public website associated with the location | URL | Keep null and flag | https://... |
| website_domain | string | Derived | Normalised website domain | Text | Null when website is missing | heden.co |
| collection_date | date | Collection log | Observation date | YYYY-MM-DD | Not allowed | 2026-07-22 |
| verification_status | category | Verification workflow | Evidence-review state | pending / verified_official_site | Not allowed | verified_official_site |
| matched_rule | string | Derived | Discovery rule that selected the record | Text | Not allowed | office=coworking |
| osm_type | category | OSM | OSM element type | node / way / relation | Null for web-only record | node |
| osm_id | integer | OSM | Source OSM element identifier | Integer | Null for web-only record | 4720152466 |
| duplicate_group | string | QA | Candidate duplicate cluster | Text | Null when no candidate duplicate remains | near_name_match_001 |
| review_note | string | Verification workflow | Short auditable caveat or decision note | Text | Optional | Official site checked |
| raw_tags | string | OSM | Original OSM tags serialised as JSON | JSON text | Null for web-only record | {"office":"coworking"} |

## `parish_indicators.csv`
Grain: one row per Lisbon civil parish.

| Column | Type | Source | Description | Unit / values | Missing-value rule | Example |
|---|---|---|---|---|---|---|
| parish | category | Lisboa Aberta | Official parish name | 24 parishes | Not allowed | Avenidas Novas |
| area_km2 | float | Boundary geometry | Parish area | km² | Not allowed | 2.99 |
| working_age_population_15_64 | integer | INE Census 2021 | Residents aged 15-64; the official synthesis bands do not isolate ages 20-24 | persons | Not allowed | 14200 |
| coworking_count | integer | Aggregated locations table | Verified active locations | count | Zero only after confirmed coverage | 14 |
| pending_coworking_count | integer | Aggregated locations table | Candidate locations still awaiting verification | count | Not allowed | 4 |
| office_count | integer | OSM rule set | Mapped office POIs, excluding coworking | count | Zero only after successful query | 620 |
| cafe_count | integer | OSM rule set | Café POIs | count | Zero only after successful query | 185 |
| hotel_count | integer | OSM rule set | Hotel POIs | count | Zero only after successful query | 54 |
| municipal_higher_education_count | integer | Lisboa Aberta | Active higher-education locations | count | Not allowed | 3 |
| municipal_metro_station_count | integer | Lisboa Aberta | Existing metro station points | count | Not allowed | 4 |
| municipal_hotel_2015_count | integer | Lisboa Aberta | Historical hotel count used only as a coverage reference | count | Not allowed; never treat as current | 12 |
| transit_access_score | float | Lisboa Aberta + OSM | 60% official metro-station density rank + 40% OSM bus/tram-stop density rank | 0-100 | Not allowed after successful collection | 72.4 |
| median_rent_eur_m2_month | float | Dated listing sample | Median commercial asking rent | EUR/m²/month | Keep null; flag fewer than 5 listings | 28.50 |
| demand_proxy_score | float | Calculated | 40% working-age density, 30% OSM office density and 10% each OSM café, OSM hotel and official higher-education density ranks | 0-100 | Calculate only under documented rule | 78.1 |
| opportunity_score | float | Calculated | Final screening score | 0-100 | Calculate only with documented scenario | 84.3 |

## Data-quality rules
- Preserve raw files unchanged and resolve duplicates only in processed data.
- Keep a documented matching/deduplication rule and a review flag for uncertain records.
- Record all conversions, recoding and derived variables in the cleaning notebook.
- Missing does not mean zero. Use zero only when the collection method confirms absence.
- Record coverage gaps, source limitations and the latest update date.

## `parish_analysis_base.csv`

Grain: one row per Lisbon civil parish. This 24-row table is generated by
`notebooks/02_cleaning.ipynb` from `parish_indicators.csv`.

It retains the documented population, supply, POI, education, transit and rent
fields used in the analysis and adds:

| Column | Type | Source | Description | Unit / values | Missing-value rule | Example |
|---|---|---|---|---|---|---|
| competition_opportunity_score | float | Derived | Inverse percentile score of coworking locations per 10,000 working-age residents | 0-100 | Not allowed after successful build | 100.0 |
| analysis_status | category | Derived | States whether all planned model components are available | provisional_no_rent | Not allowed | provisional_no_rent |

The current dated, terms-compliant sample populates rent fields for the
provisional top-ten candidates. Rent remains missing for the other parishes and
must not be converted to zero.

## Commercial rent tables

`commercial_rent_listings.csv` has one row per collected listing and retains
the listing ID, source URL, collection date, requested search parish, official
spatially assigned parish, asking rent, area, calculated unit rent, coordinates,
building key, QA flags and verification note.

`commercial_rent_buildings.csv` has one row per rounded coordinate/building.
It uses the median of multiple offers in the same building so repeated units or
broker variants do not dominate the parish result.

`commercial_rent_parish_summary.csv` has one row per observed parish:

| Column | Type | Description |
|---|---|---|
| parish | category | Official parish assigned from coordinates |
| rent_sample_size | integer | Number of distinct building observations |
| valid_listing_count | integer | Valid listing records before building aggregation |
| median_rent_eur_m2_month | float | Median building-level asking rent |
| min_rent_eur_m2_month | float | Minimum building-level asking rent |
| max_rent_eur_m2_month | float | Maximum building-level asking rent |
| collection_date | date | Latest observation date in the sample |
| rent_coverage_flag | category | target_met / usable_low_coverage / insufficient |

## Provisional analysis outputs

`reports/tables/provisional_opportunity_ranking.csv` contains the balanced
no-rent score, rank and sensitivity results.

`reports/tables/provisional_opportunity_scenarios.csv` contains scores and
ranks under four documented weight scenarios.

`reports/tables/provisional_score_sensitivity.csv` contains top-one/top-three
shares and rank ranges from 5,000 reproducible weight simulations.

These outputs are screening results, not a final site recommendation.

## Recommendation outputs

- `rent_inclusive_pilot_ranking.csv`: four-component ranking of the ten covered
  candidates.
- `rent_inclusive_shortlist_sensitivity.csv`: 5,000-run four-component weight
  stability results.
- `final_shortlist.csv`: close three-area shortlist of Areeiro, Arroios and
  Lumiar after the 13 August 2026 competitor audit; score order is retained for
  transparency but is not treated as a final business ranking.
- `recommendation_evidence.csv`: strengths, trade-offs and next due-diligence
  actions for the three recommended parishes.
