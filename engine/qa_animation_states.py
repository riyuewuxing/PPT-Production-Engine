#!/usr/bin/env python3
"""Render and verify presenter-paced animation states for native PPTX candidates.

The engine keeps animation QA split into two independent claims:
1. authored-state evidence: every click state can be rendered from the exact
   semantic SVG groups referenced by animations.json;
2. native-package evidence: the generated PPTX contains the same number and
   order of on-click entrance effects on the expected slides.

This does not claim target-player acceptance. PowerPoint Desktop playback is a
separate final gate because LibreOffice/static SVG rendering cannot prove the
Microsoft PowerPoint animation runtime.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

ROOT = Path.cwd().resolve()
SVG_NS = "http://www.w3.org/2000/svg"
P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
NS = {"p": P_NS, "a": A_NS}
ET.register_namespace("", SVG_NS)


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


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def run(command: list[str]) -> None:
    proc = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
    )
    if proc.stdout:
        print(proc.stdout, end="")
    if proc.stderr:
        print(proc.stderr, end="")
    if proc.returncode != 0:
        raise SystemExit(f"command failed ({proc.returncode}): {' '.join(command)}")


def render_svg(svg: Path, png: Path, *, width: int) -> None:
    converter = shutil.which("rsvg-convert")
    if not converter:
        die("rsvg-convert is required for animation-state rendering")
    png.parent.mkdir(parents=True, exist_ok=True)
    run([
        converter,
        "-w",
        str(width),
        "--background-color",
        "#FFFFFF",
        str(svg),
        "-o",
        str(png),
    ])
    if not png.is_file() or png.stat().st_size < 500:
        die(f"animation-state PNG missing or too small: {png}")


def ordered_groups(slide_cfg: dict, *, slide_key: str) -> list[tuple[str, dict]]:
    groups = slide_cfg.get("groups")
    if not isinstance(groups, dict) or not groups:
        die(f"{slide_key}: animations config requires non-empty groups")
    rows: list[tuple[str, dict]] = []
    for group_id, spec in groups.items():
        if not isinstance(group_id, str) or not group_id:
            die(f"{slide_key}: invalid animation group id")
        if not isinstance(spec, dict):
            die(f"{slide_key}.{group_id}: animation spec must be an object")
        order = spec.get("order")
        if not isinstance(order, int) or order < 1:
            die(f"{slide_key}.{group_id}: order must be a positive integer")
        if spec.get("trigger") != "on-click":
            die(f"{slide_key}.{group_id}: state QA v1 supports trigger='on-click' only")
        rows.append((group_id, spec))
    rows.sort(key=lambda item: item[1]["order"])
    orders = [item[1]["order"] for item in rows]
    if orders != list(range(1, len(rows) + 1)):
        die(f"{slide_key}: animation orders must be contiguous 1..N; got {orders}")
    return rows


def slide_number(slide_key: str) -> int:
    match = re.match(r"^(\d+)-", slide_key)
    if not match:
        die(f"animation slide key must start with numeric slide index: {slide_key!r}")
    return int(match.group(1))


def direct_group_lookup(root: ET.Element) -> dict[str, ET.Element]:
    return {
        child.get("id", ""): child
        for child in list(root)
        if local_name(child.tag) == "g" and child.get("id")
    }


def native_target_summary(slide_root: ET.Element, spid: str) -> dict:
    for element in slide_root.iter():
        if local_name(element.tag) == "grpSp":
            c_nv = element.find("./p:nvGrpSpPr/p:cNvPr", NS)
            xfrm = element.find("./p:grpSpPr/a:xfrm", NS)
        elif local_name(element.tag) == "sp":
            c_nv = element.find("./p:nvSpPr/p:cNvPr", NS)
            xfrm = element.find("./p:spPr/a:xfrm", NS)
        else:
            continue
        if c_nv is None or c_nv.get("id") != spid:
            continue
        texts = [node.text for node in element.findall(".//a:t", NS) if node.text]
        off = xfrm.find("./a:off", NS) if xfrm is not None else None
        ext = xfrm.find("./a:ext", NS) if xfrm is not None else None
        return {
            "spid": spid,
            "shape_name": c_nv.get("name"),
            "text": texts,
            "off": dict(off.attrib) if off is not None else None,
            "ext": dict(ext.attrib) if ext is not None else None,
        }
    return {"spid": spid, "shape_name": None, "text": [], "off": None, "ext": None}


def native_click_effects(slide_root: ET.Element) -> list[dict]:
    rows: list[dict] = []
    for c_tn in slide_root.findall('.//p:cTn[@nodeType="clickEffect"]', NS):
        targets = c_tn.findall(".//p:spTgt", NS)
        target_ids = [node.get("spid") for node in targets if node.get("spid")]
        unique_targets = list(dict.fromkeys(target_ids))
        target = unique_targets[0] if len(unique_targets) == 1 else None
        set_node = c_tn.find(".//p:set", NS)
        to_node = c_tn.find(".//p:set/p:to/p:strVal", NS)
        effect = c_tn.find(".//p:animEffect", NS)
        duration = c_tn.find(".//p:animEffect/p:cBhvr/p:cTn", NS)
        rows.append({
            "target_spid": target,
            "target_reference_count": len(targets),
            "unique_target_count": len(unique_targets),
            "preset_class": c_tn.get("presetClass"),
            "preset_id": c_tn.get("presetID"),
            "set_visibility": (
                set_node is not None
                and to_node is not None
                and to_node.get("val") == "visible"
            ),
            "transition": effect.get("transition") if effect is not None else None,
            "filter": effect.get("filter") if effect is not None else None,
            "duration_ms": duration.get("dur") if duration is not None else None,
        })
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    args = ap.parse_args()

    manifest_path = safe_path(args.manifest, "manifest", must_exist=True)
    cfg = json.loads(manifest_path.read_text(encoding="utf-8"))
    if cfg.get("contract_version") != "1":
        die("contract_version must be '1'")

    project = safe_path(str(cfg.get("project", "")), "project", must_exist=True)
    pptx = safe_path(str(cfg.get("output", "")), "output", must_exist=True)
    state_dir = safe_path(str(cfg.get("animation_state_dir", "")), "animation_state_dir")
    qa_path = safe_path(str(cfg.get("animation_state_qa", "")), "animation_state_qa")
    animation_name = str(cfg.get("animation_config", "animations.json"))
    render_width = cfg.get("animation_state_render_width", 1600)
    if not isinstance(render_width, int) or render_width < 640 or render_width > 4096:
        die("animation_state_render_width must be an integer in 640..4096")
    if Path(animation_name).is_absolute() or ".." in Path(animation_name).parts:
        die("animation_config must be a safe project-relative filename")
    animation_path = project / animation_name
    if not animation_path.is_file():
        die(f"animation config missing: {animation_path}")

    config = json.loads(animation_path.read_text(encoding="utf-8"))
    slides_cfg = config.get("slides")
    if config.get("version") != 1 or not isinstance(slides_cfg, dict) or not slides_cfg:
        die("animations.json must be version 1 with non-empty slides object")

    if state_dir.exists():
        shutil.rmtree(state_dir)
    state_dir.mkdir(parents=True, exist_ok=True)
    qa_path.parent.mkdir(parents=True, exist_ok=True)

    failures: list[str] = []
    slide_rows: list[dict] = []
    total_states = 0

    try:
        archive = zipfile.ZipFile(pptx)
    except zipfile.BadZipFile as exc:
        raise SystemExit(f"PPTX is not a readable ZIP package: {exc}") from exc

    with archive:
        for slide_key, slide_cfg in slides_cfg.items():
            if not isinstance(slide_cfg, dict):
                die(f"{slide_key}: slide animation config must be an object")
            number = slide_number(slide_key)
            groups = ordered_groups(slide_cfg, slide_key=slide_key)
            source_svg = project / "svg_output" / f"{slide_key}.svg"
            if not source_svg.is_file():
                die(f"{slide_key}: matching SVG missing: {source_svg}")
            try:
                root = ET.parse(source_svg).getroot()
            except ET.ParseError as exc:
                raise SystemExit(f"{slide_key}: invalid SVG XML: {exc}") from exc
            lookup = direct_group_lookup(root)
            missing = [group_id for group_id, _ in groups if group_id not in lookup]
            if missing:
                failures.append(f"{slide_key}: animation groups are not direct root children: {missing}")

            slide_xml_name = f"ppt/slides/slide{number}.xml"
            try:
                slide_root = ET.fromstring(archive.read(slide_xml_name))
            except KeyError:
                failures.append(f"{slide_key}: PPTX missing {slide_xml_name}")
                continue
            effects = native_click_effects(slide_root)
            if len(effects) != len(groups):
                failures.append(
                    f"{slide_key}: native clickEffect count {len(effects)} != config group count {len(groups)}"
                )
            for idx, effect in enumerate(effects, start=1):
                if effect["unique_target_count"] != 1 or not effect["target_spid"]:
                    failures.append(f"{slide_key}: click {idx} does not target exactly one shape")
                if effect["preset_class"] != "entr":
                    failures.append(f"{slide_key}: click {idx} is not an entrance effect")
                if not effect["set_visibility"]:
                    failures.append(f"{slide_key}: click {idx} does not set target visibility to visible")
                if effect["transition"] != "in":
                    failures.append(f"{slide_key}: click {idx} animation transition is not 'in'")
                if idx <= len(groups) and "fade" in str(groups[idx - 1][1].get("effect", "")):
                    if effect["filter"] != "fade":
                        failures.append(f"{slide_key}: click {idx} expected fade filter, got {effect['filter']!r}")

            native_targets = []
            for effect in effects:
                spid = effect.get("target_spid")
                native_targets.append({
                    **effect,
                    "target": native_target_summary(slide_root, spid) if spid else None,
                })

            state_rows: list[dict] = []
            for visible_count in range(0, len(groups) + 1):
                state_root = copy.deepcopy(root)
                state_lookup = direct_group_lookup(state_root)
                hidden_ids = [group_id for group_id, _ in groups[visible_count:]]
                visible_ids = [group_id for group_id, _ in groups[:visible_count]]
                for group_id in hidden_ids:
                    target = state_lookup.get(group_id)
                    if target is None:
                        continue
                    target.set("display", "none")
                state_stem = f"slide-{number:02d}-state-{visible_count:02d}"
                state_svg = state_dir / f"{state_stem}.svg"
                state_png = state_dir / f"{state_stem}.png"
                state_svg.write_text(ET.tostring(state_root, encoding="unicode"), encoding="utf-8")
                render_svg(state_svg, state_png, width=render_width)
                state_rows.append({
                    "state": visible_count,
                    "after_clicks": visible_count,
                    "visible_animation_groups": visible_ids,
                    "hidden_animation_groups": hidden_ids,
                    "svg": state_svg.relative_to(ROOT).as_posix(),
                    "svg_sha256": sha256(state_svg),
                    "png": state_png.relative_to(ROOT).as_posix(),
                    "png_sha256": sha256(state_png),
                })
                total_states += 1

            slide_rows.append({
                "slide": number,
                "slide_key": slide_key,
                "animation_groups_in_click_order": [group_id for group_id, _ in groups],
                "state_count": len(state_rows),
                "states": state_rows,
                "native_click_effect_count": len(effects),
                "native_click_effects": native_targets,
                "native_count_matches_config": len(effects) == len(groups),
            })

    evidence = {
        "status": "PASS" if not failures else "FAIL",
        "contract_version": "1",
        "manifest": manifest_path.relative_to(ROOT).as_posix(),
        "project": project.relative_to(ROOT).as_posix(),
        "animation_config": animation_path.relative_to(ROOT).as_posix(),
        "animation_config_sha256": sha256(animation_path),
        "pptx": pptx.relative_to(ROOT).as_posix(),
        "pptx_sha256": sha256(pptx),
        "animated_slide_count": len(slide_rows),
        "rendered_state_count": total_states,
        "render_width": render_width,
        "slides": slide_rows,
        "failures": failures,
        "target_player_scope": "Pre-target-player state evidence only; Microsoft PowerPoint Desktop playback remains required for final acceptance.",
    }
    qa_path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "status": evidence["status"],
        "pptx_sha256": evidence["pptx_sha256"],
        "animated_slide_count": evidence["animated_slide_count"],
        "rendered_state_count": evidence["rendered_state_count"],
        "failures": failures,
    }, ensure_ascii=False, indent=2))
    if failures:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
