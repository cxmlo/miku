/**
 * Miku UI · Runtime de Componentes y Microinteracciones (Vanilla JS)
 * Fuente de verdad: miku-catalogo.html & miku-componentes.md
 */
const MikuUI = (() => {
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const el = (t, c, h) => {
    const e = document.createElement(t);
    if (c) e.className = c;
    if (h) e.innerHTML = h;
    return e;
  };
  const svg = id => `<svg class="ic"><use href="#${id}"/></svg>`;

  /* ═══ SELECCIÓN GELATINA (§4) ═══ */
  function gel(box, sel, cb) {
    if (!box) return;
    const y = box.dataset.axis === 'y';
    const A = y ? ['top', 'bottom'] : ['left', 'right'];
    const pad = +(box.dataset.pad || 0);
    let ind = $('.ind', box);
    if (!ind) {
      ind = el('div', 'ind');
      box.prepend(ind);
    }
    let last = null;
    const place = (b, anim = true) => {
      if (!b) return;
      const st = (y ? b.offsetTop : b.offsetLeft) - pad;
      const sz = (y ? b.offsetHeight : b.offsetWidth) + pad * 2;
      const tot = y ? box.clientHeight : box.clientWidth;
      const lead = last === null || st > last ? A[1] : A[0];
      const trail = lead === A[1] ? A[0] : A[1];
      ind.style.transition = anim
        ? `${lead} ${box.dataset.ld || '.38s'} cubic-bezier(.2,.85,.25,1),${trail} ${box.dataset.tr || '.95s'} var(--spring)`
        : 'none';
      if (anim) {
        ind.classList.remove('vis');
        void ind.offsetWidth;
        ind.classList.add('vis');
      }
      ind.style[A[0]] = st + 'px';
      ind.style[A[1]] = (tot - st - sz) + 'px';
      ind.style[y ? 'left' : 'top'] = ((y ? b.offsetLeft : b.offsetTop) - pad) + 'px';
      ind.style[y ? 'width' : 'height'] = ((y ? b.offsetWidth : b.offsetHeight) + pad * 2) + 'px';
      ind.classList.add('rdy');
      last = st;
    };
    const items = () => $$(sel, box);
    items().forEach(b => b.addEventListener('click', () => {
      items().forEach(x => x.classList.toggle('on', x === b));
      place(b, true);
      cb && cb(b);
    }));
    box._gel = () => {
      last = null;
      place($(sel + '.on', box), false);
    };
    requestAnimationFrame(box._gel);
  }

  const refresh = () => requestAnimationFrame(() => $$('.seg,.chips,.nav').forEach(b => b._gel && b._gel()));
  window.addEventListener('resize', refresh);

  /* ═══ BARRAS DE VALOR / SLIDERS (§6) ═══ */
  function sliders(root = document) {
    $$('.sl', root).forEach(s => {
      if (s._b) return;
      s._b = 1;
      const mn = +(s.dataset.min || 0);
      const mx = +(s.dataset.max || 100);
      const u = s.dataset.unit ?? '%';
      const init = +(s.dataset.value || 50);
      s.innerHTML = (s.dataset.icon === 'vol' ? '<svg class="ic" viewBox="0 0 24 24"><path d="M11 5 6 9H2v6h4l5 4z"/><path d="M15.5 8.5a5 5 0 0 1 0 7"/></svg>' : '') +
        '<div class="sl-t" tabindex="0" role="slider"><div class="sl-f"></div><div class="sl-k"></div><div class="sl-b"></div></div><span class="sl-v"></span>';
      const t = $('.sl-t', s), f = $('.sl-f', s), k = $('.sl-k', s), b = $('.sl-b', s), v = $('.sl-v', s);
      const set = (n, ev) => {
        n = Math.max(mn, Math.min(mx, Math.round(n)));
        const p = (n - mn) / (mx - mn) * 100;
        f.style.width = p + '%';
        k.style.left = p + '%';
        b.style.left = p + '%';
        b.textContent = v.textContent = n + u;
        t.setAttribute('aria-valuemin', mn);
        t.setAttribute('aria-valuemax', mx);
        t.setAttribute('aria-valuenow', n);
        s.value = n;
        if (ev) s.dispatchEvent(new Event('input', { bubbles: true }));
      };
      const px = e => {
        const r = t.getBoundingClientRect();
        set(mn + (e.clientX - r.left) / r.width * (mx - mn), 1);
      };
      t.addEventListener('pointerdown', e => {
        t.setPointerCapture(e.pointerId);
        t.classList.add('drag');
        px(e);
      });
      t.addEventListener('pointermove', e => t.classList.contains('drag') && px(e));
      t.addEventListener('pointerup', () => t.classList.remove('drag'));
      t.addEventListener('dblclick', () => set(init, 1));
      t.addEventListener('keydown', e => {
        const d = { ArrowRight: 1, ArrowUp: 1, ArrowLeft: -1, ArrowDown: -1 }[e.key];
        if (d) {
          set(s.value + d * (e.shiftKey ? 10 : 1), 1);
          e.preventDefault();
        }
      });
      set(init);
      s._set = set;
    });
  }

  /* ═══ MANTENER PULSADO (§5 - .bt.hb) ═══ */
  function hold(b, fn, ms = 1100) {
    if (!b) return;
    const lbl = b.textContent.trim();
    const ic = b.dataset.icon === 'reset'
      ? '<path d="M3 12a9 9 0 1 0 3-6.7L3 8M3 3v5h5"/>'
      : '<path d="M4 7h16M10 11v6M14 11v6M6 7l1 12a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2l1-12M9 7V4h6v3"/>';
    b.classList.add('hb');
    b.innerHTML = `<svg class="ic hi" viewBox="0 0 24 24">${ic}</svg><svg class="ic hk" viewBox="0 0 24 24"><path d="M5 12l5 5 9-10"/></svg><span>${lbl}</span>`;
    let st = 0, raf = 0, on = false;
    const set = p => b.style.setProperty('--p', p);
    const frame = n => {
      const p = Math.min(1, (n - st) / ms);
      set(p);
      if (p >= 1) {
        on = false;
        b.classList.remove('hold');
        b.classList.add('done');
        navigator.vibrate && navigator.vibrate(15);
        fn && fn(b);
        setTimeout(() => {
          b.classList.remove('done', 'rb');
          set(0);
        }, 1000);
        return;
      }
      raf = requestAnimationFrame(frame);
    };
    const start = () => {
      if (on || b.classList.contains('done')) return;
      on = true;
      b.classList.remove('rb');
      b.classList.add('hold');
      st = performance.now();
      raf = requestAnimationFrame(frame);
    };
    const stop = () => {
      if (!on) return;
      on = false;
      cancelAnimationFrame(raf);
      b.classList.remove('hold');
      b.classList.add('rb');
      set(0);
    };
    b.addEventListener('pointerdown', e => {
      b.setPointerCapture(e.pointerId);
      start();
    });
    ['pointerup', 'pointercancel', 'pointerleave'].forEach(t => b.addEventListener(t, stop));
    b.addEventListener('keydown', e => {
      if ((e.key === ' ' || e.key === 'Enter') && !e.repeat) {
        e.preventDefault();
        start();
      }
    });
    b.addEventListener('keyup', e => (e.key === ' ' || e.key === 'Enter') && stop());
    b.addEventListener('contextmenu', e => e.preventDefault());
  }

  /* ═══ CONTADOR / STEPPER (§5) ═══ */
  function stepper(s, { min = 0, max = 99 } = {}) {
    if (!s) return;
    const o = $('output', s), [a, b] = $$('button', s);
    let v = +(o ? o.textContent : 0);
    const set = n => {
      v = Math.max(min, Math.min(max, n));
      if (o) o.textContent = v;
      if (a) a.disabled = v <= min;
      if (b) b.disabled = v >= max;
      s.value = v;
      s.dispatchEvent(new Event('input', { bubbles: true }));
    };
    if (a) a.onclick = () => set(v - 1);
    if (b) b.onclick = () => set(v + 1);
    set(v);
  }

  /* ═══ MOSTRAR / OCULTAR CLAVE (§7) ═══ */
  function reveal(btn, input, hint) {
    if (!btn || !input) return;
    btn.onclick = () => {
      const on = btn.getAttribute('aria-pressed') !== 'true';
      btn.setAttribute('aria-pressed', on);
      btn.setAttribute('aria-label', on ? 'Ocultar' : 'Mostrar');
      input.type = on ? 'text' : 'password';
      if (hint) hint.textContent = on ? 'Texto visible' : 'Texto oculto';
    };
  }

  /* ═══ COPIAR AL PORTAPAPELES (§5) ═══ */
  function copy(b, get) {
    if (!b) return;
    b.addEventListener('click', async () => {
      try {
        await navigator.clipboard.writeText(get ? get() : b.textContent);
      } catch (e) {}
      const h = b.innerHTML;
      b.classList.add('ok');
      b.innerHTML = svg('ck') + 'Copiado';
      setTimeout(() => {
        b.classList.remove('ok');
        b.innerHTML = h;
      }, 1500);
    });
  }

  /* ═══ SELECTOR / MENÚ FLOTANTE (§6 - .sel & #mn) ═══ */
  function select(selBtn, onChange) {
    if (!selBtn || selBtn._b) return;
    selBtn._b = 1;
    let mn = $('#mn');
    if (!mn) {
      mn = el('div');
      mn.id = 'mn';
      document.body.appendChild(mn);
    }
    const close = () => {
      mn.classList.remove('open');
      selBtn.setAttribute('aria-expanded', 'false');
    };
    selBtn.addEventListener('click', e => {
      e.stopPropagation();
      const isOpen = mn.classList.contains('open') && mn._for === selBtn;
      if (isOpen) return close();
      const opts = (selBtn.dataset.opts || '').split('|').map(s => s.trim()).filter(Boolean);
      const cur = selBtn.querySelector('span')?.textContent.trim();
      mn.innerHTML = opts.map(o => `<div class="mi${o === cur ? ' on' : ''}" data-val="${o}"><span>${o}</span><svg class="ic" viewBox="0 0 24 24" style="stroke:currentColor;fill:none;stroke-width:2.5"><path d="M5 12l5 5 9-10"/></svg></div>`).join('');
      mn._for = selBtn;
      mn.classList.add('open');
      selBtn.setAttribute('aria-expanded', 'true');
      const r = selBtn.getBoundingClientRect();
      const w = mn.offsetWidth || 200, h = mn.offsetHeight || 150;
      let x = r.left, y = r.bottom + 6;
      if (y + h > window.innerHeight - 12) y = Math.max(12, r.top - 6 - h);
      mn.style.left = Math.max(12, Math.min(x, window.innerWidth - w - 12)) + 'px';
      mn.style.top = Math.max(12, y) + 'px';
    });
    mn.addEventListener('click', e => {
      const it = e.target.closest('.mi');
      if (!it || mn._for !== selBtn) return;
      const val = it.dataset.val;
      const sp = selBtn.querySelector('span');
      if (sp) sp.textContent = val;
      close();
      onChange && onChange(val);
      selBtn.dispatchEvent(new CustomEvent('change', { detail: { value: val }, bubbles: true }));
    });
    document.addEventListener('pointerdown', e => {
      if (!e.target.closest('.sel,#mn')) close();
    });
  }

  function init(root = document) {
    sliders(root);
    $$('.sel', root).forEach(s => select(s));
  }

  return {
    gel,
    refresh,
    sliders,
    hold,
    stepper,
    reveal,
    copy,
    select,
    init
  };
})();

/* ═══ AUTO-INICIALIZACIÓN ═══ */
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => MikuUI.init());
} else {
  MikuUI.init();
}

/* ═══ MICROINTERACCIÓN GLOBAL: Luz que sigue al puntero en botones (§12) ═══ */
document.addEventListener('pointermove', e => {
  const t = e.target.closest('.bt,.ib,.fchip,.sel,.sec-btn');
  if (!t) return;
  const r = t.getBoundingClientRect();
  t.style.setProperty('--mx', (e.clientX - r.left) + 'px');
  t.style.setProperty('--my', (e.clientY - r.top) + 'px');
}, { passive: true });

window.MikuUI = MikuUI;
