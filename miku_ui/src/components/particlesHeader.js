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

    // Fast clear without expensive destination-out compositing
    x.clearRect(0, 0, W, H);

    // Subtle ambient glow patch at cursor or center
    const glowX = mx > 0 ? mx : W * 0.5;
    const glowY = my > 0 ? my : H * 0.4;
    const grad = x.createRadialGradient(glowX, glowY, 4, glowX, glowY, 140);
    grad.addColorStop(0, hs(c.h, 60, 0.08));
    grad.addColorStop(1, 'transparent');
    x.fillStyle = grad;
    x.fillRect(0, 0, W, H);

    // Optimized Epic Cyber Dot-Matrix (<1% CPU)
    for (let i = 0; i < P.length; i++) {
      const q = P[i];
      const sp = 0.15 + q.z * 0.35;
      const angle = q.p + tNow * 0.0004;

      // Gentle interactive cursor influence
      const dx = q.x - mx;
      const dy = q.y - my;
      const distSq = dx * dx + dy * dy;

      if (distSq < 10000 && distSq > 4) {
        const dist = Math.sqrt(distSq);
        const force = (1 - dist / 100) * 0.4;
        q.vx += (dx / dist) * force;
        q.vy += (dy / dist) * force;
      }

      q.vx *= 0.94;
      q.vy *= 0.94;
      q.x += Math.cos(angle) * sp + q.vx;
      q.y += Math.sin(angle) * sp * 0.6 + q.vy;

      if (q.x > W + 4) q.x = -4;
      else if (q.x < -4) q.x = W + 4;
      if (q.y > H + 4) q.y = -4;
      else if (q.y < -4) q.y = H + 4;

      const alpha = (0.35 + 0.55 * Math.sin(tNow * 0.0018 + q.p)) * (0.4 + q.z * 0.6);
      const dotHue = (c.h + q.o * 0.3 + 360) % 360;

      // Draw epic crisp dots
      x.fillStyle = hs(dotHue, Math.min(95, c.l + q.z * 15), alpha);
      const dotSize = q.r <= 1.2 ? 1.5 : (q.r <= 1.8 ? 2.2 : 3.0);
      x.beginPath();
      x.arc(q.x, q.y, dotSize, 0, 6.283);
      x.fill();
    }

    // Occasional subtle shooting star
    if (tNow > ns) {
      ns = tNow + 5000 + Math.random() * 4000;
      SS.push({
        x: Math.random() * W * 0.7,
        y: Math.random() * H * 0.3,
        vx: 5 + Math.random() * 3,
        vy: 1.5 + Math.random() * 1.5,
        l: 1
      });
    }

    for (let k = SS.length - 1; k >= 0; k--) {
      const s = SS[k];
      const sgr = x.createLinearGradient(s.x, s.y, s.x - s.vx * 6, s.y - s.vy * 6);
      sgr.addColorStop(0, hs(c.h, 92, 0.7 * s.l));
      sgr.addColorStop(1, 'transparent');
      x.strokeStyle = sgr;
      x.lineWidth = 1.2;
      x.beginPath();
      x.moveTo(s.x, s.y);
      x.lineTo(s.x - s.vx * 6, s.y - s.vy * 6);
      x.stroke();
      s.x += s.vx;
      s.y += s.vy;
      s.l -= 0.025;
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

