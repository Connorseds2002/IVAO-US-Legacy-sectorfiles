# FAA ARTCC alignment update

**Review date:** 2026-09-30

This PR tracks the alignment of the legacy US sector files with current FAA ARTCC information.

## FAA reference data

The FAA currently lists 21 domestic Air Route Traffic Control Centers (ARTCCs):

| Designator | FAA facility name |
|---|---|
| ZAB | Albuquerque |
| ZAU | Chicago |
| ZBW | Boston |
| ZDC | Washington, Leesburg |
| ZDV | Denver |
| ZFW | Ft Worth |
| ZHU | Houston |
| ZID | Indianapolis |
| ZJX | Jacksonville |
| ZKC | Kansas City |
| ZLA | Los Angeles |
| ZLC | Salt Lake |
| ZMA | Miami |
| ZME | Memphis |
| ZMP | Minneapolis |
| ZNY | New York |
| ZOA | Oakland |
| ZOB | Cleveland |
| ZSE | Seattle |
| ZTL | Atlanta |
| ZAN | Anchorage |

FAA also lists Honolulu Control Facility (HCF), San Juan (ZSU), Guam (ZUA), and Joshua TRACON (JCF) as Combined Control Facilities rather than domestic ARTCCs.

## Boundary-data note

The FAA publishes 28-day ARTCC boundary data through NASR and separate ERAM ground-level ARTCC boundary data. The FAA explicitly states that ERAM ground-level boundaries are intended for matching off-airport points to a controlling ARTCC and may not match the low-level ARTCC boundaries shown on FAA charts.

For this reason, the sector-file geometry must be compared against the FAA NASR ARTCC Boundary Description (ARB/ARB_SEG) high- and low-altitude records rather than replacing the IVAO geometry with the ERAM surface dataset alone.

Current FAA ERAM reference available during this review:
- Current edition: 03 September 2026
- Next edition: 01 October 2026

## Changes already made in this PR

- Corrected the misspelled **Denver Center** label in the Kansas City sector data.
- Corrected the misspelled **Edmonton Center** label in the Salt Lake City sector data.
- Added this tracking document so the FAA source, scope, and validation method are explicit before geometry changes are committed.

## Next sector-data pass

The remaining work is to reconcile each ARTCC's high/low boundary geometry and associated sector definitions with the current FAA NASR ARB data, while preserving the IVAO sector-file format and the repository's existing terminal/approach data.
