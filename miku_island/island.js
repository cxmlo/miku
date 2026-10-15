(()=>{
const $=s=>document.querySelector(s), $$=s=>[...document.querySelectorAll(s)];
const NOW=()=>performance.now();
const clamp=(v,a,b)=>Math.max(a,Math.min(b,v)), lerp=(a,b,t)=>a+(b-a)*t;
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const E={out:t=>1-Math.pow(1-t,3),inOut:t=>t<.5?4*t*t*t:1-Math.pow(-2*t+2,3)/2,back:t=>{const c1=1.7,c3=c1+1;return 1+c3*Math.pow(t-1,3)+c1*Math.pow(t-1,2)},lin:t=>t};
const hexRgb=h=>{h=h.replace('#','');return[parseInt(h.slice(0,2),16),parseInt(h.slice(2,4),16),parseInt(h.slice(4,6),16)]};
const rgba=(c,a)=>`rgba(${c[0]|0},${c[1]|0},${c[2]|0},${a})`;
const mix=(a,b,t)=>[lerp(a[0],b[0],t),lerp(a[1],b[1],t),lerp(a[2],b[2],t)];

/* ---------------- SON ---------------- */
const Snd={ctx:null,on:false,vol:.7,
  init(){ if(this.ctx)return; const C=window.AudioContext||window.webkitAudioContext; if(!C)return; const c=this.ctx=new C();
    this.master=c.createGain(); this.master.gain.value=this.vol; const comp=c.createDynamicsCompressor(); comp.threshold.value=-18;
    this.master.connect(comp); comp.connect(c.destination);
    const len=Math.floor(c.sampleRate*1.3), ir=c.createBuffer(2,len,c.sampleRate);
    for(let ch=0;ch<2;ch++){const d=ir.getChannelData(ch); for(let i=0;i<len;i++) d[i]=(Math.random()*2-1)*Math.pow(1-i/len,3.4);}
    const rev=c.createConvolver(); rev.buffer=ir; const wet=c.createGain(); wet.gain.value=.2; rev.connect(wet); wet.connect(this.master);
    this.bus=c.createGain(); this.bus.connect(this.master); this.bus.connect(rev);
    const nb=c.createBuffer(1,c.sampleRate,c.sampleRate), nd=nb.getChannelData(0); for(let i=0;i<nd.length;i++) nd[i]=Math.random()*2-1; this.nb=nb;
  },
  setVol(v){this.vol=v; if(this.master) this.master.gain.value=v},
  tone({f=440,to=0,d=.2,type='sine',g=.1,a=.006,delay=0,vib=0,vibf=6,h=0}){ const c=this.ctx,t=c.currentTime+delay;
    const o=c.createOscillator(); o.type=type; o.frequency.setValueAtTime(f,t); if(to) o.frequency.exponentialRampToValueAtTime(to,t+d*.9);
    const gn=c.createGain(); gn.gain.setValueAtTime(.0001,t); gn.gain.exponentialRampToValueAtTime(g,t+a); gn.gain.exponentialRampToValueAtTime(.0001,t+d);
    if(vib){const l=c.createOscillator(),lg=c.createGain(); l.frequency.value=vibf; lg.gain.value=vib; l.connect(lg); lg.connect(o.frequency); l.start(t); l.stop(t+d+.05);}
    o.connect(gn); gn.connect(this.bus); o.start(t); o.stop(t+d+.05);
    if(h){const o2=c.createOscillator(); o2.frequency.setValueAtTime(f*h,t); const g2=c.createGain(); g2.gain.setValueAtTime(.0001,t); g2.gain.exponentialRampToValueAtTime(g*.3,t+a); g2.gain.exponentialRampToValueAtTime(.0001,t+d*.35); o2.connect(g2); g2.connect(this.bus); o2.start(t); o2.stop(t+d);}
  },
  noise({d=.2,g=.04,f=1500,to=0,q=.9,type='bandpass',delay=0}){ const c=this.ctx,t=c.currentTime+delay;
    const s=c.createBufferSource(); s.buffer=this.nb; const fl=c.createBiquadFilter(); fl.type=type; fl.Q.value=q; fl.frequency.setValueAtTime(f,t); if(to) fl.frequency.exponentialRampToValueAtTime(to,t+d);
    const gn=c.createGain(); gn.gain.setValueAtTime(.0001,t); gn.gain.exponentialRampToValueAtTime(g,t+d*.35); gn.gain.exponentialRampToValueAtTime(.0001,t+d);
    s.connect(fl); fl.connect(gn); gn.connect(this.bus); s.start(t); s.stop(t+d+.05);
  },
  play(n){ if(!this.on)return; this.init(); if(!this.ctx)return; if(this.ctx.state==='suspended') this.ctx.resume(); const f=this.lib[n]; if(f) try{f.call(this)}catch(e){} },
  lib:{
    peek(){this.tone({f:1320,d:.09,g:.04});this.tone({f:1760,d:.12,g:.035,delay:.07})},
    open(){this.tone({f:300,to:560,d:.24,g:.06});this.noise({d:.28,g:.018,f:900,to:3200})},
    close(){this.tone({f:540,to:300,d:.2,g:.05});this.noise({d:.2,g:.014,f:2600,to:800})},
    hover(){this.tone({f:2100,d:.05,g:.014})},
    blip(){this.tone({f:1480,d:.07,g:.035})},
    slap(){this.tone({f:280,to:110,d:.18,type:'triangle',g:.16});this.noise({d:.06,g:.06,f:900,q:.6})},
    annoyed(){this.tone({f:240,to:185,d:.2,type:'triangle',g:.07,delay:.06})},
    dizzy(){this.tone({f:640,to:380,d:1,g:.06,vib:45,vibf:9});this.tone({f:960,to:560,d:1,g:.025,vib:70,vibf:7,delay:.06})},
    greet(){[523.25,659.25,783.99].forEach((f,i)=>this.tone({f,d:.32,g:.06,delay:i*.085,h:4}))},
    work(){this.tone({f:880,d:.14,g:.028});this.tone({f:1174.7,d:.18,g:.022,delay:.07})},
    finish(){this.tone({f:783.99,d:.6,g:.08,h:4});this.tone({f:1046.5,d:.9,g:.08,h:4,delay:.11});this.tone({f:1318.5,d:1.1,g:.045,h:3,delay:.22})},
    error(){this.tone({f:392,d:.35,type:'triangle',g:.09});this.tone({f:311.1,d:.55,type:'triangle',g:.09,delay:.16})},
    approval(){this.tone({f:987.8,d:.35,g:.07,h:2.76});this.tone({f:987.8,d:.5,g:.07,h:2.76,delay:.18})},
    question(){this.tone({f:659.3,d:.24,g:.06,h:3});this.tone({f:880,d:.4,g:.06,h:3,delay:.12})},
    approve(){this.tone({f:660,d:.18,g:.05});this.tone({f:990,d:.3,g:.05,delay:.08,h:3})},
    gulp(){this.tone({f:340,to:120,d:.16,g:.11});this.tone({f:210,to:80,d:.22,g:.09,delay:.1})},
    tick(){this.tone({f:2400,d:.03,g:.012})},
    send(){this.noise({d:.38,g:.04,f:700,to:4200});this.tone({f:600,to:1250,d:.26,g:.035})},
    love(){this.tone({f:1046.5,d:.32,g:.045,vib:14,vibf:8});this.tone({f:1318.5,d:.5,g:.045,vib:14,vibf:8,delay:.14})},
    pop(){this.tone({f:480,to:1150,d:.11,g:.07})},
    proud(){[784,988,1175,1568].forEach((f,i)=>this.tone({f,d:.4,g:.045,delay:i*.06,h:4}))},
    wink(){this.tone({f:1400,to:1900,d:.09,g:.035})},
    yawn(){this.tone({f:430,to:250,d:.8,g:.045,vib:9,vibf:4})},
    attach(){[1568,1976,2349,2637,3136].forEach((f,i)=>this.tone({f,d:.7,g:.022,delay:i*.05}));this.noise({d:.7,g:.02,f:3000,to:6000})},
    think(){this.tone({f:520,d:.2,g:.03});this.tone({f:620,d:.25,g:.03,delay:.12})},
    search(){this.tone({f:740,d:.12,g:.025});this.tone({f:990,d:.12,g:.025,delay:.1});this.tone({f:1245,d:.2,g:.025,delay:.2})},
    rate(){this.tone({f:500,to:420,d:.3,g:.04});this.tone({f:420,to:350,d:.4,g:.04,delay:.18})},
    sleep(){this.tone({f:330,to:290,d:.5,g:.03})}
  }
};

/* ---------------- PERSONNAGE ---------------- */
const PISTES={
  galet:{name:'Galet',desc:"Une bille mate avec deux yeux en pilule. Très lisible en tout petit.",shape:'circle',eye:{w:.25,h:.52,sp:.31,p:.02},base:['#F7F8FA','#B5BAC3'],ink:'#121418'},
  miku:{name:'miku',desc:"Un petit pain de riz aplati, yeux ronds et joues qui rosissent. Le plus mignon, un peu moins neutre.",shape:'miku',eye:{w:.25,h:.27,sp:.37,p:-.12},base:['#FFFAF5','#DDCCBF'],ink:'#1A1412'},
  lueur:{name:'Lueur',desc:"Une sphère qui prend la couleur de son état. On sait ce qui se passe sans lire, même de loin.",shape:'orb',eye:{w:.22,h:.46,sp:.29,p:.02},base:['#F2F5F8','#C9D2DC'],ink:'#0D1522'}
};
const STATES={
  idle:{label:'Au repos',col:'#E6E9EE',tint:0,eye:'pill',badge:null,glow:'rgba(255,255,255,.35)',go:.25},
  working:{label:'Travaille',col:'#3B9EFF',tint:.72,eye:'pill',badge:['dots','#3B9EFF'],glow:'#3B9EFF',go:.55,snd:'work'},
  finished:{label:'Terminé',col:'#34D399',tint:.35,eye:'happy',badge:['dot','#34D399'],glow:'#34D399',go:.5,snd:'finish'},
  error:{label:'Erreur',col:'#F4505E',tint:.78,eye:'flat',badge:['dot','#F4505E'],glow:'#F4505E',go:.55,snd:'error'},
  dizzy:{label:'Sonné',col:'#F472B6',tint:.7,eye:'spiral',badge:null,glow:'#F472B6',go:.55,snd:'dizzy'},
  thinking:{label:'Réfléchit',col:'#8B5CF6',tint:.72,eye:'pill',badge:['dots','#8B5CF6'],glow:'#8B5CF6',go:.5,look:[.55,.55],snd:'think',nu:1},
  searching:{label:'Cherche',col:'#6366F1',tint:.72,eye:'pill',badge:['dots','#6366F1'],glow:'#6366F1',go:.55,scan:1,snd:'search',nu:1},
  approval:{label:'Attend ton feu vert',col:'#F5A524',tint:.78,eye:'wide',badge:['bang','#F5A524'],glow:'#F5A524',go:.6,bounce:1,snd:'approval',nu:1},
  question:{label:'Pose une question',col:'#22D3EE',tint:.75,eye:'pill',badge:['q','#22D3EE'],glow:'#22D3EE',go:.55,tilt:.17,snd:'question',nu:1},
  ratelimit:{label:'Limite atteinte',col:'#FB923C',tint:.72,eye:'tired',badge:['dot','#FB923C'],glow:'#FB923C',go:.45,sweat:1,snd:'rate',nu:1},
  sleeping:{label:'Dort',col:'#94A3B8',tint:.32,eye:'closed',badge:null,glow:'#94A3B8',go:.2,breathe:1,zz:1,snd:'sleep',nu:1}
};
const EMOTES={love:{label:'Amour',eye:'heart',snd:'love',c:'#FF4D6D'},surprised:{label:'Surpris',eye:'dot',snd:'pop',c:'#FFFFFF'},proud:{label:'Fier',eye:'star',snd:'proud',c:'#F7B32B'},wink:{label:"Clin d'œil",eye:'wink',snd:'wink',c:'#A78BFA'},yawn:{label:'Bâille',eye:'tired',snd:'yawn',c:'#94A3B8'},happy:{eye:'happy'},annoyed:{eye:'line'}};

function rr(x,X,Y,W,H,R){R=Math.max(0,Math.min(R,W/2,H/2));x.beginPath();x.moveTo(X+R,Y);x.arcTo(X+W,Y,X+W,Y+H,R);x.arcTo(X+W,Y+H,X,Y+H,R);x.arcTo(X,Y+H,X,Y,R);x.arcTo(X,Y,X+W,Y,R);x.closePath()}
function heart(x,s){x.beginPath();x.moveTo(0,s*.38);x.bezierCurveTo(-s*1.05,-s*.15,-s*.5,-s*.95,0,-s*.38);x.bezierCurveTo(s*.5,-s*.95,s*1.05,-s*.15,0,s*.38);x.closePath()}
function star(x,ro,ri){x.beginPath();for(let i=0;i<10;i++){const r=i%2?ri:ro,a=-Math.PI/2+i*Math.PI/5;x.lineTo(Math.cos(a)*r,Math.sin(a)*r)}x.closePath()}

class Bot{
  constructor(canvas,{mini=false,bodyColor=null}={}){
    this.c=canvas; this.x=canvas.getContext('2d'); this.mini=mini; this.bodyColor=bodyColor?hexRgb(bodyColor):null;
    this.s={yaw:0,pitch:0,roll:0,tilt:0,open:1,sx:1,sy:1,oy:0,ox:0,tint:0,morph:0,hands:0,blush:0,es:1,badgeS:0};
    this.tg={...this.s}; this.tw=[]; this.lock={};
    this.col=[230,233,238]; this.colT=[230,233,238];
    this.state='idle'; this.cfg=STATES.idle; this.eyeOv=null; this.ovUntil=0; this.badge=null; this.badgeCol='#fff'; this._bk='none'; this._bt=0;
    this.parts=[]; this.nextBlink=NOW()+1500+Math.random()*2000; this.look={x:0,y:0}; this.t0=NOW()-Math.random()*5000; this.waveUntil=0; this.lastAmb=0; this.last=NOW();
    const dpr=Math.min(2,window.devicePixelRatio||1); const px=mini?76:230; canvas.width=px*dpr; canvas.height=px*dpr;
  }
  anim(p,keys,after){ this.tw=this.tw.filter(t=>t.p!==p); this.tw.push({p,keys,i:0,from:this.s[p],t0:NOW(),after}); this.lock[p]=1 }
  setState(n,force){ if(!STATES[n])return; if(this.state===n&&!force)return; const prev=this.state; this.state=n; const c=this.cfg=STATES[n];
    this.colT=hexRgb(c.col); this.tg.tint=c.tint; this.tg.tilt=c.tilt||0; this.setBadge(c.badge);
    if(n==='finished'){ this.roll(950,1); setTimeout(()=>this.emit('spark',5),500) }
    else if(n==='error'){ this.anim('ox',[[.08,50,E.out],[-.08,70,E.inOut],[.05,70,E.inOut],[0,90,E.out]]) }
    else if(n==='approval'){ this.anim('oy',[[-.2,150,E.out],[0,300,E.back]]) }
    else if(n==='dizzy'){ this.roll(1300,2) }
    else if(n==='question'){ this.blink() }
    else if(n==='ratelimit'){ this.emit('sweat',1) }
    else if(prev!=='idle'||n!=='idle') this.blink();
  }
  setBadge(b){ const key=b?b.join():'none'; if(key===this._bk)return; this._bk=key; const tok=++this._bt;
    this.anim('badgeS',[[0,90,E.inOut]]); setTimeout(()=>{ if(tok!==this._bt)return; this.badge=b?b[0]:null; this.badgeCol=b?b[1]:null; if(b) this.anim('badgeS',[[1,280,E.back]]) },100) }
  blink(){ if(this.lock.open)return; this.anim('open',[[.06,70,E.inOut],[1,130,E.out]]) }
  squash(){ this.anim('sy',[[.78,70,E.out],[1.1,130,E.out],[1,170,E.inOut]]); this.anim('sx',[[1.16,70,E.out],[.95,130,E.out],[1,170,E.inOut]]) }
  roll(d=900,turns=1){ this.s.roll=0; this.anim('roll',[[Math.PI*2*turns,d,E.inOut]],()=>{this.s.roll=0;this.tg.roll=0}) }
  greet(){ this.anim('hands',[[1,280,E.back]]); this.waveUntil=NOW()+1500; this.emote('happy',1500,true); setTimeout(()=>this.anim('hands',[[0,240,E.inOut]]),1550) }
  emote(n,d=1800,silent){ const em=EMOTES[n]; if(!em)return; this.eyeOv=em.eye; this.ovUntil=NOW()+d;
    if(n==='love'){ this.anim('blush',[[1,300,E.out],[1,d-600,E.lin],[0,300,E.inOut]]); this.emit('heart',4); this.anim('oy',[[-.1,160,E.out],[0,300,E.back]]) }
    if(n==='surprised'){ this.anim('oy',[[-.3,140,E.out],[0,380,E.back]]); this.anim('es',[[1.25,120,E.out],[1,500,E.inOut]]) }
    if(n==='proud'){ this.emit('star',5); this.anim('tilt',[[-.14,220,E.out],[-.14,d-500,E.lin],[0,280,E.inOut]]) }
    if(n==='wink'){ this.anim('tilt',[[.12,160,E.out],[.12,d-400,E.lin],[0,240,E.inOut]]) }
    if(n==='yawn'){ this.anim('sy',[[1.12,500,E.inOut],[1,500,E.inOut]]); this.anim('sx',[[.94,500,E.inOut],[1,500,E.inOut]]); setTimeout(()=>{this.eyeOv='closed';this.emit('z',2)},700) }
    if(n==='happy'){ this.anim('blush',[[.6,200,E.out],[0,600,E.inOut]]) }
    if(!silent&&em.snd) Snd.play(em.snd);
  }
  emit(type,n){ for(let i=0;i<n;i++) this.parts.push({type,x:(Math.random()-.5)*.9+(type==='z'?.55:0),y:-.7-Math.random()*.2,vx:(Math.random()-.5)*.35+(type==='z'?.18:0),vy:-(.45+Math.random()*.35),age:-i*.14,life:1.3+Math.random()*.5,rot:Math.random()*6,sz:.15+Math.random()*.08}) }
  update(){
    const n=NOW(), dt=Math.min(.05,(n-this.last)/1000); this.last=n; const s=this.s, tg=this.tg, c=this.cfg, t=(n-this.t0)/1000;
    for(const tw of [...this.tw]){ const k=tw.keys[tw.i]; const p=clamp((n-tw.t0)/k[1],0,1); s[tw.p]=tw.from+(k[0]-tw.from)*k[2](p);
      if(p>=1){ tw.from=k[0]; tw.i++; tw.t0=n; if(tw.i>=tw.keys.length){ this.tw.splice(this.tw.indexOf(tw),1); delete this.lock[tw.p]; this.tg[tw.p]=tw.keys[tw.keys.length-1][0]; if(tw.after) tw.after() } } }
    let ty=this.look.x*.62, tp=this.look.y*.5;
    if(c.look){ ty=ty*.35+c.look[0]*.55; tp=tp*.3+c.look[1]*.5 }
    if(c.scan){ ty=Math.sin(t*2.6)*.6; tp=-.06 }
    if(this.state==='sleeping'){ ty=0; tp=-.14 }
    if(this.state==='dizzy'){ ty=Math.sin(t*9)*.25 }
    tg.yaw=ty; tg.pitch=tp; tg.tilt=c.tilt||0; tg.oy=c.bounce?-Math.abs(Math.sin(t*5.2))*.07:0;
    tg.sy=c.breathe?1+Math.sin(t*1.8)*.035:1; tg.sx=c.breathe?1-Math.sin(t*1.8)*.02:1;
    const kLook=1-Math.pow(.0025,dt), kGen=1-Math.pow(.0008,dt);
    for(const k in tg){ if(this.lock[k])continue; s[k]+=(tg[k]-s[k])*((k==='yaw'||k==='pitch')?kLook:kGen) }
    this.col=mix(this.col,this.colT,1-Math.pow(.002,dt));
    if(n>this.nextBlink){ if(this.state!=='sleeping'&&this.state!=='dizzy'){ this.blink(); if(Math.random()<.22) setTimeout(()=>this.blink(),230) } this.nextBlink=n+2200+Math.random()*3200 }
    if(this.eyeOv&&n>this.ovUntil) this.eyeOv=null;
    if(!this.mini&&n-this.lastAmb>1300){ this.lastAmb=n; if(c.zz) this.emit('z',1); if(c.sweat&&Math.random()<.5) this.emit('sweat',1) }
    for(const p of this.parts) p.age+=dt; this.parts=this.parts.filter(p=>p.age<p.life);
  }
  draw(){
    const x=this.x, W=this.c.width, H=this.c.height, s=this.s, P=PISTES[app.piste];
    x.clearRect(0,0,W,H);
    const R=W*.3; let rx=R, ry=R; if(P.shape==='miku'){rx=R*1.14; ry=R*.88}
    const cx=W/2+s.ox*R, cy=H/2+s.oy*R+(P.shape==='miku'?R*.06:0);
    const col=this.col;
    x.save(); x.translate(cx,cy); x.rotate(s.tilt); x.scale(s.sx,s.sy);
    const path=new Path2D(), m=s.morph;
    if(m<.01){ if(P.shape==='miku'){ for(let i=0;i<=72;i++){const a=i/72*Math.PI*2,ca=Math.cos(a),sa=Math.sin(a); const px=rx*Math.sign(ca)*Math.pow(Math.abs(ca),2/2.7), py=ry*Math.sign(sa)*Math.pow(Math.abs(sa),2/2.7); i?path.lineTo(px,py):path.moveTo(px,py)} path.closePath() } else path.ellipse(0,0,rx,ry,0,0,Math.PI*2) }
    else { const w=lerp(rx,R*1.02,m), h=lerp(ry,R*.94,m), r=lerp(Math.min(rx,ry),R*.34,m); path.roundRect(-w,-h,2*w,2*h,r) }
    // body
    const bc=this.bodyColor;
    if(P.shape==='orb'&&!bc){
      const k=Math.max(s.tint,.25); const inner=mix([255,255,255],col,.12*k), outer=mix([214,222,232],col,.9*k);
      const g=x.createRadialGradient(-rx*.3,-ry*.38,R*.05,0,0,R*1.05); g.addColorStop(0,rgba(inner,1)); g.addColorStop(.55,rgba(mix(inner,outer,.55),1)); g.addColorStop(1,rgba(outer,1));
      x.save(); if(!this.mini){x.shadowColor=rgba(col,.45*k+.1); x.shadowBlur=R*.55} x.fillStyle=g; x.fill(path); x.restore();
    } else {
      let c0,c1; if(bc){ c0=mix(bc,[255,255,255],.35); c1=mix(bc,[0,0,0],.18) } else { c0=hexRgb(P.base[0]); c1=hexRgb(P.base[1]) }
      const g=x.createLinearGradient(rx*.7,-ry*.85,-rx*.8,ry*.9); g.addColorStop(0,rgba(c0,1)); g.addColorStop(1,rgba(c1,1)); x.fillStyle=g; x.fill(path);
      if(!bc&&s.tint>.01){ const tg2=x.createLinearGradient(0,ry,0,-ry*.25); tg2.addColorStop(0,rgba(col,.92*s.tint)); tg2.addColorStop(1,rgba(col,0)); x.fillStyle=tg2; x.fill(path) }
      const sh=x.createRadialGradient(rx*.25,-ry*.32,R*.15,0,0,R*1.25); sh.addColorStop(0,'rgba(255,255,255,0)'); sh.addColorStop(.6,'rgba(0,0,0,0)'); sh.addColorStop(1,'rgba(0,0,0,.2)'); x.fillStyle=sh; x.fill(path);
      const hl=x.createRadialGradient(rx*.34,-ry*.46,0,rx*.34,-ry*.46,R*.42); hl.addColorStop(0,'rgba(255,255,255,.55)'); hl.addColorStop(1,'rgba(255,255,255,0)'); x.fillStyle=hl; x.fill(path);
    }
    // blush
    const bl=Math.max(s.blush,P.shape==='miku'?.35:0)*(1-m);
    if(bl>.01){ x.save(); x.clip(path); const yo=Math.sin(s.yaw)*rx*.8; x.fillStyle=`rgba(255,120,150,${.5*bl})`; for(const sd of[-1,1]){ x.beginPath(); x.ellipse(sd*rx*.55+yo,ry*.2,R*.17,R*.1,0,0,Math.PI*2); x.fill() } x.restore() }
    // eyes
    x.save(); x.clip(path); x.fillStyle=P.ink; x.strokeStyle=P.ink;
    const shape=this.eyeOv||this.cfg.eye;
    for(const sd of[-1,1]){
      const yaw=sd*P.eye.sp+s.yaw; let pitch=P.eye.p+s.pitch+s.roll; pitch=((pitch+Math.PI)%(2*Math.PI)+2*Math.PI)%(2*Math.PI)-Math.PI;
      const cp=Math.cos(pitch); if(Math.cos(yaw)*cp<.04) continue;
      let px=Math.sin(yaw)*cp*rx, py=-Math.sin(pitch)*ry; if(m>0) py+=ry*.14*m;
      const fx=lerp(Math.max(.18,Math.cos(yaw)),1,m*.7), fy=lerp(Math.max(.18,cp),1,m*.7);
      x.save(); x.translate(px,py); x.scale(fx,fy); this.eye(shape,R*P.eye.w*s.es,R*P.eye.h*s.es,s.open,sd,P); x.restore();
    }
    x.restore();
    if(m>.02){ const sw=R*1.5*m, sh=R*.22*m; x.fillStyle=P.ink; rr(x,-sw/2,-R*.94*1+R*.14,sw,sh,sh/2); x.fill() }
    x.restore();
    // hands
    if(s.hands>.01){ const hr=R*.2*s.hands, c0=bc?mix(bc,[255,255,255],.35):hexRgb(P.base[0]), c1=bc?bc:hexRgb(P.base[1]); const tt=NOW()/1000;
      for(const sd of[-1,1]){ let hx=cx+sd*rx*1.25*s.sx, hy=cy+ry*.42; if(sd===1&&NOW()<this.waveUntil){ hy-=R*.38+Math.sin(tt*13)*R*.16; hx+=Math.cos(tt*13)*R*.06 }
        const g=x.createLinearGradient(hx+hr,hy-hr,hx-hr,hy+hr); g.addColorStop(0,rgba(c0,1)); g.addColorStop(1,rgba(c1,1)); x.fillStyle=g; x.beginPath(); x.arc(hx,hy,hr,0,Math.PI*2); x.fill() } }
    // badge
    if(this.badge&&s.badgeS>.01){ const bs=s.badgeS*(this.mini?1.25:1); const bx=cx-rx*.76*s.sx, by=cy-ry*.72*s.sy; x.save(); x.translate(bx,by); x.scale(bs,bs);
      const bcol=this.badgeCol;
      if(this.badge==='dots'&&!this.mini){ const w=R*.74,h=R*.42; x.fillStyle='#000'; rr(x,-w/2-R*.07,-h/2-R*.07,w+R*.14,h+R*.14,(h+R*.14)/2); x.fill(); x.fillStyle=bcol; rr(x,-w/2,-h/2,w,h,h/2); x.fill();
        const tt=NOW()/1000; for(let i=0;i<3;i++){ const ph=((tt*2.4-i*.22)%1+1)%1; const r=R*.06*(1+.4*Math.max(0,Math.sin(ph*Math.PI*2))); x.fillStyle='rgba(255,255,255,.95)'; x.beginPath(); x.arc((i-1)*R*.19,0,r,0,Math.PI*2); x.fill() } }
      else if(this.badge==='bang'||this.badge==='q'){ x.fillStyle='#000'; x.beginPath(); x.arc(0,0,R*.3,0,Math.PI*2); x.fill(); x.fillStyle=bcol; x.beginPath(); x.arc(0,0,R*.23,0,Math.PI*2); x.fill();
        if(!this.mini){ x.fillStyle='#fff'; x.font=`800 ${R*.32}px -apple-system,system-ui,sans-serif`; x.textAlign='center'; x.textBaseline='middle'; x.fillText(this.badge==='bang'?'!':'?',0,R*.02) } }
      else { x.fillStyle='#000'; x.beginPath(); x.arc(0,0,R*.2,0,Math.PI*2); x.fill(); x.fillStyle=bcol; x.beginPath(); x.arc(0,0,R*.135,0,Math.PI*2); x.fill() }
      x.restore() }
    // particules
    for(const p of this.parts){ if(p.age<0)continue; const k=p.age/p.life, a=k<.2?k/.2:1-(k-.2)/.8; const px=cx+(p.x+p.vx*p.age)*R*1.3, py=cy+(p.y+p.vy*p.age)*R*1.3; const sz=R*p.sz*(1+k*.4);
      x.save(); x.translate(px,py); x.globalAlpha=clamp(a,0,1);
      if(p.type==='heart'){ x.fillStyle='#FF4D6D'; x.rotate(Math.sin(p.age*6)*.3); heart(x,sz); x.fill() }
      else if(p.type==='star'){ x.fillStyle='#F7B32B'; x.rotate(p.rot+p.age*2); star(x,sz,sz*.45); x.fill() }
      else if(p.type==='spark'){ x.fillStyle='#fff'; x.rotate(p.rot); star(x,sz*.8,sz*.18); x.fill() }
      else if(p.type==='sweat'){ x.fillStyle='#7CC7FF'; x.beginPath(); x.moveTo(0,-sz); x.quadraticCurveTo(sz*.8,sz*.2,0,sz*.6); x.quadraticCurveTo(-sz*.8,sz*.2,0,-sz); x.fill() }
      else if(p.type==='z'){ x.fillStyle='rgba(210,220,235,1)'; x.font=`700 ${sz*1.9}px -apple-system,system-ui,sans-serif`; x.fillText('z',0,0) }
      x.restore() }
  }
  eye(shape,w,h,open,sd,P){ const x=this.x, t=NOW()/1000;
    switch(shape){
      case 'wide': w*=1.16; h*=1.12; /* fallthrough */
      case 'pill': { const hh=Math.max(h*open,w*.3); rr(x,-w/2,-hh/2,w,hh,Math.min(w/2,hh/2)); x.fill(); break }
      case 'dot': x.beginPath(); x.arc(0,0,w*.45,0,Math.PI*2); x.fill(); break;
      case 'line': x.rotate(-sd*.2); rr(x,-w*.78,-w*.21,w*1.56,w*.42,w*.21); x.fill(); break;
      case 'flat': rr(x,-w*.72,-w*.2,w*1.44,w*.4,w*.2); x.fill(); break;
      case 'happy': x.lineWidth=w*.5; x.lineCap='round'; x.beginPath(); x.arc(0,h*.18,w*.82,Math.PI*1.12,Math.PI*1.88); x.stroke(); break;
      case 'closed': x.lineWidth=w*.36; x.lineCap='round'; x.beginPath(); x.arc(0,-h*.08,w*.78,Math.PI*.15,Math.PI*.85); x.stroke(); break;
      case 'spiral': { x.lineWidth=w*.22; x.lineCap='round'; x.beginPath(); for(let a=0;a<4.4*Math.PI;a+=.2){ const r=w*.06+a*w*.058, aa=a+t*9*sd; const px=Math.cos(aa)*r, py=Math.sin(aa)*r; a?x.lineTo(px,py):x.moveTo(px,py) } x.stroke(); break }
      case 'heart': x.fillStyle='#FF4D6D'; heart(x,w*1.2); x.fill(); x.fillStyle=P.ink; break;
      case 'star': x.fillStyle='#F7B32B'; x.rotate(t*1.5*sd); star(x,w*1.05,w*.46); x.fill(); x.fillStyle=P.ink; break;
      case 'tired': rr(x,-w/2,-h*.02,w,h*.38,w/2); x.fill(); rr(x,-w*.62,-h*.1,w*1.24,w*.22,w*.11); x.fill(); break;
      case 'wink': if(sd<0){ rr(x,-w/2,-h/2,w,h,w/2); x.fill() } else { x.lineWidth=w*.5; x.lineCap='round'; x.beginPath(); x.arc(0,h*.18,w*.82,Math.PI*1.12,Math.PI*1.88); x.stroke() } break;
      default: rr(x,-w/2,-h/2,w,h,w/2); x.fill();
    }
  }
}

/* ---------------- DONNÉES ---------------- */
const AGENTS={
  miku:{name:'Miku',tool:'Brain',color:'#FF6B5B',short:'Miku',steps:['Analizando contexto','Generando respuesta','Sintetizando voz','Enviando datos','Completado']},
  system:{name:'Sistema',tool:'Core',color:'#2DD4A7',short:'System',steps:['Monitorizando','Limpiando logs','Optimizando caché']}
};
const app={piste:'miku',mode:'hidden',view:'overview',tasks:[],focus:null,present:true,lastMove:NOW(),lastAct:NOW(),hover:false,autoClose:60000,demo:false,pinned:false,pinUntil:0,
  override:null,pointer:{x:548,y:420},drag:null,ctx:null,upP:0,slaps:[],file:'brief-client.pdf'};

const screen=$('#screen'), island=$('#island'), botwrap=$('#botwrap'), safari=$('#safari');
const main=new Bot($('#botc')); const floatB=new Bot($('#floatc'));
const agentEls={}, minis={};
for(const id in AGENTS){ const a=AGENTS[id], el=document.createElement('div'); el.className='agent'; el.dataset.id=id;
  const c=hexRgb(a.color); el.style.setProperty('--bg',rgba(c,.13)); el.style.setProperty('--bd',rgba(c,.32));
  el.innerHTML=`<canvas></canvas><span class="lbl" style="color:${rgba(mix(c,[255,255,255],.25),1)}">${a.short}</span>`;
  island.appendChild(el); agentEls[id]=el; minis[id]=new Bot(el.querySelector('canvas'),{mini:true,bodyColor:a.color});
  el.addEventListener('click',e=>{ if(app.demo)return; e.stopPropagation(); focusTask(id) }) }

/* ---------------- LAYOUT ---------------- */
const NW=184, NH=32, EW=640;
const VIEWS={
  overview:{h:196,bot:[64,null,70],ag:'pills'}, empty:{h:150,bot:[70,null,62],ag:'none'},
  approval:{h:206,bot:[62,null,56],ag:'column'}, question:{h:196,bot:[62,null,56],ag:'column'},
  error:{h:190,bot:[62,null,58],ag:'column'}, finished:{h:170,bot:[62,null,58],ag:'column'},
  confused:{h:160,bot:[76,null,66],ag:'column'}, upload:{h:176,bot:[140,null,62],ag:'column'},
  uploading:{h:150,bot:[0,0,28],ag:'column'}, choose:{h:170,bot:[60,null,52],ag:'column'},
  mail:{h:210,bot:[56,null,46],ag:'column'}, prompt:{h:156,bot:[52,null,44],ag:'column'},
  searching:{h:156,bot:[52,null,44],ag:'column'}, result:{h:262,bot:[52,86,44],ag:'column'}, note:{h:136,bot:[60,null,50],ag:'column'}
};
function others(){ return app.tasks.filter(t=>t.id!==app.focus) }
function applyLayout(){
  let w,h,b,ag;
  if(app.mode==='hidden'){ w=NW;h=NH;b={cx:46,cy:16,d:6,o:0};ag='none' }
  else if(app.mode==='peek'){ w=NW+64;h=NH;b={cx:19,cy:16,d:18,o:1};ag='none' }
  else if(app.mode==='compact'){ w=NW+104;h=NH;b={cx:27,cy:16,d:20,o:1};ag='grid' }
  else { const V=VIEWS[app.view]; w=EW;h=V.h; let [bx,by,bd]=V.bot; if(app.view==='uploading'){ bx=46+app.upP*(EW-10-42-78-46); by=36+77; } if(by==null) by=36+(h-46)/2; b={cx:bx,cy:by,d:bd,o:1}; ag=V.ag }
  island.style.width=w+'px'; island.style.height=h+'px'; island.dataset.mode=app.mode; island.dataset.view=app.view;
  const cs=b.d/.6; Object.assign(botwrap.style,{left:(b.cx-cs/2)+'px',top:(b.cy-cs/2)+'px',width:cs+'px',height:cs+'px',opacity:app.drag&&app.drag.type==='bot'?0:b.o});
  layoutAgents(ag,w,h);
  $$('.view').forEach(v=>v.classList.toggle('on',app.mode==='expanded'&&v.dataset.view===app.view));
  $$('.tab').forEach(t=>t.classList.toggle('on',t.dataset.go===app.view||(t.dataset.go==='overview'&&(app.view==='overview'||app.view==='empty'))));
  const n=app.tasks.length; $('#hdrCount').textContent=n?`${n} en cours`:'';
}
function layoutAgents(mode,w,h){
  const list=mode==='grid'?app.tasks.filter(t=>t.id!==app.focus):others();
  for(const id in agentEls){ const el=agentEls[id], cv=el.querySelector('canvas'); const i=list.findIndex(t=>t.id===id);
    if(i<0||i>3||mode==='none'){ el.style.opacity=0; el.style.pointerEvents='none'; el.classList.remove('pill'); continue }
    el.style.opacity=1; el.style.pointerEvents='auto'; el.style.setProperty('--d',(i*.035)+'s');
    let L,T,W,H,cs,cl,ct,pill=false; const n=Math.min(list.length,4);
    if(mode==='grid'){ const d=9.5, sp=6; const pos=n===1?[[0,0]]:n===2?[[-sp,0],[sp,0]]:n===3?[[-sp,-sp],[sp,-sp],[0,sp]]:[[-sp,-sp],[sp,-sp],[-sp,sp],[sp,sp]];
      const cx=w-27+pos[i][0], cy=16+pos[i][1]; W=H=d; L=cx-d/2; T=cy-d/2; cs=d/.6; cl=(W-cs)/2; ct=(H-cs)/2 }
    else if(mode==='column'){ const d=16; const cx=w-10-21, cy=36+14+i*24; W=H=d; L=cx-d/2; T=cy-d/2; cs=d/.6; cl=(W-cs)/2; ct=(H-cs)/2 }
    else { pill=true; W=132; H=34; const col=i%2,row=Math.floor(i/2), rows=Math.ceil(n/2); const cardX=10+332, cardY=36, cardH=h-46;
      L=cardX+8+col*(W+8); T=cardY+(cardH-(rows*H+(rows-1)*8))/2+row*(H+8); cs=24/.6; cl=17-cs/2; ct=17-cs/2 }
    Object.assign(el.style,{left:L+'px',top:T+'px',width:W+'px',height:H+'px'}); Object.assign(cv.style,{left:cl+'px',top:ct+'px',width:cs+'px',height:cs+'px'});
    el.classList.toggle('pill',pill) }
}
function setMode(m,view){ const order={hidden:0,peek:1,compact:2,expanded:3}; const shrinking=order[m]<order[app.mode];
  island.classList.toggle('closing',shrinking); const was=app.mode; app.mode=m; if(view) app.view=view; applyLayout();
  if(m==='expanded'&&was!=='expanded'){ Snd.play('open'); main.blink() }
  if(was==='expanded'&&m!=='expanded'){ Snd.play('close'); app.pinned=false; if(app.ctx&&app.ctx.type==='window'&&!['prompt','searching','result'].includes(app.view)) detach() } }
function baseMode(){ if(!app.present) return 'hidden'; return app.tasks.length?'compact':'hidden' }
function expand(view){ app.lastAct=NOW(); if(app.mode==='expanded'){ app.view=view; island.classList.remove('closing'); applyLayout() } else setMode('expanded',view) }
function collapse(){ app.pinned=false; app.pinUntil=0; if(app.ctx&&app.ctx.type==='window') detach(); app.ctx=null; resetMorph(); setMode(baseMode()) }
function defaultView(){ return app.tasks.length?'overview':'empty' }

/* ---------------- TÂCHES ---------------- */
function task(id){ return app.tasks.find(t=>t.id===id) }
function addTask(id,state='working'){ if(task(id))return; app.tasks.push({id,state,step:0}); minis[id].setState(state,true); if(!app.focus) app.focus=id; sync() }
function setTask(id,state){ const t=task(id); if(!t)return; t.state=state; minis[id].setState(state); sync() }
function removeTask(id){ app.tasks=app.tasks.filter(t=>t.id!==id); if(app.focus===id) app.focus=app.tasks[0]?app.tasks[0].id:null; sync(); if(app.mode!=='expanded') setMode(baseMode()) }
function focusTask(id){ app.focus=id; sync(); expand('overview'); Snd.play('blip') }
function sync(){
  const f=task(app.focus); const st=app.override||(f?f.state:'idle'); main.setState(st);
  const a=f?AGENTS[f.id]:null;
  $$('[data-f=name]').forEach(e=>e.textContent=a?a.name:''); $$('[data-f=tool]').forEach(e=>e.textContent=a?a.tool:''); $$('[data-f=dot]').forEach(e=>e.style.setProperty('--c',a?a.color:'#fff'));
  $$('[data-f=file]').forEach(e=>e.textContent=app.file);
  const g=botwrap.querySelector('.glow'); const S=STATES[st]; g.style.setProperty('--g',S.glow); g.style.setProperty('--go',S.go);
  if(f) setTicker(f,false);
  if(app.mode==='expanded'){ if(app.view==='empty'&&app.tasks.length) app.view='overview'; else if(app.view==='overview'&&!app.tasks.length) app.view='empty' }
  applyLayout();
}
const tkEl=$('#tk');
function setTicker(t,animate){ const st=AGENTS[t.id].steps, L=st.length; const lines=tkEl.querySelectorAll('.ln span');
  const txt=i=>st[((i%L)+L)%L];
  const fill=()=>{ lines[0].textContent=txt(t.step-1); lines[1].textContent=txt(t.step); lines[2].textContent=txt(t.step+1); lines[3].textContent=txt(t.step+2) };
  if(!animate){ fill(); return }
  tkEl.classList.add('roll'); setTimeout(()=>{ t.step++; tkEl.classList.remove('roll'); fill() },460) }
setInterval(()=>{ const f=task(app.focus); if(f&&f.state==='working'&&app.mode==='expanded'&&app.view==='overview') setTicker(f,true);
  for(const t of app.tasks) if(t.id!==app.focus&&t.state==='working'&&Math.random()<.3) t.step++ },2800);

/* ---------------- ALERTES ---------------- */
function alertView(view,id,state){ addTask(id,'working'); app.focus=id; setTask(id,state); app.present=true; expand(view); app.pinned=['approval','question','error'].includes(view);
  app.pinUntil=view==='finished'?NOW()+5200:0; Snd.play(STATES[state]&&STATES[state].snd||'blip') }
function afterDecision(id,state,emote){ setTask(id,state); if(emote) main.emote(emote,900,true); app.pinned=false; setTimeout(()=>{ if(!app.demoHold) collapse() },650) }

/* ---------------- INTERACTIONS ---------------- */
let hoverT=null;
function hoverIn(){ app.hover=true; app.lastAct=NOW(); clearTimeout(hoverT);
  if(app.mode==='hidden'){ setMode('peek'); Snd.play('peek'); setTimeout(()=>main.greet(),120); Snd.play('greet'); hoverT=setTimeout(()=>{ if(app.hover&&app.mode==='peek') expand(defaultView()) },650) }
  else if(app.mode==='compact'||app.mode==='peek'){ hoverT=setTimeout(()=>{ if(app.hover&&app.mode!=='expanded') expand(defaultView()) },200) } }
function hoverOut(){ app.hover=false; clearTimeout(hoverT); if(app.mode==='peek') hoverT=setTimeout(()=>{ if(!app.hover&&app.mode==='peek') setMode(baseMode()) },600) }
island.addEventListener('pointerenter',()=>{ if(!app.demo&&!app.drag) hoverIn() });
island.addEventListener('pointerleave',()=>{ if(!app.demo) hoverOut() });
island.addEventListener('pointermove',()=>{ app.lastAct=NOW() });

let botHoverT=null, botHovering=false;
function botHover(on){ botHovering=on; clearTimeout(botHoverT);
  if(on){ if(app.mode!=='expanded')return; main.blink(); main.tg.es=1.08; Snd.play('hover'); botHoverT=setTimeout(()=>{ if(botHovering&&!app.override) main.emote('love',2000) },1900) }
  else main.tg.es=1 }
botwrap.addEventListener('pointerenter',()=>{ if(!app.demo) botHover(true) });
botwrap.addEventListener('pointerleave',()=>{ if(!app.demo) botHover(false) });

function botClick(){ if(app.mode!=='expanded'){ expand(defaultView()); return } slap() }
function slap(){ const n=NOW(); app.slaps=app.slaps.filter(t=>n-t<1700); app.slaps.push(n); Snd.play('slap'); main.squash(); clearTimeout(botHoverT);
  if(app.slaps.length>=3){ app.slaps=[]; dizzy() } else { main.emote('annoyed',800,true); Snd.play('annoyed'); const g=botwrap.querySelector('.glow'); g.style.setProperty('--g','#A855F7'); g.style.setProperty('--go',.7); setTimeout(()=>{ if(!app.override) sync() },900) } }
function dizzy(){ app.override='dizzy'; const prev=app.view; sync(); Snd.play('dizzy'); if(app.mode==='expanded'){ app.view='confused'; applyLayout() }
  setTimeout(()=>{ app.override=null; sync(); main.blink(); if(app.mode==='expanded'&&app.view==='confused'){ app.view=prev==='confused'?defaultView():prev; applyLayout() } },3300) }

/* drag : bonhomme et fichiers */
function toScreen(cx,cy){ const r=screen.getBoundingClientRect(), k=r.width/1096; return {x:(cx-r.left)/k,y:(cy-r.top)/k} }
function rectS(el){ const r=el.getBoundingClientRect(), a=toScreen(r.left,r.top), b=toScreen(r.right,r.bottom); return {l:a.x,t:a.y,r:b.x,b:b.y,cx:(a.x+b.x)/2,cy:(a.y+b.y)/2} }
function inR(p,R,m=0){ return p.x>R.l-m&&p.x<R.r+m&&p.y>R.t-m&&p.y<R.b+m }
let press=null;
botwrap.addEventListener('pointerdown',e=>{ if(app.demo)return; e.preventDefault(); e.stopPropagation(); press={type:'bot',p:toScreen(e.clientX,e.clientY)} });
$$('.file').forEach(f=>f.addEventListener('pointerdown',e=>{ if(app.demo)return; e.preventDefault(); press={type:'file',el:f,p:toScreen(e.clientX,e.clientY)} }));
window.addEventListener('pointermove',e=>{ if(app.demo)return; const p=toScreen(e.clientX,e.clientY);
  if(press&&!app.drag&&Math.hypot(p.x-press.p.x,p.y-press.p.y)>7){ if(press.type==='bot') beginBotDrag(); else beginFileDrag(press.el) }
  if(app.drag) dragMove(p) });
window.addEventListener('pointerup',e=>{ if(app.demo)return; const p=toScreen(e.clientX,e.clientY);
  if(app.drag) dragEnd(p); else if(press&&press.type==='bot') botClick(); press=null });
screen.addEventListener('pointermove',e=>{ if(app.demo)return; app.pointer=toScreen(e.clientX,e.clientY); app.lastMove=NOW();
  if(!app.present){ app.present=true; if(app.mode==='hidden'&&app.tasks.length) setMode('compact') } });

function beginBotDrag(){ if(app.mode==='hidden')return; app.drag={type:'bot'}; const fb=$('#floatbot'); fb.style.display='block'; floatB.setState(main.state,true); floatB.emote('surprised',700,true); Snd.play('pop'); botHover(false); applyLayout() }
function beginFileDrag(el){ app.drag={type:'file',el,name:el.dataset.name}; el.classList.add('dragging'); const g=$('#fileghost'); g.style.display='block'; g.style.transform=''; g.style.opacity=1; Snd.play('blip') }
function islandZone(){ const r=rectS(island); return {l:Math.min(r.l,548-220),r:Math.max(r.r,548+220),t:0,b:Math.max(r.b,60)+26} }
function dragMove(p){ app.pointer=p;
  if(app.drag.type==='bot'){ const fb=$('#floatbot'); fb.style.left=p.x+'px'; fb.style.top=p.y+'px'; safari.classList.toggle('target',inR(p,rectS(safari))) }
  else { const g=$('#fileghost'); g.style.left=p.x+'px'; g.style.top=p.y+'px'; const over=inR(p,islandZone());
    if(over&&!(app.mode==='expanded'&&app.view==='upload')){ app.hover=true; expand('upload'); main.anim('morph',[[1,380,E.back]]); Snd.play('hover') }
    $('#drop').classList.toggle('over',over&&app.view==='upload');
    if(!over&&app.mode==='expanded'&&app.view==='upload'&&p.y>260){ app.hover=false; resetMorph(); collapse() } } }
function dragEnd(p){ const d=app.drag; app.drag=null;
  if(d.type==='bot'){ const fb=$('#floatbot'); safari.classList.remove('target');
    if(inR(p,rectS(safari))){ attach(); }
    const home=rectS(botwrap); fb.animate([{left:p.x+'px',top:p.y+'px',transform:'scale(1)'},{left:home.cx+'px',top:home.cy+'px',transform:'scale(.25)'}],{duration:420,easing:'cubic-bezier(.4,0,.2,1)'}).onfinish=()=>{ fb.style.display='none'; applyLayout() };
    setTimeout(applyLayout,380) }
  else { const g=$('#fileghost'); d.el.classList.remove('dragging');
    if(inR(p,islandZone())&&app.view==='upload'){ app.file=d.name; sync(); dropFile(p) }
    else { const home=rectS(d.el); g.animate([{left:p.x+'px',top:p.y+'px'},{left:(home.l+24)+'px',top:home.cy+'px'}],{duration:320,easing:'ease-out'}).onfinish=()=>g.style.display='none'; if(app.view==='upload') collapse() } } }
function resetMorph(){ if(main.s.morph>.01||main.lock.morph) main.anim('morph',[[0,320,E.back]]) }
function dropFile(p){ const g=$('#fileghost'), b=rectS(botwrap); $('#drop').classList.remove('over');
  g.animate([{left:p.x+'px',top:p.y+'px',transform:'scale(1)',opacity:1},{left:b.cx+'px',top:(b.t+8)+'px',transform:'scale(.2)',opacity:.2}],{duration:360,easing:'cubic-bezier(.5,0,.8,.4)'}).onfinish=()=>{ g.style.display='none' };
  setTimeout(()=>{ Snd.play('gulp'); main.squash(); main.emote('happy',700,true) },330);
  setTimeout(()=>{ main.anim('morph',[[0,340,E.back]]); app.upP=0; expand('uploading'); runUpload() },950) }
function runUpload(){ const t0=NOW(), D=2100; let lastTick=0;
  const step=()=>{ const k=clamp((NOW()-t0)/D,0,1); app.upP=E.inOut(k); $('#upBar').style.width=(app.upP*100)+'%'; $('#upPct').textContent=Math.round(app.upP*100)+' %';
    if(Math.floor(k*10)>lastTick){ lastTick=Math.floor(k*10); Snd.play('tick') } applyLayout();
    if(k<1) requestAnimationFrame(step); else { Snd.play('approve'); main.emote('happy',900,true); expand('choose'); app.pinned=true } }; step() }

function attach(){ safari.classList.add('attached'); app.ctx={type:'window',label:'Safari, escale.fr'}; Snd.play('attach'); renderChips(); expand('prompt'); app.pinned=true; main.emote('wink',700,true); if(!app.demo) setTimeout(()=>$('#promptIn').focus(),350) }
function detach(){ safari.classList.remove('attached') }
function renderChips(){ const html=app.ctx?`<span class="chip ctx"><i></i>${app.ctx.label}</span>`:''; $('#ctxChips').innerHTML=html; $$('[data-f=chips]').forEach(e=>e.innerHTML=html) }
function submitPrompt(){ const v=$('#promptIn').value.trim(); if(!v)return; $('#promptIn').value=''; Snd.play('send'); app.override='searching'; sync(); app.pinned=true;
  $$('[data-f=status]').forEach(e=>e.textContent=app.ctx&&app.ctx.type==='window'?'Miku está analizando la pantalla…':app.ctx&&app.ctx.type==='file'?`Miku está leyendo ${app.file}…`:'Miku está procesando tu consulta…');
  expand('searching');
  setTimeout(()=>{ app.override=null; renderResult(); expand('result'); main.setState('finished',true); Snd.play('finish'); setTimeout(()=>main.emote('proud',1600),900); detach(); app.pinned=false; app.lastAct=NOW(); setTimeout(()=>sync(),2600) },2800) }
function renderResult(){ const box=$('#resBox'); const isFile=app.ctx&&app.ctx.type==='file';
  box.innerHTML=isFile?`<div class="big">Resumen de ${app.file}</div><div class="res"><div><b>Progreso</b><span>Análisis completo</span></div><div><b>Estado</b><span>Exitoso</span></div></div><div class="fine">Miku procesó el documento.</div><div class="row"><button class="btn primary" data-act="copy">Copiar</button><button class="btn" data-act="close">Cerrar</button></div>`
  :`<div class="big">Resultados encontrados</div><div class="res"><div><b>Acción</b><span>Completada</span></div></div><div class="fine">Procesado por el motor de Miku.</div><div class="row"><button class="btn primary" data-act="close">Ok</button></div>` }
function note(a,b,ms=2000){ $$('[data-f=note]').forEach(e=>e.textContent=a); $$('[data-f=note2]').forEach(e=>e.textContent=b||''); expand('note'); app.pinned=true; setTimeout(()=>{ if(app.view==='note'&&!app.demoHold) collapse() },ms) }

island.addEventListener('click',e=>{ const b=e.target.closest('[data-act],[data-go]'); if(!b)return; e.stopPropagation(); app.lastAct=NOW(); act(b.dataset.act||('go-'+b.dataset.go),b) });
function act(a,b){
  const f=task(app.focus);
  switch(a){
    case 'go-overview': expand(defaultView()); Snd.play('blip'); break;
    case 'go-prompt': case 'ask': app.ctx=null; renderChips(); expand('prompt'); Snd.play('blip'); if(!app.demo) setTimeout(()=>$('#promptIn').focus(),300); break;
    case 'go-upload': expand('upload'); main.anim('morph',[[1,380,E.back]]); Snd.play('blip'); break;
    case 'allow': case 'always': Snd.play('approve'); afterDecision(app.focus,'working','happy'); break;
    case 'deny': Snd.play('blip'); afterDecision(app.focus,'thinking'); break;
    case 'answer': Snd.play('approve'); afterDecision(app.focus,'thinking','happy'); break;
    case 'retry': Snd.play('work'); afterDecision(app.focus,'working','happy'); break;
    case 'open-n8n': note("Abriendo en segundo plano...",''); break;
    case 'jump': if(f) removeTask(f.id); note('Volviendo a la interfaz.',''); break;
    case 'ok': if(f) removeTask(f.id); collapse(); break;
    case 'file-ask': app.ctx={type:'file',label:app.file}; renderChips(); expand('prompt'); if(!app.demo) setTimeout(()=>$('#promptIn').focus(),300); break;
    case 'mail': expand('mail'); if(!app.demo) setTimeout(()=>$('#mailTo').focus(),300); break;
    case 'send-mail': { const to=$('#mailTo').value.trim()||'miku@miku.com'; Snd.play('send'); main.emote('wink',900); note(`Enviado a ${to}.`,`${app.file} adjunto.`,2200); break }
    case 'send': submitPrompt(); break;
    case 'open-first': Snd.play('blip'); collapse(); break;
    case 'copy': Snd.play('blip'); note('Copié.','',1200); break;
    case 'close': collapse(); break;
  }
  if(b){ b.classList.add('pressed'); setTimeout(()=>b.classList.remove('pressed'),160) }
}
$('#promptIn').addEventListener('keydown',e=>{ if(e.key==='Enter'){ e.preventDefault(); submitPrompt() } });
window.addEventListener('keydown',e=>{ if(app.demo||e.target.tagName==='INPUT')return;
  if(app.view==='approval'&&app.mode==='expanded'){ if(e.key==='y'||e.key==='Y') act('allow',$('[data-act=allow]')); if(e.key==='n'||e.key==='N') act('deny',$('[data-act=deny]')) }
  if(e.key==='Escape'&&app.mode==='expanded') collapse() });
$('#hdrSnd').addEventListener('click',e=>{ e.stopPropagation(); setSound(!Snd.on) });

/* ---------------- BOUCLE ---------------- */
function lookAt(bot,el){ const r=rectS(el); const dx=app.pointer.x-r.cx, dy=app.pointer.y-r.cy; bot.look.x=Math.tanh(dx/260); bot.look.y=-Math.tanh(dy/200) }
function frame(){
  const n=NOW();
  if(app.mode!=='hidden'||main.s.hands>.01){ lookAt(main,botwrap); main.update(); main.draw() }
  for(const id in minis){ if(agentEls[id].style.opacity==='0')continue; lookAt(minis[id],agentEls[id]); minis[id].update(); minis[id].draw() }
  if(app.drag&&app.drag.type==='bot'){ const fb=$('#floatbot'); floatB.look.x=0; floatB.look.y=-.3; floatB.update(); floatB.draw() }
  if(!app.demo){
    if(app.mode==='expanded'&&!app.pinned&&!app.drag&&n-app.lastAct>app.autoClose) collapse();
    if(app.pinUntil&&n>app.pinUntil&&app.mode==='expanded'&&app.view==='finished'){ const f=task(app.focus); app.pinUntil=0; if(f&&f.state==='finished') removeTask(f.id); collapse() }
    if(app.present&&n-app.lastMove>25000&&app.mode!=='expanded'){ app.present=false; setMode('hidden') }
  }
  const cd=$('#cd'); if(app.mode==='expanded'&&!app.pinned&&!app.demo){ const win=Math.min(10000,app.autoClose*.6), rem=app.autoClose-(n-app.lastAct); cd.style.width=rem<win?Math.max(0,rem/win*160)+'px':'0px' } else cd.style.width='0px';
  requestAnimationFrame(frame);
}

/* ---------------- CONTRÔLES ---------------- */
function setSound(on){ Snd.on=on; if(on){ Snd.init(); if(Snd.ctx&&Snd.ctx.state==='suspended') Snd.ctx.resume() } $('#sndOn').checked=on; $('#hdrSnd .w').style.opacity=on?1:.2 }
$('#sndOn').addEventListener('change',e=>setSound(e.target.checked));
$('#sndVol').addEventListener('input',e=>Snd.setVol(+e.target.value));
$$('#segClose button').forEach(b=>b.addEventListener('click',()=>{ $$('#segClose button').forEach(x=>x.classList.toggle('on',x===b)); app.autoClose=+b.dataset.ms; app.lastAct=NOW() }));
function setPiste(p){ app.piste=p; $$('#segPiste button').forEach(b=>b.classList.toggle('on',b.dataset.p===p)); $('#pisteDesc').textContent=PISTES[p].desc }
$$('#segPiste button').forEach(b=>b.addEventListener('click',()=>{ setPiste(b.dataset.p); if(app.mode==='hidden') expand(defaultView()); main.blink(); Snd.play('blip') }));
function ensureVisible(){ app.present=true; if(app.mode==='hidden'||app.mode==='peek') expand(defaultView()); app.lastAct=NOW() }
const stateBox=$('#stateBtns');
const auto=document.createElement('button'); auto.className='cb on'; auto.innerHTML='<i style="--c:conic-gradient(#3B9EFF,#34D399,#F4505E,#3B9EFF)"></i>Automatique'; stateBox.appendChild(auto);
auto.addEventListener('click',()=>{ app.override=null; $$('#stateBtns .cb').forEach(x=>x.classList.toggle('on',x===auto)); sync() });
for(const k in STATES){ const S=STATES[k]; const b=document.createElement('button'); b.className='cb'; b.innerHTML=`<i style="--c:${S.col}"></i>${S.label}`; stateBox.appendChild(b);
  b.addEventListener('click',()=>{ ensureVisible(); $$('#stateBtns .cb').forEach(x=>x.classList.toggle('on',x===b)); app.override=k; sync(); main.setState(k,true); Snd.play(S.snd||'blip') }) }
for(const k of ['love','surprised','proud','wink','yawn']){ const em=EMOTES[k]; const b=document.createElement('button'); b.className='cb'; b.innerHTML=`<i style="--c:${em.c}"></i>${em.label}`; $('#emoteBtns').appendChild(b);
  b.addEventListener('click',()=>{ ensureVisible(); main.emote(k,1900) }) }
const SIMS=[
  ['Lancer 3 tâches','#3B9EFF',()=>{ app.present=true; ['korus','sbe','brief'].forEach((id,i)=>setTimeout(()=>addTask(id,i===1?'thinking':'working'),i*260)); setTimeout(()=>{ if(app.mode==='hidden') setMode('compact'); Snd.play('work') },100) }],
  ['Demande de permission','#F5A524',()=>alertView('approval','korus','approval')],
  ['Question','#22D3EE',()=>alertView('question','sbe','question')],
  ['Erreur n8n','#F4505E',()=>alertView('error','brief','error')],
  ['Tâche terminée','#34D399',()=>alertView('finished','korus','finished')],
  ['Limite atteinte','#FB923C',()=>{ addTask('folio','working'); app.focus='folio'; setTask('folio','ratelimit'); ensureVisible(); Snd.play('rate') }],
  ['Utilisateur absent','#94A3B8',()=>{ app.present=false; collapse(); setMode('hidden') }],
  ['Tout arrêter','#6B7280',()=>{ app.tasks=[]; app.focus=null; app.override=null; sync(); collapse(); setMode('hidden') }]
];
for(const [l,c,fn] of SIMS){ const b=document.createElement('button'); b.className='cb'; b.innerHTML=`<i style="--c:${c}"></i>${l}`; b.addEventListener('click',()=>{ if(!app.demo) fn() }); $('#simBtns').appendChild(b) }

/* ---------------- DÉMO ---------------- */
const ghost=$('#ghost');
function ghostAt(p){ ghost.style.left=p.x+'px'; ghost.style.top=p.y+'px'; app.pointer={x:p.x,y:p.y}; if(app.drag) dragMove(app.pointer) }
function move(x,y,d=700){ return new Promise(res=>{ const a={...app.pointer}, t0=NOW(); const st=()=>{ const k=clamp((NOW()-t0)/d,0,1), e=E.inOut(k); ghostAt({x:lerp(a.x,x,e),y:lerp(a.y,y,e)}); if(k<1) requestAnimationFrame(st); else res() }; st() }) }
async function clickAt(){ ghost.classList.add('down'); await sleep(110); ghost.classList.remove('down') }
async function clickEl(sel){ const el=typeof sel==='string'?$(sel):sel; if(!el)return; const r=rectS(el); await move(r.cx,r.cy,650); await sleep(120); await clickAt(); el.click(); }
async function typeIn(el,text,ms=34){ el.value=''; for(const ch of text){ el.value+=ch; if(Math.random()<.5) Snd.play('tick'); await sleep(ms+Math.random()*25) } }
async function runDemo(){
  if(app.demo)return; app.demo=true; app.demoHold=true; const btn=$('#demoBtn'); btn.disabled=true; btn.querySelector('span').textContent='Démo en cours…';
  $('#demoTag').style.display='block'; if(!Snd.on) setSound(true);
  app.tasks=[]; app.focus=null; app.override=null; app.present=true; detach(); sync(); collapse(); setMode('hidden'); await sleep(300);
  ghost.style.display='block'; ghostAt({x:720,y:520}); await sleep(500);
  await move(548,16,1100); hoverIn(); await sleep(1500);
  ['korus','sbe','brief','ig'].forEach((id,i)=>setTimeout(()=>{ addTask(id,i===1?'thinking':'working'); Snd.play('blip') },i*280)); await sleep(1900);
  let b=rectS(botwrap); await move(b.cx+60,b.cy+50,700); await move(b.cx,b.cy,600); botHover(true); await sleep(1100);
  for(let i=0;i<3;i++){ await clickAt(); slap(); await sleep(360) } await sleep(3600); botHover(false);
  await move(700,470,900); app.hover=false; await sleep(400); collapse(); await sleep(1300);
  alertView('approval','korus','approval'); await sleep(1500); await clickEl('[data-act=allow]'); await sleep(1500);
  alertView('question','sbe','question'); await sleep(1400); await clickEl($$('.opt')[1]); await sleep(1500);
  alertView('error','brief','error'); await sleep(1600); await clickEl('[data-act=retry]'); await sleep(1400);
  const fe=$$('.file')[0], fr=rectS(fe); await move(fr.l+24,fr.cy,900); await clickAt(); beginFileDrag(fe); await move(760,220,700); await move(548,70,800); await sleep(700);
  dragEnd(app.pointer); await sleep(3700);
  await clickEl('[data-act=mail]'); await sleep(700); await clickEl('#mailTo'); await typeIn($('#mailTo'),'client@exemple.fr'); await sleep(300); await clickEl('[data-act=send-mail]'); await sleep(2600);
  collapse(); await sleep(900);
  alertView('finished','korus','finished'); await sleep(3400); removeTask('korus'); collapse(); await sleep(1200);
  b=rectS(botwrap); await move(b.cx,b.cy,900); await sleep(200); ghost.classList.add('down'); beginBotDrag(); const s=rectS(safari); await move(s.cx-40,s.cy-20,1300); ghost.classList.remove('down'); dragEnd(app.pointer); await sleep(900);
  await clickEl('#promptIn'); await typeIn($('#promptIn'),"Trouve l'appart le moins cher sous 90 € la nuit"); await sleep(350); await clickEl('[data-act=send]'); await sleep(4600);
  await move(820,500,900); await sleep(1600); collapse(); await sleep(800);
  ['sbe','brief','ig'].forEach((id,i)=>setTimeout(()=>{ setTask(id,'finished'); setTimeout(()=>removeTask(id),900) },i*500)); await sleep(2800);
  collapse(); setMode('hidden'); await sleep(900);
  ghost.style.display='none'; $('#demoTag').style.display='none'; app.demo=false; app.demoHold=false; btn.disabled=false; btn.querySelector('span').textContent='Relancer la démo'; app.lastMove=NOW(); $('#promptIn').value=''; $('#mailTo').value='';
}
$('#demoBtn').addEventListener('click',runDemo);

/* ---------------- ÉCHELLE ---------------- */
function fit(){ const o=$('#stageOuter'); const k=o.clientWidth/1120; $('#stage').style.transform=`scale(${k})`; o.style.height=(700*k)+'px' }
window.addEventListener('resize',fit); fit();
setPiste('miku'); setSound(false); sync(); applyLayout(); requestAnimationFrame(frame);
window.__app=app; window.__demo=runDemo; window.__main=main; window.__snd=Snd; window.__api={expand,collapse,setMode,addTask,setTask,alertView,sync,applyLayout,removeTask};
})();
