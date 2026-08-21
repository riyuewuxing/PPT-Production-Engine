#!/usr/bin/env python3
"""Execute an explicitly hash-pinned, public-safe historical PptxGenJS source.

This is a migration-only adapter, not the normal production driver. It exists
for historical decks whose authored source predates the declarative Engine
contract. The source must match an exact Git blob id before execution. Public
handoff workflows must run without private credentials and with checkout
credentials disabled.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path

ROOT = Path.cwd().resolve()


def die(message: str) -> "NoReturn":
    raise SystemExit(message)


def safe(value: str, label: str, *, exists: bool = False) -> Path:
    raw = Path(value)
    if not value or raw.is_absolute() or ".." in raw.parts:
        die(f"{label}: unsafe path {value!r}")
    resolved = (ROOT / raw).resolve()
    try:
        resolved.relative_to(ROOT)
    except ValueError as exc:
        raise SystemExit(f"{label}: path escapes repository root") from exc
    if exists and not resolved.exists():
        die(f"{label}: missing {resolved}")
    return resolved


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_blob(path: Path) -> str:
    proc = subprocess.run(["git", "hash-object", str(path)], cwd=ROOT, text=True, capture_output=True)
    if proc.returncode != 0:
        die(proc.stderr or "git hash-object failed")
    return proc.stdout.strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    args = ap.parse_args()
    manifest_path = safe(args.manifest, "manifest", exists=True)
    cfg = json.loads(manifest_path.read_text(encoding="utf-8"))
    if cfg.get("contract_version") != "1":
        die("contract_version must be '1'")
    if cfg.get("driver") != "legacy-pptxgenjs-hash-pinned":
        die("unsupported migration driver")

    source = safe(str(cfg.get("source", "")), "source", exists=True)
    if source.suffix.lower() not in {".cjs", ".js"}:
        die("legacy source must be .cjs or .js")
    expected_blob = str(cfg.get("expected_git_blob_sha", "")).strip().lower()
    actual_blob = git_blob(source)
    if not expected_blob or actual_blob != expected_blob:
        die(f"source Git blob mismatch: expected={expected_blob} actual={actual_blob}")

    text = source.read_text(encoding="utf-8")
    forbidden = ["child_process", "node:child_process", "require('http')", "require(\"http\")", "require('https')", "require(\"https\")", "require('net')", "require(\"net\")"]
    hits = [item for item in forbidden if item in text]
    if hits:
        die(f"legacy source contains forbidden execution/network modules: {hits}")
    allowed_requires = {"pptxgenjs", "fs", "path"}
    import re
    requires = set(re.findall(r"require\(['\"]([^'\"]+)['\"]\)", text))
    unexpected = sorted(requires - allowed_requires)
    if unexpected:
        die(f"legacy source imports unexpected modules: {unexpected}")

    project_root = safe(str(cfg.get("project_root", "")), "project_root")
    output_rel = Path(str(cfg.get("expected_output", "")))
    if output_rel.is_absolute() or ".." in output_rel.parts:
        die("expected_output must be project-root-relative")
    project_root.mkdir(parents=True, exist_ok=True)
    output = (project_root / output_rel).resolve()
    try:
        output.relative_to(project_root)
    except ValueError as exc:
        raise SystemExit("expected output escapes project_root") from exc

    env = dict(os.environ)
    env["PROJECT_PATH"] = str(project_root)
    proc = subprocess.run(["node", str(source)], cwd=ROOT, env=env, text=True, encoding="utf-8", errors="replace", capture_output=True)
    if proc.stdout:
        print(proc.stdout, end="")
    if proc.stderr:
        print(proc.stderr, end="")
    if proc.returncode != 0:
        die(f"legacy source failed with exit code {proc.returncode}")
    if not output.is_file():
        die(f"legacy source did not produce expected PPTX: {output}")

    evidence = {
        "status": "PASS",
        "driver": cfg["driver"],
        "source": source.relative_to(ROOT).as_posix(),
        "source_git_blob_sha": actual_blob,
        "source_sha256": sha256(source),
        "output": output.relative_to(ROOT).as_posix(),
        "pptx_sha256": sha256(output),
    }
    qa = safe(str(cfg.get("qa", "")), "qa")
    qa.parent.mkdir(parents=True, exist_ok=True)
    qa.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(evidence, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
