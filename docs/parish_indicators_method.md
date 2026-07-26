# Parish Indicators Collection Method

## Status on 25 July 2026

The dataset has one row for each of Lisbon municipality's 24 civil parishes.
Official boundaries and INE Census 2021 population fields are complete.

The source hierarchy is:

1. Official municipal or INE data when a current, suitable field exists.
2. A saved OpenStreetMap/Overpass snapshot for reproducible POI proxies.
3. Historical municipal data only as an explicitly labelled validation
   reference.

## Counts and scores

`coworking_count` includes only rows confirmed active through an official
operator website. Pending candidates are kept in a separate count and do not
enter the confirmed competition measure.

`transit_access_score` is a 0-100 screening index: 60% percentile rank of
official metro-station density and 40% percentile rank of mapped OSM bus/tram
stop density.

`demand_proxy_score` is a 0-100 screening index: 40% working-age population
density, 30% mapped office density, and 10% each mapped café density, mapped
hotel density, and official higher-education density. It is not a forecast.

## Remaining limitations

- OSM coverage varies by tag and parish, so office, café, hotel and bus/tram
  counts are comparable exploratory proxies, not complete registers.
- Commercial asking-rent observations have not yet been collected.
- The final `opportunity_score` remains blank until rent coverage and the
  scoring scenario are documented.
- The confirmed coworking measure will change if pending candidates pass
  manual verification.
