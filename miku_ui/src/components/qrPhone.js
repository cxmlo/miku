/**
 * Miku Design System — QR Pairing SVG & Phone Mockup Components (Fase 3)
 * Exact implementation of qrSVG(t) and phone(inner) from miku-catalogo.html (lines 637-648).
 */

import { TOKENS } from '../design/tokens.js';
import { icon } from '../design/icons.js';
import { escapeHtml } from './primitives.js';
import { t } from '../i18n/es.js';

/**
 * Generador QR SVG nivel H con módulos redondeados (r=.46), ojos concéntricos
 * redondeados y cara de Mochi en el centro (~5% del área) — §7.1 del prompt y miku-catalogo.html.
 */
export function renderQrSvg(payloadUri) {
  const qrFactory = typeof window !== 'undefined' ? window.qrcode : null;
  if (typeof qrFactory !== 'function' || !payloadUri) {
    return `<div style="padding:40px 10px;color:${TOKENS.colors.ink};text-align:center;font-weight:800">QR no disponible</div>`;
  }
  const q = qrFactory(0, 'H');
  q.addData(String(payloadUri));
  q.make();
  const n = q.getModuleCount();
  const N = n + 2; // Zona de silencio de 1 módulo por lado
  const D = TOKENS.colors.ink;
  const L = TOKENS.colors.tx;
  const h = n / 2;

  let s = `<svg viewBox="0 0 ${N} ${N}" shape-rendering="geometricPrecision">`;
  function eye(a, b) {
    const x = a + 1;
    const y = b + 1;
    return (
      `<rect x="${x}" y="${y}" width="7" height="7" rx="2.4" fill="${D}"/>` +
      `<rect x="${x + 1}" y="${y + 1}" width="5" height="5" rx="1.6" fill="${L}"/>` +
      `<rect x="${x + 2}" y="${y + 2}" width="3" height="3" rx="1.1" fill="${D}"/>`
    );
  }
  s += eye(0, 0) + eye(n - 7, 0) + eye(0, n - 7);

  for (let r = 0; r < n; r++) {
    for (let c = 0; c < n; c++) {
      if ((r < 8 && c < 8) || (r < 8 && c >= n - 8) || (r >= n - 8 && c < 8)) continue;
      if (Math.abs(r + 0.5 - h) < 4 && Math.abs(c + 0.5 - h) < 4) continue;
      if (q.isDark(r, c)) {
        s += `<circle cx="${c + 1.5}" cy="${r + 1.5}" r=".46" fill="${D}"/>`;
      }
    }
  }

  const o = h + 1;
  s +=
    `<rect x="${o - 3.4}" y="${o - 3.4}" width="6.8" height="6.8" rx="2.2" fill="${D}"/>` +
    `<circle cx="${o}" cy="${o}" r="2.3" fill="${L}"/>` +
    `<rect x="${o - 1.1}" y="${o - 0.5}" width=".6" height="1.1" rx=".3" fill="${D}"/>` +
    `<rect x="${o + 0.5}" y="${o - 0.5}" width=".6" height="1.1" rx=".3" fill="${D}"/>` +
    `</svg>`;
  return s;
}

/**
 * Maqueta de teléfono (.ph) con fondo de pantalla real o "Sin imagen" — miku-catalogo.html (línea 648).
 */
export function renderPhoneMockup({ id = 'ph', wallpaperUrl = null, innerHtml = '' } = {}) {
  const hasWp = Boolean(wallpaperUrl);
  const wpStyle = hasWp ? ` style="background-image:url('${escapeHtml(wallpaperUrl)}')"` : '';
  return (
    `<div class="ph" id="${escapeHtml(id)}" data-w="${hasWp ? 1 : 0}">` +
      `<div class="none">${icon('img')}${escapeHtml(t('mikuLink.phoneNoImage'))}</div>` +
      `<div class="wp"${wpStyle}></div>` +
      `<span class="nt"></span>` +
      `${innerHtml}` +
      `<span class="hm"></span>` +
    `</div>`
  );
}

