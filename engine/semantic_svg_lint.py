#!/usr/bin/env python3
"""Project-agnostic semantic SVG geometry preflight.

Generated presentation SVGs may annotate important geometry using `data-*`
attributes. This linter catches deterministic failures before raster render and
human review: container escapes, outside->inside flow failures, and conservation
count mismatches. It deliberately does not attempt subjective visual scoring.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class Box:
    x: float
    y: float
    w: float
    h: float

    @property
    def x2(self) -> float: return self.x + self.w

    @property
    def y2(self) -> float: return self.y + self.h

    def contains_point(self, x: float, y: float, margin: float = 0.0) -> bool:
        return self.x + margin <= x <= self.x2 - margin and self.y + margin <= y <= self.y2 - margin

    def contains_box(self, other: "Box", margin: float = 0.0) -> bool:
        return (
            other.x >= self.x + margin and other.y >= self.y + margin
            and other.x2 <= self.x2 - margin and other.y2 <= self.y2 - margin
        )


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def num(value: str | None, default: float = 0.0) -> float:
    if value is None: return default
    m = re.match(r"\s*(-?\d+(?:\.\d+)?)", value)
    if not m: raise ValueError(f"not a numeric SVG value: {value!r}")
    return float(m.group(1))


def union(boxes: Iterable[Box]) -> Box | None:
    rows = list(boxes)
    if not rows: return None
    x1=min(b.x for b in rows); y1=min(b.y for b in rows)
    x2=max(b.x2 for b in rows); y2=max(b.y2 for b in rows)
    return Box(x1,y1,x2-x1,y2-y1)


def text_box(node: ET.Element) -> Box:
    x=num(node.get("x")); y=num(node.get("y")); size=num(node.get("font-size"),24)
    text="".join(node.itertext()).strip()
    units=sum(0.35 if ch.isspace() else (1.0 if ord(ch)>255 else 0.62) for ch in text)
    w=max(size*0.5, units*size); h=size*1.2
    anchor=node.get("text-anchor","start")
    if anchor=="middle": x-=w/2
    elif anchor=="end": x-=w
    return Box(x,y-h/2,w,h)


def element_box(node: ET.Element | None) -> Box | None:
    if node is None: return None
    override=node.get("data-bbox")
    if override:
        vals=[float(v) for v in re.split(r"[, ]+",override.strip()) if v]
        if len(vals)!=4: raise ValueError(f"{node.get('id')}: data-bbox must be x y w h")
        return Box(*vals)
    tag=local(node.tag)
    if tag=="rect": return Box(num(node.get("x")),num(node.get("y")),num(node.get("width")),num(node.get("height")))
    if tag=="circle":
        cx,cy,r=num(node.get("cx")),num(node.get("cy")),num(node.get("r"))
        return Box(cx-r,cy-r,2*r,2*r)
    if tag=="ellipse":
        cx,cy,rx,ry=num(node.get("cx")),num(node.get("cy")),num(node.get("rx")),num(node.get("ry"))
        return Box(cx-rx,cy-ry,2*rx,2*ry)
    if tag=="line":
        x1,y1,x2,y2=(num(node.get(k)) for k in ("x1","y1","x2","y2"))
        return Box(min(x1,x2),min(y1,y2),abs(x2-x1),abs(y2-y1))
    if tag=="text": return text_box(node)
    if tag in {"g","svg"}:
        return union(b for child in node if (b:=element_box(child)) is not None)
    return None


def point(node: ET.Element, attr: str) -> tuple[float,float] | None:
    raw=node.get(attr)
    if not raw: return None
    vals=[float(v) for v in re.split(r"[, ]+",raw.strip()) if v]
    if len(vals)!=2: raise ValueError(f"{node.get('id')}: {attr} requires two numbers")
    return vals[0],vals[1]


def line_points(node: ET.Element) -> tuple[tuple[float,float],tuple[float,float]] | None:
    a,b=point(node,"data-start"),point(node,"data-end")
    if a and b: return a,b
    if local(node.tag)=="line":
        return ((num(node.get("x1")),num(node.get("y1"))),(num(node.get("x2")),num(node.get("y2"))))
    for child in node.iter():
        if local(child.tag)=="line":
            return ((num(child.get("x1")),num(child.get("y1"))),(num(child.get("x2")),num(child.get("y2"))))
    return None


def lint(path: Path) -> dict[str, object]:
    root=ET.parse(path).getroot()
    nodes={n.get("id"):n for n in root.iter() if n.get("id")}
    failures=[]; checks=[]
    def ok(kind,msg): checks.append({"kind":kind,"status":"PASS","message":msg})
    def bad(kind,msg): failures.append(f"{kind}: {msg}"); checks.append({"kind":kind,"status":"FAIL","message":msg})

    for node in root.iter():
        role=node.get("data-role")
        container_id=node.get("data-container")
        if container_id and role in {"contained-object","particle-set"}:
            cid=nodes.get(container_id); obox=element_box(node); cbox=element_box(cid)
            margin=num(node.get("data-container-margin"),0)
            if obox is None or cbox is None:
                bad("containment",f"cannot resolve {node.get('id')} inside {container_id}")
            elif not cbox.contains_box(obox,margin):
                bad("containment",f"{node.get('id')} extends outside {container_id}")
            else: ok("containment",f"{node.get('id')} inside {container_id}")

        boundary_id=node.get("data-cross-boundary")
        if role=="flow-arrow" and boundary_id:
            bbox=element_box(nodes.get(boundary_id)); pts=line_points(node); margin=num(node.get("data-target-margin"),2)
            if bbox is None or pts is None:
                bad("flow",f"cannot resolve {node.get('id')} / {boundary_id}")
            else:
                start,end=pts
                if bbox.contains_point(*start) or not bbox.contains_point(*end,margin):
                    bad("flow",f"{node.get('id')} must start outside and end inside {boundary_id}")
                else: ok("flow",f"{node.get('id')} crosses {boundary_id} outside->inside")

    conservation: dict[str,list[tuple[str,int]]]={}
    for node in root.iter():
        if node.get("data-role")=="particle-set" and node.get("data-conservation-key"):
            count=sum(1 for x in node.iter() if x.get("data-role")=="particle")
            conservation.setdefault(node.get("data-conservation-key") or "",[]).append((node.get("id") or "<unnamed>",count))
    for key,rows in conservation.items():
        if len(rows)>1 and len({c for _,c in rows})!=1: bad("conservation",f"{key} counts differ: {rows}")
        elif len(rows)>1: ok("conservation",f"{key} counts match: {rows[0][1]}")

    return {"status":"PASS" if not failures else "FAIL","svg":path.as_posix(),"checks":checks,"failures":failures}


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("svg",nargs="+")
    ap.add_argument("--json-out")
    args=ap.parse_args()
    results=[lint(Path(p)) for p in args.svg]
    out={"status":"PASS" if all(x["status"]=="PASS" for x in results) else "FAIL","results":results}
    text=json.dumps(out,ensure_ascii=False,indent=2); print(text)
    if args.json_out: Path(args.json_out).write_text(text,encoding="utf-8")
    return 0 if out["status"]=="PASS" else 2


if __name__=="__main__": raise SystemExit(main())
