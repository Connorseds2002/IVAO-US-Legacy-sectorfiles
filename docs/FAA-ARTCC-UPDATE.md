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

## Point-level geometry changes made

The first ARTCC geometry pass added FAA ARB vertices that were absent from the legacy polygons while preserving the existing IVAO-specific boundary points:

- **Z​AU / Chicago:** added 5 missing high-altitude boundary vertices.
- **ZME / Memphis:** added 5 missing high-altitude boundary vertices.
- **ZMP / Minneapolis:** added 7 missing high-altitude boundary vertices.

The coordinate additions were checked against the 28-day NASR ARB/ARB_SEG data effective **14 May 2026** available in the public data mirror used for the point-level comparison. The FAA's current NASR subscription page now identifies the **03 September 2026** cycle as the current cycle, so these edits should receive a final current-cycle confirmation before merge.

The comparison also identified low-altitude-only vertices and ocean/foreign/FIR boundary records that are not yet being inserted into files whose existing structure does not distinguish those geometries. Those will be handled separately rather than mixing altitude structures or introducing unverified geometry.

## Additional geometry added

The ARTCC audit has now added explicit FAA ARB geometry overlays for high- and/or low-level boundaries where the legacy files were missing FAA records. These include boundary portions extending into Canadian/Mexican/Caribbean airspace and offshore/oceanic areas where those records are part of the FAA ARTCC boundary definition.

The affected repository files now include FAA-reference geometry for **ZAB, ZAN, ZAU, ZBW, ZDC, ZDV, ZFW, ZHU, ZID, ZJX, ZKC, ZLA, ZLC, ZMA, ZME, ZMP, ZNY, ZOA, ZOB, ZSE and ZTL**. Existing IVAO geometry has been retained; the new records are clearly marked as FAA ARB overlays rather than silently replacing the legacy polygons.

The FAA data used for these geometry additions is the publicly mirrored **14 May 2026** ARB/ARB_SEG snapshot. The FAA's published September 03, 2026 NASR page confirms that ARB remains an official current data group, but the September ARB ZIP is served as a binary download that could not be directly parsed in this environment. Therefore, the overlays are useful for the review and gap-filling pass, but should receive a final September-cycle coordinate diff before merge.

## Next sector-data pass

The remaining work is to reconcile each ARTCC's high/low boundary geometry and associated sector definitions with the current FAA NASR ARB data, while preserving the IVAO sector-file format and the repository's existing terminal/approach data.
