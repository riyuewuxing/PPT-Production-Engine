#!/usr/bin/env python3
"""Refine Run002 V3 assets rejected by Assistant visual review.

This script intentionally overwrites only the first-pass assets that failed the
strict Asset PASS review. It keeps the generation project-agnostic at runtime:
all semantic choices live in this public-safe Run002 handoff.
"""
from __future__ import annotations

import html
from pathlib import Path

OUT = Path("dist/run002-v3/assets/svg")
OUT.mkdir(parents=True, exist_ok=True)

C = {
    "ink": "#203047", "muted": "#607087", "blue": "#1F6FEB", "blue2": "#4A90E2",
    "blueFill": "#EAF3FF", "heat": "#F26A3D", "heat2": "#FF8A5C", "heatFill": "#FFF0E8",
    "slate": "#2D4057", "slate2": "#52667E", "green": "#2E8B57", "greenFill": "#E9F7EF",
    "cream": "#FFF8EF", "paper": "#FFFFFF", "line": "#D7DEE7", "soft": "#F4F7FA", "dark": "#172235",
}


def esc(s: object) -> str:
    return html.escape(str(s), quote=True)


def rect(x,y,w,h,fill="none",stroke="none",sw=0,rx=18,extra=""):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" {extra}/>'


def circ(cx,cy,r,fill="none",stroke="none",sw=0,extra=""):
    return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" {extra}/>'


def line(x1,y1,x2,y2,stroke=C["ink"],sw=4,extra=""):
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="{sw}" stroke-linecap="round" {extra}/>'


def path(d,fill="none",stroke=C["ink"],sw=4,extra=""):
    return f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round" {extra}/>'


def text(x,y,s,size=30,fill=C["ink"],weight=600,anchor="start",extra=""):
    return f'<text x="{x}" y="{y}" font-family="Noto Sans CJK SC, Noto Sans, sans-serif" font-size="{size}" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}" dominant-baseline="middle" {extra}>{esc(s)}</text>'


def arrow(x1,y1,x2,y2,color,width=10,ident=""):
    import math
    ang=math.atan2(y2-y1,x2-x1); ln=18+width*0.7
    ax=x2-ln*math.cos(ang-math.pi/7); ay=y2-ln*math.sin(ang-math.pi/7)
    bx=x2-ln*math.cos(ang+math.pi/7); by=y2-ln*math.sin(ang+math.pi/7)
    gid=f' id="{ident}"' if ident else ""
    return f'<g{gid}>{line(x1,y1,x2,y2,color,width)}<polygon points="{x2},{y2} {ax},{ay} {bx},{by}" fill="{color}"/></g>'


def pill(x,y,w,h,label,fill,fg=C["paper"],size=26):
    return f'<g>{rect(x,y,w,h,fill,fill,0,h/2)}{text(x+w/2,y+h/2+1,label,size,fg,700,"middle")}</g>'


def defs():
    return '''<defs>
<filter id="shadow" x="-20%" y="-20%" width="140%" height="140%"><feDropShadow dx="0" dy="8" stdDeviation="10" flood-color="#22354f" flood-opacity="0.12"/></filter>
<linearGradient id="heatGrad" x1="0" x2="1"><stop offset="0" stop-color="#FFB18F"/><stop offset="1" stop-color="#F26A3D"/></linearGradient>
</defs>'''


def wrap(body):
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="560" viewBox="0 0 1200 560">{defs()}{body}</svg>'


def particle_set(x0,y0,coords,hot=False,streak=False,scale=1.0):
    out=[]
    for i,(x,y) in enumerate(coords):
        px=x0+x; py=y0+y
        out.append(circ(px,py,7.5*scale,C["heat"] if hot else C["blue"],C["paper"],2))
        if streak and i % 2 == 0:
            out.append(line(px-14*scale,py+11*scale,px+15*scale,py-10*scale,C["heat2"] if hot else C["blue2"],3*scale,'opacity="0.72"'))
    return "".join(out)


P12=[(0,0),(56,6),(112,-4),(168,10),(224,0),(280,8),(25,63),(82,70),(140,60),(198,73),(255,63),(305,72)]
P8=[(0,0),(60,5),(120,-3),(180,7),(30,60),(90,68),(150,58),(210,66)]
P6=[(0,0),(65,5),(130,-3),(30,62),(95,70),(160,60)]


def chamber(x,y,w,h,piston_x,coords,hot=True,streak=True,ghost_x=None):
    b=[]
    b.append(rect(x,y,w,h,C["paper"],C["slate"],4,22))
    if ghost_x is not None:
        b.append(rect(ghost_x,y+20,24,h-40,"none",C["blue2"],3,10,'stroke-dasharray="9 8" opacity="0.55"'))
    b.append(rect(piston_x,y+18,28,h-36,C["blue"],C["blue"],0,11))
    gas_x=piston_x+45
    b.append(particle_set(gas_x,y+65,coords,hot=hot,streak=streak,scale=.82))
    return "".join(b)


def asset2():
    b=[]
    b.append(text(600,36,'结果都可能升温，但能量跨边界的机制不同',34,C['ink'],700,'middle'))
    b.append(rect(40,80,535,430,C['blueFill'],C['blue'],3,28,'filter="url(#shadow)"'))
    b.append(text(86,122,'路径 A｜做功',30,C['blue'],800)); b.append(text(86,160,'推动边界 → 压缩气体',25,C['ink'],600))
    # compact before/after so the force actually contacts the moving piston
    b.append(text(185,205,'前',22,C['muted'],700,'middle')); b.append(text(425,205,'后',22,C['muted'],700,'middle'))
    b.append(chamber(92,225,190,165,112,[(40,0),(88,10),(45,52),(100,61),(53,103),(112,112)],True,False))
    b.append(chamber(330,225,190,165,385,[(38,0),(72,8),(42,48),(78,58),(45,96),(82,108)],True,True,ghost_x=350))
    b.append(arrow(55,307,112,307,C['blue'],12,'work-force')); b.append(text(58,352,'外界推活塞',24,C['blue'],800))
    b.append(arrow(287,307,378,307,C['blue'],9,'boundary-motion')); b.append(text(333,413,'边界移动',22,C['blue'],700,'middle'))
    b.append(rect(625,80,535,430,C['heatFill'],C['heat'],3,28,'filter="url(#shadow)"'))
    b.append(text(670,122,'路径 B｜热传递',30,C['heat'],800)); b.append(text(670,160,'温度差 → 能量传递',25,C['ink'],600))
    b.append(rect(690,235,130,150,'url(#heatGrad)',C['heat'],2,22)); b.append(text(755,315,'热源',27,C['paper'],800,'middle'))
    b.append(rect(930,225,170,170,C['paper'],C['slate'],4,22)); b.append(particle_set(958,268,[(0,0),(50,7),(100,0),(20,58),(72,66),(120,56)],False,False,.8)); b.append(text(1015,375,'冷系统',25,C['slate'],700,'middle'))
    b.append(arrow(830,310,975,310,C['heat'],12,'heat-path')); b.append(text(875,272,'Q',30,C['heat'],800,'middle'))
    b.append(pill(472,452,256,52,'过程不同',C['slate']))
    return wrap(''.join(b))


def asset5():
    b=[]
    b.append(text(600,36,'做功改变内能：活塞推动边界，气体体积真实减小',34,C['ink'],700,'middle'))
    b.append(text(285,92,'Before',26,C['muted'],800,'middle')); b.append(text(915,92,'After',26,C['muted'],800,'middle'))
    b.append(chamber(70,125,430,300,110,P12,True,False))
    # same 12 particles, compressed into a narrower gas region; old piston position is shown dashed
    compressed=[(0,0),(38,6),(76,-2),(114,8),(152,0),(190,6),(18,62),(55,69),(94,60),(132,72),(170,62),(208,70)]
    b.append(chamber(700,125,430,300,830,compressed,True,True,ghost_x=740))
    b.append(arrow(525,275,675,275,C['blue'],13,'piston-displacement')); b.append(text(600,235,'活塞向右移动',25,C['blue'],800,'middle'))
    b.append(arrow(748,385,830,385,C['blue2'],8,'after-shift')); b.append(text(790,415,'旧位置 → 新位置',21,C['blue'],700,'middle'))
    b.append(pill(175,450,220,55,'同样 12 个粒子',C['soft'],C['slate'],23)); b.append(pill(745,450,220,55,'体积变小',C['blueFill'],C['blue'],24)); b.append(pill(980,450,170,55,'ΔU ↑',C['heat'],C['paper'],26))
    return wrap(''.join(b))


def asset6():
    b=[]
    b.append(text(600,36,'热传递改变内能：温度差驱动能量真正跨越系统边界',34,C['ink'],700,'middle'))
    b.append(rect(90,150,250,250,'url(#heatGrad)',C['heat'],3,32,'filter="url(#shadow)"')); b.append(text(215,250,'高温热源',34,C['paper'],800,'middle')); b.append(text(215,305,'T高',28,C['paper'],700,'middle'))
    b.append(rect(740,125,380,300,C['paper'],C['slate'],5,34,'stroke-dasharray="14 10" filter="url(#shadow)"')); b.append(text(930,165,'冷系统',30,C['slate'],800,'middle'))
    b.append(particle_set(805,225,[(0,0),(62,6),(124,0),(186,8),(28,66),(92,73),(156,64),(218,72)],False,False,.9))
    # arrowhead is deliberately well inside the dashed system boundary
    b.append(arrow(360,275,835,275,C['heat'],15,'heat-path')); b.append(text(555,230,'热传递 Q',30,C['heat'],800,'middle')); b.append(text(760,315,'跨边界',23,C['heat'],800))
    b.append(arrow(835,335,930,335,C['heat2'],7,'micro-response')); b.append(text(890,382,'微观运动增强',23,C['heat'],700,'middle'))
    b.append(pill(865,455,210,55,'ΔU ↑',C['heat'],C['paper'],26))
    return wrap(''.join(b))


def asset9():
    b=[]
    b.append(text(600,36,'快速压缩：Δt 很短，W 明显输入，Q 来不及显著交换',34,C['ink'],700,'middle'))
    b.append(chamber(85,105,385,245,125,P12,True,False))
    comp=[(0,0),(35,5),(70,-2),(105,8),(140,0),(175,6),(18,58),(52,65),(88,56),(123,68),(158,58),(193,66)]
    b.append(chamber(730,105,385,245,840,comp,True,True,ghost_x=770))
    b.append(arrow(500,220,700,220,C['blue'],13,'rapid-compression')); b.append(text(600,180,'快速推进',25,C['blue'],800,'middle'))
    b.append(pill(420,325,175,50,'W：显著',C['blue'])); b.append(pill(605,325,175,50,'Q：≈0',C['soft'],C['slate'],24)); b.append(pill(905,360,165,50,'T ↑  U ↑',C['heat']))
    b.append(line(100,455,1100,455,C['line'],6));
    for x in (100,420,760,1100): b.append(line(x,440,x,470,C['slate2'],4))
    b.append(text(100,505,'0',24,C['muted'],700,'middle')); b.append(text(1100,505,'Δt 很短',24,C['muted'],700,'middle'))
    return wrap(''.join(b))


def mini_box(x,y,w,h,label):
    return rect(x,y,w,h,C['soft'],C['line'],2,16)+text(x+w/2,y+20,label,20,C['muted'],700,'middle')


def asset12():
    b=[]
    b.append(text(600,36,'内能大小取决于“有多少、动多快、微观结构怎样”',34,C['ink'],700,'middle'))
    xs=[40,420,800]; titles=['质量 m','温度 T','物质种类']; cols=[C['slate'],C['heat'],C['blue']]
    for x,title,col in zip(xs,titles,cols):
        b.append(rect(x,92,340,405,C['paper'],C['line'],3,28,'filter="url(#shadow)"')); b.append(text(x+170,128,title,30,col,800,'middle'))
    # Mass: actual few -> many comparison
    b.append(mini_box(70,175,120,165,'少')); b.append(particle_set(90,225,[(0,0),(45,5),(18,52),(63,57),(10,100),(55,105)],False,False,.65))
    b.append(arrow(200,258,250,258,C['slate2'],7)); b.append(text(225,225,'m↑',22,C['slate'],800,'middle'))
    b.append(mini_box(260,175,90,165,'多')); b.append(particle_set(275,218,[(0,0),(30,5),(60,0),(12,38),(42,44),(70,37),(0,78),(30,84),(60,77),(12,112),(42,116),(70,108)],False,False,.53))
    b.append(text(210,420,'粒子更多 → 总账通常更大',22,C['ink'],650,'middle'))
    # Temperature: same count, slow -> fast
    b.append(mini_box(450,175,120,165,'低 T')); b.append(particle_set(472,225,P6,False,False,.62))
    b.append(arrow(580,258,630,258,C['heat'],7)); b.append(text(605,225,'T↑',22,C['heat'],800,'middle'))
    b.append(mini_box(640,175,120,165,'高 T')); b.append(particle_set(662,225,P6,True,True,.62))
    b.append(text(590,420,'同样粒子数，运动更快',22,C['ink'],650,'middle'))
    # Material: two structures A/B, not a fake monotonic transformation
    b.append(mini_box(830,175,120,165,'结构 A')); b.append(circ(860,255,13,C['blue'],C['paper'],2)); b.append(circ(920,255,13,C['blue'],C['paper'],2)); b.append(line(878,255,902,255,C['slate2'],5,'stroke-dasharray="8 7"'))
    b.append(text(975,258,'≠',30,C['muted'],800,'middle'))
    b.append(mini_box(1000,175,120,165,'结构 B')); b.append(circ(1025,230,13,C['heat'],C['paper'],2)); b.append(circ(1088,260,13,C['heat'],C['paper'],2)); b.append(circ(1048,315,13,C['heat'],C['paper'],2)); b.append(line(1040,238,1073,252,C['heat2'],5)); b.append(line(1035,247,1045,300,C['heat2'],5));
    b.append(text(970,420,'微观结构不同 → 势能项不同',22,C['ink'],650,'middle'))
    return wrap(''.join(b))


def asset14():
    b=[]
    b.append(text(600,36,'三个生活装置，都能用“边界 + 通道 + ΔU”解释',34,C['ink'],700,'middle'))
    xs=[45,430,815]; titles=['保温杯','冰箱','刹车']
    for x,title in zip(xs,titles):
        b.append(rect(x,90,340,410,C['paper'],C['line'],3,28,'filter="url(#shadow)"')); b.append(text(x+170,128,title,30,C['slate'],800,'middle'))
    # Thermos: hot liquid system and deliberately weakened outward Q across insulating wall
    b.append(rect(125,190,170,210,C['soft'],C['slate'],5,45)); b.append(rect(158,220,104,145,C['heatFill'],C['heat'],3,30)); b.append(text(210,292,'热水',25,C['heat'],800,'middle'))
    b.append(arrow(262,292,326,292,C['heat2'],6,'thermos-q')); b.append(line(302,260,302,325,C['slate2'],7)); b.append(text(210,440,'隔热层使 Q ↓',24,C['heat'],800,'middle'))
    # Refrigerator: blue work arrow connects to compressor; orange Q is extracted from cold space
    b.append(rect(485,180,145,225,C['blueFill'],C['blue'],4,20)); b.append(text(557,220,'冷藏室',22,C['blue'],800,'middle')); b.append(circ(705,330,38,C['paper'],C['blue'],5)); b.append(text(705,330,'压缩机',18,C['blue'],800,'middle'))
    b.append(pill(470,430,150,48,'外界做功 W',C['blue'],C['paper'],21)); b.append(arrow(620,454,684,350,C['blue'],8,'fridge-work'))
    b.append(arrow(630,280,690,315,C['heat'],7,'fridge-heat')); b.append(text(660,255,'搬运 Q',20,C['heat'],800,'middle'))
    # Brake: mechanical motion enters the contact region; internal energy rises at contact
    b.append(circ(925,285,76,C['soft'],C['slate'],8)); b.append(circ(925,285,30,C['paper'],C['slate2'],5)); b.append(rect(1015,235,45,100,C['heatFill'],C['heat'],4,14)); b.append(arrow(850,185,905,235,C['blue'],8,'brake-motion')); b.append(text(850,160,'机械运动',20,C['blue'],800));
    b.append(circ(1006,285,12,C['heat'],C['paper'],2)); b.append(line(990,265,1020,305,C['heat2'],5)); b.append(text(980,440,'接触摩擦 → U ↑',24,C['heat'],800,'middle'))
    return wrap(''.join(b))


def asset15():
    b=[]
    b.append(text(600,36,'总结：W 与 Q 是并列过程通道，二者都可以改变系统内能',34,C['ink'],700,'middle'))
    b.append(rect(360,130,520,320,C['paper'],C['slate'],5,34,'stroke-dasharray="14 10" filter="url(#shadow)"')); b.append(text(620,165,'系统边界',27,C['slate'],800,'middle'))
    # Both channel arrows end well inside the system and converge on ΔU.
    b.append(pill(55,170,180,58,'做功 W',C['blue'])); b.append(arrow(235,199,500,260,C['blue'],13,'work-path'))
    b.append(pill(55,335,180,58,'热传递 Q',C['heat'])); b.append(arrow(235,364,500,300,C['heat'],13,'heat-path'))
    b.append(pill(500,245,185,70,'ΔU',C['slate'],C['paper'],32)); b.append(text(592,340,'U₂ − U₁',28,C['slate'],800,'middle'))
    b.append(arrow(688,280,790,280,C['slate2'],10,'state-change')); b.append(pill(790,245,170,70,'状态改变',C['dark'],C['paper'],25))
    # Observable result is an interpretation, not an energy-flow arrow.
    b.append(rect(965,225,205,110,C['soft'],C['line'],3,24)); b.append(text(1068,255,'可观察到',20,C['muted'],700,'middle')); b.append(text(1068,300,'温度/状态变化',23,C['dark'],800,'middle'))
    b.append(line(960,280,965,280,C['muted'],4,'stroke-dasharray="6 7"'))
    b.append(text(600,505,'先定边界 → 判断 W / Q → 记入 ΔU → 解释状态变化',26,C['ink'],700,'middle'))
    return wrap(''.join(b))


REFINED = {
    "02-s02-work-vs-heat.svg": asset2(),
    "05-s05-compression-work.svg": asset5(),
    "06-s06-heat-transfer.svg": asset6(),
    "09-s09-fast-compression.svg": asset9(),
    "12-s12-internal-energy-factors.svg": asset12(),
    "14-s14-applications.svg": asset14(),
    "15-s15-synthesis-two-channels.svg": asset15(),
}

for name, svg in REFINED.items():
    (OUT / name).write_text(svg, encoding="utf-8")

print(f"refined {len(REFINED)} strict-review assets")
