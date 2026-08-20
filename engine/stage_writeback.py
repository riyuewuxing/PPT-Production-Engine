#!/usr/bin/env python3
"""Stage a completed engine job into a fresh checkout of the private caller repo."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path


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


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def copy_tree_files(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-caller-root", required=True)
    ap.add_argument("--writeback-root", required=True)
    ap.add_argument("--request", required=True)
    ap.add_argument("--job-root", required=True)
    args = ap.parse_args()

    source_root = Path(args.source_caller_root).resolve()
    writeback_root = Path(args.writeback_root).resolve()
    job_root = Path(args.job_root).resolve()

    request_path = resolve_inside(source_root, args.request, "request")
    request = json.loads(request_path.read_text(encoding="utf-8"))
    output_cfg = request.get("output") or {}
    pptx_dest = resolve_inside(writeback_root, output_cfg.get("pptx", ""), "output.pptx")
    evidence_dir = resolve_inside(writeback_root, output_cfg.get("evidence_dir", ""), "output.evidence_dir")

    pptx_src = job_root / "output" / "deck.pptx"
    qa_src = job_root / "output" / "qa"
    rendered_src = job_root / "output" / "rendered"
    if not pptx_src.exists():
        die(f"Generated PPTX is missing: {pptx_src}")
    for name in ("build-result.json", "package-qa.json", "render-qa.json"):
        if not (qa_src / name).exists():
            die(f"Required QA evidence is missing: {name}")

    package_qa = json.loads((qa_src / "package-qa.json").read_text(encoding="utf-8"))
    render_qa = json.loads((qa_src / "render-qa.json").read_text(encoding="utf-8"))
    pptx_hash = sha256(pptx_src)
    if package_qa.get("status") != "PASS" or render_qa.get("status") != "PASS":
        die("Refusing writeback because QA is not PASS")
    if package_qa.get("pptx_sha256") != pptx_hash or render_qa.get("pptx_sha256") != pptx_hash:
        die("Refusing writeback because QA evidence is not bound to the generated PPTX hash")

    pptx_dest.parent.mkdir(parents=True, exist_ok=True)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(pptx_src, pptx_dest)
    for name in ("build-result.json", "package-qa.json", "render-qa.json"):
        shutil.copy2(qa_src / name, evidence_dir / name)

    include_render = bool(output_cfg.get("writeback_render_evidence", True))
    if include_render:
        copy_tree_files(rendered_src, evidence_dir / "rendered")

    result = {
        "status": "PASS",
        "request_id": request.get("request_id"),
        "engine_version": "0.2.0",
        "engine_repository": os.environ.get("GITHUB_REPOSITORY"),
        "engine_commit": os.environ.get("GITHUB_SHA"),
        "source_repository": os.environ.get("SOURCE_REPOSITORY"),
        "source_ref": os.environ.get("SOURCE_REF"),
        "pptx": output_cfg.get("pptx"),
        "pptx_sha256": pptx_hash,
        "evidence_dir": output_cfg.get("evidence_dir"),
        "package_qa": package_qa.get("status"),
        "render_qa": render_qa.get("status"),
        "rendered_pages": len(render_qa.get("pages", [])),
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }
    (evidence_dir / "engine-result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
