/**
 * Miku Design System — Feedback, Progress & Loaders (Fase 3)
 * Stacked Toasts (.toasts/.toast) with pause-on-hover timer bar, Inline Alerts (.al),
 * Empty State (.emp), Error State with Retry, Progress Bar (.bar), Progress Ring (.ring),
 * Arc Loader (.ld), Wave Loader (.wv), Skeleton (.sk).
 */

import { TOKENS } from '../design/tokens.js';
import { exit, collapseIn, collapseOut } from '../design/motion.js';
import { icon, arcLoader, waveLoader } from '../design/icons.js';
import { escapeHtml } from './primitives.js';
import { t } from '../i18n/es.js';

const TOAST_ICONS = Object.freeze({
  n: 'info',
  ok: 'check',
  er: 'error'
});

export function ensureToastContainer() {
  let box = document.getElementById('toasts');
  if (!box) {
    box = document.createElement('div');
    box.className = 'toasts';
    box.id = 'toasts';
    box.setAttribute('aria-live', 'polite');
    document.body.appendChild(box);
  }
  return box;
}

/**
 * Avisos apilados abajo al centro (.toasts / .toast) — §7 de miku-design-system.
 * Entran con resorte + blur, salen colapsando su altura, incluyen barra de tiempo de 3 s
 * y se pausan al pasar el cursor (hover).
 */
export function toast(message, variant = 'n', subtitle = '') {
  let rawV = variant;
  let sub = subtitle;
  let customMs = null;
  if (variant && typeof variant === 'object') {
    rawV = variant.type || variant.variant || 'n';
    sub = variant.subtitle || variant.sub || subtitle || '';
    if (typeof variant.duration === 'number' && variant.duration > 0) {
      customMs = variant.duration;
    }
  }
  const v = rawV === true || rawV === 'ok' ? 'ok' : rawV === false || rawV === 'er' ? 'er' : 'n';
  const box = ensureToastContainer();
  const wrapper = document.createElement('div');
  wrapper.className = 'tw';

  const icSvg = icon(TOAST_ICONS[v] || 'info');
  const subHtml = sub ? `<small>${escapeHtml(sub)}</small>` : '';
  wrapper.innerHTML =
    `<div>` +
      `<div class="toast ${escapeHtml(v)}">` +
        `<span class="tk">${icSvg}</span>` +
        `<div>${escapeHtml(message)}${subHtml}</div>` +
      `</div>` +
    `</div>`;

  box.appendChild(wrapper);
  while (box.children.length > 4) {
    collapseOut(box.firstElementChild, { removeOnComplete: true });
  }
  collapseIn(wrapper);

  let remainingMs = customMs || TOKENS.motion.toastMs;
  let startedAt = performance.now();
  let timerId = null;

  const scheduleClose = (ms) => {
    clearTimeout(timerId);
    startedAt = performance.now();
    timerId = setTimeout(() => {
      collapseOut(wrapper, { removeOnComplete: true });
    }, ms);
  };

  wrapper.addEventListener('pointerenter', () => {
    clearTimeout(timerId);
    remainingMs = Math.max(400, remainingMs - (performance.now() - startedAt));
  });
  wrapper.addEventListener('pointerleave', () => {
    scheduleClose(remainingMs);
  });

  scheduleClose(remainingMs);
  return wrapper;
}
toast.show = toast;

/**
 * Alerta en línea (.al, .al.ok, .al.er)
 */
export function renderAlert({
  title = '',
  desc = '',
  variant = '',
  actionLabel = '',
  actionVariant = 'p sm',
  actionData = '',
  dismissible = false
} = {}) {
  const cls = ['al', variant].filter(Boolean).join(' ');
  const icName = variant === 'ok' ? 'check' : variant === 'er' ? 'error' : 'info';
  const actBtn = actionLabel
    ? `<button type="button" class="btn ${escapeHtml(actionVariant)}"${actionData ? ` data-a="${escapeHtml(actionData)}"` : ''}>${escapeHtml(actionLabel)}</button>`
    : '';
  const closeBtn = dismissible
    ? `<button type="button" class="btn i q sm x" aria-label="${escapeHtml(t('app.close'))}">${icon('x')}</button>`
    : '';
  return `<div class="${cls}">${icon(icName)}<div><b>${escapeHtml(title)}</b><span>${escapeHtml(desc)}</span></div>${actBtn}${closeBtn}</div>`;
}

export function mountDismissibleAlerts(root = document) {
  root.addEventListener('click', (e) => {
    const closeBtn = e.target.closest('.al .x');
    if (closeBtn) {
      const alertEl = closeBtn.closest('.al');
      if (alertEl) exit(alertEl, { removeOnComplete: true });
    }
  });
}

/**
 * Estado vacío (.emp)
 */
export function renderEmptyState({
  title = '',
  desc = '',
  subtitle = '',
  actionLabel = '',
  actionData = '',
  iconName = 'empty'
} = {}) {
  const description = desc || subtitle || '';
  const btnHtml = actionLabel
    ? `<button type="button" class="btn sm"${actionData ? ` data-a="${escapeHtml(actionData)}"` : ''}>${escapeHtml(actionLabel)}</button>`
    : '';
  return `<div class="emp">${icon(iconName, { style: 'width:26px;height:26px' })}<b>${escapeHtml(title)}</b><span>${escapeHtml(description)}</span>${btnHtml}</div>`;
}

/**
 * Estado de error con botón de reintento real (.al.er)
 */
export function renderErrorState({
  title = '',
  desc = '',
  subtitle = '',
  retryAction = 'retry'
} = {}) {
  return renderAlert({
    title,
    desc: desc || subtitle || '',
    variant: 'er',
    actionLabel: t('app.retry'),
    actionVariant: 'r sm',
    actionData: retryAction
  });
}

/**
 * Actualizar barra y anillo de progreso (.bar y .ring) — circunferencia = 138.2
 */
export function setProgress({ barFillEl = null, ringEl = null, pct = 0 } = {}) {
  const clamped = Math.max(0, Math.min(100, Number(pct) || 0));
  if (barFillEl) {
    barFillEl.style.width = `${clamped}%`;
  }
  if (ringEl) {
    const fg = ringEl.querySelector('.fg');
    const txt = ringEl.querySelector('b');
    if (fg) fg.style.strokeDashoffset = String(138.2 * (1 - clamped / 100));
    if (txt) txt.textContent = `${Math.round(clamped)}%`;
    ringEl.classList.toggle('done', clamped >= 100);
  }
}

export { arcLoader, waveLoader };

