#!/usr/bin/env python3
"""Write non-sensitive integration status so automation can inspect runs without UI access."""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path


def read_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-root", required=True)
    ap.add_argument("--output", default="status/private-smoke.json")
    args = ap.parse_args()

    work_root = Path(args.work_root).resolve()
    qa_dir = work_root / "job" / "output" / "qa"
    build = read_json(qa_dir / "build-result.json")
    package = read_json(qa_dir / "package-qa.json")
    render = read_json(qa_dir / "render-qa.json")

    if render:
        phase = "render_qa"
    elif package:
        phase = "package_qa"
    elif build:
        phase = "pptx_built"
    elif (work_root.parent / "caller-src").exists():
        phase = "private_source_checked_out"
    else:
        phase = "before_private_source_checkout"

    result = {
        "workflow_status": os.environ.get("JOB_STATUS", "unknown"),
        "phase_reached": phase,
        "run_id": os.environ.get("GITHUB_RUN_ID"),
        "run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT"),
        "engine_commit": os.environ.get("GITHUB_SHA"),
        "source_repository": os.environ.get("SOURCE_REPOSITORY") or None,
        "source_ref": os.environ.get("SOURCE_REF") or None,
        "request_path": os.environ.get("REQUEST_PATH") or None,
        "package_status": package.get("status") if package else None,
        "render_status": render.get("status") if render else None,
        "pptx_sha256": (render or package or build or {}).get("pptx_sha256"),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
