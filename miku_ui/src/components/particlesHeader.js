/**
 * Miku Design System — Section Header with 2D Particles, Aurora & Rotating Orb (§6)
 * Exact implementation of Particles(cv, st) from miku-catalogo.html (lines 566-595).
 */

import { getSectionHue } from '../design/tokens.js';
import { enter, prefersReducedMotion } from '../design/motion.js';
import { escapeHtml } from './primitives.js';
import { t } from '../i18n/es.js';

/**
 * Renderiza el marcado HTML del encabezado con partículas (.hero) idéntico a miku-catalogo.html (línea 437).
 */
export function renderParticlesHeader({
  canvasId = 'pc',
  textWrapId = 'ht',
  titleId = 'hh',
  descId = 'hp',
  suiteTag = t('app.suiteTag'),
  title = '',
  desc = ''
} = {}) {
  return (
    `<div class="hero">` +
      `<canvas id="${escapeHtml(canvasId)}"></canvas>` +
      `<div class="au"><i></i><i></i><i></i></div>` +
      `<svg class="orb" viewBox="0 0 200 200" aria-hidden="true">` +
        `<circle class="a" cx="100" cy="100" r="92"/>` +
        `<circle class="b" cx="100" cy="100" r="70"/>` +
        `<circle class="c" cx="100" cy="100" r="50"/>` +
        `<circle class="k" cx="100" cy="100" r="9"/>` +
      `</svg>` +
      `<div id="${escapeHtml(textWrapId)}">` +
        `<small>${escapeHtml(suiteTag)}</small>` +
        `<h3 id="${escapeHtml(titleId)}">${escapeHtml(title)}</h3>` +
        `<p id="${escapeHtml(descId)}">${escapeHtml(desc)}</p>` +
      `</div>` +
    `</div>`
  );
}

/**
 * Motor 2D de partículas, estelas, estrellas fugaces, conexión por cercanía y remolino al cursor.
 * Pausa automáticamente fuera de pantalla (IntersectionObserver) o ventana oculta,
 * recalcula con ResizeObserver, limita a 150 partículas y DPR <= 2, y detiene animación con prefers-reduced-motion.
 */
export function createParticlesEngine(cv, state) {
  if (!cv) return null;
  if (cv._mikuParticlesState) {
    if (state?.t) {
      cv._mikuParticlesState.t = { ...state.t };
    }
    cv._mikuParticlesState.kick?.();
    return cv._mikuParticlesState;
  }
  const x = cv.getContext('2d');
  if (!x) return null;

  const st = state || {
    c: getSectionHue('general'),
    t: getSectionHue('general')
  };
  cv._mikuParticlesState = st;

  let W = 0;
  let H = 0;
  let P = [];
  let SS = [];
  const dpr = Math.min(2, window.devicePixelRatio || 1);
  let mx = -999;
  let my = -999;
  let run = false;
  const hero = cv.parentNode;
  const rm = prefersReducedMotion();
  let ns = 0;

  function size() {
    const r = cv.getBoundingClientRect();
    W = Math.max(1, r.width);
    H = Math.max(1, r.height);
    cv.width = W * dpr;
    cv.height = H * dpr;
    x.setTransform(dpr, 0, 0, dpr, 0, 0);
    P = [];
    const n = Math.min(150, Math.round((W * H) / 3400));
    for (let i = 0; i < n; i++) {
      const z = Math.random();
      P.push({
        x: Math.random() * W,
        y: Math.random() * H,
        z,
        r: 0.45 + z * 1.6,
        p: Math.random() * 6.28,
        o: (Math.random() - 0.5) * 60,
        vx: 0,
        vy: 0
      });
    }
  }

  function hs(h, l, a) {
    return `hsla(${h.toFixed(0)},${st.c.s.toFixed(0)}%,${l.toFixed(0)}%,${a.toFixed(3)})`;
  }

  function frame(tNow) {
    if (!run) return;
    const c = st.c;
    const g = st.t;
    const dh = ((g.h - c.h + 540) % 360) - 180;
    c.h = (c.h + dh * 0.04 + 360) % 360;
    c.s += (g.s - c.s) * 0.05;
    c.l += (g.l - c.l) * 0.05;

    if (hero && hero.style) {
      hero.style.setProperty('--h', c.h.toFixed(1));
    }

    x.globalCompositeOperation = 'destination-out';
    x.fillStyle = 'rgba(0,0,0,.14)';
    x.fillRect(0, 0, W, H);
    x.globalCompositeOperation = 'lighter';

    const near = [];
    for (let i = 0; i < P.length; i++) {
      const q = P[i];
      const sp = 0.22 + q.z * 0.85;
      const a = Math.sin(q.x * 0.006 + tNow * 0.00022) * 2.4 + Math.cos(q.y * 0.01 - tNow * 0.00018) * 2.4;
      const dx = q.x - mx;
      const dy = q.y - my;
      const d = dx * dx + dy * dy;

      if (d < 16900) {
        const l = Math.sqrt(d) || 1;
        const m = (1 - l / 130) * 0.5;
        q.vx += (dx / l) * m * 0.5 - (dy / l) * m * 0.9;
        q.vy += (dy / l) * m * 0.5 + (dx / l) * m * 0.9;
        near.push(q);
      }

      q.vx *= 0.93;
      q.vy *= 0.93;
      q.x += Math.cos(a) * sp + q.vx;
      q.y += Math.sin(a) * sp * 0.55 + q.vy;

      if (q.x > W + 6) q.x = -6;
      else if (q.x < -6) q.x = W + 6;
      if (q.y > H + 6) q.y = -6;
      else if (q.y < -6) q.y = H + 6;

      const hu = c.h + q.o * 0.5 + Math.sin(tNow / 3200 + q.p) * 14;
      const al = (0.28 + 0.55 * (0.5 + 0.5 * Math.sin((tNow / 650) * (0.5 + q.z) + q.p))) * (0.35 + q.z * 0.65);

      x.fillStyle = hs(hu, c.l + q.z * 14, al * 0.16);
      x.beginPath();
      x.arc(q.x, q.y, q.r * 3.4, 0, 6.283);
      x.fill();

      x.fillStyle = hs(hu, Math.min(96, c.l + q.z * 20), al);
      x.beginPath();
      x.arc(q.x, q.y, q.r, 0, 6.283);
      x.fill();
    }

    x.lineWidth = 0.7;
    for (let i = 0; i < near.length; i++) {
      for (let j = i + 1; j < near.length; j++) {
        const u = near[i];
        const v = near[j];
        const ex = u.x - v.x;
        const ey = u.y - v.y;
        const e = ex * ex + ey * ey;
        if (e < 3600) {
          x.strokeStyle = hs(c.h, c.l + 10, (1 - e / 3600) * 0.35);
          x.beginPath();
          x.moveTo(u.x, u.y);
          x.lineTo(v.x, v.y);
          x.stroke();
        }
      }
    }

    if (tNow > ns) {
      ns = tNow + 3500 + Math.random() * 3500;
      SS.push({
        x: Math.random() * W * 0.6,
        y: Math.random() * H * 0.4,
        vx: 7 + Math.random() * 4,
        vy: 2.5 + Math.random() * 2,
        l: 1
      });
    }

    for (let k = SS.length - 1; k >= 0; k--) {
      const s = SS[k];
      const gr = x.createLinearGradient(s.x, s.y, s.x - s.vx * 7, s.y - s.vy * 7);
      gr.addColorStop(0, hs(c.h, 88, 0.85 * s.l));
      gr.addColorStop(1, hs(c.h, 88, 0));
      x.strokeStyle = gr;
      x.lineWidth = 1.4;
      x.beginPath();
      x.moveTo(s.x, s.y);
      x.lineTo(s.x - s.vx * 7, s.y - s.vy * 7);
      x.stroke();
      s.x += s.vx;
      s.y += s.vy;
      s.l -= 0.02;
      if (s.l <= 0) SS.splice(k, 1);
    }

    if (rm) {
      run = false;
      return;
    }
    requestAnimationFrame(frame);
  }

  st.kick = () => {
    if (!run && !document.hidden) {
      run = true;
      requestAnimationFrame(frame);
    }
  };

  st.setSection = (sectionId, { title = '', desc = '', textWrapEl = null, titleEl = null, descEl = null, animateText = true } = {}) => {
    st.t = getSectionHue(sectionId);
    if (titleEl && title) titleEl.textContent = title;
    if (descEl && desc) descEl.textContent = desc;
    if (animateText && textWrapEl) enter(textWrapEl);
    st.kick();
  };

  if (hero) {
    hero.addEventListener('pointermove', (e) => {
      const r = cv.getBoundingClientRect();
      mx = e.clientX - r.left;
      my = e.clientY - r.top;
    });
    hero.addEventListener('pointerleave', () => {
      mx = -999;
      my = -999;
    });
  }

  const ro = new ResizeObserver(size);
  ro.observe(cv);
  size();

  const io = new IntersectionObserver((entries) => {
    if (entries[0] && entries[0].isIntersecting) st.kick();
    else run = false;
  });
  io.observe(cv);

  document.addEventListener('visibilitychange', () => {
    if (document.hidden) run = false;
    else st.kick();
  });

  return st;
}

