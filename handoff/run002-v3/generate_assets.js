const fs = require('fs');
const path = require('path');

const OUT = path.resolve('dist/run002-v3/assets/svg');
fs.mkdirSync(OUT, { recursive: true });

const C = {
  ink:'#203047', muted:'#607087', blue:'#1F6FEB', blue2:'#4A90E2', blueFill:'#EAF3FF',
  heat:'#F26A3D', heat2:'#FF8A5C', heatFill:'#FFF0E8', slate:'#2D4057', slate2:'#52667E',
  green:'#2E8B57', greenFill:'#E9F7EF', yellow:'#F6C85F', cream:'#FFF8EF', paper:'#FFFFFF',
  line:'#D7DEE7', soft:'#F4F7FA', dark:'#172235'
};

const esc = s => String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
const r = (x,y,w,h,fill='none',stroke='none',sw=0,rx=18,extra='') => `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="${rx}" fill="${fill}" stroke="${stroke}" stroke-width="${sw}" ${extra}/>`;
const c = (cx,cy,rr,fill='none',stroke='none',sw=0,extra='') => `<circle cx="${cx}" cy="${cy}" r="${rr}" fill="${fill}" stroke="${stroke}" stroke-width="${sw}" ${extra}/>`;
const l = (x1,y1,x2,y2,stroke=C.ink,sw=4,extra='') => `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${stroke}" stroke-width="${sw}" stroke-linecap="round" ${extra}/>`;
const p = (d,fill='none',stroke=C.ink,sw=4,extra='') => `<path d="${d}" fill="${fill}" stroke="${stroke}" stroke-width="${sw}" stroke-linecap="round" stroke-linejoin="round" ${extra}/>`;
const t = (x,y,text,size=30,fill=C.ink,weight=600,anchor='start',extra='') => `<text x="${x}" y="${y}" font-family="Noto Sans CJK SC, Noto Sans, sans-serif" font-size="${size}" font-weight="${weight}" fill="${fill}" text-anchor="${anchor}" dominant-baseline="middle" ${extra}>${esc(text)}</text>`;
const arrow = (x1,y1,x2,y2,color,width=10,id='') => {
  const ang = Math.atan2(y2-y1,x2-x1), len=18+width*0.7;
  const ax=x2-len*Math.cos(ang-Math.PI/7), ay=y2-len*Math.sin(ang-Math.PI/7);
  const bx=x2-len*Math.cos(ang+Math.PI/7), by=y2-len*Math.sin(ang+Math.PI/7);
  return `<g${id?` id="${id}"`:''}>${l(x1,y1,x2,y2,color,width)}<polygon points="${x2},${y2} ${ax},${ay} ${bx},${by}" fill="${color}"/></g>`;
};
const pill = (x,y,w,h,label,fill,fg=C.paper,size=26) => `<g>${r(x,y,w,h,fill,fill,0,h/2)}${t(x+w/2,y+h/2+1,label,size,fg,700,'middle')}</g>`;
const iconBolt = (x,y,s,color=C.blue) => p(`M ${x} ${y} l ${s*.36} ${-s*.52} h ${-s*.05} l ${s*.15} ${-s*.32} l ${-s*.46} ${s*.05} l ${s*.14} ${-s*.36} l ${-s*.62} ${s*.59} h ${s*.26} l ${-s*.14} ${s*.51} z`, color, color, 1);
const defs = () => `<defs>
  <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%"><feDropShadow dx="0" dy="8" stdDeviation="10" flood-color="#22354f" flood-opacity="0.12"/></filter>
  <linearGradient id="heatGrad" x1="0" x2="1"><stop offset="0" stop-color="#FFB18F"/><stop offset="1" stop-color="#F26A3D"/></linearGradient>
  <linearGradient id="blueGrad" x1="0" x2="1"><stop offset="0" stop-color="#8BC1FF"/><stop offset="1" stop-color="#1F6FEB"/></linearGradient>
</defs>`;
const wrap = (body, bg='transparent') => `<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="560" viewBox="0 0 1200 560">${defs()}${bg!=='transparent'?r(0,0,1200,560,bg,bg,0,0):''}${body}</svg>`;

function particles(cx,cy,cols,rows,dx,dy,hot=false,scale=1){
  let out=''; let n=0;
  for(let j=0;j<rows;j++) for(let i=0;i<cols;i++){
    const px=cx+i*dx+((j%2)*dx*.23), py=cy+j*dy;
    const rr=8*scale; out += c(px,py,rr,hot?C.heat:C.blue,hot?C.paper:C.paper,2);
    if(hot && (n++%2===0)) out += l(px-15*scale,py+13*scale,px+17*scale,py-11*scale,C.heat2,3*scale,'opacity="0.65"');
  }
  return out;
}
function asset1(){
  let b='';
  b += c(600,275,168,C.paper,C.slate,5,'filter="url(#shadow)"');
  b += c(600,275,142,C.soft,'none',0);
  b += particles(522,220,4,3,52,54,false,1.1);
  b += t(600,365,'系统',36,C.slate,800,'middle');
  b += pill(80,85,170,58,'做功 W',C.blue);
  b += arrow(250,114,442,230,C.blue,13,'work-path');
  b += pill(950,85,170,58,'热传递 Q',C.heat);
  b += arrow(950,114,758,230,C.heat,13,'heat-path');
  b += pill(480,470,240,62,'内能改变 ΔU',C.slate);
  b += arrow(600,438,600,470,C.slate,11,'delta-u');
  b += t(600,40,'同样“变热”，能量可以从两条不同通道进入系统',34,C.ink,700,'middle');
  return wrap(b);
}
function piston(x,y,w,h,compressed=false){
  let b='';
  b += r(x,y,w,h,C.paper,C.slate,4,20);
  const px=compressed?x+110:x+35;
  b += r(px,y+18,28,h-36,C.blue,C.blue,0,12);
  b += l(px+28,y+28,px+28,y+h-28,C.slate2,2);
  const start=compressed?px+72:px+105;
  b += particles(start,y+65, compressed?4:5, 3, compressed?52:60, 56,true,0.82);
  return b;
}
function asset2(){
  let b='';
  b += t(600,36,'结果都可能升温，但能量跨边界的机制不同',34,C.ink,700,'middle');
  b += r(40,80,535,430,C.blueFill,C.blue,3,28,'filter="url(#shadow)"');
  b += t(86,122,'路径 A｜做功',30,C.blue,800); b += t(86,160,'推动边界 → 压缩气体',25,C.ink,600);
  b += piston(110,220,355,210,true); b += arrow(60,325,108,325,C.blue,12); b += t(60,370,'外界推活塞',25,C.blue,700);
  b += r(625,80,535,430,C.heatFill,C.heat,3,28,'filter="url(#shadow)"');
  b += t(670,122,'路径 B｜热传递',30,C.heat,800); b += t(670,160,'温度差 → 能量传递',25,C.ink,600);
  b += r(690,235,130,150,'url(#heatGrad)',C.heat,2,22); b += t(755,315,'热源',27,C.paper,800,'middle');
  b += r(930,235,150,150,C.paper,C.slate,4,22); b += particles(955,268,3,2,38,52,false,0.8); b += t(1005,360,'冷系统',25,C.slate,700,'middle');
  b += arrow(830,310,920,310,C.heat,12); b += t(875,275,'Q',30,C.heat,800,'middle');
  b += pill(472,452,256,52,'过程不同',C.slate);
  return wrap(b);
}
function asset3(){
  let b='';
  b += t(600,38,'内能 U：系统内部的“微观能量总账”',34,C.ink,700,'middle');
  b += r(72,92,1056,400,C.paper,C.line,3,30,'filter="url(#shadow)"');
  b += particles(150,160,8,4,88,78,true,1.0);
  // velocity focus
  b += c(260,242,18,C.heat,C.paper,2); b += arrow(260,242,350,190,C.heat,8); b += t(360,190,'分子热运动动能',28,C.heat,800);
  // potential pair focus
  b += c(690,318,18,C.blue,C.paper,2); b += c(805,318,18,C.blue,C.paper,2); b += l(710,318,785,318,C.slate2,5,'stroke-dasharray="10 8"');
  b += t(748,360,'相互作用势能',28,C.blue,800,'middle');
  b += pill(470,410,260,58,'合起来构成 U',C.slate);
  b += arrow(415,260,520,410,C.heat,7); b += arrow(800,375,680,410,C.blue,7);
  return wrap(b);
}
function asset4(){
  let b='';
  b += t(600,36,'先定系统边界，再谈能量从哪里进来',34,C.ink,700,'middle');
  b += r(330,105,540,350,C.paper,C.slate,5,34,'stroke-dasharray="16 12" filter="url(#shadow)"');
  b += t(600,146,'系统边界',28,C.slate,800,'middle'); b += t(600,285,'系统内部',40,C.slate,800,'middle');
  b += t(78,188,'外界',30,C.muted,700); b += t(988,188,'高温外界',30,C.muted,700);
  b += arrow(115,252,460,252,C.blue,14,'work-path'); b += t(160,215,'W',34,C.blue,800);
  b += arrow(1085,342,740,342,C.heat,14,'heat-path'); b += t(1010,305,'Q',34,C.heat,800);
  b += pill(420,387,160,50,'W > 0',C.blue); b += pill(620,387,160,50,'Q > 0',C.heat);
  b += t(168,295,'外界对系统做功',24,C.blue,700); b += t(852,385,'系统吸热',24,C.heat,700);
  return wrap(b);
}
function asset5(){
  let b='';
  b += t(600,36,'做功改变内能：边界被推动，气体被真实压缩',34,C.ink,700,'middle');
  b += t(270,92,'Before',26,C.muted,800,'middle'); b += t(930,92,'After',26,C.muted,800,'middle');
  b += piston(85,125,390,300,false); b += piston(725,125,390,300,true);
  b += arrow(520,275,675,275,C.blue,13,'piston-displacement'); b += t(598,235,'活塞向右移动',25,C.blue,800,'middle');
  b += pill(230,450,220,55,'体积较大',C.soft,C.slate,24); b += pill(750,450,220,55,'体积变小',C.blueFill,C.blue,24);
  b += pill(980,450,170,55,'ΔU ↑',C.heat,C.paper,26);
  return wrap(b);
}
function asset6(){
  let b='';
  b += t(600,36,'热传递改变内能：温度差驱动能量跨越边界',34,C.ink,700,'middle');
  b += r(90,150,250,250,'url(#heatGrad)',C.heat,3,32,'filter="url(#shadow)"'); b += t(215,250,'高温热源',34,C.paper,800,'middle'); b += t(215,305,'T高',28,C.paper,700,'middle');
  b += r(760,125,350,300,C.paper,C.slate,5,34,'stroke-dasharray="14 10" filter="url(#shadow)"'); b += t(935,165,'冷系统',30,C.slate,800,'middle');
  b += particles(815,225,4,3,62,62,false,0.9);
  b += arrow(360,275,735,275,C.heat,15,'heat-path'); b += t(548,230,'热传递 Q',30,C.heat,800,'middle');
  b += t(600,335,'温度差',25,C.muted,700,'middle'); b += p('M 445 360 C 505 420, 635 420, 695 360','none',C.heat2,5,'stroke-dasharray="10 8"');
  b += pill(865,455,210,55,'ΔU ↑',C.heat,C.paper,26);
  return wrap(b);
}
function asset7(){
  let b='';
  b += t(600,36,'两条过程通道，汇入同一个内能账本',34,C.ink,700,'middle');
  b += r(430,145,340,250,C.paper,C.slate,5,34,'filter="url(#shadow)"'); b += t(600,205,'能量账本',30,C.slate,800,'middle'); b += t(600,295,'ΔU',74,C.slate,900,'middle');
  b += pill(85,205,190,62,'做功 W',C.blue); b += arrow(275,236,425,236,C.blue,14,'work-path');
  b += pill(925,310,190,62,'热传递 Q',C.heat); b += arrow(925,341,775,341,C.heat,14,'heat-path');
  b += pill(445,435,310,58,'ΔU = W + Q',C.dark);
  return wrap(b);
}
function asset8(){
  let b='';
  b += t(600,36,'路径不同，状态变化只看初态和末态',34,C.ink,700,'middle');
  b += c(150,285,72,C.paper,C.slate,5,'filter="url(#shadow)"'); b += t(150,268,'初态',24,C.muted,700,'middle'); b += t(150,315,'U₁',36,C.slate,900,'middle');
  b += c(1050,285,72,C.paper,C.slate,5,'filter="url(#shadow)"'); b += t(1050,268,'末态',24,C.muted,700,'middle'); b += t(1050,315,'U₂',36,C.slate,900,'middle');
  b += p('M 225 255 C 430 80, 770 80, 975 255','none',C.blue,13); b += arrow(940,225,975,255,C.blue,13); b += pill(500,105,200,54,'做功路径 W',C.blue);
  b += p('M 225 315 C 430 500, 770 500, 975 315','none',C.heat,13); b += arrow(940,345,975,315,C.heat,13); b += pill(500,420,200,54,'热传递路径 Q',C.heat);
  b += pill(475,255,250,62,'相同 ΔU',C.slate);
  return wrap(b);
}
function asset9(){
  let b='';
  b += t(600,36,'快速压缩：短时间内 W 明显，Q 来不及显著交换',34,C.ink,700,'middle');
  b += l(100,420,1100,420,C.line,6); [100,420,760,1100].forEach(x=>b+=l(x,405,x,435,C.slate2,4));
  b += t(100,470,'0',24,C.muted,700,'middle'); b += t(1100,470,'Δt 很短',24,C.muted,700,'middle');
  b += piston(110,110,310,220,false); b += piston(760,110,310,220,true); b += arrow(455,220,710,220,C.blue,13);
  b += pill(430,325,175,50,'W：显著',C.blue); b += pill(615,325,175,50,'Q：≈0',C.soft,C.slate,24);
  b += pill(905,345,165,50,'T ↑  U ↑',C.heat);
  return wrap(b);
}
function asset10(){
  let b='';
  b += t(600,36,'机械能 → 微观无序运动：用“搅拌”看清能量转化',34,C.ink,700,'middle');
  b += r(360,120,480,330,C.blueFill,C.slate,5,40,'filter="url(#shadow)"');
  b += p('M 430 190 L 430 385 Q 600 460 770 385 L 770 190','none',C.slate,6);
  b += l(600,115,600,330,C.slate,16); b += p('M 515 315 Q 600 250 685 315','none',C.blue,18); b += p('M 515 315 Q 600 380 685 315','none',C.blue,18);
  b += p('M 520 150 C 555 95, 645 95, 680 150','none',C.blue,8); b += arrow(662,132,680,150,C.blue,8);
  b += particles(440,260,6,2,55,72,true,0.78);
  b += pill(80,210,220,60,'机械转动',C.blue); b += arrow(300,240,410,240,C.blue,12);
  b += pill(900,210,220,60,'内能增加',C.heat); b += arrow(790,240,900,240,C.heat,12);
  b += t(600,500,'有序机械运动逐步变成液体内部更无序的微观运动',26,C.ink,700,'middle');
  return wrap(b);
}
function asset11(){
  let b='';
  b += t(600,36,'状态量“属于系统”，过程量“发生在能量跨边界时”',34,C.ink,700,'middle');
  b += r(330,105,540,350,C.paper,C.slate,5,34,'stroke-dasharray="14 10" filter="url(#shadow)"');
  b += t(600,145,'系统此刻的状态',30,C.slate,800,'middle');
  b += pill(430,220,150,58,'温度 T',C.soft,C.slate,25); b += pill(620,220,150,58,'内能 U',C.slate);
  b += arrow(105,260,330,260,C.blue,13); b += t(115,220,'做功 W',28,C.blue,800);
  b += arrow(1095,340,870,340,C.heat,13); b += t(980,300,'热传递 Q',28,C.heat,800);
  b += t(600,420,'W、Q 描述过程；T、U 描述系统状态',27,C.ink,700,'middle');
  return wrap(b);
}
function asset12(){
  let b='';
  b += t(600,36,'内能大小取决于“有多少、动多快、相互作用怎样”',34,C.ink,700,'middle');
  const xs=[45,415,785]; const titles=['质量 m','温度 T','物质种类'];
  xs.forEach((x,i)=>{b+=r(x,95,330,390,C.paper,C.line,3,28,'filter="url(#shadow)"'); b+=t(x+165,132,titles[i],30,i===0?C.slate:(i===1?C.heat:C.blue),800,'middle');});
  b += particles(90,200,4,3,52,55,false,0.72); b += t(210,405,'粒子更多 → 总账通常更大',23,C.ink,650,'middle');
  b += particles(455,200,4,3,52,55,true,0.72); b += t(580,405,'运动更快 → U 增大',23,C.ink,650,'middle');
  b += c(855,250,17,C.blue,C.paper,2); b += c(1015,250,17,C.blue,C.paper,2); b += l(878,250,992,250,C.slate2,8,'stroke-dasharray="10 8"');
  b += c(875,325,17,C.heat,C.paper,2); b += c(995,325,17,C.heat,C.paper,2); b += l(898,325,972,325,C.heat2,8,'stroke-dasharray="4 8"');
  b += t(950,405,'微观结构不同 → 势能不同',23,C.ink,650,'middle');
  return wrap(b);
}
function asset13(){
  let b='';
  b += t(600,36,'判断题：先说理由，再点击揭晓',34,C.ink,700,'middle');
  const ys=[130,225,320,415]; const labs=['A','B','C','D'];
  ys.forEach((y,i)=>{b+=c(95,y,28,i%2===0?C.blueFill:C.heatFill,i%2===0?C.blue:C.heat,3); b+=t(95,y+1,labs[i],24,i%2===0?C.blue:C.heat,800,'middle'); b+=l(145,y,1065,y,C.line,3); b+=r(1090,y-24,58,48,C.soft,C.line,2,14);});
  b += t(600,512,'答案区域保持固定，不因 reveal 改变题干位置',24,C.muted,600,'middle');
  return wrap(b);
}
function asset14(){
  let b='';
  b += t(600,36,'三个生活装置，都能用“边界 + 通道 + ΔU”解释',34,C.ink,700,'middle');
  const xs=[50,430,810]; const titles=['保温杯','冰箱','刹车'];
  xs.forEach((x,i)=>{b+=r(x,95,340,390,C.paper,C.line,3,28,'filter="url(#shadow)"'); b+=t(x+170,132,titles[i],30,C.slate,800,'middle');});
  // thermos
  b += r(150,190,130,210,C.soft,C.slate,5,45); b += r(178,220,74,150,C.paper,C.line,3,28); b += p('M 90 290 C 120 245, 120 335, 150 290','none',C.heat,8,'stroke-dasharray="10 9"'); b += t(220,435,'目标：减小 Q',24,C.heat,800,'middle');
  // fridge
  b += r(520,190,130,220,C.blueFill,C.blue,4,20); b += l(540,260,630,260,C.line,3); b += c(710,310,34,C.blueFill,C.blue,4); b += p('M 650 320 C 675 320, 675 280, 700 280','none',C.blue,7); b += arrow(520,430,650,430,C.blue,9); b += t(600,455,'外界做功 W',24,C.blue,800,'middle');
  // brake
  b += c(910,285,72,C.soft,C.slate,8); b += c(910,285,28,C.paper,C.slate2,5); b += r(1000,235,44,100,C.heatFill,C.heat,4,14); b += arrow(970,285,995,285,C.heat,9); b += t(980,435,'机械能 → U',24,C.heat,800,'middle');
  return wrap(b);
}
function asset15(){
  let b='';
  b += t(600,36,'总结：W 与 Q 是并列过程通道，二者都可以改变 U',34,C.ink,700,'middle');
  b += r(430,155,340,225,C.paper,C.slate,5,34,'stroke-dasharray="14 10" filter="url(#shadow)"'); b += t(600,195,'系统',30,C.slate,800,'middle'); b += pill(500,250,200,64,'内能 U',C.slate);
  b += pill(65,165,190,60,'做功 W',C.blue); b += arrow(255,195,425,235,C.blue,13,'work-path');
  b += pill(65,330,190,60,'热传递 Q',C.heat); b += arrow(255,360,425,300,C.heat,13,'heat-path');
  b += pill(860,210,230,60,'ΔU',C.heat); b += arrow(775,265,855,240,C.slate,12,'delta-u');
  b += pill(860,330,230,60,'温度/状态变化',C.dark); b += arrow(975,275,975,325,C.dark,10,'state-change');
  b += t(600,500,'先定边界 → 判断 W / Q → 记入 ΔU → 解释状态变化',26,C.ink,700,'middle');
  return wrap(b);
}

const assets = [asset1,asset2,asset3,asset4,asset5,asset6,asset7,asset8,asset9,asset10,asset11,asset12,asset13,asset14,asset15];
const names = [
  's01-hero-two-channels','s02-work-vs-heat','s03-internal-energy-micro','s04-system-boundary-paths','s05-compression-work',
  's06-heat-transfer','s07-energy-ledger','s08-same-state-two-paths','s09-fast-compression','s10-stirring-conversion',
  's11-state-vs-process','s12-internal-energy-factors','s13-concept-check','s14-applications','s15-synthesis-two-channels'
];
const requiredText = [
  ['做功 W','热传递 Q','内能改变 ΔU'],
  ['路径 A｜做功','路径 B｜热传递','过程不同'],
  ['内能 U','分子热运动动能','相互作用势能'],
  ['系统边界','W > 0','Q > 0'],
  ['Before','After','ΔU ↑'],
  ['高温热源','热传递 Q','ΔU ↑'],
  ['能量账本','做功 W','热传递 Q','ΔU = W + Q'],
  ['初态','末态','相同 ΔU','做功路径 W','热传递路径 Q'],
  ['快速压缩','W：显著','Q：≈0','T ↑  U ↑'],
  ['机械转动','内能增加','搅拌'],
  ['状态量','过程量','温度 T','内能 U','做功 W','热传递 Q'],
  ['质量 m','温度 T','物质种类'],
  ['判断题','答案区域'],
  ['保温杯','冰箱','刹车'],
  ['做功 W','热传递 Q','内能 U','ΔU','温度/状态变化']
];

const manifest={version:1,canvas:{width:1200,height:560},assets:[]};
assets.forEach((fn,i)=>{
  const filename=`${String(i+1).padStart(2,'0')}-${names[i]}.svg`;
  const svg=fn();
  fs.writeFileSync(path.join(OUT,filename),svg,'utf8');
  manifest.assets.push({slide:i+1,id:names[i],svg:`assets/svg/${filename}`,required_text:requiredText[i]});
});
fs.writeFileSync(path.resolve('dist/run002-v3/assets/asset-manifest.json'),JSON.stringify(manifest,null,2));
console.log(JSON.stringify({status:'ok',assets:assets.length,out:OUT},null,2));
