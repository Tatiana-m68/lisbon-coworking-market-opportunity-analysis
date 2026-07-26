"""Apply the 25 July 2026 evidence review and rebuild the short manual queue."""

from __future__ import annotations

import csv
from pathlib import Path

from config import PROCESSED_DIR


DECISIONS = {
    "osm_node_11880069089": {
        "active_status": "uncertain",
        "verification_status": "excluded_non_target_workspace",
        "review_note": "User verified this is a small cake-making workshop venue, not a general laptop coworking space; excluded 2026-07-25.",
    },
    "osm_way_96854133": {
        "coworking_name": "Regus — Lisbon Dom João V",
        "address": "Rua Dom João V 30, Amoreiras Palace, 1250-091 Lisboa",
        "website": "https://www.regus.com/pt/pt/6613",
        "active_status": "active",
        "verification_status": "verified_official_site",
        "review_note": "OSM coordinates match the official Regus Dom João V center; Regus offers coworking and day access despite Google category 'office rental agency'; reviewed 2026-07-25.",
    },
    "osm_node_11898720626": {
        "active_status": "closed",
        "verification_status": "verified_moved_outside_scope",
        "website": "https://www.inoffice.pt/",
        "review_note": "Old Alameda dos Oceanos location no longer found; current operator address supplied by user is in Foros de Amora, Seixal, outside Lisbon municipality; excluded 2026-07-25.",
    },
    "osm_node_11869392777": {
        "active_status": "uncertain",
        "verification_status": "excluded_false_positive",
        "secondary_source_url": "https://www.altishotels.com/altis-grand-hotel/",
        "review_note": "Espaço Castilho is a building name beside Altis Grand Hotel. Hotel lists meeting rooms but no public coworking desk/day-pass product; excluded 2026-07-25.",
    },
    "osm_node_10015362767": {
        "coworking_name": "Regus — Lisbon Avenida da Liberdade",
        "address": "Avenida da Liberdade 110, 1269-046 Lisboa",
        "website": "https://www.regus.com/pt/pt/21",
        "active_status": "active",
        "verification_status": "verified_official_site",
        "review_note": "OSM coordinates match the official Regus Avenida da Liberdade 110 center; Regus offers coworking and day access despite Google category 'office rental agency'; reviewed 2026-07-25.",
    },
    "osm_node_10011209150": {
        "coworking_name": "Scape Workspaces",
        "address": "Doca de Santo Amaro, Armazém 15, 1350-353 Lisboa",
        "website": "https://scapeworkspaces.pt",
        "active_status": "active",
        "verification_status": "verified_official_site",
        "secondary_source_url": "https://www.linkedin.com/company/scapeworkspaces",
        "review_note": "Official domain and current business profile corroborate coworking service and address; reviewed 2026-07-25.",
    },
    "osm_node_12709912384": {
        "coworking_name": "AIhub by Unicorn Factory Lisboa",
        "address": "Rua João Saraiva 38, Lisboa",
        "website": "https://aihub.unicornfactorylisboa.com/",
        "active_status": "active",
        "verification_status": "verified_official_site",
        "secondary_source_url": "https://unicornfactorylisboa.com/hubs/",
        "review_note": "Official Unicorn Factory AIhub page lists 30 coworking seats and this address; reviewed 2026-07-25.",
    },
    "osm_way_1420058911": {
        "coworking_name": "Plaçes Cowork",
        "address": "Rua Flores de Lima 16, 1700-196 Lisboa",
        "website": "https://www.placeswork.pt/pt/",
        "active_status": "active",
        "verification_status": "verified_official_site",
        "review_note": "Official site lists the Lisbon workspace and address; reviewed 2026-07-25.",
    },
    "osm_node_13917926242": {
        "coworking_name": "Cowork Rizoma",
        "address": "Rua José Estêvão 4B, 1150-202 Lisboa",
        "website": "https://www.rizomacoop.pt/en/sections/services-section/cowork/",
        "active_status": "active",
        "verification_status": "verified_official_site",
        "review_note": "Official cooperative cowork page and current contact page match the address; reviewed 2026-07-25.",
    },
    "osm_node_4720152466": {
        "coworking_name": "DEVAZUKA",
        "address": "Rua do Benformoso 227, 1100-085 Lisboa",
        "website": "https://devazuka.com/",
        "active_status": "closed",
        "verification_status": "verified_closed_official_site",
        "review_note": "Official site explicitly says 'Permanently Closed'; reviewed 2026-07-25.",
    },
    "osm_node_13529352806": {
        "coworking_name": "Espaço Arroios",
        "address": "Rua Passos Manuel 99A, 1150-260 Lisboa",
        "website": "https://www.instagram.com/espaco_arroios/",
        "active_status": "active",
        "verification_status": "verified_official_site",
        "review_note": "User confirmed recent official social activity; address corroborated; reviewed 2026-07-25.",
    },
    "osm_way_99628864": {
        "coworking_name": "IDEA Spaces Saldanha",
        "address": "Avenida Defensores de Chaves 4, 1000-117 Lisboa",
        "website": "https://ideaspaces.pt/saldanha.html",
        "active_status": "active",
        "verification_status": "verified_official_site",
        "review_note": "Official location page lists coworking, current contact details and address; reviewed 2026-07-25.",
    },
    "osm_node_12709903316": {
        "coworking_name": "Gaming Hub by Unicorn Factory Lisboa",
        "address": "Avenida da República 18, 4.º andar, Lisboa",
        "website": "https://gaminghub.unicornfactorylisboa.com/",
        "active_status": "active",
        "verification_status": "verified_official_site",
        "review_note": "Official Gaming Hub page lists coworking products, prices and address; reviewed 2026-07-25.",
    },
    "osm_node_11665827947": {
        "coworking_name": "The Block Lisboa",
        "address": "Rua Latino Coelho 63, 1.º andar, 1050-133 Lisboa",
        "website": "https://www.theblocklisboa.com/",
        "active_status": "active",
        "verification_status": "verified_official_site",
        "review_note": "Official site offers flex memberships and private offices; recent 2026 events corroborate activity.",
    },
    "osm_node_12323330753": {
        "coworking_name": "NOW Beato",
        "address": "Rua da Manutenção 67, 1900-319 Lisboa",
        "active_status": "closed",
        "verification_status": "verified_closed_manual_review",
        "review_note": "User found the operation closed; no current operator page or recent activity located on 2026-07-25.",
    },
    "osm_node_11886704394": {
        "coworking_name": "Sincera Coworking",
        "address": "Rua de Pedrouços 59A/59B, 1400-285 Lisboa",
        "website": "https://www.sinceracoworking.com/",
        "active_status": "active",
        "verification_status": "verified_official_site",
        "review_note": "Official site lists coworking desks, prices, contact details and Restelo address; reviewed 2026-07-25.",
    },
    "osm_node_11880069091": {
        "coworking_name": "FORJA Cowork + Studio",
        "address": "Rua das Pedralvas 5A, 1500-487 Lisboa",
        "website": "https://www.forja.pt/",
        "active_status": "active",
        "verification_status": "verified_official_site",
        "review_note": "Official site states open, publishes cowork services, hours and address; reviewed 2026-07-25.",
    },
    "osm_node_10321568413": {
        "coworking_name": "Resvés Cowork",
        "address": "Rua Saraiva de Carvalho 1C, 1250-240 Lisboa",
        "website": "https://resvescowork.pt/",
        "active_status": "active",
        "verification_status": "verified_official_site",
        "review_note": "Official site publishes current desk plans, trial booking and address; reviewed 2026-07-25.",
    },
    "osm_way_155614383": {
        "coworking_name": "LACS Conde d'Óbidos",
        "address": "Rocha do Conde de Óbidos, 1350-352 Lisboa",
        "website": "https://www.lacs.pt/",
        "active_status": "active",
        "verification_status": "verified_official_site",
        "review_note": "Current operator presence and June 2026 reviews/events corroborate active coworking; reviewed 2026-07-25.",
    },
    "osm_node_13468469969": {
        "coworking_name": "Santander Work Café Santos",
        "address": "Avenida Dom Carlos I 49, Lisboa",
        "website": "https://www.santander.pt/work-cafe",
        "active_status": "active",
        "verification_status": "verified_official_site",
        "review_note": "Official Santander page lists this current Work Café and coworking service; reviewed 2026-07-25.",
    },
    "osm_way_155614371": {
        "active_status": "closed",
        "verification_status": "excluded_duplicate",
        "review_note": "Unnamed adjacent building footprint duplicates the named LACS Conde d'Óbidos record; excluded 2026-07-25.",
    },
    "osm_node_12526350974": {
        "coworking_name": "WorkHub Prata",
        "address": "Rua Fernando Palha 29B, 1950-130 Lisboa",
        "website": "https://workhub.pt/en/contacto/",
        "active_status": "active",
        "verification_status": "verified_official_site",
        "review_note": "Official WorkHub contact page lists the Prata location at this address; reviewed 2026-07-25.",
    },
    "osm_node_6385072016": {
        "coworking_name": "Impact Hub Lisbon — Baixa Chiado",
        "address": "Travessa das Pedras Negras 1, 1.º, 1100-404 Lisboa",
        "website": "https://lisbon.impacthub.net/",
        "active_status": "active",
        "verification_status": "verified_official_site",
        "review_note": "Official current site lists coworking and corrected Baixa Chiado address; reviewed 2026-07-25.",
    },
    "osm_node_5069382167": {
        "coworking_name": "Santander Work Café Amoreiras",
        "address": "Avenida Engenheiro Duarte Pacheco 21-B, Lisboa",
        "website": "https://www.santander.pt/work-cafe",
        "active_status": "active",
        "verification_status": "verified_official_site",
        "review_note": "Official Santander page lists this current Work Café and coworking service; reviewed 2026-07-25.",
    },
    "osm_way_98057563": {
        "coworking_name": "The Base Lisbon",
        "address": "Travessa do Fala-Só 13B, Lisboa",
        "website": "https://baselisbon.com/",
        "active_status": "active",
        "verification_status": "verified_official_site",
        "review_note": "Official site publishes current hot-desk pricing, hours and address; reviewed 2026-07-25.",
    },
    "osm_node_11892515134": {
        "coworking_name": "WeWork — Rua Alexandre Herculano 50",
        "address": "Rua Alexandre Herculano 50, 1250-096 Lisboa",
        "website": "https://www.wework.com/pt-PT/buildings/50-r-alexandre-herculano--lisbon",
        "active_status": "active",
        "verification_status": "verified_official_site",
        "review_note": "Official location page lists coworking, current hours and address; reviewed 2026-07-25.",
    },
    "osm_node_5904542939": {
        "coworking_name": "Heden Graça",
        "address": "Travessa da Pereira 35A, 1170-312 Lisboa",
        "website": "https://heden.co/",
        "active_status": "active",
        "verification_status": "verified_official_site",
        "review_note": "Current operator profile lists this location and recent activity; reviewed 2026-07-25.",
    },
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    locations_path = PROCESSED_DIR / "coworking_locations.csv"
    queue_path = PROCESSED_DIR / "coworking_verification_queue.csv"
    manual_path = PROCESSED_DIR / "coworking_manual_review.csv"

    locations = read_csv(locations_path)
    location_fields = list(locations[0])
    for row in locations:
        decision = DECISIONS.get(row["coworking_id"])
        if decision:
            row.update(decision)
            if decision.get("website"):
                row["website_domain"] = (
                    decision["website"]
                    .split("//", 1)[-1]
                    .split("/", 1)[0]
                    .removeprefix("www.")
                )
    write_csv(locations_path, locations, location_fields)

    queue_fields = [
        "coworking_id", "coworking_name", "operator", "address", "parish",
        "matched_rule", "source_url", "website", "active_status",
        "verification_status", "duplicate_group", "review_note",
    ]
    write_csv(
        queue_path,
        [{field: row.get(field, "") for field in queue_fields} for row in locations],
        queue_fields,
    )

    previous = {row["coworking_id"]: row for row in read_csv(manual_path)}
    unresolved = [
        row for row in locations if row["verification_status"] == "pending"
    ]
    manual_fields = list(next(iter(previous.values())))
    manual_rows = []
    for row in unresolved:
        old = previous.get(row["coworking_id"], {})
        manual_rows.append(
            {
                "coworking_id": row["coworking_id"],
                "current_name": row["coworking_name"],
                "current_address": row["address"],
                "current_website": row["website"],
                "source_url": row["source_url"],
                "found_name": old.get("found_name", ""),
                "found_address": old.get("found_address", ""),
                "found_website": old.get("found_website", ""),
                "instagram_url": old.get("instagram_url", ""),
                "user_status": old.get("user_status", ""),
                "user_comment": old.get("user_comment", ""),
                "assistant_review_status": (
                    "Needs a current official page, recent social activity, "
                    "or recent Google review tied to this exact address."
                ),
            }
        )
    write_csv(manual_path, manual_rows, manual_fields)
    print(
        f"Applied {len(DECISIONS)} decisions; "
        f"{len(unresolved)} rows remain for manual review."
    )


if __name__ == "__main__":
    main()
