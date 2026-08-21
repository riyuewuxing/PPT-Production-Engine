#!/usr/bin/env python3
"""Generic historical PPTX -> normalized SVG -> native PPTX migration.

Project-specific meaning enters only as declarative target/semantic text checks.
Executable scripts and the migration sequence remain fixed in the Engine.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path.cwd().resolve()
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"


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
        raise SystemExit(f"{label}: path escapes root") from exc
    if exists and not resolved.exists():
        die(f"{label}: missing {resolved}")
    return resolved


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run(command: list[str], *, capture: bool = False) -> subprocess.CompletedProcess[str]:
    print("+", " ".join(command))
    proc = subprocess.run(command, cwd=ROOT, text=True, encoding="utf-8", errors="replace", capture_output=capture)
    if capture and proc.stdout:
        print(proc.stdout, end="")
    if capture and proc.stderr:
        print(proc.stderr, end="", file=sys.stderr)
    if proc.returncode != 0:
        raise SystemExit(f"command failed ({proc.returncode}): {' '.join(command)}")
    return proc


def scripts_root(ppt_master: Path) -> Path:
    root = ppt_master / "skills" / "ppt-master" / "scripts"
    for name in ("pptx_to_svg.py", "animation_config.py", "svg_quality_checker.py", "svg_to_pptx.py", "pptx_delivery_check.py"):
        if not (root / name).is_file():
            die(f"missing PPT Master script: {name}")
    return root


def natural_key(path: Path) -> tuple[int, str]:
    nums = re.findall(r"\d+", path.stem)
    return (int(nums[-1]) if nums else 10**9, path.name)


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def group_text(group: ET.Element) -> str:
    chunks: list[str] = []
    for node in group.iter():
        if local_name(node.tag) in {"text", "tspan"} and node.text:
            chunks.append(node.text)
    return "".join(chunks).replace("\u00a0", " ").strip()


def direct_groups(svg: Path) -> list[tuple[str, str]]:
    root = ET.parse(svg).getroot()
    rows = []
    for child in list(root):
        if local_name(child.tag) != "g":
            continue
        gid = (child.get("id") or "").strip()
        if gid:
            rows.append((gid, group_text(child)))
    return rows


def find_group(svg: Path, phrase: str) -> str:
    needle = re.sub(r"\s+", "", phrase)
    matches: list[tuple[int, str, str]] = []
    for gid, text in direct_groups(svg):
        normalized = re.sub(r"\s+", "", text)
        if needle and needle in normalized:
            matches.append((len(normalized), gid, text))
    if not matches:
        sample = [f"{gid}:{txt[:60]}" for gid, txt in direct_groups(svg) if txt][:20]
        die(f"animation phrase not found in {svg.name}: {phrase!r}; sample={sample}")
    matches.sort(key=lambda row: (row[0], row[1]))
    return matches[0][1]


def pptx_texts(pptx: Path, slide_count: int) -> dict[int, str]:
    out: dict[int, str] = {}
    with zipfile.ZipFile(pptx) as zf:
        for idx in range(1, slide_count + 1):
            root = ET.fromstring(zf.read(f"ppt/slides/slide{idx}.xml"))
            out[idx] = " ".join((n.text or "") for n in root.iter(f"{{{A_NS}}}t"))
    return out


def svg_text(svg: Path) -> str:
    try:
        root = ET.parse(svg).getroot()
        return " ".join((node.text or "") for node in root.iter() if local_name(node.tag) in {"text", "tspan"})
    except ET.ParseError:
        return svg.read_text(encoding="utf-8", errors="replace")


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", "", value)


def parse_animation_slide_indexes(rows: object) -> list[int]:
    """Normalize PPT Master delivery-check animation slide formats.

    Current PPT Master emits integer slide numbers (for example [7, 15]).
    Older or alternate reports may emit objects. Accept both shapes while
    rejecting booleans and non-positive indexes so QA cannot silently widen.
    """
    if not isinstance(rows, list):
        return []
    indexes: set[int] = set()
    for row in rows:
        value: object = None
        if isinstance(row, int) and not isinstance(row, bool):
            value = row
        elif isinstance(row, dict):
            for key in ("index", "slide", "slide_index"):
                candidate = row.get(key)
                if isinstance(candidate, int) and not isinstance(candidate, bool):
                    value = candidate
                    break
        if isinstance(value, int) and value > 0:
            indexes.add(value)
    return sorted(indexes)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    args = ap.parse_args()
    manifest_path = safe(args.manifest, "manifest", exists=True)
    cfg = json.loads(manifest_path.read_text(encoding="utf-8"))
    if cfg.get("contract_version") != "1" or cfg.get("mode") != "historical-native-migration":
        die("unsupported migration contract")

    source = safe(str(cfg.get("source_pptx", "")), "source_pptx", exists=True)
    output = safe(str(cfg.get("output_pptx", "")), "output_pptx")
    work = safe(str(cfg.get("work_dir", "")), "work_dir")
    qa_dir = safe(str(cfg.get("qa_dir", "")), "qa_dir")
    ppt_master = safe(str(cfg.get("ppt_master_root", "vendor/ppt-master")), "ppt_master_root", exists=True)
    scripts = scripts_root(ppt_master)
    expected_slides = int(cfg.get("expected_slides", 0))
    if expected_slides < 1 or expected_slides > 200:
        die("expected_slides out of range")

    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True, exist_ok=True)
    qa_dir.mkdir(parents=True, exist_ok=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    import_dir = work / "import"
    native_project = work / "native-project"
    readback = work / "final-readback"

    run([sys.executable, str(scripts / "pptx_to_svg.py"), str(source), "-o", str(import_dir), "--inheritance-mode", "flat"])
    imported = sorted((import_dir / "svg").glob("*.svg"), key=natural_key)
    if len(imported) != expected_slides:
        die(f"expected {expected_slides} imported pages, got {len(imported)}")
    svg_out = native_project / "svg_output"
    svg_out.mkdir(parents=True, exist_ok=True)
    roster: dict[int, Path] = {}
    for idx, src in enumerate(imported, start=1):
        dst = svg_out / f"{idx:02d}_{src.stem}.svg"
        shutil.copy2(src, dst)
        roster[idx] = dst

    animation_targets = cfg.get("animation_targets") or {}
    slides_cfg: dict[str, object] = {}
    target_rows = []
    for slide_key, rows in animation_targets.items():
        slide_no = int(slide_key)
        if slide_no not in roster or not isinstance(rows, list):
            die(f"invalid animation target slide: {slide_key}")
        groups = {}
        used = set()
        for order, item in enumerate(rows, start=1):
            phrase = str(item.get("phrase", ""))
            gid = find_group(roster[slide_no], phrase)
            if gid in used:
                die(f"animation target collision on slide {slide_no}: {gid}")
            used.add(gid)
            groups[gid] = {
                "effect": str(item.get("effect", "entrance_fade")),
                "trigger": str(item.get("trigger", "on-click")),
                "order": int(item.get("order", order)),
                "duration": float(item.get("duration", 0.28)),
            }
            target_rows.append({
                "slide": slide_no,
                "semantic_id": item.get("semantic_id"),
                "phrase": phrase,
                "group_id": gid,
                **groups[gid],
            })
        slides_cfg[roster[slide_no].stem] = {"groups": groups}

    animations = {
        "version": 1,
        "defaults": {"transition": {"effect": "fade", "duration": 0.4}},
        "slides": slides_cfg,
    }
    (native_project / "animations.json").write_text(json.dumps(animations, ensure_ascii=False, indent=2), encoding="utf-8")
    (qa_dir / "animation-target-map.json").write_text(json.dumps({"status": "CONFIGURED", "targets": target_rows}, ensure_ascii=False, indent=2), encoding="utf-8")

    run([sys.executable, str(scripts / "animation_config.py"), "validate", str(native_project)])
    run([sys.executable, str(scripts / "svg_quality_checker.py"), str(native_project), "--quick-generate", "--stage", "final", "--json"])
    run([sys.executable, str(scripts / "svg_to_pptx.py"), str(native_project), "--quick-generate", "--animation-config", "animations.json", "--no-notes", "-o", str(output)])
    if not output.is_file():
        die("native migration did not produce final PPTX")

    delivery_proc = run([sys.executable, str(scripts / "pptx_delivery_check.py"), str(output)], capture=True)
    try:
        delivery = json.loads(delivery_proc.stdout)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"delivery check JSON parse failure: {exc}") from exc
    (qa_dir / "ppt-master-delivery-check.json").write_text(json.dumps(delivery, ensure_ascii=False, indent=2), encoding="utf-8")

    run([sys.executable, str(scripts / "pptx_to_svg.py"), str(output), "-o", str(readback), "--inheritance-mode", "flat"])
    final_svgs = sorted((readback / "svg").glob("*.svg"), key=natural_key)
    if len(final_svgs) != expected_slides:
        die(f"expected {expected_slides} final readback SVG pages, got {len(final_svgs)}")

    motion = delivery.get("motion", {}) if isinstance(delivery, dict) else {}
    obj = motion.get("object_animations", {}) if isinstance(motion, dict) else {}
    anim_slides = obj.get("object_animation_slides", []) if isinstance(obj, dict) else []
    actual_anim_indexes = parse_animation_slide_indexes(anim_slides)
    required_anim_indexes = sorted(int(key) for key in animation_targets)
    animation_pass = set(required_anim_indexes).issubset(actual_anim_indexes)

    texts = pptx_texts(output, expected_slides)
    formula_results = []
    for check in cfg.get("text_checks", []):
        slide = int(check["slide"])
        phrase = str(check["text"])
        present = normalize_text(phrase) in normalize_text(texts.get(slide, ""))
        formula_results.append({"slide": slide, "text": phrase, "present": present})

    semantic_results = []
    semantic_pass = True
    semantic_cfg = cfg.get("semantic_checks") or {}
    for slide_key, required in semantic_cfg.items():
        slide = int(slide_key)
        actual = svg_text(final_svgs[slide - 1])
        missing = [str(item) for item in required if normalize_text(str(item)) not in normalize_text(actual)]
        row_pass = not missing
        semantic_pass = semantic_pass and row_pass
        semantic_results.append({"slide": slide, "status": "PASS" if row_pass else "FAIL", "required": required, "missing": missing})
    (qa_dir / "semantic-readback-qa.json").write_text(json.dumps({"status": "PASS" if semantic_pass else "FAIL", "slides": semantic_results}, ensure_ascii=False, indent=2), encoding="utf-8")

    text_pass = all(row["present"] for row in formula_results)
    overall = animation_pass and text_pass and semantic_pass
    evidence = {
        "status": "PASS" if overall else "FAIL",
        "source_pptx": source.relative_to(ROOT).as_posix(),
        "source_pptx_sha256": sha256(source),
        "output_pptx": output.relative_to(ROOT).as_posix(),
        "output_pptx_sha256": sha256(output),
        "expected_slides": expected_slides,
        "required_object_animation_slides": required_anim_indexes,
        "actual_object_animation_slides": actual_anim_indexes,
        "native_object_animation_pass": animation_pass,
        "text_checks": formula_results,
        "semantic_readback_pass": semantic_pass,
        "ppt_master_commit": cfg.get("ppt_master_commit"),
    }
    (qa_dir / "migration-qa.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(evidence, ensure_ascii=False, indent=2))
    if not overall:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())