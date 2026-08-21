#!/usr/bin/env python3
"""Iteration 5: redraw the final four assets rejected by strict visual review.

The goal is semantic clarity, not pixel nudging. Important objects also receive
machine-readable data-role relationships so future semantic geometry lint can
validate boundary crossing and containment before human review.
"""
from __future__ import annotations

import html
from pathlib import Path

OUT = Path("dist/run002-v3/assets/svg")
OUT.mkdir(parents=True, exist_ok=True)

C = {
    "ink": "#203047", "muted": "#607087", "blue": "#1F6FEB", "blueFill": "#EAF3FF",
    "heat": "#F26A3D", "heatFill": "#FFF0E8", "slate": "#2D4057", "slate2": "#52667E",
    "paper": "#FFFFFF", "line": "#D7DEE7", "soft": "#F4F7FA", "dark": "#172235",
}


def esc(s: str) -> str:
    return html.escape(str(s), quote=True)


def rect(x, y, w, h, fill="none", stroke="none", sw=0, rx=18, extra=""):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" {extra}/>'


def circle(cx, cy, r, fill="none", stroke="none", sw=0, extra=""):
    return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" {extra}/>'


def line(x1, y1, x2, y2, stroke=C["ink"], sw=4, extra=""):
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="{sw}" stroke-linecap="round" {extra}/>'


def text(x, y, label, size=30, fill=C["ink"], weight=600, anchor="start", extra=""):
    return (
        f'<text x="{x}" y="{y}" font-family="Noto Sans CJK SC, Noto Sans, sans-serif" '
        f'font-size="{size}" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}" '
        f'dominant-baseline="middle" {extra}>{esc(label)}</text>'
    )


def arrow(x1, y1, x2, y2, color, width=10, ident="", extra=""):
    import math
    ang = math.atan2(y2 - y1, x2 - x1)
    length = 18 + width * 0.7
    ax = x2 - length * math.cos(ang - math.pi / 7)
    ay = y2 - length * math.sin(ang - math.pi / 7)
    bx = x2 - length * math.cos(ang + math.pi / 7)
    by = y2 - length * math.sin(ang + math.pi / 7)
    attrs = f' id="{ident}"' if ident else ""
    semantic = f' data-start="{x1},{y1}" data-end="{x2},{y2}" {extra}' if extra else ""
    return (
        f'<g{attrs}{semantic}>'
        f'{line(x1, y1, x2, y2, color, width)}'
        f'<polygon points="{x2},{y2} {ax},{ay} {bx},{by}" fill="{color}"/>'
        f'</g>'
    )


def pill(x, y, w, h, label, fill, fg=C["paper"], size=26, ident="", extra=""):
    attrs = f' id="{ident}"' if ident else ""
    return f'<g{attrs} {extra}>{rect(x,y,w,h,fill,fill,0,h/2)}{text(x+w/2,y+h/2+1,label,size,fg,700,"middle")}</g>'


def particle(cx, cy, color=C["heat"], r=8):
    return circle(cx, cy, r, color, C["paper"], 2, 'data-role="particle"')


def defs():
    return '<defs><filter id="shadow" x="-20%" y="-20%" width="140%" height="140%"><feDropShadow dx="0" dy="8" stdDeviation="10" flood-color="#22354f" flood-opacity="0.10"/></filter></defs>'


def wrap(body: str):
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="560" viewBox="0 0 1200 560">{defs()}{body}</svg>'


def write(name: str, body: str):
    (OUT / name).write_text(wrap(body), encoding="utf-8")


def asset1():
    b = text(600, 38, '同样“变热”，能量可以从两条不同通道进入系统', 34, C['ink'], 700, 'middle')
    b += circle(600, 280, 165, C['paper'], C['slate'], 5, 'id="system" data-role="system-boundary" filter="url(#shadow)"')
    b += circle(600, 280, 138, C['soft'])
    pts = [(530,215),(580,205),(630,215),(680,225),(550,265),(605,260),(660,270),(540,315),(590,325),(645,315),(680,335)]
    for x,y in pts: b += particle(x,y,C['blue'],7)
    b += pill(70, 120, 185, 58, '做功 W', C['blue'])
    b += arrow(255,149,505,245,C['blue'],13,'work-path','data-role="flow-arrow" data-cross-boundary="system"')
    b += pill(945, 120, 185, 58, '热传递 Q', C['heat'])
    b += arrow(945,149,695,245,C['heat'],13,'heat-path','data-role="flow-arrow" data-cross-boundary="system"')
    b += pill(505, 320, 190, 54, '内能 U', C['slate'])
    b += pill(490, 390, 220, 58, '内能改变 ΔU', C['dark'])
    b += text(600, 505, '两条过程通道 → 同一个系统状态变化', 26, C['muted'], 700, 'middle')
    return b


def small_cylinder(x, y, w, h, piston_x, hot=False, ident=''):
    b = rect(x,y,w,h,C['paper'],C['slate'],4,20, f'id="{ident}" data-role="container"' if ident else '')
    b += rect(piston_x,y+18,24,h-36,C['blue'],C['blue'],0,10)
    start = piston_x + 58
    color = C['heat'] if hot else C['blue']
    coords = [(start,y+62),(start+52,y+52),(start+105,y+67),(start+25,y+118),(start+80,y+127),(start+125,y+110)]
    for px,py in coords:
        if px < x+w-20:
            b += particle(px,py,color,7)
    return b


def asset2():
    b = text(600,36,'结果都可能升温，但能量跨边界的机制不同',34,C['ink'],700,'middle')
    # Work panel
    b += rect(38,82,535,430,C['blueFill'],C['blue'],3,28,'filter="url(#shadow)"')
    b += text(84,125,'路径 A｜做功',30,C['blue'],800)
    b += text(84,164,'推动边界 → 压缩气体',25,C['ink'],650)
    b += text(205,215,'前',24,C['muted'],800,'middle')
    b += text(430,215,'后',24,C['muted'],800,'middle')
    b += small_cylinder(82,235,205,165,108,False,'work-before')
    b += small_cylinder(335,235,205,165,395,True,'work-after')
    b += arrow(60,317,105,317,C['blue'],10,'external-force')
    b += arrow(290,317,382,317,C['blue'],10,'boundary-motion')
    b += pill(80,430,195,48,'外界力作用于活塞',C['paper'],C['blue'],21)
    b += pill(325,430,205,48,'活塞推动系统边界',C['paper'],C['blue'],21)
    # Heat panel
    b += rect(625,82,537,430,C['heatFill'],C['heat'],3,28,'filter="url(#shadow)"')
    b += text(670,125,'路径 B｜热传递',30,C['heat'],800)
    b += text(670,164,'温度差 → 能量传递',25,C['ink'],650)
    b += rect(690,245,135,145,C['heat'],C['heat'],0,22)
    b += text(757,315,'热源',27,C['paper'],800,'middle')
    b += rect(930,235,155,165,C['paper'],C['slate'],4,22,'id="cold-system" data-role="system-boundary"')
    for px,py in [(962,275),(1000,282),(1038,272),(978,335),(1018,343),(1050,328)]: b += particle(px,py,C['blue'],7)
    b += arrow(825,315,968,315,C['heat'],12,'heat-transfer','data-role="flow-arrow" data-cross-boundary="cold-system"')
    b += text(875,275,'Q',30,C['heat'],800,'middle')
    b += text(1007,374,'冷系统',24,C['slate'],700,'middle')
    b += pill(490,475,220,48,'过程不同',C['slate'],C['paper'],24)
    return b


def piston_scene(x, y, w, h, piston_x, hot, set_id):
    b = rect(x,y,w,h,C['paper'],C['slate'],4,24, f'id="{set_id}-container" data-role="container"')
    b += rect(piston_x,y+22,28,h-44,C['blue'],C['blue'],0,12, f'id="{set_id}-piston"')
    coords = [(piston_x+52,y+66),(piston_x+96,y+58),(piston_x+140,y+70),(piston_x+184,y+62),(piston_x+225,y+74),(piston_x+70,y+130),(piston_x+116,y+122),(piston_x+160,y+137),(piston_x+205,y+126),(piston_x+245,y+141),(piston_x+95,y+192),(piston_x+185,y+190)]
    color=C['heat'] if hot else C['heat']
    b += f'<g id="{set_id}-gas" data-role="particle-set" data-conservation-key="gas-sample">'
    for px,py in coords:
        if px <= x+w-24 and py <= y+h-24: b += particle(px,py,color,7)
    b += '</g>'
    return b


def asset5():
    b = text(600,36,'做功改变内能：活塞推动边界，气体体积真实减小',34,C['ink'],700,'middle')
    b += text(285,92,'Before',26,C['muted'],800,'middle')
    b += text(920,92,'After',26,C['muted'],800,'middle')
    b += piston_scene(70,125,430,300,110,False,'before')
    b += piston_scene(700,125,430,300,830,True,'after')
    # ghost old piston position, clearly separated from live piston
    b += rect(745,147,28,256,'none','#8BB9F1',3,10,'stroke-dasharray="12 9"')
    b += text(760,448,'虚线：压缩前活塞位置',21,C['muted'],650,'middle')
    b += arrow(525,275,675,275,C['blue'],13,'piston-displacement')
    b += text(600,235,'活塞向右移动',25,C['blue'],800,'middle')
    b += pill(170,475,220,52,'同样 12 个粒子',C['soft'],C['slate'],23)
    b += pill(760,475,205,52,'体积变小',C['blueFill'],C['blue'],23)
    b += pill(985,475,155,52,'ΔU ↑',C['heat'],C['paper'],25)
    return b


def asset11():
    b = text(600,36,'状态量“属于系统”，过程量“发生在能量跨边界时”',34,C['ink'],700,'middle')
    b += rect(335,105,530,390,C['paper'],C['slate'],5,30,'id="state-system" data-role="system-boundary" stroke-dasharray="15 11" filter="url(#shadow)"')
    b += text(600,145,'系统此刻的状态',31,C['slate'],800,'middle')
    b += pill(445,215,145,58,'温度 T',C['soft'],C['slate'],26,'temperature')
    b += pill(610,215,145,58,'内能 U',C['slate'],C['paper'],26,'internal-energy')
    # Process arrows cross the boundary but terminate in a neutral process zone,
    # not at T or U, so they cannot be read as W->T or Q->U.
    b += text(120,305,'做功 W',30,C['blue'],800)
    b += arrow(105,350,435,350,C['blue'],13,'work-process','data-role="flow-arrow" data-cross-boundary="state-system"')
    b += text(950,305,'热传递 Q',30,C['heat'],800)
    b += arrow(1095,350,765,350,C['heat'],13,'heat-process','data-role="flow-arrow" data-cross-boundary="state-system"')
    b += pill(500,325,200,52,'过程发生',C['paper'],C['slate'],23)
    b += text(600,435,'W、Q 描述过程；T、U 描述系统状态',27,C['ink'],750,'middle')
    return b


write('01-s01-hero-two-channels.svg', asset1())
write('02-s02-work-vs-heat.svg', asset2())
write('05-s05-compression-work.svg', asset5())
write('11-s11-state-vs-process.svg', asset11())
print('iteration5 redrew final four strict-review assets')
