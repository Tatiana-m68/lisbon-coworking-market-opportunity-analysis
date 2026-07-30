# Commercial Asking-Rent Collection Method

## Purpose and scope

The rent dataset is a decision-focused pilot, not a complete census of Lisbon
commercial property. It tests whether the current shortlist changes after an
asking-rent value component is added.

The 30 July 2026 collection covers searches for Areeiro, Arroios and Campolide.
These were the top three parishes in the provisional no-rent model. Citywide
ranking remains provisional until comparable coverage is extended.

## Source and acquisition

- Source: current Idealista office-rental listings.
- Method: Idealista connector search with structured `RENT` and `OFFICE`
  filters; no HTML scraping.
- Saved evidence: listing ID, source URL, collection date, asking rent, area,
  coordinates, property type and public location text.
- Excluded fields: advertiser names, telephone numbers, images and full
  descriptions because they are unnecessary for this analysis.

The raw JSON file is immutable. Processing is reproduced with:

```bash
./.venv/bin/python -m src.prepare_commercial_rent
```

## Validation and geographic assignment

Portal search areas do not always match the official civil-parish boundaries.
Each coordinate is therefore tested against the saved official Lisbon boundary
geometry. The requested search parish and the assigned official parish are
both retained, and discrepancies are flagged.

A listing is valid for analysis when:

- it falls inside an official Lisbon parish;
- monthly rent and area are positive;
- calculated asking rent is between EUR 2 and EUR 100 per m² per month.

One record with an implausible calculated unit rent is retained in the audit
table but excluded from aggregation.

## Deduplication and aggregation

Listing IDs are unique, but several units can be advertised in the same
building. Using all units directly could overweight a single property.
Coordinates rounded to four decimals define a transparent building key.
Multiple valid offers in one building are reduced to their median unit asking
rent. Parish medians are then calculated from these building observations.

Coverage flags:

- `target_met`: at least 10 buildings;
- `usable_low_coverage`: 5–9 buildings;
- `insufficient`: fewer than 5 buildings.

Only `target_met` and `usable_low_coverage` medians may enter the analysis
table. Missing rent is never converted to zero.

## Current result and limitations

The target is met for Areeiro, Arroios and Campolide. Search spillover also
produced observations for four neighbouring parishes, but their coverage is
insufficient and those medians are not used.

The values are advertised rents, not signed transaction rents. VAT,
condominium charges, incentives, fit-out condition and negotiability may differ
between listings. Listings are time-sensitive and should be refreshed before a
real investment decision.
