# Coworking Location Collection Method

## Current scope

The first dataset covers physical coworking-location candidates inside the
municipality of Lisbon. The collection date is 24 July 2026. This is a
candidate inventory rather than a claim that every row is currently active.
Rows may be used as confirmed active locations only when
`verification_status` equals `verified_official_site`.

## Discovery channels

1. OpenStreetMap / Overpass candidates:
   - `office=coworking`
   - `amenity=coworking_space`
   - `office=coworking_space`
   - English and European Portuguese name keywords
2. Current official operator websites in Portuguese or English.
3. Official Lisbon parish polygons from Câmara Municipal de Lisboa.

Searches included Portuguese wording such as `espaço de coworking`,
`escritório partilhado`, `espaço de trabalho partilhado`, `morada`, and
`localização`, as well as English equivalents.

## Inclusion rule

Include a candidate when public evidence describes a physical Lisbon location
that provides shared or flexible workspace to people from more than one
organisation. Team-only flexible workspaces are retained but described in
`review_note`. Virtual-only offices, ordinary single-company offices, meeting
rooms without a workspace offer, and locations outside Lisbon municipality are
excluded.

## Reproducible workflow

1. `src/collect_coworking_osm.py` saves immutable, dated OSM and municipal
   boundary snapshots.
2. `src/geocode_manual_candidates.py` geocodes the small, one-time address list
   sequentially and caches every response.
3. `src/build_coworking_locations.py` parses OSM objects, assigns official
   parishes, joins independent official-site evidence, and creates the
   processed table and verification queue.
4. `src/qa_coworking_locations.py` validates structure, IDs, coordinates,
   statuses, parish names, and missingness.

## Status meanings

- `active` + `verified_official_site`: the operator's current official site
  explicitly presents the physical location and a coworking/flexible-workspace
  service.
- `uncertain` + `pending`: discovered in OSM but an independent current source
  has not yet been reviewed.
- `closed`: retained for audit history only when closure is supported.

Missing does not mean zero, and `uncertain` does not mean inactive.

## Known limitations

- OSM coverage and tagging are incomplete and may be stale.
- Official operator sites are stronger evidence of current operation but do not
  prove occupancy, capacity, prices, or commercial performance.
- Three official-site records still require coordinates.
- Same-name OSM objects at the same street address are consolidated while all
  contributing OSM URLs are retained.
- Ten of Lisbon's 24 parishes currently have no discovered candidate; this
  cannot yet be interpreted as confirmed zero supply.
- Further independent discovery and verification are required before market
  share or competitor-density conclusions are drawn.
