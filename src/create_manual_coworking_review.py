"""Create a simple, restart-safe CSV for the user's manual coworking checks."""

from __future__ import annotations

import csv
from pathlib import Path

from config import PROCESSED_DIR


OUTPUT_COLUMNS = [
    "coworking_id",
    "current_name",
    "current_address",
    "current_website",
    "source_url",
    "found_name",
    "found_address",
    "found_website",
    "instagram_url",
    "user_status",
    "user_comment",
    "assistant_review_status",
]
USER_COLUMNS = [
    "found_name",
    "found_address",
    "found_website",
    "instagram_url",
    "user_status",
    "user_comment",
]


def read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    source_path = PROCESSED_DIR / "coworking_verification_queue.csv"
    output_path = PROCESSED_DIR / "coworking_manual_review.csv"

    previous_by_id = {
        row["coworking_id"]: row
        for row in read_rows(output_path)
        if row.get("coworking_id")
    }
    pending = [
        row
        for row in read_rows(source_path)
        if row.get("verification_status") == "pending"
    ]

    output_rows: list[dict[str, str]] = []
    for row in pending:
        coworking_id = row["coworking_id"]
        previous = previous_by_id.get(coworking_id, {})
        output = {
            "coworking_id": coworking_id,
            "current_name": row.get("coworking_name", ""),
            "current_address": row.get("address", ""),
            "current_website": row.get("website", ""),
            "source_url": row.get("source_url", ""),
            "assistant_review_status": previous.get(
                "assistant_review_status", ""
            ),
        }
        for column in USER_COLUMNS:
            output[column] = previous.get(column, "")
        output_rows.append(output)

    with output_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(output_rows)

    print(f"Saved {len(output_rows)} pending rows to {output_path}")


if __name__ == "__main__":
    main()
