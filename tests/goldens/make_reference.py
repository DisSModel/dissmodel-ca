"""
Extract the reference values used by ``tests/test_goldens.py`` from the
TerraME ``ca`` goldens of ``terrame-goldens``.

- ``grids/<case>.csv.gz``: the grid goldens (state of every cell; columns
  ``step, y, x0, x1, ...``), kept only at the steps in :func:`grid_steps`.
- ``ensembles.csv.gz``: for the stochastic models, the number of cells in
  each state for seeds 1 to 50, at the steps in ``ENSEMBLE_STEPS``
  (columns ``case, value, step, seed, count``; zeros included).
- ``reference.json``: source version, package commit, steps kept and the
  SHA-256 of each source file.

    python tests/goldens/make_reference.py /path/to/terrame-goldens
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent

ENSEMBLE_STEPS = {
    "fire": (5, 10, 20, 50, 100),
    "solid_diffusion": (10, 50, 100, 200, 400),
    "growth": (5, 10, 20, 50, 100),
    "snow": (10, 50, 100, 300, 600),
    "interspecific_competition": (5, 10, 50, 100, 200),
}


def grid_steps(final: int) -> list[int]:
    """Every step up to 10, then a few more up to the final step."""
    steps = set(range(min(final, 10) + 1)) | {final}
    steps |= {s for s in (20, 50, 100, 200, 300, 400, 500) if s <= final}
    return sorted(steps)


def write_gz(text: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    buf = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=buf, mtime=0, compresslevel=9) as gz:
        gz.write(text.encode())
    dest.write_bytes(buf.getvalue())


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(root: Path) -> None:
    src = root / "goldens" / "ca"
    sources: dict[str, str] = {}
    grids: dict[str, list[int]] = {}

    with open(src / "grids" / "cases.csv", newline="") as f:
        cases = list(csv.DictReader(f))
    for c in cases:
        path = src / "grids" / f"{c['case']}.csv.gz"
        sources[path.relative_to(root).as_posix()] = sha256(path)
        keep = grid_steps(int(c["final_time"]))
        with gzip.open(path, "rt", newline="") as f:
            lines = f.read().splitlines()
        out = [lines[0]] + [ln for ln in lines[1:] if int(ln.split(",", 1)[0]) in keep]
        write_gz("\n".join(out) + "\n", HERE / "grids" / f"{c['case']}.csv.gz")
        grids[c["case"]] = keep
    (HERE / "grids" / "cases.csv").write_bytes((src / "grids" / "cases.csv").read_bytes())

    rows = []
    for case, steps in ENSEMBLE_STEPS.items():
        path = src / "ensembles" / f"{case}.csv.gz"
        sources[path.relative_to(root).as_posix()] = sha256(path)
        counts: dict[tuple[str, int, int], int] = defaultdict(int)
        values, seeds = set(), set()
        with gzip.open(path, "rt", newline="") as f:
            for r in csv.DictReader(f):
                values.add(r["value"])
                seeds.add(int(r["seed"]))
                if int(r["step"]) in steps:
                    counts[(r["value"], int(r["step"]), int(r["seed"]))] = int(r["count"])
        for v in sorted(values):
            for t in steps:
                for s in sorted(seeds):
                    rows.append(f"{case},{v},{t},{s},{counts[(v, t, s)]}")
    write_gz("case,value,step,seed,count\n" + "\n".join(rows) + "\n", HERE / "ensembles.csv.gz")

    manifest = json.loads((root / "manifest.json").read_text())
    meta = {
        "source": "https://github.com/LambdaGeo/terrame-goldens",
        "version": manifest["version"],
        "terrame": manifest["terrame"],
        "packages": [p for p in manifest["packages"] if p["name"] == "ca"],
        "files": sources,
        "grid_steps": grids,
        "ensemble_steps": {k: list(v) for k, v in ENSEMBLE_STEPS.items()},
    }
    (HERE / "reference.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(f"{len(grids)} grids, {len(rows)} ensemble values written")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
