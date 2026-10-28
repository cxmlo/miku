/**
 * Miku Design System — Overlays, Menus, Modals & Accordions (Fase 3)
 * Selector/Dropdown (.mw / .menu), Context Menu (#cm), Modal (.ov / .win),
 * Side Panel (.ov.side), Confirmation Dialog (.hb.r), Accordion (.acc).
 */

import { icon } from '../design/icons.js';
import { escapeHtml, mountHoldButton } from './primitives.js';
import { t } from '../i18n/es.js';

/**
 * Selector / menú desplegable (.mw > button + .menu[role=menu])
 * Idéntico a #mw / .menu de miku-catalogo.html (líneas 525-529).
 */
export function renderDropdown({ id = '', label = '', options = [], selectedValue = '' } = {}) {
  const current = options.find((o) => String(o.value) === String(selectedValue)) || options[0] || { label, value: '' };
  const itemsHtml = options.map((opt) => {
    const checked = String(opt.value) === String(current.value);
    return `<button type="button" role="menuitemradio" data-val="${escapeHtml(opt.value)}" aria-checked="${checked}">${escapeHtml(opt.label)}${icon('ck', { className: 'ic k' })}</button>`;
  }).join('');
  return `<div class="mw"${id ? ` id="${escapeHtml(id)}"` : ''}><button type="button" class="btn" data-trig="1"><span class="mw-lbl">${escapeHtml(current.label)}</span>${icon('chevDown')}</button><div class="menu" role="menu" data-open="false">${itemsHtml}</div></div>`;
}

export function mountDropdown(mwEl, onSelect) {
  if (!mwEl || mwEl.dataset.mwMounted === '1') return;
  mwEl.dataset.mwMounted = '1';
  const trig = mwEl.querySelector('[data-trig], > button');
  const menu = mwEl.querySelector('.menu');
  if (!trig || !menu) return;

  const setOpen = (open) => {
    menu.dataset.open = String(Boolean(open));
    trig.setAttribute('aria-expanded', String(Boolean(open)));
  };

  trig.addEventListener('click', (e) => {
    e.stopPropagation();
    const next = menu.dataset.open !== 'true';
    document.querySelectorAll('.mw .menu[data-open="true"]').forEach((m) => {
      if (m !== menu) m.dataset.open = 'false';
    });
    setOpen(next);
  });

  menu.addEventListener('click', (e) => {
    const item = e.target.closest('button[role="menuitemradio"], button[role="menuitem"]');
    if (!item) return;
    const all = menu.querySelectorAll('button[role="menuitemradio"]');
    all.forEach((x) => x.setAttribute('aria-checked', String(x === item)));
    const lbl = mwEl.querySelector('.mw-lbl');
    if (lbl) lbl.textContent = item.textContent.trim();
    setOpen(false);
    if (typeof onSelect === 'function') {
      onSelect(item.dataset.val, item);
    }
  });

  document.addEventListener('click', (e) => {
    if (!mwEl.contains(e.target)) setOpen(false);
  });
}

/**
 * Acordeón (.acc) idéntico a #acc de miku-catalogo.html (líneas 429-432, 531).
 */
export function mountAccordions(root = document) {
  root.querySelectorAll('.acc > div > button').forEach((b) => {
    if (b.dataset.accMounted === '1') return;
    b.dataset.accMounted = '1';
    b.addEventListener('click', () => {
      const expanded = b.getAttribute('aria-expanded') === 'true';
      b.setAttribute('aria-expanded', String(!expanded));
    });
  });
}

/**
 * Ventana modal (.ov / .win) y Panel lateral (.ov.side) — §7 de miku-design-system.
 * Cierra con Escape, clic fuera y botón X.
 */
export function setModalOpen(ovEl, isOpen) {
  if (!ovEl) return;
  ovEl.dataset.open = String(Boolean(isOpen));
}

export function mountModals(root = document) {
  root.querySelectorAll('[data-open]').forEach((b) => {
    if (b.classList.contains('ov') || b.dataset.modalTrig === '1') return;
    b.dataset.modalTrig = '1';
    b.addEventListener('click', () => {
      const target = document.getElementById(b.dataset.open);
      if (target) setModalOpen(target, true);
    });
  });

  root.querySelectorAll('.ov').forEach((ov) => {
    if (ov.dataset.ovMounted === '1') return;
    ov.dataset.ovMounted = '1';
    ov.addEventListener('click', (e) => {
      if (e.target === ov || e.target.closest('[data-close]')) {
        setModalOpen(ov, false);
      }
    });
  });

  if (!document.body.dataset.escModalBound) {
    document.body.dataset.escModalBound = '1';
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        document.querySelectorAll('.ov[data-open="true"]').forEach((ov) => setModalOpen(ov, false));
        const cm = document.getElementById('cm');
        if (cm) cm.dataset.open = 'false';
      }
    });
  }
}

/**
 * Diálogo de confirmación con botón de mantener rojo (#m3 de miku-catalogo.html)
 */
export function openConfirmDialog({
  title = '',
  desc = '',
  restLabel = t('hold.deleteRest'),
  holdLabel = t('hold.deleteHold'),
  doneLabel = t('hold.deleteDone'),
  onConfirm = null
} = {}) {
  let ov = document.getElementById('miku-confirm-ov');
  if (!ov) {
    ov = document.createElement('div');
    ov.className = 'ov';
    ov.id = 'miku-confirm-ov';
    ov.dataset.open = 'false';
    document.body.appendChild(ov);
    ov.addEventListener('click', (e) => {
      if (e.target === ov || e.target.closest('[data-close]')) setModalOpen(ov, false);
    });
  }
  ov.innerHTML =
    `<div class="win" role="dialog" aria-modal="true" aria-label="${escapeHtml(title)}">` +
      `<div class="wb">` +
        `<b style="font-size:16px">${escapeHtml(title)}</b>` +
        `<p class="mu" style="margin:6px 0 16px">${escapeHtml(desc)}</p>` +
        `<div class="row" style="justify-content:flex-end">` +
          `<button type="button" class="btn" data-close>${escapeHtml(t('app.cancel'))}</button>` +
          `<button type="button" class="hb r" style="min-width:170px" data-r="${escapeHtml(restLabel)}" data-h="${escapeHtml(holdLabel)}" data-d="${escapeHtml(doneLabel)}"></button>` +
        `</div>` +
      `</div>` +
    `</div>`;
  const hb = ov.querySelector('.hb');
  mountHoldButton(hb, () => {
    if (typeof onConfirm === 'function') onConfirm();
    setModalOpen(ov, false);
  });
  setModalOpen(ov, true);
}

/**
 * Menú contextual (#cm de miku-catalogo.html)
 */
export function mountContextMenu(targetEl, items = [], onSelect = null) {
  let cm = document.getElementById('cm');
  if (!cm) {
    cm = document.createElement('div');
    cm.className = 'menu';
    cm.id = 'cm';
    cm.setAttribute('role', 'menu');
    cm.dataset.open = 'false';
    document.body.appendChild(cm);
    document.addEventListener('click', () => {
      cm.dataset.open = 'false';
    });
  }
  if (!targetEl) return;
  targetEl.addEventListener('contextmenu', (e) => {
    e.preventDefault();
    cm.innerHTML = items.map((it) =>
      `<button type="button" role="menuitem" data-act="${escapeHtml(it.id)}"${it.danger ? ' style="color:var(--er)"' : ''}>${escapeHtml(it.label)}</button>`
    ).join('');
    cm.querySelectorAll('button').forEach((b) => {
      b.addEventListener('click', () => {
        cm.dataset.open = 'false';
        if (typeof onSelect === 'function') onSelect(b.dataset.act);
      });
    });
    cm.style.left = `${Math.min(e.clientX, window.innerWidth - 200)}px`;
    cm.style.top = `${Math.min(e.clientY, window.innerHeight - 150)}px`;
    cm.dataset.open = 'true';
  });
}

