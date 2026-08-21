#!/usr/bin/env python3
"""Iteration 6: fix the final two asset-level hard failures.

S1 keeps the internal-energy change fully inside the declared system boundary.
S2 keeps the same gas sample count before/after compression and annotates the
particle sets so future semantic lint can enforce conservation automatically.
"""
from __future__ import annotations

from pathlib import Path
import xml.etree.ElementTree as ET

OUT = Path("dist/run002-v3/assets/svg")
SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)


def q(tag: str) -> str:
    return f"{{{SVG_NS}}}{tag}"


def save(path: Path, root: ET.Element) -> None:
    path.write_bytes(ET.tostring(root, encoding="utf-8", xml_declaration=True))


def fix_s1() -> None:
    path = OUT / "01-s01-hero-two-channels.svg"
    root = ET.parse(path).getroot()
    target_group = None
    for group in root.findall(q("g")):
        if "内能改变 ΔU" in "".join(group.itertext()):
            target_group = group
            break
    if target_group is None:
        raise SystemExit("iteration6 S1: ΔU group not found")
    rect = target_group.find(q("rect"))
    text = target_group.find(q("text"))
    if rect is None or text is None:
        raise SystemExit("iteration6 S1: malformed ΔU group")
    # System circle: cy=280, r=165 => bottom inner limit 445. Keep the full pill
    # comfortably inside, including stroke and anti-aliasing margin.
    rect.set("y", "377")
    rect.set("height", "56")
    rect.set("rx", "28")
    text.set("y", "406")
    target_group.set("id", "internal-change")
    target_group.set("data-role", "contained-object")
    target_group.set("data-container", "system")
    target_group.set("data-container-margin", "8")
    save(path, root)


def remove_direct_particles(container: ET.Element) -> None:
    for child in list(container):
        if child.tag == q("circle") and child.get("data-role") == "particle":
            container.remove(child)


def add_particle_set(root: ET.Element, container_id: str, set_id: str, coords: list[tuple[int, int]], color: str) -> None:
    # The original generator places circles as siblings of the container rect,
    # so create an explicit group after that rect. data-bbox lets generic lint
    # reason about the particle set without guessing text/transform geometry.
    container = next((n for n in root.iter() if n.get("id") == container_id), None)
    if container is None:
        raise SystemExit(f"iteration6 S2: missing {container_id}")
    group = ET.Element(q("g"), {
        "id": set_id,
        "data-role": "particle-set",
        "data-conservation-key": "s02-gas-sample",
        "data-container": container_id,
    })
    xs = [x for x, _ in coords]
    ys = [y for _, y in coords]
    group.set("data-bbox", f"{min(xs)-8} {min(ys)-8} {max(xs)-min(xs)+16} {max(ys)-min(ys)+16}")
    for x, y in coords:
        ET.SubElement(group, q("circle"), {
            "cx": str(x), "cy": str(y), "r": "7",
            "fill": color, "stroke": "#FFFFFF", "stroke-width": "2",
            "data-role": "particle",
        })
    # Place immediately after the container in root order.
    children = list(root)
    idx = children.index(container)
    root.insert(idx + 1, group)


def fix_s2() -> None:
    path = OUT / "02-s02-work-vs-heat.svg"
    root = ET.parse(path).getroot()

    # Remove the six-ish legacy circles that were direct siblings between each
    # work cylinder rect and subsequent shapes. Select by geometric region.
    for child in list(root):
        if child.tag != q("circle") or child.get("data-role") != "particle":
            continue
        cx = float(child.get("cx", "0")); cy = float(child.get("cy", "0"))
        if 82 <= cx <= 540 and 235 <= cy <= 400:
            root.remove(child)

    # Exactly six particles represent the same gas sample in both states.
    before = [(166,286),(218,282),(255,305),(177,345),(224,360),(258,350)]
    after = [(447,282),(486,278),(520,298),(451,342),(490,357),(522,344)]
    add_particle_set(root, "work-before", "s02-gas-before", before, "#1F6FEB")
    add_particle_set(root, "work-after", "s02-gas-after", after, "#F26A3D")

    # Make the two work cylinders explicitly part of one before/after sample.
    for cid in ("work-before", "work-after"):
        node = next(n for n in root.iter() if n.get("id") == cid)
        node.set("data-role", "container")

    save(path, root)


fix_s1()
fix_s2()
print("iteration6 fixed S1 system containment and S2 particle conservation")
