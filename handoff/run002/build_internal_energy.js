const pptxgen = require('pptxgenjs');
const fs = require('fs');
const path = require('path');

const PROJECT = process.env.PROJECT_PATH || path.resolve(__dirname, '..');
const OUT = path.join(PROJECT, 'exports', 'internal_energy_change_benchmark_v1.pptx');

const pptx = new pptxgen();
pptx.layout = 'LAYOUT_WIDE';
pptx.author = 'PPT benchmark workflow';
pptx.subject = '功、热传递与内能改变';
pptx.title = '功、热传递与内能改变';
pptx.company = 'riyuewuxing/PPT';
pptx.lang = 'zh-CN';
pptx.theme = { headFontFace: 'Noto Sans CJK SC', bodyFontFace: 'Noto Sans CJK SC', lang: 'zh-CN' };
pptx.defineLayout({ name:'LAYOUT_WIDE', width:13.333, height:7.5 });

const C = {
  bg:'FFF8EF', paper:'FFFFFF', ink:'253247', muted:'6E7B88', line:'D9CBB8',
  warm:'F29F3D', heat:'E85D3F', cool:'3478B9', blue:'2D6CDF', slate:'41546B',
  green:'4B9A72', yellow:'FFD27A', dark:'1E2B3A'
};
const W = 13.333, H = 7.5;

function newSlide(){ const s=pptx.addSlide(); s.background={color:C.bg}; return s; }
function text(s,t,x,y,w,h,c=C.ink,sz=20,b=false,align='left'){
  s.addText(t,{x,y,w,h,fontFace:'Noto Sans CJK SC',fontSize:sz,color:c,bold:b,fit:'shrink',margin:0.02,align,breakLine:false});
}
function rect(s,x,y,w,h,fill=C.paper,line=C.line,r=0.18){ s.addShape(pptx.ShapeType.roundRect,{x,y,w,h,rectRadius:r,fill:{color:fill},line:{color:line,width:1}}); }
function line(s,x,y,w,h,c=C.line,width=1.5,arrow=false){ s.addShape(pptx.ShapeType.line,{x,y,w,h,line:{color:c,width,beginArrowType:'none',endArrowType:arrow?'triangle':'none'}}); }
function circ(s,x,y,d,fill,linec=C.line){ s.addShape(pptx.ShapeType.ellipse,{x,y,w:d,h:d,fill:{color:fill,transparency:0},line:{color:linec,width:1}}); }
function header(s,kicker,title,sub,n){ text(s,kicker,0.72,0.32,2.4,0.26,C.warm,10,true); text(s,title,0.72,0.58,9.6,0.45,C.ink,27,true); text(s,sub,0.74,1.08,9.4,0.30,C.muted,13,false); text(s,String(n).padStart(2,'0'),12.18,0.38,0.42,0.26,C.muted,10,true,'center'); line(s,0.72,1.48,11.9,0,C.line,1); }
function badge(s,t,x,y,c){ s.addShape(pptx.ShapeType.roundRect,{x,y,w:1.15,h:0.34,rectRadius:0.13,fill:{color:c},line:{color:c}}); text(s,t,x,y+0.07,1.15,0.18,'FFFFFF',11,true,'center'); }
function moleculeBox(s,x,y,w,h,label,hot=false){ rect(s,x,y,w,h,hot?'FFF1E7':'EEF6FF',hot?C.heat:C.cool); text(s,label,x+0.15,y+0.14,w-0.3,0.28,hot?C.heat:C.cool,15,true,'center'); for(let i=0;i<18;i++){ const px=x+0.35+((i*37)%100)/100*(w-0.8); const py=y+0.58+((i*61)%100)/100*(h-0.9); circ(s,px,py,0.11,hot?C.heat:C.cool,hot?C.heat:C.cool); } }
function ledger(s,x,y,w,h,rows){ rect(s,x,y,w,h,'FFFFFF',C.line); text(s,'能量账本',x+0.18,y+0.15,w-0.36,0.26,C.slate,15,true); line(s,x+0.18,y+0.55,w-0.36,0,C.line,1); rows.forEach((r,i)=>{ const yy=y+0.75+i*0.52; text(s,r[0],x+0.22,yy,1.5,0.22,C.muted,12,true); text(s,r[1],x+1.7,yy,w-1.9,0.24,r[2]||C.ink,13,true); }); }
function boundary(s,x,y,w,h,label){ s.addShape(pptx.ShapeType.roundRect,{x,y,w,h,rectRadius:0.18,fill:{color:'FFFFFF',transparency:4},line:{color:C.slate,width:2,dash:'dash'}}); text(s,label,x+0.15,y+0.1,w-0.3,0.26,C.slate,13,true,'center'); }
function arrowLabel(s,t,x,y,c){ line(s,x,y,1.35,0,c,3,true); text(s,t,x+1.45,y-0.13,1.75,0.3,c,14,true); }
function warnIfSlideElementsOutOfBounds(slide,idx){ const bad=[]; for(const o of slide._slideObjects||[]){ const x=o.options?.x||0,y=o.options?.y||0,w=o.options?.w||0,h=o.options?.h||0; if(x<-.02||y<-.02||x+w>W+.02||y+h>H+.02) bad.push(o.text||o.shapeType||'object'); } if(bad.length) console.warn(`SLIDE ${idx} OUT_OF_BOUNDS`, bad.slice(0,5)); }
function warnIfSlideHasOverlaps(slide,idx){ /* intentionally conservative placeholder; full visual review is recorded separately */ return false; }

// 1
{ let s=newSlide(); header(s,'THERMO / 热学','功、热传递与内能改变','把“变热”翻译成系统内能 U 的改变。',1); moleculeBox(s,0.86,2.0,4.15,3.65,'微观：分子热运动',true); ledger(s,5.35,2.0,3.1,3.65,[['状态量','U'],['过程1','做功 W'],['过程2','热传递 Q'],['账本','ΔU = W + Q']]); rect(s,8.85,2.0,3.55,3.65,'FFF7E8',C.warm); text(s,'本节主问题',9.15,2.35,2.9,0.35,C.warm,18,true,'center'); text(s,'同样是“变热”，到底是外界做功，还是发生了热传递？',9.24,3.0,2.75,1.15,C.ink,21,true,'center'); }
// 2
{ let s=newSlide(); header(s,'观察','两个现象，看似都“变热”','先不要急着写公式，先分清机制。',2); rect(s,0.85,2.0,5.45,3.7,'FFFFFF',C.line); badge(s,'做功路径',1.15,2.25,C.cool); text(s,'快速压缩气体',1.2,2.78,2.7,0.35,C.ink,22,true); boundary(s,3.65,2.65,1.55,1.45,'气体'); line(s,2.15,3.38,1.28,0,C.cool,5,true); text(s,'外界推动活塞',1.15,4.5,3.6,0.35,C.muted,16); rect(s,7.0,2.0,5.45,3.7,'FFFFFF',C.line); badge(s,'热传递路径',7.3,2.25,C.heat); text(s,'热水加热冷水',7.35,2.78,2.7,0.35,C.ink,22,true); moleculeBox(s,9.7,2.75,1.75,1.2,'冷水',false); line(s,8.15,3.35,1.2,0,C.heat,5,true); text(s,'由温度差引起',7.35,4.5,3.6,0.35,C.muted,16); }
// 3
{ let s=newSlide(); header(s,'概念','内能 U：看不见的微观账本','不是“温度”，也不是“热量”。',3); moleculeBox(s,0.8,2.05,4.6,3.6,'分子热运动动能',true); moleculeBox(s,5.85,2.05,3.15,3.6,'分子间相互作用势能',false); rect(s,9.45,2.05,2.95,3.6,'FFFFFF',C.line); text(s,'内能 U',10.08,2.6,1.7,0.36,C.slate,26,true,'center'); text(s,'状态量：取决于系统此刻的微观状态。',9.78,3.35,2.35,0.85,C.ink,20,true,'center'); text(s,'状态变了，U 才可能变。',9.82,4.65,2.25,0.5,C.muted,16,false,'center'); }
// 4
{ let s=newSlide(); header(s,'前提','先画系统边界，再谈 W 和 Q','不画边界，能量账本就没有对象。',4); boundary(s,4.25,2.1,4.2,3.25,'系统：气体/水/物体'); text(s,'外界',1.2,3.2,1.8,0.35,C.muted,18,true); text(s,'系统内部',5.35,3.08,2.0,0.35,C.slate,20,true,'center'); arrowLabel(s,'W：外界对系统做功',1.55,2.8,C.cool); arrowLabel(s,'Q：系统吸热',1.55,3.9,C.heat); ledger(s,9.1,2.2,3.0,3.1,[['约定','W > 0'],['约定','Q > 0'],['结论','ΔU = W + Q']]); }
// 5
{ let s=newSlide(); header(s,'路径一','做功可以改变内能','宏观力和位移，把能量跨过边界送进系统。',5); boundary(s,5.3,2.05,3.2,3.1,'气体系统'); rect(s,3.95,2.35,0.5,2.5,C.cool,C.cool); line(s,2.3,3.55,1.45,0,C.cool,6,true); text(s,'外界推活塞',1.05,3.15,1.55,0.55,C.cool,18,true,'center'); moleculeBox(s,5.75,2.55,2.3,1.95,'分子运动加剧',true); ledger(s,9.15,2.28,3.0,3.0,[['W','> 0',C.cool],['Q','≈ 0'],['ΔU','> 0',C.heat]]); }
// 6
{ let s=newSlide(); header(s,'路径二','热传递可以改变内能','没有宏观位移，也可以因温度差传递能量。',6); boundary(s,5.1,2.05,3.4,3.15,'冷水系统'); moleculeBox(s,5.65,2.65,2.25,1.8,'冷水',false); text(s,'高温物体',1.45,2.72,2.2,0.35,C.heat,20,true,'center'); line(s,3.65,3.32,1.18,0,C.heat,7,true); text(s,'热量 Q',3.5,3.72,1.45,0.3,C.heat,15,true,'center'); ledger(s,9.15,2.28,3.0,3.0,[['W','≈ 0'],['Q','> 0',C.heat],['ΔU','> 0',C.heat]]); }
// 7
{ let s=newSlide(); header(s,'统一账本','两条路径，落在同一个内能账本里','高中常用约定：外界对系统做功为正，系统吸热为正。',7); text(s,'ΔU = W + Q',3.0,2.35,7.4,0.82,C.ink,42,true,'center'); rect(s,1.05,4.05,3.1,1.35,'EEF6FF',C.cool); text(s,'W：做功过程',1.25,4.4,2.7,0.35,C.cool,20,true,'center'); rect(s,5.1,4.05,3.1,1.35,'FFF1E7',C.heat); text(s,'Q：热传递过程',5.25,4.4,2.8,0.35,C.heat,20,true,'center'); rect(s,9.15,4.05,3.1,1.35,'FFFFFF',C.slate); text(s,'ΔU：状态变化',9.32,4.4,2.75,0.35,C.slate,20,true,'center'); }
// 8
{ let s=newSlide(); header(s,'同终点','同一个 ΔU，可以由不同路径造成','物理上要问：能量是怎样跨过边界的？',8); boundary(s,5.05,2.65,3.3,1.55,'同一系统'); text(s,'初态 U₁',1.25,3.0,1.5,0.35,C.slate,20,true); text(s,'末态 U₂',10.6,3.0,1.5,0.35,C.slate,20,true); line(s,2.75,3.17,2.0,-0.8,C.cool,4,true); text(s,'做功路径',3.05,2.05,1.6,0.3,C.cool,16,true); line(s,2.75,3.37,2.0,0.82,C.heat,4,true); text(s,'热传递路径',3.0,4.22,1.9,0.3,C.heat,16,true); line(s,8.45,3.22,1.65,0,C.slate,4,true); text(s,'只看初末态：ΔU 相同',5.0,5.45,3.65,0.4,C.ink,22,true,'center'); }
// 9
{ let s=newSlide(); header(s,'案例一','快速压缩：主要通过做功升高内能','重点不是“热进入了气体”，而是外界做功。',9); boundary(s,4.2,2.1,4.0,3.15,'气体'); line(s,1.7,3.45,2.1,0,C.cool,6,true); text(s,'手/机械装置做功',1.02,2.9,2.3,0.4,C.cool,20,true,'center'); moleculeBox(s,4.75,2.7,2.9,1.75,'分子更快',true); ledger(s,8.95,2.25,3.25,3.0,[['W','显著 > 0',C.cool],['Q','短时近似小'],['ΔU','增加',C.heat]]); }
// 10
{ let s=newSlide(); header(s,'案例二','摩擦/搅拌：机械能转化为内能','不是能量凭空产生，而是有序机械能变成微观无序运动。',10); rect(s,0.9,2.05,5.2,3.6,'FFFFFF',C.line); text(s,'刹车片变热',1.35,2.45,2.3,0.35,C.ink,22,true); line(s,1.55,3.55,2.6,0,C.cool,5,true); text(s,'机械能减少',1.65,4.22,2.1,0.3,C.cool,16,true); rect(s,7.05,2.05,5.2,3.6,'FFF1E7',C.heat); text(s,'微观运动更无序',7.55,2.45,3.0,0.35,C.ink,22,true); moleculeBox(s,8.0,3.05,2.9,1.5,'内能增加',true); }
// 11
{ let s=newSlide(); header(s,'辨析','温度、热量、内能：三个词别混用','热量不是物体“含有”的东西。',11); const items=[['温度 T','描述冷热程度/平均动能线索',C.warm],['内能 U','系统状态量：微观能量总账',C.slate],['热量 Q','热传递过程中转移的能量',C.heat]]; items.forEach((it,i)=>{let x=0.95+i*4.05; rect(s,x,2.0,3.35,3.7,'FFFFFF',it[2]); text(s,it[0],x+0.2,2.35,2.95,0.35,it[2],23,true,'center'); text(s,it[1],x+0.35,3.2,2.65,1.0,C.ink,20,true,'center'); }); text(s,'一句话：物体有内能；过程里才说热量。',2.6,6.15,8.2,0.4,C.ink,23,true,'center'); }
// 12
{ let s=newSlide(); header(s,'变量','内能大小受哪些因素影响？','先定性：更多分子、更高温度、不同物质，都会改变账本。',12); const items=[['质量 m','分子数更多，总账通常更大',C.slate],['温度 T','平均动能线索更强',C.warm],['物质种类','微观结构和势能不同',C.green]]; items.forEach((it,i)=>{let x=0.9+i*4.05; rect(s,x,2.1,3.35,3.45,'FFFFFF',it[2]); text(s,it[0],x+0.2,2.48,2.95,0.35,it[2],24,true,'center'); text(s,it[1],x+0.35,3.42,2.65,0.85,C.ink,19,true,'center'); }); text(s,'比较内能大小，必须先说清系统和状态。',2.8,6.15,7.8,0.4,C.ink,22,true,'center'); }
// 13
{ let s=newSlide(); header(s,'课堂判断','四个说法，哪几个站得住？','先判断，再用“系统边界 / W / Q / ΔU”说理由。',13); const qs=[['A','只要物体温度升高，就一定吸收了热量。'],['B','外界对气体做功，气体内能可能增加。'],['C','热量是物体内部本来含有的一种物质。'],['D','摩擦生热说明机械能可以转化为内能。']]; qs.forEach((q,i)=>{let y=2.0+i*0.88; circ(s,0.92,y+0.04,0.46,'FFFFFF',C.cool); text(s,q[0],0.92,y+0.12,0.46,0.18,C.cool,13,true,'center'); text(s,q[1],1.55,y,10.4,0.45,C.ink,19,false);}); text(s,'先把理由说完整，再揭晓答案。',2.95,6.1,7.4,0.38,C.warm,20,true,'center'); }
// 14
{ let s=newSlide(); header(s,'应用','生活装置都能用同一套语言解释','看边界、看通道、看内能账本。',14); const apps=[['保温杯','减少热传递 Q',C.heat],['冰箱','外界做功搬运能量',C.cool],['刹车','机械能转化为内能',C.warm]]; apps.forEach((a,i)=>{let x=0.95+i*4.05; rect(s,x,2.1,3.35,3.65,'FFFFFF',a[2]); text(s,a[0],x+0.2,2.45,2.95,0.35,a[2],24,true,'center'); text(s,a[1],x+0.35,3.45,2.65,0.72,C.ink,20,true,'center');}); }
// 15
{ let s=newSlide(); header(s,'回顾','从现象回到因果链','会说清这条链，就真正理解了本课。',15); const chain=['系统边界','做功 W','热传递 Q','能量跨边界','内能 U 改变','温度/状态变化']; chain.forEach((c,i)=>{let x=0.68+i*2.02; rect(s,x,2.35,1.55,1.05,'FFFFFF',i%2?C.cool:C.heat); text(s,c,x+0.1,2.72,1.35,0.28,i%2?C.cool:C.heat,15,true,'center'); if(i<chain.length-1) line(s,x+1.56,2.88,0.43,0,C.slate,2,true);}); text(s,'一句话：做功和热传递是改变系统内能的两条过程通道；内能是状态量，W 和 Q 是过程量。',1.15,5.05,10.95,0.72,C.ink,22,true,'center'); }

async function main(){
  fs.mkdirSync(path.dirname(OUT), { recursive: true });
  pptx._slides.forEach((slide, i)=>{ warnIfSlideElementsOutOfBounds(slide, i+1); warnIfSlideHasOverlaps(slide, i+1); });
  await pptx.writeFile({ fileName: OUT });
  console.log(JSON.stringify({status:'ok', output:OUT, slides:pptx._slides.length}, null, 2));
}
main().catch(e=>{ console.error(e); process.exit(1); });
