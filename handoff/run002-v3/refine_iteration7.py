#!/usr/bin/env python3
"""Iteration 7: make S1 visually and geometrically valid for a circular system.

The previous bbox-only check passed a label whose lower corners crossed the
actual circle. The Engine linter is now shape-aware; this refinement rearranges
particles and the U/Delta-U labels so the full semantic objects sit inside the
circle with visible breathing room.
"""
from pathlib import Path
import xml.etree.ElementTree as ET

SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)
Q = lambda tag: f"{{{SVG_NS}}}{tag}"
path = Path("dist/run002-v3/assets/svg/01-s01-hero-two-channels.svg")
root = ET.parse(path).getroot()

particles = [n for n in root.findall(Q("circle")) if n.get("data-role") == "particle"]
coords = [(545,205),(600,195),(655,205),(525,250),(575,245),(625,250),(675,245),(555,290),(645,290)]
if len(particles) < len(coords):
    raise SystemExit(f"iteration7: expected at least {len(coords)} S1 particles, got {len(particles)}")
for node,(x,y) in zip(particles,coords):
    node.set("cx",str(x)); node.set("cy",str(y))
for node in particles[len(coords):]:
    root.remove(node)

for group in root.findall(Q("g")):
    label = "".join(group.itertext()).strip()
    rect = group.find(Q("rect")); txt = group.find(Q("text"))
    if rect is None or txt is None:
        continue
    if "内能 U" == label:
        rect.set("x","520"); rect.set("y","310"); rect.set("width","160"); rect.set("height","46"); rect.set("rx","23")
        txt.set("x","600"); txt.set("y","334")
    elif "内能改变 ΔU" == label:
        rect.set("x","510"); rect.set("y","360"); rect.set("width","180"); rect.set("height","50"); rect.set("rx","25")
        txt.set("x","600"); txt.set("y","386")
        txt.set("font-size","24")
        group.set("id","internal-change")
        group.set("data-role","contained-object")
        group.set("data-container","system")
        group.set("data-container-margin","3")

path.write_bytes(ET.tostring(root,encoding="utf-8",xml_declaration=True))
print("iteration7 placed S1 particles/U/Delta-U fully inside circular system")
