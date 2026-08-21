#!/usr/bin/env python3
"""Render approved-candidate presentation assets with constrained mature drivers.

The engine treats project content as data. This runner accepts only declarative
asset manifests and fixed drivers; it never imports or executes arbitrary caller
Python modules.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path.cwd().resolve()
ID_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
DRIVERS = {"typst-cetz", "graphviz", "matplotlib"}


def die(message: str) -> "NoReturn":
    raise SystemExit(message)


def resolve_inside_root(value: str, label: str) -> Path:
    p = Path(value)
    if not value or p.is_absolute() or ".." in p.parts:
        die(f"{label}: unsafe repository-relative path: {value!r}")
    resolved = (ROOT / p).resolve()
    try:
        resolved.relative_to(ROOT)
    except ValueError as exc:
        raise SystemExit(f"{label}: path escapes repository root: {value!r}") from exc
    return resolved


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run(command: list[str]) -> None:
    proc = subprocess.run(command, cwd=ROOT, text=True, encoding="utf-8", errors="replace", capture_output=True)
    if proc.stdout:
        print(proc.stdout, end="")
    if proc.stderr:
        print(proc.stderr, end="")
    if proc.returncode != 0:
        raise SystemExit(f"Command failed ({proc.returncode}): {' '.join(command)}")


def ensure_svg(path: Path) -> None:
    if not path.exists() or path.stat().st_size < 200:
        die(f"SVG output missing or too small: {path}")
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        raise SystemExit(f"Invalid SVG XML: {path}: {exc}") from exc
    if not root.tag.lower().endswith("svg"):
        die(f"Expected SVG root element: {path}")


def preview_svg(svg: Path, png: Path) -> None:
    converter = shutil.which("rsvg-convert")
    if not converter:
        die("rsvg-convert is required for asset preview generation")
    png.parent.mkdir(parents=True, exist_ok=True)
    run([converter, "-w", "1600", "-o", str(png), str(svg)])
    if not png.exists() or png.stat().st_size < 500:
        die(f"Preview PNG missing or too small: {png}")


def render_typst_cetz(source: Path, output: Path) -> None:
    typst = shutil.which("typst")
    if not typst:
        die("typst executable is not available")
    if source.suffix.lower() != ".typ" or output.suffix.lower() != ".svg":
        die("typst-cetz driver requires .typ source and .svg output")
    output.parent.mkdir(parents=True, exist_ok=True)
    run([typst, "compile", "--root", str(ROOT), "--format", "svg", str(source), str(output)])


def render_graphviz(source: Path, output: Path) -> None:
    dot = shutil.which("dot")
    if not dot:
        die("graphviz 'dot' executable is not available")
    if source.suffix.lower() not in {".dot", ".gv"} or output.suffix.lower() != ".svg":
        die("graphviz driver requires .dot/.gv source and .svg output")
    output.parent.mkdir(parents=True, exist_ok=True)
    run([dot, "-Tsvg", str(source), "-o", str(output)])


def render_matplotlib(source: Path, output: Path) -> None:
    if source.suffix.lower() != ".json" or output.suffix.lower() != ".svg":
        die("matplotlib driver requires declarative .json source and .svg output")
    spec = json.loads(source.read_text(encoding="utf-8"))
    if spec.get("kind") != "line":
        die("matplotlib v1 currently supports kind='line' only")
    x = spec.get("x")
    series = spec.get("series")
    if not isinstance(x, list) or len(x) < 2 or not isinstance(series, list) or not series:
        die("matplotlib source requires x[] and non-empty series[]")
    for item in series:
        y = item.get("y")
        if not isinstance(y, list) or len(y) != len(x):
            die("each matplotlib series.y must match x length")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(10, 5.625), constrained_layout=True)
    for item in series:
        ax.plot(x, item["y"], marker=item.get("marker", "o"), linewidth=float(item.get("linewidth", 2.2)), label=item.get("label"))
    if spec.get("title"):
        ax.set_title(str(spec["title"]))
    if spec.get("xlabel"):
        ax.set_xlabel(str(spec["xlabel"]))
    if spec.get("ylabel"):
        ax.set_ylabel(str(spec["ylabel"]))
    if any(item.get("label") for item in series):
        ax.legend()
    ax.grid(True, alpha=0.25)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, format="svg", metadata={"Date": None})
    plt.close(fig)


def render_one(asset: dict) -> dict:
    asset_id = str(asset.get("id", "")).strip()
    driver = str(asset.get("driver", "")).strip()
    if not ID_RE.fullmatch(asset_id):
        die(f"invalid asset id: {asset_id!r}")
    if driver not in DRIVERS:
        die(f"unsupported driver {driver!r}; allowed={sorted(DRIVERS)}")

    source = resolve_inside_root(str(asset.get("source", "")), f"{asset_id}.source")
    output = resolve_inside_root(str(asset.get("output", "")), f"{asset_id}.output")
    preview = resolve_inside_root(str(asset.get("preview", "")), f"{asset_id}.preview")
    if not source.exists() or not source.is_file():
        die(f"source does not exist: {source}")

    if driver == "typst-cetz":
        render_typst_cetz(source, output)
    elif driver == "graphviz":
        render_graphviz(source, output)
    elif driver == "matplotlib":
        render_matplotlib(source, output)

    ensure_svg(output)
    preview_svg(output, preview)
    result = {
        "id": asset_id,
        "driver": driver,
        "source": source.relative_to(ROOT).as_posix(),
        "source_sha256": sha256(source),
        "output": output.relative_to(ROOT).as_posix(),
        "output_sha256": sha256(output),
        "preview": preview.relative_to(ROOT).as_posix(),
        "preview_sha256": sha256(preview),
        "status": "PASS",
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    args = ap.parse_args()

    manifest_path = resolve_inside_root(args.manifest, "manifest")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("contract_version") != "1":
        die("asset manifest contract_version must be '1'")
    assets = manifest.get("assets")
    if not isinstance(assets, list) or not assets:
        die("asset manifest requires non-empty assets[]")

    qa_dir = resolve_inside_root(str(manifest.get("qa_dir", "")), "qa_dir")
    qa_dir.mkdir(parents=True, exist_ok=True)
    results = [render_one(asset) for asset in assets]
    evidence = {
        "status": "PASS",
        "contract_version": "1",
        "request_id": manifest.get("request_id"),
        "manifest": manifest_path.relative_to(ROOT).as_posix(),
        "drivers": sorted({item["driver"] for item in results}),
        "asset_count": len(results),
        "assets": results,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    out = qa_dir / "asset-qa.json"
    out.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(evidence, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
