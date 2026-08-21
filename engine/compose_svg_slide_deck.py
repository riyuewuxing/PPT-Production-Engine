#!/usr/bin/env python3
"""Compose approved SVG assets into deterministic 16:9 full-slide SVGs.

This is a generic presentation runtime. Project meaning enters through a JSON
manifest: source assets, section labels, accent choices, and viewport geometry.
The composer does not alter the internal content geometry of approved assets; it
places it into a full-slide frame with minimal deck-level chrome.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path.cwd().resolve()
SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)
Q = lambda tag: f"{{{SVG_NS}}}{tag}"


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


def svg_text(x: float, y: float, text: str, *, size: float, fill: str, weight: int = 600, anchor: str = "start") -> ET.Element:
    node = ET.Element(Q("text"), {
        "x": str(x), "y": str(y),
        "font-family": "Noto Sans CJK SC, Noto Sans, sans-serif",
        "font-size": str(size), "font-weight": str(weight),
        "fill": fill, "text-anchor": anchor,
        "dominant-baseline": "middle",
    })
    node.text = text
    return node


def combine_transform(prefix: str, existing: str | None) -> str:
    return f"{prefix} {existing}".strip() if existing else prefix


def parse_viewbox(root: ET.Element) -> tuple[float, float, float, float]:
    raw = root.get("viewBox")
    if not raw:
        die("source SVG is missing viewBox")
    vals = [float(v) for v in re.split(r"[, ]+", raw.strip()) if v]
    if len(vals) != 4 or vals[2] <= 0 or vals[3] <= 0:
        die(f"invalid viewBox: {raw!r}")
    return vals[0], vals[1], vals[2], vals[3]


def compose_one(source: Path, output: Path, cfg: dict[str, object], deck: dict[str, object], slide_no: int, total: int) -> dict[str, object]:
    src_root = ET.parse(source).getroot()
    vx, vy, vw, vh = parse_viewbox(src_root)

    slide_w = float(deck.get("slide_width", 1600))
    slide_h = float(deck.get("slide_height", 900))
    viewport = deck.get("viewport") or {}
    x = float(viewport.get("x", 50)); y = float(viewport.get("y", 110))
    w = float(viewport.get("width", 1500)); h = float(viewport.get("height", 700))
    sx, sy = w / vw, h / vh
    if abs(sx - sy) > 1e-6:
        die(f"slide {slide_no}: viewport distorts approved asset ({sx=} {sy=})")

    colors = deck.get("colors") or {}
    bg = str(colors.get("background", "#FFF8EF"))
    ink = str(colors.get("ink", "#203047"))
    muted = str(colors.get("muted", "#607087"))
    line = str(colors.get("line", "#D7DEE7"))
    progress = str(colors.get("progress", "#1F6FEB"))
    accent = str(cfg.get("accent", progress))

    root = ET.Element(Q("svg"), {
        "width": str(int(slide_w)), "height": str(int(slide_h)),
        "viewBox": f"0 0 {int(slide_w)} {int(slide_h)}",
        "data-source-asset": source.name,
        "data-source-asset-sha256": sha256(source),
        "data-slide": str(slide_no),
    })
    ET.SubElement(root, Q("rect"), {
        "x": "0", "y": "0", "width": str(int(slide_w)), "height": str(int(slide_h)),
        "fill": bg,
    })

    section = str(cfg.get("section", ""))
    if section:
        section_node = svg_text(50, 56, section, size=23, fill=accent, weight=800)
        section_node.set("id", "deck-section-label")
        root.append(section_node)
    page_node = svg_text(slide_w - 50, 56, f"{slide_no:02d} / {total:02d}", size=18, fill=muted, weight=700, anchor="end")
    page_node.set("id", "deck-page-number")
    root.append(page_node)

    prefix = f"translate({x} {y}) scale({sx} {sy}) translate({-vx} {-vy})"
    for child in list(src_root):
        if child.tag == Q("defs"):
            root.append(copy.deepcopy(child))
            continue
        node = copy.deepcopy(child)
        node.set("transform", combine_transform(prefix, node.get("transform")))
        root.append(node)

    bar_x, bar_y, bar_w, bar_h = 50.0, slide_h - 38.0, slide_w - 100.0, 6.0
    ET.SubElement(root, Q("rect"), {
        "x": str(bar_x), "y": str(bar_y), "width": str(bar_w), "height": str(bar_h),
        "rx": str(bar_h / 2), "fill": line,
    })
    fill_w = bar_w * slide_no / total
    ET.SubElement(root, Q("rect"), {
        "x": str(bar_x), "y": str(bar_y), "width": f"{fill_w:.3f}", "height": str(bar_h),
        "rx": str(bar_h / 2), "fill": progress,
        "id": "deck-progress",
    })

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(ET.tostring(root, encoding="utf-8", xml_declaration=True))
    return {
        "slide": slide_no,
        "source": source.relative_to(ROOT).as_posix(),
        "source_sha256": sha256(source),
        "output": output.relative_to(ROOT).as_posix(),
        "output_sha256": sha256(output),
        "section": section,
        "accent": accent,
        "scale": sx,
        "viewport": {"x": x, "y": y, "width": w, "height": h},
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    args = ap.parse_args()
    manifest_path = safe(args.manifest, "manifest", exists=True)
    cfg = json.loads(manifest_path.read_text(encoding="utf-8"))
    if cfg.get("contract_version") != "1" or cfg.get("mode") != "approved-svg-assets-to-full-slides":
        die("unsupported slide-composition contract")

    source_dir = safe(str(cfg.get("source_dir", "")), "source_dir", exists=True)
    output_dir = safe(str(cfg.get("output_dir", "")), "output_dir")
    receipt_path = safe(str(cfg.get("receipt", "")), "receipt")
    slides = cfg.get("slides")
    if not isinstance(slides, list) or not slides:
        die("slides must be a non-empty list")
    total = len(slides)
    rows = []
    for expected, item in enumerate(slides, start=1):
        if not isinstance(item, dict) or int(item.get("slide", -1)) != expected:
            die(f"slides must be ordered 1..N; invalid row at {expected}")
        source_name = str(item.get("source", ""))
        if Path(source_name).name != source_name:
            die(f"slide {expected}: source must be a file name")
        source = (source_dir / source_name).resolve()
        if not source.is_file():
            die(f"slide {expected}: missing source {source}")
        output = output_dir / f"slide-{expected:02d}.svg"
        rows.append(compose_one(source, output, item, cfg, expected, total))

    evidence = {
        "status": "PASS",
        "manifest": manifest_path.relative_to(ROOT).as_posix(),
        "slide_count": total,
        "slide_width": cfg.get("slide_width", 1600),
        "slide_height": cfg.get("slide_height", 900),
        "slides": rows,
    }
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(evidence, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
