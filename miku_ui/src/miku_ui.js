/**
 * Miku UI · Runtime de Componentes, Microinteracciones y Transiciones (Vanilla JS)
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
  const IC = {
    x: '<path d="M18 6L6 18M6 6l12 12"/>',
    ck: '<path d="M5 12l5 5 9-10"/>',
    info: '<circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8h.01"/>',
    bell: '<path d="M18 8a6 6 0 1 0-12 0c0 7-3 9-3 9h18s-3-2-3-9M13.7 21a2 2 0 0 1-3.4 0"/>'
  };
  const svg = n => `<svg class="ic" viewBox="0 0 24 24">${IC[n] || ''}</svg>`;

  /* ═══ GELATINA (§4) ═══ */
  function gel(box, sel, cb) {
    if (!box) return;
    if (!$('#goo')) {
      document.body.insertAdjacentHTML(
        'beforeend',
        '<svg width="0" height="0" style="position:absolute"><filter id="goo" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur in="SourceGraphic" stdDeviation="4" result="b"/><feColorMatrix in="b" values="1 0 0 0 0 0 1 0 0 0 0 0 1 0 0 0 0 0 22 -10"/></filter></svg>'
      );
    }
    const y = box.dataset.axis === 'y';
    const pad = +(box.dataset.pad || 0);
    const A = y ? ['top', 'bottom'] : ['left', 'right'];
    const ind = $(':scope>.ind', box) || box.insertBefore(el('i', 'ind'), box.firstChild);
    let last = null;
    const place = (b, anim) => {
      if (!b || !b.offsetWidth) return;
      const bRect = b.getBoundingClientRect();
      const boxRect = box.getBoundingClientRect();
      const st = (y ? (bRect.top - boxRect.top + box.scrollTop) : (bRect.left - boxRect.left + box.scrollLeft)) - pad;
      const sz = (y ? bRect.height : bRect.width) + pad * 2;
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
      ind.style[y ? 'left' : 'top'] = ((y ? (bRect.left - boxRect.left + box.scrollLeft) : (bRect.top - boxRect.top + box.scrollTop)) - pad) + 'px';
      ind.style[y ? 'width' : 'height'] = ((y ? bRect.width : bRect.height) + pad * 2) + 'px';
      ind.classList.add('rdy');
      last = st;
    };
    const items = () => $$(sel, box);
    items().forEach(b => b.addEventListener('click', () => {
      items().forEach(x => x.classList.toggle('on', x === b));
      place(b, true);
      cb && cb(b);
    }));
    box._gel = (anim = true) => {
      place($(sel + '.on', box), anim && last !== null);
    };
    requestAnimationFrame(() => box._gel(false));
  }

  const refresh = () => requestAnimationFrame(() => $$('.seg,.chips,.nav,#rail').forEach(b => b._gel && b._gel(true)));
  window.addEventListener('resize', () => $$('.seg,.chips,.nav,#rail').forEach(b => b._gel && b._gel(false)));

  /* ═══ BARRA / SLIDERS (§6) ═══ */
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

  /* ═══ MANTENER PULSADO (§5) ═══ */
  function hold(b, fn, ms = 1100) {
    if (!b) return;
    const lbl = b.textContent.trim();
    const ic = b.dataset.icon === 'reset'
      ? '<path d="M3 12a9 9 0 1 0 3-6.7L3 8M3 3v5h5"/>'
      : '<path d="M4 7h16M10 11v6M14 11v6M6 7l1 12a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2l1-12M9 7V4h6v3"/>';
    b.classList.add('hb');
    b.innerHTML = `<svg class="ic hi" viewBox="0 0 24 24">${ic}</svg><svg class="ic hk" viewBox="0 0 24 24"><path d="M5 12l5 5 9-10"/></svg><span></span>`;
    b.lastChild.textContent = lbl;
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
      if (performance.now() - st < 250) toast('Mantén pulsado para confirmar', 'wa');
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

  /* ═══ AVISOS Y MENSAJES (§8) ═══ */
  function toast(msg, type = 'ok') {
    const c = $('#toasts') || document.body.appendChild(Object.assign(el('div'), { id: 'toasts' }));
    const t = el('div', 'toast gl ' + type, '<i></i><span></span>');
    t.lastChild.textContent = msg;
    c.appendChild(t);
    setTimeout(() => {
      t.classList.add('out');
      setTimeout(() => t.remove(), 320);
    }, 2200);
  }

  function banner({ title, text, type = 'info', actions = [], ms = 6000 }) {
    const b = el('div', 'banner gl', '<span class="ni"><svg class="ic" viewBox="0 0 24 24">' + IC.bell + '</svg></span><div><b></b><small></small></div>');
    if (type === 'ok') b.style.setProperty('--c', 'var(--ok)');
    if (type === 'er') b.style.setProperty('--c', 'var(--er)');
    if (type === 'wa') b.style.setProperty('--c', 'var(--wa)');
    $('b', b).textContent = title;
    $('small', b).textContent = text || '';
    const close = () => {
      b.classList.add('out');
      setTimeout(() => b.remove(), 400);
    };
    actions.forEach(a => {
      const x = el('button', 'bt sm t');
      x.textContent = a.label;
      x.onclick = () => {
        a.fn && a.fn();
        close();
      };
      b.appendChild(x);
    });
    const x = el('button', 'ib sm x', svg('x'));
    x.setAttribute('aria-label', 'Cerrar');
    x.onclick = close;
    b.appendChild(x);
    document.body.appendChild(b);
    setTimeout(close, ms);
  }

  function dialog({ title, text, confirm = 'Aceptar', danger = false, onConfirm }) {
    const s = el('div', 'scrim'), h = el('div', 'sheet gl', '<h3></h3><p></p><div class="acts"></div>');
    $('h3', h).textContent = title;
    $('p', h).textContent = text || '';
    const close = () => {
      s.style.opacity = '0';
      setTimeout(() => s.remove(), 200);
    };
    const c = el('button', 'bt');
    c.textContent = 'Cancelar';
    c.onclick = close;
    const ok = el('button', 'bt ' + (danger ? '' : 'p'));
    ok.textContent = confirm;
    $('.acts', h).append(c, ok);
    s.appendChild(h);
    s.onclick = e => e.target === s && close();
    document.body.appendChild(s);
    if (danger) {
      hold(ok, () => {
        onConfirm && onConfirm();
        setTimeout(close, 500);
      });
    } else {
      ok.onclick = () => {
        onConfirm && onConfirm();
        close();
      };
    }
  }

  const upd = () => {
    const e = document.getElementById('ncount');
    if (e) e.textContent = $$('#ntfl .ntf:not(.go)').length;
  };

  function dismiss(n) {
    if (!n) return;
    n.classList.add('go');
    setTimeout(() => {
      n.remove();
      upd();
    }, 450);
  }

  function clearAll() {
    $$('#ntfl .ntf').forEach((n, i) => setTimeout(() => dismiss(n), i * 70));
  }

  function notify({ title, text, icon = 'bell', color, time = 'ahora', actions = [], progress, reply }) {
    const l = document.getElementById('ntfl');
    if (!l) return;
    const n = el('div', 'ntf in', '<span class="ni"><svg class="ic"><use href="#' + icon + '"/></svg></span><div style="flex:1;min-width:0"><div class="line" style="flex-wrap:nowrap"><b></b><span class="tm"></span></div><small class="tt"></small></div>');
    if (color) n.firstChild.style.setProperty('--c', color);
    $('b', n).textContent = title;
    $('.tm', n).textContent = time;
    $('.tt', n).textContent = text || '';
    const body = n.children[1];
    let bar = null;
    if (progress != null) {
      bar = el('div', 'pg ac', '<i></i>');
      bar.style.cssText = 'margin-top:8px;--v:' + progress + '%';
      body.appendChild(bar);
    }
    if (reply) {
      const f = el('div', 'fld pill', '<input class="tx" placeholder="Responder…"><button class="ib sm t" aria-label="Enviar"><svg class="ic"><use href="#send"/></svg></button>');
      f.style.marginTop = '8px';
      body.appendChild(f);
      $('button', f).onclick = () => {
        const i = $('input', f);
        if (i.value) {
          toast('Enviado', 'ok');
          i.value = '';
        }
      };
    }
    if (actions.length) {
      const r = el('div', 'rw');
      r.style.marginTop = '8px';
      actions.forEach((a, i) => {
        const b = el('button', 'bt sm' + (i ? '' : ' t'));
        b.textContent = a;
        b.onclick = () => dismiss(n);
        r.appendChild(b);
      });
      body.appendChild(r);
    }
    const x = el('button', 'ib sm x', svg('x'));
    x.setAttribute('aria-label', 'Descartar');
    x.onclick = () => dismiss(n);
    n.appendChild(x);
    l.prepend(n);
    upd();
    return { n, bar };
  }

  /* ═══ EXTRAS ═══ */
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

  /* ═══ TRANSICIONES (§18: go · swap · flip · cascade) ═══ */
  const RM = matchMedia('(prefers-reduced-motion:reduce)').matches;
  const SPR = (window.CSS && CSS.supports('animation-timing-function', 'linear(0,1)'))
    ? 'linear(0,.02 2%,.12 5%,.33 9%,.58 13%,.8 17%,.95 21%,1.02 26%,1.04 31%,1.02 37%,1.005 44%,.998 52%,1)'
    : 'cubic-bezier(.34,1.15,.64,1)';
  let pt = 0;

  function cascade(p, dir) {
    if (!p) return;
    p.style.setProperty('--dir', dir || 1);
    [...p.children].forEach((c, k) => c.style.setProperty('--k', Math.min(k, 9)));
  }

  function go(id) {
    const to = document.getElementById(id), from = document.querySelector('.pane.on');
    if (!to) return;
    if (to === from) {
      if (from.classList.contains('out')) {
        clearTimeout(pt);
        from.classList.remove('out');
      }
      return;
    }
    const ids = $$('#nav .nv, #rail .cat').map(b => b.dataset.p || b.dataset.cat);
    const dir = ids.indexOf(id) >= ids.indexOf(from ? (from.id || from.dataset.cat) : id) ? 1 : -1;
    clearTimeout(pt);
    $$('.pane').forEach(x => {
      if (x !== from) x.classList.remove('on', 'in', 'out');
    });
    const show = () => {
      from && from.classList.remove('on', 'in', 'out');
      cascade(to, dir);
      to.scrollTop = 0;
      to.classList.add('on', 'in');
      refresh();
      setTimeout(() => to.classList.remove('in'), 1200);
    };
    if (RM || !from) return show();
    from.style.setProperty('--dir', dir);
    from.classList.remove('in');
    from.classList.add('out');
    pt = setTimeout(show, 230);
  }

  function swap(box, fn, o = {}) {
    if (!box) { fn && fn(); return; }
    if (RM || !box.firstChild) { fn && fn(); return; }
    const d = o.dir || 0, soft = o.soft, sc = soft ? 1 : .9, x = d * 18;
    const out = [
      { opacity: 1, filter: 'blur(0)', scale: 1, translate: '0 0' },
      { opacity: 0, filter: 'blur(6px)', scale: sc, translate: (-x) + 'px ' + (soft && !d ? -4 : 0) + 'px' }
    ];
    box._sw && box._sw.cancel();
    const a = box.animate(out, { duration: soft ? 110 : 130, easing: 'cubic-bezier(.4,0,1,1)', fill: 'forwards' });
    box._sw = a;
    a.onfinish = () => {
      fn && fn();
      a.cancel();
      box._sw = box.animate(
        [
          { opacity: 0, filter: 'blur(8px)', scale: soft ? 1 : .88, translate: x + 'px ' + (soft && !d ? 4 : 0) + 'px' },
          { opacity: 1, filter: 'blur(0)', scale: 1, translate: '0 0' }
        ],
        { duration: soft ? 380 : 600, easing: SPR }
      );
    };
  }

  function flip(e, t) {
    if (!e) return;
    if (e.textContent === t) return;
    if (RM) { e.textContent = t; return; }
    e._fl && e._fl.cancel();
    const a = e.animate(
      [
        { opacity: 1, translate: '0 0', filter: 'blur(0)' },
        { opacity: 0, translate: '0 -6px', filter: 'blur(3px)' }
      ],
      { duration: 110, easing: 'ease-in', fill: 'forwards' }
    );
    e._fl = a;
    a.onfinish = () => {
      e.textContent = t;
      a.cancel();
      e._fl = e.animate(
        [
          { opacity: 0, translate: '0 6px', filter: 'blur(3px)' },
          { opacity: 1, translate: '0 0', filter: 'blur(0)' }
        ],
        { duration: 380, easing: SPR }
      );
    };
  }

  function init(root = document) {
    sliders(root);
  }

  return {
    gel,
    refresh,
    sliders,
    hold,
    toast,
    banner,
    dialog,
    dismiss,
    stepper,
    reveal,
    copy,
    notify,
    clearAll,
    go,
    swap,
    flip,
    cascade,
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
