# Source Plan

| Source | Expected data | Access | Main limitation |
|---|---|---|---|
| Lisboa Aberta | Parish boundaries; municipal mobility/base data | Download or documented API | Availability and update frequency |
| INE Census 2021 | Population by parish and age group | Official download/API | Decennial snapshot |
| OpenStreetMap / Overpass | Coworking, amenities, selected transport POIs | Saved queries and raw JSON | Incomplete or inconsistent tagging |
| Public coworking websites/listings | Name, address, active status | Manual validation with URL/date | Time-sensitive; avoid personal data |
| Commercial property listings | Asking rent, area, location, date | Small manual sample only if permitted | Asking rent differs from transaction rent |

## Implemented parish sources (25 July 2026)
- Official Lisbon boundaries cover all 24 civil parishes.
- INE Census 2021 provides population and the exact available 15-64
  working-age aggregation.
- Lisboa Aberta point datasets provide 51 active higher-education locations
  and 50 metro-station records for official cross-checking and scoring.
- The municipal hotel dataset contains 148 records dated 2015 and is retained
  only as a historical coverage reference. Current hotel counts use OSM and
  remain a proxy.
- The saved OSM/Overpass snapshot supplies office, café, hotel and bus/tram
  POI proxies. A successful query confirms retrieval, not exhaustive tagging.

## Collection controls
Save raw files unchanged; record URL, date, query/filter and licence/terms note; document inclusion, exclusion, spatial join and deduplication rules; do not collect unnecessary personal data.

## Coworking-location collection started

Collection began on 24 July 2026. The first pass combines a saved Overpass
query with European Portuguese and English discovery terms, official operator
websites, and the Câmara Municipal de Lisboa parish-boundary service. See
`coworking_collection_method.md` for the operational definitions, status rules,
and current limitations.
