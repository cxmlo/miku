const $=s=>document.querySelector(s),$$=s=>document.querySelectorAll(s),isl=$('#isl'),clamp=(v,a=-1,b=1)=>Math.max(a,Math.min(b,v));
const DEFAULT_AGENTS = [
  {id: 'github', name: 'GitHub', role: 'Control de versiones, commits, ramas, pull requests y repositorios', c: '#39D353', model: 'gemini-2.5-flash', active: true, isl: 1, outfit: 'shades'},
  {id: 'antigravity', name: 'Antigravity', role: 'Diseño UI/UX, animaciones y desarrollo frontend', c: '#00D2FF', model: 'gemini-2.5-pro', active: true, isl: 2, outfit: 'crown'}
];
const ST={ws:0,mic:0,link:0,name:'',tasks:0,api:1,agents:[...DEFAULT_AGENTS]};
const CFG={voice:1,autoclose:15,voice_volume:80,sfx_volume:60,barge_in:1,wake_paused:0,mic:'default',personality:'calm',hover_open:0,local_net:1,biometric:1,lang:'es'};
let SELA=-1,PG=0,LOCKI=0;

const QR=(()=>{
 const ECC=[10,16,26,18,24,16,18,22,22,26],BLK=[1,1,1,2,2,4,4,4,5,5];
 const mul=(x,y)=>{let z=0;for(let i=7;i>=0;i--){z=(z<<1)^((z>>>7)*0x11D);z^=((y>>>i)&1)*x}return z};
 const raw=v=>{let r=(16*v+128)*v+64;if(v>=2){const n=Math.floor(v/7)+2;r-=(25*n-10)*n-55;if(v>=7)r-=36}return r>>3};
 const cap=v=>raw(v)-ECC[v-1]*BLK[v-1];
 const rsDiv=d=>{const r=Array(d).fill(0);r[d-1]=1;let root=1;for(let i=0;i<d;i++){for(let j=0;j<d;j++){r[j]=mul(r[j],root);if(j+1<d)r[j]^=r[j+1]}root=mul(root,2)}return r};
 const rsRem=(data,div)=>{const r=div.map(()=>0);for(const b of data){const f=b^r.shift();r.push(0);div.forEach((c,i)=>r[i]^=mul(c,f))}return r};
 const bit=(x,i)=>((x>>>i)&1)!=0;
 function make(text){
  const bytes=[...new TextEncoder().encode(text)];let ver=1;
  for(;ver<=10;ver++){if(4+(ver<10?8:16)+bytes.length*8<=cap(ver)*8)break}
  if(ver>10)throw new Error('QR: texto demasiado largo');
  const bits=[],put=(v,n)=>{for(let i=n-1;i>=0;i--)bits.push((v>>>i)&1)},total=cap(ver)*8;
  put(4,4);put(bytes.length,ver<10?8:16);bytes.forEach(b=>put(b,8));
  put(0,Math.min(4,total-bits.length));put(0,(8-bits.length%8)%8);for(let p=0xEC;bits.length<total;p^=0xEC^0x11)put(p,8);
  const data=[];for(let i=0;i<bits.length;i+=8){let b=0;for(let j=0;j<8;j++)b=b<<1|bits[i+j];data.push(b)}
  const nb=BLK[ver-1],el=ECC[ver-1],rc=raw(ver),ns=nb-rc%nb,sl=Math.floor(rc/nb),div=rsDiv(el),blocks=[];
  for(let i=0,k=0;i<nb;i++){const dat=data.slice(k,k+sl-el+(i<ns?0:1));k+=dat.length;const ecc=rsRem(dat,div);if(i<ns)dat.push(0);blocks.push(dat.concat(ecc))}
  const all=[];for(let i=0;i<blocks[0].length;i++)blocks.forEach((b,j)=>{if(i!=sl-el||j>=ns)all.push(b[i])});
  const n=ver*4+17,M=Array.from({length:n},()=>Array(n).fill(false)),F=Array.from({length:n},()=>Array(n).fill(false));
  const sf=(x,y,d)=>{M[y][x]=d;F[y][x]=true};
  for(let i=0;i<n;i++){sf(6,i,i%2==0);sf(i,6,i%2==0)}
  const finder=(x,y)=>{for(let dy=-4;dy<=4;dy++)for(let dx=-4;dx<=4;dx++){const d=Math.max(Math.abs(dx),Math.abs(dy)),xx=x+dx,yy=y+dy;if(xx>=0&&xx<n&&yy>=0&&yy<n)sf(xx,yy,d!=2&&d!=4)}};
  finder(3,3);finder(n-4,3);finder(3,n-4);
  const ap=[];if(ver>1){const na=Math.floor(ver/7)+2,st=Math.ceil((ver*4+4)/(na*2-2))*2;ap.push(6);for(let p=n-7;ap.length<na;p-=st)ap.splice(1,0,p)}
  ap.forEach((a,i)=>ap.forEach((b,j)=>{if(!((i==0&&j==0)||(i==0&&j==ap.length-1)||(i==ap.length-1&&j==0)))for(let dy=-2;dy<=2;dy++)for(let dx=-2;dx<=2;dx++)sf(a+dx,b+dy,Math.max(Math.abs(dx),Math.abs(dy))!=1)}));
  const fmt=m=>{const d=m;let r=d;for(let i=0;i<10;i++)r=(r<<1)^((r>>>9)*0x537);const b=((d<<10)|r)^0x5412;
   for(let i=0;i<=5;i++)sf(8,i,bit(b,i));sf(8,7,bit(b,6));sf(8,8,bit(b,7));sf(7,8,bit(b,8));for(let i=9;i<15;i++)sf(14-i,8,bit(b,i));
   for(let i=0;i<8;i++)sf(n-1-i,8,bit(b,i));for(let i=8;i<15;i++)sf(8,n-15+i,bit(b,i));sf(8,n-8,true)};
  fmt(0);
  if(ver>=7){let r=ver;for(let i=0;i<12;i++)r=(r<<1)^((r>>>11)*0x1F25);const b=(ver<<12)|r;for(let i=0;i<18;i++){const c=bit(b,i),a=n-11+i%3,q=Math.floor(i/3);sf(a,q,c);sf(q,a,c)}}
  for(let i=0,right=n-1;right>=1;right-=2){if(right==6)right=5;for(let v=0;v<n;v++)for(let j=0;j<2;j++){const x=right-j,up=((right+1)&2)==0,y=up?n-1-v:v;if(!F[y][x]&&i<all.length*8){M[y][x]=bit(all[i>>>3],7-(i&7));i++}}}
  const apply=m=>{for(let y=0;y<n;y++)for(let x=0;x<n;x++){let inv;switch(m){case 0:inv=(x+y)%2==0;break;case 1:inv=y%2==0;break;case 2:inv=x%3==0;break;case 3:inv=(x+y)%3==0;break;case 4:inv=(Math.floor(x/3)+Math.floor(y/2))%2==0;break;case 5:inv=x*y%2+x*y%3==0;break;case 6:inv=(x*y%2+x*y%3)%2==0;break;default:inv=((x+y)%2+x*y%3)%2==0}if(!F[y][x]&&inv)M[y][x]=!M[y][x]}};
  const pen=()=>{let p=0;for(let t=0;t<2;t++)for(let a=0;a<n;a++){let run=1;for(let b=1;b<n;b++){const c=t?M[b][a]:M[a][b],pv=t?M[b-1][a]:M[a][b-1];if(c==pv){run++;if(run==5)p+=3;else if(run>5)p++}else run=1}}
   for(let y=0;y<n-1;y++)for(let x=0;x<n-1;x++){const c=M[y][x];if(c==M[y][x+1]&&c==M[y+1][x]&&c==M[y+1][x+1])p+=3}
   let dk=0;M.forEach(r=>r.forEach(v=>dk+=v?1:0));return p+Math.floor(Math.abs(dk*20-n*n*10)/(n*n))*10};
  let best=0,bp=1e9;for(let m=0;m<8;m++){apply(m);fmt(m);const p=pen();apply(m);if(p<bp){bp=p;best=m}}
  apply(best);fmt(best);return M}
 function draw(cv,text,px=288,fg='#111',bg='#fff'){const M=make(text),n=M.length,q=3,s=Math.max(1,Math.floor(px/(n+2*q))),d=s*(n+2*q),off=Math.floor((px-s*n)/2);cv.width=cv.height=px;
  const x=cv.getContext('2d');x.imageSmoothingEnabled=false;x.fillStyle=bg;x.fillRect(0,0,px,px);x.fillStyle=fg;for(let y=0;y<n;y++)for(let i=0;i<n;i++)if(M[y][i])x.fillRect(off+i*s,off+y*s,s,s)}
 return{make,draw}})();

/* ───────── 1 · MIKU (Canvas 2D procedural) ───────── */
const cv=$('#mk'),BL=[59,158,255];let c=cv.getContext('2d');c.scale(2,2);c.translate(20,20);let EP=[[0,0],[0,0]],OUT='none';try{OUT=localStorage.getItem('miku_outfit')||'none'}catch{}
const X={
idle:{e:'o',m:'dot'},
listening:{e:'o',m:'O',fx:'listen',gi:1.5},
thinking:{arms:[.5,0,1.1,-12],e:'o',m:'dot',lk:[.75,-.85],fx:'think',g:[170,140,255],gi:1.3,t:-.05},
talking:{e:'o',m:'talk',fx:'talk',bounce:1},
searching:{e:'o',m:'dot',scan:1,fx:'search'},
working:{e:'o',m:'frown',br:.6,fx:'work',lk:[0,.35]},
happy:{arms:[.9,-8,.9,-8],e:'arc',m:'smile',fx:'happy',blush:1,hop:1},
proud:{arms:[.9,-8,.9,-8],e:'o',m:'smile',fx:'proud',sy:1.05,gi:1.4},
wink:{e:'wink',m:'smile',fx:'happy',t:.1},
love:{arms:[.8,-4,.8,-4],e:'o',m:'smile',fx:'love',blush:1,g:[255,157,184],gi:1.3},
surprised:{arms:[1.05,-12,1.05,-12],e:'o',m:'O',fx:'surp',big:1,jump:1,trk:.25},
question:{e:'o',m:'dot',fx:'q',t:.12},
annoyed:{e:'ang',m:'grr',br:1,fx:'ann',lk:[0,.08],t:-.03,sy:.96,trem:1,blush:1,blc:'#ff5a4d',g:[255,95,85],gi:1.4,arms:[.15,6,.15,6]},
sleeping:{e:'line',m:'none',fx:'zzz',sy:.92,gi:.5,lk:[0,.32],trk:0},
error:{lk:[0,.5],arms:[.15,5,.15,5],e:'x',m:'frown',fx:'err',shake:1,g:[255,122,112]},
dizzy:{lk:[0,0],flap:1,e:'spiral',m:'frown',fx:'diz',wob:1},
look:{e:'o',m:'dot'},
squash:{e:'arc',m:'dot',squash:1},
swallow:{e:'o',m:'eat',mo:.62,big:1,arms:[.95,-10,.95,-10],gi:1.45},
eat:{e:'o',m:'eat',big:1,arms:[1,-12,1,-12],gi:1.6,trk:.2},
chew:{e:'arc',m:'eat',blush:1,arms:[.9,-8,.9,-8],gi:1.3,hop:1},
point_upd:{arms:[.3,2,1.15,-24],e:'wink',m:'smile',lk:[1.0,-0.15],fx:'happy',hop:1,blush:1,t:0.08},
wave:{e:'o',m:'smile',fx:'wave',wave:1}
};
const P={al:.5,ll:0,ar:.5,lr:0,lx:0,ly:0,tilt:0,gi:1,r:59,g:158,b:255,sq:0,sv:0,jy:0,jv:0,sy:1,big:1,br:0,bl:0,mo:0};
const EAT={on:0,t0:0,fx:0,fy:0,ax:0,ay:0,gx:0,gy:0,mo:()=>0};
let base='idle',cur='idle',mx=0,my=0,ov=[0,0],t=0,ct=0,last=performance.now(),nb=2,bt=-9,emT,idleT=Date.now();
let bl='#5aaeff',BODY='#fff';const ML={x:0,y:-40},dark='#172B40',rgb=(a)=>`rgba(${P.r|0},${P.g|0},${P.b|0},${a})`;
const L=(a,b,x,y)=>{c.moveTo(a,b);c.lineTo(x,y)};
function spark(x,y,r){c.beginPath();c.moveTo(x,y-r);c.quadraticCurveTo(x,y,x+r,y);c.quadraticCurveTo(x,y,x,y+r);c.quadraticCurveTo(x,y,x-r,y);c.quadraticCurveTo(x,y,x,y-r);c.fill()}
function heart(x,y,s){c.beginPath();c.moveTo(x,y+s*.8);c.bezierCurveTo(x-s*1.2,y-s*.1,x-s*.6,y-s*.9,x,y-s*.35);c.bezierCurveTo(x+s*.6,y-s*.9,x+s*1.2,y-s*.1,x,y+s*.8);c.fill()}
const gr=(x0,y0,x1,y1,a,b)=>{const g=c.createLinearGradient(x0,y0,x1,y1);g.addColorStop(0,a);g.addColorStop(1,b);return g};
function star5(x,y,ro,ri,rot=0){c.beginPath();for(let i=0;i<10;i++){const r=i%2?ri:ro,a=rot-Math.PI/2+i*Math.PI/5;c[i?'lineTo':'moveTo'](x+Math.cos(a)*r,y+Math.sin(a)*r)}c.closePath()}
function gear(x,y,R,n,rot){c.save();c.translate(x,y);c.rotate(rot);const st=6.2832/n;c.beginPath();let f=1;for(let i=0;i<n;i++)for(const[r,o]of[[.76,-.3],[1,-.17],[1,.17],[.76,.3]]){const a=(i+o)*st;c[f?'moveTo':'lineTo'](Math.cos(a)*R*r,Math.sin(a)*R*r);f=0}c.closePath();c.moveTo(R*.3,0);c.arc(0,0,R*.3,0,6.2832);c.fillStyle=gr(-R,-R,R,R,'#a8d6ff','#3a86ea');c.fill('evenodd');c.strokeStyle='rgba(255,255,255,.65)';c.lineWidth=1.3;c.beginPath();c.arc(0,0,R*.62,3.6,4.8);c.stroke();c.restore()}
function heart2(x,y,sz,rot){c.save();c.translate(x,y);c.rotate(rot);c.shadowColor='rgba(255,92,138,.6)';c.shadowBlur=8;c.fillStyle=gr(0,-sz,0,sz,'#ffc3d4','#ff5c8a');heart(0,0,sz);c.shadowBlur=0;c.fillStyle='rgba(255,255,255,.7)';c.beginPath();c.ellipse(-sz*.45,-sz*.35,sz*.22,sz*.13,-.7,0,7);c.fill();c.restore()}
const FX={
listen(){c.lineCap='round';c.shadowColor=bl;c.shadowBlur=8;for(let i=0;i<3;i++)for(const d of[-1,1]){c.globalAlpha=.25+.75*Math.abs(Math.sin(t*3.6-i*.8));c.strokeStyle=bl;c.lineWidth=3.2-i*.6;c.beginPath();const a=d>0?-.8:Math.PI-.8;c.arc(80+d*(53+i*9),66,10+i*5,a,a+1.6);c.stroke()}},
think(){const b=Math.sin(t*2)*1.5;c.save();c.translate(0,b);c.shadowColor='rgba(120,180,255,.65)';c.shadowBlur=10;c.fillStyle='#eef5ff';for(const[x,y,r]of[[120,42,2.6],[125,33,4.2],[128,22,7],[136,16,8.6],[146,21,7.6],[143,28,6.6],[132,28,6.6]]){c.beginPath();c.arc(x,y,r,0,7);c.fill()}
 c.shadowBlur=0;c.fillStyle='rgba(130,175,235,.3)';c.beginPath();c.ellipse(138,31,11,2.6,0,0,7);c.fill();c.fillStyle='rgba(255,255,255,.95)';c.beginPath();c.ellipse(133,13,4,1.8,-.4,0,7);c.fill();
 for(let i=0;i<3;i++){c.globalAlpha=.3+.7*Math.max(0,Math.sin(t*4-i*.9));c.fillStyle='#4a9df0';c.beginPath();c.arc(130+i*8,23,2.3,0,7);c.fill()}c.restore()},
talk(){c.lineCap='round';c.lineWidth=3.4;c.strokeStyle=bl;c.shadowColor=bl;c.shadowBlur=6;for(const i of[-1,0,1]){const l=6+7*Math.abs(Math.sin(t*9+i*1.3));c.globalAlpha=.5+.5*Math.abs(Math.sin(t*9+i));c.beginPath();c.moveTo(131,62+i*11);c.lineTo(131+l,62+i*11+i*4);c.stroke()}},
search(){const x=120+Math.sin(t*2.2)*8,y=52+Math.cos(t*2.2)*3;c.save();c.translate(x,y);c.rotate(-.15);c.lineCap='round';
 c.strokeStyle=gr(0,8,0,24,'#e3ecf8','#8ea6c6');c.lineWidth=6;c.beginPath();c.moveTo(7.5,8);c.lineTo(15,16.5);c.stroke();c.strokeStyle='#2f6fb5';c.lineWidth=6.2;c.beginPath();c.moveTo(11.8,12.8);c.lineTo(15,16.5);c.stroke();
 c.shadowColor=bl;c.shadowBlur=8;c.fillStyle=gr(-8,-8,8,8,'rgba(215,238,255,.5)','rgba(120,190,255,.16)');c.beginPath();c.arc(0,0,10.5,0,7);c.fill();c.strokeStyle=gr(-10,-10,10,10,'#a6d6ff','#3B8EF0');c.lineWidth=3.4;c.stroke();c.shadowBlur=0;
 c.strokeStyle='rgba(255,255,255,.85)';c.lineWidth=1.8;c.beginPath();c.arc(0,0,6.6,Math.PI*1.08,Math.PI*1.45);c.stroke();c.fillStyle='rgba(255,255,255,.92)';spark(3.5,3.5,2.6*(.7+.3*Math.sin(t*6)));c.restore()},
work(){gear(127,33,10,8,t*1.2);gear(111,50,6,6,-t*2+.3);c.fillStyle=gr(40,22,40,42,'#cfe6ff','#5aaeff');c.shadowColor=bl;c.shadowBlur=6;c.globalAlpha=.5+.5*Math.sin(t*4);spark(44,32,5.5);spark(36,50,3.4)},
happy(){c.lineCap='round';c.strokeStyle=bl;c.lineWidth=3;c.shadowColor=bl;c.shadowBlur=6;c.globalAlpha=.6+.4*Math.sin(t*6);c.beginPath();L(32,44,26,40);L(40,32,36,25);L(128,44,134,40);L(120,32,124,25);c.stroke();c.fillStyle='#cfe6ff';spark(138,26,3.4*(1+.2*Math.sin(t*5)));spark(22,28,3)},
proud(){const k=1+.18*Math.sin(t*4);c.shadowColor=bl;c.shadowBlur=8;c.fillStyle=gr(0,22,0,46,'#d8edff','#3B9EFF');spark(128,34,10*k);spark(36,58,6.5/k);spark(136,58,4.2*k)},
love(){for(let i=0;i<3;i++){const p=((t*.5+i/3)%1);c.globalAlpha=Math.min(1,(1-p)*1.6);heart2(112+i*11+Math.sin(t*3+i)*4,72-p*46,5.2+i,Math.sin(t*2+i)*.25)}},
surp(){c.lineCap='round';c.strokeStyle=bl;c.lineWidth=3.4;c.shadowColor=bl;c.shadowBlur=6;c.globalAlpha=.65+.35*Math.sin(t*10);c.beginPath();L(80,24,80,11);L(63,28,56,18);L(97,28,104,18);c.stroke()},
q(){const y=Math.sin(t*2.6)*2.5;c.save();c.translate(124,38+y);c.rotate(Math.sin(t*2)*.08);c.shadowColor='rgba(59,158,255,.7)';c.shadowBlur=12;c.fillStyle=gr(0,-12,0,12,'#92d2ff','#3B9EFF');c.beginPath();c.arc(0,0,12,0,7);c.fill();c.beginPath();c.moveTo(-8,8);c.lineTo(-14.5,15.5);c.lineTo(-2,12);c.fill();c.shadowBlur=0;
 c.fillStyle='rgba(255,255,255,.33)';c.beginPath();c.ellipse(-3,-6.5,6,3,-.5,0,7);c.fill();c.strokeStyle='#fff';c.lineWidth=3.2;c.lineCap='round';c.beginPath();c.arc(0,-3.4,4.4,Math.PI*1.08,Math.PI*2.45);c.lineTo(0,3);c.stroke();c.fillStyle='#fff';c.beginPath();c.arc(0,7.2,1.7,0,7);c.fill();c.restore()},
ann(){const k=1+.14*Math.sin(t*9);c.save();c.translate(124,32);c.rotate(Math.sin(t*5)*.08);c.scale(k,k);c.strokeStyle='#ff4d42';c.shadowColor='#ff3b30';c.shadowBlur=10;c.lineWidth=3.6;c.lineCap='round';
 for(const[sx,sy]of[[1,1],[-1,1],[1,-1],[-1,-1]]){c.beginPath();c.moveTo(sx*3,sy*10);c.quadraticCurveTo(sx*3,sy*3,sx*10,sy*3);c.stroke()}c.restore();
 c.fillStyle='rgba(255,255,255,.6)';for(let i=0;i<3;i++){const p=(t*.8+i/3)%1;for(const d of[-1,1]){c.globalAlpha=(1-p)*.5;c.beginPath();c.arc(80+d*(47+i*2),54-p*38,2.5+p*4.5,0,7);c.fill()}}},
zzz(){c.lineCap=c.lineJoin='round';c.shadowColor=bl;c.shadowBlur=7;for(let i=0;i<3;i++){const p=(t*.35+i/3)%1,z=3.2+i*1.6+p*1.4,x=112+p*18+i*4,y=56-p*30-i*3;c.globalAlpha=Math.sin(p*Math.PI)*.9;c.strokeStyle=gr(x,y-z,x,y+z,'#dcefff','#5aaeff');c.lineWidth=2.4+z*.12;c.beginPath();c.moveTo(x-z,y-z);c.lineTo(x+z,y-z);c.lineTo(x-z,y+z);c.lineTo(x+z,y+z);c.stroke()}},
err(){const k=1+.06*Math.sin(t*10);c.save();c.translate(124,32);c.scale(k,k);c.shadowColor='rgba(255,90,90,.7)';c.shadowBlur=10;c.fillStyle=gr(0,-12,0,12,'#ff9d96','#ee4d4d');c.beginPath();c.arc(0,0,12,0,7);c.fill();c.shadowBlur=0;c.fillStyle='rgba(255,255,255,.3)';c.beginPath();c.ellipse(-3,-6.5,6,3,-.5,0,7);c.fill();c.strokeStyle='#fff';c.lineWidth=3.4;c.lineCap='round';c.beginPath();L(-4.5,-4.5,4.5,4.5);L(4.5,-4.5,-4.5,4.5);c.stroke();c.restore()},
diz(){for(let i=0;i<3;i++){const a=t*4+i*2.094,x=80+Math.cos(a)*52,y=34+Math.sin(a)*10;c.globalAlpha=.65+.35*Math.sin(a);c.shadowColor='#ffd54a';c.shadowBlur=8;c.fillStyle=gr(x,y-6,x,y+6,'#fff2a6','#ffb62b');star5(x,y,5.6,2.4,t*2+i);c.fill()}c.shadowBlur=0;c.strokeStyle=bl;c.globalAlpha=.4;c.lineWidth=2;c.lineCap='round';const w=Math.sin(t*3)*.2;c.beginPath();c.arc(80,34,58,Math.PI*1.12+w,Math.PI*1.4+w);c.stroke()},
mail(){const y=Math.sin(t*3)*2;c.save();c.translate(80,112+y);c.shadowColor='rgba(0,0,0,.35)';c.shadowBlur=6;c.shadowOffsetY=2;c.fillStyle=gr(0,-11,0,12,'#fff','#d9e5f5');c.beginPath();c.roundRect(-19,-11,38,24,4);c.fill();c.shadowBlur=0;c.shadowOffsetY=0;c.strokeStyle='#9db4d3';c.lineWidth=1.5;c.lineJoin='round';c.beginPath();L(-18,-9,0,3);c.lineTo(18,-9);c.moveTo(-18,11);c.lineTo(-6,0);c.moveTo(18,11);c.lineTo(6,0);c.stroke();c.fillStyle='#ff9db8';c.beginPath();c.arc(0,3,2.6,0,7);c.fill();c.restore()},
wave(){c.lineCap='round';c.strokeStyle=bl;c.lineWidth=3;c.shadowColor=bl;c.shadowBlur=6;for(let i=0;i<2;i++){c.globalAlpha=.3+.7*Math.abs(Math.sin(t*6-i));c.beginPath();c.arc(130,56,9+i*6,-1,.5);c.stroke()}c.fillStyle='#cfe6ff';spark(142,34,3.4)}
};

Object.assign(FX,{
search(){const x=118+Math.sin(t*2.2)*9,y=50+Math.cos(t*2.2)*4;c.save();c.translate(x,y);c.rotate(-.2);c.lineCap='round';
 c.strokeStyle='#1d2f4d';c.lineWidth=8;c.beginPath();L(8,9,22,23);c.stroke();
 c.strokeStyle=gr(0,8,0,24,'#5b7fb5','#2a4472');c.lineWidth=6;c.beginPath();L(8,9,22,23);c.stroke();
 c.strokeStyle='rgba(255,255,255,.35)';c.lineWidth=1.4;c.beginPath();L(10,8,23,21);c.stroke();
 c.strokeStyle=gr(0,0,12,12,'#f4f8ff','#8aa3c7');c.lineWidth=7.5;c.beginPath();L(6.5,7.5,10,11);c.stroke();
 c.shadowColor=bl;c.shadowBlur=10;c.fillStyle=gr(-10,-10,10,10,'rgba(230,246,255,.55)','rgba(110,185,255,.2)');c.beginPath();c.arc(0,0,11,0,7);c.fill();c.shadowBlur=0;
 c.lineWidth=3.6;c.strokeStyle=gr(-11,-11,11,11,'#f4f8ff','#6f9fe0');c.stroke();
 c.lineWidth=1;c.strokeStyle='rgba(30,70,140,.5)';c.beginPath();c.arc(0,0,12.9,0,7);c.stroke();
 c.strokeStyle='rgba(255,255,255,.9)';c.lineWidth=2;c.beginPath();c.arc(0,0,7.2,Math.PI*1.1,Math.PI*1.45);c.stroke();
 c.fillStyle='#fff';c.beginPath();c.arc(-3.2,-4.5,1.3,0,7);c.fill();spark(4,4,2.6*(.7+.3*Math.sin(t*6)));c.restore()},
q(){const y=Math.sin(t*2.6)*2.5;c.save();c.translate(124,36+y);c.rotate(Math.sin(t*2)*.07);
 const bp=()=>{c.beginPath();c.roundRect(-15,-13,30,25,10);c.moveTo(-6,11);c.quadraticCurveTo(-8,16,-14,18);c.quadraticCurveTo(-3,18,3,11);c.closePath()};
 c.shadowColor='rgba(59,158,255,.75)';c.shadowBlur=12;c.fillStyle=gr(0,-13,0,13,'#a9dcff','#2f86f0');bp();c.fill();c.shadowBlur=0;
 c.strokeStyle='rgba(255,255,255,.55)';c.lineWidth=1.2;bp();c.stroke();
 c.fillStyle='rgba(255,255,255,.28)';c.beginPath();c.roundRect(-12,-11,24,8,5);c.fill();
 c.strokeStyle='#fff';c.lineWidth=3.2;c.lineCap='round';c.beginPath();c.arc(0,-3.6,4.6,Math.PI*1.1,Math.PI*2.5);c.lineTo(0,2.4);c.stroke();
 c.fillStyle='#fff';c.beginPath();c.arc(0,7,1.8,0,7);c.fill();c.restore()},
think(){c.save();c.translate(0,Math.sin(t*2)*1.5);c.shadowColor='rgba(120,180,255,.6)';c.shadowBlur=10;
 for(const[x,y,r]of[[112,56,2],[119,46,3.4]]){c.fillStyle=gr(x,y-r,x,y+r,'#fff','#cfe0f7');c.beginPath();c.arc(x,y,r,0,7);c.fill()}
 c.fillStyle=gr(0,14,0,48,'#fff','#c9dcf5');c.beginPath();for(const[x,y,r]of[[124,32,8],[133,24,10],[146,24,9],[154,32,8],[146,40,8],[133,40,9]]){c.moveTo(x+r,y);c.arc(x,y,r,0,7)}c.fill();c.shadowBlur=0;
 c.fillStyle='rgba(255,255,255,.9)';c.beginPath();c.ellipse(131,18,5,2,-.4,0,7);c.fill();
 for(let i=0;i<3;i++){c.globalAlpha=.3+.7*Math.max(0,Math.sin(t*4-i*.9));c.fillStyle='#3B8EF0';c.beginPath();c.arc(135+i*8,32,2.5,0,7);c.fill()}c.restore()}
});
function bodyPath(sx=1,sy=1){const p=new Path2D();for(let i=0;i<=84;i++){const a=i/84*6.2832,ca=Math.cos(a),sa=Math.sin(a),top=sa<0,e=top?1.18:.6,ry=top?47:40,px=49*sx*Math.sign(ca)*Math.abs(ca)**e,py=-40+ry*sy*Math.sign(sa)*Math.abs(sa)**e;i?p.lineTo(px,py):p.moveTo(px,py)}p.closePath();return p}
let TAILS=true;try{TAILS=localStorage.getItem('miku_tails')!='0'}catch{}
const TL=[{a:0,v:0},{a:0,v:0}],TC=['#62e8de','#25b1ab'];
function tails(dt,s){TL.forEach((T,i)=>{const d=i?1:-1,tg=.12+Math.sin(t*1.6+i*1.1)*.06+P.tilt*d*1.1+Math.min(.45,Math.abs(P.jv)*.0035)+((s.bounce||s.hop)?Math.sin(t*(s.bounce?6:4.2)+i)*.14:0)-(s.nt?.05:0);
 T.v+=(-70*(T.a-tg)-7.5*T.v)*dt;T.a+=T.v*dt;
 c.save();c.translate(d*41,-62);c.scale(d,1);c.rotate(-T.a);
 const B=[[0,0],[20,-8],[36,30],[26,74]],bz=(u,k)=>{const m=1-u;return m*m*m*B[0][k]+3*m*m*u*B[1][k]+3*m*u*u*B[3][k]+u*u*u*B[3][k]},dz=(u,k)=>{const m=1-u;return 3*m*m*(B[1][k]-B[0][k])+6*m*u*(B[2][k]-B[1][k])+3*u*u*(B[3][k]-B[2][k])};
 const N=20,pt=[];for(let j=0;j<=N;j++){const u=j/N,dx=dz(u,0),dy=dz(u,1),l=Math.hypot(dx,dy)||1;pt.push({x:bz(u,0),y:bz(u,1),nx:-dy/l,ny:dx/l,w:(1-Math.pow(u,1.5))*(.62+.38*Math.sin(Math.min(1,u*2.4)*1.5708))*9.5})}
 c.beginPath();pt.forEach((q,j)=>c[j?'lineTo':'moveTo'](q.x+q.nx*q.w,q.y+q.ny*q.w));for(let j=N;j>=0;j--){const q=pt[j];c.lineTo(q.x-q.nx*q.w,q.y-q.ny*q.w)}c.closePath();c.fillStyle=gr(0,-6,0,74,TC[0],TC[1]);c.fill();
 c.lineCap='round';for(const[o,col,lw,a0,a1]of[[-.5,'rgba(18,110,115,.32)',1.3,.05,.95],[.1,'rgba(18,110,115,.28)',1.2,.05,.85],[.55,'rgba(255,255,255,.5)',1.7,.08,.6]]){c.strokeStyle=col;c.lineWidth=lw;c.beginPath();for(let j=Math.round(a0*N);j<=Math.round(a1*N);j++){const q=pt[j];c[j==Math.round(a0*N)?'moveTo':'lineTo'](q.x+q.nx*q.w*o,q.y+q.ny*q.w*o)}c.stroke()}
 const q=pt[1];c.save();c.translate(q.x,q.y);c.rotate(Math.atan2(dz(.07,1),dz(.07,0)));c.fillStyle='#24344f';c.beginPath();c.roundRect(-3.2,-(q.w+1.4),6.4,2*q.w+2.8,3);c.fill();c.fillStyle='#ff8fb1';c.beginPath();c.arc(0,-(q.w+1.4)+1.6,1.7,0,7);c.fill();c.restore();c.restore()})}
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
 else if(m=='eat'){const o=Math.max(0,Math.min(1.1,P.mo)),w=3.4+o*6.4,h=.9+o*10.8,cy=1+h*.4;c.ellipse(0,cy,w,h,0,0,7);c.fill();
  if(o>.22){c.save();c.beginPath();c.ellipse(0,cy,w,h,0,0,7);c.clip();c.fillStyle='#FF9DB8';c.beginPath();c.ellipse(0,cy+h*.58,w*.8,h*.5,0,0,7);c.fill();c.restore()}}
}
function hand(d,rot,oy,g){c.save();c.translate(d*50,-28+oy);c.rotate(rot*d);c.beginPath();c.ellipse(0,0,6.5,12,0,0,7);c.fillStyle=g;c.fill();c.restore()}

const ringR=y=>Math.pow(1-Math.pow(Math.min(1,Math.abs(y)),2.7),1/2.7),surf=(y,lon,sc=1)=>{const r=ringR(y)*sc;return[r*Math.sin(lon),y,r*Math.cos(lon)]};
function rot3(p){const yw=P.lx*.5,pt=-.30+(-P.ly*.4)*.4,cy=Math.cos(yw),sy=Math.sin(yw),cp=Math.cos(pt),sp=Math.sin(pt),x1=p[0]*cy+p[2]*sy,z1=-p[0]*sy+p[2]*cy;return[x1,p[1]*cp+z1*sp,-p[1]*sp+z1*cp]}
const pj=p=>{const r=rot3(p);return{x:r[0]*49,y:-40-r[1]*(r[1]>0?47:40),z:r[2]}};
const frontArc=(y,sc)=>{const a=[];for(let i=0;i<=100;i++){const q=pj(surf(y,-Math.PI+i/100*6.2832,sc));if(q.z>=-.02)a.push(q)}return a.sort((p,q)=>p.x-q.x)};
const circ=(y,r)=>{const a=[];for(let i=0;i<=60;i++){const q=pj([r*Math.sin(i/60*6.2832),y,r*Math.cos(i/60*6.2832)]);if(q.z>=-.02)a.push(q)}return a.sort((p,q)=>p.x-q.x)};
const capClip=(y,sc)=>{const a=frontArc(y,sc),p=new Path2D(),L0=a[0],R0=a[a.length-1];p.moveTo(L0.x-49,L0.y);a.forEach(q=>p.lineTo(q.x,q.y));p.lineTo(R0.x+49,R0.y);p.lineTo(110,-180);p.lineTo(-110,-180);p.closePath();return p};
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
 const sp=pj([0,.44,1.08]);c.fillStyle=gr(sp.x,sp.y-7,sp.x,sp.y+7,'#fff3b0','#ffc21a');star5(sp.x,sp.y,6.2,2.8,Math.sin(t*1.6)*.25);c.fill();
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
window.__miku_paused = false;
window.__miku_hidden = false;
let frameRaf = null;
function startFrameLoop() {
  if (window.__miku_paused || window.__miku_hidden) return;
  if (!frameRaf) frameRaf = requestAnimationFrame(frame);
}
function stopFrameLoop() {
  if (frameRaf) { cancelAnimationFrame(frameRaf); frameRaf = null; }
}

function frame(now){
 if(window.__miku_paused || window.__miku_hidden){ frameRaf = null; return; }
 frameRaf = requestAnimationFrame(frame);
 const dt=Math.min(.04,(now-last)/1000);last=now;t=now/1000;const s=X[cur],k=1-Math.exp(-dt*9);
 const TK=s.trk??1;let[tx,ty]=cur=='look'?ov:[mx*TK,my*TK];if(s.lk)[tx,ty]=s.lk;if(s.scan)tx=Math.sin(t*7);if(EAT.on){tx=EAT.gx;ty=EAT.gy}
 P.lx+=(tx-P.lx)*k;P.ly+=(ty-P.ly)*k;
 const g=s.g||BL,gi=s.gi||1;P.r+=(g[0]-P.r)*k;P.g+=(g[1]-P.g)*k;P.b+=(g[2]-P.b)*k;P.gi+=(gi-P.gi)*k;
 P.tilt+=((s.t||0)+(s.wob?Math.sin(t*3)*.13:0)+P.lx*.035-P.tilt)*k;
 P.bl+=((s.blush?1:0)-P.bl)*k;P.sy+=((s.sy||1)-P.sy)*k;P.big+=((s.big?1.18:1)-P.big)*k;P.br+=((s.br||0)-P.br)*k;{const moT=EAT.on?EAT.mo():(s.mo?s.mo+.1*Math.sin(t*5.5):0);P.mo+=(moT-P.mo)*(1-Math.exp(-dt*(EAT.on?28:11)))}
 P.sv+=(-190*P.sq-9*P.sv)*dt;P.sq+=P.sv*dt;P.jv+=(-60*P.jy-7*P.jv)*dt;P.jy+=P.jv*dt;
 if(t>nb){bt=t;nb=t+2.5+Math.random()*3.5}const kb=t-bt,blink=kb<.14?Math.sin(kb/.14*Math.PI):0;
 const op=(s.half?.6:1)*(1-blink),breath=1+.014*Math.sin(t*(cur=='sleeping'?1.1:2.2));
 const sh=(s.shake?Math.sin(t*45)*3*Math.max(0,1-(t-ct)):0)+(s.trem?Math.sin(t*41)*1.2:0);
 const bob=(s.bounce?-Math.abs(Math.sin(t*6))*4:0)+(s.hop?-Math.abs(Math.sin(t*4.2))*5:0)+P.jy;

 drawChar(s,k,dt,op,breath,sh,bob);
 if(FX[s.fx]){c.save();FX[s.fx]();c.restore();c.globalAlpha=1}
 place(dt);warpDraw(dt,now)
}

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

  // Mascot Head Notification Badge (speech bubble ... or permission !)
  const unreadAg = getUnreadAgent();
  const isApprove = (scene === 'approve');
  if (unreadAg || isApprove) {
    c.save();
    c.translate(-38, -66);
    if (isApprove) {
      c.shadowColor = 'rgba(255, 179, 0, 0.85)';
      c.shadowBlur = 12;
      c.fillStyle = '#ffb300';
      c.beginPath();
      c.arc(0, 0, 11, 0, Math.PI * 2);
      c.fill();
      c.shadowBlur = 0;
      c.strokeStyle = '#14141c';
      c.lineWidth = 2.2;
      c.stroke();
      c.fillStyle = '#14141c';
      c.font = 'bold 12px "Segoe UI", sans-serif';
      c.textAlign = 'center';
      c.textBaseline = 'middle';
      c.fillText('!', 0, 0.8);
    } else if (unreadAg) {
      c.shadowColor = 'rgba(147, 51, 234, 0.85)';
      c.shadowBlur = 14;
      c.fillStyle = '#8b5cf6';
      c.beginPath();
      c.arc(0, 0, 11, 0, Math.PI * 2);
      c.fill();
      c.shadowBlur = 0;
      c.strokeStyle = '#14141c';
      c.lineWidth = 2.2;
      c.stroke();
      c.fillStyle = '#ffffff';
      for (let di = -1; di <= 1; di++) {
        c.beginPath();
        c.arc(di * 4.2, 0.5, 1.35, 0, Math.PI * 2);
        c.fill();
      }
    }
    c.restore();
  }

 c.restore();
 }

const SNAP=new Map(),PRIN={id:'miku',name:'Miku',c:'#f5f5f5',outfit:OUT},drag={on:0,x:0,y:0},THK={on:0,start:0,end:0,dur:0};
const curAg=()=>SELA<0?PRIN:(ST.agents[SELA]||PRIN),bodyOf=a=>a===PRIN?'#fff':a.c;
const lum=h=>{const n=parseInt(h.slice(1),16);return(.299*(n>>16)+.587*((n>>8)&255)+.114*(n&255))/255};
const mix=(h,t=.35)=>{const n=parseInt(h.slice(1),16),f=s=>Math.round(((n>>s)&255)*(1-t)+255*t);return`rgb(${f(16)},${f(8)},${f(0)})`};
function snap(color,outfit,crop,blink=0){const key=color+'|'+outfit+'|'+crop+'|'+blink;if(SNAP.has(key))return SNAP.get(key);if(SNAP.size>120)SNAP.delete(SNAP.keys().next().value);
 const off=document.createElement('canvas');off.width=off.height=400;const oc=off.getContext('2d');oc.scale(2,2);oc.translate(20,20);
 const sv={c,OUT,BODY,P:{...P},mx:ML.x,my:ML.y,ep:EP.map(a=>a.slice())};
 c=oc;OUT=outfit;BODY=color;
 const isPrin = color === '#fff';
 const hh=[...(color+'|'+outfit)].reduce((a,b)=>Math.imul(31,a)+b.charCodeAt(0)|0,0);
 const rx = isPrin ? 0 : (((Math.abs(hh)%100)/50)-1)*0.8;
 const ry = isPrin ? 0 : ((((Math.abs(hh)>>8)%100)/50)-1)*0.45;
 Object.assign(P,{al:.5,ll:0,ar:.5,lr:0,lx:rx,ly:ry,tilt:rx*0.1,gi:1,r:59,g:158,b:255,sq:0,sv:0,jy:0,jv:0,sy:1,big:1,br:0,bl:0});
 try{drawChar(X.idle,1,1,1-blink,1,0,0)}finally{c=sv.c;OUT=sv.OUT;BODY=sv.BODY;Object.assign(P,sv.P);ML.x=sv.mx;ML.y=sv.my;EP[0]=sv.ep[0];EP[1]=sv.ep[1]}
 const[x0,y0,w,h]=crop=='head'?[-2,-20,164,156]:[-2,-20,164,166];
 const o2=document.createElement('canvas');o2.width=w*2;o2.height=h*2;
 o2.getContext('2d').drawImage(off,(x0+20)*2,(y0+20)*2,w*2,h*2,0,0,w*2,h*2);const u=o2.toDataURL();SNAP.set(key,u);return u}
const AVC=new Map(),AVB=new Map();
function avRender(color,outfit,gx,gy,bl,ex){
 const off=document.createElement('canvas');off.width=off.height=400;const oc=off.getContext('2d');oc.scale(2,2);oc.translate(20,20);
 const sv={c,OUT,BODY,P:{...P},mx:ML.x,my:ML.y,ep:EP.map(a=>a.slice())},s=X[ex]||X.idle;
 c=oc;OUT=outfit;BODY=color;
 Object.assign(P,{al:.5,ll:0,ar:.5,lr:0,lx:gx,ly:gy,tilt:gx*.1,gi:1,r:59,g:158,b:255,sq:0,sv:0,jy:0,jv:0,sy:1,big:1,br:0,bl:s.blush?1:0,mo:0});
 try{drawChar(s,1,1,1-bl,1,0,0)}finally{c=sv.c;OUT=sv.OUT;BODY=sv.BODY;Object.assign(P,sv.P);ML.x=sv.mx;ML.y=sv.my;EP[0]=sv.ep[0];EP[1]=sv.ep[1]}
 return off}
function avBox(outfit,color){if(AVB.has(outfit))return AVB.get(outfit);
 const d=avRender(color,outfit,0,0,0,'idle').getContext('2d').getImageData(0,0,400,400).data;let x0=400,y0=400,x1=-1,y1=-1;
 for(let y=0;y<400;y++)for(let x=0;x<400;x++)if(d[(y*400+x)*4+3]>215){if(x<x0)x0=x;if(x>x1)x1=x;if(y<y0)y0=y;if(y>y1)y1=y}
 const b=x1<x0?{x:40,y:40,w:320,h:320}:{x:x0,y:y0,w:x1-x0+1,h:y1-y0+1};AVB.set(outfit,b);return b}
function avFrame(color,outfit,crop,gx,gy,bl,ex,peek){
 const key=[color,outfit,gx,gy,bl,ex].join('|'),hit=AVC.get(key);if(hit||peek)return hit||null;
 const b=avBox(outfit,color),off=avRender(color,outfit,gx,gy,bl,ex),sc=Math.min(66/b.w,66/b.h),mg=9/sc,W=b.w*sc+18,H=b.h*sc+18,
  o=document.createElement('canvas');o.width=o.height=84;const x=o.getContext('2d');x.imageSmoothingQuality='high';
 x.drawImage(off,b.x-mg,b.y-mg,b.w+2*mg,b.h+2*mg,(84-W)/2,(84-H)/2,W,H);
 x.globalCompositeOperation='destination-in';const g=x.createRadialGradient(42,42,33,42,42,43);g.addColorStop(0,'#000');g.addColorStop(1,'rgba(0,0,0,0)');x.fillStyle=g;x.fillRect(0,0,84,84);
 if(AVC.size>500)AVC.delete(AVC.keys().next().value);AVC.set(key,o);return o}
function avt(col,out,i=0,act=0,crop='full',mode=''){return `<span class="apw ${crop}${act?' act':''}" data-av="${col}|${out}|${crop}|${i}|${mode}"><canvas class="apimg" width="84" height="84"></canvas></span>`}

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
function init(el){const[col,out,crop,seed,mode]=el.dataset.av.split('|'),cv=el.firstElementChild,n=performance.now(),host=el.closest('button')||el;
 const isWork=(mode=='working');
 const s={el,cv,x:cv.getContext('2d'),col,out,crop,lite:mode=='lite',isWork,ph:(+seed||0)*1.9+Math.random()*6.28,gx:0,gy:0,tgx:0,tgy:0,gt:0,ex:isWork?'working':'idle',exUntil:0,
  nl:n+R(500,2500),nb:n+R(700,3800),bs:-1,dbl:0,nh:n+R(2500,7000),nw:n+R(9000,22000),y:0,vy:0,r:0,vr:0,sx:0,key:''};
 host.addEventListener('pointerenter',()=>react(s,'happy',950,-85));
 host.addEventListener('pointerdown',()=>react(s,'happy',800,-120));
 S.set(el,s);return s}
function tick(now){
 const dt=Math.min(.05,Math.max(.001,(now-last)/1000));last=now;if(document.hidden)return;
 let bud=3;
 for(const el of document.querySelectorAll('.apw[data-av]')){
  const s=S.get(el)||init(el),r=el.getBoundingClientRect();if(!r.width)continue;
  const dx=px-(r.left+r.width/2),dy=py-(r.top+r.height/2),near=Math.hypot(dx,dy)<200&&now-pt<3500;
  if(!s.lite&&!RM){
   if(near){s.tgx=cl(Math.round(dx/36),-2,2);s.tgy=cl(Math.round(dy/28),-1,1);s.nl=now+700}
   else if(now>s.nl){s.tgx=Math.random()<.35?0:Math.round(R(-2,2));s.tgy=Math.random()<.65?0:Math.round(R(-1,1));s.nl=now+R(1100,4200)}
   if(now-s.gt>65){s.gt=now;s.gx+=Math.sign(s.tgx-s.gx);s.gy+=Math.sign(s.tgy-s.gy)}
  }
  if(s.bs<0&&now>s.nb){s.bs=now;s.nb=now+R(1800,5400);s.dbl=Math.random()<.2}
  let lv=0;if(s.bs>=0){const a=now-s.bs;lv=Math.max(bk(a),s.dbl?bk(a-300):0);if(a>560)s.bs=-1}
  if(s.isWork){s.ex='working';s.exUntil=now+5000}
  else if(s.ex!='idle'&&now>s.exUntil)s.ex='idle';
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
let loopRaf = null;
function tickLoop(now){
  if(window.__miku_paused || window.__miku_hidden){ loopRaf = null; return; }
  loopRaf = requestAnimationFrame(tickLoop);
  tick(now);
}
loopRaf = requestAnimationFrame(tickLoop);
return{react}})(avFrame);
function applyTheme(){const a=curAg(),r=document.documentElement.style,pr=a===PRIN;
 r.setProperty('--ac',a.c);r.setProperty('--acx',lum(a.c)>.6?'#111':'#fff');r.setProperty('--sky',pr?'#dfe3ec':mix(a.c,.4));
 r.setProperty('--gl',pr?'rgba(255,255,255,.1)':`color-mix(in srgb,${a.c} 26%,transparent)`);
 BODY=bodyOf(a);OUT=a.outfit||'none';bl=pr?'#5aaeff':mix(a.c,.35);emit({k:'theme',c:a.c})}
function set(n){cur=n;ct=t;const s=X[n]||X.idle;const glowStates=['listening','thinking','talking','searching','working','swallow','error','love','proud','annoyed'];const shouldGlow=glowStates.includes(n)||!!s.g||(s.gi&&s.gi>1.2)||!!THK.on;isl.classList.toggle('vz',shouldGlow);let glowCol=s.g;if(!glowCol){if(n=='searching')glowCol=[130,200,255];else if(n=='working')glowCol=[255,175,75];else if(curAg()&&curAg().c){const hx=curAg().c.replace('#','');glowCol=[parseInt(hx.slice(0,2),16),parseInt(hx.slice(2,4),16),parseInt(hx.slice(4,6),16)]}else{glowCol=BL}}isl.style.setProperty('--vc',`rgb(${glowCol.join(',')})`);if(s.jump)P.jv=-150;if(s.squash){P.sq=.34;P.sv=0}if(n=='dizzy'||n=='error')P.sv=-1;label()}
const LBL={idle:'Lista',listening:'Escuchando…',thinking:'Pensando…',talking:'Hablando',searching:'Buscando…',working:'Trabajando',sleeping:'Zzz…',swallow:'Recibiendo'};
function label(){const m=$('.mini');if(m&&scene=='compact'){m.innerHTML=MINIH();inn.style.width=inn.style.minWidth=inn.style.maxWidth=cW()+'px'}$('#bmic')?.classList.toggle('on',base=='listening'||!!ST.mic)}
const LOCK={until:0,prio:0},HARD={error:3,dizzy:3,surprised:2,love:2,wave:2,proud:2,happy:2};
window.buddy={
 setState(n){if(!X[n]||(LOCKI&&n!='idle'))return;base=n;tlTrack(n);set(n);poke()},
 emote(n,ms=1800,prio=1){if(!X[n]||(LOCKI&&prio<9))return;if(n=='look'||n.startsWith('look_'))return this.look(n.split('_')[1]||'left',ms);
  const now=Date.now();if(now<LOCK.until&&prio<LOCK.prio)return;
  LOCK.until=now+ms;LOCK.prio=Math.max(prio||1,HARD[n]||0);set(n);clearTimeout(emT);emT=setTimeout(()=>set(base),ms)},
 look(d='left',ms=1800){ov={up:[0,-1],down:[0,1],left:[-1,0],right:[1,0]}[d]||[0,0];set('look');clearTimeout(emT);emT=setTimeout(()=>set(base),ms)}
};
function poke(){idleT=Date.now()}
function wake(){if(base=='sleeping'){lastExp=0;base='idle';buddy.emote('surprised',900)}poke()}
setInterval(()=>{if(Date.now()-idleT>20000&&base!='sleeping'&&scene=='compact')buddy.setState('sleeping')},1000);
// Test animación: Miku señalando el botón de actualización en la isla compacta
setInterval(()=>{if(scene=='compact'&&base=='idle'&&Date.now()-idleT>2800&&Math.random()<0.55){buddy.emote('point_upd',2600)}},7500);

const ic=n=>`<svg class="i"><use href="#i-${n}"/></svg>`;
const esc=s=>String(s??'').replace(/[&<>]/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[m]));
let HAS_UPD=0;
const IB=(n,a,t)=>`<button class="ib" data-a="${a}" title="${t}" aria-label="${t}">${ic(n)}</button>`;
const B=(l,a,c='',i='',t='')=>`<button class="${c}" data-a="${a}" ${t?`title="${t}" aria-label="${t}"`:''}>${i?ic(i):''}${l}</button>`;
const I18N_ISLAND = {
  es: {
    tab_home: 'Inicio',
    tab_chat: 'Preguntar',
    tab_files: 'Subir archivos',
    boot_eyebrow: 'MIKU CORE',
    beta_tag: 'BETA v0.2.0',
    boot_title: 'Iniciando el servidor...',
    boot_step_0: 'Iniciando servicios',
    boot_step_1: 'Preparando recursos',
    boot_step_2: 'Conectando WebSocket',
    boot_connected: 'Core conectado',
    boot_beta_note: 'Software en desarrollo activo',
    report_issue: 'Reportar errores',
    orchestrator: 'Orquestador',
    subagent: 'Sub-agente',
    active_status: 'Activo',
    ready_status: 'Listo',
    memory_active: 'Memoria: 100% activa',
    agents_avail_prefix: 'Agentes',
    agents_avail: 'disponibles',
    system_status: 'Sistema',
    core_synced: 'Core 8000 sincronizado',
    local_mode: 'Modo local',
    model_label: 'Modelo',
    role_label: 'Rol',
    status_label: 'Estado',
    thinking: 'Pensando respuesta...',
    done_task: 'Última tarea completada',
    idle_task: 'En espera de órdenes',
    chat_placeholder: 'Escribe tu mensaje o pide una acción...',
    quick_settings: 'Ajustes rápidos',
    sound: 'Sonido'
  },
  en: {
    tab_home: 'Home',
    tab_chat: 'Chat',
    tab_files: 'Upload files',
    boot_eyebrow: 'MIKU CORE',
    beta_tag: 'BETA v0.2.0',
    boot_title: 'Starting server...',
    boot_step_0: 'Starting services',
    boot_step_1: 'Preparing resources',
    boot_step_2: 'Connecting WebSocket',
    boot_connected: 'Core connected',
    boot_beta_note: 'Software in active development',
    report_issue: 'Report errors',
    orchestrator: 'Orchestrator',
    subagent: 'Sub-agent',
    active_status: 'Active',
    ready_status: 'Ready',
    memory_active: 'Memory: 100% active',
    agents_avail_prefix: 'Agents',
    agents_avail: 'available',
    system_status: 'System',
    core_synced: 'Core 8000 synced',
    local_mode: 'Local mode',
    model_label: 'Model',
    role_label: 'Role',
    status_label: 'Status',
    thinking: 'Thinking response...',
    done_task: 'Last task completed',
    idle_task: 'Waiting for orders',
    chat_placeholder: 'Type your message or ask an action...',
    quick_settings: 'Quick Settings',
    sound: 'Sound'
  },
  ko: {
    tab_home: '홈',
    tab_chat: '채팅',
    tab_files: '파일 업로드',
    boot_eyebrow: 'MIKU CORE',
    beta_tag: 'BETA v0.2.0',
    boot_title: '서버 시작 중...',
    boot_step_0: '서비스 시작',
    boot_step_1: '리소스 준비',
    boot_step_2: '웹소켓 연결 중',
    boot_connected: '코어 연결됨',
    boot_beta_note: '개발 진행 중인 소프트웨어',
    report_issue: '오류 신고',
    orchestrator: '오케스트레이터',
    subagent: '하위 에이전트',
    active_status: '활성',
    ready_status: '준비 완료',
    memory_active: '메모리: 100% 활성',
    agents_avail_prefix: '에이전트',
    agents_avail: '사용 가능',
    system_status: '시스템',
    core_synced: 'Core 8000 동기화됨',
    local_mode: '로컬 모드',
    model_label: '모델',
    role_label: '역할',
    status_label: '상태',
    thinking: '생각 중...',
    done_task: '마지막 작업 완료',
    idle_task: '명령 대기 중',
    chat_placeholder: '메시지를 입력하거나 작업을 요청하세요...',
    quick_settings: '빠른 설정',
    sound: '소리'
  }
};
const tr = k => {
  const lang = (typeof CFG !== 'undefined' && CFG.lang) ? CFG.lang : 'es';
  return (I18N_ISLAND[lang] && I18N_ISLAND[lang][k]) || (I18N_ISLAND.es && I18N_ISLAND.es[k]) || k;
};
function updateIslandLang() {
  TABS[0][2] = tr('tab_home');
  TABS[1][2] = tr('tab_chat');
  TABS[2][2] = tr('tab_files');
  if (typeof scene !== 'undefined') {
    if (scene === 'overview' && typeof renderOv === 'function') {
      renderOv();
    } else if ((scene === 'prompt' || scene === 'result' || scene === 'boot') && typeof go === 'function') {
      go(scene);
    }
  }
}
const TABS=[['overview','home',tr('tab_home')],['prompt','chat',tr('tab_chat')],['drop','plus',tr('tab_files')]];
const HD=(tx,x='')=>`<div class="hd"><span class="tabs">${TABS.map(([g,i,l])=>`<button class="ib tb ${scene==g?'on':''}" data-a="go:${g}" title="${l}" aria-label="${l}">${ic(i)}</button>`).join('')}</span><span class="r">${x}${(typeof HAS_UPD!=='undefined'&&HAS_UPD)?`<button class="ib upd" data-a="island_update" title="Nueva actualización disponible">${ic('spark')}<span class="upd-dot"></span></button>`:''}<button class="ib ph ${scene=='link'?'on':''} ${ST.link?'live':''}" data-a="go:link" title="Miku-Link" aria-label="Miku-Link">${ic('phone')}</button><button class="ib ${scene=='settings'?'on':''}" data-a="go:settings" title="${tr('quick_settings')}" aria-label="${tr('quick_settings')}">${ic('cog')}</button><button class="ib spk" data-a="mute" title="${tr('sound')}" aria-label="${tr('sound')}">${ic(CFG.voice?'speaker':'speaker-off')}</button>${(scene==='boot'||scene==='intro')?'':`<button class="ib cls" data-a="island_hide" title="Minimizar Isla" aria-label="Minimizar">${ic('x')}</button>`}</span></div>`;
const MN=()=>{const n=Math.min(ST.tasks||0,4);return n?`<div class="minis">${[['#4FD3B1','#ff6b5e'],['#F0B94F','#2dd4a0'],['#A995EF','#22C5E8'],['#6CB2F5','#ffb020']].slice(0,n).map(([c,d])=>`<i class="mi" style="--c:${c};--d:${d}"></i>`).join('')}</div>`:''};
function wrapRow(h,s){const m=h.match(/^(<div class="hd">.*?<\/span><\/div>)([\s\S]*)$/),hd=m?m[1]:'',b=m?m[2]:h,g=(X[s.st]||X.idle).g||BL;
 return hd+`<div class="row"><div class="card mk" style="--g:var(--gl)"><i class="cs" data-k=".6" style="width:67px;height:50px"></i><div class="cp">${b}</div></div></div>`}
const BDG=()=>`<i class="dot ${ST.ws?'on':''}" id="bws" title="WebSocket"></i><i class="dot t ${ST.mic?'on':''}" id="bmic" title="Micrófono"></i>${ST.link?`<span class="lk" title="${esc(ST.name)}">${ic('phone')}</span>`:''}`;

const MG={
think:`<svg class="mg" viewBox="0 0 26 18"><path d="M7 15a4.2 4.2 0 0 1-.4-8.4A5.4 5.4 0 0 1 16.6 4 4.6 4.6 0 0 1 21 15z" fill="#eaf3ff"/><g fill="var(--c)"><circle class="d" cx="8.5" cy="10.5" r="1.6"/><circle class="d" style="animation-delay:.15s" cx="13.5" cy="10.5" r="1.6"/><circle class="d" style="animation-delay:.3s" cx="18.5" cy="10.5" r="1.6"/></g></svg>`,
search:`<svg class="mg sw" viewBox="0 0 20 20"><circle cx="8" cy="8" r="5.6" fill="rgba(130,200,255,.25)" stroke="#dbeaff" stroke-width="2.2"/><path d="M12.4 12.4 18 18" stroke="#6f9fe0" stroke-width="3" stroke-linecap="round"/><path d="M5 6.5a3.4 3.4 0 0 1 2.6-2" stroke="#fff" stroke-width="1.3" fill="none" stroke-linecap="round"/></svg>`,
work:`<svg class="mg cg" viewBox="0 0 20 20"><circle cx="10" cy="10" r="6.4" fill="none" stroke="var(--c)" stroke-width="3.4" stroke-dasharray="2.513 2.513"/><circle cx="10" cy="10" r="5" fill="none" stroke="#dbeaff" stroke-width="2"/></svg>`,
zz:`<svg class="mg" viewBox="0 0 22 18"><g fill="none" stroke="#9fc4f2" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path class="z1" d="M3 9h5l-5 6h5"/><path class="z2" d="M12 2h6l-6 7h6"/></g></svg>`,
err:`<svg class="mg" viewBox="0 0 16 16"><circle cx="8" cy="8" r="7" fill="#ee4d4d"/><path d="M5.2 5.2l5.6 5.6M10.8 5.2l-5.6 5.6" stroke="#fff" stroke-width="1.8" stroke-linecap="round"/></svg>`};

/* ── agentes en la isla (máx. 3) ── */
const normIsl=l=>{if(l.length&&!l.some(a=>a.isl!=null))l.forEach((a,i)=>a.isl=i<3?i+1:0);return l};
const ISLN=()=>normIsl(ST.agents).map((a,i)=>[a,i]).filter(([a])=>a.isl>0).sort((x,y)=>x[0].isl-y[0].isl).slice(0,3).map(x=>x[1]);
const hexd=(a,b)=>{const x=parseInt(a.slice(1),16),y=parseInt(b.slice(1),16);return Math.hypot((x>>16)-(y>>16),((x>>8)&255)-((y>>8)&255),(x&255)-(y&255))};
const usedBy=(h,a)=>ST.agents.some(x=>x!==a&&hexd(x.c,h)<44);
const AB3=()=>{const A=ST.agents,l=ISLN();return l.length?`<span class="ab3">${l.map(i=>`<i class="mi" title="${esc(A[i].name)}" style="--c:${A[i].c};--d:${A[i].active?'#2dd4a0':'#ff6b5e'}"></i>`).join('')}</span>`:''};
/* ── asterisco térmico: la forma «Asterisk» del HeatWord, para cuando suena música ── */
const NEON=[[0,[255,150,225]],[.1,[255,90,190]],[.2,[255,50,60]],[.32,[255,150,40]],[.42,[255,228,100]],[.54,[120,215,255]],[.68,[40,120,245]],[.84,[12,44,150]],[1,[6,18,80]]];
const STAR_LUT=(()=>{const t=new Uint8ClampedArray(1024),F=34,cl=(v,a,b)=>Math.min(b,Math.max(a,v));for(let i=0;i<256;i++){if(i<F)continue;const u=(i-F)/(255-F);let k=0;while(k<NEON.length-2&&u>NEON[k+1][0])k++;const[u0,c0]=NEON[k],[u1,c1]=NEON[k+1],f=cl((u-u0)/(u1-u0),0,1);for(let q=0;q<3;q++)t[i*4+q]=c0[q]+(c1[q]-c0[q])*f;t[i*4+3]=255*cl((i-F)/26,0,1)}return t})();
const STARH='<canvas class="star" width="72" height="72" title="Música"></canvas>';
function drawStar(cv,now){
 const w=cv.width,h=cv.height,t=now/1000,f=cv._f||(cv._f=document.createElement('canvas')),k=cv._w||(cv._w=document.createElement('canvas'));
 if(f.width!=w){f.width=k.width=w;f.height=k.height=h}
 const g=f.getContext('2d'),off=w*3;
 g.setTransform(1,0,0,1,0,0);g.shadowColor='transparent';g.fillStyle='#000';g.fillRect(0,0,w,h);
 g.shadowColor='#fff';g.shadowBlur=w*.085;g.shadowOffsetX=off;g.strokeStyle='#fff';g.lineCap='round';g.lineWidth=w*.1;
 g.save();g.translate(-off,0);
 const turn=t*.5,L=w*.34*(1+.05*Math.sin(t*5));
 for(let r=0;r<2;r++)for(let i=0;i<3;i++){const a=turn+i/3*Math.PI,cc=Math.cos(a)*L,ss=Math.sin(a)*L;g.beginPath();g.moveTo(w/2-cc,h/2-ss);g.lineTo(w/2+cc,h/2+ss);g.stroke()}
 g.restore();
 const q=k.getContext('2d',{willReadFrequently:true});
 q.globalCompositeOperation='source-over';q.fillStyle='#000';q.fillRect(0,0,w,h);q.drawImage(f,0,0);
 const hv=now-(cv._hv||-1e9)<500,hx=hv?cv._hx*w:w/2+Math.cos(t*1.7)*w*.16,hy=hv?cv._hy*h:h/2+Math.sin(t*1.3)*w*.16,rad=w*.5,amt=.62;
 q.globalCompositeOperation='multiply';const cg=q.createRadialGradient(hx,hy,0,hx,hy,rad),v=x=>Math.round(255*(1-amt*x));
 cg.addColorStop(0,`rgb(${v(1)},${v(1)},${v(1)})`);cg.addColorStop(.45,`rgb(${v(.6)},${v(.6)},${v(.6)})`);cg.addColorStop(1,'rgb(255,255,255)');q.fillStyle=cg;q.fillRect(0,0,w,h);
 const src=q.getImageData(0,0,w,h).data,cx=cv.getContext('2d'),out=cx.createImageData(w,h),d=out.data;
 for(let i=0;i<src.length;i+=4){const o=src[i]*4;d[i]=STAR_LUT[o];d[i+1]=STAR_LUT[o+1];d[i+2]=STAR_LUT[o+2];d[i+3]=STAR_LUT[o+3]}
 cx.putImageData(out,0,0)}
let starRaf=null;
function starLoop(now){
  if(!MUS.playing||document.hidden||window.__miku_paused||window.__miku_hidden){starRaf=null;return}
  starRaf=requestAnimationFrame(starLoop);
  for(const cv of document.querySelectorAll('canvas.star')){if(now-(cv._t||0)<33)continue;cv._t=now;drawStar(cv,now)}
}
function triggerStarLoop(){if(MUS.playing&&!starRaf&&!document.hidden&&!window.__miku_paused&&!window.__miku_hidden){starRaf=requestAnimationFrame(starLoop)}}
const MINIH=()=>{const g0=(X[cur]||X.idle).g||BL,col=`rgb(${g0.join(',')})`,b=base;let g='';
 if(b=='listening'||b=='talking')g='<span class="gl"><i></i><i></i><i></i><i></i></span>';
 else if(b=='thinking')g=tlHtml(1);else if(b=='searching')g=MG.search;else if(b=='working')g=MG.work;else if(b=='error')g=MG.err;if(!g&&THK.dur&&Date.now()-THK.end<3000)g=tlHtml(0);
 const updBadge=(typeof HAS_UPD!=='undefined'&&HAS_UPD)?`<button class="mini-upd-badge" data-a="island_update" title="¡Nueva actualización disponible!"><span class="mub-spark">${ic('spark')}</span><span>Actualizar</span></button>`:'';
 return `<span class="mn" style="--c:${col}">${g}</span>${updBadge}${MUS.playing?STARH:''}`};
const fmtTL=ms=>{const d=Math.floor(ms/100);return d<600?(d/10).toFixed(1)+'s':Math.floor(d/600)+'m '+((d%600)/10).toFixed(1)+'s'};
const tlHtml=live=>`<span class="tl ${live?'live':''}"><svg class="i"><use href="#i-spark"/></svg><span class="tl-t">${live?'Pensando…':'Pensó'}</span><span class="tl-n">${fmtTL(live?performance.now()-THK.start:THK.dur)}</span></span>`;
function tlTrack(n){if(n=='thinking'){if(!THK.on){THK.on=1;THK.start=performance.now();THK.dur=0}}else if(THK.on){THK.on=0;THK.dur=performance.now()-THK.start;THK.end=Date.now();setTimeout(label,3100)}}
setInterval(()=>{if(THK.on)$$('.tl.live .tl-n').forEach(e=>e.textContent=fmtTL(performance.now()-THK.start))},100);
const MUS={title:'Sin reproducción',artist:'—',playing:0,vol:50};
let MICS=[['default','Predeterminado']],PAIR='miku://pair?s=init&ip=127.0.0.1',PAIR_ERROR='';
let RES='',QL={title:'',text:''},FN='archivo',lastQ='',tabK='link',scene='compact',bk0='compact',lw=0,lh=0,tm,notT;
const AGENT_CHATS=(()=>{try{return JSON.parse(localStorage.getItem('miku_agent_chats')||'{}')}catch(_){return {}}})();
function getAgChat(id){const k=id||'miku';if(!AGENT_CHATS[k])AGENT_CHATS[k]={lastQ:'',lastA:'',history:[],unread:false,busy:false};return AGENT_CHATS[k];}
function saveAgChats(){try{localStorage.setItem('miku_agent_chats',JSON.stringify(AGENT_CHATS))}catch(_){}}
function getUnreadAgent(){
  for(const a of ST.agents){if(getAgChat(a.id).unread)return a}
  if(getAgChat('miku').unread && curAg().id!=='miku')return PRIN;
  return null;
}
const SUG=['Resume mi pantalla','¿Qué hay en mi portapapeles?','Busca un archivo'];
const F=(l,c)=>`<div class="f"><span>${l}</span>${c}</div>`;
const R=k=>`<input type="range" data-k="${k}" value="${CFG[k]}">`;
const T=k=>`<label class="sw"><input type="checkbox" data-k="${k}" ${CFG[k]?'checked':''}><i></i></label>`;
const S=(k,o)=>`<select data-k="${k}">${o.map(x=>`<option value="${x[0]}" ${CFG[k]==x[0]?'selected':''}>${x[1]}</option>`).join('')}</select>`;

/* ── File Attachment Helpers ── */
window.__attachedFile = null;
function getFileIconSvg(name = '') {
  const ext = (name.split('.').pop() || '').toLowerCase();
  if (['png', 'jpg', 'jpeg', 'gif', 'webp', 'svg', 'bmp'].includes(ext)) {
    return `<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="#38bdf8" stroke-width="2"><rect width="18" height="18" x="3" y="3" rx="2"/><circle cx="9" cy="9" r="2"/><path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"/></svg>`;
  }
  if (['py', 'js', 'ts', 'jsx', 'tsx', 'html', 'css', 'json', 'cpp', 'c', 'rs', 'go'].includes(ext)) {
    return `<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="#4ade80" stroke-width="2"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>`;
  }
  if (['pdf', 'doc', 'docx', 'txt', 'md', 'csv', 'xlsx'].includes(ext)) {
    return `<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="#f472b6" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>`;
  }
  if (['mp3', 'wav', 'flac', 'ogg', 'm4a'].includes(ext)) {
    return `<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="#fbbf24" stroke-width="2"><path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/></svg>`;
  }
  if (['mp4', 'mkv', 'avi', 'mov', 'webm'].includes(ext)) {
    return `<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="#a78bfa" stroke-width="2"><polygon points="23 7 16 12 23 17 23 7"/><rect width="14" height="14" x="1" y="5" rx="2" ry="2"/></svg>`;
  }
  return `<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="#94a3b8" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>`;
}
function truncName(name = '', max = 18) {
  if (name.length <= max) return esc(name);
  const parts = name.split('.');
  if (parts.length > 1) {
    const ext = parts.pop();
    const base = parts.join('.');
    return esc(base.slice(0, Math.max(4, max - ext.length - 4)) + '...' + ext);
  }
  return esc(name.slice(0, max - 3) + '...');
}
function renderChatAttachmentPill() {
  const f = window.__attachedFile;
  if (!f) return '';
  const sz = f.size ? `${(f.size / 1024).toFixed(0)} KB` : '';
  return `
    <div class="chat-attached-pill" id="chatAttachedPill">
      <span class="caf-icon">${getFileIconSvg(f.name)}</span>
      <span class="caf-name" title="${esc(f.name)}">${truncName(f.name, 20)}</span>
      ${sz ? `<span class="caf-size">${sz}</span>` : ''}
      <button type="button" class="caf-send" data-a="send-attached-phone" title="Enviar archivo al celular" aria-label="Enviar archivo al celular">
        <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><rect x="7" y="2" width="10" height="20" rx="2"/><path d="M12 7v7m-3-3 3 3 3-3"/></svg>
      </button>
      <button type="button" class="caf-remove" onclick="removeChatAttachment(event)" title="Quitar archivo">
        <svg viewBox="0 0 24 24" width="11" height="11" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M18 6L6 18M6 6l12 12"/></svg>
      </button>
    </div>
  `;
}
window.removeChatAttachment = function(e) {
  if (e) { e.preventDefault(); e.stopPropagation(); }
  window.__attachedFile = null;
  const wrap = document.getElementById('chat-attached-wrap');
  if (wrap) wrap.innerHTML = '';
};

function formatAgentMarkdown(str) {
  if (!str) return '';
  let s = esc(str);
  s = s.replace(/\*\*(.+?)\*\*/g, '<b>$1</b>');
  s = s.replace(/`([^`]+)`/g, '<code class="ag-code">$1</code>');
  const lines = s.split('\n');
  const res = [];
  for (let l of lines) {
    const t = l.trim();
    if (t.startsWith('- ') || t.startsWith('* ')) {
      res.push(`<div class="ag-bullet"><span class="ag-bullet-dot">•</span><span>${t.slice(2)}</span></div>`);
    } else {
      res.push(l);
    }
  }
  return res.join('<br>').replace(/(<\/div>)<br>/g, '$1').replace(/<br>(<div class="ag-bullet">)/g, '$1');
}

function renderSyntaxDiffBox(diffStr, fileLabel = '') {
  if (!diffStr) return '';
  const lines = String(diffStr).split('\n').slice(0, 24);
  const formatted = lines.map(raw => {
    const cls = raw.startsWith('+') ? 'add' : (raw.startsWith('-') ? 'del' : 'ctx');
    return `<div class="miku-diff-line ${cls}">${esc(raw)}</div>`;
  }).join('');
  return `
    <div class="miku-diff-box">
      ${fileLabel ? `<div style="font-size:10.5px;color:#38bdf8;margin-bottom:4px;font-weight:700">${esc(fileLabel)}</div>` : ''}
      ${formatted}
    </div>
  `;
}

window.__liveThought = window.__liveThought || null;

const renderChatCard = () => {
  const a = curAg();
  const ch = getAgChat(a.id);
  const longContent = (ch.lastQ?.length || 0) > 280 || (ch.lastA?.length || 0) > 600;
  
  // Miku siempre como Orquestador principal, más los agentes seleccionados en la isla
  const islandAgentIds = ISLN().map(i => ST.agents[i]?.id).filter(Boolean);
  const selectedAgents = ST.agents.filter(x => x.id !== PRIN.id && islandAgentIds.includes(x.id));
  
  const headerHtml = `
    <div class="hd chat-hd">
      <span class="tabs">${TABS.map(([g,i,l])=>`<button class="ib tb ${scene==g?'on':''}" data-a="go:${g}" title="${l}" aria-label="${l}">${ic(i)}</button>`).join('')}</span>
      <div class="ag-chat-pill-wrap" style="position:relative;margin-left:6px">
        <button class="ag-chat-pill" id="agChatPill" type="button" title="Cambiar de agente">
          <i class="ag-chat-dot" style="background:${a.c || '#ffffff'};color:${a.c || '#ffffff'}"></i>
          <span class="ag-chat-name">${esc(a.name)}</span>
          <svg class="ag-chat-chev" viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M6 9l6 6 6-6"/></svg>
        </button>
        <div class="ag-chat-dropdown" id="agChatDropdown" style="display:none">
          <div class="ag-dd-title">Hablar con un agente:</div>
          <!-- 1. Miku siempre como Orquestador -->
          <button type="button" class="ag-dd-item ${a.id === PRIN.id ? 'active' : ''}" data-switch-ag="${esc(PRIN.id)}">
            <i class="ag-chat-dot" style="background:#ffffff;box-shadow:0 0 8px #ffffff"></i>
            <span class="ag-dd-name">Miku</span>
            ${a.id === PRIN.id ? '<span class="ag-dd-badge">Actual</span>' : ''}
            ${getAgChat(PRIN.id).unread ? '<span class="ag-dd-dot-unread" title="Nueva respuesta"></span>' : ''}
          </button>
          <div class="ag-dd-sep"></div>
          <!-- 2. Agentes de la Isla -->
          ${selectedAgents.map(g => `
            <button type="button" class="ag-dd-item ${g.id === a.id ? 'active' : ''}" data-switch-ag="${esc(g.id)}">
              <i class="ag-chat-dot" style="background:${g.c};color:${g.c}"></i>
              <span class="ag-dd-name">${esc(g.name)}</span>
              ${g.id === a.id ? '<span class="ag-dd-badge">Actual</span>' : ''}
              ${getAgChat(g.id).unread ? '<span class="ag-dd-dot-unread" title="Nueva respuesta"></span>' : ''}
            </button>
          `).join('')}
          <div class="ag-dd-sep"></div>
          <button type="button" class="ag-dd-item manage" data-a="cfgwin">
            <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12h14"/></svg>
            <span>Gestionar agentes en Ajustes...</span>
          </button>
        </div>
      </div>
      <div class="r">
        <button class="ib ${scene=='settings'?'on':''}" data-a="go:settings" title="Ajustes">${ic('cog')}</button>
        <button class="ib spk" data-a="mute" title="Sonido">${ic(CFG.voice?'speaker':'speaker-off')}</button>
        <button class="ib cls" data-a="island_hide" title="Minimizar Isla" aria-label="Minimizar">${ic('x')}</button>
      </div>
    </div>
  `;

  const agentColor = (a.id === PRIN.id || a === PRIN) ? '#ffffff' : (a.c || '#ffffff');
  const chatAgentPresence = `
    <div class="chat-mascot-side">
      <i class="cs" data-k=".75" style="width:66px;height:54px;cursor:pointer" data-a="agent-mascot-click" role="img" aria-label="${esc(a.name)}" title="${getUnreadAgent() ? 'Ver agente con notificación' : esc(a.name)}"></i>
      <span class="chat-agent-name">${esc(a.name)}</span>
    </div>
  `;

  const userBubbleHtml = ch.lastQ ? `
    <div class="msg-user-wrap">
      <div class="msg-user-bubble" style="--pc:${agentColor}">
        ${ch.lastFile ? `
          <div class="chat-bubble-file">
            ${getFileIconSvg(ch.lastFile.name)}
            <span class="cbf-name" title="${esc(ch.lastFile.name)}">${truncName(ch.lastFile.name, 22)}</span>
            ${ch.lastFile.size ? `<span class="cbf-size">${(ch.lastFile.size / 1024).toFixed(0)} KB</span>` : ''}
          </div>
        ` : ''}
        <div class="msg-user-text" style="font-size:13.5px;line-height:1.45;color:#ffffff">${esc(ch.lastQ)}</div>
      </div>
    </div>
  ` : '';

  const thinkingHtml = (ch.busy || ch.thinkDur > 0) ? `
    <details class="agent-thinking-box" ${ch.busy ? 'open' : ''}>
      <summary class="atb-summary">
        <span class="atb-label">
          <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
          <span>${ch.busy ? 'Pensando respuesta...' : (ch.thinkDur ? `Pensó durante ${ch.thinkDur < 60 ? ch.thinkDur + 's' : Math.floor(ch.thinkDur/60) + 'm ' + (ch.thinkDur%60) + 's'}` : 'Razonamiento completado')}</span>
        </span>
        <svg class="atb-chev" viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M6 9l6 6 6-6"/></svg>
      </summary>
      <div class="atb-content">
        ${ch.busy ? 'Analizando contexto, herramientas disponibles y deduciendo la mejor respuesta...' : 'Línea de pensamiento completada.'}
      </div>
    </details>
  ` : '';

  const toolsHtml = (ch.steps && ch.steps.length > 0) ? `
    <details class="agent-tools-box" open>
      <summary class="atb-summary">
        <span class="atb-label">
          <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><polyline points="4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/></svg>
          <span>Ejecutó ${ch.steps.length} ${ch.steps.length === 1 ? 'acción' : 'acciones / comandos'}</span>
        </span>
        <svg class="atb-chev" viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M6 9l6 6 6-6"/></svg>
      </summary>
      <div class="agent-steps-list">
        ${ch.steps.map((st, idx) => {
          if (st.step_type === 'screenshot') {
            const src = st.thumbnail ? (st.thumbnail.startsWith('data:') ? st.thumbnail : 'data:image/jpeg;base64,' + st.thumbnail) : '';
            const full = st.full_image ? (st.full_image.startsWith('data:') ? st.full_image : 'data:image/png;base64,' + st.full_image) : src;
            return `
              <div class="step-item step-shot">
                <div class="step-meta">
                  <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="#38bdf8" stroke-width="2"><rect width="18" height="18" x="3" y="3" rx="2"/><circle cx="9" cy="9" r="2"/><path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"/></svg>
                  <span>${esc(st.title || `Captura #${idx + 1}`)}</span>
                </div>
                ${src ? `
                  <div class="step-thumb-wrap" onclick="window.zoomImage('${full}')" title="Clic para ampliar captura">
                    <img src="${src}" class="step-thumb-img" alt="Captura ${idx + 1}">
                    <span class="step-zoom-icon">[Ampliar]</span>
                  </div>
                ` : ''}
              </div>
            `;
          } else {
            return `
              <div class="step-item step-cmd">
                <div class="step-meta">
                  <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="#4ade80" stroke-width="2"><polyline points="4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/></svg>
                  <span>${esc(st.title || 'Ejecutó un comando')}</span>
                </div>
                ${st.command ? `<code class="step-cmd-code">${esc(st.command)}</code>` : ''}
              </div>
            `;
          }
        }).join('')}
      </div>
    </details>
  ` : '';

  const liveThoughtHtml = window.__liveThought && window.__liveThought.step ? `
    <div class="thought-stream-bar" id="thoughtStreamBar">
      <i class="thought-stream-dot"></i>
      <span class="thought-stream-text">${esc(window.__liveThought.step)}</span>
      ${window.__liveThought.file ? `<code class="ag-code">${esc(window.__liveThought.file)}</code>` : ''}
    </div>
    ${window.__liveThought.diff ? renderSyntaxDiffBox(window.__liveThought.diff, window.__liveThought.file) : ''}
  ` : '';

  const agentMessageHtml = `
    <div class="msg-agent-col">
      ${liveThoughtHtml}
      ${thinkingHtml}
      ${toolsHtml}
      ${ch.busy ? `
        <div class="msg-agent-bubble" style="--pc:${agentColor};width:auto;display:inline-block;padding:8px 16px;">
          <div class="chat-typing-dots">
            <span></span><span></span><span></span>
          </div>
        </div>
      ` : (ch.lastA ? `
        <div class="msg-agent-bubble" style="--pc:${agentColor}">
          <div class="msg-agent-meta">
            <span class="msg-agent-badge" style="color:${agentColor}"><i class="msg-agent-badge-dot" style="background:${agentColor};box-shadow:0 0 6px ${agentColor}"></i>${esc(a.name)}</span>
            <span class="msg-agent-time">ahora</span>
          </div>
          <div class="msg-agent-inbox scr">
            <div class="msg-agent-text">${formatAgentMarkdown(ch.lastA)}</div>
          </div>
        </div>
      ` : `
        <div class="msg-agent-bubble welcome" style="--pc:${agentColor}">
          <div class="msg-agent-text welcome">Hola, soy <b>${esc(a.name)}</b>. ¿Qué tarea necesitas que realice?</div>
        </div>
      `)}
    </div>
  `;

  const bottomInputHtml = `
    <div id="chat-attached-wrap" style="width:100%;display:flex;padding-left:4px">${renderChatAttachmentPill()}</div>
    <div class="fld chat-fld" style="margin-top:6px;position:relative">
      <div class="crt-stage" id="crtStage">
        <button class="crt-pill" id="crtPill" type="button" aria-expanded="false" title="Acciones">
          <svg class="crt-glyph" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="M12 5v14M5 12h14"/></svg>
        </button>
        <div class="crt-panel" id="crtPanel">
          <ul class="crt-menu">
            <li class="crt-item">
              <button type="button" data-crt="file">
                <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                <span>Adjuntar archivo</span>
              </button>
            </li>
            <li class="crt-item">
              <button type="button" data-crt="vision">
                <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2"><rect width="18" height="18" x="3" y="3" rx="2"/><circle cx="9" cy="9" r="2"/><path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"/></svg>
                <span>Analizar pantalla</span>
              </button>
            </li>
            <li class="crt-item">
              <button type="button" data-crt="clip">
                <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2"><rect width="8" height="4" x="8" y="2" rx="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/></svg>
                <span>Pegar portapapeles</span>
              </button>
            </li>
            <li class="crt-item">
              <button type="button" data-crt="agents">
                <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2"><rect width="18" height="18" x="3" y="3" rx="4"/><path d="M9 10h.01M15 10h.01M9.5 15a3.5 3.5 0 0 0 5 0"/></svg>
                <span>Agentes y herramientas</span>
              </button>
            </li>
          </ul>
        </div>
      </div>
      <input id="q" placeholder="Escribe un mensaje o '/' para comandos..." autocomplete="off">
      <div id="cmdPalettePop" class="cmd-palette-pop" style="display:none"></div>
      <button class="rb-send" data-a="send" title="Enviar" aria-label="Enviar">
        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M12 19V5M5 12l7-7 7 7"/></svg>
      </button>
    </div>
  `;

  return `
    ${headerHtml}
    <div class="row">
      <div class="card mk chat-card ${longContent ? 'long-content' : ''}" style="--pc:${a.c || '#ffffff'};box-shadow:0 0 28px color-mix(in srgb,${a.c || '#ffffff'} 18%,transparent);border-color:color-mix(in srgb,${a.c || '#ffffff'} 32%,rgba(255,255,255,0.12));">
        ${chatAgentPresence}
        <div class="chat-main-side">
          <div class="chat-convo-body">
            ${userBubbleHtml}
            ${agentMessageHtml}
          </div>
          ${bottomInputHtml}
        </div>
      </div>
    </div>
  `;
};

const SC={
 compact:{m:1,st:'idle',x:()=>`<div class="mini">${MINIH()}</div>`},
 boot:{w:500,hc:1,st:'idle',x:()=>`<div class="boot-scene"><div style="display:flex;align-items:center;justify-content:center;width:104px;height:95px;flex:none"><i class="cs" data-k="1.0" style="width:104px;height:95px"></i></div><div class="boot-copy"><div class="boot-header-row"><span class="boot-eyebrow">${tr('boot_eyebrow')}</span><span class="boot-beta-badge" title="Fase Beta pública activa">${tr('beta_tag')}</span></div><strong class="boot-title" id="bootStatus">${tr('boot_title')}</strong><div class="boot-steps"><div class="boot-step" data-boot-step="0"><i class="boot-step-dot"></i>${tr('boot_step_0')}</div><div class="boot-step" data-boot-step="1"><i class="boot-step-dot"></i>${tr('boot_step_1')}</div><div class="boot-step" data-boot-step="2"><i class="boot-step-dot"></i>${tr('boot_step_2')}</div></div><div class="boot-beta-footer"><span class="boot-beta-note">${tr('boot_beta_note')}</span><button type="button" class="boot-issue-btn" onclick="window.Bridge?.openExternalUrl?.('https://github.com/cxmlo/miku/issues');event.stopPropagation();">${tr('report_issue')}</button></div></div></div>`,after:()=>{burst();P.jv=-80;P.sq=.2;setTimeout(()=>(scene=='boot'||scene=='intro')&&buddy.emote('happy',800,9),550);setTimeout(()=>(scene=='boot'||scene=='intro')&&buddy.emote('wave',1500,9),1350);startBootProgress();if(window.__mikuCoreConnected)finishBoot();}},
 prompt:{w:640,hc:1,st:'idle',after:()=>setTimeout(()=>{initLiquidMenu();$('#q')?.focus()},150),
    x:()=>renderChatCard()},
 result:{w:640,hc:1,st:'idle',em:'happy',after:()=>setTimeout(()=>{initLiquidMenu();$('#q')?.focus()},150),
    x:()=>renderChatCard()},
 intro:{w:500,hc:1,st:'idle',x:()=>SC.boot.x(),after:()=>SC.boot.after()},
 overview:{w:620,hc:1,st:'idle',after:()=>{
  const IX=ISLN();
  if(PG==1){
    PLY=mkSound($('#snh'),{get:()=>MUS,act:x=>ACT.m(x)});
    PLV=Slosh($('#vlr'),{value:MUS.vol,label:'Volumen',onChange:v=>setVol(v)});
  }
 },x:()=>{
  const A=ST.agents,a=curAg(),pr=(a.id===PRIN.id);
  const ch=getAgChat(a.id);

  const roleLabel = pr ? tr('orchestrator') : (a.role || tr('subagent'));
  const previewMetric = pr ? (ST.ws ? 'Online · 100%' : tr('active_status')) : (a.model ? a.model.replace(/^(google\/|groq\/)/i, '') : tr('ready_status'));
  const previewLines = pr ? [
    `• ${tr('memory_active')}`,
    `• ${tr('agents_avail_prefix')}: ${A.length} ${tr('agents_avail')}`,
    `• ${tr('system_status')}: ${ST.ws ? tr('core_synced') : tr('local_mode')}`
  ] : [
    `• ${tr('model_label')}: ${esc(a.model || 'Gemini Flash')}`,
    `• ${tr('role_label')}: ${esc(a.role || tr('subagent'))}`,
    `• ${tr('status_label')}: ${esc(ch.busy ? tr('thinking') : (ch.lastA ? tr('done_task') : tr('idle_task')))}`
  ];

  const agColor = (a.id === PRIN.id || a === PRIN) ? '#ffffff' : (a.c || '#ffffff');

  const leftCardHtml = `
    <div class="card hubc hz live-ag-card" data-a="go:prompt" title="Abrir chat con ${esc(a.name)}" style="--ag-card-c:${agColor};--pc:${agColor};">
      <div style="display:flex;align-items:center;justify-content:center;width:78px;flex:none">
        <i class="cs" data-k=".58" style="width:78px;height:62px;margin:0 auto"></i>
      </div>
      <div class="ov-agent-info" style="padding-left:4px">
        <div class="ov-agent-head">
          <i class="ov-agent-dot" style="background:${agColor};color:${agColor};box-shadow:0 0 8px ${agColor}"></i>
          <span class="marquee-wrap" style="flex:1"><span class="marquee-text" style="font-weight:700;font-size:13px">${esc(a.name)}</span></span>
        </div>
        <div class="ov-agent-metric marquee-wrap" style="font-size:13px;color:rgba(255,255,255,0.85);font-weight:500;margin-top:2px">
          <span class="marquee-text">${esc(previewMetric)}</span>
        </div>
      </div>
    </div>
  `;

  // Agentes en la tarjeta derecha: Miku no está fija; se excluye el agente activo de la izquierda
  const pool = [PRIN, ...ST.agents];
  const gridAgents = pool.filter(x => x.id !== a.id).slice(0, 4);
  const rightColors = gridAgents.map(g => (g.id === PRIN.id || g === PRIN) ? '#ffffff' : (g.c || '#ffffff'));
  const c1 = rightColors[0] || '#39D353';
  const c2 = rightColors[1] || rightColors[0] || '#00D2FF';
  const c3 = rightColors[2] || c1;

  const gridHtml = `
    <div class="miku-grid-2x2">
      ${gridAgents.map(g => {
        const agIdx = (g.id === PRIN.id) ? -1 : ST.agents.findIndex(x => x.id === g.id);
        const ch = getAgChat(g.id);
        const isWorking = !!ch.busy;
        const pillC = (g.id === PRIN.id) ? '#ffffff' : (g.c || '#ffffff');
        return `
          <button type="button" class="miku-ag-pill ${isWorking ? 'is-working' : ''}" data-a="agent:${agIdx}" title="${esc(g.name)}${isWorking ? ' (Trabajando en segundo plano...)' : ''}" style="border-color:color-mix(in srgb,${pillC} 35%,rgba(255,255,255,0.12));--pc:${pillC}">
            ${avt(bodyOf(g), g.outfit || 'none', agIdx < 0 ? 0 : agIdx, 0, 'head', isWorking ? 'working' : 'lite')}
            <span class="miku-ag-pill-name marquee-wrap"><span class="marquee-text">${esc(g.name)}</span></span>
          </button>
        `;
      }).join('')}
    </div>
  `;

  const musicHtml = `
    <div class="plc ovpl" style="padding:4px 8px">
      <div id="snh"></div>
      <div class="vlh thin">${ic('speaker-off')}<span id="vlr"></span>${ic('speaker')}</div>
    </div>
  `;

  const PN = 2; PG = PG % PN;
  const body = (PG == 1) ? musicHtml : gridHtml;
  const pgr = `
    <div class="pgr" style="margin-top:4px">
      <button data-a="pg:-1" title="Anterior" aria-label="Anterior"><svg class="i" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><path d="M15 6l-6 6 6 6"/></svg></button>
      <span class="pds"><i class="pd" data-a="pgto:0"></i><i class="pd" data-a="pgto:1"></i><b class="pth" style="transform:translateX(${PG*15}px)"></b></span>
      <button data-a="pg:1" title="Siguiente" aria-label="Siguiente"><svg class="i" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><path d="M9 6l6 6-6 6"/></svg></button>
    </div>
  `;

  return `${HD()}<div class="two h2">${leftCardHtml}<div class="card hubc ovp" style="--ag-c1:${c1};--ag-c2:${c2};--ag-c3:${c3};display:flex;flex-direction:column;justify-content:space-between;padding:8px 10px">${body}${pgr}</div></div>`;
 }},

 wardrobe:{hc:1,st:'idle',x:()=>{const a=curAg(),cu=a.outfit||'none',bc=bodyOf(a);
  return `${HD()}<div class="card mk wdr" style="--g:var(--gl)"><i class="cs" data-k=".8" style="width:92px;height:70px"></i><div class="cp"><div class="wh"><b>Guardarropa${a===PRIN?'':` <em>${esc(a.name)}</em>`}</b><span class="wn" id="wn">${OL[cu]||cu}</span></div>${a===PRIN?'':`<div class="crow"><span class="wn">Color</span>${PRESET.map(h=>`<button class="sw8 ${h.toLowerCase()==a.c.toLowerCase()?'on':''}" style="--c:${h}" data-a="color:${h}" aria-label="Color ${h}" ${usedBy(h,a)?'disabled title="En uso por otro agente"':''}></button>`).join('')}<label class="colorin" title="Otro color"><input type="color" id="colin" value="${a.c.toLowerCase()}"></label></div>`}<div class="wrow">${WARDROBE.map(([k,l],n)=>`<button class="wb ${cu==k?'on':''}" data-a="wear:${k}" title="${l}" aria-label="${l}">${k=='none'?ic('none'):avt(bc,k,n,0,'head','lite')}</button>`).join('')}</div></div></div>`}},
 settings:{hc:1,st:'idle',after:()=>$$('.so-host').forEach(h=>SmoothSlider(h,{value:CFG[h.dataset.k]||80,unit:'%',onChange:v=>{CFG[h.dataset.k]=v;window.Bridge?.setVolume?.(v);window.Bridge?.setSetting?.(h.dataset.k,v);}})),x:()=>{const DT=(l,on)=>`<span class="dd"><i class="sd ${on?'on':''}"></i>${l}</span>`;
  return `${HD()}<div class="card mk" style="--g:var(--gl)"><i class="cs" data-k=".7" style="width:80px;height:60px"></i><div class="cp qs"><div class="sr" style="flex-direction:column;align-items:stretch;gap:8px"><div style="display:flex;align-items:center;justify-content:space-between"><div style="display:flex;align-items:center;gap:8px"><label class="sw"><input type="checkbox" data-k="voice" ${CFG.voice?'checked':''}><i></i></label><span style="font-weight:600;font-size:13px">Sonido y voz</span></div></div><div class="so-host" data-k="voice_volume" style="width:100%"></div></div><div class="sr" style="margin-top:4px"><label class="sw"><input type="checkbox" data-k="hover_open" ${CFG.hover_open?'checked':''}><i></i></label><span>Abrir al pasar el cursor</span></div><div class="sr st2">${DT('Core 8000',ST.ws)}${DT('API',ST.api)}<button class="lk2" data-a="go:link">${DT('Miku-Link',ST.link)}</button><button class="lnk" data-a="cfgwin">Ajustes…</button></div></div></div>`}},
 link:{hc:1,st:'idle',after:()=>{drawQR(PAIR||'miku://pair?s=init&ip=127.0.0.1');window.Bridge?.syncLinkStatus?.();if(window.Bridge?.generatePairingUrl)window.Bridge.generatePairingUrl(false);},x:()=>`${HD()}<div class="lkg"><div class="card lkd"><i class="cs" data-k=".8" style="width:104px;height:78px"></i></div><div class="card lkr"><div class="lkt"><b>Vincular con el celular</b><div class="sub2">Escanea el código con la app móvil de Miku para sincronizar portapapeles, archivos y notificaciones.</div><small class="sub2" id="qu" style="margin:0"></small><span class="st ${ST.link?'on':''}">${ST.link?'Conectado: '+esc(ST.name):'Desconectado'}</span></div><canvas id="qr" width="288" height="288"></canvas></div></div><div class="card lopt"><div class="sr"><label class="sw"><input type="checkbox" data-k="local_net" ${CFG.local_net?'checked':''}><i></i></label><span class="mut">Permitir conexiones en la red local</span></div><div class="sr"><label class="sw"><input type="checkbox" data-k="biometric" ${CFG.biometric?'checked':''}><i></i></label><span class="mut">Pedir huella o bloqueo para «Permitir»</span></div></div><div class="chips">${B('Nuevo código','newcode','','retry')}${B('Abrir Miku-Link','linkcfg','p','phone')}${ST.link?B('Desvincular','unpair','','x'):''}</div>`},
 gallery:{w:520,hc:1,st:'idle',x:()=>`${HD('Animaciones',B('Reproducir todas','playall','p','spark'))}<div class="card hubc"><i class="cs" data-k=".95" style="width:107px;height:80px"></i><div class="gal">${GAL.map(k=>`<button data-a="emo:${k}">${k=='ask'?'pregunta':k=='approve'?'permiso':k.replace('_',' ')}</button>`).join('')}</div></div>`},
 tool_use:{w:440,st:'searching',
  x:a=>`${HD(esc(a.label||'Analizando pantalla'))}<div class="card"><div class="tu"><span class="badge">${esc(a.badge||'Visión')}</span><div class="scan"></div></div><div class="sub2">${esc(a.sub||'Computer Use')}</div></div><div class="chips">${B('Cancelar','cancel','','x')}</div>`},
 notify:{w:420,st:'idle',x:a=>`${HD()}<div class="nt">${a.badge?`<span class="badge" style="background:#38bdf8;color:#050811;font-weight:700;margin-bottom:4px;display:inline-block">${esc(a.badge)}</span><br>`:''}<b>${esc(a.title||'Miku')}</b><div class="sub2" style="margin-top:4px">${esc(a.text||'')}</div>${a.btns?`<div class="chips">${a.btns.map(b=>B(esc(b[0]),b[1])).join('')}</div>`:''}</div>`},
 alert:{w:420,st:'idle',x:a=>`${HD()}<div class="nt"><span class="badge" style="background:#2dd4a0;color:#050811;font-weight:700;margin-bottom:4px;display:inline-block">${esc(a.badge||'Enfoque')}</span><br><b>${esc(a.title||'Alerta de Miku')}</b><div class="sub2" style="margin-top:4px">${esc(a.text||a.message||'')}</div></div>`},
 approve:{w:500,hc:1,st:'thinking',x:a=>{
    const agName = a.agent_name || (curAg() ? curAg().name : 'Miku');
    const title = a.title || `${agName} solicita permiso`;
    const cmdText = a.text || a.cmd || a.command || 'ejecutar_comando_sistema';
    const diffHtml = a.diff ? renderSyntaxDiffBox(a.diff, a.file || '') : '';
    return `
      <div class="hd chat-hd">
        <div class="ag-chat-pill danger">
          <i class="ag-chat-dot" style="background:#ffb300;box-shadow:0 0 8px #ffb300"></i>
          <span class="ag-chat-name"><b>${esc(title)}</b></span>
        </div>
      </div>
      <div class="row">
        <div class="card mk approve-card" style="--g:radial-gradient(circle,rgba(255,179,0,0.15),transparent);padding:16px 18px 14px;min-height:120px;display:flex;align-items:center;gap:14px">
          <i class="cs" data-k=".85" style="width:78px;height:64px;flex:none"></i>
          <div style="flex:1;min-width:0;display:flex;flex-direction:column;gap:8px">
            <div class="cmd-box"><code>${esc(cmdText)}</code></div>
            ${diffHtml}
            <div class="ap-actions">
              <button class="btn-allow" data-a="apok" title="Permitir (Atajo: Y)">Permitir <kbd>Y</kbd></button>
              <button class="btn-deny" data-a="denyap" title="Denegar (Atajo: N)">Denegar <kbd>N</kbd></button>
              <button class="btn-always" data-a="apalways" title="Permitir siempre para este comando (Atajo: A)">Siempre <kbd>A</kbd></button>
            </div>
          </div>
        </div>
      </div>
    `;
  }},
 question:{w:500,hc:1,st:'thinking',x:a=>{
    const opts = Array.isArray(a.options) && a.options.length ? a.options : ['Sí, continuar', 'No, cancelar'];
    return `
      <div class="hd chat-hd">
        <div class="ag-chat-pill">
          <i class="ag-chat-dot" style="background:#38bdf8;box-shadow:0 0 8px #38bdf8"></i>
          <span class="ag-chat-name"><b>${esc(a.title || 'Pregunta de Miku')}</b></span>
        </div>
      </div>
      <div class="row">
        <div class="card mk" style="--g:radial-gradient(circle,rgba(56,189,248,0.16),transparent);padding:16px 18px;display:flex;align-items:center;gap:14px">
          <i class="cs" data-k=".82" style="width:76px;height:62px;flex:none"></i>
          <div style="flex:1;min-width:0">
            ${a.sub || a.text ? `<div class="sub2" style="margin-bottom:6px;color:#cbd5e1">${esc(a.sub || a.text)}</div>` : ''}
            <div class="question-opts-grid">
              ${opts.map((opt, idx) => `
                <button type="button" class="question-opt-btn" data-a="pick:${esc(opt)}">
                  <span>${esc(opt)}</span>
                  <kbd>${idx + 1}</kbd>
                </button>
              `).join('')}
            </div>
          </div>
        </div>
      </div>
    `;
  }},
 error_card:{w:510,hc:1,st:'error',x:a=>{
    const exitCode = a.exit_code != null ? a.exit_code : 1;
    const stderrText = a.stderr || a.text || 'Error inesperado durante la ejecución.';
    return `
      <div class="hd chat-hd">
        <div class="ag-chat-pill danger">
          <i class="ag-chat-dot" style="background:#ff5c66;box-shadow:0 0 8px #ff5c66"></i>
          <span class="ag-chat-name"><b>${esc(a.title || 'Error de Ejecución')}</b></span>
        </div>
        <span class="error-exit-badge">EXIT ${esc(String(exitCode))}</span>
      </div>
      <div class="row">
        <div class="card mk error-card-box" style="--g:radial-gradient(circle,rgba(255,92,102,0.18),transparent);padding:16px 18px;display:flex;align-items:center;gap:14px">
          <i class="cs" data-k=".82" style="width:76px;height:62px;flex:none"></i>
          <div style="flex:1;min-width:0">
            <div class="error-stderr-pre scr">${esc(stderrText)}</div>
            <div class="ap-actions">
              <button class="btn-allow" data-a="errretry:${esc(a.retry_cmd || '')}">Reintentar</button>
              <button class="btn-deny" data-a="go:prompt">Abrir Chat</button>
              <button class="btn-always" data-a="go:compact">Cerrar</button>
            </div>
          </div>
        </div>
      </div>
    `;
  }},
 player:{hc:1,st:'idle',x:()=>`${HD('Música')}<div class="plr"><i class="cs" data-k=".6" style="width:67px;height:50px;flex:none"></i><div class="plc"><div id="snh"></div><div class="vlh thin">${ic('speaker-off')}<span id="vlr"></span>${ic('speaker')}</div></div></div>`,after:()=>{PLY=mkSound($('#snh'),{get:()=>MUS,act:x=>ACT.m(x)});PLV=Slosh($('#vlr'),{value:MUS.vol,label:'Volumen',onChange:v=>setVol(v)})}},
 quicklook:{w:470,st:'idle',x:()=>`${HD('Vista previa')}<div class="card"><div class="fn">${ic('file')}${esc(QL.title)}</div><div class="ql scr">${esc(QL.text)}</div></div><div class="chips">${B('Copiar','qcopy','','copy')}${B('Hacer una pregunta','go:prompt','p','chat')}</div>`},
 drop:{w:440,st:'swallow',x:()=>`${HD()}<div class="card dz"><b>Suelta tus archivos aquí</b><div class="chips"><i>PDF</i><i>Imágenes</i><i>Código</i><i>Docs</i></div></div>`},
 uploading:{w:470,st:'working',after:()=>upload(),x:()=>`${HD()}<div class="card"><div class="l2"><span>Analizando <b>${esc(FN)}</b></span><span id="pc">0 %</span></div><div class="pg"><i id="fl"></i></div></div>`},
 choose:{w:450,st:'idle',em:'happy',x:()=>`${HD(esc(FN)+' está listo')}<div class="sub2" style="margin:0 0 4px">¿Qué quieres hacer con el archivo?</div><div class="chips">${B('Hacer una pregunta','go:prompt','p','chat')}${B('Vista previa','go:quicklook','','eye')}${B('Enviar al celular','phone2','','phone')}</div>`},
 agent_work:{w:640,hc:1,st:'working',x:a=>{
  const agObj = a.agent || {};
  const agId = agObj.id || a.agent_id || 'korus';
  const ag = ST.agents.find(x => x.id === agId) || { id: agId, name: agObj.name || 'Korus', role: agObj.role || 'Claude Code', category: agObj.category || (agObj.is_coding === false ? 'research' : 'code'), c: '#7C3AED', phases: agObj.phases };
  const category = a.category || agObj.category || ag.category || 'code';
  const phases = a.phases || agObj.phases || ag.phases || (category === 'code' ? ['Read', 'Edit', 'Bash', 'Done'] :
                               category === 'research' ? ['Search', 'Extract', 'Synthesize', 'Done'] :
                               category === 'data' ? ['Scan', 'Process', 'Write', 'Done'] :
                               ['Listen', 'Think', 'Action', 'Done']);
  const currentPhase = a.phase || agObj.current_phase || phases[1] || phases[0];
  const currentPhaseIdx = Math.max(0, phases.findIndex(p => p.toLowerCase() === String(currentPhase).toLowerCase()));
  const file = a.file || agObj.file_path || agObj.file_name || (category === 'research' ? 'docs/synthesis_report.md' : category === 'data' ? 'queries/migration_audit.sql' : category === 'general' ? 'stream/thought_log.txt' : 'src/invoice.ts');
  const lang = file.endsWith('.ts') ? 'TS' : file.endsWith('.js') ? 'JS' : file.endsWith('.py') ? 'PY' : file.endsWith('.md') ? 'MD' : file.endsWith('.sql') ? 'SQL' : 'STREAM';
  const cbBanner = a.circuit_breaker_tripped ? `
    <div class="cb-amber-banner" style="background:rgba(245,158,11,0.16);border:1px solid rgba(251,191,36,0.4);border-radius:8px;padding:6px 12px;margin-bottom:6px;display:flex;justify-content:space-between;align-items:center;font-size:11.5px;color:#fcd34d">
      <span>Proveedor principal saturado (HTTP 429). Conmutando temporalmente a respaldo (${esc(a.fallback_provider || 'Groq / DeepSeek')}).</span>
      <b style="font-family:monospace">Reintentando en ${esc(String(a.cooldown_sec || 178))}s</b>
    </div>
  ` : '';

  let rightBodyHtml = '';
  if (category === 'code') {
    rightBodyHtml = `
      <div class="alw-code-body scr">
        <div class="alw-diff-row"><span class="alw-ln">10</span><span class="alw-code-text"><span style="color:#c084fc">import</span> { Item } <span style="color:#c084fc">from</span> <span style="color:#86efac">'./types'</span></span></div>
        <div class="alw-diff-row"><span class="alw-ln">11</span><span class="alw-code-text"></span></div>
        <div class="alw-diff-row is-del"><span class="alw-ln">12</span><span class="alw-code-text">- const TVA = 0.196</span></div>
        <div class="alw-diff-row is-add"><span class="alw-ln">12</span><span class="alw-code-text">+ const TVA <span class="alw-cursor"></span></span></div>
        <div class="alw-diff-row"><span class="alw-ln">13</span><span class="alw-code-text"></span></div>
        <div class="alw-diff-row"><span class="alw-ln">14</span><span class="alw-code-text"><span style="color:#38bdf8">export function</span> <span style="color:#fbbf24">total</span>(items: Item[]) {</span></div>
        <div class="alw-diff-row"><span class="alw-ln">15</span><span class="alw-code-text">  <span style="color:#38bdf8">const</span> sum = items.reduce((s, i) => s + i.price, 0)</span></div>
        <div class="alw-diff-row"><span class="alw-ln">16</span><span class="alw-code-text">  <span style="color:#c084fc">return</span> sum * (1 + TVA)</span></div>
        <div class="alw-diff-row"><span class="alw-ln">17</span><span class="alw-code-text">}</span></div>
      </div>
    `;
  } else if (category === 'research') {
    rightBodyHtml = `
      <div class="alw-code-body scr" style="padding:10px 14px;color:#e2e8f0;font-size:12px;line-height:1.5">
        <div style="color:#38bdf8;font-weight:700;margin-bottom:4px"># Síntesis de Fuentes y Grounding</div>
        <div style="color:#94a3b8;margin-bottom:6px">Fuentes verificadas: 4 repositorios oficiales · Latencia: 140ms</div>
        <div style="border-left:2px solid #38bdf8;padding-left:8px;margin-bottom:6px;color:#cbd5e1">Extrayendo especificaciones de protocolo MCP y límites de concurrencia para agentes autónomos...<span class="alw-cursor"></span></div>
      </div>
    `;
  } else if (category === 'data') {
    rightBodyHtml = `
      <div class="alw-code-body scr" style="padding:10px 14px;color:#e2e8f0;font-size:11.5px;font-family:monospace">
        <div style="color:#fbbf24;margin-bottom:4px">-- Escaneo e indexación de registros activos</div>
        <div style="color:#86efac">SELECT agent_id, COUNT(*) AS tasks, AVG(latency_ms) FROM telemetry GROUP BY agent_id;</div>
        <div style="color:#94a3b8;margin-top:6px">korus       | 12 | 164.2 ms</div>
        <div style="color:#94a3b8">antigravity | 16 | 118.5 ms <span class="alw-cursor"></span></div>
      </div>
    `;
  } else {
    rightBodyHtml = `
      <div class="alw-code-body scr" style="padding:10px 14px;color:#e2e8f0;font-size:12px;line-height:1.5">
        <div style="color:#f87171;font-weight:700;margin-bottom:4px">[ThoughtStream · Ejecución General]</div>
        <div style="color:#cbd5e1">Analizando directrices de la tarea delegada y verificando estado de servicios conectados...<span class="alw-cursor"></span></div>
      </div>
    `;
  }

  return `
    <div class="hd chat-hd">
      <span class="tabs">${TABS.map(([g,i,l])=>`<button class="ib tb ${scene==g?'on':''}" data-a="go:${g}" title="${l}" aria-label="${l}">${ic(i)}</button>`).join('')}</span>
      <div class="ag-chat-pill danger" style="background:rgba(37,99,235,0.15);border:1px solid rgba(56,189,248,0.3)">
        <i class="ag-chat-dot" style="background:#38bdf8;box-shadow:0 0 8px #38bdf8"></i>
        <span class="ag-chat-name"><b>${esc(ag.name)} en ejecución</b></span>
      </div>
      <div class="r">
        <button class="ib" data-a="go:overview" title="Volver al panel">${ic('home')}</button>
        <button class="ib" data-a="go:prompt" title="Abrir chat">${ic('chat')}</button>
        <button class="ib cls" data-a="island_hide" title="Minimizar Isla">${ic('x')}</button>
      </div>
    </div>
    ${cbBanner}
    <div class="row">
      <div class="agent-live-work">
        <div class="alw-sidebar">
          <div class="alw-avatar-wrap">
            <div class="alw-avatar-bubble">
              <div class="alw-bubble-dots"><span></span><span></span><span></span></div>
            </div>
            <div style="display:flex;align-items:center;justify-content:center;width:66px;height:52px">
              <i class="cs" data-k=".68" style="width:66px;height:52px"></i>
            </div>
          </div>
          <div class="alw-agent-info">
            <div class="alw-agent-name">${esc(ag.name.toLowerCase())}</div>
            <div class="alw-agent-role">${esc(ag.role)}</div>
          </div>
          <div class="alw-phases-list">
            ${phases.map((ph, idx) => {
              const isDone = idx < currentPhaseIdx;
              const isActive = idx === currentPhaseIdx;
              const stateClass = isDone ? 'is-done' : (isActive ? 'is-active' : 'is-pending');
              const iconSvg = isDone
                ? `<svg class="alw-phase-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"/></svg>`
                : isActive
                  ? `<svg class="alw-phase-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="9" stroke-dasharray="14 14"/></svg>`
                  : `<svg class="alw-phase-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="8"/></svg>`;
              return `
                <div class="alw-phase-item ${stateClass}">
                  ${iconSvg}
                  <span>${esc(ph)}</span>
                </div>
              `;
            }).join('')}
          </div>
        </div>
        <div class="alw-editor">
          <div class="alw-editor-top">
            <div class="alw-file-tab">
              <span class="alw-badge-lang">${esc(lang)}</span>
              <span>${esc(file.split('/').pop())}</span>
              <span class="alw-dot-dirty"></span>
            </div>
            <span class="alw-file-path">${esc(file)}</span>
          </div>
          ${rightBodyHtml}
        </div>
      </div>
    </div>
    <div class="chips" style="margin-top:6px">
      ${B('Pausar agente', 'pause_agent', '', 'x')}
      ${B(category === 'code' ? 'Ver diff completo' : 'Ver registro completo', 'view_diff', 'p', 'spark')}
      ${B('Aceptar cambios', 'accept_diff', '', 'check')}
    </div>
  `;
 }},
 agent_delegate:{w:520,hc:1,st:'idle',x:a=>{
  const agId = a.agent_id || 'antigravity';
  const ag = ST.agents.find(x => x.id === agId) || { name: 'Antigravity', role: 'Project Architect', c: '#00D2FF', model: 'gemini-2.5-pro' };
  return `
    <div class="hd chat-hd">
      <div class="ag-chat-pill" style="--pc:${ag.c || '#00D2FF'}">
        <i class="ag-chat-dot" style="background:${ag.c || '#00D2FF'};box-shadow:0 0 8px ${ag.c || '#00D2FF'}"></i>
        <span class="ag-chat-name"><b>Delegar tarea a ${esc(ag.name)}</b></span>
      </div>
    </div>
    <div class="row">
      <div class="card mk" style="padding:16px 18px;display:flex;gap:14px;align-items:flex-start">
        <div style="display:flex;flex-direction:column;align-items:center;width:76px;flex:none">
          <i class="cs" data-k=".75" style="width:76px;height:58px"></i>
          <span style="font-size:11px;color:rgba(255,255,255,0.5);margin-top:4px">${esc(ag.role)}</span>
        </div>
        <div style="flex:1;min-width:0;display:flex;flex-direction:column;gap:8px">
          <div style="font-size:12.5px;color:#cbd5e1">Instrucciones para <b>${esc(ag.name)}</b> (${esc(ag.model || 'Gemini')}):</div>
          <textarea id="delegateTaskInput" class="fld scr" style="width:100%;height:68px;border-radius:10px;padding:8px 10px;font-size:12.5px;resize:none" placeholder="Describe la tarea o función que debe implementar este agente..."></textarea>
          <div class="ap-actions">
            <button class="btn-allow" data-a="submit_delegate:${esc(ag.id)}">Iniciar tarea</button>
            <button class="btn-deny" data-a="go:overview">Cancelar</button>
          </div>
        </div>
      </div>
    </div>
  `;
 }},
 update_card:{w:520,hc:1,st:'point_upd',x:a=>{
  const title = a.title || 'Ya salió Miku 0.5.6';
  const sub = a.sub || 'Tienes la 0.5.3';
  return `
    <div class="hd chat-hd">
      <span class="tabs">${TABS.map(([g,i,l])=>`<button class="ib tb ${scene==g?'on':''}" data-a="go:${g}" title="${l}" aria-label="${l}">${ic(i)}</button>`).join('')}</span>
      <div class="r">
        <button class="ib cls" data-a="island_hide" title="Cerrar">${ic('x')}</button>
      </div>
    </div>
    <div class="row">
      <div class="miku-update-card">
        <div class="cuc-avatar-wrap">
          <div style="display:flex;align-items:center;justify-content:center;width:58px;height:48px">
            <i class="cs" data-k=".64" style="width:58px;height:48px"></i>
          </div>
        </div>
        <div class="cuc-info">
          <div class="cuc-title">${esc(title)}</div>
          <div class="cuc-subtitle">${esc(sub)}</div>
          <div class="cuc-actions">
            <button class="cuc-btn-now" data-a="do_update">Actualizar ahora</button>
            <button class="cuc-btn-news" data-a="view_changelog">Novedades</button>
            <button class="cuc-btn-later" data-a="island_hide">Más tarde</button>
          </div>
        </div>
      </div>
    </div>
  `;
 }},
 mcp_download:{w:480,hc:1,st:'working',x:a=>{
  const name = a.name || 'Servidor MCP';
  const step = a.step || 'Descargando paquete de GitHub...';
  const pct = a.pct || 45;
  return `
    <div class="hd chat-hd">
      <div class="ag-chat-pill">
        <i class="ag-chat-dot" style="background:#38bdf8;box-shadow:0 0 8px #38bdf8"></i>
        <span class="ag-chat-name"><b>Instalación en Curso</b></span>
      </div>
    </div>
    <div class="row">
      <div class="process-card-box">
        <div class="pcb-header">
          <span class="pcb-step-text">${esc(name)}: ${esc(step)}</span>
          <span class="pcb-percent">${pct} %</span>
        </div>
        <div class="pcb-progress-track">
          <div class="pcb-progress-fill" style="width:${pct}%"></div>
        </div>
        <div class="pcb-footer-note">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/></svg>
          <span>Verificando firmas y registrando herramientas nativas...</span>
        </div>
      </div>
    </div>
    <div class="chips">
      ${B('Cancelar instalación', 'go:overview', '', 'x')}
    </div>
  `;
 }},
 ai_inference:{w:490,hc:1,st:'thinking',x:a=>{
  const model = a.model || 'gemini-2.5-flash';
  const tokens = a.tokens || 1420;
  const elapsed = a.elapsed_ms || 380;
  const cbTripped = Boolean(a.circuit_breaker_tripped);
  return `
    <div class="hd chat-hd">
      <div class="ag-chat-pill">
        <i class="ag-chat-dot" style="background:#a855f7;box-shadow:0 0 8px #a855f7"></i>
        <span class="ag-chat-name"><b>Inferencia de IA en Curso</b></span>
      </div>
    </div>
    ${cbTripped ? `<div class="cb-amber-banner" style="background:rgba(245,158,11,0.16);border:1px solid rgba(251,191,36,0.4);border-radius:8px;padding:6px 12px;margin-bottom:6px;display:flex;justify-content:space-between;align-items:center;font-size:11.5px;color:#fcd34d"><span>Proveedor principal saturado (HTTP 429). Conmutando temporalmente a respaldo.</span><b style="font-family:monospace">Reintentando en 178s</b></div>` : ''}
    <div class="row">
      <div class="process-card-box">
        <div class="pcb-header">
          <span class="pcb-step-text">Modelo: <b>${esc(model)}</b></span>
          <span class="pcb-percent">${esc(String(elapsed))} ms · ${esc(String(tokens))} tok</span>
        </div>
        <div class="pcb-progress-track">
          <div class="pcb-progress-fill" style="width:72%;background:linear-gradient(90deg,#a855f7,#38bdf8)"></div>
        </div>
        <div class="pcb-footer-note">
          <span>Generando respuesta estructurada con telemetría activa...</span>
        </div>
      </div>
    </div>
  `;
 }},
 web_grounding:{w:500,hc:1,st:'working',x:a=>{
  const query = a.query || 'Model Context Protocol security sandboxing';
  const sources = a.sources || 4;
  return `
    <div class="hd chat-hd">
      <div class="ag-chat-pill">
        <i class="ag-chat-dot" style="background:#10b981;box-shadow:0 0 8px #10b981"></i>
        <span class="ag-chat-name"><b>Búsqueda Web y Grounding</b></span>
      </div>
    </div>
    <div class="row">
      <div class="process-card-box">
        <div class="pcb-header">
          <span class="pcb-step-text">Consulta: <b>${esc(query)}</b></span>
          <span class="pcb-percent">${esc(String(sources))} fuentes</span>
        </div>
        <div class="pcb-progress-track">
          <div class="pcb-progress-fill" style="width:84%;background:linear-gradient(90deg,#10b981,#06b6d4)"></div>
        </div>
        <div class="pcb-footer-note">
          <span>Extrayendo fragmentos verificados y validando citas en tiempo real...</span>
        </div>
      </div>
    </div>
  `;
 }}
};
function tabs(){if(scene=='settings'||scene=='link')go(scene)}

const inn=$('#in'),col=$('#col'),mkw=$('#mkw');let gi,lastExp=Date.now(),mxk=0,myk=0,mkk=.4,mi=0;
function renderOv(){col.innerHTML=SC.overview.x();fit();SC.overview.after?.()}
function go(n='compact',a={}){if(LOCKI&&!a.__i)return;if(a.__i)LOCKI=0;if(n=='overview')PG=a.pg||0;
 const previousScene=scene;
 if(n=='compact')PIN=0;
 if(n=='intro'){if(window.__intro)n='compact';else{LOCKI=1;setTimeout(()=>{LOCKI=0},9000)}window.__intro=1}const s=SC[n];if(!s)return;clearTimeout(tm);clearTimeout(notT);scene=n;poke();
 if(n=='result')RES=a.text??RES;if(n=='quicklook')QL={title:a.title||QL.title,text:a.text??QL.text};
 clearInterval(gi);let h=s.x(a);const wr=!s.m&&!s.stg&&!s.hc&&!h.includes('class="cs"');if(wr)h=wrapRow(h,s);
 inn.classList.toggle('m',!!s.m);inn.classList.toggle('stg',!!s.stg);inn.classList.toggle('hc',!!s.hc||wr);if(!s.m)lastExp=Date.now();
 const k=s.k||(s.m?.34:.85);mkw.dataset.k=k;mkw.style.width=112*k+'px';mkw.style.height=84*k+'px';
 inn.style.width=inn.style.minWidth=inn.style.maxWidth=(s.m?cW():(s.w||620))+'px';col.innerHTML=h;stagger();fit();
 const agChat = getAgChat(curAg().id);
 const targetSt = a.st || (agChat.busy ? 'thinking' : (n=='tool_use'&&/cursor|mov/i.test(a.label||'')?'working':s.st)); buddy.setState(targetSt);
 const em=a.emote||s.em;if(em)buddy.emote(em,n=='notify'?2400:1600,2);
 const visibleSound=previousScene==='compact'&&n!=='compact'?'open':previousScene!=='compact'&&n==='compact'?'tap':null;
 if(visibleSound)requestAnimationFrame(()=>setTimeout(()=>{if(scene===n&&!document.hidden)window.SoundFX?.play?.(visibleSound,visibleSound==='tap'?{pitch:520}:{})},90));
 const convo=$('.chat-convo-body');if(convo)convo.scrollTop=convo.scrollHeight;
 if(n==='boot')startBootProgress();else clearInterval(bootProgressTimer);
 s.after?.();armAC();
 if(n=='notify'&&!a.ask)notT=setTimeout(()=>go('compact'),a.ms||5000);
}
window.go=go;
function fit(){const w=Math.ceil(Math.max(inn.offsetWidth||0, inn.scrollWidth||0));const h=Math.ceil(Math.max(inn.offsetHeight||0, inn.scrollHeight||0));
 isl.classList.toggle('closing',w<lw||h<lh);lw=w;lh=h;
 isl.style.width=w+'px';isl.style.height=h+'px';isl.style.borderRadius=inn.classList.contains('m')?`0 0 ${h/2}px ${h/2}px`:'0 0 32px 32px';
 notify();
}
new ResizeObserver(fit).observe(inn);
function applyWinSize(w,h){
 if(window.pywebview?.api?.resize_window)window.pywebview.api.resize_window(w,h);
 else if(window.__TAURI__?.core?.invoke)window.__TAURI__.core.invoke('resize_window',{width:w,height:h}).catch(()=>{});
}
let cw=0,ch=0,wt=null,shrinkTimer=null;
function notify(){
 const isComp=(scene==='compact');
 if(isComp){
  clearTimeout(shrinkTimer);
  clearTimeout(wt);
  shrinkTimer=setTimeout(()=>{
   if(scene==='compact'){
    const compW=Math.max(340,Math.ceil(inn.offsetWidth||340)+6);
    const compH=Math.max(44,Math.ceil(inn.offsetHeight||44)+4);
    cw=compW;ch=compH;
    applyWinSize(compW,compH);
   }
  },280);
  return;
 }
 clearTimeout(shrinkTimer);
 clearTimeout(wt);
 const contentW = Math.max(inn.scrollWidth||0, inn.offsetWidth||0, 580);
 const contentH = Math.max(inn.scrollHeight||0, inn.offsetHeight||0, scene==='overview'?240:320);
 const targetW = Math.ceil(contentW + 12);
 const targetH = Math.ceil(contentH + 8);
 cw = targetW;
 ch = targetH;
 applyWinSize(cw, ch);
}
new ResizeObserver(notify).observe(isl);addEventListener('pywebviewready',notify);
addEventListener('DOMContentLoaded',()=>{
  setTimeout(notify,150);
  // Click-through inteligente: si el ratón sale de la isla compacta, permitir clics en ventanas detrás
  try {
    const win = window.__TAURI__?.window?.getCurrentWindow?.();
    if (win?.setIgnoreCursorEvents) {
      let isPassThrough = false;
      document.addEventListener('pointermove', (e) => {
        const inside = !!e.target.closest('#isl');
        if (inside && isPassThrough) {
          isPassThrough = false;
          win.setIgnoreCursorEvents(false).catch(()=>{});
        } else if (!inside && !isPassThrough && scene === 'compact') {
          isPassThrough = true;
          win.setIgnoreCursorEvents(true).catch(()=>{});
        }
      });
      document.addEventListener('pointerleave', () => {
        if (scene === 'compact' && !isPassThrough) {
          isPassThrough = true;
          win.setIgnoreCursorEvents(true).catch(()=>{});
        }
      });
    }
  } catch (_) {}
});

let taps=0,tt;
function tap(){if(LOCKI)return;clearTimeout(tt);taps++;tt=setTimeout(()=>taps=0,900);
 if(Date.now()<LOCK.until&&LOCK.prio>=3){P.sq=Math.max(P.sq,.1);return}
 P.sq=.26;P.sv=0;P.jv=-120;
 if(base=='sleeping'){wake();return}
 if(taps>=5){taps=0;go('notify',{title:'Demasiados toques',text:'Me recompongo y vuelvo al trabajo.',emote:'dizzy',ms:3000})}
 else buddy.emote(taps>=2?'surprised':'wink',taps>=2?900:700,0)}
function look(e){if(drag.on){drag.x=e.clientX;drag.y=e.clientY}const r=$('#mk').getBoundingClientRect(),gx=drag.on?70:260,gy=drag.on?55:180;mx=clamp((e.clientX-r.left-r.width/2)/gx);my=clamp((e.clientY-r.top-r.height/2)/gy)}
addEventListener('pointermove',look);
window.__pickingFile = false;
const KEEP=['compact','boot','intro','drop','uploading','tool_use','prompt','result','approve','question','error_card','agent_work','agent_delegate','update_card','mcp_download','ai_inference','web_grounding'],collapse=()=>{if(!window.__pickingFile&&window.__mikuCoreConnected&&scene!=='boot'&&scene!=='intro'&&!KEEP.includes(scene))go('compact')};
addEventListener('pointerdown',e=>{wake();if(!isl.contains(e.target))collapse()});
addEventListener('blur',()=>{collapse()});
try{
 window.__TAURI__?.event?.listen?.('window-blur',()=>{collapse()});
 window.__TAURI__?.event?.listen?.('tauri://blur',()=>{collapse()});
 window.__TAURI__?.window?.getCurrentWindow?.()?.onFocusChanged?.(({payload:f})=>{if(!f)collapse()});
}catch(_){}
addEventListener('keydown',e=>{
 wake();
 if(scene=='approve'&&!e.target.closest('input,textarea')){
  if(e.key=='y'||e.key=='Y'){e.preventDefault();ACT.apok();}
  else if(e.key=='n'||e.key=='N'){e.preventDefault();ACT.denyap();}
  else if(e.key=='a'||e.key=='A'){e.preventDefault();ACT.apalways();}
 }
 if(scene=='question'&&!e.target.closest('input,textarea')&&/^[1-9]$/.test(e.key)){
  const idx=parseInt(e.key,10)-1;
  const btns=$$('.question-opt-btn');
  if(btns[idx]){e.preventDefault();btns[idx].click();}
 }
 if(e.key=='Escape'){
  const pop=$('#cmdPalettePop');
  if(pop&&pop.style.display!=='none'){pop.style.display='none';return;}
  if(scene==='boot'||scene==='intro'||!window.__mikuCoreConnected)return;
  scene=='tool_use'||scene=='drop'?ACT.cancel():go('compact');
 }
 if(e.target.id=='q'&&e.key=='Enter')send();
});
isl.addEventListener('wheel',e=>{wake();if(e.target.closest('.scr'))return;
 if(scene=='overview'){e.preventDefault();setVol(MUS.vol-Math.sign(e.deltaY)*5)}
 else if(scene=='compact'){e.preventDefault();e.deltaY>0?go('overview'):buddy.emote('look','up')}},{passive:false});

const kc=(v,a,b)=>Math.min(b,Math.max(a,v)),QUART=t=>1-(1-t)**4,FLAT=t=>t,SWING=t=>t<.5?4*t**3:1-(-2*t+2)**3/2;
function mkTw(a,b,ms,ease,fn,done){let id,t0=performance.now();const f=n=>{const t=Math.min(1,(n-t0)/ms);fn(a+(b-a)*ease(t));if(t<1)id=requestAnimationFrame(f);else done&&done()};id=requestAnimationFrame(f);return()=>cancelAnimationFrame(id)}
function mkSp(x,fn){const s={x,v:0,t:x,raf:0,k:300,c:30,m:1,cb:null,
 to(t,k,c,m,cb){s.t=t;s.k=k;s.c=c;s.m=m||1;s.cb=cb||null;if(s.raf)return;let p=0;const f=n=>{const dt=p?Math.min(.02,(n-p)/1000):.016;p=n;s.v+=((-s.k*(s.x-s.t)-s.c*s.v)/s.m)*dt;s.x+=s.v*dt;fn(s.x);if(Math.abs(s.x-s.t)<.02&&Math.abs(s.v)<.02){s.x=s.t;s.v=0;s.raf=0;fn(s.x);const c=s.cb;s.cb=null;c&&c();return}s.raf=requestAnimationFrame(f)};s.raf=requestAnimationFrame(f)},
 stop(){cancelAnimationFrame(s.raf);s.raf=0},set(v){s.stop();s.x=v;s.v=0;fn(v)}};return s}

function SmoothSlider(host, { value = 80, min = 0, max = 100, step = 1, unit = '%', onChange }) {
  let cur = Math.max(min, Math.min(max, value));
  let dragging = false;
  let activePointerId = null;

  host.innerHTML = `
    <div class="so-slider" tabindex="0" role="slider" aria-valuenow="${cur}" aria-valuemin="${min}" aria-valuemax="${max}">
      <svg class="so-spk so-spk-mute" viewBox="0 0 24 24" title="Silenciar"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><line x1="23" y1="9" x2="17" y2="15"/><line x1="17" y1="9" x2="23" y2="15"/></svg>
      <div class="so-slider-track">
        <div class="so-slider-fill" style="width: ${((cur - min) / (max - min) * 100).toFixed(1)}%"></div>
      </div>
      <svg class="so-spk so-spk-high" viewBox="0 0 24 24" title="100%"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"/></svg>
      <span class="so-slider-val">${Math.round(cur)}${unit}</span>
    </div>
  `;

  const slider = host.querySelector('.so-slider');
  const track = host.querySelector('.so-slider-track');
  const fill = host.querySelector('.so-slider-fill');
  const valText = host.querySelector('.so-slider-val');
  const spkMute = host.querySelector('.so-spk-mute');
  const spkHigh = host.querySelector('.so-spk-high');

  const update = (clientX) => {
    const rect = track.getBoundingClientRect();
    if (!rect.width) return;
    const ratio = Math.max(0, Math.min(1, (clientX - rect.left) / rect.width));
    let raw = min + ratio * (max - min);
    if (step > 0) raw = Math.round(raw / step) * step;
    cur = Math.max(min, Math.min(max, raw));
    const pct = ((cur - min) / (max - min) * 100).toFixed(1);
    fill.style.width = pct + '%';
    valText.textContent = Math.round(cur) + unit;
    slider.setAttribute('aria-valuenow', Math.round(cur));
    onChange?.(cur);
  };

  const onPointerMove = (e) => {
    if (!dragging) return;
    update(e.clientX);
  };

  const onPointerUp = (e) => {
    if (dragging) {
      dragging = false;
      window.removeEventListener('pointermove', onPointerMove);
      window.removeEventListener('pointerup', onPointerUp);
      window.removeEventListener('pointercancel', onPointerUp);
      if (activePointerId !== null) {
        try { track.releasePointerCapture(activePointerId); } catch (_) {}
        activePointerId = null;
      }
    }
  };

  slider.addEventListener('pointerdown', (e) => {
    if (e.button !== 0) return;
    if (e.target.closest('.so-spk') || e.target.closest('.so-slider-val')) return;
    dragging = true;
    activePointerId = e.pointerId;
    try { slider.setPointerCapture(e.pointerId); } catch (_) {}
    window.addEventListener('pointermove', onPointerMove, { passive: true });
    window.addEventListener('pointerup', onPointerUp);
    window.addEventListener('pointercancel', onPointerUp);
    update(e.clientX);
    window.SoundFX?.click?.();
    e.preventDefault();
  });

  spkMute?.addEventListener('click', () => {
    cur = min;
    fill.style.width = '0%';
    valText.textContent = Math.round(cur) + unit;
    window.SoundFX?.pop?.();
    onChange?.(cur);
  });

  spkHigh?.addEventListener('click', () => {
    cur = max;
    fill.style.width = '100%';
    valText.textContent = Math.round(cur) + unit;
    window.SoundFX?.pop?.();
    onChange?.(cur);
  });

  return {
    set(v) {
      cur = Math.max(min, Math.min(max, v));
      const pct = ((cur - min) / (max - min) * 100).toFixed(1);
      fill.style.width = pct + '%';
      valText.textContent = Math.round(cur) + unit;
      slider.setAttribute('aria-valuenow', Math.round(cur));
    }
  };
}

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
 const onMove=e=>{if(!held)return;const v=at(e.clientX),dt=Math.max(1,e.timeStamp-last.t);hv=(v-last.v)/dt*16.67;last={v,t:e.timeStamp};val=v;run()};
 const onUp=e=>{if(!held)return;held=0;tr.removeAttribute('data-held');window.removeEventListener('pointermove',onMove);window.removeEventListener('pointerup',onUp);window.removeEventListener('pointercancel',onUp);hv=kc(hv,-6,6);if(flat)hv=0;run()};
 tr.addEventListener('pointerdown',e=>{held=1;tr.setAttribute('data-held','1');hv=0;val=at(e.clientX);last={v:val,t:e.timeStamp};run();window.addEventListener('pointermove',onMove);window.addEventListener('pointerup',onUp);window.addEventListener('pointercancel',onUp);e.preventDefault()});
 tr.addEventListener('keydown',e=>{const s=e.shiftKey?10:2,to=e.key=='ArrowRight'||e.key=='ArrowUp'?val+s:e.key=='ArrowLeft'||e.key=='ArrowDown'?val-s:e.key=='Home'?0:e.key=='End'?100:null;if(to===null)return;e.preventDefault();hv=0;val=kc(to,0,100);run()});
 paint();return{set(v){val=kc(v,0,100);hv=0;lastE=Math.round(val);run()}}}

const SV='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">';
const ICN={arrow:'<svg viewBox="0 0 24 24"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>',check:'<svg viewBox="0 0 24 24"><path d="M20 6 9 17l-5-5"/></svg>',
 back:SV+'<polygon points="19 20 9 12 19 4 19 20"/><line x1="5" x2="5" y1="19" y2="5"/></svg>',fwd:SV+'<polygon points="5 4 15 12 5 20 5 4"/><line x1="19" x2="19" y1="5" y2="19"/></svg>',
 heart:SV+'<path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/></svg>',
 note:'<svg viewBox="0 0 24 24"><path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/></svg>'};

function SlideConfirm(host,o={}){
 const H=56,PAD=4,GRIP=48,span=o.span||260,TR=span-PAD*2-GRIP,lab=o.label||'Desliza para permitir';
 host.innerHTML=`<div class="sld" style="width:${span}px;height:${H}px"><div class="sld-track"><i class="sld-wash" style="border-radius:24px"></i><span class="sld-say">${lab}</span><button type="button" class="sld-grip" style="border-radius:24px" aria-label="${lab}"><span class="sld-arrow">${ICN.arrow}</span><span class="sld-done">${ICN.check}${o.doneLabel||'Permitido'}</span></button></div></div>`;
 const tr=host.querySelector('.sld-track'),wash=tr.children[0],say=tr.children[1],gp=tr.children[2],arw=gp.children[0];
 let x=0,anchor=0,shown=1,pulse=1,hot=0,held=0,done=0,g=null,off=null;
 const stiff=500,crit=2*Math.sqrt(stiff*.9);
 const paint=()=>{const seen=kc(x,0,TR),wide=GRIP+kc(anchor-seen,0,TR),q=1-Math.min(.08,Math.max(0,-x)/110),sw=hot&&!held&&!done?1.03:1;
  gp.style.width=wide+'px';gp.style.transform=`translateX(${seen}px) scale(${q*sw},${1/q*sw})`;wash.style.width=(seen+GRIP)+'px';
  say.style.opacity=kc(1-seen/(TR*.55),0,1);arw.style.opacity=shown*kc(1-(seen-TR*.55)/(TR*.4),0,1);tr.style.transform=`scale(${pulse})`};
 const X=mkSp(0,v=>{x=v;paint()});
 const local=cx=>{const b=tr.getBoundingClientRect();return(cx-b.left)/((b.width/span)||1)};
 const finish=()=>{if(done)return;done=1;tr.dataset.done=1;anchor=x;mkTw(1,0,120,FLAT,v=>{shown=v;paint()});X.to(0,stiff,crit,.9);
  setTimeout(()=>mkTw(0,1,460,FLAT,u=>{pulse=u<.62?1-.026*(u/.62):.974+.026*((u-.62)/.38);paint()}),100);setTimeout(()=>o.onConfirm?.(),900)};
 const mv=e=>{if(!g||g.id!==e.pointerId)return;const a=local(e.clientX);if(g.grab===null){g.grab=a-x;return}X.set(kc(a-g.grab,0,TR))};
 const up=e=>{if(!g)return;g=null;held=0;delete tr.dataset.held;removeEventListener('pointermove',mv);removeEventListener('pointerup',up);removeEventListener('pointercancel',up);
  if(x>=TR)finish();else X.to(0,stiff,crit*.62,.9)};
 tr.addEventListener('pointerdown',e=>{if(done)return;e.stopPropagation();g={id:e.pointerId,grab:null};held=1;tr.dataset.held=1;try{tr.setPointerCapture(e.pointerId)}catch{}
  addEventListener('pointermove',mv);addEventListener('pointerup',up);addEventListener('pointercancel',up)});
 gp.addEventListener('pointerenter',()=>{hot=1;paint()});gp.addEventListener('pointerleave',()=>{hot=0;paint()});
 gp.addEventListener('keydown',e=>{if(e.key=='Enter'||e.key==' '){e.preventDefault();X.set(TR);finish()}});
 paint()}

let PLY,PLV;
function mkSound(host,o={}){
 const W=Math.max(220,Math.round(host.clientWidth)||260),SHUT=78,PAD=10,A0=40,A1=64,LIKE=30,LEAD=46,RAIL_H=3,RAIL_Y=PAD+A1+22,OPS_Y=RAIL_Y+RAIL_H+8+10+16+LEAD/2,OPEN=Math.round(OPS_Y+LEAD/2+PAD);
 const mix=(a,b,t)=>a+(b-a)*t,reduced=!!matchMedia?.('(prefers-reduced-motion: reduce)').matches;
 const PL=[6,4,10,4,10,20,6,20],PY=[6.5,4,13.25,8,13.25,16,6.5,20],PR=[14,4,18,4,18,20,14,20],PYR=[13.25,8,20,12,20,12,13.25,16];
 const quad=(a,b,t)=>{let d='';for(let i=0;i<8;i+=2)d+=`${i?'L':'M'}${mix(a[i],b[i],t).toFixed(2)} ${mix(a[i+1],b[i+1],t).toFixed(2)}`;return d+'Z'};
 const clock=s=>`${Math.floor(s/60)}:${String(Math.floor(s%60)).padStart(2,'0')}`;
 host.innerHTML=`<div class="sn"><div class="sn-box"><span class="sn-art">${ICN.note}</span><span class="sn-say"><span class="sn-t"></span><span class="sn-by"></span></span><span class="sn-bar"><span class="sn-rail"><span class="sn-run"></span></span><span class="sn-clock"><span></span><span></span></span></span><button class="sn-tap" aria-expanded="false" aria-label="Abrir el reproductor"></button><button class="sn-like" aria-label="Me gusta" aria-pressed="false" tabindex="-1">${ICN.heart}</button><span class="sn-ops"><button class="sn-op" data-r="prev" aria-label="Anterior">${ICN.back}</button><button class="sn-op" data-lead data-r="toggle" aria-label="Reproducir"><svg viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"><path/><path/></svg></button><button class="sn-op" data-r="next" aria-label="Siguiente">${ICN.fwd}</button></span></div></div>`;
 const $q=s=>host.querySelector(s),sn=$q('.sn'),box=$q('.sn-box'),art=$q('.sn-art'),say=$q('.sn-say'),tt=$q('.sn-t'),by=$q('.sn-by'),bar=$q('.sn-bar'),run=$q('.sn-run'),ck=$q('.sn-clock'),tap=$q('.sn-tap'),like=$q('.sn-like'),ops=$q('.sn-ops'),sv=ops.querySelectorAll('svg'),mp=sv[1].querySelectorAll('path'),lead=ops.children[1];
 let p=0,u=0,open=0,going=!!o.get().playing,at=0,mt=going?0:1,c1,c2,c3,liked=0,TOTAL=214;
 const layout=()=>{const zoom=open?1:1-.035*Math.sin(Math.PI*kc(u,0,1)**1.5),h=mix(SHUT,OPEN,p),late=kc((p-.6)/.4,0,1),s=mix(A0,A1,p),sd=mix(24,34,p),ld=mix(30,LEAD,p),S=(e,w,hh)=>{e.style.width=w+'px';e.style.height=hh+'px'};
  sn.style.height=h+'px';box.style.height=h+'px';box.style.borderRadius=mix(20,26,p)+'px';box.style.scale=zoom;
  art.style.cssText+=`;left:${PAD}px;top:${PAD}px;width:${s}px;height:${s}px;border-radius:${mix(10,16,p)}px`;
  say.style.left=mix(PAD+A0+10,PAD+A1+10,p)+'px';say.style.top=PAD+'px';say.style.height=s+'px';say.style.width=mix(94,W-PAD-(PAD+A1+10)-(LIKE+10),p)+'px';tt.style.fontSize=mix(13,15.5,p)+'px';by.style.fontSize=mix(11,12,p)+'px';
  bar.style.top=mix(SHUT-PAD-RAIL_H,RAIL_Y,p)+'px';bar.style.left=PAD+'px';bar.style.width=W-PAD*2+'px';ck.style.opacity=late;
  tap.style.left=mix(0,PAD,p)+'px';tap.style.top=mix(0,PAD,p)+'px';tap.style.width=mix(W,W-PAD*2,p)+'px';tap.style.height=mix(SHUT,A1,p)+'px';tap.style.borderRadius=mix(20,16,p)+'px';
  like.style.cssText+=`;left:${W-PAD-LIKE}px;top:${PAD}px;width:${LIKE}px;height:${LIKE}px;opacity:${late};pointer-events:${late>.9?'auto':'none'}`;
  ops.style.left=mix(W-PAD-44,W/2,p)+'px';ops.style.top=mix(PAD+A0/2,OPS_Y,p)+'px';ops.style.gap=mix(5,14,p)+'px';
  S(ops.children[0],sd,sd);S(lead,ld,ld);S(ops.children[2],sd,sd);[0,2].forEach(i=>{const z=mix(13,16,p);sv[i].setAttribute('width',z);sv[i].setAttribute('height',z)});sv[1].setAttribute('width',mix(14,18,p));sv[1].setAttribute('height',mix(14,18,p))};
 const mark=()=>{const goo=Math.sin(kc(mt,0,1)*Math.PI),pull=1.6*goo,tip=(going?-9:9)*goo;sv[1].style.transform=`rotate(${tip}deg) scale(${1-.13*goo},${1+.11*goo})`;
  mp[0].setAttribute('d',quad(PL,PY,mt));mp[0].setAttribute('transform',`translate(${pull} 0)`);mp[1].setAttribute('d',quad(PR,PYR,mt));mp[1].setAttribute('transform',`translate(${-pull} 0)`)};
 const prog=()=>{run.style.width=kc(at/TOTAL,0,1)*100+'%';ck.children[0].textContent=clock(at);ck.children[1].textContent='−'+clock(Math.max(0,TOTAL-at))};
 const sync=()=>{const m=o.get(),g=!!m.playing;tt.textContent=m.playing||m.title&&m.title!='Sin reproducción'?m.title:'Sin música';by.textContent=m.artist||'—';
  if(m.cover)art.style.backgroundImage=`url(${m.cover})`;if(m.dur)TOTAL=m.dur;if(m.pos!=null)at=m.pos;prog();
  if(g!==going){going=g;lead.setAttribute('aria-label',g?'Pausa':'Reproducir');c3&&c3();c3=mkTw(mt,g?0:1,reduced?1:300,SWING,v=>{mt=v;mark()})}};
 const flip=()=>{open=open?0:1;tap.setAttribute('aria-expanded',!!open);tap.setAttribute('aria-label',open?'Cerrar el reproductor':'Abrir el reproductor');like.tabIndex=open?0:-1;c1&&c1();c2&&c2();
  const d=reduced?1:460;isl.classList.add('live');setTimeout(()=>isl.classList.remove('live'),d+80);c1=mkTw(p,open,d,QUART,v=>{p=v;layout()});c2=mkTw(u,open,d,FLAT,v=>{u=v;layout()})};
 tap.addEventListener('click',flip);
 like.addEventListener('click',()=>{liked=liked?0:1;like.toggleAttribute('data-on',!!liked);like.setAttribute('aria-pressed',!!liked);like.firstChild.setAttribute('fill',liked?'currentColor':'none');window.Bridge?.like?.(!!liked)});
 ops.addEventListener('click',e=>{const b=e.target.closest('[data-r]');if(!b)return;const r=b.dataset.r;if(r!='toggle')at=0;prog();o.act?.(r)});
 const away=e=>{if(!host.isConnected){document.removeEventListener('pointerdown',away);return}if(open&&e.isTrusted&&!box.contains(e.target))flip()};document.addEventListener('pointerdown',away);
 const iv=setInterval(()=>{if(!host.isConnected){clearInterval(iv);return}if(going){at=at>=TOTAL?0:at+1;prog()}},1000);
 layout();mark();prog();sync();lead.setAttribute('aria-label',going?'Pausa':'Reproducir');return{sync}}
function setVol(v){MUS.vol=clamp(v,0,100);const f=$('#vf'),p=$('#vp');if(f)f.style.width=MUS.vol+'%';if(p)p.textContent=Math.round(MUS.vol)+'%';window.Bridge?.media?.('vol', Math.round(MUS.vol));PLV?.set?.(MUS.vol)}
function music(m){Object.assign(MUS,m);PLY?.sync?.();if(m.volume!=null)MUS.vol=m.volume;const e=$('#pmt');if(e&&scene=='overview')e.textContent=MUS.playing?MUS.title:'Música';triggerStarLoop();label()}
isl.addEventListener('pointerdown',e=>{const b=e.target.closest('button');if(!b||b.matches('.sw'))return;const r=b.getBoundingClientRect(),d=Math.max(r.width,r.height)*2.2,o=document.createElement('span');
 o.className='rip';o.style.cssText=`width:${d}px;height:${d}px;left:${e.clientX-r.left-d/2}px;top:${e.clientY-r.top-d/2}px`;b.appendChild(o);o.addEventListener('animationend',()=>o.remove())});

const flash=(b,t)=>{const o=b.innerHTML;b.innerHTML=ic('check')+t;b.classList.add('ok');setTimeout(()=>{b.innerHTML=o;b.classList.remove('ok')},1200)};
const copy=async(x,b)=>{try{await navigator.clipboard.writeText(x)}catch{const a=document.createElement('textarea');a.value=x;document.body.append(a);a.select();document.execCommand('copy');a.remove()}flash(b,'Copiado')};
async function send(){
  const q=$('#q'),v=q?.value.trim();
  const file = window.__attachedFile;
  if(!v && !file) return;
  if(file && file.pendingPromise){
    try { await file.pendingPromise; } catch(_){}
  }
  const queryText = v || (file ? `Analiza este archivo: ${file.name}` : '');
  window.SoundFX?.send?.();
  lastQ=queryText;
  const a=curAg();
  const ch=getAgChat(a.id);
  ch.lastQ=queryText;
  ch.lastFile=file ? { name: file.name, size: file.size || 0, type: file.type || '', content: file.content || null } : null;
  ch.busy=true;
  ch.steps=[];
  ch.thinkStart=performance.now();
  ch.thinkDur=0;
  ch.unread=false;
  ch.history.push({role:'user',content:queryText,file:ch.lastFile});
  saveAgChats();
  if(q)q.value='';
  
  // Guardar copia del archivo y limpiar inmediatamente la píldora sobre el input
  const fileToSend = file ? { ...file } : null;
  window.__attachedFile = null;
  const wrap = document.getElementById('chat-attached-wrap');
  if (wrap) wrap.innerHTML = '';
  
  const slashMatch = queryText.match(/^\/([a-zA-Z0-9_\-]+)\s*(.*)/);
  if (slashMatch) {
    const slug = slashMatch[1].toLowerCase();
    const taskRemainder = slashMatch[2].trim() || 'Ejecutar tarea delegada';
    const foundAg = ST.agents.find(x => x.id.toLowerCase() === slug || x.name.toLowerCase() === slug);
    if (foundAg) {
      if (q) q.value = '';
      const targetCh = getAgChat(foundAg.id);
      targetCh.busy = true;
      targetCh.lastQ = taskRemainder;
      fetch('/api/agents/delegate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ agent_id: foundAg.id, task: taskRemainder })
      }).catch(()=>{});
      window.SoundFX?.play?.('pop');
      buddy.setState('working');
      go('agent_work', { agent_id: foundAg.id, task: taskRemainder, phase: 'Edit', file: 'src/invoice.ts' });
      return;
    }
  }

  tlTrack('thinking');
  buddy.setState('thinking');
  if(window.Bridge?.sendChat)window.Bridge.sendChat(queryText, a, fileToSend);
  else setTimeout(()=>go('result',{text:'(demo) Recibí: «'+queryText+'». Conecta window.Bridge.sendChat para respuestas reales.'}),1400);
  go('prompt');
}
const ACT={
 agent:x=>{
  const idx=+x;
  window.Bridge?.stopSpeaking?.();
  if(idx<0){
    SELA=-1;
    applyTheme();
    go('prompt');
    return;
  }
  SELA=Math.max(0,Math.min(ST.agents.length-1,idx));
  applyTheme();
  const target=curAg();
  const ch=getAgChat(target.id);
  const isBusy = ch.busy || target.id==='korus' || (window.__activeTasks && window.__activeTasks[target.id]);
  buddy.setState(isBusy?'thinking':'idle');
  if(isBusy){
    go('agent_work',{agent_id:target.id,phase:'Edit',file:'src/invoice.ts'});
  } else {
    go('agent_delegate',{agent_id:target.id});
  }
 },
 submit_delegate:x=>{
  const agentId = x || (curAg() ? curAg().id : 'korus');
  const inputEl = $('#delegateTaskInput');
  const taskText = inputEl ? inputEl.value.trim() : 'Refactorizar código';
  const ch = getAgChat(agentId);
  ch.busy = true;
  fetch('/api/agents/delegate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ agent_id: agentId, task: taskText })
  }).catch(()=>{});
  window.SoundFX?.play?.('pop');
  go('agent_work', { agent_id: agentId, task: taskText, phase: 'Edit', file: 'src/invoice.ts' });
 },
 do_update:()=>{
  window.SoundFX?.play?.('update');
  go('mcp_download', { name: 'Actualización Miku 0.5.6', step: 'Descargando binario y actualizando dependencias...', pct: 68 });
 },
 view_changelog:()=>{
  go('notify', {
    badge: 'Novedades v0.5.6',
    title: 'Novedades de Miku 0.5.6',
    text: '• Pantalla de trabajo en vivo para agentes\n• Desacople de Agentes e Integraciones\n• Catálogo online MCP con enlaces GitHub\n• Skills Nativas con auto-activación\n• Dashboard de uso de API con circuit-breaker',
    btns: [['Actualizar ahora', 'do_update'], ['Entendido', 'compact']]
  });
 },
 pause_agent:()=>{
  const target = curAg();
  const ch = getAgChat(target.id);
  ch.busy = false;
  window.SoundFX?.play?.('tap');
  go('notify', { title: 'Agente en pausa', text: `Se ha pausado la tarea de ${target.name}.`, ms: 2500 });
 },
 view_diff:()=>{
  window.SoundFX?.play?.('pop');
  go('quicklook', { title: 'src/invoice.ts · Diff en vivo', text: '@@ -12,1 +12,1 @@\n- const TVA = 0.196\n+ const TVA = 0.20\n\nexport function total(items: Item[]) {\n  const sum = items.reduce((s, i) => s + i.price, 0)\n  return sum * (1 + TVA)\n}' });
 },
 accept_diff:()=>{
  window.SoundFX?.play?.('chime');
  go('notify', { badge: 'Completado', title: 'Cambios aplicados', text: 'El diff ha sido integrado y verificado sin errores.', ms: 3000 });
 },
 emo:x=>{if(x=='approve'){approve({title:'¿Permitir a Claude Code ejecutar un comando?',text:'npm run build'});return}if(x=='ask'){ask({title:'¿Cómo te sientes hoy?',text:'Puedo ajustar mi tono contigo.',options:['Con energía','Tranquilo','Enfocado']});return}$$('.gal button').forEach(b=>b.classList.toggle('on',b.dataset.a=='emo:'+x));x.startsWith('look_')?buddy.look(x.slice(5),2200):buddy.emote(x,2200)},
 playall:()=>{clearInterval(gi);let i=0;const t=()=>{if(scene!='gallery'||i>=GAL.length){clearInterval(gi);return}ACT.emo(GAL[i++])};t();gi=setInterval(t,2300)},
 go:x=>{if(scene===x&&x==='overview'){if(typeof PG!=='undefined'&&PG!==0){PG=0;renderOv()}return}go(x,x=='tool_use'?{label:'Analizando pantalla'}:{});if(x==='link'){openSettings('link',true);}},tab:x=>tabs(x),send,
 q:x=>{const q=$('#q');q.value=x;q.focus()},
 dictate:()=>{ST.mic=!ST.mic;window.Bridge?.dictate?.(ST.mic);buddy.setState(ST.mic?'listening':'idle')},
 copy:(x,b)=>copy(RES,b),qcopy:(x,b)=>copy(QL.text,b),
 phone:async(x,b)=>{try{await window.Bridge?.sendToPhone?.(RES);flash(b,'Enviado')}catch(e){console.error('[Island] Error enviando texto al celular:',e);flash(b,'Sin conexión')}},
 phone2:async(x,b)=>{try{await window.Bridge?.sendToPhone?.(QL.text);flash(b,'Enviado')}catch(e){console.error('[Island] Error enviando texto al celular:',e);flash(b,'Sin conexión')}},
 'send-attached-phone':async(x,b)=>{
  const file=window.__attachedFile;
  if(!file)return;
  try{
   if(file.fileObj)await window.Bridge?.sendFile?.(file.fileObj);
   else if(file.filePath)await window.Bridge?.sendFileToPhonePath?.(file.filePath);
   else throw new Error('El archivo adjunto no tiene contenido disponible.');
   flash(b,'Listo');
  }catch(e){console.error('[Island] Error enviando archivo al celular:',e);flash(b,'Error')}
 },
 sum:()=>{window.Bridge?.chipAction?.('summarize',RES);buddy.setState('thinking');go('compact');},
 retry:()=>{if(!lastQ)return;if(window.Bridge?.sendChat)window.Bridge.sendChat(lastQ);buddy.setState('thinking');go('compact');},
 
 m:x=>{if(window.Bridge?.media)window.Bridge.media(x);else if(x=='toggle')music({playing:!MUS.playing})},
 vision:()=>go('tool_use',{label:'Analizando pantalla'}),cancel:()=>{window.Bridge?.cancel?.();go('compact')},
 unpair:(x,b)=>{window.Bridge?.unpairDevices?.();link(false);flash(b,'Listo')},
 cfgwin:()=>openSettings(),
 linkcfg:()=>openSettings('link',true),
 island_update:()=>{openSettings();try{window.Bridge?.checkUpdate?.()}catch(_){}},
 island_hide:()=>{
  if(scene==='boot'||scene==='intro')return;
  window.__suppress_hover_until = Date.now() + 1400;
  PIN=0;
  clearTimeout(hvT);
  clearTimeout(acT);
  window.__miku_paused=false;
  window.__miku_hidden=false;
  startFrameLoop();
  go('compact');
 },
 newcode:()=>{if(window.Bridge?.generatePairingUrl)window.Bridge.generatePairingUrl(true);else drawQR(PAIR)}
};
isl.addEventListener('click',e=>{
 if(e.target.closest('.dz')){
  let inp=$('#hidden_drop_picker');
  if(!inp){
   inp=document.createElement('input');inp.type='file';inp.id='hidden_drop_picker';inp.style.display='none';
   document.body.appendChild(inp);
   inp.addEventListener('change',async ev=>{
    const f=ev.target.files?.[0];
    if(f){
     FN=f.name;window.Bridge?.sendFile?.(f);
     QL={title:f.name,text:`Archivo seleccionado\n${f.name}\n${(f.size/1024).toFixed(1)} KB`};
     try{if(/^text|json/.test(f.type)||/\.(txt|md|json|csv|py|js|html)$/i.test(f.name))QL.text=(await f.text()).slice(0,1500)}catch(_){}
     eatFile(f,window.innerWidth/2,80);
    }
   });
  }
  inp.click();return;
 }
 if(e.target.closest('canvas.star')&&scene=='compact'){go('overview',{pg:1});return}
 const mascot=e.target.closest('.cs[data-a="agent-mascot-click"]');
 if(mascot&&getUnreadAgent()){ACT['agent-mascot-click']();return}
 if(e.target.closest('#mkw,.cs')){tap();return}
 const b=e.target.closest('[data-a]');if(b){const[a,...r]=b.dataset.a.split(':');ACT[a]?.(r.join(':'),b);return}
 if(SC[scene].m&&!e.target.closest('.bdg'))go('overview')});
document.addEventListener('input',e=>{if(e.target.id=='colin'){const a=curAg();if(a!==PRIN){if(usedBy(e.target.value,a)){e.target.value=a.c.toLowerCase();P.sq=.12;return}a.c=e.target.value;ls_save();applyTheme()}return}const k=e.target.dataset?.k;if(!k)return;const v=e.target.type=='checkbox'?e.target.checked:e.target.value;CFG[k]=v;window.Bridge?.setSetting?.(k,v);if(k=='voice')syncSpk();saveCfg()});

addEventListener('dragenter',e=>{e.preventDefault();wake();drag.on=1;if(scene!='drop'&&scene!='uploading'){bk0=scene;go('drop')}look(e)});
addEventListener('dragover',e=>{e.preventDefault();look(e)});
addEventListener('dragleave',e=>{if(!e.relatedTarget)drag.on=0;if(!e.relatedTarget&&scene=='drop')go(bk0=='drop'?'compact':bk0)});
// Tauri Drag & Drop Native Support
try{
 window.__TAURI__?.event?.listen('tauri://drag-enter',()=>{wake();drag.on=1;if(scene!='drop'&&scene!='uploading'){bk0=scene;go('drop')}});
 window.__TAURI__?.event?.listen('tauri://drag-leave',()=>{drag.on=0;if(scene=='drop')go(bk0=='drop'?'compact':bk0)});
 window.__TAURI__?.event?.listen('tauri://drag-drop',async ev=>{
  drag.on=0;const paths=ev.payload?.paths;
  if(paths&&paths.length){
   const p=paths[0],name=p.split(/[\/\\]/).pop();
   FN=name;QL={title:name,text:`Archivo: ${p}`};
   window.Bridge?.sendFilePath?.(p);
   const pos=ev.payload?.position||{};
   eatFile({name,path:p},pos.x||(window.innerWidth/2),pos.y||80);
  }else{go('compact')}
 });
}catch(_){}

addEventListener('drop',async e=>{e.preventDefault();look(e);drag.on=0;const f=e.dataTransfer.files[0];if(!f){go('compact');return}
 FN=f.name;window.Bridge?.sendFile?.(f);QL={title:f.name,text:`Archivo recibido\n${f.name}\n${(f.size/1024).toFixed(1)} KB · ${f.type||'tipo desconocido'}`};
 try{if(/^text|json/.test(f.type)||/\.(txt|md|json|csv|py|js|html)$/i.test(f.name))QL.text=(await f.text()).slice(0,1500)}catch{}
 eatFile(f,e.clientX,e.clientY)});
function eatFile(f,x,y){
 const q=isl.getBoundingClientRect(),sx=x-q.left,sy=y-q.top;
 const fName=f.name||'archivo';
 const ext=((fName.split('.').pop()||'').slice(0,4)||'file').toUpperCase();
 FN=fName;
 window.__attachedFile = { name: fName, size: f.size || 0, type: f.type || '', path: f.path || '' };
 if(f instanceof Blob){
  const reader=new FileReader();
  reader.onload=async()=>{
   try{
    const res=await window.Bridge?.uploadFile?.(fName,reader.result,false);
    QL={title:fName,text:res?.analysis||res?.preview||'Archivo cargado'};
   }catch(_){}
  };
  reader.readAsDataURL(f);
 }else if(f.path&&window.Bridge?.sendFilePath){
  window.Bridge.sendFilePath(f.path);
 }
 const el=document.createElement('div');el.className='eatf';el.innerHTML='<i></i><b>'+esc(ext)+'</b>';isl.appendChild(el);
 const T0=performance.now(),FLY=480,CLOSE=FLY+120,END=CLOSE+780;let gulped=0;
 EAT.ax=mxk;EAT.ay=myk;EAT.on=1;EAT.t0=T0;EAT.fx=sx;EAT.fy=sy;EAT.gx=0;EAT.gy=0;
 EAT.mo=()=>{const a=performance.now()-T0;if(a<FLY)return 1.05;if(a<CLOSE)return 1.05*(1-(a-FLY)/(CLOSE-FLY));
  if(a<END){const u=(a-CLOSE)/(END-CLOSE);return .06+.26*Math.abs(Math.sin(u*Math.PI*3))*(1-u*.5)}return 0};
 buddy.emote('eat',FLY+120,3);const dz=$('.dz b');if(dz)dz.textContent='Ñam…';
 const step=now=>{const a=now-T0,mxp=mxk,myp=myk+13*mkk;
  if(a<FLY){const u=a/FLY,e=u*u*(2.1*u-1.1),cx=(sx+mxp)/2,cy=Math.min(sy,myp)-40,i=1-e,
    X1=i*i*sx+2*i*e*cx+e*e*mxp,Y1=i*i*sy+2*i*e*cy+e*e*myp,sc=1-.78*Math.max(0,e),rot=-16*(1-e)+e*10,op=e>.84?1-(e-.84)/.16:1;
   EAT.fx=X1;EAT.fy=Y1;EAT.gx=clamp((X1-mxk)/80,-1,1);EAT.gy=clamp((Y1-myk)/60,-1,1);
   el.style.transform='translate('+X1+'px,'+Y1+'px) translate(-50%,-50%) rotate('+rot+'deg) scale('+sc+')';el.style.opacity=op}
  else if(!gulped){gulped=1;el.remove();P.sq=.26;P.sv=0;P.jv=-55;burst(.45);buddy.emote('chew',END-FLY,3);EAT.gx=0;EAT.gy=.25}
  if(a<END)requestAnimationFrame(step);else{EAT.on=0;el.remove();go('prompt')}};
 requestAnimationFrame(step)}
function upload(){let p=0;const i=setInterval(()=>{p=Math.min(100,p+4+Math.random()*7);const f=$('#fl');if(!f||scene!='uploading'){clearInterval(i);return}
 f.style.width=p+'%';$('#pc').textContent=(p|0)+' %';if(p>=100){clearInterval(i);go('choose')}},110)}

function drawQR(url){const cv=$('#qr');if(!cv)return;const ctx=cv.getContext('2d');cv.width=cv.height=288;ctx.fillStyle='#fff';ctx.fillRect(0,0,288,288);if(url){try{QR.draw(cv,url,288)}catch{}}const qu=$('#qu');if(qu)qu.textContent=PAIR_ERROR||url}
window.setPairQR=d=>{const i=new Image();i.onload=()=>{const cv=$('#qr');if(!cv)return;cv.width=cv.height=288;const ctx=cv.getContext('2d');ctx.imageSmoothingEnabled=false;ctx.fillStyle='#fff';ctx.fillRect(0,0,288,288);ctx.drawImage(i,0,0,288,288)};i.src=d};
window.setPairUrl=u=>{PAIR=u;PAIR_ERROR='';if($('#qr'))drawQR(u)};
window.setPairError=message=>{PAIR_ERROR=message;if($('#qu'))$('#qu').textContent=message};
window.setLinkStatus=(ok,name)=>{
 ST.link=ok?1:0;
 ST.name=name||'';
 const stEl=document.querySelector('.lkt .st');
 if(stEl){
  stEl.className='st '+(ok?'on':'');
  stEl.textContent=ok?('Conectado: '+esc(name||'Dispositivo')):'Desconectado';
 }
 const b=$('.bdg');if(b)b.innerHTML=BDG();
};
window.setMics=l=>{MICS=l.map(m=>[m.id||m,m.label||m])};
function link(ok,name=''){ST.link=ok;ST.name=name;emit({k:'link',ok:!!ok,name});const b=$('.bdg');if(b)b.innerHTML=BDG();if(scene=='settings'||scene=='link')tabs();
 if(ok)go('notify',{title:'Miku-Link',text:name+' conectado',emote:'happy',ms:3000})}
let bootReady=false,bootProgressTimer=null,bootReadyTimer=null,bootStartedAt=0;
function updateBootProgress(){
 const elapsed=performance.now()-bootStartedAt;
 const active=elapsed<1000?0:elapsed<2200?1:2;
 $$('.boot-step').forEach((step,index)=>{
  step.classList.toggle('is-done',index<active);
  step.classList.toggle('is-active',index===active);
 });
}
function startBootProgress(){
 clearInterval(bootProgressTimer);
 clearTimeout(bootReadyTimer);
 bootReady=false;
 bootStartedAt=performance.now();
 updateBootProgress();
 bootProgressTimer=setInterval(updateBootProgress,250);
}
function finishBoot(){
 if((scene!=='boot'&&scene!=='intro')||bootReady)return;
 bootReady=true;
 clearInterval(bootProgressTimer);
 const status=$('#bootStatus');
 if(status)status.textContent=tr('boot_connected');
 $$('.boot-step').forEach(step=>{step.classList.remove('is-active');step.classList.add('is-done')});
 buddy.emote('proud',1200,9);
 bootReadyTimer=setTimeout(()=>{
  if(scene==='boot'||scene==='intro'){
    window.__mikuBooting=false;
    LOCKI=0;
    go('overview',{__i:1});
  }
 },950);
}
window.feed=(a,b)=>{if(typeof a=='number'){const wx=window.screenX??window.screenLeft??0,wy=window.screenY??window.screenTop??0;look({clientX:a-wx,clientY:b-wy});return}const m=a||{};
 switch(m.type){
  case'miku_link_connected':link(true,m.name||m.device||'Teléfono');break;
  case'miku_link_disconnected':link(false);break;
  case'user_message':{
    const targetId=m.agent_id||'miku',ch=getAgChat(targetId),text=m.text||'';
    const alreadyActive=ch.busy&&ch.lastQ===text;
    if(!alreadyActive){
      ch.lastQ=text;
      ch.lastFile=null;
      ch.busy=true;
      ch.steps=[];
      ch.thinkStart=performance.now();
      ch.thinkDur=0;
      const exists=ch.history.some(item=>item.id===m.id);
      if(!exists&&ch.history.at(-1)?.content!==text)ch.history.push({id:m.id,role:'user',content:text});
      ch.unread=curAg().id!==targetId;
      saveAgChats();
    }
    if(curAg().id===targetId&&(scene==='prompt'||scene==='result'))go('prompt');
    break;
  }
  case'ws':
    ST.ws=!!m.ok;
    window.__mikuCoreConnected=ST.ws;
    $('#bws')?.classList.toggle('on',ST.ws);
    if((scene==='boot'||scene==='intro')&&ST.ws)finishBoot();
    else if((scene==='boot'||scene==='intro')&&!ST.ws){
      if(bootReady){bootReady=false;clearTimeout(bootReadyTimer);startBootProgress()}
      if($('#bootStatus'))$('#bootStatus').textContent='Iniciando el servidor...';
    }
    break;
  case'mic':ST.mic=!!m.on;$('#bmic')?.classList.toggle('on',ST.mic);break;
  case'state':
    if(m.name==='talking'||m.name==='listening'){
      if(curAg().id==='miku')buddy.setState(m.name);
    }else{
      buddy.setState(m.name);
    }
    break;
  case'emote':buddy.emote(m.name,m.ms);break;
  case'music':music(m);break;
  case'scene':
    if(m.name==='approve'){
      approve(m.args||m);
    }else if(m.name==='question'){
      question(m.args||m);
    }else if(m.name==='error_card'){
      errorCard(m.args||m);
    }else if((m.name==='prompt'||m.name==='result')&&curAg().id!=='miku'){
      /* No secuestrar la vista si el usuario está con otro agente */
    }else if(scene===m.name&&(m.name==='prompt'||m.name==='result')){
      /* Ya estamos en esta vista, evitar parpadeo o recarga innecesaria */
    }else{
      go(m.name,m.args||{});
    }
    break;
  case'ask':ask(m);break;
  case'question':question(m);break;
  case'approve':approve(m);break;
  case'error_card':errorCard(m);break;
  case'thought_stream':thoughtStream(m);break;
  case'miku_state':
    if(m.state)buddy.setState(m.state);
    if(m.thought)thoughtStream({text:m.thought,source:m.source||'hook',agent_id:'miku'});
    break;
  case'api':ST.api=!!m.ok;break;
  case'tasks':ST.tasks=+m.n||0;break;
  case'agent_reply':{
    const ch = getAgChat(m.agent_id);
    const isErr = !!(m.error || (m.text && (m.text.startsWith('Error') || m.text.includes('Error al contactar') || m.text.includes('Código del error'))));
    if (isErr) {
      if (ch.lastA && !ch.busy && !ch.lastA.startsWith('Error')) {
        return;
      }
      ch.busy = false;
      ch.thinkStart = 0;
      ch.lastA = m.text || 'Error al procesar la solicitud.';
      ch.history.push({ role: 'assistant', content: ch.lastA });
      saveAgChats();
      buddy.setState('error');
      buddy.emote('error', 2600, 3);
      try { window.SoundFX?.play?.('error'); } catch (_) {}
      if (curAg().id === m.agent_id && (scene === 'prompt' || scene === 'result')) {
        go('prompt');
      }
      return;
    }
    if (!ch.busy && ch.lastA === m.text) {
      return;
    }
    const wasBusy = ch.busy;
    ch.busy = false;
    if (wasBusy && ch.thinkStart) {
      ch.thinkDur = Math.max(1, Math.round((performance.now() - ch.thinkStart) / 1000));
    }
    ch.thinkStart = 0;
    ch.lastA = m.text;
    ch.history.push({ role: 'assistant', content: m.text });
    window.SoundFX?.receive?.();
    const isViewing = (curAg().id === m.agent_id && (scene === 'prompt' || scene === 'result'));
    if (isViewing) {
      ch.unread = false;
      saveAgChats();
      buddy.setState('idle');
      buddy.emote('happy', 1200);
      go('prompt');
    } else {
      if (m.agent_id === 'miku') {
        window.Bridge?.stopSpeaking?.();
      }
      ch.unread = true;
      saveAgChats();
      buddy.emote('happy', 900);
      if (scene === 'overview') renderOv();
      else if (scene === 'prompt' || scene === 'result') go(scene);
      else label();
    }
    break;
  }
  case'agent_tool_step':{
    const targetId = m.agent_id || curAg().id;
    const ch = getAgChat(targetId);
    if (!ch.steps) ch.steps = [];
    ch.steps.push(m);
    if (curAg().id === targetId && (scene === 'prompt' || scene === 'result')) {
      go('prompt');
    }
    break;
  }
  case'agent_busy':{
    const ch = getAgChat(m.agent_id);
    ch.busy = !!m.busy;
    saveAgChats();
    if (curAg().id === m.agent_id) {
      buddy.setState(ch.busy ? 'thinking' : 'idle');
    }
    if (scene === 'overview') renderOv();
    else if (scene === 'prompt' || scene === 'result') go(scene);
    break;
  }
  case'switch_agent_chat':{
    const id = m.agent_id;
    window.Bridge?.stopSpeaking?.();
    if (id === 'miku') {
      SELA = -1;
    } else {
      const idx = ST.agents.findIndex(x => x.id === id);
      if (idx >= 0) SELA = idx;
    }
    applyTheme();
    const target = curAg();
    const ch = getAgChat(target.id);
    buddy.setState(ch.busy ? 'thinking' : 'idle');
    wake();
    go('prompt');
    break;
  }
  case'agent_hook':{
    const agName = m.agent || 'Agente';
    const ev = m.event || 'Notification';
    const text = m.prompt || m.tool || '';
    if(ev === 'PermissionRequest'){
      approve({
        title: `¿Permitir a ${agName} ejecutar un comando?`,
        text: text || 'Ejecución de herramienta CLI'
      });
    } else if(ev === 'PreToolUse' || ev === 'UserPromptSubmit'){
      buddy.setState('working');
    } else if(ev === 'Stop'){
      buddy.setState('idle');
      buddy.emote('happy', 1400);
    }
    break;
  }
  case'wake':{
    SELA = -1;
    applyTheme();
    wake();
    go('prompt');
    try {
      if (window.__TAURI__?.window?.getCurrentWindow) {
        const w = window.__TAURI__.window.getCurrentWindow();
        w.unminimize?.();
        w.show?.();
        w.setFocus?.();
      }
    } catch (_) {}
    break;
  }
  case'agents':onMsg({k:'agents',list:m.list});break;
  case'ui_command':if(m.action==='show_scene'&&m.scene==='question'){const p=m.params||{};ask({title:p.title||'Pregunta de Miku',text:p.q||'',options:p.options||[]})}break;
  case'notify':go('notify',m)}};

const WARDROBE=[['none','Ninguno'],['beanie','Gorro'],['crown','Corona'],['party','Fiesta'],['santa','Santa'],['witch','Bruja'],['shades','Gafas sol'],['round','Gafas'],['bow','Moño'],['scarf','Bufanda'],['pumpkin','Calabaza'],['bunny','Orejas'],['halo','Aureola'],['propeller','Hélice'],['phones','Audífonos']];
const GAL=['ask','approve','idle','listening','thinking','talking','searching','working','happy','proud','wink','love','surprised','question','annoyed','sleeping','error','dizzy','look_up','look_down','look_left','look_right','squash','swallow','wave'];
function stagger(){col.querySelectorAll('.hd,.card.mk,.minis>*,.fld,.chips>*,.side>*,.hello>b,.hello>small,.strip>*,.gal>*,.acts>*').forEach((el,i)=>{el.style.animation=`up .6s var(--ease) ${70+i*32}ms backwards`})}
const OTP=new Map();function OTOP(o){o=o||'none';if(!OTP.has(o))OTP.set(o,avBox(o,'#fff').y);return OTP.get(o)}
function place(dt){const sl=$('.cs')||mkw,q=isl.getBoundingClientRect(),r=sl.getBoundingClientRect();if(!r.width){cv.style.opacity=0;return}cv.style.opacity=1;
 let k=+(sl.dataset.k||.4);let cx=r.left-q.left+r.width/2,cy=r.top-q.top+r.height/2;
 const chase=(drag.on||EAT.on)&&scene=='drop';
 if(!chase){const host=sl.closest('.card')||isl,hr=host.getBoundingClientRect(),mg=host===isl?1:4,top=hr.top-q.top+mg,bot=hr.bottom-q.top-mg,up=108-OTOP(OUT)/2,dn=40,full=(up+dn)*k;
  if(bot-top>8){if(full>bot-top)k=(bot-top)/(up+dn);cy=Math.min(Math.max(cy,top+up*k),bot-dn*k)}}if(chase){if(EAT.on){cx=EAT.ax;cy=EAT.ay}else{cx=clamp(drag.x-q.left,34,q.width-34);cy=clamp(drag.y-q.top-36,40,q.height-24)}}
 const ox=mxk,oy=myk,f=mi?1-Math.exp(-dt*10):1;mi=1;let wall=0;
 if(chase){const rx=EAT.on?EAT.fx:drag.x-q.left;wall=clamp((rx-cx)/160,-.3,.3);
  const fl=Math.sin(t*4.6)*3.2,sx=Math.sin(t*2.3)*2.2;
  CH.vx+=((cx+sx-mxk)*92-CH.vx*10.5)*dt;CH.vy+=((cy+fl-myk)*92-CH.vy*10.5)*dt;mxk+=CH.vx*dt;myk+=CH.vy*dt}
 else{mxk+=(cx-mxk)*f;myk+=(cy-myk)*f;CH.vx=(mxk-ox)/Math.max(dt,.001);CH.vy=(myk-oy)/Math.max(dt,.001)}
 mkk+=(k-mkk)*f;
 const lean=clamp(CH.vx*(chase?.0016:.0006),-.42,.42)+wall+(chase?Math.sin(t*3.1)*.045:0),kr=1-Math.exp(-dt*(chase?13:9));
 CH.rot+=(lean-CH.rot)*kr;
 const sp=Math.hypot(CH.vx,CH.vy),str=clamp(-CH.vy*(chase?.00042:.0002),-.16,.2)+Math.min(.07,sp*(chase?.00012:.00004));
 CH.sy+=((1+str)-CH.sy)*kr;const sy=CH.sy,sx2=1/Math.sqrt(sy)*(1+clamp(Math.abs(CH.vx)*.00012,0,.08));
 cv.style.transform=`translate(${mxk}px,${myk}px) rotate(${CH.rot.toFixed(4)}rad) scale(${(mkk*sx2).toFixed(4)},${(mkk*sy).toFixed(4)}) translate(-100px,-108px)`}
const CH={vx:0,vy:0,rot:0,sy:1};
const wp=$('#warp'),wx=wp.getContext('2d'),WP={on:0,t0:0,k:1};
const RG=[.08,.18,.29,.40,.52].map(t0=>({t0,d:Array.from({length:72},()=>({a:Math.random()*6.283,j:(Math.random()-.5)*.24,s:.7+Math.random()*.8,al:.35+Math.random()*.5}))}));
const SK=Array.from({length:18},(_,i)=>({a:i/18*6.283+(Math.random()-.5)*.35,sp:190+Math.random()*190,len:6+Math.random()*8,t0:.06+Math.random()*.16}));
function burst(k=1){WP.on=1;WP.t0=performance.now();WP.k=k}
function warpDraw(dt,now){if(!WP.on)return;const W=isl.offsetWidth,H=isl.offsetHeight;if(!W)return;
 if(wp.width!=W*2||wp.height!=H*2){wp.width=W*2;wp.height=H*2;wp.style.width=W+'px';wp.style.height=H+'px'}
 wx.setTransform(2,0,0,2,0,0);wx.clearRect(0,0,W,H);const age=(now-WP.t0)/1000,cx=mxk,cy=myk,mr=Math.min(W*.55,260),sg=(a,b)=>Math.max(0,Math.min(1,(age-a)/(b-a)));
 for(const r of RG){const k=sg(r.t0,r.t0+1.3);if(k<=0||k>=1)continue;const e=1-Math.pow(1-k,3),rx=14+(mr-14)*e,ry=rx*.38,f=(1-k)*Math.min(1,k/.08)*WP.k;
  for(const d of r.d){wx.fillStyle=`rgba(255,255,255,${(d.al*f).toFixed(3)})`;wx.fillRect(cx+Math.cos(d.a)*rx*(1+d.j),cy+Math.sin(d.a)*ry*(1+d.j),d.s,d.s)}}
 wx.lineCap='round';wx.lineWidth=1.5;
 for(const t of SK){const k=sg(t.t0,t.t0+.6);if(k<=0||k>=1)continue;const d=t.sp*(1-Math.pow(1-k,3))*.8+12;wx.strokeStyle=`rgba(128,196,255,${((1-k)*.8*WP.k).toFixed(3)})`;wx.beginPath();wx.moveTo(cx+Math.cos(t.a)*(d-t.len),cy+Math.sin(t.a)*d*.5);wx.lineTo(cx+Math.cos(t.a)*d,cy+Math.sin(t.a)*d*.5);wx.stroke()}
 if(age>1.9){WP.on=0;wx.clearRect(0,0,W,H)}}
function postUiDecision(id, decision, extra = {}) {
  try {
    window.Bridge?.choice?.(id, decision);
  } catch (_) {}
  try {
    fetch('/api/ui/choice', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id: id || 'active', decision: String(decision), extra })
    }).catch(() => {});
  } catch (_) {}
}
let ASKR,ASKID;
window.ask=o=>new Promise(r=>{
  ASKR=r;
  ASKID=o?.id||'question';
  LOCKI=0;
  go('question',{
    __i: 1,
    id: ASKID,
    title: o?.title || 'Pregunta de Miku',
    sub: o?.sub || o?.text || '',
    options: (o?.options && o.options.length) ? o.options : ['Sí, continuar', 'No, cancelar'],
    emote: 'question'
  });
});
const ask = window.ask;
const question = window.ask;
window.question = window.ask;

ACT.pick=x=>{
  const v=x=='Ahora no'?null:x;
  ASKR&&ASKR(v);
  ASKR=null;
  postUiDecision(ASKID, v || 'cancel');
  go('compact');
  if(v)buddy.emote('happy',1200);
};
window.approve=o=>new Promise(r=>{
  ASKR=r;
  ASKID=o?.id||'approve';
  LOCKI=0;
  go('approve',{...(o||{}),__i:1,emote:'question'});
});
const approve = window.approve;

function errorCard(o={}) {
  LOCKI=0;
  buddy.setState('error');
  buddy.emote('error', 2400, 3);
  go('error_card', { ...(o||{}), __i: 1, emote: 'error' });
}
window.errorCard = errorCard;

function thoughtStream(m={}) {
  const targetId = m.agent_id || curAg().id || 'miku';
  const ch = getAgChat(targetId);
  if (!ch.steps) ch.steps = [];
  ch.steps.push({
    tool: m.source || 'hook',
    status: m.state || 'working',
    detail: m.step || m.text || 'Procesando...',
    diff: m.diff || '',
    file: m.file || ''
  });
  if (m.state) buddy.setState(m.state);
  if (scene === 'prompt' || scene === 'result') go(scene);
}
window.thoughtStream = thoughtStream;
ACT.apok=()=>{
  ASKR&&ASKR('allow');
  ASKR=null;
  postUiDecision(ASKID, 'allow');
  go('compact');
  buddy.emote('happy',1200);
};
ACT.denyap=()=>{
  ASKR&&ASKR('deny');
  ASKR=null;
  postUiDecision(ASKID, 'deny');
  go('compact');
};
ACT.apalways=()=>{
  ASKR&&ASKR('always');
  ASKR=null;
  postUiDecision(ASKID, 'always');
  go('compact');
  buddy.emote('proud',1300);
};
ACT.errretry=cmd=>{
  if(cmd&&window.Bridge?.sendChat){
    window.Bridge.sendChat(`Reintenta este comando y corrige el fallo: ${cmd}`, curAg());
  }
  buddy.setState('thinking');
  go('prompt');
};
ACT.tg=k=>{CFG[k]=!CFG[k];window.Bridge?.setSetting?.(k,!!CFG[k]);$$('[data-a="tg:'+k+'"]').forEach(b=>b.classList.toggle('on',!!CFG[k]))};
ACT.pers=k=>{CFG.personality=k;window.Bridge?.setSetting?.('personality',k);$$('[data-a^="pers:"]').forEach(b=>b.classList.toggle('on',b.dataset.a=='pers:'+k))};
ACT.ac=v=>{CFG.autoclose=+v;window.Bridge?.setSetting?.('autoclose',+v);armAC();if(scene=='settings')go('settings')};
ACT.tails=()=>{TAILS=!TAILS;try{localStorage.setItem('miku_tails',TAILS?'1':'0')}catch{}$$('[data-a="tails:1"]').forEach(b=>b.classList.toggle('on',TAILS))};
ACT.wear=k=>{OUT=k;try{localStorage.setItem('miku_outfit',k)}catch{}$$('.wd button').forEach(b=>b.classList.toggle('on',b.dataset.a=='wear:'+k));buddy.emote('happy',1100)};
function openSettings(section = null, keepIslandOpen = false){
  if (section) {
    try { localStorage.setItem('miku_cat', JSON.stringify(section)); } catch (_) {}
    emit({ k: 'go_cat', cat: section });
  }
  try {
    if (window.parent && window.parent !== window && window.parent.document && window.parent.document.getElementById('ajustes')) {
      window.parent.document.getElementById('ajustes').scrollIntoView({ behavior: 'smooth', block: 'center' });
      if (!keepIslandOpen) go('compact');
      return;
    }
  } catch (_) {}

  if(window.Bridge?.openSettings){
    window.Bridge.openSettings(section);
  } else if(window.__TAURI__?.core?.invoke){
    const cmd = section === 'link' ? 'open_link_window' : 'open_settings_window';
    window.__TAURI__.core.invoke(cmd).catch(()=>{
      window.__TAURI__.core.invoke('open_settings_window').catch(()=>{
        openSettingsFallback(section);
      });
    });
  } else if(window.pywebview?.api?.open_settings){
    window.pywebview.api.open_settings();
  } else {
    openSettingsFallback(section);
  }
  if (!keepIslandOpen) go('compact');
}

function openSettingsFallback(section = null) {
  try {
    if (window.parent && window.parent !== window && window.parent.document && window.parent.document.getElementById('ajustes')) {
      window.parent.document.getElementById('ajustes').scrollIntoView({ behavior: 'smooth', block: 'center' });
      return;
    }
  } catch (_) {}

  let base = '';
  try {
    if (window.parent && window.parent !== window && window.parent.location.href && !window.parent.location.href.startsWith('about:')) {
      base = window.parent.location.href;
    }
  } catch (_) {}
  if (!base || base.startsWith('about:')) {
    base = (location.href && !location.href.startsWith('about:')) ? location.href : window.location.origin;
  }
  base = base.split('?')[0].split('#')[0];
  if (base.endsWith('.html')) {
    base = base.substring(0, base.lastIndexOf('/') + 1);
  } else if (!base.endsWith('/')) {
    base += '/';
  }
  const isIsland = location.pathname.includes('/island');
  const hash = section ? `#${section}` : '';
  const target = (isIsland ? 'island/miku_settings.html' : 'miku_settings.html') + hash;
  const finalUrl = new URL(target, base).href;
  window.open(finalUrl, 'miku_settings', 'width=1080,height=780');
}
const BC=window.BroadcastChannel?new BroadcastChannel('miku'):null,emit=m=>{try{BC?.postMessage(m)}catch{}try{window.__TAURI__?.event?.emit('miku',m)}catch{}};
const saveCfg=()=>{try{localStorage.setItem('miku_cfg',JSON.stringify(CFG))}catch{}emit({k:'cfg',cfg:CFG})};
function syncSpk(){$$('.spk').forEach(b=>b.innerHTML=ic(CFG.voice?'speaker':'speaker-off'));$$('input[data-k="voice"]').forEach(i=>i.checked=!!CFG.voice)}
ACT.mute=()=>{CFG.voice=CFG.voice?0:1;window.Bridge?.setSetting?.('voice',!!CFG.voice);syncSpk();saveCfg()};
ACT.cfgwin=()=>openSettings();
ACT.linkcfg=()=>openSettings('link',true);
ACT.newcode=()=>{if(window.Bridge?.generatePairingUrl)window.Bridge.generatePairingUrl(true);else drawQR(PAIR)};
const PRESET=['#F2A765','#F06CF0','#6C63FF','#FF5C66','#4FD3B1','#3B9EFF','#FFD84D','#9BE15D'];
const OL={none:'Ninguno',beanie:'Gorro',crown:'Corona',party:'Fiesta',santa:'Santa',witch:'Bruja',shades:'Gafas de sol',round:'Gafas',bow:'Moño',scarf:'Bufanda',pumpkin:'Calabaza',bunny:'Orejas',halo:'Aureola',propeller:'Hélice',phones:'Audífonos'};
const ls_save=()=>{try{localStorage.setItem('miku_agents',JSON.stringify(ST.agents))}catch{}emit({k:'agents',list:ST.agents});pushImgs();window.Bridge?.saveAgentsBackend?.(ST.agents)};
const saveAgents=()=>{try{localStorage.setItem('miku_agents',JSON.stringify(ST.agents))}catch{}emit({k:'agents',list:ST.agents});pushImgs();window.Bridge?.saveAgentsBackend?.(ST.agents)};
let piT;const imgsMsg=()=>{const o={miku:snap(PRIN.c,PRIN.outfit||'none','full')};ST.agents.forEach(a=>{o[a.id]=snap(a.c,a.outfit||'none','full')});return{k:'imgs',imgs:o}};
function pushImgs(){clearTimeout(piT);piT=setTimeout(()=>{try{emit(imgsMsg())}catch{}},120)}
const selMsg=()=>({k:'select',who:SELA<0?'miku':(ST.agents[SELA]||{}).id||'miku'});
function setOutfit(a,k,silent){a.outfit=k;
 if(a===PRIN){try{localStorage.setItem('miku_outfit',k)}catch{}if(!silent)emit({k:'outfit',who:'miku',v:k});pushImgs()}
 else if(silent){try{localStorage.setItem('miku_agents',JSON.stringify(ST.agents))}catch{}}else saveAgents();
 if(a===curAg())OUT=k}
ACT.wear=k=>{setOutfit(curAg(),k);$$('.wb').forEach(b=>b.classList.toggle('on',b.dataset.a=='wear:'+k));const n=$('#wn');if(n)n.textContent=OL[k]||k;buddy.emote('happy',1100)};
ACT.color=h=>{const a=curAg();if(a===PRIN)return;if(usedBy(h,a)){P.sq=.12;return}a.c=h;saveAgents();applyTheme();col.innerHTML=SC.wardrobe.x();fit();P.sq=.2;P.sv=0;P.jv=-70;buddy.emote('happy',900)};
ACT['agent-mascot-click']=()=>{
  const unreadAg = getUnreadAgent();
  if (unreadAg) {
    const idx = unreadAg.id === 'miku' ? -1 : ST.agents.findIndex(x => x.id === unreadAg.id);
    SELA = idx;
    getAgChat(unreadAg.id).unread = false;
    saveAgChats();
    applyTheme();
    go('prompt');
  }
};
ACT.agent=x=>{
  const i=+x;
  SELA=i;
  const current=curAg();
  getAgChat(current.id).unread=false;
  saveAgChats();
  applyTheme();
  emit(selMsg());
  P.sq=.2;P.sv=0;P.jv=-70;
  buddy.emote('happy',800);
  if(scene==='overview'){
    renderOv();
  } else if(scene==='prompt'||scene==='result'){
    go(scene);
  } else {
    go('prompt');
  }
};
function onMsg(m){if(!m)return;
 if(m.k=='lang'||(m.k=='cfg'&&m.cfg?.lang)){
   const nl=m.lang||m.cfg.lang;
   if(nl&&CFG.lang!==nl){
     CFG.lang=nl;
     try{localStorage.setItem('miku_cfg',JSON.stringify(CFG))}catch(_){}
     updateIslandLang();
   }
 }
 if(m.k=='cfg'){Object.assign(CFG,m.cfg);syncSpk();armAC()}
 else if(m.k=='outfit'){const a=(!m.who||m.who=='miku')?PRIN:ST.agents.find(x=>x.id==m.who);if(a){setOutfit(a,m.v,true);if(scene=='wardrobe')go('wardrobe');if(a===curAg())buddy.emote('happy',1100)}}
 else if(m.k=='emote'){m.n.startsWith('look_')?buddy.look(m.n.slice(5),2200):buddy.emote(m.n,2200,4)}
 else if(m.k=='agents'){ST.agents=normIsl(m.list||[]);if(SELA>=ST.agents.length)SELA=-1;applyTheme();pushImgs();if(scene=='overview'){renderOv()}}
 else if(m.k=='select'){SELA=m.who=='miku'?-1:ST.agents.findIndex(x=>x.id==m.who);applyTheme();if(scene=='overview'){renderOv()}else if(scene=='wardrobe')go('wardrobe')}
 else if(m.k=='pair'){PAIR=m.url;try{localStorage.setItem('miku_pair',m.url)}catch{}if(scene=='link')drawQR(m.url)}
 else if(m.k=='unpair'){window.Bridge?.unpairDevices?.();link(false)}
 else if(m.k=='hello'){emit({k:'link',ok:!!ST.link,name:ST.name});emit({k:'agents',list:ST.agents});emit({k:'outfit',who:'miku',v:PRIN.outfit||'none'});emit({k:'cfg',cfg:CFG});emit({k:'theme',c:curAg().c});emit(selMsg());pushImgs()}}
document.addEventListener('change',e=>{if(e.target.id=='colin'&&scene=='wardrobe'){col.innerHTML=SC.wardrobe.x();fit()}});
let WBACK='overview';
const WOK=['compact','overview','prompt','settings','link','gallery','result','quicklook'];
isl.addEventListener('contextmenu',e=>{if(e.target.closest('input,select,textarea'))return;e.preventDefault();wake();
 if(scene=='wardrobe'){if(e.target.closest('#mkw,.cs'))go(WBACK);return}
 const p=e.target.closest('.pill,.mgc');if(p){const i=+p.dataset.a.split(':')[1];WBACK=WOK.includes(scene)?scene:'overview';if(SELA!=i)ACT.agent(i);go('wardrobe');return}
 if(e.target.closest('#mkw,.cs')){WBACK=WOK.includes(scene)?scene:'overview';go('wardrobe')}});
if(BC)BC.onmessage=e=>onMsg(e.data);
try{window.__TAURI__?.event?.listen('miku',e=>onMsg(e.payload))}catch{}
try{Object.assign(CFG,JSON.parse(localStorage.getItem('miku_cfg')||'{}'));updateIslandLang()}catch{}
try{
  let a=JSON.parse(localStorage.getItem('miku_agents'));
  if(Array.isArray(a)&&a.length){
    a=a.filter(x=>x.id==='github'||x.id==='antigravity');
    if(a.length>=2){
      const gh=a.find(x=>x.id==='github');if(gh){gh.name='GitHub';gh.c=gh.c||'#39D353';gh.outfit=gh.outfit||'shades';}
      const ag=a.find(x=>x.id==='antigravity');if(ag){ag.name='Antigravity';ag.c=ag.c||'#00D2FF';ag.outfit=ag.outfit||'crown';}
      ST.agents=a;
    }else ST.agents=[...DEFAULT_AGENTS];
  }else ST.agents=[...DEFAULT_AGENTS];
}catch{ST.agents=[...DEFAULT_AGENTS]}
try{const p=localStorage.getItem('miku_pair');if(p)PAIR=p}catch{}
setTimeout(()=>{window.Bridge?.syncLinkStatus?.()},1200);
let acT;function armAC(){clearTimeout(acT);if(!SC[scene].m&&!KEEP.includes(scene)&&scene!=='boot'&&scene!=='intro'&&window.__mikuCoreConnected&&!(scene=='notify'&&ASKR))acT=setTimeout(collapse,CFG.autoclose*1000)}
isl.addEventListener('pointermove',armAC);addEventListener('keydown',armAC);
ACT.pg=x=>{PG=((PG+(+x))%2+2)%2;renderOv()};
isl.addEventListener('pointermove',e=>{const s=e.target.closest?.('canvas.star');if(s){const r=s.getBoundingClientRect();s._hx=(e.clientX-r.left)/r.width;s._hy=(e.clientY-r.top)/r.height;s._hv=performance.now()}});
triggerStarLoop();
let PIN=0,hvT;
isl.addEventListener('pointerenter',()=>{if(Date.now()<(window.__suppress_hover_until||0))return;clearTimeout(hvT);if(scene=='compact')PIN=0;if(CFG.hover_open&&!drag.on&&scene=='compact'){wake();go('overview',{pg:HS?1:0})}});
isl.addEventListener('pointerleave',()=>{window.__suppress_hover_until=0;clearTimeout(hvT);if(!CFG.hover_open||PIN||scene==='boot'||scene==='intro'||!window.__mikuCoreConnected)return;
 hvT=setTimeout(()=>{if(!PIN&&scene!='compact'&&!KEEP.includes(scene)&&scene!=='boot'&&scene!=='intro'&&window.__mikuCoreConnected&&!(scene=='notify'&&ASKR))go('compact')},700)});
isl.addEventListener('pointerdown',()=>{if(CFG.hover_open)PIN=1});

/* ── extras v6 ── */
const cW=()=>{
  if(base!='idle'&&base!='sleeping'){
    let w=260;
    if(typeof HAS_UPD!=='undefined'&&HAS_UPD)w+=96;
    if(MUS.playing)w+=64;
    return w;
  }
  let w=128;
  if(typeof HAS_UPD!=='undefined'&&HAS_UPD)w+=96;
  if(MUS.playing)w+=64;
  return w;
};

setTimeout(async()=>{
  try{
    const upd=await window.Bridge?.checkUpdate?.();
    if(upd&&upd.available){
      HAS_UPD=1;
      label();
    }
  }catch(_){}
  try{
    const ags=await window.Bridge?.getAgents?.();
    if(ags&&Array.isArray(ags)&&ags.length){
      const clean=ags.filter(x=>x.id==='github'||x.id==='antigravity');
      if(clean.length){
        ST.agents=clean;
        applyTheme();
        renderOv();
      }
    }
  }catch(_){}
},2000);
let HS=0;
['pointerdown','click','contextmenu','wheel','keydown','dblclick'].forEach(t=>document.addEventListener(t,e=>{if(LOCKI&&(t=='keydown'||isl.contains(e.target))){e.stopImmediatePropagation();e.preventDefault()}},true));
isl.addEventListener('pointerover',e=>{HS=!!e.target.closest?.('canvas.star')});
isl.addEventListener('click',e=>{if(e.target.closest('canvas.star')&&scene=='compact'){PIN=1;go('overview',{pg:1})}});
/* selector magnético (port de MagneticSelect.tsx): el elegido se hincha y empuja al resto en radial */
const MAG={last:null,
 pts:n=>n>=3?[[0,-26],[22.5,13],[-22.5,13]]:n==2?[[-22.5,0],[22.5,0]]:[[0,0]],
 field(n,at){const P=MAG.pts(n),C=44,PD=22,PITCH=45,p=.55,grow=1.16+.22*p,room=C*(grow-1)/2,aura=3+9*p,cower=.04+.09*p,tilt=5*p,
  xs=P.map(q=>q[0]),ys=P.map(q=>q[1]),mx=Math.min(...xs),my=Math.min(...ys);
  return{W:Math.max(...xs)-mx+C+PD*2,H:Math.max(...ys)-my+C+PD*2,c:P.map(([px,py],i)=>{const L=px-mx+PD,T=py-my+PD;
   if(at==null||at>=n)return{L,T,x:0,y:0,s:1,r:0,far:0};
   const[ax,ay]=P[at],dx=px-ax,dy=py-ay,g=Math.hypot(dx,dy),far=g/PITCH,on=i==at,fall=on?0:Math.exp(-(far-1)/2.8),push=on?0:room+aura,ux=g?dx/g:0,uy=g?dy/g:0;
   return{L,T,x:ux*push,y:uy*push,s:on?grow:1-cower*fall,r:ux*tilt*fall,far}})}},
 mount(){const h=$('#mgh');if(!h)return;const IX=ISLN(),n=IX.length,k=IX.indexOf(SELA),a=k<0?null:k,pv=MAG.last&&MAG.last.n==n?MAG.last.at:a,ch=[...h.children],
  ap=(at,an)=>{const F=MAG.field(n,at);ch.forEach((el,i)=>{const q=F.c[i];el.style.transition=an?'':'none';el.style.transitionDelay=an?(q.far*22)+'ms':'0ms';
   el.style.transform=`translate(${q.x}px,${q.y}px) rotate(${q.r}deg) scale(${q.s})`;if(an)el.toggleAttribute('data-on',i==a)})};
  ap(pv,0);void h.offsetWidth;ap(a,1);MAG.last={n,at:a};
  if(matchMedia('(prefers-reduced-motion: reduce)').matches)return;
  const card=h.parentElement,F=MAG.field(n,a),R=Math.max(1,...F.c.map(q=>Math.hypot(q.L+22+q.x-F.W/2,q.T+22+q.y-F.H/2)+22)),
  lean=(x,y)=>ch.forEach(el=>{el.firstChild.style.setProperty('--lx',x.toFixed(2)+'px');el.firstChild.style.setProperty('--ly',y.toFixed(2)+'px')});
  card.onpointermove=e=>{const b=h.getBoundingClientRect(),z=b.width/(h.offsetWidth||b.width)||1,dx=(e.clientX-b.left)/z-F.W/2,dy=(e.clientY-b.top)/z-F.H/2,d=Math.hypot(dx,dy),
   m=Math.min(1,d/R)*(d<=R?1:Math.max(0,1-(d-R)/44))*4.5;lean(d?dx/d*m:0,d?dy/d*m:0)};
  card.onpointerleave=()=>lean(0,0)}};
function MAGH(IX,A){const F=MAG.field(IX.length,null);
 return `<div class="mg" id="mgh" style="width:${F.W}px;height:${F.H}px">${IX.map((i,k)=>{const sel=i==SELA,g=sel?PRIN:A[i],q=F.c[k];
  return `<button class="mgc" data-a="agent:${i}" style="--pc:${g.c};--d:${A[i].active?'#2dd4a0':'#ff6b5e'};left:${q.L}px;top:${q.T}px" title="${sel?'Volver a '+esc(PRIN.name):esc(g.name)}"><span class="mgs">${avt(g.c,g.outfit||'none',i,g.active)}</span><span class="nm">${esc(sel?PRIN.name:g.name)}</span></button>`}).join('')}</div>`}

/* ── transición fluida agentes ⇄ música ── */
let PGB=0;
ACT.pgto=x=>{const target=+x;if(target===PG)return;ACT.pg(target-PG);};
ACT.pg=x=>{const d=+x;if(!d||PGB)return;PGB=1;
 try{
  const from=PG;PG=((PG+d)%2+2)%2;
  const card=$('.ovp'),row=$('.two.h2'),th=$('.pth');
  if(scene!='overview'||!card||!row){renderOv();PGB=0;return;}
  window.SoundFX?.tab?.();
  const dir=d>0?1:-1,E='cubic-bezier(.32,.72,0,1)',body=card.firstElementChild,h0=row.offsetHeight;
  if(th){const a=from*15,b=PG*15,lo=Math.min(a,b);
   th.animate([{transform:`translateX(${a}px)`,width:'7px'},{transform:`translateX(${lo}px)`,width:(7+Math.abs(b-a))+'px',offset:.45},{transform:`translateX(${b}px)`,width:'7px'}],{duration:440,easing:E});
   th.style.transform=`translateX(${b}px)`;}
  if(body){
   body.animate([{opacity:1,transform:'none'},{opacity:0,transform:`translateX(${-16*dir}px) scale(.97)`}],{duration:150,easing:'ease-in',fill:'forwards'}).finished.then(()=>{
    try{
     const t=document.createElement('template');t.innerHTML=SC.overview.x();
     const newOvp=t.content.querySelector('.ovp');
     const nb=newOvp?newOvp.firstElementChild:null;
     if(nb&&body.parentNode===card){
      card.replaceChild(nb,body);
      nb.animate([{opacity:0,transform:`translateX(${16*dir}px) scale(.97)`},{opacity:1,transform:'none'}],{duration:320,easing:E,fill:'backwards'});
     }else{
      renderOv();
     }
     if(PG==1){PLY=mkSound($('#snh'),{get:()=>MUS,act:x=>ACT.m(x)});PLV=Slosh($('#vlr'),{value:MUS.vol,label:'Volumen',onChange:v=>setVol(v)});}
    }catch(e){console.warn("[ACT.pg error]",e);renderOv();}
    finally{PGB=0;fit();}
   }).catch(()=>{renderOv();PGB=0;});
  }else{renderOv();PGB=0;}
 }catch(err){console.warn("[ACT.pg uncaught]",err);renderOv();PGB=0;}
};
const urlP = new URLSearchParams(location.search);
if (urlP.get('ag')) {
  const agName = urlP.get('ag');
  const foundIdx = ST.agents.findIndex(x => x.id === agName);
  if (foundIdx >= 0) SELA = foundIdx;
}
applyTheme();isl.style.width='120px';isl.style.height='30px';
window.__mikuBooting=!location.hash;
window.__mikuCoreConnected=false;
startFrameLoop();
const requestedScene=location.hash?location.hash.slice(1):'boot';
LOCKI=(requestedScene==='intro'||requestedScene==='boot')?1:0;
setTimeout(()=>{
  go(requestedScene,{__i:1});
  if((requestedScene==='boot'||requestedScene==='intro')&&window.__mikuCoreConnected)finishBoot();
},250);

try {
  window.__TAURI__?.event?.listen?.('miku-power-save', e => {
    const isLow = !!e.payload;
    window.__miku_paused = isLow;
    if (isLow) {
      stopFrameLoop();
      if (loopRaf) { cancelAnimationFrame(loopRaf); loopRaf = null; }
    } else {
      startFrameLoop();
      if (!loopRaf) loopRaf = requestAnimationFrame(tickLoop);
    }
  });
} catch (_) {}

document.addEventListener('visibilitychange', () => {
  if (document.hidden) {
    window.__miku_hidden = true;
    stopFrameLoop();
  } else {
    window.__miku_hidden = false;
    if (!window.__miku_paused) {
      startFrameLoop();
      if (!loopRaf) loopRaf = requestAnimationFrame(tickLoop);
    }
  }
});

function initLiquidMenu(){
  // 1. Selector de agente en el chat
  const agPill = document.getElementById('agChatPill');
  const agDd = document.getElementById('agChatDropdown');
  if (agPill && agDd && !agPill._inited) {
    agPill._inited = true;
    agPill.onclick = (e) => {
      e.preventDefault();
      e.stopPropagation();
      const open = agDd.style.display === 'block';
      agDd.style.display = open ? 'none' : 'block';
    };
    agDd.querySelectorAll('[data-switch-ag]').forEach(btn => {
      btn.onclick = (e) => {
        e.preventDefault();
        e.stopPropagation();
        const id = btn.dataset.switchAg;
        agDd.style.display = 'none';
        window.Bridge?.stopSpeaking?.();
        if (id === 'miku') {
          SELA = -1;
        } else {
          const idx = ST.agents.findIndex(x => x.id === id);
          if (idx >= 0) SELA = idx;
        }
        applyTheme();
        const target = curAg();
        const ch = getAgChat(target.id);
        buddy.setState(ch.busy ? 'thinking' : 'idle');
        renderOv();
        go('prompt');
      };
    });
  }

  // 1.5 Paleta rápida de comandos "/" en el input #q
  const qInput = document.getElementById('q');
  const cmdPop = document.getElementById('cmdPalettePop');
  if (qInput && cmdPop && !qInput._cmdInited) {
    qInput._cmdInited = true;

    function getSlashOptions() {
      const options = [];
      // Dynamic agents from ST.agents
      (ST.agents || []).forEach(ag => {
        options.push({
          cmd: `/${ag.id}`,
          agentId: ag.id,
          name: ag.name,
          desc: `Delegar tarea a ${ag.name} (${ag.role})`,
          isAgent: true,
          color: ag.c || '#38bdf8'
        });
      });
      // System commands
      options.push(
        { cmd: '/update', desc: 'Ver tarjeta de actualización de Miku', isAgent: false },
        { cmd: '/mcp', desc: 'Abrir catálogo online de servidores MCP con descarga', isAgent: false },
        { cmd: '/skills', desc: 'Ver y descargar Skills nativas de Miku', isAgent: false },
        { cmd: '/spotify', desc: 'Abrir reproductor multimedia con audio ducking', isAgent: false },
        { cmd: '/settings', desc: 'Abrir panel de configuración y ajustes', isAgent: false }
      );
      return options;
    }

    qInput.addEventListener('input', () => {
      const val = (qInput.value || '').trimStart();
      if (!val.startsWith('/')) {
        cmdPop.style.display = 'none';
        return;
      }
      const rawQ = val.slice(1).toLowerCase();
      const allOpts = getSlashOptions();
      // Fuzzy tolerant matching: query is substring of cmd, name, or desc
      const matches = allOpts.filter(item => {
        const c = item.cmd.toLowerCase().slice(1);
        const n = (item.name || '').toLowerCase();
        return c.includes(rawQ) || n.includes(rawQ) || rawQ.split('').every(ch => c.includes(ch));
      });

      if (!matches.length) {
        cmdPop.style.display = 'none';
        return;
      }

      cmdPop.innerHTML = matches.slice(0, 7).map((m, idx) => `
        <button type="button" class="cmd-palette-item ${idx === 0 ? 'active' : ''}" data-slash="${esc(m.cmd)}" data-is-agent="${m.isAgent ? '1' : '0'}" data-agent-id="${esc(m.agentId || '')}">
          <span class="cmd-palette-cmd" style="${m.color ? `color:${m.color}` : ''}">${esc(m.cmd)}</span>
          <span class="cmd-palette-desc">${esc(m.desc)}</span>
        </button>
      `).join('');
      cmdPop.style.display = 'block';

      cmdPop.querySelectorAll('[data-slash]').forEach(btn => {
        btn.onclick = ev => {
          ev.preventDefault();
          ev.stopPropagation();
          const isAg = btn.dataset.isAgent === '1';
          const agId = btn.dataset.agentId;
          const sc = btn.dataset.slash;
          cmdPop.style.display = 'none';

          if (isAg && agId) {
            // Set prompt to /agent_id and focus
            qInput.value = `/${agId} `;
            qInput.focus();
            window.SoundFX?.play?.('pop');
          } else {
            qInput.value = '';
            if (sc === '/update') go('update_card');
            else if (sc === '/settings') openSettings();
            else if (sc === '/mcp') openSettings('mcp');
            else if (sc === '/skills') openSettings('skills');
            else if (sc === '/spotify') go('overview', { pg: 1 });
          }
        };
      });
    });
  }

  // 2. Menu liquido + del chat
  const stages = document.querySelectorAll('.crt-stage');
  stages.forEach(stage => {
    const pill = stage.querySelector('.crt-pill');
    const panel = stage.querySelector('.crt-panel');
    if (!pill || !panel || pill._inited) return;
    pill._inited = true;
    pill.onclick = e => {
      e.preventDefault();
      e.stopPropagation();
      const open = panel.classList.toggle('open');
      pill.classList.toggle('open', open);
      pill.setAttribute('aria-expanded', open ? 'true' : 'false');
    };
    panel.querySelectorAll('button[data-crt]').forEach(btn => {
      btn.onclick = e => {
        e.preventDefault();
        e.stopPropagation();
        const act = btn.dataset.crt;
        panel.classList.remove('open');
        pill.classList.remove('open');
        pill.setAttribute('aria-expanded', 'false');
        if (act == 'file') {
          window.__pickingFile = true;
          let inp = document.getElementById('chat-file-picker');
          if (!inp) {
            inp = document.createElement('input');
            inp.type = 'file';
            inp.id = 'chat-file-picker';
            inp.style.display = 'none';
            document.body.appendChild(inp);
          }
          inp.onchange = async ev => {
            const f = ev.target.files?.[0];
            if (f) {
              window.__attachedFile = { name: f.name, size: f.size || 0, type: f.type || '', fileObj: f };
              const wrap = document.getElementById('chat-attached-wrap');
              if (wrap) wrap.innerHTML = renderChatAttachmentPill();
              buddy.emote('happy', 1000);

              // 1. Lectura instantánea directa de texto/HTML/código para el modelo
              let pendingPromise = null;
              if (f.text && f.size < 600000 && (!f.type || f.type.startsWith('text') || /\.(html|htm|py|js|ts|json|txt|md|css|rs|go|c|cpp|java|csv)$/i.test(f.name))) {
                pendingPromise = f.text().then(txt => {
                  if (window.__attachedFile) window.__attachedFile.content = txt;
                }).catch(() => {});
              }
              window.__attachedFile.pendingPromise = pendingPromise;

              // 2. Subida a disco / backend
              const reader = new FileReader();
              reader.onload = async () => {
                try {
                  const dataUrl = reader.result;
                  const isB64 = typeof dataUrl === 'string' && dataUrl.startsWith('data:');
                  const res = await window.Bridge?.uploadFile?.(f.name, dataUrl, isB64);
                  if (res && res.file_path && window.__attachedFile) {
                    window.__attachedFile.filePath = res.file_path;
                    window.__attachedFile.analysis = res.analysis || res.preview;
                    window.__attachedFile.dataUrl = dataUrl;
                  }
                } catch (_) {}
              };
              reader.readAsDataURL(f);
              const q = document.getElementById('q');
              if (q) q.focus();
            }
            setTimeout(() => { window.__pickingFile = false; }, 800);
          };
          window.addEventListener('focus', () => {
            setTimeout(() => { window.__pickingFile = false; }, 800);
          }, { once: true });
          inp.value = '';
          inp.click();
        } else if (act == 'vision') {
          const q = document.getElementById('q');
          if (q) q.value = '¿Qué ves en mi pantalla?';
          document.querySelector('[data-a="send"]')?.click();
        } else if (act == 'clip') {
          navigator.clipboard?.readText?.().then(txt => {
            const q = document.getElementById('q');
            if (q && txt) { q.value = (q.value ? q.value + ' ' : '') + txt; q.focus(); }
          }).catch(() => {});
        } else if (act == 'agents') {
          window.Bridge?.openSettings?.();
        }
      };
    });
  });
}
document.addEventListener('click', e => {
  if (!e.target.closest('.ag-chat-pill-wrap')) {
    const agDd = document.getElementById('agChatDropdown');
    if (agDd) agDd.style.display = 'none';
  }
  if (!e.target.closest('.crt-stage')) {
    document.querySelectorAll('.crt-panel.open').forEach(p => p.classList.remove('open'));
    document.querySelectorAll('.crt-pill.open').forEach(b => { b.classList.remove('open'); b.setAttribute('aria-expanded', 'false'); });
  }
});
window.initLiquidMenu = initLiquidMenu;
window.zoomImage = function(src) {
  if (!src) return;
  const old = document.getElementById('zoomModal');
  if (old) old.remove();
  const d = document.createElement('div');
  d.id = 'zoomModal';
  d.className = 'zoom-modal-backdrop';
  d.onclick = () => d.remove();
  d.innerHTML = `<img src="${src}" alt="Captura ampliada">`;
  document.body.appendChild(d);
};
