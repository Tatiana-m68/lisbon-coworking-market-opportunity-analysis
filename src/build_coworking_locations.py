"""Build a review-ready coworking-location table from immutable raw snapshots."""

from __future__ import annotations

import argparse
import json
import math
import re
import unicodedata
from datetime import date
from difflib import SequenceMatcher
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd

from config import PROCESSED_DIR, RAW_DIR


PARISH_NAME_FIELDS = (
    "NOME",
    "NOME_FREG",
    "FREGUESIA",
    "DESIGNACAO",
    "name",
)


def normalize_text(value: object) -> str:
    """Normalize text for conservative candidate matching."""
    if value is None:
        return ""
    text = unicodedata.normalize("NFKD", str(value))
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = re.sub(r"[^a-zA-Z0-9]+", " ", text.lower())
    return " ".join(text.split())


def first_nonempty(tags: dict, keys: tuple[str, ...]) -> str | None:
    for key in keys:
        value = tags.get(key)
        if value not in (None, ""):
            return str(value).strip()
    return None


def build_address(tags: dict) -> str | None:
    full = first_nonempty(tags, ("addr:full",))
    if full:
        return full
    street = first_nonempty(tags, ("addr:street",))
    number = first_nonempty(tags, ("addr:housenumber",))
    postcode = first_nonempty(tags, ("addr:postcode",))
    city = first_nonempty(tags, ("addr:city",))
    parts = [
        " ".join(item for item in (street, number) if item),
        postcode,
        city,
    ]
    address = ", ".join(item for item in parts if item)
    return address or None


def matched_rule(tags: dict) -> str:
    rules: list[str] = []
    if tags.get("office") == "coworking":
        rules.append("office=coworking")
    if tags.get("amenity") == "coworking_space":
        rules.append("amenity=coworking_space")
    if tags.get("office") == "coworking_space":
        rules.append("office=coworking_space")
    name = normalize_text(tags.get("name"))
    if any(term in name for term in ("cowork", "co work")):
        rules.append("name_keyword_cowork")
    if (
        "escritorio partilhado" in name
        or "espaco de trabalho partilhado" in name
    ):
        rules.append("name_keyword_pt")
    return "|".join(rules) or "unclassified"


def get_coordinates(element: dict) -> tuple[float | None, float | None]:
    lat = element.get("lat")
    lon = element.get("lon")
    if lat is None or lon is None:
        center = element.get("center", {})
        lat = center.get("lat")
        lon = center.get("lon")
    return lat, lon


def osm_rows(payload: dict, collection_date: str) -> list[dict]:
    rows: list[dict] = []
    for element in payload["elements"]:
        tags = element.get("tags", {})
        lat, lon = get_coordinates(element)
        osm_type = element["type"]
        osm_id = element["id"]
        website = first_nonempty(
            tags,
            ("contact:website", "website", "url"),
        )
        rows.append(
            {
                "coworking_id": f"osm_{osm_type}_{osm_id}",
                "coworking_name": first_nonempty(
                    tags,
                    ("name", "brand", "operator"),
                ),
                "operator": first_nonempty(tags, ("operator", "brand")),
                "address": build_address(tags),
                "latitude": lat,
                "longitude": lon,
                "parish": None,
                "active_status": "uncertain",
                "source_type": "OpenStreetMap",
                "source_url": (
                    f"https://www.openstreetmap.org/{osm_type}/{osm_id}"
                ),
                "secondary_source_url": None,
                "website": website,
                "website_domain": (
                    urlparse(website).netloc.lower().removeprefix("www.")
                    if website
                    else None
                ),
                "collection_date": collection_date,
                "verification_status": "pending",
                "matched_rule": matched_rule(tags),
                "osm_type": osm_type,
                "osm_id": osm_id,
                "duplicate_group": None,
                "review_note": None,
                "raw_tags": json.dumps(tags, ensure_ascii=False, sort_keys=True),
            }
        )
    return rows


def find_parish_name_field(properties: dict) -> str:
    for field in PARISH_NAME_FIELDS:
        if field in properties:
            return field
    string_fields = [field for field, value in properties.items() if isinstance(value, str)]
    if len(string_fields) == 1:
        return string_fields[0]
    raise KeyError(
        "Could not identify parish-name field. "
        f"Available fields: {list(properties)}"
    )


def point_in_ring(lon: float, lat: float, ring: list[list[float]]) -> bool:
    """Return True when a point is inside a linear ring (ray casting)."""
    inside = False
    previous = ring[-1]
    for current in ring:
        x1, y1 = previous[:2]
        x2, y2 = current[:2]
        crosses_latitude = (y1 > lat) != (y2 > lat)
        if crosses_latitude:
            crossing_lon = (x2 - x1) * (lat - y1) / (y2 - y1) + x1
            if lon < crossing_lon:
                inside = not inside
        previous = current
    return inside


def point_in_polygon(lon: float, lat: float, coordinates: list) -> bool:
    """Respect a polygon's exterior ring and any interior holes."""
    if not coordinates or not point_in_ring(lon, lat, coordinates[0]):
        return False
    return not any(point_in_ring(lon, lat, hole) for hole in coordinates[1:])


def geometry_contains_point(geometry: dict, lon: float, lat: float) -> bool:
    geometry_type = geometry.get("type")
    coordinates = geometry.get("coordinates", [])
    if geometry_type == "Polygon":
        return point_in_polygon(lon, lat, coordinates)
    if geometry_type == "MultiPolygon":
        return any(point_in_polygon(lon, lat, polygon) for polygon in coordinates)
    return False


def assign_parishes(
    dataframe: pd.DataFrame,
    parish_path: Path,
) -> pd.DataFrame:
    parish_geojson = json.loads(parish_path.read_text(encoding="utf-8"))
    features = parish_geojson["features"]
    parish_field = find_parish_name_field(features[0]["properties"])

    for index, row in dataframe.iterrows():
        lat = row["latitude"]
        lon = row["longitude"]
        if pd.isna(lat) or pd.isna(lon):
            continue
        for feature in features:
            if geometry_contains_point(feature["geometry"], lon, lat):
                dataframe.at[index, "parish"] = feature["properties"][parish_field]
                break
    return dataframe


def flag_duplicate_candidates(dataframe: pd.DataFrame) -> pd.DataFrame:
    dataframe["_normalized_name"] = dataframe["coworking_name"].map(normalize_text)
    group_number = 1
    grouped_indexes: set[int] = set()
    for left_index in dataframe.index:
        left = dataframe.loc[left_index]
        if not left["_normalized_name"] or pd.isna(left["latitude"]):
            continue
        matches = [left_index]
        for right_index in dataframe.index:
            if right_index <= left_index:
                continue
            right = dataframe.loc[right_index]
            if (
                left["_normalized_name"] == right["_normalized_name"]
                and not pd.isna(right["latitude"])
                and haversine_metres(
                    left["latitude"],
                    left["longitude"],
                    right["latitude"],
                    right["longitude"],
                )
                <= 150
            ):
                matches.append(right_index)
        if len(matches) > 1 and not set(matches).issubset(grouped_indexes):
            dataframe.loc[matches, "duplicate_group"] = (
                f"near_name_match_{group_number:03d}"
            )
            grouped_indexes.update(matches)
            group_number += 1
    return dataframe.drop(columns="_normalized_name")


def deduplicate_same_name_and_address(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Consolidate duplicate OSM objects representing one named street address."""
    output = dataframe.copy()
    output["_normalized_name"] = output["coworking_name"].map(normalize_text)
    output["_normalized_address"] = output["address"].map(normalize_text)
    drop_indexes: list[int] = []
    grouped = output.groupby(
        ["_normalized_name", "_normalized_address"],
        dropna=False,
    )
    for (name, address), indexes in grouped.groups.items():
        indexes = list(indexes)
        if not name or not address or len(indexes) < 2:
            continue
        keeper = indexes[0]
        duplicate_urls = output.loc[indexes[1:], "source_url"].dropna().tolist()
        if duplicate_urls:
            output.at[keeper, "secondary_source_url"] = "; ".join(duplicate_urls)
        output.at[keeper, "review_note"] = (
            f"Consolidated {len(indexes)} same-name OSM objects at one address."
        )
        drop_indexes.extend(indexes[1:])
    return output.drop(index=drop_indexes).drop(
        columns=["_normalized_name", "_normalized_address"]
    )


def haversine_metres(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> float:
    radius = 6_371_000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1)
        * math.cos(phi2)
        * math.sin(delta_lambda / 2) ** 2
    )
    return 2 * radius * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def related_names(manual: pd.Series, osm: pd.Series) -> bool:
    manual_terms = {
        normalize_text(manual.get("coworking_name")),
        normalize_text(manual.get("operator")),
    } - {""}
    osm_terms = {
        normalize_text(osm.get("coworking_name")),
        normalize_text(osm.get("operator")),
    } - {""}
    for manual_term in manual_terms:
        for osm_term in osm_terms:
            if manual_term in osm_term or osm_term in manual_term:
                return True
            if SequenceMatcher(None, manual_term, osm_term).ratio() >= 0.65:
                return True
    return False


def manual_rows(
    discovery_path: Path,
    geocoding_path: Path,
    collection_date: str,
) -> list[dict]:
    discovery = pd.read_csv(discovery_path)
    geocoding = json.loads(geocoding_path.read_text(encoding="utf-8"))
    geocodes = {item["row_number"]: item["result"] for item in geocoding}
    rows: list[dict] = []
    for index, item in discovery.iterrows():
        geocode = geocodes.get(index)
        website = item["source_url"]
        rows.append(
            {
                "coworking_id": f"web_{index + 1:03d}",
                "coworking_name": item["coworking_name"],
                "operator": item["operator"],
                "address": item["address"],
                "latitude": float(geocode["lat"]) if geocode else None,
                "longitude": float(geocode["lon"]) if geocode else None,
                "parish": None,
                "active_status": "active",
                "source_type": item["source_type"],
                "source_url": website,
                "secondary_source_url": None,
                "website": website,
                "website_domain": urlparse(website).netloc.lower().removeprefix("www."),
                "collection_date": collection_date,
                "verification_status": "verified_official_site",
                "matched_rule": "official_site_discovery",
                "osm_type": None,
                "osm_id": None,
                "duplicate_group": None,
                "review_note": (
                    item["discovery_note"]
                    if geocode
                    else f"{item['discovery_note']} Coordinates still required."
                ),
                "raw_tags": None,
            }
        )
    return rows


def merge_manual_with_osm(
    osm_dataframe: pd.DataFrame,
    manual_dataframe: pd.DataFrame,
) -> pd.DataFrame:
    output = osm_dataframe.copy()
    for _, manual in manual_dataframe.iterrows():
        match_index: int | None = None
        match_distance = float("inf")
        if not pd.isna(manual["latitude"]):
            for osm_index, osm in output.iterrows():
                if (
                    pd.isna(osm["latitude"])
                    or osm["source_type"] != "OpenStreetMap"
                    or not related_names(manual, osm)
                ):
                    continue
                distance = haversine_metres(
                    manual["latitude"],
                    manual["longitude"],
                    osm["latitude"],
                    osm["longitude"],
                )
                if distance <= 250 and distance < match_distance:
                    match_index = osm_index
                    match_distance = distance
        if match_index is None:
            output = pd.concat(
                [output, manual.to_frame().T],
                ignore_index=True,
            )
            continue

        output.at[match_index, "secondary_source_url"] = manual["source_url"]
        output.at[match_index, "website"] = manual["website"]
        output.at[match_index, "website_domain"] = manual["website_domain"]
        output.at[match_index, "active_status"] = "active"
        output.at[match_index, "verification_status"] = "verified_official_site"
        output.at[match_index, "source_type"] = (
            "OpenStreetMap + official operator website"
        )
        output.at[match_index, "review_note"] = (
            f"Matched to official-site record within {match_distance:.0f} m."
        )
        if normalize_text(output.at[match_index, "coworking_name"]) in {
            "spaces",
            "regus",
            "",
        }:
            output.at[match_index, "coworking_name"] = manual["coworking_name"]
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--collection-date",
        default=date.today().isoformat(),
        help="Raw snapshot date in YYYY-MM-DD format.",
    )
    args = parser.parse_args()
    collection_date = date.fromisoformat(args.collection_date).isoformat()

    osm_path = RAW_DIR / f"osm_coworking_{collection_date}.json"
    parish_path = RAW_DIR / f"lisbon_parishes_{collection_date}.geojson"
    discovery_path = RAW_DIR / f"manual_discovery_{collection_date}.csv"
    geocoding_path = RAW_DIR / f"nominatim_geocoding_{collection_date}.json"
    output_path = PROCESSED_DIR / "coworking_locations.csv"
    review_path = PROCESSED_DIR / "coworking_verification_queue.csv"

    payload = json.loads(osm_path.read_text(encoding="utf-8"))
    dataframe = pd.DataFrame(osm_rows(payload, collection_date))
    dataframe = assign_parishes(dataframe, parish_path)
    dataframe = dataframe[dataframe["parish"].notna()].copy()
    dataframe = deduplicate_same_name_and_address(dataframe)
    if discovery_path.exists() and geocoding_path.exists():
        manual_dataframe = pd.DataFrame(
            manual_rows(discovery_path, geocoding_path, collection_date)
        )
        dataframe = merge_manual_with_osm(dataframe, manual_dataframe)
        dataframe = assign_parishes(dataframe, parish_path)
    dataframe = flag_duplicate_candidates(dataframe)

    dataframe["review_note"] = dataframe["review_note"].astype("object")
    dataframe.loc[
        dataframe["coworking_name"].isna(),
        "review_note",
    ] = "Missing public name"
    dataframe.loc[
        dataframe["website"].isna() & dataframe["review_note"].isna(),
        "review_note",
    ] = "No website in OSM; find an independent public source"

    dataframe = dataframe.sort_values(
        ["parish", "coworking_name", "osm_type", "osm_id"],
        na_position="last",
    ).reset_index(drop=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    dataframe.to_csv(output_path, index=False)

    review_columns = [
        "coworking_id",
        "coworking_name",
        "operator",
        "address",
        "parish",
        "matched_rule",
        "source_url",
        "website",
        "active_status",
        "verification_status",
        "duplicate_group",
        "review_note",
    ]
    dataframe[review_columns].to_csv(review_path, index=False)

    print(f"Saved {len(dataframe)} Lisbon candidates to {output_path}")
    print(f"Saved verification queue to {review_path}")
    print(f"Parishes represented: {dataframe['parish'].nunique()}")
    print(f"Missing names: {dataframe['coworking_name'].isna().sum()}")
    print(f"Missing websites: {dataframe['website'].isna().sum()}")
    print(f"Potential duplicate rows: {dataframe['duplicate_group'].notna().sum()}")


if __name__ == "__main__":
    main()
