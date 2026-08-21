#!/usr/bin/env python3
"""Bounded adapter for a pinned PPT Master checkout.

The caller supplies declarative paths only. This adapter owns the executable
script roster and arguments; handoff manifests cannot request arbitrary
commands. The adapter is intended for native SVG->DrawingML generation,
animation validation/read-back, and PPTX normalization.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd().resolve()


def die(message: str) -> "NoReturn":
    raise SystemExit(message)


def safe_path(value: str, label: str, *, must_exist: bool = False) -> Path:
    raw = Path(value)
    if not value or raw.is_absolute() or ".." in raw.parts:
        die(f"{label}: unsafe repository-relative path: {value!r}")
    resolved = (ROOT / raw).resolve()
    try:
        resolved.relative_to(ROOT)
    except ValueError as exc:
        raise SystemExit(f"{label}: path escapes repository root: {value!r}") from exc
    if must_exist and not resolved.exists():
        die(f"{label}: missing path: {resolved}")
    return resolved


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run(command: list[str], *, capture: bool = False) -> subprocess.CompletedProcess[str]:
    print("+", " ".join(command))
    proc = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=capture,
        env={**os.environ, "PYTHONUNBUFFERED": "1"},
    )
    if capture and proc.stdout:
        print(proc.stdout, end="")
    if capture and proc.stderr:
        print(proc.stderr, end="", file=sys.stderr)
    if proc.returncode != 0:
        raise SystemExit(f"command failed ({proc.returncode}): {' '.join(command)}")
    return proc


def scripts_root(ppt_master_root: Path) -> Path:
    root = ppt_master_root / "skills" / "ppt-master" / "scripts"
    required = [
        "animation_config.py",
        "svg_quality_checker.py",
        "svg_to_pptx.py",
        "pptx_delivery_check.py",
        "pptx_to_svg.py",
    ]
    missing = [name for name in required if not (root / name).is_file()]
    if missing:
        die(f"PPT Master checkout is incomplete; missing {missing}")
    return root


def svg_to_pptx(cfg: dict, scripts: Path) -> dict:
    project = safe_path(str(cfg.get("project", "")), "project", must_exist=True)
    output = safe_path(str(cfg.get("output", "")), "output")
    readback = safe_path(str(cfg.get("readback_dir", "")), "readback_dir")
    qa_path = safe_path(str(cfg.get("qa", "")), "qa")
    animation = str(cfg.get("animation_config", "animations.json"))
    if Path(animation).is_absolute() or ".." in Path(animation).parts:
        die("animation_config must be a safe project-relative filename")
    animation_path = project / animation
    if not animation_path.is_file():
        die(f"animation config missing: {animation_path}")
    if not (project / "svg_output").is_dir():
        die(f"svg_output directory missing: {project / 'svg_output'}")

    output.parent.mkdir(parents=True, exist_ok=True)
    qa_path.parent.mkdir(parents=True, exist_ok=True)

    run([sys.executable, str(scripts / "animation_config.py"), "validate", str(project)])
    run([
        sys.executable,
        str(scripts / "svg_quality_checker.py"),
        str(project),
        "--quick-generate",
        "--stage",
        "final",
        "--json",
    ])
    run([
        sys.executable,
        str(scripts / "svg_to_pptx.py"),
        str(project),
        "--quick-generate",
        "--animation-config",
        animation,
        "--no-notes",
        "-o",
        str(output),
    ])
    if not output.is_file():
        die(f"PPT Master did not generate output: {output}")

    delivery_proc = run(
        [sys.executable, str(scripts / "pptx_delivery_check.py"), str(output)],
        capture=True,
    )
    try:
        delivery = json.loads(delivery_proc.stdout)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"PPT Master delivery check did not return JSON: {exc}") from exc

    run([
        sys.executable,
        str(scripts / "pptx_to_svg.py"),
        str(output),
        "-o",
        str(readback),
        "--inheritance-mode",
        "flat",
    ])

    motion = delivery.get("motion", {}) if isinstance(delivery, dict) else {}
    object_animations = motion.get("object_animations", {}) if isinstance(motion, dict) else {}
    animation_slides = object_animations.get("object_animation_slides", []) if isinstance(object_animations, dict) else []
    evidence = {
        "status": "PASS",
        "mode": "svg-to-pptx",
        "project": project.relative_to(ROOT).as_posix(),
        "output": output.relative_to(ROOT).as_posix(),
        "pptx_sha256": sha256(output),
        "animation_config": animation,
        "native_object_animation_slide_count": len(animation_slides),
        "native_object_animation_slides": animation_slides,
        "delivery": delivery,
        "readback_dir": readback.relative_to(ROOT).as_posix(),
    }
    qa_path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in evidence.items() if k != "delivery"}, ensure_ascii=False, indent=2))
    return evidence


def normalize_pptx(cfg: dict, scripts: Path) -> dict:
    source = safe_path(str(cfg.get("source", "")), "source", must_exist=True)
    output_dir = safe_path(str(cfg.get("output_dir", "")), "output_dir")
    qa_path = safe_path(str(cfg.get("qa", "")), "qa")
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    qa_path.parent.mkdir(parents=True, exist_ok=True)
    run([
        sys.executable,
        str(scripts / "pptx_to_svg.py"),
        str(source),
        "-o",
        str(output_dir),
        "--inheritance-mode",
        "flat",
    ])
    svg_files = sorted((output_dir / "svg").glob("*.svg"))
    if not svg_files:
        die("PPTX normalization produced no SVG pages")
    evidence = {
        "status": "PASS",
        "mode": "normalize-pptx",
        "source": source.relative_to(ROOT).as_posix(),
        "source_sha256": sha256(source),
        "output_dir": output_dir.relative_to(ROOT).as_posix(),
        "svg_pages": len(svg_files),
    }
    qa_path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(evidence, ensure_ascii=False, indent=2))
    return evidence


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    args = ap.parse_args()

    manifest_path = safe_path(args.manifest, "manifest", must_exist=True)
    cfg = json.loads(manifest_path.read_text(encoding="utf-8"))
    if cfg.get("contract_version") != "1":
        die("contract_version must be '1'")
    ppt_master_root = safe_path(str(cfg.get("ppt_master_root", "vendor/ppt-master")), "ppt_master_root", must_exist=True)
    scripts = scripts_root(ppt_master_root)
    mode = cfg.get("mode")
    if mode == "svg-to-pptx":
        svg_to_pptx(cfg, scripts)
    elif mode == "normalize-pptx":
        normalize_pptx(cfg, scripts)
    else:
        die(f"unsupported PPT Master adapter mode: {mode!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
