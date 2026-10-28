const $=s=>document.querySelector(s),$$=s=>document.querySelectorAll(s);
const T=window.__TAURI__,BC=window.BroadcastChannel?new BroadcastChannel('miku'):null;
const emit=m=>{try{BC?.postMessage(m)}catch{}try{T?.event?.emit('miku',m)}catch{}};
const esc=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));

// Ventana movible por la cabecera y redimensionable (responsive 380-1200+ px)
try {
  T?.window?.getCurrentWindow?.()?.setResizable?.(true)?.catch?.(()=>{});
} catch(_) {}

document.addEventListener('DOMContentLoaded', () => {
  // Efecto de sonido suave al abrir la ventana de ajustes
  setTimeout(() => {
    try { window.SoundFX?.open?.(); } catch(_) {}
  }, 120);

  const topChrome = document.querySelector('.top-chrome');
  if (topChrome) {
    topChrome.addEventListener('pointerdown', e => {
      if (e.target.closest('.win-ctrls') || e.target.closest('button')) return;
      try {
        const win = T?.window?.getCurrentWindow?.();
        if (win?.startDragging) win.startDragging().catch(()=>{});
      } catch(_) {}
    });
  }
  const btnMin = document.getElementById('win-min');
  if (btnMin) {
    btnMin.onclick = () => {
      window.SoundFX?.pop?.();
      try {
        const win = T?.window?.getCurrentWindow?.();
        if (win?.minimize) win.minimize().catch(()=>{});
      } catch(_) {}
    };
  }
  const btnCls = document.getElementById('win-cls');
  if (btnCls) {
    btnCls.onclick = () => {
      window.SoundFX?.pop?.();
      try {
        const win = T?.window?.getCurrentWindow?.();
        if (win?.hide) win.hide().catch(()=>{ window.close(); });
        else window.close();
      } catch(_) { window.close(); }
    };
  }
});
const ls={get(k,d){try{const v=localStorage.getItem(k);return v==null?d:JSON.parse(v)}catch{return d}},set(k,v){try{localStorage.setItem(k,JSON.stringify(v))}catch{}}};

/* ───── estado ───── */
const CFG=Object.assign({voice:1,autoclose:15,voice_volume:80,sfx_volume:60,barge_in:1,wake_paused:0,mic:'default',personality:'calm'},ls.get('miku_cfg',{}));
const DEFAULT_AGENTS = [
  { id: 'github', name: 'GitHub', c: '#39D353', role: 'Control de versiones, commits, ramas, pull requests y estado de repositorios', model: 'google/gemini-2.5-flash', hooks: 1, active: 1, isl: 1, outfit: 'shades' },
  { id: 'antigravity', name: 'Antigravity', c: '#00D2FF', role: 'Desarrollo frontend, interfaz reactiva, animación y diseño UI/UX', model: 'google/gemini-2.5-pro', hooks: 1, active: 1, isl: 2, outfit: 'crown' }
];
let AG = [...DEFAULT_AGENTS];
const sa = ls.get('miku_agents', null);
if (Array.isArray(sa) && sa.length) {
  const filtered = sa.filter(a => a.id === 'github' || a.id === 'antigravity' || a.custom);
  if (filtered.length) {
    AG = filtered.map(a => {
      const def = DEFAULT_AGENTS.find(d => d.id === a.id);
      return def ? { ...def, ...a } : a;
    });
  }
}
let STOP2=null,SELID='miku',IMG={},PROUT='none',STOP=null;try{PROUT=localStorage.getItem('miku_outfit')||'none'}catch{}
let EMO='';

// Capturar el ratón para el smooth tracking con consumo de CPU ultra-bajo
let mx = 0, my = 0, smx = 0, smy = 0, PX = -1e4, PY = -1e4, PT = 0;
let mouseInWin = true;
document.addEventListener('mouseenter', () => { mouseInWin = true; });
document.addEventListener('mouseleave', () => { mouseInWin = false; });
document.addEventListener('pointermove', e => { 
  mouseInWin = true;
  PX = e.clientX; 
  PY = e.clientY; 
  PT = performance.now(); 
}, {passive:true});

// Seguimiento global del cursor solo cuando la ventana esté activa y el cursor esté afuera
async function trackGlobalCursor() {
  if (document.hidden || mouseInWin) return;
  if (window.__TAURI__?.core?.invoke) {
    try {
      const [gx, gy] = await window.__TAURI__.core.invoke('get_cursor_position');
      PX = gx - window.screenX;
      PY = gy - window.screenY;
      PT = performance.now();
    } catch (_) {}
  }
}
setInterval(trackGlobalCursor, 120);

const WARDROBE=[['none','Ninguno','-'],['beanie','Gorro','Gorro'],['crown','Corona','Corona'],['party','Fiesta','Fiesta'],['santa','Santa','Navidad'],['witch','Bruja','Bruja'],['shades','Gafas de sol','Gafas'],['round','Gafas','Lentes'],['bow','Moño','Lazo'],['scarf','Bufanda','Bufanda'],['pumpkin','Calabaza','Calabaza'],['bunny','Orejas','Orejas']];
const HAT=Object.fromEntries(WARDROBE.map(([k,,e])=>[k,k=='none'?'':e]));
const GAL=['idle','listening','thinking','talking','searching','working','happy','proud','wink','love','surprised','question','annoyed','sleeping','error','dizzy','look_up','look_down','look_left','look_right','squash','swallow','wave'];
const PRESET=['#F2A765','#F06CF0','#6C63FF','#FF5C66','#4FD3B1','#3B9EFF','#FFD84D','#9BE15D'];
const lum=h=>{const n=parseInt(h.slice(1),16);return(.299*(n>>16)+.587*((n>>8)&255)+.114*(n&255))/255};
const mix=(h,t=.4)=>{const n=parseInt(h.slice(1),16),f=s=>Math.round(((n>>s)&255)*(1-t)+255*t);return`rgb(${f(16)},${f(8)},${f(0)})`};
function theme(){const r=document.documentElement.style;r.removeProperty('--ac');r.removeProperty('--acx');r.removeProperty('--acs');}

/* ───── Motor de dibujo de Miku ───── */
const MK=(()=>{
let c,OUT='none',BODY='#fff',t=0,EP=[[0,0],[0,0]];
const P={al:.5,ll:0,ar:.5,lr:0,lx:0,ly:0,tilt:0,gi:1,r:59,g:158,b:255,sq:0,sv:0,jy:0,jv:0,sy:1,big:1,br:0,bl:0},ML={x:0,y:-40},dark='#172B40',X={idle:{e:'o',m:'dot'},happy:{arms:[.9,-8,.9,-8],e:'arc',m:'smile',blush:1},wink:{e:'wink',m:'smile'},
listening:{e:'o',m:'O'},
thinking:{arms:[.5,0,1.1,-12],e:'o',m:'dot'},
talking:{e:'o',m:'talk'},
searching:{e:'o',m:'dot'},
working:{e:'o',m:'frown',br:.6},
proud:{arms:[.9,-8,.9,-8],e:'o',m:'smile',sy:1.05},
love:{arms:[.8,-4,.8,-4],e:'o',m:'smile',blush:1},
surprised:{arms:[1.05,-12,1.05,-12],e:'o',m:'O',big:1},
question:{e:'o',m:'dot'},
annoyed:{e:'ang',m:'grr',br:1,sy:.96,blush:1,blc:'#ff5a4d',arms:[.15,6,.15,6]},
sleeping:{e:'line',m:'none',sy:.92},
error:{arms:[.15,5,.15,5],e:'x',m:'frown'},
dizzy:{e:'spiral',m:'frown'},
look:{e:'o',m:'dot'},
squash:{e:'arc',m:'dot'},
swallow:{e:'o',m:'O',big:1,arms:[.95,-10,.95,-10]},
wave:{e:'o',m:'smile',arms:[.2,0,1.1,-14]}};
const L=(a,b,x,y)=>{c.moveTo(a,b);c.lineTo(x,y)};
function spark(x,y,r){c.beginPath();c.moveTo(x,y-r);c.quadraticCurveTo(x,y,x+r,y);c.quadraticCurveTo(x,y,x,y+r);c.quadraticCurveTo(x,y,x-r,y);c.quadraticCurveTo(x,y,x,y-r);c.fill()}
function heart(x,y,s){c.beginPath();c.moveTo(x,y+s*.8);c.bezierCurveTo(x-s*1.2,y-s*.1,x-s*.6,y-s*.9,x,y-s*.35);c.bezierCurveTo(x+s*.6,y-s*.9,x+s*1.2,y-s*.1,x,y+s*.8);c.fill()}
const gr=(x0,y0,x1,y1,a,b)=>{const g=c.createLinearGradient(x0,y0,x1,y1);g.addColorStop(0,a);g.addColorStop(1,b);return g};
function star5(x,y,ro,ri,rot=0){c.beginPath();for(let i=0;i<10;i++){const r=i%2?ri:ro,a=rot-Math.PI/2+i*Math.PI/5;c[i?'lineTo':'moveTo'](x+Math.cos(a)*r,y+Math.sin(a)*r)}c.closePath()}
function gear(x,y,R,n,rot){c.save();c.translate(x,y);c.rotate(rot);const st=6.2832/n;c.beginPath();let f=1;for(let i=0;i<n;i++)for(const[r,o]of[[.76,-.3],[1,-.17],[1,.17],[.76,.3]]){const a=(i+o)*st;c[f?'moveTo':'lineTo'](Math.cos(a)*R*r,Math.sin(a)*R*r);f=0}c.closePath();c.moveTo(R*.3,0);c.arc(0,0,R*.3,0,6.2832);c.fillStyle=gr(-R,-R,R,R,'#a8d6ff','#3a86ea');c.fill('evenodd');c.strokeStyle='rgba(255,255,255,.65)';c.lineWidth=1.3;c.beginPath();c.arc(0,0,R*.62,3.6,4.8);c.stroke();c.restore()}

function bodyPath(sx=1,sy=1){const p=new Path2D();for(let i=0;i<=84;i++){const a=i/84*6.2832,ca=Math.cos(a),sa=Math.sin(a),top=sa<0,e=top?1.18:.6,ry=top?47:40,px=49*sx*Math.sign(ca)*Math.abs(ca)**e,py=-40+ry*sy*Math.sign(sa)*Math.abs(sa)**e;i?p.lineTo(px,py):p.moveTo(px,py)}p.closePath();return p}

function eye(side,x,y,type,op,sc){
 c.fillStyle=c.strokeStyle=dark;c.lineWidth=3.2;c.lineCap='round';c.lineJoin='round';
 if(type=='wink'&&side>0)type='<';
 if(type=='ang'){c.save();const ix=x-side*9,ox=x+side*9,ln=u=>y-2-6.5*((u-ix)/(ox-ix)),xa=x-side*13.5,xb=x+side*13.5;
  c.beginPath();c.moveTo(xa,ln(xa));c.lineTo(xb,ln(xb));c.lineTo(xb,y+12);c.lineTo(xa,y+12);c.closePath();c.clip();
  c.beginPath();c.ellipse(x,y,5.4*sc,7.8*sc*Math.max(.08,op),0,0,7);c.fill();c.restore()}
 if(type=='o'||type=='wink'){c.beginPath();c.ellipse(x,y,5.2*sc,7.8*sc*Math.max(.08,op),0,0,7);c.fill();}
 else if(type=='arc'){c.beginPath();c.arc(x,y+4,7,Math.PI*1.1,Math.PI*1.9);c.stroke()}
 else if(type=='line'){c.beginPath();c.arc(x,y-3,7,.15*Math.PI,.85*Math.PI);c.stroke()}
 else if(type=='x'){c.beginPath();L(x-6,y-6,x+6,y+6);L(x+6,y-6,x-6,y+6);c.stroke()}
 else if(type=='<'){c.beginPath();L(x+5,y-5,x-5,y);L(x-5,y,x+5,y+5);c.stroke()}
 else if(type=='spiral'){c.beginPath();for(let a=0;a<14;a+=.4){const r=a*.55,px=x+Math.cos(a+t*8)*r,py=y+Math.sin(a+t*8)*r;a?c.lineTo(px,py):c.moveTo(px,py)}c.stroke()}
}
function mouth(m){
 c.fillStyle=c.strokeStyle=dark;c.lineWidth=2.6;c.lineCap='round';c.beginPath();
 if(m=='dot'){L(-3,0,3,0);c.stroke()}
 else if(m=='O'){c.ellipse(0,1,3.2,4.2,0,0,7);c.fill()}
 else if(m=='smile'){c.arc(0,-3,5.5,.15*Math.PI,.85*Math.PI);c.stroke()}
 else if(m=='frown'){c.arc(0,6,5,1.15*Math.PI,1.85*Math.PI);c.stroke()}
 else if(m=='talk'){const o=.8+Math.abs(Math.sin(t*14))*4;c.ellipse(0,1,4.5,o,0,0,7);c.fill();c.fillStyle='#FF9DB8';c.beginPath();c.ellipse(0,o*.55+1,2.8,o*.4,0,0,7);c.fill()}
 else if(m=='grr'){c.lineJoin='round';for(let i=0;i<=5;i++){const px=-9+i*3.6,py=(i%2?-2.4:1.8)+Math.sin(t*34+i*1.7)*.5;i?c.lineTo(px,py):c.moveTo(px,py)}c.stroke()}
  else if(m=='slot'){c.roundRect(-17,-3,34,9,4.5);c.fill()}
}
function hand(d,rot,oy,g){c.save();c.translate(d*50,-28+oy);c.rotate(rot*d);c.beginPath();c.ellipse(0,0,6.5,12,0,0,7);c.fillStyle=g;c.fill();c.restore()}

const ringR=y=>Math.pow(1-Math.pow(Math.min(1,Math.abs(y)),2.7),1/2.7),surf=(y,lon,sc=1)=>{const r=ringR(y)*sc;return[r*Math.sin(lon),y,r*Math.cos(lon)]};
function rot3(p){const yw=P.lx*.5,pt=-.30+(-P.ly*.4)*.4,cy=Math.cos(yw),sy=Math.sin(yw),cp=Math.cos(pt),sp=Math.sin(pt),x1=p[0]*cy+p[2]*sy,z1=-p[0]*sy+p[2]*cy;return[x1,p[1]*cp+z1*sp,-p[1]*sp+z1*cp]}
const pj=p=>{const r=rot3(p);return{x:r[0]*49,y:-40-r[1]*(r[1]>0?47:40),z:r[2]}};
const frontArc=(y,sc)=>{const a=[];for(let i=0;i<=100;i++){const q=pj(surf(y,-Math.PI+i/100*6.2832,sc));if(q.z>=-.02)a.push(q)}return a.sort((p,q)=>p.x-q.x)};
const circ=(y,r)=>{const a=[];for(let i=0;i<=60;i++){const q=pj([r*Math.sin(i/60*6.2832),y,r*Math.cos(i/60*6.2832)]);if(q.z>=-.02)a.push(q)}return a.sort((p,q)=>p.x-q.x)};
const capClip=(y,sc)=>{const a=frontArc(y,sc),p=new Path2D(),L0=a[0],R0=a[a.length-1];p.moveTo(L0.x-49,L0.y);a.forEach(q=>p.lineTo(q.x,q.y));p.lineTo(110,-180);p.lineTo(-110,-180);p.closePath();return p};
const poly=(f,a)=>{c.fillStyle=f;c.beginPath();a.forEach((q,i)=>c[i?'lineTo':'moveTo'](q.x,q.y));c.closePath();c.fill()},ci=(x,y,r,f)=>{c.fillStyle=f;c.beginPath();c.arc(x,y,r,0,7);c.fill()},pom=(x,y,r)=>{ci(x,y,r,gr(x,y-r,x,y+r,'#fff','#d3dbea'));ci(x-r*.3,y-r*.35,r*.28,'rgba(255,255,255,.95)')};
const band=(y0,y1,sc,f)=>poly(f,[...frontArc(y0,sc),...frontArc(y1,sc).reverse()]);
function crownPart(side){const N=96,sg=[];for(let i=0;i<=N;i++){const lon=-Math.PI+i/N*6.2832,ph=(lon+Math.PI)/6.2832*8,f=ph-Math.floor(ph),sp=Math.pow(Math.max(0,1-Math.abs(f-.5)*2),1.6),b=pj(surf(.46,lon,1.06)),tp=surf(.66,lon,1.06);tp[1]=.66+.4*sp;tp[0]*=1-.08*sp;tp[2]*=1-.08*sp;sg.push({b,t:pj(tp)})}
 const k=sg.filter(q=>side>0?q.b.z>=0:q.b.z<.02).sort((a,b)=>a.b.x-b.b.x);if(k.length<2)return;poly(side>0?gr(0,-110,0,-58,'#ffe58a','#dd9a0c'):'#a9730d',[...k.map(q=>q.t),...k.map(q=>q.b).reverse()]);
 if(side>0)for(let m=0;m<8;m++){const g=pj(surf(.56,-Math.PI+(m+.5)/8*6.2832,1.07));if(g.z>.18)ci(g.x,g.y,2.4,['#ef4444','#3b82f6','#22c55e','#a855f7'][m%4])}}
function ears(){for(const d of[-1,1]){const b=pj([d*.38,.93,0]);c.save();c.translate(b.x,b.y+4);c.rotate(d*.16);c.fillStyle=BODY;c.beginPath();c.ellipse(0,-15,7.4,16.5,0,0,7);c.fill();c.strokeStyle='rgba(0,0,0,.14)';c.lineWidth=1;c.stroke();c.fillStyle='#ffb3c8';c.beginPath();c.ellipse(0,-14,3.4,11.5,0,0,7);c.fill();c.restore()}}
const brimPts=dy=>{const r=[];for(let i=0;i<=60;i++){const a=i/60*6.2832,q=pj([1.4*Math.sin(a),.7,1.4*Math.cos(a)]);r.push({x:q.x,y:q.y+dy,z:q.z})}return r};

let OPV=1;
const hull=a=>{const p=a.map(q=>({x:q.x,y:q.y})).sort((u,v)=>u.x-v.x||u.y-v.y),cr=(o,a,b)=>(a.x-o.x)*(b.y-o.y)-(a.y-o.y)*(b.x-o.x),lo=[],up=[];for(const q of p){while(lo.length>1&&cr(lo[lo.length-2],lo[lo.length-1],q)<=0)lo.pop();lo.push(q)}for(let i=p.length-1;i>=0;i--){const q=p[i];while(up.length>1&&cr(up[up.length-2],up[up.length-1],q)<=0)up.pop();up.push(q)}lo.pop();up.pop();return lo.concat(up)};
const ringP=(y,R,ox=0,oz=0,n=40)=>{const a=[];for(let i=0;i<n;i++){const k=i/n*6.2832;a.push(pj([ox+R*Math.sin(k),y,oz+R*Math.cos(k)]))}return a};
const frontP=(y,R,ox=0,oz=0)=>{const a=[];for(let i=0;i<=72;i++){const k=i/72*6.2832;if(rot3([Math.sin(k),0,Math.cos(k)])[2]>=0)a.push(pj([ox+R*Math.sin(k),y,oz+R*Math.cos(k)]))}return a.sort((p,q)=>p.x-q.x)};
const strokeP=a=>{c.beginPath();a.forEach((q,i)=>c[i?'lineTo':'moveTo'](q.x,q.y));c.stroke()};
const phU=(d,y)=>d*Math.pow(Math.cos(Math.asin(Math.min(1,Math.pow(y,1/1.18)))),1.18);
const phBand=()=>{const a=[],f0=.2118,n=28;for(let i=0;i<=n;i++){const ph=f0+(Math.PI-2*f0)*i/n,ca=Math.cos(ph),sa=Math.sin(ph);a.push(pj([Math.sign(ca)*Math.pow(Math.abs(ca),1.18)*1.045,Math.pow(sa,1.18)*1.045,0]))}return a};
function phCup(d){const q=pj([phU(d,.16),.16,0]),w=3.6+3.4*Math.max(0,Math.min(1,.4+q.z));c.save();c.translate(q.x+d*2.2,q.y);
 c.fillStyle=gr(-w,-12,w,12,'#3a4152','#171a23');c.beginPath();c.ellipse(0,0,w,11.5,0,0,7);c.fill();
 c.globalAlpha=.55+.45*Math.sin(t*3);c.strokeStyle=BODY;c.lineWidth=1.4;c.beginPath();c.ellipse(0,0,w*.68,9,0,0,7);c.stroke();c.globalAlpha=1;
 c.fillStyle=BODY;for(let i=0;i<3;i++){const h=3+6*Math.abs(Math.sin(t*6+i*1.4+d));c.fillRect(-w*.42+i*w*.42,-h/2,Math.max(1,w*.28),h)}
 c.fillStyle='rgba(255,255,255,.16)';c.beginPath();c.ellipse(-d*w*.3,-7,w*.25,3.6,0,0,7);c.fill();c.restore()}
const fluff=(x,y,r,n=7,sp=.6)=>{for(let i=0;i<n;i++){const an=i/n*6.2832+t*sp;ci(x+Math.cos(an)*r*.66,y+Math.sin(an)*r*.62,r*.58,'#eef2fa')}pom(x,y,r*.94)};
function outBack(){const o=OUT;if(o=='bunny')ears();else if(o=='crown')crownPart(-1);else if(o=='phones'){for(const d of[-1,1]){if(pj([phU(d,.16),.16,0]).z<-.02)phCup(d)}}}
const bat=(x,y,s,fl)=>{c.save();c.translate(x,y);c.scale(s,s);c.fillStyle='#1b0b33';const w=Math.sin(fl)*5;c.beginPath();c.moveTo(0,-2);c.quadraticCurveTo(-7,-8-w,-15,-2+w);c.quadraticCurveTo(-10,0,-8,3);c.quadraticCurveTo(-4,1,0,5);c.quadraticCurveTo(4,1,8,3);c.quadraticCurveTo(10,0,15,-2+w);c.quadraticCurveTo(7,-8-w,0,-2);c.fill();c.beginPath();c.arc(0,0,3.2,0,7);c.fill();c.fillStyle='#ffd84d';c.fillRect(-2,-1,1.2,1.2);c.fillRect(.8,-1,1.2,1.2);c.restore()};
const flake=(x,y,r,rot)=>{c.save();c.translate(x,y);c.rotate(rot);c.beginPath();for(let i=0;i<3;i++){c.moveTo(0,-r);c.lineTo(0,r);c.rotate(1.0472)}c.stroke();c.restore()};
const OF={
beanie(){
 const a=frontArc(.5,1.06),Lq=a[0],Rq=a[a.length-1],cr=pj([0,1.06,0]),sw=Math.sin(t*2.4),tx=cr.x+sw*2.2,ty=cr.y-7;
 c.beginPath();c.moveTo(Lq.x-1,Lq.y);c.bezierCurveTo(Lq.x-6,Lq.y-26,tx-30,ty-3,tx,ty-3);c.bezierCurveTo(tx+30,ty-3,Rq.x+6,Rq.y-26,Rq.x+1,Rq.y);a.slice().reverse().forEach(q=>c.lineTo(q.x,q.y));c.closePath();
 c.fillStyle=gr(Lq.x,-138,Rq.x,-62,'#8cc0ff','#2152c4');c.fill();c.save();c.clip();
 for(const[y,w,f]of[[.74,7,'#f4f7ff'],[.9,4,'#ffd84d']]){c.strokeStyle=f;c.lineWidth=w;c.beginPath();frontArc(y,1.06).forEach((q,i)=>c[i?'lineTo':'moveTo'](q.x,q.y-2));c.stroke()}
 c.strokeStyle='rgba(10,30,120,.24)';c.lineWidth=1.3;for(const y of[.6,.67,.82,.98,1.06]){const f=frontArc(y,1.06);for(let i=2;i<f.length-2;i+=4){const q=f[i];c.beginPath();c.moveTo(q.x-2.2,q.y-3);c.lineTo(q.x,q.y);c.lineTo(q.x+2.2,q.y-3);c.stroke()}}
 const rg=c.createRadialGradient(-18,-100,2,-8,-84,66);rg.addColorStop(0,'rgba(255,255,255,.42)');rg.addColorStop(1,'rgba(255,255,255,0)');c.fillStyle=rg;c.fillRect(-90,-160,180,130);
 const sh=((t*.5)%1.6)*160-60;c.fillStyle='rgba(255,255,255,.14)';c.beginPath();c.moveTo(sh,-130);c.lineTo(sh+10,-130);c.lineTo(sh-14,-50);c.lineTo(sh-24,-50);c.fill();c.restore();
 band(.54,.34,1.08,gr(0,-72,0,-46,'#5b93f2','#1f4fbf'));
 for(let k=-10;k<=10;k++){const lon=k*.15,p=pj(surf(.54,lon,1.08)),q=pj(surf(.34,lon,1.08));if(p.z>.06){c.strokeStyle='rgba(8,28,110,.34)';c.lineWidth=1.6;c.beginPath();L(p.x,p.y,q.x,q.y);c.stroke();c.strokeStyle='rgba(255,255,255,.14)';c.lineWidth=.9;c.beginPath();L(p.x+1.2,p.y,q.x+1.2,q.y);c.stroke()}}
 c.strokeStyle='rgba(255,255,255,.45)';c.lineWidth=1.5;c.beginPath();frontArc(.54,1.08).forEach((q,i)=>c[i?'lineTo':'moveTo'](q.x,q.y-.5));c.stroke();
 c.strokeStyle='rgba(0,0,50,.3)';c.lineWidth=2;c.beginPath();frontArc(.34,1.08).forEach((q,i)=>c[i?'lineTo':'moveTo'](q.x,q.y+1));c.stroke();
 const bn=Math.abs(sw);const px=tx,py=ty-5-bn*1.6;
 ci(px,py,6.6,gr(px,py-6.6,px,py+6.6,'#fff','#c9d6f0'));ci(px-2.2,py-2.4,2.1,'rgba(255,255,255,.95)');
 c.fillStyle='#ffd84d';for(let i=0;i<2;i++){const p=(t*.45+i*.5)%1;c.globalAlpha=Math.sin(p*Math.PI)*.9;spark(px+(i?13:-13)+Math.sin(t*2+i)*2,py-3-p*7,2)}c.globalAlpha=1},
party(){
 const A=.9,R=.44,ax=-.1,ay=1.44,ap=pj([ax,ay,0]);ap.x+=Math.sin(t*3)*.8;
 const H=hull([...ringP(A,R),ap]);
 c.beginPath();H.forEach((q,i)=>c[i?'lineTo':'moveTo'](q.x,q.y));c.closePath();c.fillStyle=gr(0,ap.y,0,ap.y+34,'#ff9bd0','#c8228a');c.fill();
 c.save();c.clip();
 for(const[u,col]of[[.26,'#ffe066'],[.52,'#5ce1e6'],[.78,'#ffe066']]){const fr=frontP(A+(ay-A)*u,R*(1-u),ax*u);if(fr.length>1){c.strokeStyle=col;c.lineWidth=3;strokeP(fr)}}
 for(const[u,l]of[[.39,.5],[.39,-.6],[.65,.15],[.65,-.45],[.13,.2],[.13,-.9],[.13,1]]){const r=R*(1-u),g=pj([ax*u+r*Math.sin(l),A+(ay-A)*u,r*Math.cos(l)]);if(g.z>.05)ci(g.x,g.y,1.7,'rgba(255,255,255,.92)')}
 c.fillStyle='rgba(255,255,255,.2)';c.beginPath();c.moveTo(ap.x,ap.y);c.lineTo(ap.x-4,ap.y+34);c.lineTo(ap.x+6,ap.y+34);c.closePath();c.fill();c.restore();
 {const fr=frontP(A,R);c.lineCap='round';c.strokeStyle='#ffd84d';c.lineWidth=3;strokeP(fr);c.strokeStyle='#fff3b0';c.lineWidth=1;strokeP(fr.map(q=>({x:q.x,y:q.y-1})))}
 c.save();c.lineWidth=2.2;c.lineCap='round';['#5ce1e6','#ffd84d','#ff6bd6'].forEach((col,k)=>{const d=(k-1)*8,w=Math.sin(t*4+k*1.6)*2.5;c.strokeStyle=col;c.beginPath();c.moveTo(ap.x,ap.y);c.quadraticCurveTo(ap.x+d*.6+w,ap.y-5,ap.x+d+w,ap.y-9+Math.abs(k-1)*3);c.stroke()});c.restore();
 c.save();c.shadowColor='#ffd84d';c.shadowBlur=7;c.fillStyle=gr(ap.x,ap.y-5,ap.x,ap.y+4,'#fff6c0','#ffc21a');star5(ap.x,ap.y-1,5.2,2.3,t*1.5);c.fill();c.restore();
 const cc=['#ff6bd6','#ffd84d','#5ce1e6','#9bff7a','#ff8a5c'];
 for(let i=0;i<5;i++){const p=(t*.4+i*.2)%1,x=ap.x+Math.sin(i*2.4+t*1.3)*(7+p*18),y=ap.y+2+p*36;c.save();c.globalAlpha=Math.sin(p*Math.PI)*.95;c.translate(x,y);c.rotate(t*4+i);c.fillStyle=cc[i];c.fillRect(-2,-1.1,4,2.2);c.restore()}},
witch(){
 const A=.84,br=hull(ringP(A,.96)),fb=frontP(A,.96);
 c.save();c.lineCap='round';c.strokeStyle='rgba(0,0,0,.24)';c.lineWidth=3.5;strokeP(fb.map(q=>({x:q.x,y:q.y+2.6})));c.restore();
 poly(gr(0,-100,0,-62,'#6d28d9','#2e1065'),br);
 c.strokeStyle='rgba(200,170,255,.55)';c.lineWidth=1.3;c.beginPath();br.forEach((q,i)=>c[i?'lineTo':'moveTo'](q.x,q.y));c.closePath();c.stroke();
 const B1=1.22,ap=pj([.2,1.56,0]);ap.x+=Math.sin(t*1.7)*1.2;
 const s1=hull([...ringP(A+.02,.5),...ringP(B1,.2,.04)]),s2=hull([...ringP(B1,.2,.04),ap]);
 for(const sg of[s1,s2])poly(gr(-24,0,24,0,'#9a6cfb','#2a0f5e'),sg);
 {const fr=frontP(.96,.43);c.lineCap='round';c.strokeStyle='#ffa24a';c.lineWidth=4.6;strokeP(fr);c.strokeStyle='#c2410c';c.lineWidth=1.1;strokeP(fr.map(q=>({x:q.x,y:q.y+2.6})))}
 const bk=pj([0,.96,.43]);if(bk.z>0){c.fillStyle=gr(bk.x,bk.y-6,bk.x,bk.y+6,'#ffe58a','#d99a0b');c.beginPath();c.roundRect(bk.x-4.6,bk.y-4,9.2,8,2);c.fill();c.fillStyle='#7c2d12';c.beginPath();c.roundRect(bk.x-2.4,bk.y-1.8,4.8,3.6,1);c.fill()}
 c.fillStyle='#ffe27a';for(const[x,y,r,ph]of[[.08,1.12,2.6,0],[-.1,1.0,2,1.8]]){const g=pj([x,y,.28]);if(g.z>0){c.globalAlpha=.6+.4*Math.sin(t*4+ph);star5(g.x,g.y,r*(.8+.2*Math.sin(t*4+ph)),r*.42,t*.8+ph);c.fill()}}c.globalAlpha=1},
santa(){
 const a=frontArc(.52,1.06),Lq=a[0],Rq=a[a.length-1],cr=pj([0,1.05,0]),sw=Math.sin(t*2.2),tip={x:cr.x+34+sw*3,y:cr.y+14+Math.abs(sw)*2},pk={x:cr.x+6,y:cr.y-17};
 c.beginPath();c.moveTo(Lq.x,Lq.y);c.bezierCurveTo(Lq.x-3,Lq.y-26,pk.x-22,pk.y,pk.x,pk.y);c.quadraticCurveTo(tip.x-4,pk.y-3,tip.x,tip.y);c.quadraticCurveTo(tip.x-8,tip.y-14,pk.x+10,pk.y+16);c.bezierCurveTo(Rq.x+3,pk.y+26,Rq.x+4,Rq.y-18,Rq.x,Rq.y);a.slice().reverse().forEach(q=>c.lineTo(q.x,q.y));c.closePath();
 c.fillStyle=gr(Lq.x,-130,Rq.x+30,-60,'#ff5a5a','#a31515');c.fill();c.save();c.clip();
 c.fillStyle='rgba(0,0,0,.13)';c.beginPath();c.moveTo(pk.x+10,pk.y+16);c.quadraticCurveTo(pk.x+26,pk.y+30,Rq.x,Rq.y-6);c.lineTo(Rq.x+20,Rq.y);c.lineTo(Rq.x+20,pk.y);c.closePath();c.fill();
 c.fillStyle='rgba(255,255,255,.17)';c.beginPath();c.ellipse(Lq.x+11,Lq.y-20,5,18,.5,0,7);c.fill();c.restore();
 const fur=frontArc(.52,1.09);c.strokeStyle='#e6ecf6';c.lineWidth=9;c.beginPath();fur.forEach((q,i)=>c[i?'lineTo':'moveTo'](q.x,q.y-1));c.stroke();
 for(let i=0;i<fur.length;i+=3){const q=fur[i],y=q.y-1.5+(i%2?1.6:-1);ci(q.x,y,5.2,gr(q.x,y-6,q.x,y+5,'#fff','#dbe3f0'))}
 fluff(tip.x,tip.y+3,5.8,7,.9);
 c.fillStyle='#fff';for(let i=0;i<3;i++){const p=(t*.35+i/3)%1;c.globalAlpha=Math.sin(p*Math.PI)*.9;spark(tip.x-8+i*9+Math.sin(t*2+i)*3,tip.y-26+p*38,2.4)}c.globalAlpha=1;c.strokeStyle='rgba(255,255,255,.55)';c.lineWidth=1.1;c.setLineDash([3,3]);c.beginPath();c.moveTo(Lq.x+4,Lq.y-14);c.quadraticCurveTo(pk.x-8,pk.y+16,pk.x+6,pk.y+8);c.stroke();c.setLineDash([]);
 c.strokeStyle='#fff';c.lineWidth=1.2;c.lineCap='round';for(let k=0;k<4;k++){const p=(t*.22+k/4)%1,fx=cr.x-26+k*17+Math.sin(t*1.4+k*1.9)*4,fy=-126+p*58;c.globalAlpha=Math.sin(p*Math.PI)*.9;flake(fx,fy,2.6+(k%3)*.9,t*1.5+k)}c.globalAlpha=1},
pumpkin(){
 /* máscara de calabaza puesta en lo alto de la cabeza: fija a ella y se mueve con ella */
 const a=EP[0],b=EP[1],fx=Math.max(.3,(a[2]+b[2])/2),fy=Math.max(.4,(a[3]+b[3])/2),mx=(a[0]+b[0])/2,my=(a[1]+b[1])/2-33,
  fl=.6+.4*Math.sin(t*9+Math.sin(t*3.3)*2),op=Math.max(.15,OPV),mo=Math.min(1,Math.max(0,P.mo));
 c.save();c.clip(bodyPath());c.translate(mx,my);c.scale(fx,fy);c.strokeStyle='#2b1a0e';c.lineWidth=2.2;c.lineCap='round';
 for(const d of[-1,1]){c.beginPath();c.moveTo(d*22,0);c.lineTo(d*Math.min(52,46/fx),1);c.stroke()}c.restore();
 c.save();c.translate(mx,my);c.rotate(-.05);c.scale(fx,fy);
 for(const[dx,rx]of[[-16,10],[16,10],[-8,12.5],[8,12.5],[0,14]]){c.fillStyle=gr(0,-18,0,18,'#ffa63a','#e0540a');c.beginPath();c.ellipse(dx,0,rx,18,0,0,7);c.fill()}
 c.strokeStyle='rgba(110,35,0,.38)';c.lineWidth=1;for(const x of[-10,-4.5,4.5,10]){c.beginPath();c.moveTo(x*.9,-15);c.quadraticCurveTo(x*1.3,0,x*.9,15);c.stroke()}
 c.fillStyle='rgba(255,255,255,.22)';c.beginPath();c.ellipse(-14,-8,2,4.5,.4,0,7);c.fill();
 c.save();c.shadowColor='#ffb300';c.shadowBlur=6*fl;c.fillStyle=`rgba(255,${200+30*fl|0},70,${.8+.2*fl})`;c.strokeStyle='rgba(110,35,0,.55)';c.lineWidth=1;c.lineJoin='round';
 for(const d of[-1,1]){c.save();c.translate(d*10.5,-3);c.scale(1,op);c.beginPath();c.moveTo(-4.6,3.6);c.lineTo(0,-5);c.lineTo(4.6,3.6);c.closePath();c.fill();c.stroke();c.restore()}
 c.beginPath();c.moveTo(-10,4);c.lineTo(-6,2.6);c.lineTo(-3.6,5.4);c.lineTo(0,2.6);c.lineTo(3.6,5.4);c.lineTo(6,2.6);c.lineTo(10,4);c.quadraticCurveTo(0,10+mo*9,-10,4);c.closePath();c.fill();c.stroke();c.restore();
 c.lineCap='round';c.strokeStyle='#3f7d20';c.lineWidth=4;c.beginPath();c.moveTo(0,-16);c.quadraticCurveTo(1,-20,4,-23);c.stroke();c.strokeStyle='#6bb53a';c.lineWidth=1.4;c.beginPath();c.moveTo(0,-16.5);c.quadraticCurveTo(1,-20,3.6,-22.6);c.stroke();
 c.fillStyle=gr(5,-21,12,-17,'#7ccf45','#3f8f1d');c.beginPath();c.moveTo(2.5,-18);c.quadraticCurveTo(8,-25,13,-18);c.quadraticCurveTo(8,-15,2.5,-18);c.fill();
 c.restore()},
halo(){
 const q=pj([0,1.2,0]),cx=q.x,cy=q.y-7+Math.sin(t*2)*1.8;
 c.save();c.shadowColor='#ffd84d';c.shadowBlur=11+3*Math.sin(t*3);c.lineWidth=4.4;c.strokeStyle=gr(cx-27,cy,cx+27,cy,'#ffe58a','#f5a40c');c.beginPath();c.ellipse(cx,cy,26,7.6,0,0,7);c.stroke();c.restore();
 c.strokeStyle='rgba(255,255,255,.7)';c.lineWidth=1.3;c.beginPath();c.ellipse(cx,cy-1,25,6.6,0,Math.PI*1.1,Math.PI*1.8);c.stroke();
 c.fillStyle='#fff6c4';for(let i=0;i<3;i++){const an=t*1.8+i*2.094;spark(cx+Math.cos(an)*26,cy+Math.sin(an)*7.6,2.3+Math.sin(an*2)*.8)}},
propeller(){
 c.save();c.clip(capClip(.62,1.05));c.clip(bodyPath(1.06,1.06));c.fillStyle=gr(-40,-120,40,-52,'#59abff','#1a49ad');c.fill(bodyPath(1.06,1.06));
 const cols=['#ffd84d','#ff5c66'];
 for(let k=0;k<6;k++){const lon=-Math.PI+k*Math.PI/3+.5,z0=pj(surf(.62,lon,1.06)).z;c.strokeStyle=cols[k%2];c.lineWidth=2+9*Math.max(.15,z0);c.lineCap='butt';c.beginPath();let st=0;for(let s=0;s<=10;s++){const q=pj(surf(.6+.46*s/10,lon,1.06));if(q.z>0){c[st?'lineTo':'moveTo'](q.x,q.y);st=1}else st=0}c.stroke()}
 const rg=c.createRadialGradient(-16,-94,2,-8,-82,62);rg.addColorStop(0,'rgba(255,255,255,.34)');rg.addColorStop(1,'rgba(255,255,255,0)');c.fillStyle=rg;c.fill(bodyPath(1.06,1.06));c.restore();
 band(.62,.5,1.07,gr(0,-72,0,-60,'#2c64d8','#12378a'));
 const t0=pj([0,1.07,0]),hx=t0.x,hy=t0.y-11,w=Math.cos(t*14);
 c.fillStyle='#d9dde6';c.beginPath();c.roundRect(hx-1.6,hy,3.2,10,1);c.fill();
 c.fillStyle='rgba(255,255,255,.13)';c.beginPath();c.ellipse(hx,hy,18,3.6,0,0,7);c.fill();
 for(const d of[-1,1]){const bw=Math.max(2,Math.abs(w)*16);c.fillStyle=d>0?'#ff5c66':'#ffd84d';c.beginPath();c.ellipse(hx+d*bw*.5,hy+Math.sin(t*14)*.8,bw*.5,3,0,0,7);c.fill()}
 ci(hx,hy,3,'#ffd84d');ci(hx-.8,hy-.8,1,'rgba(255,255,255,.9)')},
phones(){
 const pts=phBand();c.lineJoin=c.lineCap='round';c.strokeStyle='#262b38';c.lineWidth=4.6;strokeP(pts);
 c.strokeStyle='rgba(255,255,255,.22)';c.lineWidth=1.3;strokeP(pts.map(q=>({x:q.x,y:q.y-1.2})));
 for(const d of[-1,1]){if(pj([phU(d,.16),.16,0]).z>=-.02)phCup(d)}}
};
function outfit(){const o=OUT;if(o=='none')return;c.save();c.lineJoin=c.lineCap='round';
 if(OF[o])OF[o]();
 else if(o=='crown')crownPart(1);
 else if(o=='shades'||o=='round'){const sh=o=='shades';c.strokeStyle=sh?'#0f1116':'#d9a25f';c.lineWidth=sh?3:2.4;c.beginPath();L(EP[0][0]+11*EP[0][2],EP[0][1]-3,EP[1][0]-11*EP[1][2],EP[1][1]-3);c.stroke();
  for(const q of EP){c.save();c.translate(q[0],q[1]);c.scale(q[2],q[3]);c.beginPath();if(sh){c.roundRect(-13,-9,26,18,7);c.fillStyle='rgba(15,17,22,.94)';c.fill();c.fillStyle='rgba(255,255,255,.3)';c.beginPath();c.moveTo(-8,-3);c.lineTo(-3,-7);c.lineTo(0,-7);c.lineTo(-6,-1);c.fill()}else{c.arc(0,0,12,0,7);c.fillStyle='rgba(190,225,255,.12)';c.fill();c.stroke();c.strokeStyle='rgba(255,255,255,.6)';c.lineWidth=1.4;c.beginPath();c.arc(0,0,9,3.6,4.5);c.stroke()}c.restore()}}
 else if(o=='bow'){const a=pj(surf(.86,.55,1.02)),sq=Math.max(.45,Math.cos(.55+P.lx*.5));c.save();c.translate(a.x,a.y);c.rotate(.35+P.lx*.15);c.scale(sq,1);for(const d of[-1,1]){c.fillStyle=gr(0,-10,0,10,'#ff9bd0','#e0307f');c.beginPath();c.moveTo(0,0);c.bezierCurveTo(d*6,-11,d*17,-8,d*15,0);c.bezierCurveTo(d*17,8,d*6,11,0,0);c.fill()}ci(0,0,3.6,gr(0,-4,0,4,'#ffc0de','#c2185b'));c.restore()}
 else if(o=='scarf'){band(-.34,-.66,1.05,gr(0,-26,0,-12,'#f87171','#b91c1c'));const k=pj(surf(-.5,-.55,1.06));if(k.z>0){c.fillStyle=gr(0,k.y,0,k.y+26,'#ef4444','#b91c1c');c.beginPath();c.roundRect(k.x-7,k.y-2,14,28,5);c.fill();c.fillStyle='rgba(255,255,255,.8)';c.fillRect(k.x-7,k.y+10,14,3);ci(k.x,k.y,7,gr(0,k.y-7,0,k.y+7,'#f87171','#b91c1c'))}}
 c.restore()}

function drawChar(s,k,dt,op,breath,sh,bob){c.clearRect(-20,-20,200,200);c.globalAlpha=1;
 c.save();c.translate(80+sh,128+bob*.5);c.rotate(P.tilt);c.scale(1+P.sq,breath*P.sy*(1-P.sq*1.1));
 c.shadowColor=`rgba(${(P.r+510)/3|0},${(P.g+510)/3|0},${(P.b+510)/3|0},${Math.min(1,.6*P.gi)})`;c.shadowBlur=38;if(BODY!='#fff')c.shadowColor=BODY+'b3';
 const A=s.arms||[.5,0,.5,0],tA=[...A];if(s.wave){tA[2]=.9+Math.sin(t*9)*.35;tA[3]=-20}if(s.flap){tA[0]=.7+Math.sin(t*10)*.5;tA[2]=.7+Math.sin(t*10+2)*.5}
 const ka=Math.min(1,k*1.5);P.al+=(tA[0]-P.al)*ka;P.ll+=(tA[1]-P.ll)*ka;P.ar+=(tA[2]-P.ar)*ka;P.lr+=(tA[3]-P.lr)*ka;
 
 c.save();c.shadowBlur=0;outBack();c.restore();
 hand(-1,P.al,P.ll,BODY);hand(1,P.ar,P.lr,BODY);
 const bp=bodyPath();
 c.fillStyle=BODY;c.fill(bp);c.fill(bp);c.shadowBlur=0;
 const HY=P.lx*.5,HP=-P.ly*.4,fp=(yw,pt)=>{const cp=Math.cos(pt+HP);return{x:Math.sin(yw+HY)*cp*49,y:-40-Math.sin(pt+HP)*40,fx:Math.max(.25,Math.cos(yw+HY)),fy:Math.max(.3,cp),sk:-Math.sin(yw+HY)*Math.sin(pt+HP)*.6}};
 if(P.bl>.02)for(const d of[-1,1]){const f=fp(d*.8,-.42),vis=Math.min(1,Math.max(0,(Math.cos(d*.8+HY)-.3)*4));c.globalAlpha=.5*vis*P.bl;c.fillStyle=s.blc||'#FF9DB8';c.beginPath();c.ellipse(f.x,f.y,6.5*f.fx,3.8*f.fy,f.sk,0,7);c.fill()}c.globalAlpha=1;
 for(const d of[-1,1]){const f=fp(d*.43,-.12),x=f.x,y=f.y;
  c.save();c.translate(x,y);c.transform(1,f.sk,0,1,0,0);c.scale(f.fx,f.fy);eye(d,0,0,s.e,op,P.big);c.restore();EP[d<0?0:1]=[x,y,f.fx,f.fy];
  if(P.br>.05){c.strokeStyle=dark;c.lineWidth=3.2;c.beginPath();L(x-d*7*f.fx,y-(11-P.br*5)*f.fy,x+d*8*f.fx,y-(11+P.br*3.2)*f.fy);c.stroke()}}
 {const f=fp(0,-.34),a=1-Math.exp(-dt*16);ML.x+=(f.x-ML.x)*a;ML.y+=(f.y-ML.y)*a;c.save();c.translate(ML.x,ML.y);c.transform(1,f.sk,0,1,0,0);c.scale(f.fx,f.fy);mouth(s.m);c.restore()}
 OPV=op;outfit();
 c.restore();
 }

const off=document.createElement('canvas');off.width=off.height=400;const oc=off.getContext('2d',{willReadFrequently:true});
const reset=()=>Object.assign(P,{al:.5,ll:0,ar:.5,lr:0,lx:0,ly:0,tilt:0,gi:1,r:59,g:158,b:255,sq:0,sv:0,jy:0,jv:0,sy:1,big:1,br:0,bl:0});

function paint(color,outfit,tt,lx=0,ly=0,blink=0,o={}){
 c=oc;oc.setTransform(1,0,0,1,0,0);oc.clearRect(0,0,400,400);oc.scale(2,2);oc.translate(20,20);
 OUT=outfit||'none';BODY=color;t=tt;reset();P.lx=lx;P.ly=ly;
 const s={...(X[o.ex]||X.idle)};if(o.arms)s.arms=o.arms;
 P.bl=s.blush?1:0;P.tilt=o.tilt||0;P.sq=o.sq||0;
 drawChar(s,1,1,1-blink,o.breath||1,o.sh||0,o.bob||0);
}

const crops=new Map();
function crop(o){o=o||'none';if(crops.has(o))return crops.get(o);paint('#fff',o,1.3,0,0);
 const w=360,d=oc.getImageData(20,0,w,400).data;let T=400;for(let y=0;y<400&&T==400;y++)for(let x=0;x<w;x++)if(d[(y*w+x)*4+3]>12){T=y;break}
 const half=Math.min(210,Math.max(104,210-T+44)),r=[20,210-half,w,half*2];crops.set(o,r);return r}

const cache=new Map();
function snap(color,outfit,id='',blink=0){
 const k=color+'|'+outfit+'|'+id+'|'+blink;
 if(cache.has(k))return cache.get(k);
 let lx=0,ly=0;
 if(id&&id!=='miku'){
   const h=id.split('').reduce((a,b)=>Math.imul(31,a)+b.charCodeAt(0)|0,0);
   lx=(((Math.abs(h)%100)/50)-1)*0.8;
   ly=((((Math.abs(h)>>8)%100)/50)-1)*0.45;
 }
 const r=crop(outfit);paint(color,outfit,1.3,lx,ly,blink);
 const o=document.createElement('canvas');o.width=r[2];o.height=r[3];
 o.getContext('2d').drawImage(off,r[0],r[1],r[2],r[3],0,0,r[2],r[3]);
 const u=o.toDataURL();cache.set(k,u);return u;
}

const AVC=new Map(),AVB=new Map();
function avBox(outfit,color){if(AVB.has(outfit))return AVB.get(outfit);
 paint(color,outfit,1.3,0,0,0);const d=oc.getImageData(0,0,400,400).data;let x0=400,y0=400,x1=-1,y1=-1;
 for(let y=0;y<400;y++)for(let x=0;x<400;x++)if(d[(y*400+x)*4+3]>215){if(x<x0)x0=x;if(x>x1)x1=x;if(y<y0)y0=y;if(y>y1)y1=y}
 const b=x1<x0?{x:40,y:40,w:320,h:320}:{x:x0,y:y0,w:x1-x0+1,h:y1-y0+1};AVB.set(outfit,b);return b}
function avFrame(color,outfit,crop,gx,gy,bl,ex,peek){
 const key=[color,outfit,gx,gy,bl,ex].join('|'),hit=AVC.get(key);if(hit||peek)return hit||null;
 const b=avBox(outfit,color);paint(color,outfit,1.3,gx,gy,bl,{ex,tilt:gx*.1});
 const sc=Math.min(66/b.w,66/b.h),mg=9/sc,W=b.w*sc+18,H=b.h*sc+18,o=document.createElement('canvas');o.width=o.height=84;
 const x=o.getContext('2d');x.imageSmoothingQuality='high';
 x.drawImage(off,b.x-mg,b.y-mg,b.w+2*mg,b.h+2*mg,(84-W)/2,(84-H)/2,W,H);
 x.globalCompositeOperation='destination-in';const g=x.createRadialGradient(42,42,33,42,42,43);g.addColorStop(0,'#000');g.addColorStop(1,'rgba(0,0,0,0)');x.fillStyle=g;x.fillRect(0,0,84,84);
 if(AVC.size>500)AVC.delete(AVC.keys().next().value);AVC.set(key,o);return o}

/* Héroe grande: resortes para mirada, cuerpo, inclinación, brazos y saltos (con modo subtle sutil) */
function live(cv,get,opts={}){
 const x=cv.getContext('2d'),cl=(v,a,b)=>Math.max(a,Math.min(b,v)),R=(a,b)=>a+Math.random()*(b-a);
 let on=1,nb=1.2,bt=-9,dbl=0,prev=performance.now()/1000;
 const H={lx:0,vlx:0,ly:0,vly:0,sh:0,vsh:0,tilt:0,vt:0,bob:0,vb:0,sq:0,vsq:0,ex:'idle',exU:0,gx:0,gy:0,nl:0,nh:3,hov:0};
 const pulse=(v,sq,ms)=>{
  H.vb=opts.subtle?v*0.35:v;
  H.sq=opts.subtle?sq*0.4:sq;
  H.ex='happy';
  H.exU=performance.now()+ms;
 };
 cv.style.cursor='pointer';
 cv.addEventListener('pointerdown',()=>pulse(-560,.17,1100));
 cv.addEventListener('pointerenter',()=>{H.hov=1;pulse(-300,.05,850)});
 cv.addEventListener('pointerleave',()=>{H.hov=0});
 const bl=k=>k<0||k>.15?0:Math.sin(k/.15*Math.PI);
 const loop=now=>{
  if(!on||!cv.isConnected)return;
  requestAnimationFrame(loop);
  if(document.hidden)return;
  const t=now/1000,dt=Math.min(.05,Math.max(.001,t-prev));prev=t;
  const g=get(),r=crop(g.outfit);
  if(cv.width!=r[2]||cv.height!=r[3]){cv.width=r[2];cv.height=r[3]}
  const b=cv.getBoundingClientRect(),dx=PX-(b.left+b.width/2),dy=PY-(b.top+b.height/2),act=performance.now()-PT<2800;
  let tx,ty;
  if(act){
   if(opts.subtle){
    tx=cl(dx/340,-1,1)*0.60;
    ty=cl(dy/260,-1,1)*0.38;
   }else{
    tx=cl(dx/230,-1,1)*.95;
    ty=cl(dy/170,-1,1)*.55;
   }
  }else{
   if(t>H.nl){
    H.gx=Math.random()<.4?0:R(opts.subtle?-.35:.8,opts.subtle?.35:.8);
    H.gy=Math.random()<.6?0:R(opts.subtle?-.2:.35,opts.subtle?.2:.4);
    H.nl=t+R(1.4,3.8);
   }
   tx=H.gx;ty=H.gy;
  }
  const springK=opts.subtle?50:95;
  const damp=opts.subtle?15:10;
  H.vlx+=((tx-H.lx)*springK-H.vlx*damp)*dt;H.lx+=H.vlx*dt;
  H.vly+=((ty-H.ly)*springK-H.vly*damp)*dt;H.ly+=H.vly*dt;
  const shK=opts.subtle?2.2:11;
  H.vsh+=((tx*shK-H.sh)*55-H.vsh*7.5)*dt;H.sh+=H.vsh*dt;
  const tiltK=opts.subtle?0.03:0.11;
  const tt=tx*tiltK+H.vlx*(opts.subtle?0.01:0.03);
  H.vt+=((tt-H.tilt)*120-H.vt*12)*dt;H.tilt+=H.vt*dt;
  H.vb+=((0-H.bob)*300-H.vb*14)*dt;H.bob+=H.vb*dt;
  H.vsq+=((0-H.sq)*280-H.vsq*15)*dt;H.sq+=H.vsq*dt;
  if(!act&&t>H.nh){
   H.vb=opts.subtle?-R(80,140):-R(300,460);
   H.nh=t+R(4,9);
  }
  if(H.ex!='idle'&&performance.now()>H.exU)H.ex='idle';
  if(t>nb){bt=t;nb=t+R(2.2,5.8);dbl=Math.random()<.2}
  const kb=t-bt,blink=Math.max(bl(kb),dbl?bl(kb-.28):0);
  const sw=Math.sin(t*1.6),al=.5+sw*.06-H.vlx*.06+(H.hov?.3:0),ar=.5+Math.sin(t*1.6+1.9)*.06+H.vlx*.06+(H.hov?.3:0),
   hy=cl(-H.vb*.012,-4,4);
  paint(g.color,g.outfit,t,H.lx,H.ly,blink,{ex:H.ex,tilt:H.tilt,sh:H.sh,bob:H.bob,breath:1+.017*Math.sin(t*2.2),
   sq:H.sq+cl(H.bob*.0035,-.07,.07),arms:[al,hy,ar,hy]});
  x.clearRect(0,0,cv.width,cv.height);
  x.drawImage(off,r[0],r[1],r[2],r[3],0,0,r[2],r[3]);
 };
 requestAnimationFrame(loop);
 const stop=()=>{on=0};stop.emote=(n,ms)=>{const lk={look_up:[0,-.9],look_down:[0,.9],look_left:[-.95,0],look_right:[.95,0]}[n];
  H.ex=lk?'look':(n||'idle');H.exU=performance.now()+ms+(n=='sleeping'?1800:0);
  const mv={happy:[-460,.12],wave:[-380,.08],surprised:[-600,.2],love:[-320,.1],proud:[-280,.06],squash:[0,.28],swallow:[-200,.2],wink:[-260,.06],question:[-180,.04],talking:[-220,.05]}[n]||[-160,.03];
  H.vb=mv[0];H.sq=mv[1];
  if(n=='error'||n=='annoyed')H.vsh=n=='error'?360:240;
  if(n=='dizzy')H.vt=16;
  if(lk){H.gx=lk[0];H.gy=lk[1];H.nl=performance.now()/1000+ms/1000+.3}};return stop;
}
return{snap,live,avFrame}})();

/* ── Avatares pequeños: aleatorios, reactivos y fluidos ──
   Se pre-renderizan fotogramas (mirada x parpadeo x expresión) y se animan con
   resortes (inclinación, salto, aplastamiento) sobre un <canvas> por avatar. */
const MA=(AVF=>{
const S=new WeakMap(),cl=(v,a,b)=>Math.max(a,Math.min(b,v)),R=(a,b)=>a+Math.random()*(b-a),
 RM=matchMedia('(prefers-reduced-motion:reduce)').matches;
let px=-1e4,py=-1e4,pt=0,last=performance.now();
addEventListener('pointermove',e=>{px=e.clientX;py=e.clientY;pt=performance.now()},{passive:true});
document.documentElement.addEventListener('pointerleave',()=>{px=py=-1e4});
const bk=a=>a<0?0:a<45?.55:a<120?1:a<165?.55:0;
function react(s,ex,ms,v){s.ex=ex;s.exUntil=performance.now()+ms;if(v&&!RM)s.vy=v}
function init(el){
 if(!el?.dataset?.av||!el.firstElementChild?.getContext) return null;
 const[col,out,crop,seed,mode]=el.dataset.av.split('|'),cv=el.firstElementChild,n=performance.now(),host=el.closest('button')||el;
 const s={el,cv,x:cv.getContext('2d'),col,out,crop,lite:mode=='lite',ph:(+seed||0)*1.9+Math.random()*6.28,gx:0,gy:0,tgx:0,tgy:0,gt:0,ex:'idle',exUntil:0,
  nl:n+R(500,2500),nb:n+R(700,3800),bs:-1,dbl:0,nh:n+R(2500,7000),nw:n+R(9000,22000),y:0,vy:0,r:0,vr:0,sx:0,key:''};
 host.addEventListener('pointerenter',()=>react(s,'happy',950,-85));
 host.addEventListener('pointerdown',()=>react(s,'happy',800,-120));
 S.set(el,s);return s}
function tick(now){
 const dt=Math.min(.05,Math.max(.001,(now-last)/1000));last=now;if(document.hidden)return;
 let bud=3;
 for(const el of document.querySelectorAll('.apw[data-av]')){
  const s=S.get(el)||init(el);if(!s)continue;
  const r=el.getBoundingClientRect();if(!r.width)continue;
  const dx=px-(r.left+r.width/2),dy=py-(r.top+r.height/2),near=Math.hypot(dx,dy)<200&&now-pt<3500;
  if(!s.lite&&!RM){
   if(near){s.tgx=cl(Math.round(dx/36),-2,2);s.tgy=cl(Math.round(dy/28),-1,1);s.nl=now+700}
   else if(now>s.nl){s.tgx=Math.random()<.35?0:Math.round(R(-2,2));s.tgy=Math.random()<.65?0:Math.round(R(-1,1));s.nl=now+R(1100,4200)}
   if(now-s.gt>65){s.gt=now;s.gx+=Math.sign(s.tgx-s.gx);s.gy+=Math.sign(s.tgy-s.gy)}
  }
  if(s.bs<0&&now>s.nb){s.bs=now;s.nb=now+R(1800,5400);s.dbl=Math.random()<.2}
  let lv=0;if(s.bs>=0){const a=now-s.bs;lv=Math.max(bk(a),s.dbl?bk(a-300):0);if(a>560)s.bs=-1}
  if(s.ex!='idle'&&now>s.exUntil)s.ex='idle';
  if(!s.lite&&!RM&&s.ex=='idle'&&now>s.nw){react(s,'wink',650);s.nw=now+R(12000,28000)}
  const gxv=s.gx*.4,gyv=s.gy*.45,key=gxv+'|'+gyv+'|'+lv+'|'+s.ex;
  if(key!==s.key){const f=AVF(s.col,s.out,s.crop,gxv,gyv,lv,s.ex,bud<=0);if(f){bud--;s.x.clearRect(0,0,84,84);s.x.drawImage(f,0,0);s.key=key}}
  if(!RM){
   const tr=near?cl(dx/240,-1,1)*.2:Math.sin(now/1000*.8+s.ph)*.03,tx=near?cl(dx/70,-1,1)*1.5:0;
   s.vr+=((tr-s.r)*140-s.vr*13)*dt;s.r+=s.vr*dt;s.sx+=(tx-s.sx)*(1-Math.exp(-dt*9));
   if(!s.lite&&now>s.nh){s.vy=-R(50,80);s.nh=now+R(3500,9500)}
   s.vy+=(-s.y*420-s.vy*20)*dt;s.y+=s.vy*dt;
   const sy=1+cl(-s.y/46,-.16,.16)+Math.sin(now/1000*2.2+s.ph)*.016,sxx=1/Math.sqrt(sy);
   s.cv.style.transform='translate('+s.sx.toFixed(2)+'px,'+s.y.toFixed(2)+'px) rotate('+s.r.toFixed(3)+'rad) scale('+sxx.toFixed(3)+','+sy.toFixed(3)+')'
  }
 }
}
(function loop(now){requestAnimationFrame(loop);tick(now)})(performance.now());
return{react}})(MK.avFrame);


/* ───── utilidades de movimiento (resorte, tween) y Slosh ───── */
const kc=(v,a,b)=>Math.min(b,Math.max(a,v)),QUART=t=>1-(1-t)**4,FLAT=t=>t,SWING=t=>t<.5?4*t**3:1-(-2*t+2)**3/2;
function mkTw(a,b,ms,ease,fn,done){let id,t0=performance.now();const f=n=>{const t=Math.min(1,(n-t0)/ms);fn(a+(b-a)*ease(t));if(t<1)id=requestAnimationFrame(f);else done&&done()};id=requestAnimationFrame(f);return()=>cancelAnimationFrame(id)}
function mkSp(x,fn){const s={x,v:0,t:x,raf:0,k:300,c:30,m:1,cb:null,
 to(t,k,c,m,cb){s.t=t;s.k=k;s.c=c;s.m=m||1;s.cb=cb||null;if(s.raf)return;let p=0;const f=n=>{const dt=p?Math.min(.02,(n-p)/1000):.016;p=n;s.v+=((-s.k*(s.x-s.t)-s.c*s.v)/s.m)*dt;s.x+=s.v*dt;fn(s.x);if(Math.abs(s.x-s.t)<.02&&Math.abs(s.v)<.02){s.x=s.t;s.v=0;s.raf=0;fn(s.x);const c=s.cb;s.cb=null;c&&c();return}s.raf=requestAnimationFrame(f)};s.raf=requestAnimationFrame(f)},
 stop(){cancelAnimationFrame(s.raf);s.raf=0},set(v){s.stop();s.x=v;s.v=0;fn(v)}};return s}

function Slosh(host,o={}){
 host.innerHTML=`<div class="so-track" role="slider" tabindex="0" aria-label="${o.label||'Volumen'}" aria-valuemin="0" aria-valuemax="100"><div class="so-fill"></div><div class="so-knob"></div></div>`;
 const tr=host.firstChild,fl=tr.children[0],kn=tr.children[1],K={visc:15,mom:55,tilt:45},flat=!!matchMedia?.('(prefers-reduced-motion: reduce)').matches;
 let val=o.value??50,hv=0,fill=val,fv=0,held=0,raf=0,prev=0,lastE=Math.round(val),last={v:val,t:0};
 const emit=()=>{const r=Math.round(val);if(r!==lastE){lastE=r;o.onChange?.(r)}};
 const paint=()=>{fl.style.width=fill.toFixed(2)+'%';kn.style.left=val.toFixed(2)+'%';fl.style.setProperty('--lean',(flat?0:kc(K.tilt/100*fv*3,-20,20)).toFixed(2)+'px');tr.setAttribute('aria-valuenow',Math.round(val))};
 const rest=()=>!held&&Math.abs(hv)<.01&&Math.abs(fv)<.01&&Math.abs(val-fill)<.02;
 const tick=t=>{const dt=prev?kc((t-prev)/16.67,0,2.5):1;prev=t;
  if(!held&&hv){val+=hv*dt;hv*=Math.pow(.86+K.mom/100*.115,dt);if(val<=0||val>=100){val=kc(val,0,100);hv=0}if(Math.abs(hv)<.01)hv=0}
  const soft=flat?0:K.visc/100;
  if(!soft){fill=val;fv=0}else{const sf=.34-soft*.29,dp=.74+soft*.22;fv+=(val-fill)*sf*dt;fv*=Math.pow(dp,dt);fill+=fv*dt;
   if(fill>100){fill=100;fv=-fv*.42}else if(fill<0){fill=0;fv=-fv*.42}
   if(Math.abs(val-fill)<.02&&Math.abs(fv)<.02){fill=val;fv=0}}
  paint();emit();if(rest()){raf=0;prev=0;return}raf=requestAnimationFrame(tick)};
 const run=()=>{if(!raf)raf=requestAnimationFrame(tick)};
 const at=x=>{const b=tr.getBoundingClientRect(),k=b.width/(tr.offsetWidth||b.width)||1;return kc((x-b.left)/k/tr.offsetWidth*100,0,100)};
 tr.addEventListener('pointerdown',e=>{try{tr.setPointerCapture(e.pointerId)}catch{}held=1;hv=0;val=at(e.clientX);last={v:val,t:e.timeStamp};run()});
 tr.addEventListener('pointermove',e=>{if(!held)return;const v=at(e.clientX),dt=Math.max(1,e.timeStamp-last.t);hv=(v-last.v)/dt*16.67;last={v,t:e.timeStamp};val=v;run()});
 const drop=()=>{if(!held)return;held=0;hv=kc(hv,-6,6);if(flat)hv=0;run()};
 tr.addEventListener('pointerup',drop);tr.addEventListener('pointercancel',drop);
 tr.addEventListener('keydown',e=>{const s=e.shiftKey?10:2,to=e.key=='ArrowRight'||e.key=='ArrowUp'?val+s:e.key=='ArrowLeft'||e.key=='ArrowDown'?val-s:e.key=='Home'?0:e.key=='End'?100:null;if(to===null)return;e.preventDefault();hv=0;val=kc(to,0,100);run()});
 paint();return{set(v){val=kc(v,0,100);hv=0;lastE=Math.round(val);run()}}}

/* ───── persistencia + difusión ───── */
const saveCfg=()=>{ls.set('miku_cfg',CFG);emit({k:'cfg',cfg:CFG});if(window.Bridge?.setSetting)Object.entries(CFG).forEach(([k,v])=>window.Bridge.setSetting(k,v))};
const saveAgents=()=>{ls.set('miku_agents',AG);emit({k:'agents',list:AG});window.Bridge?.saveAgents?.(AG);};
/* ── agentes en la isla (máx. 3): zona a la derecha de la tarjeta, arrastrar o botones ── */
const ISLMAX=3;
const normIsl=l=>{if(l.length&&!l.some(a=>a.isl!=null))l.forEach((a,i)=>a.isl=i<3?i+1:0);return l};
const islIds=()=>normIsl(AG).filter(a=>a.isl>0).sort((x,y)=>x.isl-y.isl).slice(0,ISLMAX).map(a=>a.id);
const setIsl=ids=>{window.__pop=1;ids=ids.slice(0,ISLMAX);AG.forEach(a=>{const k=ids.indexOf(a.id);a.isl=k>=0?k+1:0});saveAgents()};
(function(){
 let d=null;
 const dockEl=()=>document.getElementById('dock');
 document.addEventListener('pointerdown',e=>{
  if(e.button||e.target.closest('[data-rm]'))return;
  const src=e.target.closest('[data-ag],.dk[data-dk]');if(!src)return;
  d={id:src.dataset.ag||src.dataset.dk,from:src.classList.contains('dk')?'dock':'list',x:e.clientX,y:e.clientY,on:0,src,ghost:null,over:0};
 });
 document.addEventListener('pointermove',e=>{
  if(!d)return;
  if(!d.on){if(Math.hypot(e.clientX-d.x,e.clientY-d.y)<7)return;
   const a=AG.find(x=>x.id==d.id);if(!a){d=null;return}
   d.on=1;const g=document.createElement('div');g.className='dghost';g.style.setProperty('--pc',a.c);g.textContent=a.name;document.body.appendChild(g);d.ghost=g;
   d.src.classList.add('dragging');document.body.classList.add('dnd');getSelection?.().removeAllRanges()}
  d.ghost.style.transform=`translate(${e.clientX}px,${e.clientY}px)`;
  const dk=dockEl(),r=dk&&dk.getBoundingClientRect();
  d.over=!!(r&&e.clientX>=r.left-10&&e.clientX<=r.right+10&&e.clientY>=r.top-10&&e.clientY<=r.bottom+10);
  dk?.classList.toggle('over',d.over);
 });
 const end=e=>{
  if(!d)return;const w=d;d=null;if(!w.on)return;
  w.ghost?.remove();w.src.classList.remove('dragging');document.body.classList.remove('dnd');
  const dk=dockEl();dk?.classList.remove('over');window.__dnd=performance.now();
  const ids=islIds(),k=ids.indexOf(w.id);
  if(w.over&&dk){
   const slot=[...dk.querySelectorAll('.dks>*')].filter(el=>{const r=el.getBoundingClientRect();return e.clientX>r.left+r.width/2}).length;
   const next=ids.filter(x=>x!=w.id);
   if(k<0&&next.length>=ISLMAX){dk.classList.remove('full');void dk.offsetWidth;dk.classList.add('full');return}
   next.splice(Math.min(slot,next.length),0,w.id);setIsl(next);render();
  }else if(w.from=='dock'){setIsl(ids.filter(x=>x!=w.id));render()}
 };
 document.addEventListener('pointerup',end);document.addEventListener('pointercancel',end);
 document.addEventListener('click',e=>{if(performance.now()-(window.__dnd||0)<250){e.stopPropagation();e.preventDefault()}},true);
 document.addEventListener('click',e=>{
  const b=e.target.closest('[data-act="islAdd"],[data-act="islDel"],[data-rm]');if(!b)return;
  const ids=islIds();
  if(b.dataset.rm){setIsl(ids.filter(x=>x!=b.dataset.rm));render();return}
  const id=SELID;if(id=='miku')return;
  if(b.dataset.act=='islAdd'){if(ids.includes(id)||ids.length>=ISLMAX)return;setIsl([...ids,id])}else setIsl(ids.filter(x=>x!=id));
  render()});
})();


/* ───── componentes ───── */
const CHEV='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M6 9l6 6 6-6"/></svg>';
const TICK='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>';
const sw=(k,on)=>`<label class="sw sq"><input type="checkbox" data-k="${k}" ${on?'checked':''}><i></i></label>`;
const rg=k=>`<span class="so-host" data-k="${k}"></span>`;
const row=(t,h,c,fx)=>`<div class="row${fx?' fx':''}"><div><b>${t}</b>${h?`<small>${h}</small>`:''}</div><div class="ctl">${c}</div></div>`;

/* GlideSelect */
function GlideSelect(host,{options,value,label='Seleccionar',onChange}){
 const items=options.map(o=>typeof o=='string'?{value:o,label:o}:o);
 let cur=value,phase='closed',active=null,menu,pill,list,tmr,scrub=null;
 host.classList.add('gs');
 host.innerHTML=`<button type="button" class="gs-t" role="combobox" aria-haspopup="listbox" aria-expanded="false" aria-label="${esc(label)}"><span class="gs-wrap"><span class="gs-track"></span></span>${CHEV}</button>`;
 const trig=host.firstElementChild,wrap=trig.querySelector('.gs-wrap'),track=trig.querySelector('.gs-track');
 const sel=()=>items.findIndex(i=>i.value==cur);
 const paint=()=>{
   const i=sel();
   const txt=i>=0?items[i].label:'Seleccionar…';
   track.textContent=txt;
   track.classList.remove('marquee');
   track.style.transform='';
   setTimeout(()=>{
     const overflow=track.scrollWidth-wrap.clientWidth;
     if(overflow>4){
       track.style.setProperty('--mq-dist',`-${overflow+10}px`);
       track.classList.add('marquee');
     }
   },70);
 };
 paint();

 const getOptIndex = (target, clientX, clientY) => {
   if (target) {
     const o = target.closest?.('.gs-o');
     if (o && o.dataset.i != null) return +o.dataset.i;
   }
   if (clientX != null && clientY != null) {
     const el = document.elementFromPoint(clientX, clientY);
     const o = el ? el.closest?.('.gs-o') : null;
     if (o && o.dataset.i != null) return +o.dataset.i;
     if (list) {
       const opts = list.querySelectorAll('.gs-o');
       for (const opt of opts) {
         const r = opt.getBoundingClientRect();
         if (clientY >= r.top && clientY <= r.bottom) return +opt.dataset.i;
       }
     }
   }
   return null;
 };

 const setActive = (i) => {
   active = i;
   if (!list) return;
   list.querySelectorAll('.gs-o').forEach((o, n) => {
     o.id = trig.id + '-' + n;
     o.classList.toggle('active', n === i);
   });
   if (i != null) {
     trig.setAttribute('aria-activedescendant', trig.id + '-' + i);
     const opt = list.querySelector(`.gs-o[data-i="${i}"]`);
     if (opt && menu) {
       opt.scrollIntoView({ block: 'nearest' });
     }
   }
 };

 function open(viaKey){
   if(phase=='open')return;
   clearTimeout(tmr);
   trig.id=trig.id||('gs'+Math.random().toString(36).slice(2,7));
   host.style.zIndex='120';
   const _psec=host.closest('section')||host.closest('.card')||host.closest('.row');
   if(_psec)_psec.style.zIndex='100';
   window.SoundFX?.pop?.();
   menu=document.createElement('div');
   menu.className='gs-m closed';
   menu.innerHTML=`<div class="gs-l" role="listbox" aria-label="${esc(label)}"><span class="gs-p"></span>${items.map((it,i)=>`<div class="gs-o" role="option" data-i="${i}" aria-selected="${i==sel()}"><span class="n">${esc(it.label)}</span>${TICK}</div>`).join('')}</div>`;
   host.appendChild(menu);
   list=menu.firstChild;
   pill=list.firstChild;
   const _card=host.closest('.alert-item-card');
   if(_card)_card.style.zIndex='300';
   const r=host.getBoundingClientRect();
   const spaceBelow=window.innerHeight-r.bottom;
   const spaceAbove=r.top;
   const need=Math.min(240,items.length*36+16);
   if(spaceBelow<need&&spaceAbove>spaceBelow){
     menu.classList.add('up');
     menu.style.setProperty('--o','center bottom');
   }else{
     menu.classList.remove('up');
     menu.style.setProperty('--o','center top');
   }
   if(r.right-menu.offsetWidth<8){
     menu.style.left='0';
     menu.style.right='auto';
   }
   void menu.offsetHeight;
   menu.classList.remove('closed');
   menu.classList.add('open');
   phase='open';
   trig.setAttribute('aria-expanded','true');
   const s=sel();
   setActive(s>=0?s:(viaKey?0:null));

   list.addEventListener('pointerover',e=>{
     if(scrub && e.pointerType === 'touch') return;
     const idx = getOptIndex(e.target, e.clientX, e.clientY);
     if(idx != null && idx !== active) setActive(idx);
   });

   list.addEventListener('pointerdown',e=>{
     if(e.button !== 0) return;
     const idx = getOptIndex(e.target, e.clientX, e.clientY);
     if(idx != null) setActive(idx);
     scrub = { id: e.pointerId, startX: e.clientX, startY: e.clientY };
     if(e.pointerType === 'touch'){
       try { list.setPointerCapture(e.pointerId); } catch {}
     }
   });

   list.addEventListener('pointermove',e=>{
     if(!scrub) return;
     const idx = getOptIndex(null, e.clientX, e.clientY);
     if(idx != null && idx !== active) setActive(idx);
   });

   const up = e => {
     if(!scrub) return;
     scrub = null;
     if(e.type === 'pointerup'){
       const idx = getOptIndex(e.target, e.clientX, e.clientY);
       if(idx != null){
         pick(idx);
         return;
       }
     }
   };
   list.addEventListener('pointerup', up);
   list.addEventListener('pointercancel', () => { scrub = null; });

   list.addEventListener('click', e => {
     const idx = getOptIndex(e.target, e.clientX, e.clientY);
     if(idx != null) pick(idx);
   });
 }

 function close(instant){
   if(phase!='open')return;
   phase='closed';
   scrub=null;
   host.style.zIndex='';
   const _card=host.closest('.alert-item-card');
   if(_card)_card.style.zIndex='';
   const _psec=host.closest('section')||host.closest('.card')||host.closest('.row');
   if(_psec)_psec.style.zIndex='';
   trig.setAttribute('aria-expanded','false');
   trig.removeAttribute('aria-activedescendant');
   const m=menu;
   if(instant){m.remove();return}
   m.classList.remove('open');
   m.classList.add('closed');
   tmr=setTimeout(()=>m.remove(),130);
 }

 function pick(i){
   if(phase != 'open') return;
   const it=items[i];
   if(!it){close(true);return}
   if(it.value!=cur){
     cur=it.value;
     paint();
     window.SoundFX?.click?.();
     wrap.animate([{opacity:.6,filter:'blur(2px)'},{opacity:1,filter:'none'}],{duration:160});
     onChange?.(cur,it);
   }
   close(true);
   trig.focus({preventScroll:true});
 }

 trig.addEventListener('pointerdown',e=>{
   if(e.button!==0)return;
   trig.focus({preventScroll:true});
   phase=='open'?close():open(false);
   e.preventDefault();
 });

 trig.addEventListener('keydown',e=>{
   const k=e.key,n=items.length,c=active??Math.max(0,sel());
   if(phase!='open'){
     if(['Enter',' ','ArrowDown','ArrowUp'].includes(k)){
       e.preventDefault();
       open(true);
     }
     return;
   }
   const go=i=>{
     e.preventDefault();
     setActive(Math.min(n-1,Math.max(0,i)));
   };
   if(k=='ArrowDown'||k=='ArrowUp') go(active==null?c:c+(k=='ArrowDown'?1:-1));
   else if(k=='Home'||k=='End') go(k=='Home'?0:n-1);
   else if(k=='Enter'||k==' '){ e.preventDefault(); if(c>=0&&c<n) pick(c); }
   else if(k=='Escape'||k=='Tab'){ if(k=='Escape') e.preventDefault(); close(true); }
   else if(k.length==1&&!e.metaKey&&!e.ctrlKey&&!e.altKey){
     for(let j=1;j<=n;j++){
       const i=(c+j)%n;
       if(items[i].label.toLowerCase().startsWith(k.toLowerCase())){
         go(i);
         break;
       }
     }
   }
 });

 document.addEventListener('pointerdown',e=>{
   if(phase=='open'&&!host.contains(e.target)) close();
 },true);

 return{
   set(v){cur=v;paint()},
   items:()=>items
 };
}

/* HoldButton v2 */
function HoldButton(host,{label,doneLabel='Listo',holdLabel='Sigue manteniendo',icon='',hold=1800,onHold,small,variant='n'}){
 if(!host)return;
 const checkIcon='<svg style="width:15px;height:15px;stroke:currentColor;fill:none;stroke-width:2.2;stroke-linecap:round;stroke-linejoin:round" viewBox="0 0 24 24"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>';
 const layer=`<span class="t"><span class="r">${icon}${esc(label)}</span><span class="h">${esc(holdLabel)}</span><span class="dn d">${checkIcon}${esc(doneLabel)}</span></span>`;
 host.innerHTML=`<button type="button" class="hb ${variant} ${small?'sm':''}" data-phase="idle" data-s="idle" style="--hold:${hold}ms;--hb-hold:${hold}ms;--hb-cycles:${hold/1100}" aria-label="${esc(label)}">${layer}<span class="f" aria-hidden="true">${layer}</span></button>`;
 const b=host.firstElementChild||host.firstChild;if(!b)return;
 let phase='idle',p=0,raf=0,start=0,rect=null,pid=null,kind=null,tC=0;
 const ease={lin:t=>t,out:t=>1-Math.pow(1-t,3)};
 const go=(n,k=null)=>{phase=n;kind=k;b.dataset.phase=n;b.dataset.s=(n==='holding'?'hold':n)};
 const drive=(to,dur,fn)=>{cancelAnimationFrame(raf);const from=p,t0=performance.now(),step=now=>{const t=dur>0?Math.min(1,(now-t0)/dur):1;p=from+(to-from)*fn(t);b.style.setProperty('--hb-p',p.toFixed(4));if(t<1){raf=requestAnimationFrame(step);return}raf=0;if(to==1)done()};raf=requestAnimationFrame(step)};
 function done(){if(phase!='holding'||performance.now()-start<hold-50)return;clearTimeout(tC);go('done',kind);onHold?.();setTimeout(()=>{go('idle');drive(0,200,ease.out)},1400)}
 function begin(k){if(phase!='idle')return false;rect=b.getBoundingClientRect();start=performance.now();go('holding',k);drive(1,hold,ease.lin);tC=setTimeout(done,hold+100);return true}
 function release(){if(phase!='holding')return;clearTimeout(tC);go('idle');drive(0,200,ease.out)}
 const meas=()=>{if(b&&b.style){b.style.setProperty('--hb-w',b.offsetWidth+'px');b.style.setProperty('--hb-h',b.offsetHeight+'px')}};meas();if(window.ResizeObserver&&b){new ResizeObserver(meas).observe(b);}
 b.addEventListener('pointerdown',e=>{if(e.button!==0||!e.isPrimary||pid!==null)return;if(!begin('pointer'))return;pid=e.pointerId;try{b.setPointerCapture(e.pointerId)}catch{}});
 const end=e=>{if(e.pointerId!==pid)return;pid=null;try{b.releasePointerCapture(e.pointerId)}catch{}release()};
 b.addEventListener('pointerup',end);b.addEventListener('pointercancel',end);b.addEventListener('lostpointercapture',end);
 b.addEventListener('pointermove',e=>{if(e.pointerId!==pid||!rect)return;const P=10;if(e.clientX<rect.left-P||e.clientX>rect.right+P||e.clientY<rect.top-P||e.clientY>rect.bottom+P)end(e)});
 b.addEventListener('keydown',e=>{if(e.key=='Escape'){if(kind=='key')release();return}if(e.key==' '||e.key=='Enter'){e.preventDefault();if(!e.repeat)begin('key')}});
 b.addEventListener('keyup',e=>{if((e.key==' '||e.key=='Enter')&&kind=='key'){e.preventDefault();release()}});
 b.addEventListener('contextmenu',e=>e.preventDefault());
 addEventListener('blur',release);
}

/* ───── pantallas ───── */

/* ───── I18N DICCIONARIO BILINGÜE ───── */
const I18N = {
  es: {
    cat_general: "General",
    cat_island: "Isla Dinámica",
    cat_permisos: "Permisos y PC",
    cat_agentes: "Agentes",
    cat_modelos: "Modelos de IA",
    cat_keys: "Claves de API",
    cat_mcp: "Servidores MCP",
    cat_alertas: "Notificaciones y Juegos",
    cat_voz: "Sonido y voz",
    cat_link: "Miku-Link",
    cat_peligro: "Zona de peligro",
    isl_title: "Isla Dinámica",
    hover_open_title: "Abrir al pasar el cursor",
    hover_open_desc: "La isla se despliega al pasar el ratón y se repliega automáticamente al salir.",
    autoclose_title: "Cierre automático",
    autoclose_desc: "Tiempo de inactividad antes de que la isla se minimice por completo.",
    lang_title: "Idioma del sistema",
    lang_desc: "Idioma de las respuestas de texto y menús de la interfaz.",
    pers_title: "Personalidad",
    pers_desc: "Cambia el tono y estilo de las respuestas de Miku.",
    reset_title: "Restablecer",
    reset_btn: "Restablecer",
    reset_desc: "Restaura la configuración local de la interfaz a los valores predeterminados.",
    reset_note: "Tus claves y modelos del backend no se borran al restablecer los valores locales.",
    voice_title: "Voz de Miku",
    voice_active: "Voz activa",
    voice_active_desc: "Permite que Miku hable en voz alta al responder consultas.",
    voice_dials_title: "Centro de Control de Volumen",
    voice_vol_title: "Voz de Miku",
    voice_vol_desc: "Nivel de audio de las respuestas habladas",
    sfx_vol_title: "Alertas y Efectos",
    sfx_vol_desc: "Nivel para notificaciones de salud y avisos",
    mic_title: "Micrófono de entrada",
    mic_desc: "Dispositivo de audio para captura y reconocimiento de voz.",
    barge_title: "Interrumpir con voz (Barge-in)",
    barge_desc: "Hablar mientras Miku responde corta inmediatamente el audio.",
    wake_title: "Pausar palabra 'Miku'",
    wake_desc: "Desactiva temporalmente la detección del wake word.",
    ag_principal: "Principal",
    ag_custom: "Agente",
    ag_in_island: "En la isla",
    ag_create: "Crear agente",
    ag_delete: "Quitar agente",
    ag_add_isl: "Poner en la isla",
    ag_rem_isl: "Quitar de la isla",
    keys_title: "Modelos de Lenguaje (LLMs)",
    keys_note: "Las claves se guardan en el archivo .env de forma segura y se recargan al instante.",
    mcp_title: "Servidores MCP Conectados",
    mcp_note: "Model Context Protocol: Permite a Miku interactuar con SQLite, filesystem, navegadores y herramientas externas.",
    mcp_add: "Añadir Servidor MCP",
    alerts_title: "Alertas de Salud y Enfoque Activas",
    alerts_note: "Miku monitorea en segundo plano el tiempo en aplicaciones y te avisa cuando superas el límite establecido.",
    alerts_detectable: "Aplicaciones detectadas en tu equipo",
    alerts_mins: "minutos",
    link_title: "Vincular con Dispositivo Móvil",
    link_note: "Escanea este código QR con la app móvil de Miku para sincronizar portapapeles y notificaciones.",
    miku_original: "Miku (Blanco)"
  },
  en: {
    cat_general: "General",
    cat_island: "Dynamic Island",
    cat_permisos: "Permissions & PC",
    cat_agentes: "Agents",
    cat_modelos: "AI Models",
    cat_keys: "API Keys",
    cat_mcp: "MCP Servers",
    cat_alertas: "Games & Notifications",
    cat_voz: "Sound & Voice",
    cat_link: "Miku-Link",
    cat_peligro: "Danger Zone",
    isl_title: "Dynamic Island",
    hover_open_title: "Open on cursor hover",
    hover_open_desc: "Island expands on mouse hover and automatically collapses when leaving.",
    autoclose_title: "Auto-close timer",
    autoclose_desc: "Inactivity duration before the island minimizes completely.",
    lang_title: "System Language",
    lang_desc: "Language for text responses and user interface menus.",
    pers_title: "Personality",
    pers_desc: "Change tone and style of Miku's responses.",
    reset_title: "Factory Reset",
    reset_btn: "Reset",
    reset_desc: "Restore local interface settings to factory defaults.",
    reset_note: "Your backend API keys and models will not be deleted when resetting local settings.",
    voice_title: "Miku's Voice",
    voice_active: "Voice Active",
    voice_active_desc: "Allows Miku to speak aloud when answering queries.",
    voice_dials_title: "Volume Control Center",
    voice_vol_title: "Miku Voice",
    voice_vol_desc: "Audio level for spoken responses",
    sfx_vol_title: "Alerts & Effects",
    sfx_vol_desc: "Volume level for health alerts and system sounds",
    mic_title: "Input Microphone",
    mic_desc: "Audio device for voice recognition and capture.",
    barge_title: "Voice Barge-in",
    barge_desc: "Speaking while Miku is talking immediately stops audio playback.",
    wake_title: "Pause wake word 'Miku'",
    wake_desc: "Temporarily disables wake word listening.",
    ag_principal: "Main",
    ag_custom: "Agent",
    ag_in_island: "In Island",
    ag_create: "Create Agent",
    ag_delete: "Delete Agent",
    ag_add_isl: "Pin to Island",
    ag_rem_isl: "Remove from Island",
    keys_title: "Language Models (LLMs)",
    keys_note: "Keys are securely stored in the local .env file and reloaded instantly.",
    mcp_title: "Connected MCP Servers",
    mcp_note: "Model Context Protocol: Allows Miku to interact with SQLite, filesystem, and external tools.",
    mcp_add: "Add MCP Server",
    alerts_title: "Active Health & Focus Alerts",
    alerts_note: "Miku monitors app usage in the background and notifies you when exceeding your time limit.",
    alerts_detectable: "Detectable Apps on your PC",
    alerts_mins: "minutes",
    link_title: "Pair Mobile Device",
    link_note: "Scan this QR code with the Miku mobile app to sync clipboard and notifications.",
    miku_original: "Miku (White)"
  },
  ko: {
    cat_general: "일반 설정",
    cat_island: "다이내믹 아일랜드",
    cat_permisos: "권한 및 PC",
    cat_agentes: "에이전트",
    cat_modelos: "AI 모델",
    cat_keys: "API 키",
    cat_mcp: "MCP 서버",
    cat_alertas: "게임 및 알림",
    cat_voz: "사운드 및 음성",
    cat_link: "Miku-Link",
    cat_peligro: "위험 구역",
    isl_title: "다이내믹 아일랜드",
    hover_open_title: "마우스 오버 시 열기",
    hover_open_desc: "마우스를 올리면 아일랜드가 확장되고 벗어나면 자동으로 접힙니다.",
    autoclose_title: "자동 닫힘 시간",
    autoclose_desc: "아일랜드가 완전히 최소화되기 전 대기 시간.",
    lang_title: "시스템 언어",
    lang_desc: "텍스트 응답 및 사용자 인터페이스 언어 설정.",
    pers_title: "성격",
    pers_desc: "Miku의 응답 톤과 스타일을 변경합니다.",
    reset_title: "초기화",
    reset_btn: "초기화",
    reset_desc: "로컬 인터페이스 설정을 기본값으로 복원합니다.",
    reset_note: "로컬 설정을 초기화해도 백엔드 API 키 및 모델은 삭제되지 않습니다.",
    voice_title: "Miku 음성",
    voice_active: "음성 활성화",
    voice_active_desc: "질문에 답변할 때 Miku가 음성으로 말할 수 있도록 허용합니다.",
    voice_dials_title: "볼륨 제어 센터",
    voice_vol_title: "Miku 음성",
    voice_vol_desc: "음성 답변 볼륨 크기",
    sfx_vol_title: "알림 및 효과음",
    sfx_vol_desc: "건강 알림 및 시스템 사운드 볼륨",
    mic_title: "입력 마이크",
    mic_desc: "음성 인식 및 캡처를 위한 오디오 장치.",
    barge_title: "음성 끼어들기 (Barge-in)",
    barge_desc: "Miku가 말하는 중에 사용자가 말하면 음성 재생을 즉시 중지합니다.",
    wake_title: "'Miku' 호출어 일시정지",
    wake_desc: "호출어 감지를 일시적으로 비활성화합니다.",
    ag_principal: "메인",
    ag_custom: "에이전트",
    ag_in_island: "아일랜드 등록됨",
    ag_create: "에이전트 생성",
    ag_delete: "에이전트 삭제",
    ag_add_isl: "아일랜드에 고정",
    ag_rem_isl: "아일랜드에서 제거",
    keys_title: "언어 모델 (LLM)",
    keys_note: ".env 파일에 안전하게 저장되며 즉시 다시 로드됩니다.",
    mcp_title: "연결된 MCP 서버",
    mcp_note: "Model Context Protocol: SQLite, 파일 시스템, 외부 도구와 상호작용합니다.",
    mcp_add: "MCP 서버 추가",
    alerts_title: "건강 및 집중 알림",
    alerts_note: "백그라운드에서 앱 사용 시간을 모니터링하고 한도를 초과하면 알립니다.",
    alerts_detectable: "PC에서 감지 가능한 앱",
    alerts_mins: "분",
    link_title: "모바일 기기 연결",
    link_note: "Miku 모바일 앱으로 QR 코드를 스캔하여 클립보드와 알림을 동기화하세요.",
    miku_original: "Miku (화이트)"
  }
};

function t(k) {
  const lang = CFG.lang === 'ko' ? 'ko' : (CFG.lang === 'en' ? 'en' : 'es');
  return I18N[lang]?.[k] || I18N['es'][k] || k;
}

const CATS = [
  ['general', 'cat_general'],
  ['agentes', 'cat_agentes'],
  ['modelos', 'cat_modelos'],
  ['keys', 'cat_keys'],
  ['mcp', 'cat_mcp'],
  ['alertas', 'cat_alertas'],
  ['voz', 'cat_voz'],
  ['link', 'cat_link'],
  ['peligro', 'cat_peligro']
];
let CAT = ls.get('miku_cat', 'general');
if (!CATS.find(c => c[0] == CAT)) CAT = 'general';

const TOOLS = [
  ['copilot', 'GitHub Copilot / Git CLI'],
  ['mcp', 'Servidor MCP (General)'],
  ['gemini', 'Google Gemini Assistant'],
  ['antigravity', 'Antigravity IDE Assistant'],
  ['claude', 'Claude Code Assistant'],
  ['custom', 'Agente Personalizado']
];

const KEYS = ls.get('miku_keysaved', {});

const STATE = {
  keys: {},
  models: { current: { chat: '', computer_use: '', stt: '' }, available: { chat: [], computer_use: [], stt: [] } },
  execMode: 'full',
  execDetails: {},
  mcp: [],
  alerts: {},
  detectableApps: [],
  desktopStatus: {},
  pairUrl: 'miku://pair?s=init&ip=127.0.0.1',
  linkConnected: false,
  linkName: ''
};

function showToast(msg = 'Guardado correctamente', type = '') {
  const autoType = type || (/error|fallo|inválid|no se pudo/i.test(msg) ? 'er' : 'ok');
  if (window.MikuComponents?.toast?.show) {
    window.MikuComponents.toast.show(msg, { type: autoType, duration: 3000 });
    return;
  }
  let t = document.getElementById('toast');
  if (!t) {
    t = document.createElement('div');
    t.id = 'toast';
    document.body.appendChild(t);
  }
  t.textContent = msg;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 2200);
}

/* ───── WHEEL DIAL (Adaptado del componente React Liquid Spring Gauge) ───── */
function WheelDial(host, { value = 50, onChange, title = '', subtitle = '' }) {
  const N = 60, START = 120, SWEEP = 300, CX = 100, CY = 100, R = 52, waveAmp = 2.6;
  const rad = d => (d * Math.PI) / 180;
  const clamp = (v, a, b) => Math.min(b, Math.max(a, v));

  let target = value, cur = value, vel = 0, wave = 0, dragging = false;
  let rafId = null, lastT = performance.now();

  host.innerHTML = `
    <div class="hum-card">
      <div class="hum-card-title">${esc(title)}</div>
      <div class="hum" data-state="ok">
        <div class="hum-dial">
          <svg class="hwheel" viewBox="0 0 200 200" role="slider" tabindex="0" aria-label="${esc(title)}" aria-valuenow="${Math.round(value)}" aria-valuemin="0" aria-valuemax="100">
            <g class="hwheel-ticks"></g>
          </svg>
          <div class="hwheel-readout">
            <span class="hum-figure">${Math.round(value)}</span>
            <span class="hum-unit">%</span>
          </div>
        </div>
      </div>
      <div class="hum-card-sub">${esc(subtitle)}</div>
    </div>
  `;

  const hum = host.querySelector('.hum');
  const svg = host.querySelector('.hwheel');
  const gTicks = host.querySelector('.hwheel-ticks');
  const figure = host.querySelector('.hum-figure');

  function stateFor(v) {
    if (v < 12) return "crit";
    if (v < 25) return "low";
    if (v > 80) return "high";
    return "ok";
  }

  function fromPointer(e) {
    const b = svg.getBoundingClientRect();
    const x = ((e.clientX - b.left) / b.width) * 200 - CX;
    const y = ((e.clientY - b.top) / b.height) * 200 - CY;
    let deg = (Math.atan2(y, x) * 180) / Math.PI;
    if (deg < 0) deg += 360;
    let rel = deg - START;
    if (rel < 0) rel += 360;
    if (rel > SWEEP) rel = rel < SWEEP + 30 ? SWEEP : 0;
    const next = Math.round((rel / SWEEP) * 100);
    target = next;
    onChange?.(next);
  }

  const lines = [];
  for (let i = 0; i < N; i++) {
    const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
    line.setAttribute("stroke-width", "2");
    line.setAttribute("stroke-linecap", "round");
    gTicks.appendChild(line);
    lines.push(line);
  }

  function tick(t) {
    const dt = Math.min(34, t - lastT) / 16.67;
    lastT = t;

    const k = 0.16;
    const d = 0.76;
    vel += (target - cur) * k * dt;
    vel *= Math.pow(d, dt);
    cur += vel * dt;
    if (Math.abs(target - cur) < 0.02 && Math.abs(vel) < 0.02) {
      cur = target;
      vel = 0;
    }
    wave += dt * 0.055;

    const display = cur;
    const st = stateFor(display);
    hum.setAttribute("data-state", st);
    figure.textContent = Math.round(display);
    svg.setAttribute("aria-valuenow", Math.round(display));

    const f = clamp(display, 0, 100) / 100;
    const amp = 1 + (display / 100) * waveAmp;

    for (let i = 0; i < N; i++) {
      const tf = i / (N - 1);
      const on = tf <= f + 0.001;
      const behind = f - tf;
      const comet = on && behind < 0.14 ? (1 - behind / 0.14) * 8 : 0;
      const undulate = on ? Math.sin(wave + i * 0.5) * amp : 0;
      const len = (on ? 24 : 21) + comet + undulate;
      const a = rad(START + tf * SWEEP);
      const cos = Math.cos(a);
      const sin = Math.sin(a);

      const x1 = CX + cos * R;
      const y1 = CY + sin * R;
      const x2 = CX + cos * (R + len);
      const y2 = CY + sin * (R + len);

      const line = lines[i];
      line.setAttribute("x1", x1.toFixed(2));
      line.setAttribute("y1", y1.toFixed(2));
      line.setAttribute("x2", x2.toFixed(2));
      line.setAttribute("y2", y2.toFixed(2));
      line.style.stroke = on ? "var(--hum-lit)" : "currentColor";
      line.setAttribute("stroke-opacity", on ? (0.42 + (1 - clamp(behind, 0, 1)) * 0.58).toFixed(2) : "0.24");
    }

    rafId = requestAnimationFrame(tick);
  }
  rafId = requestAnimationFrame(tick);

  svg.addEventListener("pointerdown", e => {
    e.stopPropagation();
    dragging = true;
    svg.setAttribute("data-dragging", "true");
    try { svg.setPointerCapture(e.pointerId); } catch (_) {}
    fromPointer(e);
  });
  svg.addEventListener("pointermove", e => {
    if (dragging) fromPointer(e);
  });
  const stopDrag = () => {
    dragging = false;
    svg.removeAttribute("data-dragging");
  };
  svg.addEventListener("pointerup", stopDrag);
  svg.addEventListener("pointercancel", stopDrag);

  svg.addEventListener("keydown", e => {
    if (e.key === "ArrowRight" || e.key === "ArrowUp") {
      target = clamp(target + 2, 0, 100);
      onChange?.(target);
    }
    if (e.key === "ArrowLeft" || e.key === "ArrowDown") {
      target = clamp(target - 2, 0, 100);
      onChange?.(target);
    }
  });

  return {
    set(v) { target = clamp(v, 0, 100); },
    destroy() { if (rafId) cancelAnimationFrame(rafId); }
  };
}

/* ───── GENERADOR QR STANDALONE ───── */
const QR = (() => {
  const ECC = [10, 16, 26, 18, 24, 16, 18, 22, 22, 26], BLK = [1, 1, 1, 2, 2, 4, 4, 4, 5, 5];
  const mul = (x, y) => { let z = 0; for (let i = 7; i >= 0; i--) { z = (z << 1) ^ ((z >>> 7) * 0x11D); z ^= ((y >>> i) & 1) * x; } return z; };
  const raw = v => { let r = (16 * v + 128) * v + 64; if (v >= 2) { const n = Math.floor(v / 7) + 2; r -= (25 * n - 10) * n - 55; if (v >= 7) r -= 36; } return r >> 3; };
  const cap = v => raw(v) - ECC[v - 1] * BLK[v - 1];
  const rsDiv = d => { const r = Array(d).fill(0); r[d - 1] = 1; let root = 1; for (let i = 0; i < d; i++) { for (let j = 0; j < d; j++) { r[j] = mul(r[j], root); if (j + 1 < d) r[j] ^= r[j + 1]; } root = mul(root, 2); } return r; };
  const rsRem = (data, div) => { const r = div.map(() => 0); for (const b of data) { const f = b ^ r.shift(); r.push(0); div.forEach((c, i) => r[i] ^= mul(c, f)); } return r; };
  const bit = (x, i) => ((x >>> i) & 1) != 0;
  function make(text) {
    const bytes = [...new TextEncoder().encode(text)]; let ver = 1;
    for (; ver <= 10; ver++) { if (4 + (ver < 10 ? 8 : 16) + bytes.length * 8 <= cap(ver) * 8) break; }
    if (ver > 10) throw new Error('QR: texto demasiado largo');
    const bits = [], put = (v, n) => { for (let i = n - 1; i >= 0; i--) bits.push((v >>> i) & 1); }, total = cap(ver) * 8;
    put(4, 4); put(bytes.length, ver < 10 ? 8 : 16); bytes.forEach(b => put(b, 8));
    put(0, Math.min(4, total - bits.length)); put(0, (8 - bits.length % 8) % 8); for (let p = 0xEC; bits.length < total; p ^= 0xEC ^ 0x11) put(p, 8);
    const data = []; for (let i = 0; i < bits.length; i += 8) { let b = 0; for (let j = 0; j < 8; j++) b = b << 1 | bits[i + j]; data.push(b); }
    const nb = BLK[ver - 1], el = ECC[ver - 1], rc = raw(ver), ns = nb - rc % nb, sl = Math.floor(rc / nb), div = rsDiv(el), blocks = [];
    for (let i = 0, k = 0; i < nb; i++) { const dat = data.slice(k, k + sl - el + (i < ns ? 0 : 1)); k += dat.length; const ecc = rsRem(dat, div); if (i < ns) dat.push(0); blocks.push(dat.concat(ecc)); }
    const all = []; for (let i = 0; i < blocks[0].length; i++) blocks.forEach((b, j) => { if (i != sl - el || j >= ns) all.push(b[i]); });
    const n = ver * 4 + 17, M = Array.from({ length: n }, () => Array(n).fill(false)), F = Array.from({ length: n }, () => Array(n).fill(false));
    const sf = (x, y, d) => { M[y][x] = d; F[y][x] = true; };
    for (let i = 0; i < n; i++) { sf(6, i, i % 2 == 0); sf(i, 6, i % 2 == 0); }
    const finder = (x, y) => { for (let dy = -4; dy <= 4; dy++) for (let dx = -4; dx <= 4; dx++) { const d = Math.max(Math.abs(dx), Math.abs(dy)), xx = x + dx, yy = y + dy; if (xx >= 0 && xx < n && yy >= 0 && yy < n) sf(xx, yy, d != 2 && d != 4); } };
    finder(3, 3); finder(n - 4, 3); finder(3, n - 4);
    const ap = []; if (ver > 1) { const na = Math.floor(ver / 7) + 2, st = Math.ceil((ver * 4 + 4) / (na * 2 - 2)) * 2; ap.push(6); for (let p = n - 7; ap.length < na; p -= st) ap.splice(1, 0, p); }
    ap.forEach((a, i) => ap.forEach((b, j) => { if (!((i == 0 && j == 0) || (i == 0 && j == ap.length - 1) || (i == ap.length - 1 && j == 0))) for (let dy = -2; dy <= 2; dy++) for (let dx = -2; dx <= 2; dx++) sf(a + dx, b + dy, Math.max(Math.abs(dx), Math.abs(dy)) != 1); }));
    const fmt = m => { const d = m; let r = d; for (let i = 0; i < 10; i++) r = (r << 1) ^ ((r >>> 9) * 0x537); const b = ((d << 10) | r) ^ 0x5412;
      for (let i = 0; i <= 5; i++) sf(8, i, bit(b, i)); sf(8, 7, bit(b, 6)); sf(8, 8, bit(b, 7)); sf(7, 8, bit(b, 8)); for (let i = 9; i < 15; i++) sf(14 - i, 8, bit(b, i));
      for (let i = 0; i < 8; i++) sf(n - 1 - i, 8, bit(b, i)); for (let i = 8; i < 15; i++) sf(8, n - 15 + i, bit(b, i)); sf(8, n - 8, true); };
    fmt(0);
    for (let i = 0, right = n - 1; right >= 1; right -= 2) { if (right == 6) right = 5; for (let v = 0; v < n; v++) for (let j = 0; j < 2; j++) { const x = right - j, up = ((right + 1) & 2) == 0, y = up ? n - 1 - v : v; if (!F[y][x] && i < all.length * 8) { M[y][x] = bit(all[i >>> 3], 7 - (i & 7)); i++; } } }
    const apply = m => { for (let y = 0; y < n; y++) for (let x = 0; x < n; x++) { let inv; switch (m) { case 0: inv = (x + y) % 2 == 0; break; case 1: inv = y % 2 == 0; break; case 2: inv = x % 3 == 0; break; case 3: inv = (x + y) % 3 == 0; break; case 4: inv = (Math.floor(x / 3) + Math.floor(y / 2)) % 2 == 0; break; case 5: inv = x * y % 2 + x * y % 3 == 0; break; case 6: inv = (x * y % 2 + x * y % 3) % 2 == 0; break; default: inv = ((x + y) % 2 + x * y % 3) % 2 == 0; } if (!F[y][x] && inv) M[y][x] = !M[y][x]; } };
    apply(0);
    return M;
  }
  function draw(cv, text, px = 140, fg = '#111', bg = '#fff') {
    if (!cv) return;
    const M = make(text), n = M.length, q = 3, s = Math.max(1, Math.floor(px / (n + 2 * q))), d = s * (n + 2 * q);
    cv.width = cv.height = d; cv.style.width = cv.style.height = px + 'px';
    const x = cv.getContext('2d'); x.fillStyle = bg; x.fillRect(0, 0, d, d); x.fillStyle = fg;
    for (let y = 0; y < n; y++) for (let i = 0; i < n; i++) if (M[y][i]) x.fillRect((i + q) * s, (y + q) * s, s, s);
  }
  return { make, draw };
})();

const DEF = { voice: 1, autoclose: 15, voice_volume: 80, sfx_volume: 60, barge_in: 1, wake_paused: 0, mic: 'default', personality: 'calm', hover_open: 0, lang: 'es', local_net: 1, biometric: 1 };
for (const k in DEF) if (!(k in CFG)) CFG[k] = DEF[k];

const inp = (id, ph, type = 'text', w = '') => `<input class="tx-in" id="${id}" type="${type}" placeholder="${esc(ph)}" autocomplete="off" spellcheck="false" ${w ? `style="width:${w}"` : ''}>`;
const note = t => `<p class="nt">${t}</p>`;
const stat = (id, on, t) => `<span class="pill ${on ? 'on' : ''}" id="${id}">${t}</span>`;

const NAV_GROUPS = [
  {
    title: 'BASE',
    items: [
      { id: 'general',  label: 'cat_general',  icon: 'gear' }
    ]
  },
  {
    title: 'INTELIGENCIA',
    items: [
      { id: 'agentes',  label: 'cat_agentes',  icon: 'bot' },
      { id: 'modelos',  label: 'cat_modelos',  icon: 'sparkles' },
      { id: 'keys',     label: 'cat_keys',     icon: 'key' },
      { id: 'mcp',      label: 'cat_mcp',      icon: 'server' }
    ]
  },
  {
    title: 'ASISTENCIA',
    items: [
      { id: 'alertas',  label: 'cat_alertas',  icon: 'bell' },
      { id: 'voz',      label: 'cat_voz',      icon: 'mic' },
      { id: 'link',     label: 'cat_link',     icon: 'link' }
    ]
  },
  {
    title: 'SISTEMA',
    items: [
      { id: 'peligro',  label: 'cat_peligro',  icon: 'danger', danger: true }
    ]
  }
];

function railHtml() {
  return NAV_GROUPS.map(g => `
    <div class="nav-group">
      <div class="nav-group-title">${g.title}</div>
      <div class="nav-group-items">
        ${g.items.map(it => `
          <button class="cat nv ${it.danger ? 'dg' : ''}" data-cat="${it.id}">
            <svg class="ic" width="18" height="18"><use href="#ic-${it.icon}"/></svg>
            <span>${t(it.label)}</span>
          </button>
        `).join('')}
      </div>
    </div>
  `).join('');
}

const V = {};
V.island = () => (V.general ? V.general() : '');
V.permisos = () => (V.general ? V.general() : '');


/* ── Componente de Slider Suave con perilla circular acordada (miku-catalogo.html) ── */
function SmoothSlider(host, { value = 80, min = 0, max = 100, step = 1, unit = '%', onChange }) {
  let cur = Math.max(min, Math.min(max, value));
  let dragging = false;
  let activePointerId = null;
  const initPct = ((cur - min) / (max - min) * 100).toFixed(1);

  host.innerHTML = `
    <div class="so-slider" tabindex="0" role="slider" aria-valuenow="${cur}" aria-valuemin="${min}" aria-valuemax="${max}">
      <svg class="so-spk so-spk-mute" viewBox="0 0 24 24" title="Silenciar"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><line x1="23" y1="9" x2="17" y2="15"/><line x1="17" y1="9" x2="23" y2="15"/></svg>
      <div class="so-slider-track">
        <div class="so-slider-fill" style="width: ${initPct}%"></div>
        <div class="so-slider-thumb" style="left: ${initPct}%"></div>
      </div>
      <svg class="so-spk so-spk-high" viewBox="0 0 24 24" title="100%"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"/></svg>
      <span class="so-slider-val">${Math.round(cur)}${unit}</span>
    </div>
  `;

  const slider = host.querySelector('.so-slider');
  const track = host.querySelector('.so-slider-track');
  const fill = host.querySelector('.so-slider-fill');
  const thumb = host.querySelector('.so-slider-thumb');
  const valText = host.querySelector('.so-slider-val');
  const spkMute = host.querySelector('.so-spk-mute');
  const spkHigh = host.querySelector('.so-spk-high');

  const syncDom = (pct) => {
    fill.style.width = pct + '%';
    if (thumb) thumb.style.left = pct + '%';
    valText.textContent = Math.round(cur) + unit;
    slider.setAttribute('aria-valuenow', Math.round(cur));
  };

  const update = (clientX) => {
    const rect = track.getBoundingClientRect();
    if (!rect.width) return;
    const ratio = Math.max(0, Math.min(1, (clientX - rect.left) / rect.width));
    let raw = min + ratio * (max - min);
    if (step > 0) raw = Math.round(raw / step) * step;
    cur = Math.max(min, Math.min(max, raw));
    const pct = ((cur - min) / (max - min) * 100).toFixed(1);
    syncDom(pct);
    onChange?.(cur);
  };

  const onPointerMove = (e) => {
    if (!dragging) return;
    update(e.clientX);
  };

  const onPointerUp = () => {
    if (dragging) {
      dragging = false;
      slider.classList.remove('dragging');
      window.removeEventListener('pointermove', onPointerMove);
      window.removeEventListener('pointerup', onPointerUp);
      window.removeEventListener('pointercancel', onPointerUp);
      if (activePointerId !== null) {
        try { slider.releasePointerCapture(activePointerId); } catch (_) {}
        activePointerId = null;
      }
    }
  };

  const startDrag = (e) => {
    if (e.button !== 0) return;
    if (e.target.closest('.so-spk') || e.target.closest('.so-slider-val')) return;
    dragging = true;
    slider.classList.add('dragging');
    activePointerId = e.pointerId;
    try { slider.setPointerCapture(e.pointerId); } catch (_) {}
    window.addEventListener('pointermove', onPointerMove, { passive: true });
    window.addEventListener('pointerup', onPointerUp);
    window.addEventListener('pointercancel', onPointerUp);
    update(e.clientX);
    window.SoundFX?.click?.();
    e.preventDefault();
  };
  slider.addEventListener('pointerdown', startDrag);

  spkMute?.addEventListener('click', () => {
    cur = min;
    syncDom('0');
    window.SoundFX?.pop?.();
    onChange?.(cur);
  });

  spkHigh?.addEventListener('click', () => {
    cur = max;
    syncDom('100');
    window.SoundFX?.pop?.();
    onChange?.(cur);
  });

  return {
    set(v) {
      cur = Math.max(min, Math.min(max, v));
      const pct = ((cur - min) / (max - min) * 100).toFixed(1);
      syncDom(pct);
    }
  };
}

// 1. GENERAL
V.general = () => `
<section>
  <h2>${t('isl_title')}</h2>
  ${row(t('hover_open_title'), t('hover_open_desc'), sw('hover_open', CFG.hover_open))}
  ${row(t('autoclose_title'), t('autoclose_desc'), `<span id="gs-ac"></span>`)}
  ${row(t('lang_title'), t('lang_desc'), `<span id="gs-lang"></span>`)}
  ${row(t('pers_title'), t('pers_desc'), `<span id="gs-pers"></span>`)}
</section>
<section>
  <h2>Nivel de Permisos y Modos de Ejecución</h2>
  <div style="font-size:12.5px;color:var(--mut);margin-bottom:12px">
    Define los límites de permisos con los que Miku puede interactuar con tu PC, ejecutar comandos y manipular archivos al estilo de Antigravity.
  </div>
  <div class="exec-mode-grid">
    <div class="mode-card ${STATE.execMode === 'full' ? 'active on' : ''}" data-setmode="full">
      <div class="mode-card-head">
        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg> <span>Toda mi PC</span>
      </div>
      <div class="mode-card-desc">
        Acceso total a la consola de Windows, cualquier disco o archivo, scripts y automatización de interfaz.
      </div>
    </div>
    <div class="mode-card ${STATE.execMode === 'sandbox' ? 'active on' : ''}" data-setmode="sandbox">
      <div class="mode-card-head">
        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/></svg> <span>Sandbox</span>
      </div>
      <div class="mode-card-desc">
        Confinada al espacio de trabajo del proyecto. Protege carpetas del sistema y archivos fuera del workspace.
      </div>
    </div>
    <div class="mode-card ${STATE.execMode === 'restricted' ? 'active on' : ''}" data-setmode="restricted">
      <div class="mode-card-head">
        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg> <span>Restringido</span>
      </div>
      <div class="mode-card-desc">
        Solo lectura y consultas seguras. Comandos de consola, scripts y clics automáticos quedan bloqueados.
      </div>
    </div>
  </div>
  ${note('Puedes alternar entre estos modos en cualquier momento. Los cambios se aplican de forma inmediata sin reiniciar el servidor.')}
</section>
<section>
  <h2>Actualizaciones de Software</h2>
  ${row('Miku Desktop v0.2.0 (Beta)', 'Comprueba si hay nuevas versiones publicadas en GitHub.', `<button class="btn sm" id="btn-check-update">Buscar actualización</button>`)}
  <div id="update-status" style="margin-top:6px;font-size:12.5px;color:var(--mut)"></div>
</section>
<section>
  <h2>Apoyar el Proyecto · Ko-fi</h2>
  <div style="background:var(--s2);border:1px solid var(--ln);border-radius:16px;padding:16px 18px;display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap">
    <div style="display:flex;align-items:center;gap:14px;min-width:0;flex:1">
      <img src="assets/kofi_badge.png" width="44" height="44" style="border-radius:12px;object-fit:contain;flex:none" alt="Ko-fi">
      <div style="min-width:0">
        <div style="font-weight:700;font-size:13.5px;color:var(--tx)">Invítame un café en Ko-fi</div>
        <div style="font-size:11.5px;color:var(--mut);margin-top:3px;line-height:1.4">
          Tu aporte ayuda a cubrir pruebas de APIs de IA y mantener Miku libre, abierta y sin anuncios.
        </div>
      </div>
    </div>
    <a href="https://ko-fi.com/cxmlo" target="_blank" rel="noopener noreferrer" class="btn p" style="text-decoration:none;white-space:nowrap">
      Apoyar en Ko-fi
    </a>
  </div>
</section>
<section>
  <h2>${t('reset_title')}</h2>
  ${row(t('reset_btn'), t('reset_desc'), `<span id="hb-reset"></span>`)}
  ${note(t('reset_note'))}
</section>
`;

// 2. VOZ Y SONIDO (Barras con click sostenido y normal)
V.voz = () => `
<section>
  <h2>${t('voice_dials_title')}</h2>
  ${row(t('voice_vol_title'), t('voice_vol_desc'), `<div id="slider-voice" style="width:240px"></div>`, 1)}
  ${row(t('sfx_vol_title'), t('sfx_vol_desc'), `<div id="slider-sfx" style="width:240px"></div>`, 1)}
</section>
<section>
  <h2>${t('voice_title')}</h2>
  ${row(t('voice_active'), t('voice_active_desc'), sw('voice', CFG.voice))}
  ${row(t('mic_title'), t('mic_desc'), `<span id="gs-mic"></span>`)}
  ${row(t('barge_title'), t('barge_desc'), sw('barge_in', CFG.barge_in))}
  ${row(t('wake_title'), t('wake_desc'), sw('wake_paused', CFG.wake_paused))}
</section>
`;

// 3. AGENTES (Agentes secundarios/personalizados; Miku Blanco es el avatar principal fijo en el sidebar)
V.agentes = () => {
  if ((SELID === 'miku' || !SELID) && AG.length) {
    SELID = AG[0].id;
  }
  const sel = AG.find(a => a.id == SELID) || AG[0] || { id: 'custom', name: 'Agente', c: '#F2A765' };
  const ids = islIds();
  const inI = ids.includes(sel.id);

  const chip = (g, k) => `<button class="dk" data-dk="${esc(g.id)}" style="--pc:${g.c}" title="${esc(g.name)}"><span class="apw" data-av="${g.c}|${g.outfit || 'none'}|full|${k}|"><canvas class="apimg" width="84" height="84"></canvas></span><em>${esc(g.name)}</em><i class="dkx" data-rm="${esc(g.id)}" title="Quitar de la isla"><svg class="ic" width="12" height="12"><use href="#ic-trash"/></svg></i></button>`;
  const dock = () => `<div class="dock" id="dock"><small class="dkt">En la isla · ${ids.length}/${ISLMAX}</small><div class="dks">${[0, 1, 2].map(k => { const g = AG.find(x => x.id == ids[k]); return g ? chip(g, k) : `<span class="dk e"></span>`; }).join('')}</div></div>`;

  return `
<div class="ag-hero-card">
  <div class="ag-hero-main">
    <div class="ag-canvas-wrap"><canvas class="hl" data-who="${esc(sel.id)}"></canvas></div>
    <div class="ag-hero-info">
      <h2>${esc(sel.name)}<em>${t('ag_custom')}</em></h2>
      <p><i class="sd ${inI ? 'on' : ''}"></i><span class="nt" style="padding:0">${inI ? 'En la isla' : 'Disponible'}</span></p>
      <div style="margin-top:8px;display:flex;gap:8px;">
        <button class="btn sm ${inI ? '' : 'p'}" data-act="${inI ? 'islDel' : 'islAdd'}">${inI ? t('ag_rem_isl') : t('ag_add_isl')}</button>
      </div>
    </div>
  </div>
  ${dock()}
</div>

<section>
  <h2>Seleccionar Agente Personalizado</h2>
  <div class="apg">
    ${AG.map((a, idx) => `
      <button class="ap ${SELID === a.id ? 'on swp' : ''} ${ids.includes(a.id) ? ' isl' : ''}" data-ag="${esc(a.id)}" data-sel="${esc(a.id)}" style="--pc:${a.c}" title="${esc(a.name)}">
        <span class="apw" data-av="${a.c}|${a.outfit || 'none'}|full|${idx + 1}|"><canvas class="apimg" width="84" height="84"></canvas></span>
        <span>${esc(a.name)}</span>
      </button>
    `).join('')}
  </div>
  ${note('Arrastra cualquier agente a la isla para activarlo, o tócalo para editarlo.')}
</section>

<section>
  <h2>Prioridad en la Isla Dinámica (Arrastra para reordenar · Los 3 primeros van a la isla)</h2>
  <div id="ag-reorder-list" class="ro" style="margin-top:14px;position:relative;display:block"></div>
</section>

${sel ? `
<section>
  <h2>Configuración de ${esc(sel.name)}</h2>
  ${row('Nombre', 'Identificador visible en la Isla Dinámica', `<input class="tx-in" id="ag-edit-name" type="text" value="${esc(sel.name)}" placeholder="Nombre del agente" autocomplete="off" spellcheck="false" style="width:220px">`, 1)}
  ${row('Color distintivo', 'Color del halo y ojos del agente', `
    <div class="chips" style="align-items:center">
      ${PRESET.map(hex => `<button class="sw8 ${sel.c.toLowerCase() === hex.toLowerCase() ? 'on' : ''}" data-color="${hex}" style="--c:${hex}" title="${hex}"></button>`).join('')}
      <label class="colorin" title="Seleccionar color personalizado" style="display:inline-flex;align-items:center;justify-content:center;cursor:pointer">
        <input type="color" id="ag-colin" value="${sel.c.toLowerCase()}">
      </label>
    </div>
  `)}
  ${row('Modelo / API de IA', 'Asigna un proveedor o modelo específico para este agente (opcional)', `<span id="gs-ag-model"></span>`)}
  ${row('Servidor MCP Asignado', 'Conecta un servidor de herramientas exclusivo para este agente', `<span id="gs-ag-mcp"></span>`)}
  ${row('Generador de Prompt con IA', 'Describe su función y redacta automáticamente el rol del agente', `
    <div style="display:flex;gap:8px;align-items:center;width:100%;justify-content:flex-end;flex-wrap:wrap">
      <input class="tx-in" id="ag-ai-desc" placeholder="Ej: Revisar código y hacer pull requests..." style="flex:1;min-width:210px;height:36px">
      <button type="button" class="btn p sm" id="btn-gen-prompt" style="height:36px;padding:0 14px">
        <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z"/></svg>
        <span>Generar Prompt</span>
      </button>
    </div>
  `, 1)}
  ${row('Instrucciones / Rol', 'Prompt del sistema específico para este agente', `<textarea class="tx-in" id="ag-edit-prompt" placeholder="Instrucciones del sistema para este agente..." style="width:100%;height:78px;resize:vertical">${esc(sel.prompt || sel.role || '')}</textarea>`, 1)}
  ${row('Quitar agente', 'Elimina este agente de tu lista', `<span id="hb-del-curr"></span>`)}
</section>
` : ''}

<section>
  <h2>${t('ag_create')}</h2>
  ${row('Rol inicial', 'Plantilla o especialidad', `<span id="gs-tool"></span>`)}
  ${row('Nombre', '', inp('ag-name', 'Mi agente', 'text', '220px'), 1)}
  ${row('Modelo / API de IA', 'Asigna un modelo específico o deja el automático', `<span id="gs-new-ag-model"></span>`)}
  ${row('Generar Instrucciones con IA', 'Redacta automáticamente las instrucciones del nuevo agente', `
    <div style="display:flex;gap:8px;align-items:center;width:100%;justify-content:flex-end;flex-wrap:wrap">
      <input class="tx-in" id="ag-new-ai-desc" placeholder="Describe la tarea que realizará este nuevo agente..." style="flex:1;min-width:210px;height:36px">
      <button type="button" class="btn p sm" id="btn-new-gen-prompt" style="height:36px;padding:0 14px">
        <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z"/></svg>
        <span>Generar con IA</span>
      </button>
    </div>
  `, 1)}
  ${row('Instrucciones / Contexto', 'Prompt del sistema o personalidad específica para este agente', `<textarea class="tx-in" id="ag-prompt" placeholder="Ej: Eres un asistente especializado en análisis de código..." style="width:100%;height:76px;resize:vertical"></textarea>`, 1)}
  ${row('Crear agente', 'Mantén pulsado para confirmar y añadir agente', `<span id="hb-ag-add"></span>`)}
</section>
`;
};

function selAgent(id, noEmit) {
  SELID = (id === 'miku' || !id) ? 'miku' : (AG.some(a => a.id == id) ? id : 'miku');
  if (!noEmit) emit({ k: 'select', who: SELID });
}

// 4. MODELOS DE IA
V.modelos = () => {
  const hasProviders = STATE.models?.has_providers || (STATE.models?.active_providers && STATE.models.active_providers.length > 0);
  const warnBanner = !hasProviders ? `
  <div class="al er" role="alert" style="margin-bottom:4px">
    <svg class="ic" viewBox="0 0 24 24"><path d="M10.3 3.9L1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"/><path d="M12 9v4M12 17h.01"/></svg>
    <div class="b">
      <b>No tienes claves de API configuradas</b>
      <small>Para activar modelos de IA, ve a la pestaña <b>Claves de API</b> e ingresa al menos una clave (Google Gemini, Groq, OpenAI, etc.).</small>
    </div>
  </div>` : '';

  const selProv = STATE.selectedModelProvider || 'all';
  const providers = [
    { id: 'all', label: 'Todos los Proveedores' },
    { id: 'google', label: 'Google Gemini' },
    { id: 'groq', label: 'Groq' },
    { id: 'openai', label: 'OpenAI' },
    { id: 'deepseek', label: 'DeepSeek' },
    { id: 'anthropic', label: 'Anthropic' },
    { id: 'ollama', label: 'Ollama / Local' }
  ];

  return `
  ${warnBanner}
  <section>
    <h2>Filtrar por Proveedor de API</h2>
    ${note('Toca un proveedor para desplegar únicamente sus modelos disponibles según tu plan:')}
    <div style="display:flex;gap:8px;flex-wrap:wrap;margin:10px 0 14px">
      ${providers.map(p => `
        <button type="button" class="btn sm ${selProv === p.id ? 'p' : ''}" data-model-prov="${p.id}">
          ${p.label}
        </button>
      `).join('')}
    </div>
  </section>

  <section>
    <h2>Modelos de Inteligencia Artificial</h2>
    ${note('Configuración en vivo de los cerebros de Miku según su especialidad:')}
    ${row('Cerebro Principal (Chat & Conversación)', 'Modelo general para respuestas rápidas y conversación diaria.', `<span id="gs-chat"></span>`)}
    ${row('Cerebro Pro / Código (Programación & Lógica)', 'Modelo especializado para código, refactorización y tareas avanzadas.', `<span id="gs-pro"></span>`)}
    ${row('Control de PC (Computer Use & Pantalla)', 'Modelo especializado en visión multimodal e interacción con ventanas.', `<span id="gs-comp"></span>`)}
    ${row('Transcripción de Voz (STT)', 'Modelo para transcripción de audio del micrófono a texto.', `<span id="gs-stt"></span>`)}
  </section>
  <section>
    <h2>Aplicar cambios</h2>
    ${row('Guardar configuración', 'Aplica inmediatamente los modelos al gateway sin necesidad de reiniciar.', `<span id="hb-models"></span>`)}
  </section>
  `;
};

// 5. CLAVES DE API (.env)
V.keys = () => {
  const K = STATE.keys || {};
  const kRow = (id, label, desc, isPassword = true) => {
    const raw = K[id];
    const item = typeof raw === 'string'
      ? { is_set: !!raw, value_masked: raw }
      : (raw || { is_set: false, value_masked: '' });
    const shortMask = item.is_set && item.value_masked
      ? `••••${String(item.value_masked).replace(/^\*+/, '').slice(-4)}`
      : '';
    return `
    <div class="row" style="display:flex;align-items:center;justify-content:space-between;gap:16px;padding:12px 0">
      <div style="flex:1;min-width:0">
        <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">
          <b style="font-size:13px;color:var(--tx)">${label}</b>
          ${stat('st-' + id, item.is_set, item.is_set ? 'Configurada' : 'Sin clave')}
          ${shortMask ? `<code style="font-size:11px;color:var(--mu);background:rgba(255,255,255,0.06);padding:1px 6px;border-radius:6px">${esc(shortMask)}</code>` : ''}
        </div>
        <small style="margin-top:3px;display:block;color:var(--mu);font-size:11.5px">${desc}</small>
      </div>
      <div style="display:flex;align-items:center;gap:8px;flex:none">
        <input class="tx-in key-input-field" id="k-${id}" type="${isPassword ? 'password' : 'text'}" placeholder="${item.is_set ? '••••••••' : 'Introduce tu clave...'}" autocomplete="off" spellcheck="false" style="width:210px;height:36px;font-size:12.5px">
        <button type="button" class="btn sm p btn-save-key-icon" data-savekey="${id}" title="Guardar clave" style="width:36px;height:36px;padding:0;display:inline-flex;align-items:center;justify-content:center;border-radius:10px;flex:none;cursor:pointer">
          <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>
        </button>
        ${item.is_set ? `
        <button type="button" class="btn sm r btn-del-key-icon" data-delkey="${id}" title="Eliminar clave de .env" style="width:36px;height:36px;padding:0;display:inline-flex;align-items:center;justify-content:center;border-radius:10px;flex:none;cursor:pointer">
          <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
        </button>` : ''}
      </div>
    </div>`;
  };
  return `
  <section>
    <h2>${t('keys_title')}</h2>
    ${note(t('keys_note'))}
    ${kRow('GEMINI_API_KEY', 'Google Gemini API Key', 'Modelos Gemini Flash desde Google AI Studio (Recomendado).')}
    ${kRow('GROQ_API_KEY', 'Groq API Key', 'Inferencia ultra rápida para Llama 3.3 70B y transcripción Whisper.')}
    ${kRow('DEEPSEEK_API_KEY', 'DeepSeek API Key', 'Modelos oficiales DeepSeek-V3 y DeepSeek-R1.')}
    ${kRow('OPENAI_API_KEY', 'OpenAI API Key', 'Modelos GPT-4o y Whisper de OpenAI.')}
    ${kRow('ANTHROPIC_API_KEY', 'Anthropic API Key', 'Modelos Claude 3.5 Sonnet de Anthropic.')}
    ${kRow('OPENROUTER_API_KEY', 'OpenRouter API Key', 'Catálogo unificado de modelos en la nube.')}
    ${kRow('GOOGLE_CLOUD_PROJECT', 'Vertex AI - Project ID', 'ID del proyecto en Google Cloud para Vertex AI.', false)}
    ${kRow('NVIDIA_API_KEY', 'NVIDIA NIM API Key', 'Inferencia de modelos en la nube de NVIDIA.')}
    ${kRow('GITHUB_TOKEN', 'GitHub Token', 'Acceso a repositorios y GitHub Copilot.', true)}
  </section>
  <section>
    <h2>Multimedia y Servicios</h2>
    ${kRow('SPOTIFY_CLIENT_ID', 'Spotify Client ID', 'ID de cliente de Spotify para detección y reproducción.', false)}
    ${kRow('SPOTIFY_CLIENT_SECRET', 'Spotify Client Secret', 'Clave secreta de la aplicación de Spotify.')}
    ${kRow('ELEVENLABS_API_KEY', 'ElevenLabs API Key', 'Síntesis de voz realista opcional.')}
  </section>
  `;
};

// 6. SERVIDORES MCP (mcp_config.json)
const RECOMMENDED_MCPS = [
  {
    id: 'file_system',
    name: 'Archivos de la PC (Filesystem)',
    desc: 'Permite a Miku explorar carpetas, buscar documentos, leer código y gestionar archivos de tu equipo.',
    cmd: 'npx',
    args: ['-y', '@modelcontextprotocol/server-filesystem', 'C:\\Users\\cxmluwu\\Desktop', 'C:\\Users\\cxmluwu\\Downloads'],
    icon: '<svg viewBox="0 0 24 24" fill="var(--ac)" width="22" height="22"><path d="M10 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z"/></svg>'
  },
  {
    id: 'memory',
    name: 'Memoria y Contexto (Knowledge Graph)',
    desc: 'Grafo de conocimiento persistente para que Miku recuerde proyectos, preferencias y decisiones pasadas.',
    cmd: 'npx',
    args: ['-y', '@modelcontextprotocol/server-memory'],
    icon: '<svg viewBox="0 0 24 24" fill="var(--tx)" width="22" height="22"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/></svg>'
  },
  {
    id: 'sqlite',
    name: 'Base de Datos SQLite',
    desc: 'Conexión a bases de datos SQLite locales para análisis de datos, consultas SQL e informes.',
    cmd: 'npx',
    args: ['-y', '@modelcontextprotocol/server-sqlite'],
    icon: '<svg viewBox="0 0 24 24" fill="var(--tx)" width="22" height="22"><path d="M12 2C6.48 2 2 4.02 2 6.5v11C2 19.98 6.48 22 12 22s10-2.02 10-4.5v-11C22 4.02 17.52 2 12 2zm0 3c3.86 0 7 1.12 7 2.5S15.86 10 12 10s-7-1.12-7-2.5S8.14 5 12 5zm0 14c-3.86 0-7-1.12-7-2.5V14.7c1.86 1.14 4.31 1.8 7 1.8s5.14-.66 7-1.8v1.8c0 1.38-3.14 2.5-7 2.5zm0-4.5c-3.86 0-7-1.12-7-2.5V10.2c1.86 1.14 4.31 1.8 7 1.8s5.14-.66 7-1.8v1.8c0 1.38-3.14 2.5-7 2.5z"/></svg>'
  },
  {
    id: 'github',
    name: 'GitHub Repositorios y Código',
    desc: 'Exploración de repositorios de código, commits, ramas, pull requests y issues de GitHub.',
    cmd: 'npx',
    args: ['-y', '@modelcontextprotocol/server-github'],
    icon: '<svg viewBox="0 0 24 24" fill="var(--tx)" width="22" height="22"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0 0 24 12c0-6.63-5.37-12-12-12z"/></svg>'
  },
  {
    id: 'google-drive',
    name: 'Google Drive en la Nube',
    desc: 'Búsqueda y consulta de documentos, hojas de cálculo y archivos de tu cuenta de Google Drive.',
    cmd: 'npx',
    args: ['-y', '@piotr-agier/google-drive-mcp'],
    icon: '<svg viewBox="0 0 24 24" width="22" height="22" fill="var(--tx)"><path d="M7.71 3.5L1.15 15l3.43 6 6.55-11.5L7.71 3.5zm3.43 6l4.29 7.5H23l-4.29-7.5H11.14zm5.15-6L12 10.5h6.86L23 3.5h-6.71z"/></svg>'
  }
];

V.mcp = () => {
  const list = STATE.mcp || [];
  const installedNames = new Set(list.map(s => (s.name || '').toLowerCase()));

  return `
  <section>
    <h2>Servidores MCP Recomendados (1 Clic)</h2>
    <div class="mcp-grid-compact">
      ${RECOMMENDED_MCPS.map(r => {
        const isInst = installedNames.has(r.id.toLowerCase());
        return `
        <div class="mcp-card rec">
          <div style="display:flex;align-items:center;gap:9px;min-width:0;flex:1">
            <span class="app-badge-icon" style="width:20px;height:20px">${r.icon}</span>
            <div style="min-width:0;flex:1">
              <b style="font-size:12.5px;color:var(--tx);display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${esc(r.name)}</b>
              <small style="font-size:11px;color:var(--mu);display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis" title="${esc(r.desc)}">${esc(r.desc)}</small>
            </div>
          </div>
          <div style="flex:none">
            ${isInst 
              ? `<span class="pill on" style="font-size:10.5px;padding:2px 8px">Instalado</span>` 
              : `<span class="hb-mcp-inst" data-mcpid="${esc(r.id)}"></span>`
            }
          </div>
        </div>
        `;
      }).join('')}
    </div>
  </section>

  <section>
    <h2>${t('mcp_title')} (${list.length})</h2>
    <div id="mcp-list" style="margin-top:6px;">
      ${list.length ? list.map(s => {
        const isEnabled = s.enabled !== false;
        return `
        <div class="mcp-card ${isEnabled ? 'active' : 'paused'}">
          <div class="mcp-info" style="flex:1;min-width:0;">
            <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap">
              <b style="font-size:12.5px"><i class="sd ${s.connected && isEnabled ? 'on' : ''}"></i>${esc(s.name)}</b>
              <span class="mcp-token-badge ${isEnabled ? 'active' : 'paused'}">
                ${isEnabled ? (s.tools_count ? `${s.tools_count} tools` : 'Activo') : 'Pausado'}
              </span>
              <code style="font-size:10.5px;color:var(--mut);background:rgba(255,255,255,0.05);padding:1px 6px;border-radius:5px;max-width:260px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${esc(s.command)} ${(s.args || []).join(' ')}</code>
            </div>
          </div>
          <div style="display:flex;align-items:center;gap:10px;flex:none;">
            <label class="sq" title="${isEnabled ? 'Desactivar para ahorrar tokens' : 'Activar servidor MCP'}">
              <input type="checkbox" class="mcp-toggle-sw" data-mcp="${esc(s.name)}" ${isEnabled ? 'checked' : ''}>
              <i></i>
            </label>
            <span class="hb-del-mcp" data-delmcp="${esc(s.name)}"></span>
          </div>
        </div>
        `;
      }).join('') : '<p class="nt" style="padding:4px 0">No hay servidores MCP configurados.</p>'}
    </div>
  </section>

  <section>
    <h2>${t('mcp_add')} (Personalizado)</h2>
    <div style="display:flex;flex-direction:column;gap:12px;margin-top:6px">
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
        <div>
          <label style="font-size:11px;font-weight:700;color:var(--mu);display:block;margin-bottom:4px">Nombre del servidor</label>
          <input class="tx-in" id="mcp-name" type="text" placeholder="ej. memory" style="width:100%;height:38px">
        </div>
        <div>
          <label style="font-size:11px;font-weight:700;color:var(--mu);display:block;margin-bottom:4px">Comando ejecutable</label>
          <input class="tx-in" id="mcp-cmd" type="text" placeholder="ej. npx, uvx, node" style="width:100%;height:38px">
        </div>
      </div>
      <div>
        <label style="font-size:11px;font-weight:700;color:var(--mu);display:block;margin-bottom:4px">Argumentos del servidor</label>
        <div style="display:flex;gap:10px;align-items:center">
          <input class="tx-in" id="mcp-args" type="text" placeholder="ej. -y @modelcontextprotocol/server-memory" style="flex:1;height:38px">
          <span id="hb-add-mcp" style="flex:none"></span>
        </div>
      </div>
    </div>
  </section>
  `;
};

// 7. ALERTAS PROACTIVAS Y NOTIFICACIONES DE JUEGOS
V.alertas = () => {
  const A = STATE.alerts || {};
  const alertKeys = Object.keys(A);
  const selApp = STATE.selectedActiveApp;

  return `
  <section>
    <h2>Registrar Actividad de Juegos y Aplicaciones</h2>
    ${row('Juego o aplicación activa en tu PC', 'Selecciona una aplicación o juego activo para monitorear su tiempo de uso', `
      <div style="display:flex;gap:10px;align-items:center;flex-wrap:nowrap;justify-content:flex-end;width:100%;max-width:440px">
        <div id="gs-app-select" style="flex:1 1 0;min-width:0;width:100%"></div>
        <button type="button" class="btn p" id="btn-add-discord-app" style="height:36px;padding:0 14px;border-radius:10px;white-space:nowrap;flex:none;display:inline-flex;align-items:center;gap:6px">
          <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 5v14M5 12h14"/></svg>
          <span>Añadir app</span>
        </button>
      </div>
    `, 1)}
    <div id="discord-custom-wrap" class="row fx" style="display:${selApp?.id === 'custom' ? 'flex' : 'none'}">
      <div>
        <b>Ruta del ejecutable (.exe)</b>
        <small>Selecciona o escribe la ruta del proceso que deseas monitorear</small>
      </div>
      <div class="ctl" style="display:flex;gap:8px;align-items:center;flex:1;max-width:380px">
        <input class="tx-in" id="custom-app-path" type="text" placeholder="Ej: C:\\Juegos\\Juego.exe..." style="flex:1">
        <button type="button" class="btn" id="btn-browse-app" style="white-space:nowrap">Examinar...</button>
      </div>
    </div>
  </section>

  <section>
    <h2>Juegos y Aplicaciones Registradas</h2>
    <div id="active-alerts-list" style="margin-top:4px;display:flex;flex-direction:column;gap:8px">
      ${alertKeys.length ? alertKeys.map(k => {
        const item = A[k] || { enabled: true, threshold: 120, label: k };
        const iconHtml = (item.icon && item.icon.startsWith('data:image')) 
          ? `<img src="${item.icon}" width="26" height="26" style="border-radius:6px;object-fit:contain">`
          : ((item.icon && item.icon.includes('<svg') && !item.icon.includes('<rect width="18"'))
              ? item.icon
              : getKnownAppIcon(k, item.label));
        return `
        <div class="row" style="padding:10px 0">
          <div style="display:flex;align-items:center;gap:12px;min-width:0;flex:1">
            <span style="flex:none;display:grid;place-items:center;width:32px;height:32px;background:rgba(255,255,255,0.04);border:1px solid var(--ln);border-radius:9px">${iconHtml}</span>
            <div style="min-width:0;flex:1">
              <span class="marquee-wrap" style="color:var(--tx);font-size:13.5px;font-weight:700;display:block">
                <span class="marquee-text">${esc(item.label || k)}</span>
              </span>
              <small style="color:var(--mut);font-size:11.5px;display:block">Alerta tras ${item.threshold || 120} minutos</small>
            </div>
          </div>
          <div class="ctl" style="display:flex;align-items:center;gap:12px;flex:none">
            <div style="display:flex;align-items:center;gap:6px">
              <span style="font-size:11.5px;color:var(--mut)">Tiempo:</span>
              <div id="gs-alert-${esc(k)}" style="min-width:115px"></div>
            </div>
            <label class="sq" title="Activar/Desactivar"><input type="checkbox" data-alert-en="${esc(k)}" ${item.enabled ? 'checked' : ''}><i></i></label>
            <button type="button" class="btn-del-alert" data-del-alert="${esc(k)}" title="Eliminar registro"><svg class="ic" width="14" height="14"><use href="#ic-trash"/></svg></button>
          </div>
        </div>`;
      }).join('') : '<p class="nt" style="padding:8px 0">No tienes juegos o aplicaciones registradas. Selecciona una arriba para empezar.</p>'}
    </div>
    ${row('Probar Sistema de Alertas', 'Emite una notificación de prueba con el icono de Miku en la Isla Dinámica y Windows.', `<button type="button" class="btn p" id="btn-test-alert" style="white-space:nowrap">Probar Alerta en Vivo</button>`)}
  </section>
  `;
};

// 9. ZONA DE PELIGRO
V.peligro = () => `
  <div class="al er" role="alert" style="margin-bottom:14px">
    <svg class="ic" width="16" height="16"><use href="#ic-danger"/></svg>
    <div style="flex:1"><b>Acciones irreversibles.</b> Requieren mantener presionado el botón de confirmación para evitar clics accidentales.</div>
  </div>
  <section style="border-color:rgba(255,69,58,.28)">
    <h2 style="color:var(--er)">Zona de peligro</h2>
    ${row('Restablecer ajustes de interfaz', 'Devuelve todos los ajustes visuales, idioma y volumen a sus valores predeterminados.', `<span id="hb-danger-reset-cfg"></span>`, 1)}
    ${row('Restablecer lista de agentes', 'Elimina los agentes personalizados creados y restaura los agentes predeterminados.', `<span id="hb-danger-reset-agents"></span>`, 1)}
    ${row('Desvincular todos los dispositivos móviles', 'Revoca los tokens de emparejamiento de Miku-Link y cierra conexiones activas.', `<span id="hb-danger-unpair-all"></span>`)}
  </section>
`;

// 8. MIKU-LINK (Móvil — como Phone Link dentro de Configuración, Fase 5)
V.link = () => {
  if (window.MikuLinkSection?.renderMikuLinkSectionHtml) {
    return window.MikuLinkSection.renderMikuLinkSectionHtml();
  }
  return `<section class="card" style="padding:20px"><div id="ml"></div></section>`;
};

const renderRail = () => {
  const r = $('#rail');
  if (!r) return;
  const html = railHtml();
  if (r.dataset.rendered !== html) {
    r.innerHTML = html;
    r.dataset.rendered = html;
    if (window.MikuUI?.gel) {
      r.dataset.axis = 'y';
      window.MikuUI.gel(r, '.cat');
    }
  }
  $$('.cat', r).forEach(b => b.classList.toggle('on', b.dataset.cat == CAT));
  if (r._gel) r._gel(true);
};

// SECTION_THEMES eliminado: sistema monocromático v2 (§21)

function getSectionHeroMeta(catId) {
  const titles = {
    general: 'Preferencias del sistema',
    island: 'Isla Dinámica',
    permisos: 'Nivel de Permisos',
    agentes: 'Especialistas activos',
    modelos: 'Enrutamiento de modelos',
    keys: 'Credenciales de proveedores',
    mcp: 'Servidores MCP conectados',
    alertas: 'Avisos y recordatorios',
    voz: 'Síntesis y micrófono',
    link: 'Teléfono vinculado',
    peligro: 'Restablecer y borrar datos'
  };
  const subs = {
    general: 'Idioma, arranque automático, comportamiento de la isla y atajos globales.',
    island: 'Comportamiento del widget flotante de Windows, expansión y autocierre.',
    permisos: 'Límites de acceso al sistema operativo, archivos y consola.',
    agentes: 'Asigna roles, herramientas y prioridades de ejecución a cada agente.',
    modelos: 'Elige qué proveedor responde en conversación, código, visión y voz.',
    keys: 'Almacenadas localmente en tu llavero del sistema; nunca salen de tu equipo.',
    mcp: 'Conecta herramientas externas: archivos, navegador, terminal y calendario.',
    alertas: 'Controla qué eventos pueden interrumpirte y con qué prioridad.',
    voz: 'Timbre de voz, velocidad de lectura, detección de activación y dispositivo de entrada.',
    link: 'Notificaciones, mensajes, llamadas, fotos y archivos entre tu móvil y el escritorio.',
    peligro: 'Acciones irreversibles: requieren mantener pulsado para confirmar.'
  };
  const i18nFn = window.MikuI18n?.t;
  const tag = i18nFn ? i18nFn(`sections.${catId}.tag`, t(`cat_${catId}`) || 'MIKU DESKTOP') : (t(`cat_${catId}`) || 'MIKU DESKTOP');
  const title = i18nFn ? i18nFn(`sections.${catId}.title`, titles[catId] || 'Preferencias del sistema') : (titles[catId] || 'Preferencias del sistema');
  const desc = i18nFn ? i18nFn(`sections.${catId}.desc`, subs[catId] || '') : (subs[catId] || '');
  return { tag, title, desc };
}

function heroHtml() {
  const meta = getSectionHeroMeta(CAT);
  const hueFn = window.MikuTokens?.getSectionHue || (() => ({ h: 215, s: 75, l: 72 }));
  const targetHue = hueFn(CAT);
  return `
  <div class="miku-hero-wrap">
    <div class="hero miku-hero" style="margin:0;--h:${targetHue.h}">
      <canvas class="hero-galaxy-cv" id="heroGalaxyCv"></canvas>
      <div class="au"><i></i><i></i><i></i></div>
      <svg class="orb" viewBox="0 0 200 200" aria-hidden="true">
        <circle class="a" cx="100" cy="100" r="92"/>
        <circle class="b" cx="100" cy="100" r="70"/>
        <circle class="c" cx="100" cy="100" r="50"/>
        <circle class="k" cx="100" cy="100" r="9"/>
      </svg>
      <div class="miku-hero-body" id="ht">
        <small class="miku-hero-tag" id="hg">${esc(meta.tag)}</small>
        <h3 class="miku-hero-title" id="hh">${esc(meta.title)}</h3>
        <p class="miku-hero-desc" id="hp">${esc(meta.desc)}</p>
      </div>
    </div>
  </div>
  `;
}

let HERO_PARTICLES_STATE = null;

function initHeroGalaxy() {
  const cv = document.getElementById('heroGalaxyCv');
  if (!cv) return;
  const hueFn = window.MikuTokens?.getSectionHue || (() => ({ h: 215, s: 75, l: 72 }));
  const targetHue = hueFn(CAT);
  const heroEl = cv.closest('.hero');
  if (heroEl) heroEl.style.setProperty('--h', String(targetHue.h));
  if (!HERO_PARTICLES_STATE) {
    HERO_PARTICLES_STATE = { c: { ...targetHue }, t: { ...targetHue } };
  } else {
    HERO_PARTICLES_STATE.t = { ...targetHue };
  }
  if (window.MikuComponents?.createParticlesEngine) {
    window.MikuComponents.createParticlesEngine(cv, HERO_PARTICLES_STATE);
  }
}

let _lastRenderedCat = null;

function updateHeroText(animate = false) {
  const meta = getSectionHeroMeta(CAT);
  const hg = document.getElementById('hg');
  const hh = document.getElementById('hh');
  const hp = document.getElementById('hp');
  const ht = document.getElementById('ht');
  if (hg) hg.textContent = meta.tag;
  if (hh) hh.textContent = meta.title;
  if (hp) hp.textContent = meta.desc;
  if (animate && ht && window.MikuMotion?.enter) {
    window.MikuMotion.enter(ht);
  }
}

function render() {
  theme();
  renderRail();
  $$('.cat').forEach(b => b.classList.toggle('on', b.dataset.cat == CAT));
  window.MikuUI?.refresh?.();
  const pane = $('#pane');
  if (!pane) return;

  const catChanged = _lastRenderedCat !== null && _lastRenderedCat !== CAT;
  _lastRenderedCat = CAT;

  let heroWrap = pane.querySelector('.miku-hero-wrap');
  let cbody = document.getElementById('cbody');

  if (!heroWrap || !cbody) {
    pane.innerHTML = heroHtml() + `<div id="cbody" class="cbody bi">${(V[CAT] || V.general)()}</div>`;
    pane.scrollTop = 0;
    mount();
    initHeroGalaxy();
    return;
  }

  updateHeroText(catChanged);
  initHeroGalaxy();

  if (catChanged && !window.matchMedia?.('(prefers-reduced-motion: reduce)').matches) {
    cbody.classList.remove('bi');
    cbody.classList.add('bo');
    const targetCat = CAT;
    setTimeout(() => {
      if (CAT !== targetCat) return;
      cbody.innerHTML = (V[CAT] || V.general)();
      pane.scrollTop = 0;
      cbody.classList.remove('bo');
      void cbody.offsetWidth;
      cbody.classList.add('bi');
      mount();
    }, 150);
  } else {
    const prevScroll = pane.scrollTop;
    cbody.classList.remove('bi', 'bo');
    cbody.innerHTML = (V[CAT] || V.general)();
    if (catChanged) pane.scrollTop = 0;
    else pane.scrollTop = prevScroll;
    mount();
  }
}

const holdReset = () => { Object.assign(CFG, DEF); saveCfg(); setTimeout(render, 700); };
function miniLive() { STOP2?.(); STOP2 = null; const cv = document.querySelector('canvas.hm'); if (!cv) return; const id = cv.dataset.who; STOP2 = MK.live(cv, () => { const g = AG.find(x => x.id == id) || { id: 'miku', c: '#fff', outfit: PROUT }; return { color: bodyOf(g), outfit: outOf(g) }; }); }
function holdify() { $$('[data-key],[data-act="relay"],[data-conn],[data-act="keyreset"],#ag-add').forEach(b => { if (b.dataset.hold) return; b.dataset.hold = 1; const h = document.createElement('span'); h.className = 'hbh'; b.after(h); b.style.display = 'none'; HoldButton(h, { label: b.textContent.trim(), doneLabel: 'Hecho', hold: b.matches('[data-key],[data-conn]') ? 700 : b.matches('#ag-add') ? 900 : 1200, small: 1, onHold: () => b.click() }); }); }
let STOP_SIDEBAR = null;
function sidebarLive() {
  if (STOP_SIDEBAR) return;
  const cv = document.getElementById('sidebar-hl');
  if (!cv) return;
  STOP_SIDEBAR = MK.live(cv, () => ({ color: '#fff', outfit: PROUT }), { subtle: true });
}
function heroLive() {
  STOP?.(); STOP = null;
  const cv = document.querySelector('#pane canvas.hl');
  if (!cv) return;
  const id = cv.dataset.who;
  STOP = MK.live(cv, () => {
    const g = AG.find(x => x.id == id) || { id: 'custom', c: '#F2A765', outfit: 'none' };
    return { color: bodyOf(g), outfit: outOf(g) };
  });
}
const bodyOf = g => g.id == 'miku' ? '#fff' : g.c, outOf = g => g.id == 'miku' ? PROUT : (g.outfit || 'none');

let activeVoiceDial = null, activeSfxDial = null;

function mount() {
  sidebarLive();
  heroLive();
  miniLive();
  setTimeout(holdify, 0);

  const hbWinUpd = document.getElementById('hb-win-update');
  if (hbWinUpd && !hbWinUpd.dataset.mounted) {
    hbWinUpd.dataset.mounted = '1';
    hbWinUpd.style.display = 'none';
    HoldButton(hbWinUpd, {
      label: 'Reiniciar',
      doneLabel: 'Reiniciando...',
      hold: 900,
      small: 1,
      icon: '<svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2.5" style="margin-right:4px;vertical-align:middle"><path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/></svg>',
      onHold: async () => {
        showToast('Reiniciando Miku Desktop...');
        if (window.__TAURI__?.process?.relaunch) {
          try { await window.__TAURI__.process.relaunch(); } catch (_) { location.reload(); }
        } else {
          location.reload();
        }
      }
    });
    window.Bridge?.checkUpdate?.().then(res => {
      if (res?.available && hbWinUpd) {
        hbWinUpd.style.display = 'inline-block';
      }
    }).catch(() => {});
  }

  const G = (id, o) => { const h = $('#' + id); return h ? GlideSelect(h, o) : null; };

  if (CAT === 'general') {
    G('gs-ac', { options: [10, 15, 30, 60].map(n => ({ value: n, label: n + ' s' })), value: CFG.autoclose, label: t('autoclose_title'), onChange: v => { CFG.autoclose = +v; saveCfg(); } });
    G('gs-pers', { options: [{ value: 'calm', label: 'Calma' }, { value: 'casual', label: 'Casual' }, { value: 'code', label: 'Código' }], value: CFG.personality, label: t('pers_title'), onChange: v => { CFG.personality = v; saveCfg(); } });
    G('gs-lang', {
      options: [
        { value: 'es', label: 'Español' },
        { value: 'en', label: 'English' },
        { value: 'ko', label: '한국어 (Korean)' }
      ],
      value: CFG.lang || 'es',
      label: t('lang_title'),
      onChange: v => {
        CFG.lang = v;
        saveCfg();
        renderRail();
        render();
        emit({ k: 'lang', lang: v });
      }
    });
    HoldButton($('#hb-reset'), {
      label: t('reset_btn') || 'Restablecer',
      holdLabel: 'Mantén pulsado...',
      doneLabel: 'Restablecido',
      hold: 1400,
      small: 1,
      icon: '<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2.2" style="margin-right:4px"><path d="M21 12a9 9 0 1 1-3-6.7L21 8M21 3v5h-5"/></svg>',
      onHold: holdReset
    });

    $$('.mode-card').forEach(card => {
      card.onclick = async () => {
        const mode = card.dataset.setmode;
        if (!mode) return;
        const res = await window.Bridge?.setExecutionMode?.(mode);
        if (res && res.status === 'ok') {
          STATE.execMode = res.current_mode;
          showToast(`Modo cambiado: ${res.current_details?.name || mode}`);
          render();
        } else {
          showToast('Error al cambiar modo');
        }
      };
    });

    const btnUpdate = $('#btn-check-update');
    const stUpdate = $('#update-status');

    function formatChangelog(md) {
      if (!md) return '';
      const lines = md.split(/\r?\n/);
      const out = [];
      let inList = false;
      for (let rawLine of lines) {
        let line = rawLine.trim();
        if (!line) {
          if (inList) { out.push('</ul>'); inList = false; }
          continue;
        }
        if (line.startsWith('### ')) {
          if (inList) { out.push('</ul>'); inList = false; }
          out.push(`<div class="upd-subhead">${esc(line.substring(4))}</div>`);
        } else if (line.startsWith('## ')) {
          if (inList) { out.push('</ul>'); inList = false; }
          out.push(`<div class="upd-head">${esc(line.substring(3))}</div>`);
        } else if (line.startsWith('---')) {
          if (inList) { out.push('</ul>'); inList = false; }
          out.push('<hr class="upd-divider">');
        } else if (line.startsWith('- ') || line.startsWith('* ')) {
          if (!inList) { out.push('<ul class="upd-list">'); inList = true; }
          let c = esc(line.substring(2));
          c = c.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
          c = c.replace(/`([^`]+)`/g, '<code>$1</code>');
          out.push(`<li>${c}</li>`);
        } else {
          if (inList) { out.push('</ul>'); inList = false; }
          let c = esc(line);
          c = c.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
          c = c.replace(/`([^`]+)`/g, '<code>$1</code>');
          out.push(`<p class="upd-para">${c}</p>`);
        }
      }
      if (inList) out.push('</ul>');
      return out.join('');
    }

    function showUpdateAvailable(res) {
      if (!btnUpdate) return;
      btnUpdate.className = 'btn-upd-available';
      btnUpdate.textContent = `Instalar v${res.version}`;
      
      const formattedNotes = formatChangelog(res.body || '');
      if (stUpdate) {
        stUpdate.innerHTML = `
          <div class="update-box">
            <div class="update-box-head">
              <div class="update-badge">
                <span class="pulse-dot"></span>
                <span>¡Nueva versión disponible: v${esc(res.version)}!</span>
              </div>
              <span class="update-tag">Beta pública</span>
            </div>
            ${formattedNotes ? `
              <div class="update-notes-card">
                ${formattedNotes}
              </div>
            ` : ''}
            <div class="update-actions">
              <button class="btn-install-main" id="btn-install-inline">Descargar e Instalar v${esc(res.version)}</button>
              <a href="${esc(res.url || 'https://github.com/cxmlo/miku/releases/latest')}" target="_blank" class="btn-view-gh">
                <svg viewBox="0 0 24 24" width="13" height="13" fill="currentColor"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/></svg>
                Ver notas en GitHub
              </a>
            </div>
          </div>
        `;

        const doInstall = async () => {
          btnUpdate.disabled = true;
          btnUpdate.textContent = 'Instalando...';
          const btnInline = $('#btn-install-inline');
          if (btnInline) {
            btnInline.disabled = true;
            btnInline.textContent = 'Descargando e instalando...';
          }
          stUpdate.innerHTML = `
            <div class="update-installing">
              <span class="pulse-dot"></span>
              <span>Descargando e instalando actualización en segundo plano. Miku se reiniciará automáticamente al completar...</span>
            </div>
          `;
          await window.Bridge?.installUpdate?.();
        };

        btnUpdate.onclick = doInstall;
        const btnInline = $('#btn-install-inline');
        if (btnInline) btnInline.onclick = doInstall;
      }
    }

    if (btnUpdate) {
      window.Bridge?.checkUpdate?.().then(res => {
        if (res?.available) {
          showUpdateAvailable(res);
        }
      }).catch(() => {});

      btnUpdate.onclick = async () => {
        btnUpdate.disabled = true;
        btnUpdate.textContent = 'Buscando...';
        if (stUpdate) stUpdate.textContent = 'Consultando GitHub Releases...';
        try {
          const res = await window.Bridge?.checkUpdate?.();
          if (res?.available) {
            btnUpdate.disabled = false;
            showUpdateAvailable(res);
          } else if (res?.error) {
            btnUpdate.disabled = false;
            btnUpdate.textContent = 'Buscar actualización';
            if (stUpdate) stUpdate.textContent = res.error.includes('404') ? 'Tienes la versión más reciente instalada.' : `Info: ${res.error}`;
            showToast('Al día: no hay versiones pendientes');
          } else {
            btnUpdate.disabled = false;
            btnUpdate.textContent = 'Buscar actualización';
            if (stUpdate) stUpdate.textContent = 'Miku está en la versión más reciente (Beta v0.2.0).';
            showToast('Miku está al día');
          }
        } catch (e) {
          btnUpdate.disabled = false;
          btnUpdate.textContent = 'Buscar actualización';
          if (stUpdate) stUpdate.textContent = 'Error: ' + e.message;
        }
      };
    }
  }

  if (CAT === 'voz') {
    G('gs-mic', {
      options: window.__mics || [{ value: 'default', label: 'Predeterminado del sistema' }],
      value: CFG.mic || 'default',
      label: t('mic_title'),
      onChange: v => {
        CFG.mic = v;
        saveCfg();
        window.Bridge?.setAudioDevice?.(v);
      }
    });

    const vHost = $('#slider-voice');
    if (vHost) {
      SmoothSlider(vHost, {
        value: CFG.voice_volume || 80,
        unit: '%',
        onChange: val => {
          CFG.voice_volume = val;
          saveCfg();
          window.Bridge?.setVolume?.(val);
        }
      });
    }
    const sHost = $('#slider-sfx');
    if (sHost) {
      SmoothSlider(sHost, {
        value: CFG.sfx_volume || 60,
        unit: '%',
        onChange: val => {
          CFG.sfx_volume = val;
          saveCfg();
        }
      });
    }
  }

  if (CAT === 'agentes') {
    let tool = 'copilot';
    G('gs-tool', {
      options: TOOLS.map(t => ({ value: t[0], label: t[1] })),
      value: tool,
      label: 'Rol',
      onChange: v => {
        tool = v;
        const nInp = $('#ag-name');
        if (nInp) nInp.placeholder = (TOOLS.find(t => t[0] == v) || [])[1] || 'Mi agente';
      }
    });

    const reorderEl = document.getElementById('ag-reorder-list');
    if (reorderEl && window.MikuComponents?.mountReorderList) {
      window.MikuComponents.mountReorderList(reorderEl, AG, {
        maxActive: 3,
        onSelect: (id) => {
          selAgent(id);
          render();
        },
        onReorder: (orderIds) => {
          if (!Array.isArray(orderIds) || !orderIds.length) return;
          const map = new Map(AG.map(a => [String(a.id), a]));
          const nextAg = [];
          orderIds.forEach(id => {
            if (map.has(String(id))) {
              nextAg.push(map.get(String(id)));
              map.delete(String(id));
            }
          });
          map.forEach(a => nextAg.push(a));
          nextAg.forEach((a, idx) => {
            a.isl = idx < 3 ? 1 : 0;
          });
          AG = nextAg;
          saveAgents();
        }
      });
    }

    let newAgModel = '';
    const buildAgentModelOptions = () => {
      const availChat = STATE.models?.available?.chat || [];
      const availPro = STATE.models?.available?.pro || [];
      const seen = new Set();
      const opts = [{ value: '', label: 'Automático (Usar Cerebro Principal)' }];
      const addOpt = (val, lbl) => {
        if (!val || seen.has(val)) return;
        seen.add(val);
        opts.push({ value: val, label: lbl });
      };
      [...availChat, ...availPro].forEach(m => {
        if (typeof m === 'string') addOpt(m, m);
        else if (m && m.id) addOpt(m.id, (m.name || m.id) + (m.has_key === false ? ' [Sin clave]' : ''));
      });
      if (opts.length === 1) {
        addOpt('gemini-2.5-flash', 'Google · Gemini 2.5 Flash');
        addOpt('gemini-2.5-pro', 'Google · Gemini 2.5 Pro');
        addOpt('llama-3.3-70b-versatile', 'Groq · Llama 3.3 70B');
        addOpt('deepseek-chat', 'DeepSeek · DeepSeek V3');
        addOpt('deepseek-reasoner', 'DeepSeek · DeepSeek R1');
        addOpt('gpt-4o', 'OpenAI · GPT-4o');
        addOpt('claude-3-5-sonnet-20241022', 'Anthropic · Claude 3.5 Sonnet');
      }
      return opts;
    };
    const agModelOptions = buildAgentModelOptions();

    G('gs-new-ag-model', {
      options: agModelOptions,
      value: newAgModel,
      label: 'Modelo / API de IA',
      onChange: v => { newAgModel = v; }
    });

    const add = $('#hb-ag-add');
    if (add) {
      HoldButton(add, {
        label: 'Crear agente',
        doneLabel: 'Agente creado',
        hold: 850,
        variant: 'p',
        onHold: () => {
          if (AG.length >= 8) { showToast('Máximo 8 agentes'); return; }
          const t = TOOLS.find(x => x[0] == tool),
                name = ($('#ag-name')?.value.trim()) || (t && t[0] != 'custom' ? t[1] : 'Agente ' + (AG.length + 1));
          const used = new Set(AG.map(a => a.c.toLowerCase())),
                c = PRESET.find(h => !used.has(h.toLowerCase())) || PRESET[AG.length % PRESET.length];
          const na = {
            id: tool + '-' + Date.now().toString(36),
            name,
            c,
            outfit: 'none',
            tool,
            model: newAgModel || '',
            custom: 1,
            prompt: ($('#ag-prompt')?.value || '').trim()
          };
          AG.push(na);
          saveAgents();
          selAgent(na.id);
          render();
        }
      });
    }

    // Edición de agente seleccionado
    const editName = $('#ag-edit-name');
    if (editName) {
      editName.onchange = () => {
        const sel = AG.find(a => a.id == SELID);
        if (sel) {
          sel.name = editName.value.trim() || sel.name;
          saveAgents();
          render();
        }
      };
    }

    const editPrompt = $('#ag-edit-prompt');
    if (editPrompt) {
      editPrompt.onchange = () => {
        const sel = AG.find(a => a.id == SELID);
        if (sel) {
          sel.prompt = editPrompt.value.trim();
          saveAgents();
        }
      };
    }

    $$('[data-color]').forEach(btn => {
      btn.onclick = () => {
        const sel = AG.find(a => a.id == SELID);
        if (sel) {
          sel.c = btn.dataset.color;
          saveAgents();
          $$('[data-color]').forEach(b => b.classList.toggle('on', b === btn));
          const colIn = $('#ag-colin');
          if (colIn) colIn.value = sel.c.toLowerCase();
          heroLive();
          render();
        }
      };
    });

    const agColin = $('#ag-colin');
    if (agColin) {
      agColin.oninput = () => {
        const sel = AG.find(a => a.id == SELID);
        if (sel) {
          sel.c = agColin.value;
          saveAgents();
          heroLive();
        }
      };
      agColin.onchange = () => {
        render();
      };
    }

    const delHost = $('#hb-del-curr');
    if (delHost) {
      HoldButton(delHost, {
        label: t('ag_delete'),
        doneLabel: 'Eliminado',
        hold: 1400,
        small: 1,
        variant: 'r',
        onHold: () => {
          AG = AG.filter(a => a.id != SELID);
          selAgent('miku');
          saveAgents();
          showToast('Agente eliminado');
          setTimeout(render, 300);
        }
      });
    }

    // Configuración de Modelo IA y Servidor MCP exclusivo para el agente
    const selAg = AG.find(a => a.id == SELID);
    if (selAg) {
      G('gs-ag-model', {
        options: agModelOptions,
        value: selAg.model || '',
        label: 'Modelo / API de IA',
        onChange: v => {
          selAg.model = v || '';
          saveAgents();
          const chosen = agModelOptions.find(o => o.value === v);
          showToast(v ? `IA "${chosen?.label || v}" asignada a ${selAg.name}` : `${selAg.name} usará el Cerebro Principal`);
        }
      });

      const mcpServers = STATE.mcp || [];
      const mcpInUse = {};
      AG.forEach(a => {
        if (a.id !== selAg.id && a.mcp) {
          mcpInUse[a.mcp] = a.name;
        }
      });

      const mcpOptions = [
        { value: '', label: 'Ninguno (Sin herramientas MCP)' },
        ...mcpServers.map(s => {
          const inUseBy = mcpInUse[s.name];
          return {
            value: s.name,
            label: inUseBy ? `${s.name} [En uso por ${inUseBy}]` : `${s.name} (Disponible)`
          };
        })
      ];

      G('gs-ag-mcp', {
        options: mcpOptions,
        value: selAg.mcp || '',
        label: 'Servidor MCP',
        onChange: v => {
          if (v && mcpInUse[v]) {
            showToast(`El servidor MCP "${v}" ya está en uso por ${mcpInUse[v]}`);
            return;
          }
          selAg.mcp = v;
          saveAgents();
          showToast(v ? `MCP "${v}" asignado a ${selAg.name}` : `Sin MCP para ${selAg.name}`);
        }
      });
    }

    // Generador de Prompt con IA para el agente seleccionado
    const btnGen = $('#btn-gen-prompt');
    if (btnGen) {
      btnGen.onclick = async () => {
        const descInp = $('#ag-ai-desc');
        const desc = (descInp?.value || '').trim();
        if (!desc) {
          showToast('Describe brevemente la función del agente');
          descInp?.focus();
          return;
        }
        const selAg = AG.find(a => a.id == SELID);
        btnGen.disabled = true;
        btnGen.innerHTML = '<span>Generando...</span>';
        try {
          const res = await fetch('http://127.0.0.1:8000/api/agent/generate_prompt', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'x-api-key': 'miku_secure_key_2026' },
            body: JSON.stringify({
              name: selAg?.name || 'Agente',
              role: selAg?.role || '',
              description: desc
            })
          });
          if (res.ok) {
            const data = await res.json();
            const promptArea = $('#ag-edit-prompt');
            if (promptArea && data.prompt) {
              promptArea.value = data.prompt;
              if (selAg) {
                selAg.prompt = data.prompt;
                saveAgents();
              }
              showToast('Prompt generado con IA. Puedes revisarlo.');
            }
          } else {
            showToast('Error generando prompt');
          }
        } catch (_) {
          showToast('Error de conexión con el backend');
        } finally {
          btnGen.disabled = false;
          btnGen.innerHTML = '<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z"/></svg><span>Generar Prompt</span>';
        }
      };
    }

    // Generador de Prompt con IA para creación de nuevo agente
    const btnNewGen = $('#btn-new-gen-prompt');
    if (btnNewGen) {
      btnNewGen.onclick = async () => {
        const descInp = $('#ag-new-ai-desc');
        const desc = (descInp?.value || '').trim();
        const nameInp = $('#ag-name');
        const name = (nameInp?.value || '').trim() || 'Nuevo Agente';
        if (!desc) {
          showToast('Describe brevemente la función del nuevo agente');
          descInp?.focus();
          return;
        }
        btnNewGen.disabled = true;
        btnNewGen.innerHTML = '<span>Generando...</span>';
        try {
          const res = await fetch('http://127.0.0.1:8000/api/agent/generate_prompt', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'x-api-key': 'miku_secure_key_2026' },
            body: JSON.stringify({
              name: name,
              role: 'Sub-agente',
              description: desc
            })
          });
          if (res.ok) {
            const data = await res.json();
            const promptArea = $('#ag-prompt');
            if (promptArea && data.prompt) {
              promptArea.value = data.prompt;
              showToast('Instrucciones generadas con IA.');
            }
          }
        } catch (_) {
          showToast('Error de conexión con el backend');
        } finally {
          btnNewGen.disabled = false;
          btnNewGen.innerHTML = '<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z"/></svg><span>Generar con IA</span>';
        }
      };
    }
  }

  if (CAT === 'modelos') {
    // Filtrado por botones de proveedor
    $$('[data-model-prov]').forEach(btn => {
      btn.onclick = () => {
        STATE.selectedModelProvider = btn.dataset.modelProv;
        render();
      };
    });

    const M = STATE.models || {};
    const avail = M.available || {};
    const cur = M.current || {};
    const selProv = (STATE.selectedModelProvider || 'all').toLowerCase();

    const filterByProv = list => {
      if (!list || !list.length) return [];
      if (selProv === 'all') return list;
      return list.filter(m => {
        const p = (m.provider || '').toLowerCase();
        const id = (m.id || '').toLowerCase();
        if (selProv === 'google') return p === 'google' || id.startsWith('gemini');
        if (selProv === 'groq') return p === 'groq' || id.startsWith('llama') || id.startsWith('whisper') || id.startsWith('mixtral') || id.startsWith('deepseek-r1-distill');
        if (selProv === 'openai') return p === 'openai' || id.startsWith('gpt');
        if (selProv === 'deepseek') return p === 'deepseek' || id.startsWith('deepseek');
        if (selProv === 'anthropic') return p === 'anthropic' || id.startsWith('claude');
        if (selProv === 'ollama') return p === 'ollama';
        return p === selProv;
      });
    };

    const optLabel = m => (m.name || m.id) + (m.has_key ? '' : ' [Requiere Clave]');
    const chatOpts = filterByProv(avail.chat || []).map(m => ({ value: m.id, label: optLabel(m) }));
    const proOpts = filterByProv(avail.pro || []).map(m => ({ value: m.id, label: optLabel(m) }));
    const compOpts = filterByProv(avail.computer_use || []).map(m => ({ value: m.id, label: optLabel(m) }));
    const sttOpts = filterByProv(avail.stt || []).map(m => ({ value: m.id, label: optLabel(m) }));

    G('gs-chat', {
      options: chatOpts.length ? chatOpts : [{ value: '', label: 'Sin modelos disponibles para este filtro' }],
      value: cur.chat,
      label: 'Chat',
      onChange: v => { if (v) cur.chat = v; }
    });
    G('gs-pro', {
      options: proOpts.length ? proOpts : (chatOpts.length ? chatOpts : [{ value: '', label: 'Sin modelos pro disponibles' }]),
      value: cur.pro || cur.chat,
      label: 'Pro / Código',
      onChange: v => { if (v) cur.pro = v; }
    });
    G('gs-comp', {
      options: compOpts.length ? compOpts : [{ value: '', label: 'Sin proveedor de visión' }],
      value: cur.computer_use,
      label: 'Computer Use',
      onChange: v => { if (v) cur.computer_use = v; }
    });
    G('gs-stt', {
      options: sttOpts.length ? sttOpts : [{ value: '', label: 'Sin proveedor de voz' }],
      value: cur.stt,
      label: 'STT',
      onChange: v => { if (v) cur.stt = v; }
    });
    HoldButton($('#hb-models'), {
      label: 'Guardar modelos',
      doneLabel: 'Modelos guardados',
      hold: 1400,
      onHold: async () => {
        const ok = await window.Bridge?.saveModelsConfig?.(cur);
        showToast(ok ? 'Modelos de IA actualizados' : 'Error al guardar modelos');
        await loadBackendData();
      }
    });
  }

  if (CAT === 'keys') {
    $$('.btn-save-key-icon').forEach(btn => {
      const keyId = btn.dataset.savekey;
      btn.onclick = async () => {
        const input = document.getElementById('k-' + keyId);
        const val = input ? input.value.trim() : '';
        if (!val) { showToast('Introduce un valor para la clave'); input?.focus(); return; }
        btn.disabled = true;
        const ok = await window.Bridge?.saveConfigKeys?.({ [keyId]: val });
        btn.disabled = false;
        if (ok) {
          showToast(`Clave ${keyId} guardada correctamente`);
          if (input) input.value = '';
          const res = await window.Bridge?.getConfigKeys?.();
          STATE.keys = res?.keys || {};
          render();
        } else {
          showToast('Error al guardar clave');
        }
      };
    });

    $$('.btn-del-key-icon').forEach(btn => {
      const keyId = btn.dataset.delkey;
      btn.onclick = async () => {
        btn.disabled = true;
        const res = await window.Bridge?.deleteConfigKey?.(keyId);
        btn.disabled = false;
        if (!res?.error) {
          showToast(`Clave ${keyId} eliminada`);
          const keysRes = await window.Bridge?.getConfigKeys?.();
          STATE.keys = keysRes?.keys || {};
          render();
        } else {
          showToast('Error al eliminar clave: ' + (res?.error || ''));
        }
      };
    });
  }

  if (CAT === 'mcp') {
    $$('.hb-mcp-inst').forEach(host => {
      const id = host.dataset.mcpid;
      const r = RECOMMENDED_MCPS.find(x => x.id === id);
      if (!r) return;
      HoldButton(host, {
        label: 'Instalar', variant: 'p',
        doneLabel: 'Instalado',
        hold: 700,
        small: 1,
        onHold: async () => {
          showToast(`Instalando servidor MCP ${r.name}...`);
          const ok = await window.Bridge?.addMcpServer?.(r.id, r.cmd, r.args);
          if (ok) {
            showToast(`Servidor ${r.name} instalado`);
            const data = await window.Bridge?.getMcpServers?.();
            STATE.mcp = data.servers || [];
            render();
          } else {
            showToast(`Error al instalar ${r.name}`);
          }
        }
      });
    });

    const btnAdd = $('#hb-add-mcp');
    if (btnAdd) {
      HoldButton(btnAdd, {
        label: 'Añadir Servidor', variant: 'p',
        doneLabel: 'Añadido',
        hold: 800,
        onHold: async () => {
          const name = $('#mcp-name')?.value.trim();
          const cmd = $('#mcp-cmd')?.value.trim();
          const argsStr = $('#mcp-args')?.value.trim() || '';
          const args = argsStr ? argsStr.split(/\s+/) : [];
          if (!name || !cmd) { showToast('Introduce nombre y comando'); return; }
          const ok = await window.Bridge?.addMcpServer?.(name, cmd, args);
          if (ok) {
            showToast(`Servidor ${name} añadido`);
            const data = await window.Bridge?.getMcpServers?.();
            STATE.mcp = data.servers || [];
            render();
          } else {
            showToast('Error al añadir servidor MCP');
          }
        }
      });
    }

    $$('.hb-del-mcp').forEach(host => {
      const name = host.dataset.delmcp;
      HoldButton(host, {
        label: 'Eliminar',
        doneLabel: 'Eliminado',
        variant: 'd',
        hold: 1000,
        small: 1,
        onHold: async () => {
          const ok = await window.Bridge?.deleteMcpServer?.(name);
          if (ok) {
            showToast(`Servidor ${name} eliminado`);
            const data = await window.Bridge?.getMcpServers?.();
            STATE.mcp = data.servers || [];
            render();
          } else {
            showToast('Error al eliminar servidor MCP');
          }
        }
      });
    });

    $$('.mcp-toggle-sw').forEach(sw => {
      sw.onchange = async () => {
        const name = sw.dataset.mcp;
        const checked = sw.checked;
        showToast(checked ? `Activando servidor ${name}...` : `Pausando ${name} (ahorrando tokens)...`);
        const ok = await window.Bridge?.toggleMcpServer?.(name, checked);
        if (ok) {
          const data = await window.Bridge?.getMcpServers?.();
          STATE.mcp = data.servers || [];
          render();
        } else {
          sw.checked = !checked;
          showToast(`Error al alternar servidor ${name}`);
        }
      };
    });
  }

  if (CAT === 'alertas') {
    const alertTimeOpts = [
      { value: 15, label: '15 min' },
      { value: 30, label: '30 min' },
      { value: 45, label: '45 min' },
      { value: 60, label: '1 hora' },
      { value: 90, label: '1.5 h' },
      { value: 120, label: '2 horas' },
      { value: 180, label: '3 horas' },
      { value: 240, label: '4 horas' }
    ];

    Object.keys(STATE.alerts || {}).forEach(k => {
      const gHost = document.getElementById('gs-alert-' + k);
      if (gHost) {
        const curVal = STATE.alerts[k].threshold || 120;
        GlideSelect(gHost, {
          options: alertTimeOpts,
          value: curVal,
          label: 'Tiempo',
          onChange: val => {
            if (!STATE.alerts[k]) STATE.alerts[k] = { enabled: true, threshold: +val };
            STATE.alerts[k].threshold = +val;
            window.Bridge?.saveAlertsConfig?.(STATE.alerts);
          }
        });
      }
    });

    // Selector GlideSelect nativo para Apps y Juegos activos (diseño por defecto de la foto)
    const gAppHost = document.getElementById('gs-app-select');
    const customWrap = document.getElementById('discord-custom-wrap');
    if (gAppHost) {
      // Filtrar estrictamente solo apps activas y excluir las que ya tienen alerta registrada
      const available = (STATE.runningApps || []).filter(r => !STATE.alerts?.[r.id] && !STATE.alerts?.[r.process]);
      const appOpts = [];
      if (available.length > 0) {
        available.forEach(r => {
          appOpts.push({
            value: `${r.id}|${r.name}|${r.process || r.name}`,
            label: `${r.name} (${r.process || r.id})`
          });
        });
      } else {
        appOpts.push({
          value: 'none',
          label: 'No hay juegos activos detectados'
        });
      }
      appOpts.push({
        value: 'custom',
        label: 'Examinar otro ejecutable (.exe)...'
      });

      let initialVal = STATE.selectedActiveApp?.id === 'custom' 
        ? 'custom' 
        : (STATE.selectedActiveApp ? `${STATE.selectedActiveApp.id}|${STATE.selectedActiveApp.name}|${STATE.selectedActiveApp.process}` : (available.length > 0 ? appOpts[0].value : 'none'));

      if (available.length > 0 && (!STATE.selectedActiveApp || STATE.selectedActiveApp.id !== 'custom')) {
        const parts = appOpts[0].value.split('|');
        STATE.selectedActiveApp = { id: parts[0], name: parts[1], process: parts[2] || '' };
      }

      GlideSelect(gAppHost, {
        options: appOpts,
        value: initialVal,
        label: 'Juego o Aplicación',
        onChange: (val) => {
          if (val === 'custom') {
            STATE.selectedActiveApp = { id: 'custom', name: 'Otro ejecutable (.exe)', process: '' };
            if (customWrap) customWrap.style.display = 'block';
          } else if (val === 'none') {
            STATE.selectedActiveApp = null;
            if (customWrap) customWrap.style.display = 'none';
          } else {
            const parts = val.split('|');
            STATE.selectedActiveApp = { id: parts[0], name: parts[1], process: parts[2] || '' };
            if (customWrap) customWrap.style.display = 'none';
          }
        }
      });
    }

    // Botón para registrar juego o app activa
    const btnAddDiscord = $('#btn-add-discord-app');
    const pathInp = $('#custom-app-path');

    if (btnAddDiscord) {
      btnAddDiscord.onclick = async () => {
        const sel = STATE.selectedActiveApp;
        if (!sel || sel.id === 'none') {
          showToast('Elige una aplicación o juego activo de la lista');
          return;
        }

        let appKey = '', appLabel = '', appIcon = '';
        if (sel.id === 'custom') {
          const customVal = (pathInp?.value || '').trim();
          if (!customVal) {
            showToast('Escribe o examina la ruta del ejecutable');
            pathInp?.focus();
            return;
          }
          const fileName = customVal.split(/[/\\]/).pop() || customVal;
          appKey = fileName.toLowerCase().replace(/[^a-z0-9_.]/g, '_');
          appLabel = fileName;
          appIcon = getKnownAppIcon(appKey, appLabel);
        } else {
          appKey = sel.id;
          appLabel = sel.name || sel.id;
          const found = (STATE.runningApps || []).find(x => x.id === sel.id);
          appIcon = (found && found.icon && !found.icon.includes('<rect width="18"')) ? found.icon : getKnownAppIcon(sel.id, sel.name);
        }

        if (!STATE.alerts) STATE.alerts = {};
        STATE.alerts[appKey] = {
          enabled: true,
          threshold: 120,
          label: appLabel,
          icon: appIcon
        };
        await window.Bridge?.saveAlertsConfig?.(STATE.alerts);
        STATE.selectedActiveApp = null;
        render();
        showToast(`${appLabel} registrado correctamente.`);
      };
    }

    // Selector de tiempo/minutos por cada juego o aplicación registrada
    $$('select[data-alert-threshold]').forEach(sel => {
      sel.onchange = async () => {
        const key = sel.dataset.alertThreshold;
        if (!STATE.alerts[key]) STATE.alerts[key] = { enabled: true };
        STATE.alerts[key].threshold = +sel.value;
        await window.Bridge?.saveAlertsConfig?.(STATE.alerts);
        showToast(`Tiempo límite actualizado a ${sel.value} min`);
      };
    });

    // Switches ON/OFF
    $$('[data-alert-en]').forEach(inp => {
      inp.onchange = () => {
        const key = inp.dataset.alertEn;
        if (!STATE.alerts[key]) STATE.alerts[key] = { enabled: true, threshold: 120 };
        STATE.alerts[key].enabled = inp.checked;
        window.Bridge?.saveAlertsConfig?.(STATE.alerts);
      };
    });

    // Eliminar alerta
    $$('[data-del-alert]').forEach(btn => {
      btn.onclick = async (e) => {
        e.stopPropagation();
        const key = btn.dataset.delAlert;
        delete STATE.alerts[key];
        await window.Bridge?.saveAlertsConfig?.(STATE.alerts);
        render();
        showToast(`Registro eliminado`);
      };
    });

    // Examinar archivo ejecutable nativo
    const btnBrowse = $('#btn-browse-app');
    if (btnBrowse) {
      btnBrowse.onclick = async () => {
        btnBrowse.disabled = true;
        btnBrowse.textContent = 'Examinando...';
        try {
          const path = await window.Bridge?.browseExe?.();
          if (path && pathInp) pathInp.value = path;
        } catch (_) {}
        btnBrowse.disabled = false;
        btnBrowse.textContent = 'Examinar...';
      };
    }
    // Botón de prueba de alerta en vivo
    const btnTestAlert = $('#btn-test-alert');
    if (btnTestAlert) {
      btnTestAlert.onclick = async () => {
        showToast('Enviando alerta de prueba...');
        const ok = await window.Bridge?.testAlert?.();
        if (ok) showToast('Alerta de prueba emitida en la Isla y Windows');
        else showToast('Error al emitir alerta de prueba');
      };
    }
  }

  if (CAT === 'link') {
    window.MikuLinkSection?.mountMikuLinkSection?.();
  } else {
    window.MikuLinkSection?.stopMikuLinkTimers?.();
  }

  if (CAT === 'peligro') {
    const hbResetCfg = $('#hb-danger-reset-cfg');
    if (hbResetCfg) {
      HoldButton(hbResetCfg, {
        label: 'Mantén para restablecer',
        doneLabel: 'Restablecido',
        hold: 1600,
        variant: 'r',
        onHold: () => {
          holdReset();
          showToast('Ajustes restablecidos a valores de fábrica');
        }
      });
    }
    const hbResetAg = $('#hb-danger-reset-agents');
    if (hbResetAg) {
      HoldButton(hbResetAg, {
        label: 'Mantén para borrar agentes',
        doneLabel: 'Restaurados',
        hold: 1600,
        variant: 'r',
        onHold: () => {
          AG = structuredClone(DEFAULT_AGENTS);
          SELID = 'miku';
          saveAgents();
          showToast('Agentes restaurados a los predeterminados');
          setTimeout(render, 300);
        }
      });
    }
    const hbUnpairAll = $('#hb-danger-unpair-all');
    if (hbUnpairAll) {
      HoldButton(hbUnpairAll, {
        label: 'Mantén para desvincular',
        doneLabel: 'Desvinculados',
        hold: 1600,
        variant: 'r',
        onHold: async () => {
          try {
            await fetch('http://127.0.0.1:8000/api/link/unpair', { method: 'POST' });
            STATE.linkConnected = false;
            STATE.linkName = '';
            try { new BroadcastChannel('miku').postMessage({ k: 'unpair' }); } catch (_) {}
            showToast('Todos los dispositivos móviles fueron desvinculados');
          } catch (_) {
            showToast('Error al desvincular dispositivos');
          }
        }
      });
    }
  }
}

/* Deslizamiento automático en hover para cualquier texto que se desborde del botón o recuadro */
document.addEventListener('mouseover', e => {
  const el = e.target.closest('.marquee-wrap, .gs-t span.l, .cat span, .sec-btn');
  if (!el) return;
  const target = el.querySelector('.marquee-text') || el;
  const dist = target.scrollWidth - el.clientWidth;
  if (dist > 4) {
    el.style.textOverflow = 'clip';
    const dur = Math.max(1.6, Math.min(5.5, dist * 0.035));
    target.style.willChange = 'transform';
    target.style.transition = `transform ${dur}s cubic-bezier(0.2, 0.8, 0.4, 1) 0.15s`;
    target.style.transform = `translateX(-${dist + 6}px)`;
  }
});
document.addEventListener('mouseout', e => {
  const el = e.target.closest('.marquee-wrap, .gs-t span.l, .cat span, .sec-btn');
  if (!el) return;
  const target = el.querySelector('.marquee-text') || el;
  target.style.transition = 'transform 0.35s ease';
  target.style.transform = 'translateX(0)';
  setTimeout(() => {
    if (!el.matches(':hover')) el.style.textOverflow = 'ellipsis';
  }, 350);
});

/* Eventos globales */
document.addEventListener('click', e => {
  const b = e.target.closest('button');
  if (!b) return;

  if (b.dataset.cat) {
    CAT = b.dataset.cat;
    ls.set('miku_cat', CAT);
    render();
    const pane = $('#pane');
    if (pane) pane.scrollTop = 0;
    scrollTo({ top: 0 });
    b.scrollIntoView?.({ inline: 'center', block: 'nearest' });
  } else if (b.dataset.sel) {
    selAgent(b.dataset.sel);
    render();
  } else if (b.dataset.emo) {
    EMO = b.dataset.emo;
    STOP2?.emote?.(EMO, 2600);
    $$('[data-emo]').forEach(x => x.classList.toggle('on', x == b));
    emit({ k: 'emote', n: EMO });
  }
});

document.addEventListener('input', e => {
  const t = e.target, k = t.dataset.k;
  if (!k) return;
  CFG[k] = t.type == 'checkbox' ? (t.checked ? 1 : 0) : t.type == 'range' ? +t.value : t.value;
  saveCfg();
});

const typing = () => !!document.activeElement?.closest?.('.tx-in');

function onMsg(m) {
  if (!m) return;
  if (m.type === 'core_connected' || m.k === 'core_connected') {
    loadBackendData();
    return;
  }
  if (m.k == 'cfg' && m.cfg) {
    const prev = JSON.stringify(CFG);
    Object.assign(CFG, m.cfg);
    if (JSON.stringify(CFG) !== prev && !typing()) render();
  }
  else if (m.k == 'agents') {
    const sa = ls.get('miku_agents', null);
    if (Array.isArray(sa) && sa.length) {
      const prev = JSON.stringify(AG);
      AG = sa;
      if (CAT == 'agentes' && !typing() && JSON.stringify(AG) !== prev) render();
    }
  }
  else if (m.k == 'select') {
    const nextWho = m.who || 'miku';
    if (nextWho !== SELID) {
      selAgent(nextWho, 1);
      if (CAT == 'agentes' && !typing()) render();
    }
  }
  else if (m.k == 'go_cat' && m.cat) { window.__goCat?.(m.cat); }
  else if (m.k == 'pair') {
    STATE.pairUrl = m.url;
    if (CAT == 'link' && !window.MikuLinkSection) render();
  }
  else if (m.k == 'link') {
    STATE.linkConnected = !!m.ok;
    STATE.linkName = m.name || '';
    if (CAT == 'link' && !window.MikuLinkSection) render();
  }
  else if (m.k == 'outfit') {
    const nextOut = m.v || 'none';
    if (m.who == 'miku' || !m.who) {
      if (PROUT === nextOut) return;
      PROUT = nextOut;
      try { localStorage.setItem('miku_outfit', PROUT); } catch (_) {}
      sidebarLive();
      heroLive();
    } else {
      const ag = AG.find(x => x.id == m.who);
      if (ag && ag.outfit !== nextOut) {
        ag.outfit = nextOut;
        ls.set('miku_agents', AG);
        if (CAT == 'agentes' && !typing()) render();
      }
    }
  }
}

if (BC) BC.onmessage = e => onMsg(e.data);
try { window.__TAURI__?.event?.listen('miku', e => onMsg(e.payload)); } catch (_) {}

window.addEventListener('focus', () => {
  try {
    const cur = localStorage.getItem('miku_outfit') || 'none';
    if (cur !== PROUT) {
      PROUT = cur;
      sidebarLive();
      heroLive();
    }
  } catch (_) {}
});
window.addEventListener('storage', e => {
  if (e.key === 'miku_outfit' && e.newValue && e.newValue !== PROUT) {
    PROUT = e.newValue;
    sidebarLive();
    heroLive();
  }
});

let _backendPollTimer = null;
async function loadBackendData() {
  const isWebShowcase = !window.__TAURI__ && !window.pywebview && (
    !!window.IS_WEB_SHOWCASE ||
    (typeof window !== 'undefined' && (
      window.location.hostname.includes('github.io') ||
      (window.self !== window.top && (location.protocol === 'about:' || location.protocol === 'https:'))
    ))
  );

  if (isWebShowcase) {
    STATE.keys = {
      GEMINI_API_KEY: 'AIzaSy...DEMO_KEY',
      GROQ_API_KEY: 'gsk_...DEMO_KEY',
      OPENAI_API_KEY: 'sk-proj-...DEMO_KEY',
      ANTHROPIC_API_KEY: 'sk-ant-...DEMO_KEY'
    };
    STATE.models = {
      current: {
        chat: 'google/gemini-2.5-flash',
        computer_use: 'google/gemini-2.5-pro',
        stt: 'groq/whisper-large-v3'
      },
      available: {
        chat: [
          'google/gemini-2.5-flash',
          'google/gemini-2.5-pro',
          'groq/llama-3.3-70b-versatile',
          'openai/gpt-4o',
          'anthropic/claude-3-7-sonnet'
        ],
        computer_use: [
          'google/gemini-2.5-pro',
          'anthropic/claude-3-7-sonnet'
        ],
        stt: [
          'groq/whisper-large-v3',
          'openai/whisper-1'
        ]
      }
    };
    STATE.execMode = 'full';
    STATE.execDetails = { name: 'Modo Completo (PC + Nube)', desc: 'Agentes autónomos, visión de pantalla y sincronización móvil activa.' };
    STATE.mcp = [
      { name: 'sqlite-explorer', command: 'uvx mcp-server-sqlite --db data.db', enabled: true },
      { name: 'filesystem-agent', command: 'npx -y @modelcontextprotocol/server-filesystem C:\\Users\\Desktop', enabled: true },
      { name: 'brave-search', command: 'npx -y @modelcontextprotocol/server-brave-search', enabled: false }
    ];
    STATE.alerts = {
      'Visual Studio Code': { limit_minutes: 120, enabled: true },
      'League of Legends': { limit_minutes: 60, enabled: true },
      'Spotify': { limit_minutes: 180, enabled: false }
    };
    STATE.detectableApps = ['Visual Studio Code', 'League of Legends', 'Valorant', 'Spotify', 'Discord', 'Google Chrome'];
    STATE.runningApps = ['Visual Studio Code', 'Discord', 'Spotify'];
    STATE.pairUrl = 'miku://pair?s=demo_showcase_2026&ip=192.168.1.50';
    STATE.linkConnected = true;
    STATE.linkName = 'Galaxy S24 Ultra (Miku-Link)';
    window.__mics = [
      { value: 'default', label: 'Predeterminado del sistema' },
      { value: '1', label: 'Micrófono Studio USB' }
    ];
    renderRail();
    render();
    return;
  }

  let backendOnline = false;
  try {
    if (window.Bridge?.getConfigKeys) {
      const res = await window.Bridge.getConfigKeys();
      if (res && res.keys) {
        STATE.keys = res.keys;
        backendOnline = true;
      }
    }
    if (!backendOnline) {
      // El backend aún está iniciando en el puerto 8000; evitar ráfaga de peticiones fallidas y esperar a core_connected / poll
      if (!_backendPollTimer) {
        let attempts = 0;
        _backendPollTimer = setInterval(async () => {
          attempts++;
          if (attempts > 25) {
            clearInterval(_backendPollTimer);
            _backendPollTimer = null;
            return;
          }
          try {
            const testRes = await window.Bridge?.getConfigKeys?.();
            if (testRes && testRes.keys) {
              clearInterval(_backendPollTimer);
              _backendPollTimer = null;
              loadBackendData();
            }
          } catch (_) {}
        }, 1200);
      }
      return;
    }
    if (window.Bridge?.getExecutionMode) {
      const emRes = await window.Bridge.getExecutionMode();
      if (emRes && emRes.current_mode) {
        STATE.execMode = emRes.current_mode;
        STATE.execDetails = emRes.current_details;
        backendOnline = true;
      }
    }
    if (window.Bridge?.getAgents) {
      const aRes = await window.Bridge.getAgents();
      if (aRes?.agents && aRes.agents.length > 0) {
        AG = aRes.agents;
        ls.set('miku_agents', AG);
        backendOnline = true;
      }
    }
    if (window.Bridge?.getModelsConfig) {
      const res = await window.Bridge.getModelsConfig();
      if (res && res.current) {
        STATE.models = res;
        backendOnline = true;
      }
    }
    if (window.Bridge?.getMcpServers) {
      const res = await window.Bridge.getMcpServers();
      STATE.mcp = res.servers || [];
    }
    if (window.Bridge?.getAlertsConfig) {
      const res = await window.Bridge.getAlertsConfig();
      STATE.alerts = res.alerts || {};
    }
    if (window.Bridge?.getDetectableApps) {
      const res = await window.Bridge.getDetectableApps();
      STATE.detectableApps = res.apps || [];
    }
    if (window.Bridge?.getRunningApps) {
      const res = await window.Bridge.getRunningApps();
      STATE.runningApps = res.apps || [];
    }
    if (window.Bridge?.getAudioDevices) {
      const aRes = await window.Bridge.getAudioDevices();
      if (aRes?.devices && aRes.devices.length > 0) {
        window.__mics = [
          { value: 'default', label: 'Predeterminado del sistema' },
          ...aRes.devices.map(d => ({
            value: String(d.index),
            label: d.name + (d.is_default ? ' (predeterminado)' : '')
          }))
        ];
        if (CAT === 'voz') {
          const micEl = document.getElementById('gs-mic');
          if (micEl) {
            GlideSelect(micEl, {
              options: window.__mics,
              value: CFG.mic || 'default',
              label: t('mic_title'),
              onChange: v => {
                CFG.mic = v;
                saveCfg();
                window.Bridge?.setAudioDevice?.(v);
              }
            });
          }
        }
      }
    }
    if (CFG.mic && window.Bridge?.setAudioDevice) {
      window.Bridge.setAudioDevice(CFG.mic).catch(() => {});
    }
  } catch (err) {
    console.warn("Error loading backend data in settings:", err);
  }
  const nextSnap = JSON.stringify({ k: STATE.keys, m: STATE.models?.current, e: STATE.execMode, mcp: STATE.mcp, al: STATE.alerts, ag: AG });
  if (!window.__lastBackendSnap || window.__lastBackendSnap !== nextSnap) {
    window.__lastBackendSnap = nextSnap;
    if (!typing() && CAT !== 'link') render();
  }

  // Si el backend aún no estaba listo al abrir la ventana, reintentar automáticamente en segundo plano
  if (!backendOnline && !_backendPollTimer) {
    let attempts = 0;
    _backendPollTimer = setInterval(async () => {
      attempts++;
      if (attempts > 20) {
        clearInterval(_backendPollTimer);
        _backendPollTimer = null;
        return;
      }
      try {
        const testRes = await window.Bridge?.getModelsConfig?.();
        if (testRes && testRes.current) {
          clearInterval(_backendPollTimer);
          _backendPollTimer = null;
          loadBackendData();
        }
      } catch (_) {}
    }, 1200);
  }
}

// Controles de ventana minimalista
function initWindowChrome() {
  const minBtn = document.getElementById('win-min');
  const clsBtn = document.getElementById('win-cls');
  if (clsBtn) {
    clsBtn.onclick = () => {
      if (window.__TAURI__?.core?.invoke) {
        window.__TAURI__.core.invoke('close_settings');
      } else {
        window.close();
      }
    };
  }
  if (minBtn) {
    minBtn.onclick = () => {
      if (window.__TAURI__?.core?.invoke) {
        window.__TAURI__.core.invoke('minimize_settings');
      }
    };
  }
  const railEl = document.getElementById('rail');
  if (railEl) {
    railEl.addEventListener('wheel', e => {
      if (e.deltaY !== 0) {
        e.preventDefault();
        railEl.scrollLeft += e.deltaY;
      }
    }, { passive: false });
  }
}
setTimeout(initWindowChrome, 50);
window.__lang = l => { CFG.lang = l; saveCfg(); renderRail(); render(); };
window.__goCat = cat => {
  if (cat && V[cat]) {
    CAT = cat;
    renderRail();
    render();
  }
};

window.addEventListener('hashchange', () => {
  const h = (location.hash || '').replace(/^#/, '');
  if (h && V[h] && CAT !== h) {
    window.__goCat(h);
  }
});

window.addEventListener('miku-core-connected', () => {
  if (_backendPollTimer) {
    clearInterval(_backendPollTimer);
    _backendPollTimer = null;
  }
  loadBackendData();
});

(async () => {
  const initialHash = (location.hash || '').replace(/^#/, '');
  if (initialHash && V[initialHash]) {
    CAT = initialHash;
  }
  renderRail();
  render();
  if (!window.Bridge?.isCoreConnected || window.Bridge.isCoreConnected()) {
    loadBackendData();
  }
  emit({ k: 'hello' });
})();
