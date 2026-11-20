#!/usr/bin/env python3
"""Build release zips: one per ARTCC/FIR .isc file plus a full US package.

Each per-facility zip holds the facility's .isc file and the Include/US/<facility>/
folder it points to (the "US\\XXXX" line in the .isc [INFO] block), keeping the
repo's folder layout so it can be unzipped straight into Aurora's SectorFiles folder.
The full zip holds every .isc file and the whole Include folder.

usage: build_release.py <output dir>
Writes the zips plus release_notes.md and prints "cycle=<YYNN>" for GitHub Actions.
"""
import datetime as dt
import os
import re
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "dist")
os.makedirs(OUT, exist_ok=True)


def airac_for(date):
    """FAA/ICAO 28-day cycle in effect on `date` as YYNN (anchor: 2601 = 2026-01-22)."""
    anchor = dt.date(2026, 1, 22)
    eff = anchor + dt.timedelta(days=28 * ((date - anchor).days // 28))
    first = eff
    while (first - dt.timedelta(days=28)).year == eff.year:
        first -= dt.timedelta(days=28)
    return f"{eff.year % 100:02d}{(eff - first).days // 28 + 1:02d}"


def repo_cycle():
    """Newest 'AIRAC NNNN' marker written by the FAA update into the airac files."""
    best = None
    pat = re.compile(rb"AIRAC (\d{4})")
    for d, _, files in os.walk(os.path.join(ROOT, "Include")):
        if os.path.basename(d) != "airac":
            continue
        for f in files:
            with open(os.path.join(d, f), "rb") as fh:
                for m in pat.finditer(fh.read()):
                    best = max(best or m.group(1).decode(), m.group(1).decode())
    return best


def add_tree(z, rel):
    base = os.path.join(ROOT, rel)
    for d, dirs, files in os.walk(base):
        dirs.sort()
        for f in sorted(files):
            p = os.path.join(d, f)
            z.write(p, os.path.relpath(p, ROOT))


def include_dir(isc_path):
    with open(isc_path, encoding="latin-1") as fh:
        for line in fh:
            m = re.match(r"\s*US[\\/](\w+)\s*$", line)
            if m:
                return m.group(1)
    return None


us = os.path.join(ROOT, "Include", "US")
folders = {d.lower(): d for d in os.listdir(us) if os.path.isdir(os.path.join(us, d))}
iscs = sorted(f for f in os.listdir(ROOT) if f.lower().endswith(".isc"))
built, skipped, used = [], [], set()

for isc in iscs:
    fac = include_dir(os.path.join(ROOT, isc))
    folder = folders.get((fac or "").lower())
    if not folder:
        skipped.append(isc)
        continue
    used.add(folder)
    name = f"{fac.upper()}.zip"
    with zipfile.ZipFile(os.path.join(OUT, name), "w", zipfile.ZIP_DEFLATED) as z:
        z.write(os.path.join(ROOT, isc), isc)
        add_tree(z, os.path.join("Include", "US", folder))
    built.append((name, isc))

full = "US-ALL.zip"
with zipfile.ZipFile(os.path.join(OUT, full), "w", zipfile.ZIP_DEFLATED) as z:
    for isc in iscs:
        z.write(os.path.join(ROOT, isc), isc)
    add_tree(z, "Include")

# The data may be merged ahead of its effective date, so take the newer of the
# cycle marked in the files and the cycle currently in effect.
cycle = max(filter(None, [repo_cycle(), airac_for(dt.date.today())]))
with open(os.path.join(OUT, "release_notes.md"), "w") as fh:
    fh.write(f"IVAO US legacy sector files, FAA data AIRAC {cycle}.\n\n")
    fh.write(f"- **{full}**: every ARTCC/FIR .isc file and the full `Include` folder\n")
    for name, isc in built:
        fh.write(f"- **{name}**: `{isc}` + its `Include/US` folder\n")
    extra = sorted(set(folders.values()) - used)
    if extra:
        fh.write(f"\nFolders without their own .isc (only in {full}): {', '.join(extra)}\n")
    if skipped:
        fh.write(f"Not packaged separately (no matching Include/US folder): {', '.join(skipped)}\n")

print(f"built {len(built)} facility zips + {full}", file=sys.stderr)
print(f"cycle={cycle}")
