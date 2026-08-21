#!/usr/bin/env python3
"""Normalize legacy negative line extents without changing historical source."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path.cwd().resolve()
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


def die(message: str):
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


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes"}


def toggle_flip(xfrm: ET.Element, attr: str) -> None:
    if truthy(xfrm.get(attr)):
        xfrm.attrib.pop(attr, None)
    else:
        xfrm.set(attr, "1")


def shape_identity(shape: ET.Element) -> tuple[str | None, str | None]:
    node = shape.find(f"./{{{P_NS}}}nvSpPr/{{{P_NS}}}cNvPr")
    if node is None:
        node = shape.find(f"./{{{P_NS}}}nvCxnSpPr/{{{P_NS}}}cNvPr")
    return (node.get("id"), node.get("name")) if node is not None else (None, None)


def normalize_slide_xml(data: bytes, slide_no: int) -> tuple[bytes, list[dict[str, object]]]:
    root = ET.fromstring(data)
    fixes: list[dict[str, object]] = []
    shapes = list(root.findall(f".//{{{P_NS}}}sp")) + list(root.findall(f".//{{{P_NS}}}cxnSp"))
    for shape in shapes:
        sp_pr = shape.find(f"{{{P_NS}}}spPr")
        if sp_pr is None:
            continue
        geom = sp_pr.find(f"{{{A_NS}}}prstGeom")
        if shape.tag == f"{{{P_NS}}}sp" and (geom is None or geom.get("prst") != "line"):
            continue
        xfrm = sp_pr.find(f"{{{A_NS}}}xfrm")
        if xfrm is None:
            continue
        off = xfrm.find(f"{{{A_NS}}}off")
        ext = xfrm.find(f"{{{A_NS}}}ext")
        if off is None or ext is None:
            continue
        try:
            x, y = int(off.get("x", "0")), int(off.get("y", "0"))
            cx, cy = int(ext.get("cx", "0")), int(ext.get("cy", "0"))
        except ValueError:
            continue
        if cx >= 0 and cy >= 0:
            continue

        before = {
            "x": x, "y": y, "cx": cx, "cy": cy,
            "flipH": xfrm.get("flipH"), "flipV": xfrm.get("flipV"),
        }
        if cx < 0:
            off.set("x", str(x + cx))
            ext.set("cx", str(-cx))
            toggle_flip(xfrm, "flipH")
        if cy < 0:
            off.set("y", str(y + cy))
            ext.set("cy", str(-cy))
            toggle_flip(xfrm, "flipV")

        sid, name = shape_identity(shape)
        fixes.append({
            "slide": slide_no,
            "shape_id": sid,
            "shape_name": name,
            "before": before,
            "after": {
                "x": int(off.get("x", "0")), "y": int(off.get("y", "0")),
                "cx": int(ext.get("cx", "0")), "cy": int(ext.get("cy", "0")),
                "flipH": xfrm.get("flipH"), "flipV": xfrm.get("flipV"),
            },
        })

    if not fixes:
        return data, []
    ET.register_namespace("a", A_NS)
    ET.register_namespace("p", P_NS)
    ET.register_namespace("r", R_NS)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True), fixes


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    args = ap.parse_args()
    manifest = safe(args.manifest, "manifest", exists=True)
    cfg = json.loads(manifest.read_text(encoding="utf-8"))
    if cfg.get("contract_version") != "1" or cfg.get("mode") != "legacy-pptx-geometry-normalization":
        die("unsupported geometry-normalization contract")

    source = safe(str(cfg.get("source_pptx", "")), "source_pptx", exists=True)
    output = safe(str(cfg.get("output_pptx", "")), "output_pptx")
    qa = safe(str(cfg.get("qa", "")), "qa")
    output.parent.mkdir(parents=True, exist_ok=True)
    qa.parent.mkdir(parents=True, exist_ok=True)

    fixes: list[dict[str, object]] = []
    with zipfile.ZipFile(source, "r") as zin, zipfile.ZipFile(output, "w") as zout:
        for info in zin.infolist():
            data = zin.read(info.filename)
            match = re.fullmatch(r"ppt/slides/slide(\d+)\.xml", info.filename)
            if match:
                data, rows = normalize_slide_xml(data, int(match.group(1)))
                fixes.extend(rows)
            zout.writestr(info, data)

    with zipfile.ZipFile(output, "r") as check:
        bad = check.testzip()
        if bad:
            die(f"normalized PPTX ZIP integrity failure: {bad}")

    expected = cfg.get("expected_negative_line_fixes")
    count_ok = expected is None or int(expected) == len(fixes)
    evidence = {
        "status": "PASS" if count_ok else "FAIL",
        "source_pptx": source.relative_to(ROOT).as_posix(),
        "source_pptx_sha256": sha256(source),
        "output_pptx": output.relative_to(ROOT).as_posix(),
        "output_pptx_sha256": sha256(output),
        "expected_negative_line_fixes": expected,
        "actual_negative_line_fixes": len(fixes),
        "fixes": fixes,
        "rule": "Only negative line extents are normalized; the hash-pinned historical source remains unchanged.",
    }
    qa.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(evidence, ensure_ascii=False, indent=2))
    return 0 if count_ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
