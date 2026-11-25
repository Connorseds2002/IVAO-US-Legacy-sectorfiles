#!/usr/bin/env python3
"""Build combined-ARTCC Aurora profiles (e.g. ZMA+ZJX, ZLA+ZOA).

For each combination in COMBOS this writes:

  * <isc>                         a combined .isc at the repo root, and
  * Include/US/<folder>/          the include folder it points to.

The include folder is generated from the single-ARTCC folders every time, so it
always carries the current AIRAC data and is not committed (see .gitignore).
The release workflow runs this before zipping; run it yourself after pulling
if you use the repo directly instead of the release zips:

    python3 .github/scripts/build_combos.py

Layout of a generated folder, e.g. Include/US/kzma_kzjx/:

  kzma/ ...        ZMA's airac, airspace, geo, ad, app folders and any
  kzjx/ ...        root files its .isc references (each ARTCC kept apart,
                   so files with the same name never overwrite each other)
  atc.atc          both ATC position lists, merged (first seen wins)
  default.atis     ATIS template
  <icao>.sid/.str/.tfl/.txi/.gts/.mva/.vfi/.vrt
                   per-airport files from both ARTCCs. Where both folders
                   have a different file for the same airport, the ARTCC that
                   owns the airport wins (OWNERS), otherwise the first ARTCC.

The combined .isc opens centred midway between the two ARTCCs and loads both
ARTCCs' boundaries, airports, fixes, navaids, airways and video maps. Files
whose content is identical in both ARTCCs are loaded once.
"""
import math
import os
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
US = os.path.join(ROOT, "Include", "US")

COMBOS = [
    {
        "isc": "KZMA_KZJX Miami-Jacksonville combined.isc",
        "folder": "kzma_kzjx",
        "sources": [("KZMA.isc", "kzma"), ("KZJX.isc", "kzjx")],
        # Airports whose per-airport files differ between the two folders:
        # take that airport's files from the ARTCC that owns it.
        "owners": {
            "kmia": "kzma",
            "ktpa": "kzjx",
            "kcof": "kzjx",
            "kism": "kzjx",
            "ktix": "kzjx",
            "kmlb": "kzjx",
        },
    },
    {
        "isc": "KZLA_KZOA Los Angeles-Oakland combined.isc",
        "folder": "kzla_kzoa",
        "sources": [("KZLA Los Angeles ARTCC.isc", "kzla"), ("KZOA.isc", "kzoa")],
        "owners": {},
    },
]

FILE_LINE = re.compile(r"^(\s*(?://\s*)?)([Ff])[;:](.*)$")
SHARED_ROOT = {"atc.atc", "default.atis"}
AIRPORT_EXT = (".sid", ".str", ".tfl", ".txi", ".gts", ".mva", ".vfi", ".vrt")
SECTION = re.compile(r"^\s*\[([^\]]+)\]\s*$")


def read(path):
    with open(path, encoding="latin-1") as fh:
        return fh.read().splitlines()


def parse_isc(path):
    """Return (info_lines, [(section_name, [lines])]) keeping section order."""
    sections, cur = [], None
    for line in read(path):
        m = SECTION.match(line)
        if m:
            cur = (m.group(1).strip(), [])
            sections.append(cur)
        elif cur is not None:
            cur[1].append(line)
    info = next((l for n, l in sections if n.upper() == "INFO"), [])
    info = [l.strip() for l in info if l.strip()]
    return info, [s for s in sections if s[0].upper() != "INFO"]


def dms(value):
    """'N025.47.43.300' or '25.79' -> signed decimal degrees."""
    value = value.strip()
    sign = -1 if value[:1] in "SWsw" else 1
    if value[:1].isalpha():
        value = value[1:]
    parts = value.split(".")
    if len(parts) >= 3:
        deg, mins = int(parts[0]), int(parts[1])
        secs = float(".".join(parts[2:]))
        return sign * (deg + mins / 60 + secs / 3600)
    return sign * float(value)


def to_dms(value, pos, neg):
    hemi = pos if value >= 0 else neg
    value = abs(value)
    deg = int(value)
    mins_f = (value - deg) * 60
    mins = int(mins_f)
    secs = round((mins_f - mins) * 60, 3)
    if secs >= 60:
        secs -= 60
        mins += 1
    if mins >= 60:
        mins -= 60
        deg += 1
    return f"{hemi}{deg:03d}.{mins:02d}.{secs:06.3f}"


def file_hash(path):
    with open(path, "rb") as fh:
        return hash(fh.read())


def find_file(base, rel):
    """Resolve a Windows-style relative path case-insensitively under base."""
    cur = base
    for part in re.split(r"[\\/]", rel.strip()):
        if not part:
            continue
        try:
            names = {n.lower(): n for n in os.listdir(cur)}
        except NotADirectoryError:
            return None
        hit = names.get(part.lower())
        if hit is None:
            return None
        cur = os.path.join(cur, hit)
    return cur if os.path.isfile(cur) else None


# AIRAC point files: name -> (fields forming the key, lat field, lon field).
# A later ARTCC's line is dropped when an earlier ARTCC has the same key at
# (nearly) the same position; same name somewhere else is a different point.
AIRAC_KEYS = {
    "airports.ap": ((0,), 3, 4),
    "runways.rw": ((0, 1, 2), 7, 8),
    "vor.vor": ((0, 1), 2, 3),
    "ndb.ndb": ((0, 1), 2, 3),
    "fixes.fix": ((0,), 1, 2),
}
SAME_POINT_NM = 1.0


def norm_field(value):
    """Upper-case text; numbers compared by value so 115.00 == 115.000."""
    try:
        return f"{float(value):g}"
    except ValueError:
        return value.upper()


def airac_entry(line, spec):
    """(key, (lat, lon)) for a data line, or None for comments/blank/odd lines."""
    if not line.strip() or line.lstrip().startswith("//"):
        return None
    fields = [f.strip() for f in line.split("//")[0].split(";")]
    idx, la, lo = spec
    if len(fields) <= max(max(idx), la, lo):
        return None
    try:
        pos = (dms(fields[la]), dms(fields[lo]))
    except (ValueError, IndexError):
        return None
    key = tuple(norm_field(fields[i]) for i in idx)
    if fields[0].upper() == "KEY" or not key[0]:
        return None
    return key, pos


def near(a, b):
    dlat = (a[0] - b[0]) * 60
    dlon = (a[1] - b[1]) * 60 * math.cos(math.radians(a[0]))
    return math.hypot(dlat, dlon) <= SAME_POINT_NM


def dedupe_airac(out, facs):
    warnings, seen = [], {name: {} for name in AIRAC_KEYS}
    for n, fac in enumerate(facs):
        for name, spec in AIRAC_KEYS.items():
            path = find_file(os.path.join(out, fac), "airac\\" + name)
            if not path:
                continue
            lines, kept, dropped = read(path), [], 0
            for line in lines:
                e = airac_entry(line, spec)
                if e and n and any(near(e[1], p) for p in seen[name].get(e[0], ())):
                    dropped += 1
                    continue
                kept.append(line)
            for line in kept:
                e = airac_entry(line, spec)
                if e:
                    seen[name].setdefault(e[0], []).append(e[1])
            if dropped:
                with open(path, "w", encoding="latin-1", newline="\n") as fh:
                    fh.write("\n".join(kept) + "\n")
                print(f"  {fac}/airac/{name}: {dropped} entries already in an earlier ARTCC, dropped", file=sys.stderr)
    return warnings


def build(combo):
    out = os.path.join(US, combo["folder"])
    if os.path.isdir(out):
        shutil.rmtree(out)
    os.makedirs(out)
    warnings = []
    infos, parsed = [], []

    # 1. Each ARTCC's folders (and root files its .isc names) under its own prefix.
    for isc, fac in combo["sources"]:
        src = os.path.join(US, fac)
        info, sections = parse_isc(os.path.join(ROOT, isc))
        infos.append(info)
        parsed.append((fac, sections))
        dst = os.path.join(out, fac)
        os.makedirs(dst)
        for name in os.listdir(src):
            p = os.path.join(src, name)
            if os.path.isdir(p):
                shutil.copytree(p, os.path.join(dst, name))
        for _, lines in sections:
            for line in lines:
                m = FILE_LINE.match(line)
                if not m:
                    continue
                rel = m.group(3).strip()
                if re.search(r"[\\/]", rel):
                    continue  # lives in a subfolder, already copied
                hit = find_file(src, rel)
                if hit:
                    shutil.copy2(hit, os.path.join(dst, os.path.basename(hit)))

    # 1b. Each ARTCC's AIRAC files list some neighbouring airports, navaids and
    # fixes too (ZOA's airports.ap has KLAX, KBUR, KSNA). Loaded side by side
    # they would show twice in Aurora, so drop from later ARTCCs whatever an
    # earlier one already has.
    warnings.extend(dedupe_airac(out, [fac for _, fac in combo["sources"]]))

    # 2. Per-airport files at the folder root, plus merged ATC list.
    placed = {}
    for _, fac in combo["sources"]:
        src = os.path.join(US, fac)
        for name in sorted(os.listdir(src)):
            p = os.path.join(src, name)
            low = name.lower()
            if os.path.isdir(p) or low in SHARED_ROOT:
                continue
            if not low.endswith(AIRPORT_EXT):
                continue  # maps, colours etc. are reached through the prefixed copy
            if low not in placed:
                placed[low] = (fac, p)
                continue
            other_fac, other_p = placed[low]
            if file_hash(other_p) == file_hash(p):
                continue
            icao = low.split(".")[0]
            owner = combo["owners"].get(icao)
            if owner == fac:
                placed[low] = (fac, p)
            elif owner is None:
                warnings.append(f"{name}: differs between {other_fac} and {fac}, kept {other_fac}")
    for low, (fac, p) in placed.items():
        shutil.copy2(p, os.path.join(out, os.path.basename(p)))

    seen, atc = set(), []
    for _, fac in combo["sources"]:
        p = find_file(os.path.join(US, fac), "atc.atc")
        for line in read(p) if p else []:
            key = line.split(";")[0].strip().upper()
            if not key or key in seen:
                continue
            seen.add(key)
            atc.append(line.rstrip())
    with open(os.path.join(out, "atc.atc"), "w", encoding="latin-1", newline="\n") as fh:
        fh.write("\n".join(atc) + "\n")
    atis = find_file(os.path.join(US, combo["sources"][0][1]), "default.atis")
    if atis:
        shutil.copy2(atis, os.path.join(out, "default.atis"))

    # 3. Combined .isc
    lats = [dms(i[0]) for i in infos]
    lons = [dms(i[1]) for i in infos]
    lat, lon = sum(lats) / len(lats), sum(lons) / len(lons)
    magvars = [float(i[4]) for i in infos]
    magvar = round(sum(magvars) / len(magvars), 1)
    isc = [
        "[INFO]",
        to_dms(lat, "N", "S"),
        to_dms(lon, "E", "W"),
        "60",
        str(round(60 * math.cos(math.radians(lat)))),
        f"{magvar:g}",
        f"US\\{combo['folder'].upper()}",
        "",
    ]

    order, merged = [], {}
    for fac, sections in parsed:
        for name, lines in sections:
            key = name.upper()
            if key not in merged:
                order.append(key)
                merged[key] = {"name": name, "lines": [], "files": set(), "defines": set()}
            sec = merged[key]
            if key in ("ATC", "ATIS"):
                if not sec["lines"]:
                    sec["lines"].append("F;atc.atc" if key == "ATC" else "F;default.atis")
                continue
            for line in lines:
                if not line.strip():
                    continue
                m = FILE_LINE.match(line)
                if m:
                    rel = m.group(3).strip()
                    comment = m.group(1)
                    path = find_file(os.path.join(out, fac), rel)
                    line_out = f"{comment}F;{fac}\\{rel}"
                    if line_out.lower() in (l.lower() for l in sec["lines"]):
                        continue
                    if path and not comment:
                        h = file_hash(path)
                        if h in sec["files"]:
                            continue
                        sec["files"].add(h)
                    elif not path and not comment:
                        # also missing for the single-ARTCC profile; leave it out here
                        warnings.append(f"{fac}: [{name}] {rel} not found, skipped")
                        continue
                    sec["lines"].append(line_out)
                elif key == "DEFINE":
                    dkey = line.split(";")[0].strip().lstrip("/").strip().upper()
                    if dkey in sec["defines"]:
                        continue
                    sec["defines"].add(dkey)
                    sec["lines"].append(line.rstrip())
                else:
                    sec["lines"].append(line.rstrip())
    for key in order:
        sec = merged[key]
        isc.append(f"[{sec['name']}]")
        isc.extend(sec["lines"])
        isc.append("")
    with open(os.path.join(ROOT, combo["isc"]), "w", encoding="latin-1", newline="\n") as fh:
        fh.write("\n".join(isc))
    return warnings


def main():
    for combo in COMBOS:
        for w in build(combo):
            print(f"warning [{combo['folder']}]: {w}", file=sys.stderr)
        print(f"built {combo['isc']} -> Include/US/{combo['folder']}", file=sys.stderr)


if __name__ == "__main__":
    main()
