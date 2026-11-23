# IVAO US legacy sector files

Aurora sector files for the US ARTCCs and FIRs. Each `.isc` at the repo root is
one profile; its data lives in `Include/US/<facility>/`.

## Combined ARTCC profiles

Two combined profiles let one controller cover neighbouring centres in a single
Aurora session:

| Profile | Covers |
|---|---|
| `KZMA_KZJX Miami-Jacksonville combined.isc` | Miami + Jacksonville |
| `KZLA_KZOA Los Angeles-Oakland combined.isc` | Los Angeles + Oakland |

Each loads both ARTCCs' boundaries, airports, fixes, navaids, airways, video maps,
procedures and ATC positions, and opens centred between the two centres. The
single-ARTCC profiles are unchanged.

The combined include folders (`Include/US/kzma_kzjx`, `Include/US/kzla_kzoa`) are
built from the single-ARTCC folders by `.github/scripts/build_combos.py`, so they
always carry the current AIRAC data. They are not stored in the repo:

- **Release zips** (`KZMA_KZJX.zip`, `KZLA_KZOA.zip`, `US-ALL.zip`) already include them.
- **Using the repo directly?** Run `python3 .github/scripts/build_combos.py` after
  each pull.

To change what a combined profile loads, edit the single-ARTCC `.isc` files or the
`COMBOS` list in the script, not the generated combined `.isc`.
