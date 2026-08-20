#!/usr/bin/env python3
"""PPTX package QA for the public fixture engine."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import zipfile

ROOT = Path.cwd().resolve()
EMU_PER_INCH = 914400


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_inside_root(rel: str, label: str) -> Path:
    raw = Path(rel)
    if raw.is_absolute():
        raise SystemExit(f"{label}: absolute paths are forbidden: {rel}")
    resolved = (ROOT / raw).resolve()
    try:
        resolved.relative_to(ROOT)
    except ValueError as exc:
        raise SystemExit(f"{label}: path escapes repository root: {rel}") from exc
    return resolved


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def package_qa(manifest_path: Path) -> dict:
    manifest = load_json(manifest_path)
    pptx_path = resolve_inside_root(manifest["output"]["pptx"], "output.pptx")
    qa_dir = resolve_inside_root(manifest["output"]["qa_dir"], "output.qa_dir")
    qa_dir.mkdir(parents=True, exist_ok=True)

    if not pptx_path.exists():
        raise SystemExit(f"PPTX missing: {pptx_path}")

    with zipfile.ZipFile(pptx_path, "r") as zf:
        names = zf.namelist()
        bad = zf.testzip()
        slide_files = sorted(n for n in names if re.fullmatch(r"ppt/slides/slide\d+\.xml", n))
        pres_xml = zf.read("ppt/presentation.xml").decode("utf-8", errors="replace")

    match = re.search(r"<p:sldSz[^>]*cx=\"(\d+)\"[^>]*cy=\"(\d+)\"", pres_xml)
    if not match:
        raise SystemExit("Could not read slide size from ppt/presentation.xml")
    cx, cy = int(match.group(1)), int(match.group(2))
    width_in = cx / EMU_PER_INCH
    height_in = cy / EMU_PER_INCH
    ratio = width_in / height_in if height_in else 0

    declared_slides = len(manifest["slides"])
    expected_min = int(manifest.get("quality", {}).get("min_slides", declared_slides))
    require_wide = bool(manifest.get("quality", {}).get("require_wide", True))
    failures = []
    if bad:
        failures.append(f"Corrupt ZIP member: {bad}")
    if len(slide_files) != declared_slides:
        failures.append(f"Slide count mismatch: package={len(slide_files)} declared={declared_slides}")
    if len(slide_files) < expected_min:
        failures.append(f"Slide count below minimum: {len(slide_files)} < {expected_min}")
    if require_wide and abs(ratio - (16 / 9)) > 0.02:
        failures.append(f"Canvas is not 16:9 wide: ratio={ratio:.4f}")

    result = {
        "status": "PASS" if not failures else "FAIL",
        "engine_version": manifest.get("engine_version"),
        "request_id": manifest.get("request_id"),
        "manifest": manifest_path.relative_to(ROOT).as_posix(),
        "pptx": pptx_path.relative_to(ROOT).as_posix(),
        "pptx_sha256": sha256(pptx_path),
        "zip_ok": bad is None,
        "slide_count": len(slide_files),
        "slide_count_declared": declared_slides,
        "canvas": {
            "cx": cx,
            "cy": cy,
            "width_in": round(width_in, 4),
            "height_in": round(height_in, 4),
            "ratio": round(ratio, 6),
            "wide_16_9": abs(ratio - (16 / 9)) <= 0.02,
        },
        "failures": failures,
    }
    out = qa_dir / "package-qa.json"
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    args = parser.parse_args()
    manifest_path = resolve_inside_root(args.manifest, "manifest")
    result = package_qa(manifest_path)
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
