/**
 * Miku Design System — Stroke SVG Icons System (§2)
 * All icons are pure stroke SVGs (stroke: currentColor; stroke-width: 2; round caps/joins).
 * Zero emojis allowed.
 */

export const ICONS = Object.freeze({
  // Catálogo oficial (miku-catalogo.html)
  general: '<circle cx="12" cy="12" r="3"/><path d="M12 3v3M12 18v3M3 12h3M18 12h3M5.6 5.6l2.1 2.1M16.3 16.3l2.1 2.1M5.6 18.4l2.1-2.1M16.3 7.7l2.1-2.1"/>',
  gear: '<circle cx="12" cy="12" r="3"/><path d="M12 3v3M12 18v3M3 12h3M18 12h3M5.6 5.6l2.1 2.1M16.3 16.3l2.1 2.1M5.6 18.4l2.1-2.1M16.3 7.7l2.1-2.1"/>',
  modelos: '<path d="M12 3l8 4.5v9L12 21l-8-4.5v-9z"/><path d="M12 12l8-4.5M12 12v9M12 12L4 7.5"/>',
  cube: '<path d="M12 3l8 4.5v9L12 21l-8-4.5v-9z"/><path d="M12 12l8-4.5M12 12v9M12 12L4 7.5"/>',
  agentes: '<circle cx="9" cy="8" r="3"/><circle cx="17" cy="9" r="2.2"/><path d="M3 19c0-3.3 2.7-5 6-5s6 1.7 6 5M15.5 14.2c3 0 5.5 1.3 5.5 4.3"/>',
  bot: '<rect x="4" y="7.5" width="16" height="12" rx="4.2"/><path d="M12 3.5v4M9 13.3h.01M15 13.3h.01"/>',
  link: '<rect x="7" y="2.5" width="10" height="19" rx="2.5"/><path d="M11 18.5h2"/>',
  phone: '<rect x="7" y="2.5" width="10" height="19" rx="2.5"/><path d="M11 18.5h2"/>',
  call: '<path d="M5 4h4l2 5-2.5 1.5a11 11 0 005 5L15 13l5 2v4a2 2 0 01-2 2A16 16 0 013 6a2 2 0 012-2z"/>',
  permisos: '<path d="M12 3l7 3v5c0 4.5-3 8-7 10-4-2-7-5.5-7-10V6z"/>',
  shield: '<path d="M12 3l7 3v5c0 4.5-3 8-7 10-4-2-7-5.5-7-10V6z"/><path d="M8.8 12l2.2 2.2 4.2-4.4"/>',
  peligro: '<path d="M12 4l9 16H3z"/><path d="M12 10v4M12 17h.01"/>',
  island: '<rect x="6" y="2.5" width="12" height="19" rx="3.8"/><path d="M10 6h4"/>',
  keys: '<circle cx="7.5" cy="12" r="4"/><path d="M11.5 12H21M18 12v3M15 12v2.2"/>',
  mcp: '<rect x="3.5" y="4" width="17" height="6.5" rx="2.5"/><rect x="3.5" y="13.5" width="17" height="6.5" rx="2.5"/><path d="M7.5 7.25h.01M7.5 16.75h.01M12 7.25h5M12 16.75h5"/>',
  alertas: '<path d="M6 17v-6a6 6 0 0112 0v6l1.8 2H4.2z"/><path d="M10 21a2.2 2.2 0 004 0"/>',
  voz: '<rect x="9" y="3" width="6" height="11.5" rx="3"/><path d="M5.8 11a6.2 6.2 0 0012.4 0M12 17.2V21M8.8 21h6.4"/>',
  sparkles: '<path d="M11 4.5c.7 4.2 2.8 6.3 7 7-4.2.7-6.3 2.8-7 7-.7-4.2-2.8-6.3-7-7 4.2-.7 6.3-2.8 7-7z"/><path d="M19 15.5c.3 1.5 1 2.2 2.5 2.5-1.5.3-2.2 1-2.5 2.5-.3-1.5-1-2.2-2.5-2.5 1.5-.3 2.2-1 2.5-2.5z"/>',

  // Controles y utilidades del catálogo
  x: '<path d="M6 6l12 12M18 6L6 18"/>',
  close: '<path d="M6 6l12 12M18 6L6 18"/>',
  ck: '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
  check: '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
  chevDown: '<path d="M6 9l6 6 6-6"/>',
  back: '<path d="M15 6l-6 6 6 6"/>',
  home: '<path d="M4 11l8-7 8 7v9H4z"/>',
  send: '<path d="M4 12l16-8-6 16-3-7z"/>',
  img: '<rect x="3" y="4" width="18" height="16" rx="3"/><circle cx="9" cy="10" r="1.6"/><path d="M4 18l5-5 4 4 3-3 4 4"/>',
  grip: '<circle cx="9" cy="7" r="1"/><circle cx="15" cy="7" r="1"/><circle cx="9" cy="12" r="1"/><circle cx="15" cy="12" r="1"/><circle cx="9" cy="17" r="1"/><circle cx="15" cy="17" r="1"/>',
  search: '<circle cx="11" cy="11" r="6.5"/><path d="M16 16l4 4"/>',
  info: '<circle cx="12" cy="12" r="9"/><path d="M12 8h.01M12 11v5"/>',
  error: '<circle cx="12" cy="12" r="9"/><path d="M12 8v4.5M12 16h.01"/>',
  empty: '<circle cx="12" cy="12" r="9"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  trash: '<path d="M6.2 7l.9 12.4a1.6 1.6 0 001.6 1.5h6.6a1.6 1.6 0 001.6-1.5L17.8 7M4 7h16M9.5 7V4.5h5V7M10 11v6M14 11v6"/>',
  refresh: '<path d="M20 12a8 8 0 11-2.4-5.7M20 4.5v4.8h-4.8"/>',
  download: '<path d="M12 4v11M7.5 10.5l4.5 4.5 4.5-4.5M5 20h14"/>',
  folder: '<path d="M3 7.5A2.5 2.5 0 015.5 5h3.8l2 2.5h7.2A2.5 2.5 0 0121 10v7a2.5 2.5 0 01-2.5 2.5h-13A2.5 2.5 0 013 17z"/>',
  lock: '<rect x="5" y="10.5" width="14" height="10.5" rx="3.2"/><path d="M8 10.5V8a4 4 0 018 0v2.5M12 15.7h.01"/>',
  clipboard: '<rect x="8" y="3" width="8" height="4" rx="1.8"/><path d="M16 5h1.5A2.5 2.5 0 0120 7.5v11a2.5 2.5 0 01-2.5 2.5h-11A2.5 2.5 0 014 18.5v-11A2.5 2.5 0 016.5 5H8"/>',
  eye: '<path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7-10-7-10-7z"/><circle cx="12" cy="12" r="3"/>',
  eyeOff: '<path d="M17.9 17.9A10.1 10.1 0 0112 19c-6.4 0-10-7-10-7a18.5 18.5 0 015.1-5.9M9.9 4.2A9.1 9.1 0 0112 4c6.4 0 10 7 10 7a18.5 18.5 0 01-2.2 3.2M1 1l22 22"/>',
  wifi: '<path d="M2.45 9.95a13.5 13.5 0 0119.1 0M5.64 13.14a9 9 0 0112.72 0M8.82 16.32a4.5 4.5 0 016.36 0M12 19.5h.01"/>'
});

/**
 * Renderiza un icono SVG de trazo limpio.
 */
export function icon(name, { className = 'ic', style = '', ariaHidden = true } = {}) {
  const paths = ICONS[name] || ICONS.info;
  const cls = className ? ` class="${className}"` : ' class="ic"';
  const st = style ? ` style="${style}"` : '';
  const ah = ariaHidden ? ' aria-hidden="true"' : '';
  return `<svg${cls}${st} viewBox="0 0 24 24"${ah}>${paths}</svg>`;
}

/**
 * Renderiza el cargador de arco continuo (§4 y §5 de miku-design-system).
 */
export function arcLoader({ size = 26 } = {}) {
  const st = size !== 26 ? ` style="width:${size}px;height:${size}px"` : '';
  return `<svg class="ld"${st} viewBox="0 0 26 26" aria-hidden="true"><circle cx="13" cy="13" r="10"/></svg>`;
}

/**
 * Renderiza el cargador de puntos en ola (§5 de miku-design-system).
 */
export function waveLoader() {
  return '<div class="wv" aria-hidden="true"><i></i><i></i><i></i></div>';
}

if (typeof window !== 'undefined') {
  window.MikuIcons = { ICONS, icon, arcLoader, waveLoader };
}

