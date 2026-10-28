/**
 * Miku Design System — Shared Motion Utilities
 * Implements the single shared enter(el), exit(el), swap(outEl, inEl) and list collapse utilities (§4).
 */

import { TOKENS } from './tokens.js';

export function prefersReducedMotion() {
  return typeof window !== 'undefined' &&
    typeof window.matchMedia === 'function' &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

/**
 * Regla de blur de entrada (§4):
 * Entra de opacity 0, blur(12px), scale .97, translateY(10px) a nítido en .6s --e.
 */
export function enter(el) {
  if (!el) return;
  el.hidden = false;
  el.classList.remove('bo', 'bi');
  if (!prefersReducedMotion()) {
    void el.offsetWidth;
    el.classList.add('bi');
  }
}

/**
 * Regla de blur de salida (§4):
 * Sale con blur(10px) y opacity 0 en .2s --e.
 */
export function exit(el, { hideOnComplete = false, removeOnComplete = false } = {}) {
  if (!el) return Promise.resolve();
  if (prefersReducedMotion()) {
    el.classList.remove('bi', 'bo');
    if (hideOnComplete) el.hidden = true;
    if (removeOnComplete) el.remove();
    return Promise.resolve();
  }
  el.classList.remove('bi');
  el.classList.add('bo');
  return new Promise((resolve) => {
    const finish = () => {
      el.removeEventListener('animationend', finish);
      el.classList.remove('bo');
      if (hideOnComplete) el.hidden = true;
      if (removeOnComplete) el.remove();
      resolve();
    };
    el.addEventListener('animationend', finish, { once: true });
    // Safety fallback bound to CSS animation token if animationend is suppressed (e.g. detached node)
    requestAnimationFrame(() => {
      if (!el.isConnected) finish();
    });
  });
}

/**
 * Transición entre dos vistas o pestañas (§4 y §7):
 * La vista saliente hace exit (0.2s) y la entrante hace enter (0.6s).
 */
export async function swap(outEl, inEl, onBeforeEnter) {
  if (outEl && !outEl.hidden) {
    await exit(outEl, { hideOnComplete: true });
  }
  if (typeof onBeforeEnter === 'function') {
    onBeforeEnter();
  }
  if (inEl) {
    enter(inEl);
  }
}

/**
 * Expansión de elemento en lista con grid-template-rows: 0fr -> 1fr (§4).
 */
export function collapseIn(wrapperEl) {
  if (!wrapperEl) return;
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      wrapperEl.classList.add('in');
    });
  });
}

/**
 * Colapso de elemento en lista con grid-template-rows: 1fr -> 0fr (§4).
 */
export function collapseOut(wrapperEl, { removeOnComplete = true } = {}) {
  if (!wrapperEl) return Promise.resolve();
  if (prefersReducedMotion()) {
    wrapperEl.classList.remove('in');
    if (removeOnComplete) wrapperEl.remove();
    return Promise.resolve();
  }
  wrapperEl.classList.remove('in');
  return new Promise((resolve) => {
    const done = (ev) => {
      if (ev && ev.target !== wrapperEl) return;
      wrapperEl.removeEventListener('transitionend', done);
      if (removeOnComplete) wrapperEl.remove();
      resolve();
    };
    wrapperEl.addEventListener('transitionend', done);
    requestAnimationFrame(() => {
      if (!wrapperEl.isConnected) done();
    });
  });
}

export const collapseAndRemove = collapseOut;

if (typeof window !== 'undefined') {
  window.MikuMotion = {
    prefersReducedMotion,
    enter,
    exit,
    swap,
    collapseIn,
    collapseOut,
    TOKENS
  };
}

