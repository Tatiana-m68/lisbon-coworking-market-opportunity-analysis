# Parish Indicators Collection Method

## Current status

The dataset has one row for each of Lisbon municipality's 24 civil parishes.
Official boundaries and INE Census 2021 population fields are complete.

The source hierarchy is:

1. Official municipal or INE data when a current, suitable field exists.
2. A saved OpenStreetMap/Overpass snapshot for reproducible POI proxies.
3. Historical municipal data only as an explicitly labelled validation
   reference.

## Counts and scores

`coworking_count` includes only rows supported by the documented active-location
verification rules. The current audit contains 67 verified active locations
and no pending candidates. Public discovery sources can still omit locations,
so a zero means "none found under the current method", not proven absence.

`transit_access_score` is a 0-100 screening index: 60% percentile rank of
official metro-station density and 40% percentile rank of mapped OSM bus/tram
stop density.

`demand_proxy_score` is a 0-100 screening index: 40% working-age population
density, 30% mapped office density, and 10% each mapped café density, mapped
hotel density, and official higher-education density. It is not a forecast.

## Remaining limitations

- OSM coverage varies by tag and parish, so office, café, hotel and bus/tram
  counts are comparable exploratory proxies, not complete registers.
- Commercial asking-rent coverage is available for the ten screening
  candidates, but it is not a complete citywide market register.
- The base `parish_indicators.csv` keeps `opportunity_score` blank by design.
  Reproducible scores are generated in the analysis notebooks and exported to
  `reports/tables/`.
- The verified coworking inventory can change as public business information
  changes or newly discovered locations pass the documented review rules.
