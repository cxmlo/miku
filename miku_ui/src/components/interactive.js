/**
 * Miku Design System — Interactive Components (Fase 3)
 * Search Box (.srch with clear + Ctrl K), File DropZone (.dz), Shortcut Recorder (kbd),
 * Stepper (.stp), Reorderable Drag List (.ro / .rw).
 */

import { enter } from '../design/motion.js';
import { icon } from '../design/icons.js';
import { escapeHtml } from './primitives.js';
import { toast } from './feedback.js';
import { t } from '../i18n/es.js';

/**
 * Buscador con limpiar (.x2) y atajo (<kbd>Ctrl K</kbd>) — miku-catalogo.html (líneas 444, 738-739).
 */
export function renderSearchBox({ id = 'sq', placeholder = '', shortcut = 'Ctrl K' } = {}) {
  return `<div class="srch">${icon('search')}<input id="${escapeHtml(id)}" placeholder="${escapeHtml(placeholder)}" autocomplete="off" aria-label="${escapeHtml(placeholder)}"><button type="button" class="btn i q sm x2" hidden aria-label="Limpiar">${icon('x')}</button><kbd>${escapeHtml(shortcut)}</kbd></div>`;
}

export function mountSearchBox(srchEl, { listContainer = null, emptyEl = null, onFilter = null } = {}) {
  if (!srchEl || srchEl.dataset.srchMounted === '1') return;
  srchEl.dataset.srchMounted = '1';
  const input = srchEl.querySelector('input');
  const clearBtn = srchEl.querySelector('.x2');
  if (!input) return;

  const applyFilter = () => {
    const val = input.value.trim().toLowerCase();
    if (clearBtn) clearBtn.hidden = !val;
    if (listContainer) {
      let count = 0;
      listContainer.querySelectorAll('.rw, [data-search-item]').forEach((row) => {
        const match = row.textContent.toLowerCase().includes(val);
        if (match) count++;
        if (match && row.hidden) {
          row.hidden = false;
          enter(row);
        } else if (!match) {
          row.hidden = true;
        }
      });
      if (emptyEl) emptyEl.hidden = count > 0;
    }
    if (typeof onFilter === 'function') onFilter(val);
  };

  input.addEventListener('input', applyFilter);
  if (clearBtn) {
    clearBtn.addEventListener('click', () => {
      input.value = '';
      applyFilter();
      input.focus();
    });
  }
  document.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
      e.preventDefault();
      input.focus();
    }
  });
}

/**
 * Zona de soltar archivos (.dz) — miku-catalogo.html (líneas 446, 727-735).
 * Permite conectar un uploader asíncrono real (onUploadFile(file, setProgressPct)).
 */
export function mountDropZone(dzEl, { onUploadFile = null } = {}) {
  if (!dzEl || dzEl.dataset.dzMounted === '1') return;
  dzEl.dataset.dzMounted = '1';
  const fileInput = dzEl.querySelector('input[type="file"]');
  let fl = dzEl.querySelector('.fl');
  if (!fl) {
    fl = document.createElement('div');
    fl.className = 'fl';
    dzEl.appendChild(fl);
  }

  const handleFiles = (fileList) => {
    Array.from(fileList || []).forEach(async (file) => {
      const row = document.createElement('div');
      row.className = 'fi bi';
      const kb = Math.max(1, Math.round(file.size / 1024));
      row.innerHTML =
        `<span style="flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;text-align:left">${escapeHtml(file.name)}</span>` +
        `<div class="bar sm" style="max-width:90px"><i></i></div>` +
        `<span class="mu">${kb} KB</span>`;
      fl.appendChild(row);
      const fill = row.querySelector('i');
      const setPct = (pct, doneOk = false, isErr = false) => {
        if (!fill) return;
        fill.style.width = `${Math.max(0, Math.min(100, pct))}%`;
        if (isErr) fill.style.background = 'var(--er)';
        else if (doneOk || pct >= 100) fill.style.background = 'var(--ok)';
      };
      if (typeof onUploadFile === 'function') {
        try {
          setPct(15);
          await onUploadFile(file, setPct);
          setPct(100, true);
        } catch (err) {
          setPct(100, false, true);
        }
      } else {
        setPct(100, true);
      }
    });
  };

  ['dragenter', 'dragover'].forEach((evt) => {
    dzEl.addEventListener(evt, (e) => {
      e.preventDefault();
      dzEl.classList.add('on');
    });
  });
  dzEl.addEventListener('dragleave', (e) => {
    if (!dzEl.contains(e.relatedTarget)) dzEl.classList.remove('on');
  });
  dzEl.addEventListener('drop', (e) => {
    e.preventDefault();
    dzEl.classList.remove('on');
    handleFiles(e.dataTransfer.files);
  });
  dzEl.addEventListener('click', (e) => {
    if (e.target.tagName !== 'INPUT' && !e.target.closest('.fl') && fileInput) {
      fileInput.click();
    }
  });
  dzEl.addEventListener('keydown', (e) => {
    if ((e.key === 'Enter' || e.key === ' ') && fileInput) {
      e.preventDefault();
      fileInput.click();
    }
  });
  if (fileInput) {
    fileInput.addEventListener('change', () => {
      handleFiles(fileInput.files);
      fileInput.value = '';
    });
  }
}

/**
 * Grabador de atajos (kbd + botón Grabar) — miku-catalogo.html (líneas 740-746).
 */
export function mountShortcutRecorder(btnEl, displayEl, initialKeys = ['Ctrl', 'Alt', 'M'], onSave = null) {
  if (!btnEl || !displayEl || btnEl.dataset.recMounted === '1') return;
  btnEl.dataset.recMounted = '1';
  let recording = false;
  let currentKeys = Array.isArray(initialKeys) && initialKeys.length ? [...initialKeys] : ['Ctrl', 'Alt', 'M'];

  const renderKeys = (keys) => {
    displayEl.innerHTML = keys.map((k) => `<kbd>${escapeHtml(k)}</kbd>`).join(' ');
  };
  renderKeys(currentKeys);

  btnEl.addEventListener('click', () => {
    recording = !recording;
    btnEl.textContent = recording ? 'Presiona las teclas…' : 'Grabar';
    if (recording) {
      displayEl.innerHTML = '<span class="mu">…</span>';
    } else {
      renderKeys(currentKeys);
    }
  });

  document.addEventListener('keydown', (e) => {
    if (!recording) return;
    e.preventDefault();
    e.stopPropagation();
    if (e.key === 'Escape') {
      recording = false;
      btnEl.textContent = 'Grabar';
      renderKeys(currentKeys);
      return;
    }
    if (['Control', 'Shift', 'Alt', 'Meta'].includes(e.key)) return;
    const next = [];
    if (e.ctrlKey) next.push('Ctrl');
    if (e.altKey) next.push('Alt');
    if (e.shiftKey) next.push('Shift');
    if (e.metaKey) next.push('Win');
    next.push(e.key.length === 1 ? e.key.toUpperCase() : e.key);
    currentKeys = next;
    recording = false;
    btnEl.textContent = 'Grabar';
    renderKeys(next);
    toast('Atajo guardado', 'ok', next.join(' + '));
    if (typeof onSave === 'function') onSave(next);
  }, true);
}

/**
 * Pasos / Stepper (.stp) — miku-catalogo.html (líneas 747-750).
 */
export function mountStepper(stpEl, textEl, steps = [], initialStep = 0) {
  if (!stpEl || !steps.length) return { next: () => {}, prev: () => {}, set: () => {} };
  let cur = Math.max(0, Math.min(steps.length - 1, initialStep));
  stpEl.innerHTML = steps.map((_, i) => `${i ? '<span class="l"><i></i></span>' : ''}<span class="s"></span>`).join('');

  const update = () => {
    stpEl.querySelectorAll('.s').forEach((el, i) => {
      el.className = 's' + (i < cur ? ' d' : i === cur ? ' c' : '');
      el.innerHTML = i < cur ? icon('ck') : String(i + 1);
    });
    stpEl.querySelectorAll('.l').forEach((el, i) => {
      el.classList.toggle('d', i < cur);
    });
    if (textEl && steps[cur]) {
      textEl.textContent = `${steps[cur].title} · ${steps[cur].desc}`;
      enter(textEl);
    }
  };
  update();
  return {
    next: () => { cur = Math.min(steps.length - 1, cur + 1); update(); return cur; },
    prev: () => { cur = Math.max(0, cur - 1); update(); return cur; },
    set: (idx) => { cur = Math.max(0, Math.min(steps.length - 1, idx)); update(); return cur; }
  };
}

/**
 * Lista reordenable por arrastre (.ro / .rw) — miku-catalogo.html (líneas 751-759).
 * Las 3 primeras filas se marcan como "En la isla" (.chip.g) y dispara onReorder(orderedIds).
 */
export function mountReorderList(boxEl, items = [], { maxActive = 3, onReorder = null, onSelect = null } = {}) {
  if (!boxEl) return;
  boxEl.innerHTML = '';
  const ROW_H = 58;
  const order = [];

  items.forEach((item) => {
    const r = document.createElement('div');
    r.className = 'rw';
    r.dataset.id = String(item.id);
    r.style.cssText = 'position:absolute;left:0;right:0;top:0;height:52px;cursor:pointer';
    const initial = escapeHtml((item.name || item.label || 'A')[0].toUpperCase());
    r.innerHTML =
      `<span class="gp" aria-label="Arrastrar">${icon('grip')}</span>` +
      `<span class="av" style="width:28px;height:28px;font-size:12px">${initial}</span>` +
      `<b style="flex:1">${escapeHtml(item.name || item.label)}</b>` +
      `<span class="chip"></span>`;
    r.addEventListener('click', (e) => {
      if (e.target.closest('.gp')) return;
      if (typeof onSelect === 'function') onSelect(item.id, item);
    });
    boxEl.appendChild(r);
    order.push(r);
  });

  boxEl.style.height = `${Math.max(1, items.length) * ROW_H}px`;

  function layout(skipEl = null) {
    order.forEach((r, i) => {
      if (r !== skipEl) {
        r.style.translate = `0 ${i * ROW_H}px`;
      }
      const chip = r.querySelector('.chip');
      if (chip) {
        const onIsland = i < maxActive;
        chip.className = 'chip' + (onIsland ? ' g' : '');
        chip.textContent = onIsland ? 'En la isla' : 'Disponible';
      }
    });
  }
  layout();

  if (boxEl.dataset.roMounted === '1') return;
  boxEl.dataset.roMounted = '1';

  boxEl.addEventListener('pointerdown', (e) => {
    const g = e.target.closest('.gp');
    if (!g) return;
    const el = g.parentNode;
    const y0 = e.clientY;
    const rows = Array.from(boxEl.querySelectorAll('.rw'));
    rows.sort((a, b) => (parseFloat(a.style.translate?.split(' ')[1]) || 0) - (parseFloat(b.style.translate?.split(' ')[1]) || 0));
    const i0 = rows.indexOf(el);
    if (i0 < 0) return;

    el.classList.add('dr');
    try { g.setPointerCapture(e.pointerId); } catch (_) {}

    function move(ev) {
      const y = Math.max(0, Math.min((rows.length - 1) * ROW_H, i0 * ROW_H + ev.clientY - y0));
      el.style.translate = `0 ${y}px`;
      const nextIdx = Math.round(y / ROW_H);
      const curIdx = rows.indexOf(el);
      if (nextIdx !== curIdx && nextIdx >= 0 && nextIdx < rows.length) {
        rows.splice(curIdx, 1);
        rows.splice(nextIdx, 0, el);
        rows.forEach((r, idx) => {
          if (r !== el) r.style.translate = `0 ${idx * ROW_H}px`;
          const chip = r.querySelector('.chip');
          if (chip) {
            const onIsland = idx < maxActive;
            chip.className = 'chip' + (onIsland ? ' g' : '');
            chip.textContent = onIsland ? 'En la isla' : 'Disponible';
          }
        });
      }
    }

    function up() {
      g.removeEventListener('pointermove', move);
      g.removeEventListener('pointerup', up);
      g.removeEventListener('pointercancel', up);
      el.classList.remove('dr');
      rows.forEach((r, idx) => {
        r.style.translate = `0 ${idx * ROW_H}px`;
        const chip = r.querySelector('.chip');
        if (chip) {
          const onIsland = idx < maxActive;
          chip.className = 'chip' + (onIsland ? ' g' : '');
          chip.textContent = onIsland ? 'En la isla' : 'Disponible';
        }
      });
      if (typeof onReorder === 'function') {
        onReorder(rows.map((r) => r.dataset.id));
      }
    }

    g.addEventListener('pointermove', move);
    g.addEventListener('pointerup', up);
    g.addEventListener('pointercancel', up);
  });
}

