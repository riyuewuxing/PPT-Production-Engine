#!/usr/bin/env python3
"""Prepare an isolated engine job from a private project build request."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ENGINE_VERSION = "0.2.0"


def die(msg: str) -> None:
    raise SystemExit(msg)


def resolve_inside(root: Path, rel: str, label: str) -> Path:
    raw = Path(rel)
    if not rel or raw.is_absolute() or ".." in raw.parts:
        die(f"{label}: unsafe path: {rel!r}")
    resolved = (root / raw).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise SystemExit(f"{label}: path escapes root: {rel!r}") from exc
    return resolved


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--caller-root", required=True)
    ap.add_argument("--request", required=True)
    ap.add_argument("--job-root", required=True)
    args = ap.parse_args()

    caller_root = Path(args.caller_root).resolve()
    job_root = Path(args.job_root).resolve()
    job_root.mkdir(parents=True, exist_ok=True)

    request_path = resolve_inside(caller_root, args.request, "request")
    request = json.loads(request_path.read_text(encoding="utf-8"))

    if request.get("contract_version") != "1":
        die("Unsupported contract_version; expected '1'")
    if request.get("driver") != "pptxgenjs-spec-v1":
        die("Unsupported driver; expected 'pptxgenjs-spec-v1'")

    request_id = str(request.get("request_id", "")).strip()
    if not request_id or len(request_id) > 120:
        die("request_id is required and must be <= 120 characters")

    source_path = resolve_inside(caller_root, request.get("source", ""), "source")
    source = json.loads(source_path.read_text(encoding="utf-8"))
    if not isinstance(source.get("deck"), dict):
        die("source.deck must be an object")
    slides = source.get("slides")
    if not isinstance(slides, list) or not slides:
        die("source.slides must be a non-empty array")

    output = request.get("output") or {}
    pptx_dest = output.get("pptx", "")
    evidence_dest = output.get("evidence_dir", "")
    # Validate writeback destinations now, even though they are not written in this step.
    resolve_inside(caller_root, pptx_dest, "output.pptx")
    resolve_inside(caller_root, evidence_dest, "output.evidence_dir")

    quality = request.get("quality") or {}
    min_slides = int(quality.get("min_slides", len(slides)))
    if min_slides < 1 or min_slides > len(slides):
        die("quality.min_slides must be between 1 and the declared slide count")
    render_dpi = int(quality.get("render_dpi", 144))
    if render_dpi < 72 or render_dpi > 300:
        die("quality.render_dpi must be between 72 and 300")

    rel_job_root = job_root.relative_to(Path.cwd().resolve()).as_posix()
    manifest = {
        "engine_version": ENGINE_VERSION,
        "request_id": request_id,
        "deck": source["deck"],
        "slides": slides,
        "output": {
            "pptx": f"{rel_job_root}/output/deck.pptx",
            "qa_dir": f"{rel_job_root}/output/qa",
            "render_dir": f"{rel_job_root}/output/rendered",
        },
        "quality": {
            "min_slides": min_slides,
            "require_wide": bool(quality.get("require_wide", True)),
            "render_dpi": render_dpi,
        },
    }

    (job_root / "build-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    summary = {
        "status": "PREPARED",
        "engine_version": ENGINE_VERSION,
        "request_id": request_id,
        "driver": request["driver"],
        "source_path": source_path.relative_to(caller_root).as_posix(),
        "slide_count": len(slides),
        "writeback": {"pptx": pptx_dest, "evidence_dir": evidence_dest},
    }
    (job_root / "request-summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
