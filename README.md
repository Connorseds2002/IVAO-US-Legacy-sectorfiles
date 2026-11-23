# IVAO US legacy sector files

Sector files for IVAO's **Aurora** ATC client covering the United States ARTCCs, the
US oceanic and offshore FIRs, and combined-ARTCC profiles. The navigation data is kept
up to date with the FAA's 28-day NASR (AIRAC) cycle.

**Current AIRAC:** see [`AIRAC.txt`](AIRAC.txt).

## Download and install

Get the zips from the [latest release](../../releases/latest):

| Zip | Contents |
|---|---|
| `US-ALL.zip` | Every profile and the whole `Include` folder |
| `<FACILITY>.zip` (e.g. `KZNY.zip`) | One profile's `.isc` and its `Include/US/<facility>` folder |
| `KZMA_KZJX.zip`, `KZLA_KZOA.zip` | The combined profiles (see below) |

Unzip into Aurora's `SectorFiles` folder. The zips keep the repo layout: the `.isc` sits
at the top and its data lands in `Include/US/...`. Then open the `.isc` profile in Aurora.

## Profiles

| Profile | Facility |
|---|---|
| `KZAB.isc` | Albuquerque ARTCC |
| `KZAU.isc` | Chicago ARTCC |
| `KZBW.isc` | Boston ARTCC |
| `KZDC.isc` | Washington ARTCC |
| `KZDV.isc` | Denver ARTCC |
| `KZFW.isc` | Fort Worth ARTCC |
| `KZHU.isc` | Houston ARTCC |
| `KZID.isc` | Indianapolis ARTCC |
| `KZJX.isc` | Jacksonville ARTCC |
| `KZKC.isc` | Kansas City ARTCC |
| `KZLA Los Angeles ARTCC.isc` | Los Angeles ARTCC |
| `KZLC.isc` | Salt Lake ARTCC |
| `KZMA.isc` | Miami ARTCC |
| `KZME.isc` | Memphis ARTCC |
| `KZMP.isc` | Minneapolis ARTCC |
| `KZNY.isc` | New York ARTCC |
| `KZOA.isc` | Oakland ARTCC |
| `KZOB.isc` | Cleveland ARTCC |
| `KZSE.isc` | Seattle ARTCC |
| `KZTL.isc` | Atlanta ARTCC |
| `KZAK Oakland Oceanic FIR.isc` | Oakland Oceanic FIR |
| `KZWY New York Oceanic FIR.isc` | New York Oceanic FIR, including Bermuda (TXKF) |
| `PAZA.isc` | Anchorage ARTCC |
| `PHZH.isc` | Honolulu Control Facility |
| `PGZU.isc` | Guam CERAP |
| `TJZS.isc` | San Juan CERAP |
| `OCC North Atlantic.isc` | North Atlantic oceanic (Gander/Shanwick and neighbours) |
| `KZMA_KZJX Miami-Jacksonville combined.isc` | Miami + Jacksonville combined |
| `KZLA_KZOA Los Angeles-Oakland combined.isc` | Los Angeles + Oakland combined |

Note: `OCC North Atlantic.isc` points to `Include/CA/CZQX`, which isn't in this repo. It
needs the Canadian sector files installed alongside.

## Combined ARTCC profiles

The combined profiles let one controller cover two neighbouring centres in a single
Aurora session. Each loads both ARTCCs' boundaries, airports, runways, fixes, navaids,
airways, video maps, procedures and ATC positions, and opens centred between the two
centres. The single-ARTCC profiles are unchanged.

Their include folders (`Include/US/kzma_kzjx`, `Include/US/kzla_kzoa`) are generated
from the single-ARTCC folders by `.github/scripts/build_combos.py`, so they always carry
the current AIRAC data. They aren't stored in the repo:

- The release zips already include them.
- If you use the repo directly, run `python3 .github/scripts/build_combos.py` after each pull.

Inside a combined folder, each ARTCC's data keeps its own subfolder (`kzma/`, `kzjx/`...),
so files with the same name never overwrite each other. Files that are identical in both
ARTCCs are loaded once. Where both ARTCCs have a different file for the same airport, the
owning ARTCC's version is used; this is set in the `owners` map in the script.

To change what a combined profile loads, edit the single-ARTCC `.isc` files or the
`COMBOS` list in the script, not the generated combined `.isc`. To add a new
combination, add an entry to `COMBOS`.

## Repository layout

```
<FACILITY>.isc            Aurora profile: map centre, colours, and which files to load
AIRAC.txt                 AIRAC cycle the releases are labelled with
Include/US/<facility>/
  airac/                  FAA navigation data: airports.ap, runways.rw, fixes.fix,
                          vor.vor, ndb.ndb, awhigh.awh, awlow.awl
  airspace/  (ARTCC/)     ARTCC boundaries (.artcc), Class B/C/D airspace, fill areas (.fcl)
  geo/  (GEO/)            coastlines, restricted/warning/prohibited areas, MOAs
  app/                    approach/TRACON video maps
  ad/                     aerodrome diagrams and centrelines
  atc.atc                 ATC positions and frequencies
  default.atis            ATIS template
  <airport>.sid / .str    SIDs and STARs
  <airport>.tfl / .txi    taxiway fills and taxiway labels
  <airport>.gts           gates and stands
  <airport>.mva           minimum vectoring altitudes
  <airport>.vfi / .vrt    VFR reporting points and routes
docs/                     notes on FAA data reviews
.changeset/               change notes
.github/                  release workflow and build scripts
```

Not every facility has every folder; a few use `ARTCC/` or `GEO/` instead of
`airspace/` or `geo/`. File paths in the `.isc` files are Windows-style and not
case-sensitive in Aurora.

## AIRAC updates

The FAA publishes new NASR data every 28 days (e.g. 2612 effective 26 Nov 2026, 2613
on 24 Dec 2026). A weekly automated check looks for a new cycle and, when one is out,
opens a pull request named **AIRAC YYNN – FAA data update** on a branch `airac-YYNN`.

Each update PR:
- applies the FAA changes to fixes, navaids, airports, runways and, where listed,
  airways and ARTCC boundaries, in the existing file formats
- puts new items under a `// FAA NASR AIRAC YYNN additions` block in the owning
  facility's file
- flags things that need a human decision (deleted fixes still used in procedures,
  deleted or new airports) instead of changing them automatically
- updates `AIRAC.txt` to the new cycle

Corrections the FAA publishes for the same cycle are pushed to that PR. Nothing is
merged automatically: review the PR and merge it when you're happy.

ARTCC boundary geometry is compared against the FAA NASR ARTCC Boundary (ARB) data;
see [`docs/FAA-ARTCC-UPDATE.md`](docs/FAA-ARTCC-UPDATE.md) for the method and status.

New York Oceanic (`kzwy`) is updated the same way. FAA data covers its fixes, its
oceanic routes in `airac/awhigh.awh` and the ZWY boundary (drawn as the `KZWY FAA FIR`
and `KZWY FAA CTA` overlays in `airspace/kzwy.artcc`). In `awhigh.awh`, points inside
ZWY are written by fix name and points outside it as coordinates with a `//NAME`
comment, and each segment has a label at its midpoint (`R1-R2` where routes share
a segment). Bermuda's own data (TXKF procedures, TMA, taxiways) isn't FAA data and is
kept by hand.

## Releases

Merging a change to `Include/`, an `.isc` file or `AIRAC.txt` into `main` publishes a
GitHub release automatically (`.github/workflows/release.yml`). Changes to only the
README, docs or workflow don't. You can also run the release by hand from the
**Actions** tab.

Releases are named from `AIRAC.txt`:

| Release | Title | Tag |
|---|---|---|
| First in a cycle | AIRAC 2612 – US sector files (date) | `airac-2612` |
| Second in the same cycle | AIRAC 2612 – US sector files (date) v2 | `airac-2612-v2` |
| Third | … v3 | `airac-2612-v3` |
| First after `AIRAC.txt` changes to 2613 | AIRAC 2613 – US sector files (date) | `airac-2613` |

The label only ever comes from `AIRAC.txt`, so change it whenever the data moves to a
new cycle (the AIRAC update PRs do this for you).

To build the zips locally:

```
python3 .github/scripts/build_release.py dist
```

This generates the combined profiles, then writes one zip per profile, `US-ALL.zip`
and `release_notes.md` to `dist/`.

## Contributing

- Make changes on a branch and open a pull request into `main`.
- Keep each file's existing format: semicolon-separated values, with coordinates
  written the way the file already writes them (mostly `N033.52.30.000` /
  `W106.49.56.000`, some files use decimal degrees).
- Don't edit the generated combined profiles or their folders.
