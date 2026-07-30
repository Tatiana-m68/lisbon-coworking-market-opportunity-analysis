"""Shared project paths and analysis constants."""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
FIGURES_DIR = PROJECT_ROOT / "reports" / "figures"
TABLES_DIR = PROJECT_ROOT / "reports" / "tables"

PARISH_INDICATORS_FILE = PROCESSED_DIR / "parish_indicators.csv"
COWORKING_LOCATIONS_FILE = PROCESSED_DIR / "coworking_locations.csv"
PARISH_ANALYSIS_BASE_FILE = PROCESSED_DIR / "parish_analysis_base.csv"
COMMERCIAL_RENT_RAW_FILE = RAW_DIR / "commercial_rent_listings_2026-07-30.json"
COMMERCIAL_RENT_LISTINGS_FILE = PROCESSED_DIR / "commercial_rent_listings.csv"
COMMERCIAL_RENT_BUILDINGS_FILE = PROCESSED_DIR / "commercial_rent_buildings.csv"
COMMERCIAL_RENT_PARISH_FILE = PROCESSED_DIR / "commercial_rent_parish_summary.csv"

RANDOM_STATE = 42
SENSITIVITY_ITERATIONS = 5_000

# The provisional model excludes rent and renormalises the planned
# demand/accessibility/competition weights to sum to one.
PROVISIONAL_WEIGHTS = {
    "demand_proxy_score": 35 / 85,
    "transit_access_score": 25 / 85,
    "competition_opportunity_score": 25 / 85,
}

FINAL_WEIGHTS = {
    "demand_proxy_score": 0.35,
    "transit_access_score": 0.25,
    "competition_opportunity_score": 0.25,
    "rent_opportunity_score": 0.15,
}
