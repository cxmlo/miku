/**
 * sound_fx.js — Sistema modular de efectos de sonido sintetizados (Web Audio API)
 * Diseñado para Miku Dynamic Island y Miku Settings.
 * No requiere archivos externos, tiene latencia ultra-baja (<5ms)
 * y respuesta táctil estilo Apple / iOS Taptic Engine.
 */
const SoundFX = (() => {
  'use strict';

  let ctx = null;

  function getAudioContext() {
    if (!ctx) {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (AudioCtx) {
        ctx = new AudioCtx();
      }
    }
    if (ctx && ctx.state === 'suspended') {
      ctx.resume().catch(() => {});
    }
    return ctx;
  }

  function getVolume() {
    try {
      if (window.CFG && typeof window.CFG.sfx_volume === 'number') {
        return Math.max(0, Math.min(1, window.CFG.sfx_volume / 100));
      }
      const raw = localStorage.getItem('miku_cfg');
      if (raw) {
        const parsed = JSON.parse(raw);
        if (typeof parsed.sfx_volume === 'number') {
          return Math.max(0, Math.min(1, parsed.sfx_volume / 100));
        }
      }
    } catch (_) {}
    return 0.6;
  }

  function play(type, opts = {}) {
    const vol = getVolume();
    if (vol <= 0.01) return;

    const ac = getAudioContext();
    if (!ac) return;

    const t = ac.currentTime;

    try {
      switch (type) {
        case 'click':
        case 'tap': {
          // Micro-click suave táctil tipo iPhone (10ms)
          const osc = ac.createOscillator();
          const gain = ac.createGain();
          const filter = ac.createBiquadFilter();

          osc.type = 'sine';
          const p = opts.pitch || 820;
          osc.frequency.setValueAtTime(p, t);
          osc.frequency.exponentialRampToValueAtTime(p * 0.45, t + 0.012);

          filter.type = 'bandpass';
          filter.frequency.setValueAtTime(1200, t);
          filter.Q.setValueAtTime(2.5, t);

          gain.gain.setValueAtTime(0.001, t);
          gain.gain.linearRampToValueAtTime(0.24 * vol, t + 0.002);
          gain.gain.exponentialRampToValueAtTime(0.0001, t + 0.014);

          osc.connect(filter);
          filter.connect(gain);
          gain.connect(ac.destination);

          osc.start(t);
          osc.stop(t + 0.015);
          break;
        }

        case 'pop':
        case 'open': {
          // Pop elástico de menú / expansión de isla (28ms)
          const osc = ac.createOscillator();
          const gain = ac.createGain();

          osc.type = 'sine';
          osc.frequency.setValueAtTime(280, t);
          osc.frequency.exponentialRampToValueAtTime(640, t + 0.024);

          gain.gain.setValueAtTime(0.001, t);
          gain.gain.linearRampToValueAtTime(0.26 * vol, t + 0.003);
          gain.gain.exponentialRampToValueAtTime(0.0001, t + 0.03);

          osc.connect(gain);
          gain.connect(ac.destination);

          osc.start(t);
          osc.stop(t + 0.032);
          break;
        }

        case 'toggle': {
          // Switch On/Off estilo Apple
          const on = opts.on !== false;
          const osc = ac.createOscillator();
          const gain = ac.createGain();

          osc.type = 'triangle';
          const startFreq = on ? 420 : 660;
          const endFreq = on ? 760 : 340;

          osc.frequency.setValueAtTime(startFreq, t);
          osc.frequency.exponentialRampToValueAtTime(endFreq, t + 0.02);

          gain.gain.setValueAtTime(0.001, t);
          gain.gain.linearRampToValueAtTime(0.18 * vol, t + 0.003);
          gain.gain.exponentialRampToValueAtTime(0.0001, t + 0.024);

          osc.connect(gain);
          gain.connect(ac.destination);

          osc.start(t);
          osc.stop(t + 0.026);
          break;
        }

        case 'tab': {
          // Cambio de pestaña suave
          const osc = ac.createOscillator();
          const gain = ac.createGain();

          osc.type = 'sine';
          osc.frequency.setValueAtTime(560, t);
          osc.frequency.exponentialRampToValueAtTime(400, t + 0.018);

          gain.gain.setValueAtTime(0.001, t);
          gain.gain.linearRampToValueAtTime(0.18 * vol, t + 0.002);
          gain.gain.exponentialRampToValueAtTime(0.0001, t + 0.022);

          osc.connect(gain);
          gain.connect(ac.destination);

          osc.start(t);
          osc.stop(t + 0.024);
          break;
        }

        case 'send': {
          // Enviar mensaje tipo iMessage
          const osc1 = ac.createOscillator();
          const osc2 = ac.createOscillator();
          const gain = ac.createGain();

          osc1.type = 'sine';
          osc1.frequency.setValueAtTime(340, t);
          osc1.frequency.exponentialRampToValueAtTime(980, t + 0.045);

          osc2.type = 'sine';
          osc2.frequency.setValueAtTime(500, t);
          osc2.frequency.exponentialRampToValueAtTime(1440, t + 0.045);

          gain.gain.setValueAtTime(0.001, t);
          gain.gain.linearRampToValueAtTime(0.22 * vol, t + 0.005);
          gain.gain.exponentialRampToValueAtTime(0.0001, t + 0.055);

          osc1.connect(gain);
          osc2.connect(gain);
          gain.connect(ac.destination);

          osc1.start(t);
          osc2.start(t);
          osc1.stop(t + 0.06);
          osc2.stop(t + 0.06);
          break;
        }

        case 'receive':
        case 'chime': {
          // Campana armónica doble suave al recibir respuesta de IA
          [523.25, 659.25].forEach((freq, i) => { // C5, E5
            const osc = ac.createOscillator();
            const gain = ac.createGain();

            osc.type = 'sine';
            const startTime = t + i * 0.07;
            osc.frequency.setValueAtTime(freq, startTime);

            gain.gain.setValueAtTime(0.0001, startTime);
            gain.gain.linearRampToValueAtTime(0.18 * vol, startTime + 0.008);
            gain.gain.exponentialRampToValueAtTime(0.0001, startTime + 0.17);

            osc.connect(gain);
            gain.connect(ac.destination);

            osc.start(startTime);
            osc.stop(startTime + 0.18);
          });
          break;
        }

        case 'hold': {
          // Pequeño pulso háptico durante pulsación larga
          const osc = ac.createOscillator();
          const gain = ac.createGain();

          osc.type = 'triangle';
          osc.frequency.setValueAtTime(160, t);
          osc.frequency.linearRampToValueAtTime(280, t + 0.025);

          gain.gain.setValueAtTime(0.001, t);
          gain.gain.linearRampToValueAtTime(0.14 * vol, t + 0.004);
          gain.gain.exponentialRampToValueAtTime(0.0001, t + 0.03);

          osc.connect(gain);
          gain.connect(ac.destination);

          osc.start(t);
          osc.stop(t + 0.032);
          break;
        }

        default:
          break;
      }
    } catch (_) {}
  }

  function initAutoSounds() {
    document.addEventListener('pointerdown', e => {
      const el = e.target.closest('button, [data-a], .tab, .cat, .sq, .miku-ag-pill, .wc-btn, .rb-send, .crt-item button, .gs-t, .gs-o, .sw8, .dk, .ap');
      if (!el) return;

      getAudioContext();

      if (el.classList.contains('sq') || el.closest('.sq')) {
        const inp = el.querySelector('input') || el;
        play('toggle', { on: !inp.checked });
        return;
      }
      if (el.classList.contains('cat') || el.classList.contains('tab') || el.dataset.a?.startsWith('go:')) {
        play('tab');
        return;
      }
      if (el.classList.contains('crt-pill') || el.classList.contains('gs-t')) {
        play('pop');
        return;
      }
      if (el.classList.contains('rb-send') || el.dataset.a === 'send') {
        play('send');
        return;
      }
      play('click');
    }, { capture: true, passive: true });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAutoSounds);
  } else {
    initAutoSounds();
  }

  return {
    play,
    click: (pitch) => play('click', { pitch }),
    pop: () => play('pop'),
    toggle: (on) => play('toggle', { on }),
    tab: () => play('tab'),
    send: () => play('send'),
    receive: () => play('receive'),
    chime: () => play('chime'),
    hold: () => play('hold'),
    getAudioContext
  };
})();

if (typeof window !== 'undefined') {
  window.SoundFX = SoundFX;
}
