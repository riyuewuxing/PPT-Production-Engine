#!/usr/bin/env python3
"""Third strict visual refinement for Run002 V3 assets.

Imports the prior deterministic refinement helpers, then fixes residual
connector, containment and semantic-layout defects found by full-size review.
"""
from __future__ import annotations

import refine_failed_assets as b

C=b.C
OUT=b.OUT


def safe_particles(x0,y0,coords,hot=False,streak=False,scale=1.0):
    return b.particle_set(x0,y0,coords,hot=hot,streak=streak,scale=scale)


SAFE12=[(0,0),(42,6),(84,-2),(126,8),(168,0),(210,6),(20,58),(60,65),(102,56),(144,68),(184,58),(220,66)]
SAFE8=[(0,0),(38,5),(76,-2),(114,7),(18,48),(55,55),(92,47),(128,54)]
SAFE6=[(0,0),(34,6),(68,-2),(16,43),(50,50),(82,42)]


def asset1():
    s=[]
    s.append(b.text(600,36,'同样“变热”，能量可以从两条不同通道进入系统',34,C['ink'],700,'middle'))
    s.append(b.circ(600,290,175,C['paper'],C['slate'],5,'filter="url(#shadow)"'))
    s.append(b.circ(600,290,148,C['soft'],'none',0))
    s.append(safe_particles(525,200,[(0,0),(52,6),(104,0),(156,8),(24,54),(78,61),(132,53),(40,108),(94,115),(148,106)],False,False,.9))
    s.append(b.pill(510,330,180,58,'内能 U',C['slate']))
    # Arrowheads are deliberately inside the system, not parked on its boundary.
    s.append(b.pill(65,105,175,58,'做功 W',C['blue'])); s.append(b.arrow(240,134,500,245,C['blue'],13,'work-path'))
    s.append(b.pill(960,105,175,58,'热传递 Q',C['heat'])); s.append(b.arrow(960,134,700,245,C['heat'],13,'heat-path'))
    s.append(b.pill(500,445,200,58,'ΔU 改变',C['dark']))
    s.append(b.text(600,415,'两条过程通道共同改变系统状态',24,C['muted'],700,'middle'))
    return b.wrap(''.join(s))


def mini_chamber(x,y,w,h,piston_x,coords,streak=False,ghost=None):
    return b.chamber(x,y,w,h,piston_x,coords,True,streak,ghost_x=ghost)


def asset2():
    s=[]
    s.append(b.text(600,36,'结果都可能升温，但能量跨边界的机制不同',34,C['ink'],700,'middle'))
    s.append(b.rect(40,80,535,430,C['blueFill'],C['blue'],3,28,'filter="url(#shadow)"'))
    s.append(b.text(86,122,'路径 A｜做功',30,C['blue'],800)); s.append(b.text(86,160,'推动边界 → 压缩气体',25,C['ink'],600))
    s.append(b.text(185,205,'前',22,C['muted'],700,'middle')); s.append(b.text(425,205,'后',22,C['muted'],700,'middle'))
    before=[(0,0),(36,8),(72,0),(18,45),(55,52),(86,44)]
    after=[(0,0),(25,7),(50,0),(12,42),(37,49),(62,41)]
    s.append(mini_chamber(92,225,190,165,112,before,False))
    s.append(mini_chamber(330,225,190,165,385,after,True,ghost=350))
    s.append(b.arrow(55,307,112,307,C['blue'],12,'work-force')); s.append(b.text(77,415,'外界力直接作用在活塞',21,C['blue'],800))
    s.append(b.arrow(287,307,378,307,C['blue'],9,'boundary-motion')); s.append(b.text(333,413,'边界移动',22,C['blue'],700,'middle'))
    s.append(b.rect(625,80,535,430,C['heatFill'],C['heat'],3,28,'filter="url(#shadow)"'))
    s.append(b.text(670,122,'路径 B｜热传递',30,C['heat'],800)); s.append(b.text(670,160,'温度差 → 能量传递',25,C['ink'],600))
    s.append(b.rect(690,235,130,150,'url(#heatGrad)',C['heat'],2,22)); s.append(b.text(755,315,'热源',27,C['paper'],800,'middle'))
    s.append(b.rect(930,225,170,170,C['paper'],C['slate'],4,22)); s.append(safe_particles(958,268,[(0,0),(38,7),(76,0),(18,50),(56,57),(94,49)],False,False,.8)); s.append(b.text(1015,375,'冷系统',25,C['slate'],700,'middle'))
    s.append(b.arrow(820,310,980,310,C['heat'],12,'heat-path')); s.append(b.text(875,272,'Q',30,C['heat'],800,'middle'))
    s.append(b.pill(472,452,256,52,'过程不同',C['slate']))
    return b.wrap(''.join(s))


def asset3():
    s=[]
    s.append(b.text(600,38,'内能 U：系统内部的“微观能量总账”',34,C['ink'],700,'middle'))
    s.append(b.rect(72,92,1056,400,C['paper'],C['line'],3,30,'filter="url(#shadow)"'))
    # Left zone: kinetic contribution. Right zone: interaction potential, kept visually isolated.
    s.append(b.rect(115,145,430,235,C['heatFill'],'none',0,24)); s.append(b.text(330,178,'分子热运动动能',28,C['heat'],800,'middle'))
    s.append(safe_particles(165,230,[(0,0),(70,5),(140,-3),(210,7),(280,0),(35,70),(105,77),(175,68),(245,76)],True,True,.85))
    s.append(b.arrow(330,380,500,430,C['heat'],8,'kinetic-to-u'))
    s.append(b.rect(655,145,430,235,C['blueFill'],'none',0,24)); s.append(b.text(870,178,'分子间相互作用势能',28,C['blue'],800,'middle'))
    s.append(b.circ(780,270,23,C['blue'],C['paper'],2)); s.append(b.circ(955,270,23,C['blue'],C['paper'],2)); s.append(b.line(808,270,927,270,C['slate2'],7,'stroke-dasharray="12 10"')); s.append(b.text(868,318,'距离/结构改变 → 势能改变',22,C['blue'],700,'middle'))
    s.append(b.arrow(870,380,700,430,C['blue'],8,'potential-to-u'))
    s.append(b.pill(480,420,240,58,'合起来构成 U',C['slate']))
    return b.wrap(''.join(s))


def asset5():
    s=[]
    s.append(b.text(600,36,'做功改变内能：活塞推动边界，气体体积真实减小',34,C['ink'],700,'middle'))
    s.append(b.text(285,92,'Before',26,C['muted'],800,'middle')); s.append(b.text(915,92,'After',26,C['muted'],800,'middle'))
    s.append(b.chamber(70,125,430,300,110,SAFE12,True,False))
    compressed=[(0,0),(34,6),(68,-2),(102,8),(136,0),(170,6),(16,58),(49,65),(84,56),(118,68),(152,58),(186,66)]
    s.append(b.chamber(700,125,430,300,830,compressed,True,True,ghost_x=740))
    s.append(b.arrow(525,275,675,275,C['blue'],13,'piston-displacement')); s.append(b.text(600,235,'活塞向右移动',25,C['blue'],800,'middle'))
    s.append(b.text(785,392,'虚线 = 原活塞位置',20,C['muted'],700,'middle'))
    s.append(b.pill(175,450,220,55,'同样 12 个粒子',C['soft'],C['slate'],23)); s.append(b.pill(745,450,220,55,'体积变小',C['blueFill'],C['blue'],24)); s.append(b.pill(980,450,170,55,'ΔU ↑',C['heat'],C['paper'],26))
    return b.wrap(''.join(s))


def asset6():
    s=[]
    s.append(b.text(600,36,'热传递改变内能：温度差驱动能量真正跨越系统边界',34,C['ink'],700,'middle'))
    s.append(b.rect(90,150,250,250,'url(#heatGrad)',C['heat'],3,32,'filter="url(#shadow)"')); s.append(b.text(215,250,'高温热源',34,C['paper'],800,'middle')); s.append(b.text(215,305,'T高',28,C['paper'],700,'middle'))
    s.append(b.rect(740,125,380,300,C['paper'],C['slate'],5,34,'stroke-dasharray="14 10" filter="url(#shadow)"')); s.append(b.text(930,165,'冷系统',30,C['slate'],800,'middle'))
    s.append(safe_particles(805,225,[(0,0),(55,6),(110,0),(165,8),(26,62),(82,69),(138,60),(194,68)],False,False,.9))
    # Starts at hot-source boundary and ends well inside system.
    s.append(b.arrow(340,275,835,275,C['heat'],15,'heat-path')); s.append(b.text(555,230,'热传递 Q',30,C['heat'],800,'middle')); s.append(b.text(760,315,'跨边界',23,C['heat'],800))
    s.append(b.arrow(835,345,930,345,C['heat2'],7,'micro-response')); s.append(b.text(890,392,'微观运动增强',23,C['heat'],700,'middle'))
    s.append(b.pill(865,455,210,55,'ΔU ↑',C['heat'],C['paper'],26))
    return b.wrap(''.join(s))


def asset7():
    s=[]
    s.append(b.text(600,36,'两条过程通道，汇入同一个内能账本',34,C['ink'],700,'middle'))
    s.append(b.rect(430,145,340,250,C['paper'],C['slate'],5,34,'filter="url(#shadow)"')); s.append(b.text(600,205,'能量账本',30,C['slate'],800,'middle')); s.append(b.text(600,295,'ΔU',74,C['slate'],900,'middle'))
    s.append(b.pill(85,205,190,62,'做功 W',C['blue'])); s.append(b.arrow(275,236,475,236,C['blue'],14,'work-path'))
    s.append(b.pill(925,310,190,62,'热传递 Q',C['heat'])); s.append(b.arrow(925,341,725,341,C['heat'],14,'heat-path'))
    s.append(b.pill(445,435,310,58,'ΔU = W + Q',C['dark']))
    return b.wrap(''.join(s))


def asset9():
    s=[]
    s.append(b.text(600,36,'快速压缩：Δt 很短，W 明显输入，Q 来不及显著交换',34,C['ink'],700,'middle'))
    s.append(b.chamber(85,105,385,245,125,SAFE12,True,False))
    comp=[(0,0),(32,5),(64,-2),(96,8),(128,0),(160,6),(15,55),(46,62),(78,53),(110,65),(142,55),(174,63)]
    s.append(b.chamber(730,105,385,245,840,comp,True,True,ghost_x=770))
    s.append(b.arrow(500,220,700,220,C['blue'],13,'rapid-compression')); s.append(b.text(600,180,'快速推进',25,C['blue'],800,'middle'))
    s.append(b.pill(395,370,180,50,'W：显著',C['blue'])); s.append(b.pill(590,370,180,50,'Q：≈0',C['soft'],C['slate'],24)); s.append(b.pill(925,370,165,50,'T ↑  U ↑',C['heat']))
    s.append(b.line(100,465,1100,465,C['line'],6));
    for x in (100,420,760,1100): s.append(b.line(x,450,x,480,C['slate2'],4))
    s.append(b.text(100,512,'0',24,C['muted'],700,'middle')); s.append(b.text(1100,512,'Δt 很短',24,C['muted'],700,'middle'))
    return b.wrap(''.join(s))


def asset11():
    s=[]
    s.append(b.text(600,36,'状态量“属于系统”，过程量“发生在能量跨边界时”',34,C['ink'],700,'middle'))
    s.append(b.rect(330,105,540,350,C['paper'],C['slate'],5,34,'stroke-dasharray="14 10" filter="url(#shadow)"')); s.append(b.text(600,145,'系统此刻的状态',30,C['slate'],800,'middle'))
    s.append(b.pill(430,220,150,58,'温度 T',C['soft'],C['slate'],25)); s.append(b.pill(620,220,150,58,'内能 U',C['slate']))
    s.append(b.text(112,220,'做功 W',28,C['blue'],800)); s.append(b.arrow(105,260,500,260,C['blue'],13,'work-path'))
    s.append(b.text(980,300,'热传递 Q',28,C['heat'],800)); s.append(b.arrow(1095,340,800,340,C['heat'],13,'heat-path'))
    s.append(b.text(600,420,'W、Q 描述过程；T、U 描述系统状态',27,C['ink'],700,'middle'))
    return b.wrap(''.join(s))


def asset12():
    s=[]
    s.append(b.text(600,36,'内能大小取决于“有多少、动多快、微观结构怎样”',34,C['ink'],700,'middle'))
    xs=[40,420,800]; titles=['质量 m','温度 T','物质种类']; cols=[C['slate'],C['heat'],C['blue']]
    for x,title,col in zip(xs,titles,cols):
        s.append(b.rect(x,92,340,405,C['paper'],C['line'],3,28,'filter="url(#shadow)"')); s.append(b.text(x+170,128,title,30,col,800,'middle'))
    s.append(b.mini_box(70,175,120,165,'少')); s.append(safe_particles(90,225,SAFE6,False,False,.62))
    s.append(b.arrow(200,258,250,258,C['slate2'],7)); s.append(b.text(225,225,'m↑',22,C['slate'],800,'middle'))
    many=[(0,0),(26,4),(52,0),(78,5),(12,36),(39,42),(66,35),(18,72),(46,78),(74,70),(10,105),(38,110)]
    s.append(b.mini_box(260,175,90,165,'多')); s.append(safe_particles(270,220,many,False,False,.48)); s.append(b.text(210,420,'粒子更多 → 总账通常更大',22,C['ink'],650,'middle'))
    s.append(b.mini_box(450,175,120,165,'低 T')); s.append(safe_particles(470,225,SAFE6,False,False,.58))
    s.append(b.arrow(580,258,630,258,C['heat'],7)); s.append(b.text(605,225,'T↑',22,C['heat'],800,'middle'))
    hot=[(0,0),(30,5),(60,-2),(15,40),(45,47),(75,39)]
    s.append(b.mini_box(640,175,120,165,'高 T')); s.append(safe_particles(660,225,hot,True,True,.56)); s.append(b.text(590,420,'同样粒子数，运动更快',22,C['ink'],650,'middle'))
    s.append(b.mini_box(830,175,120,165,'结构 A')); s.append(b.circ(860,255,13,C['blue'],C['paper'],2)); s.append(b.circ(920,255,13,C['blue'],C['paper'],2)); s.append(b.line(878,255,902,255,C['slate2'],5,'stroke-dasharray="8 7"'))
    s.append(b.text(975,258,'≠',30,C['muted'],800,'middle'))
    s.append(b.mini_box(1000,175,120,165,'结构 B')); s.append(b.circ(1025,230,13,C['heat'],C['paper'],2)); s.append(b.circ(1088,260,13,C['heat'],C['paper'],2)); s.append(b.circ(1048,315,13,C['heat'],C['paper'],2)); s.append(b.line(1040,238,1073,252,C['heat2'],5)); s.append(b.line(1035,247,1045,300,C['heat2'],5)); s.append(b.text(970,420,'微观结构不同 → 势能项不同',22,C['ink'],650,'middle'))
    return b.wrap(''.join(s))


def asset15():
    s=[]
    s.append(b.text(600,36,'总结：W 与 Q 是并列过程通道，二者都可以改变系统内能',34,C['ink'],700,'middle'))
    s.append(b.rect(350,130,550,320,C['paper'],C['slate'],5,34,'stroke-dasharray="14 10" filter="url(#shadow)"')); s.append(b.text(625,165,'系统边界',27,C['slate'],800,'middle'))
    s.append(b.pill(55,170,180,58,'做功 W',C['blue'])); s.append(b.arrow(235,199,505,260,C['blue'],13,'work-path'))
    s.append(b.pill(55,335,180,58,'热传递 Q',C['heat'])); s.append(b.arrow(235,364,505,300,C['heat'],13,'heat-path'))
    s.append(b.pill(500,245,165,70,'ΔU',C['slate'],C['paper'],32)); s.append(b.text(582,345,'内能 U：U₁ → U₂',25,C['slate'],800,'middle'))
    s.append(b.arrow(670,280,715,280,C['slate2'],9,'state-change')); s.append(b.pill(715,245,145,70,'状态改变',C['dark'],C['paper'],23))
    # State remains inside the system; only an interpretation guide reaches the observable box.
    s.append(b.rect(960,225,205,110,C['soft'],C['line'],3,24)); s.append(b.text(1063,255,'可观察到',20,C['muted'],700,'middle')); s.append(b.text(1063,300,'温度/状态变化',23,C['dark'],800,'middle')); s.append(b.line(860,280,955,280,C['muted'],4,'stroke-dasharray="7 7"'))
    s.append(b.text(600,505,'先定边界 → 判断 W / Q → 记入 ΔU → 解释状态变化',26,C['ink'],700,'middle'))
    return b.wrap(''.join(s))


REFINED={
    '01-s01-hero-two-channels.svg':asset1(),
    '02-s02-work-vs-heat.svg':asset2(),
    '03-s03-internal-energy-micro.svg':asset3(),
    '05-s05-compression-work.svg':asset5(),
    '06-s06-heat-transfer.svg':asset6(),
    '07-s07-energy-ledger.svg':asset7(),
    '09-s09-fast-compression.svg':asset9(),
    '11-s11-state-vs-process.svg':asset11(),
    '12-s12-internal-energy-factors.svg':asset12(),
    '15-s15-synthesis-two-channels.svg':asset15(),
}
for name,svg in REFINED.items():
    (OUT/name).write_text(svg,encoding='utf-8')
print(f'iteration3 refined {len(REFINED)} assets')
