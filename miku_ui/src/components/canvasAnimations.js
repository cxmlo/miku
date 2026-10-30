/**
 * Modular Procedural Canvas 2D Animations & Expressions for Miku Dynamic Island
 * Allows adding or customizing expressions, bounces, and eye shapes in a clean, isolated format
 * without modifying the core renderer loop.
 */

export const CANVAS_ANIMATION_PRESETS = {
  idle: {
    id: 'idle',
    label: 'Reposo suave',
    bounceFreq: 1.8,
    bounceAmp: 2.2,
    blinkIntervalMs: 3600,
    eyeShape: 'oval',
    mouthCurve: 0.15,
    auraOpacity: 0.25
  },
  thinking: {
    id: 'thinking',
    label: 'Pensando / Razonando',
    bounceFreq: 2.6,
    bounceAmp: 3.0,
    blinkIntervalMs: 2400,
    eyeShape: 'focused',
    mouthCurve: 0.0,
    auraOpacity: 0.55,
    bubbleDots: true
  },
  working: {
    id: 'working',
    label: 'Ejecutando código o tarea',
    bounceFreq: 3.8,
    bounceAmp: 3.5,
    blinkIntervalMs: 4200,
    eyeShape: 'determined',
    mouthCurve: 0.1,
    auraOpacity: 0.75
  },
  happy: {
    id: 'happy',
    label: 'Celebración / Tarea completada',
    bounceFreq: 4.5,
    bounceAmp: 5.0,
    blinkIntervalMs: 5000,
    eyeShape: 'arc',
    mouthCurve: 0.45,
    auraOpacity: 0.85
  },
  point_upd: {
    id: 'point_upd',
    label: 'Aviso de actualización del sistema',
    bounceFreq: 2.4,
    bounceAmp: 2.8,
    blinkIntervalMs: 3200,
    eyeShape: 'wink',
    mouthCurve: 0.35,
    auraOpacity: 0.9
  },
  error: {
    id: 'error',
    label: 'Alerta / Error de ejecución',
    bounceFreq: 5.2,
    bounceAmp: 2.0,
    blinkIntervalMs: 1800,
    eyeShape: 'wide',
    mouthCurve: -0.25,
    auraOpacity: 0.9
  }
};

export function registerCustomAnimation(id, config) {
  if (!id || typeof config !== 'object') return false;
  CANVAS_ANIMATION_PRESETS[id] = {
    ...CANVAS_ANIMATION_PRESETS.idle,
    ...config,
    id
  };
  return true;
}

export function getAnimationPreset(stateId) {
  return CANVAS_ANIMATION_PRESETS[stateId] || CANVAS_ANIMATION_PRESETS.idle;
}

if (typeof window !== 'undefined') {
  window.MikuCanvasAnimations = {
    PRESETS: CANVAS_ANIMATION_PRESETS,
    registerCustomAnimation,
    getAnimationPreset
  };
}
