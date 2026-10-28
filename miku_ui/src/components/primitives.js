/**
 * Miku Design System — Primitive Components (Fase 3)
 * Buttons, HoldButton (.hb), Segmented/Tabs (group), Switch (.tg), Checkbox (.ck),
 * Radio (.rd), Slider (.sl), Floating Field (.fld), Chips (.chip), Setting Row (.line).
 */

import { TOKENS } from '../design/tokens.js';
import { enter } from '../design/motion.js';
import { icon, arcLoader } from '../design/icons.js';
import { t } from '../i18n/es.js';

export function escapeHtml(str) {
  return String(str ?? '').replace(/[&<>"]/g, (ch) => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;'
  }[ch]));
}

/**
 * Fila de ajuste (.line)
 */
export function renderSettingRow(title, description, controlHtml) {
  const desc = description ? `<span class="d">${escapeHtml(description)}</span>` : '';
  return `<div class="line"><div><b>${escapeHtml(title)}</b>${desc}</div>${controlHtml}</div>`;
}

/**
 * Botón (.btn) con variantes: '' (neutro), 'p' (principal), 'g' (confirmar),
 * 'q' (fantasma), 'r' (destructivo), 'i' (icono), 'sm' (pequeño).
 */
export function renderButton({
  label = '',
  variant = '',
  size = '',
  iconName = '',
  tip = '',
  ariaLabel = '',
  disabled = false,
  id = '',
  dataAction = ''
} = {}) {
  const cls = ['btn', variant, size].filter(Boolean).join(' ');
  const attrs = [
    id ? `id="${escapeHtml(id)}"` : '',
    tip ? `data-tip="${escapeHtml(tip)}"` : '',
    ariaLabel ? `aria-label="${escapeHtml(ariaLabel)}"` : '',
    dataAction ? `data-a="${escapeHtml(dataAction)}"` : '',
    disabled ? 'disabled' : ''
  ].filter(Boolean).join(' ');
  const ic = iconName ? icon(iconName) : '';
  return `<button type="button" class="${cls}" ${attrs}>${ic}${escapeHtml(label)}</button>`;
}

/**
 * Estado cargando en botón (arco continuo 14px + etiqueta)
 */
export function setButtonLoading(btnEl, isLoading, loadingText = t('app.loading')) {
  if (!btnEl) return;
  if (isLoading) {
    if (!btnEl.dataset.origHtml) {
      btnEl.dataset.origHtml = btnEl.innerHTML;
    }
    btnEl.disabled = true;
    btnEl.innerHTML = `${arcLoader({ size: 14 })}${escapeHtml(loadingText)}`;
  } else {
    btnEl.disabled = false;
    if (btnEl.dataset.origHtml) {
      btnEl.innerHTML = btnEl.dataset.origHtml;
      delete btnEl.dataset.origHtml;
    }
  }
}

/**
 * Botón de mantener (.hb) idéntico a miku-catalogo.html (líneas 548-561).
 * Variantes: '' (neutro), 'p' (blanco), 'g' (verde), 'r' (rojo).
 */
export function mountHoldButton(b, onComplete) {
  if (!b || b.dataset.hbMounted === '1') return;
  b.dataset.hbMounted = '1';

  const restLabel = b.dataset.r || b.textContent.trim() || t('hold.confirmRest');
  const holdLabel = b.dataset.h || t('hold.confirmHold');
  const doneLabel = b.dataset.d || t('hold.confirmDone');
  b.dataset.r = restLabel;
  b.dataset.h = holdLabel;
  b.dataset.d = doneLabel;

  const checkSvg = '<svg style="width:15px;height:15px;stroke:currentColor;fill:none;stroke-width:2.2;stroke-linecap:round;stroke-linejoin:round" viewBox="0 0 24 24"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>';
  const layerHtml =
    `<span class="t">` +
      `<span class="r">${escapeHtml(restLabel)}</span>` +
      `<span class="h">${escapeHtml(holdLabel)}</span>` +
      `<span class="dn">${checkSvg}${escapeHtml(doneLabel)}</span>` +
    `</span>`;

  b.type = 'button';
  b.innerHTML = `${layerHtml}<span class="f" aria-hidden="true">${layerHtml}</span>`;
  b.dataset.s = 'idle';
  b.setAttribute('aria-label', restLabel);

  let holdTimer = null;
  let resetTimer = null;

  function finish() {
    b.dataset.s = 'done';
    b.dispatchEvent(new CustomEvent('hold-complete', { bubbles: true }));
    if (typeof onComplete === 'function') {
      onComplete(b);
    }
    clearTimeout(resetTimer);
    resetTimer = setTimeout(() => {
      b.dataset.s = 'idle';
    }, TOKENS.motion.loadMs + 100);
  }

  function startHold() {
    if (b.disabled || b.dataset.s === 'done') return;
    b.dataset.s = 'hold';
    clearTimeout(holdTimer);
    const ms = parseInt(getComputedStyle(b).getPropertyValue('--hold'), 10) || TOKENS.motion.holdMs;
    holdTimer = setTimeout(finish, ms);
  }

  function cancelHold() {
    if (b.dataset.s !== 'hold') return;
    clearTimeout(holdTimer);
    b.dataset.s = 'idle';
  }

  b.addEventListener('pointerdown', (e) => {
    if (e.button > 0) return;
    try { b.setPointerCapture(e.pointerId); } catch (_) {}
    startHold();
  });
  ['pointerup', 'pointercancel', 'lostpointercapture', 'blur'].forEach((evtName) => {
    b.addEventListener(evtName, cancelHold);
  });
  b.addEventListener('keydown', (e) => {
    if ((e.key === ' ' || e.key === 'Enter') && !e.repeat) {
      e.preventDefault();
      startHold();
    }
  });
  b.addEventListener('keyup', (e) => {
    if (e.key === ' ' || e.key === 'Enter') {
      cancelHold();
    }
  });
  b.addEventListener('contextmenu', (e) => e.preventDefault());
}

export function mountAllHoldButtons(root = document) {
  root.querySelectorAll('.hb').forEach((el) => mountHoldButton(el));
}

/**
 * Segmentado (.seg) y Pestañas (.tabs) con indicador elástico (.ind.fwd / .ind.bwd)
 * Idéntico a group(el, cb) de miku-catalogo.html (líneas 496-507).
 */
export function mountGroup(el, onChange) {
  if (!el) return () => {};
  let ind = el.querySelector(':scope > .ind');
  if (!ind) {
    ind = document.createElement('span');
    ind.className = 'ind';
    el.insertBefore(ind, el.firstChild);
  }
  const buttons = Array.from(el.querySelectorAll(':scope > button'));
  if (!buttons.length) return () => {};

  let cur = 0;
  buttons.forEach((b, i) => {
    if (b.getAttribute('aria-pressed') === 'true' || b.classList.contains('on')) {
      cur = i;
      b.setAttribute('aria-pressed', 'true');
    } else if (!b.hasAttribute('aria-pressed')) {
      b.setAttribute('aria-pressed', 'false');
    }
  });

  function place(i, dirClass) {
    const target = buttons[i];
    if (!target) return;
    ind.className = 'ind' + (dirClass ? ' ' + dirClass : '');
    ind.style.left = target.offsetLeft + 'px';
    ind.style.right = Math.max(0, el.clientWidth - target.offsetLeft - target.offsetWidth) + 'px';
  }

  function pick(i, animate) {
    if (i < 0 || i >= buttons.length) return;
    const prev = cur;
    buttons.forEach((b, k) => {
      b.setAttribute('aria-pressed', String(k === i));
      b.classList.toggle('on', k === i);
    });
    place(i, animate ? (i > prev ? 'fwd' : 'bwd') : '');
    cur = i;
    if (animate && typeof onChange === 'function') {
      onChange(i, buttons[i]);
    }
  }

  buttons.forEach((b, i) => {
    b.addEventListener('click', () => {
      if (i !== cur) pick(i, true);
    });
    b.addEventListener('keydown', (e) => {
      const next = e.key === 'ArrowRight' ? cur + 1 : e.key === 'ArrowLeft' ? cur - 1 : null;
      if (next !== null && next >= 0 && next < buttons.length) {
        e.preventDefault();
        pick(next, true);
        buttons[next].focus();
      }
    });
  });

  place(cur, '');
  const re = () => place(cur, '');
  window.addEventListener('resize', re);
  if (document.fonts && document.fonts.ready) {
    document.fonts.ready.then(re);
  }
  requestAnimationFrame(re);
  return (index, animate = false) => pick(index, animate);
}

/**
 * Deslizador (.sl y .sl.g) idéntico a upd(s) de miku-catalogo.html (línea 516).
 */
export function updateSliderFill(sliderEl) {
  if (!sliderEl) return;
  const min = parseFloat(sliderEl.min || '0');
  const max = parseFloat(sliderEl.max || '100');
  const val = parseFloat(sliderEl.value || '0');
  const pct = max > min ? ((val - min) / (max - min)) * 100 : 0;
  sliderEl.style.setProperty('--v', `${pct}%`);
  const outId = sliderEl.dataset.o;
  if (outId) {
    const outEl = document.getElementById(outId);
    if (outEl) outEl.textContent = String(sliderEl.value);
  }
}

export function mountSliders(root = document) {
  root.querySelectorAll('input[type="range"].sl').forEach((s) => {
    updateSliderFill(s);
    if (s.dataset.slMounted !== '1') {
      s.dataset.slMounted = '1';
      s.addEventListener('input', () => updateSliderFill(s));
    }
  });
}

/**
 * Interruptor (.tg), Casilla (.ck) y Radio (.rd)
 */
export function renderSwitch({ checked = false, ariaLabel = '', id = '', dataKey = '' } = {}) {
  return `<button type="button" class="tg" role="switch" aria-checked="${Boolean(checked)}"${ariaLabel ? ` aria-label="${escapeHtml(ariaLabel)}"` : ''}${id ? ` id="${escapeHtml(id)}"` : ''}${dataKey ? ` data-k="${escapeHtml(dataKey)}"` : ''}></button>`;
}

export function renderCheckbox({ checked = false, label = '', id = '' } = {}) {
  const ck = `<button type="button" class="ck" role="checkbox" aria-checked="${Boolean(checked)}"${id ? ` id="${escapeHtml(id)}"` : ''}><svg viewBox="0 0 24 24"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg></button>`;
  return label ? `<label class="opt">${ck}${escapeHtml(label)}</label>` : ck;
}

export function renderRadio({ checked = false, label = '', group = '' } = {}) {
  const rd = `<button type="button" class="rd" role="radio" aria-checked="${Boolean(checked)}"${group ? ` data-group="${escapeHtml(group)}"` : ''}></button>`;
  return label ? `<label class="opt">${rd}${escapeHtml(label)}</label>` : rd;
}

/**
 * Campo con etiqueta flotante (.fld)
 */
export function renderFloatingField({ id = '', label = '', value = '', type = 'text', valid = false, error = false } = {}) {
  const cls = ['fld', valid ? 'ok' : '', error ? 'er' : ''].filter(Boolean).join(' ');
  const fid = id || `fld-${Math.random().toString(36).slice(2, 8)}`;
  return `<div class="${cls}"><input id="${escapeHtml(fid)}" type="${escapeHtml(type)}" placeholder=" " value="${escapeHtml(value)}" autocomplete="off"><label for="${escapeHtml(fid)}">${escapeHtml(label)}</label></div>`;
}

/**
 * Chips interactivos (.chip)
 */
export function mountChips(containerEl, onSelect) {
  if (!containerEl) return;
  const chips = Array.from(containerEl.querySelectorAll('.chip:not(.g):not(.r)'));
  chips.forEach((c, idx) => {
    const activate = () => {
      chips.forEach((x) => x.setAttribute('aria-pressed', String(x === c)));
      if (typeof onSelect === 'function') onSelect(idx, c);
    };
    c.addEventListener('click', activate);
    c.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        activate();
      }
    });
  });
}

export { enter };

