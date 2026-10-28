/**
 * Miku Design System — TypeScript Tokens Module
 * Mirrors styles/tokens.css and design/tokens.js.
 */

export interface SectionHue {
  readonly h: number;
  readonly s: number;
  readonly l: number;
}

export const TOKENS = {
  colors: {
    s0: '#000',
    s1: '#0e0f11',
    s2: '#17181b',
    s3: '#1d1d20',
    ln: 'rgba(255,255,255,.08)',
    ln2: 'rgba(255,255,255,.14)',
    tx: '#f5f5f7',
    mu: 'rgba(235,235,245,.45)',
    ink: '#0b0b0c',
    ok: '#30d158',
    okbg: 'rgba(48,209,88,.12)',
    er: '#ff453a',
    erbg: 'rgba(255,69,58,.10)'
  },
  motion: {
    spring: 'linear(0,.17 3%,.52 7%,.86 12%,1.04 17%,1.1 22%,1.07 28%,1.01 36%,.99 46%,1)',
    ease: 'cubic-bezier(.2,.8,.2,1)',
    load: 'cubic-bezier(.45,.05,.55,.95)',
    pressMs: 150,
    exitMs: 200,
    optMs: 250,
    medMs: 300,
    slowMs: 350,
    springSmMs: 400,
    springMdMs: 450,
    springMs: 500,
    enterMs: 600,
    holdMs: 900,
    loadMs: 1600,
    toastMs: 3000,
    indicatorLagMs: 40
  },
  radii: {
    sm: 8,
    nav: 9,
    btn: 11,
    btnLg: 12,
    chip: 13,
    acc: 14,
    lift: 16,
    card: 18,
    win: 20,
    toast: 20,
    qr: 24,
    phone: 36
  },
  heights: {
    btnSm: 30,
    btn: 36,
    holdBtn: 40,
    search: 40,
    field: 44
  },
  zIndex: {
    tooltip: 5,
    menu: 20,
    modal: 50,
    toast: 60,
    contextMenu: 70
  }
} as const;

export const SECTION_HUES: Record<string, SectionHue> = {
  general:  { h: 212, s: 75, l: 72 },
  island:   { h: 212, s: 75, l: 72 },
  modelos:  { h: 268, s: 75, l: 72 },
  agentes:  { h: 34,  s: 92, l: 62 },
  link:     { h: 150, s: 72, l: 56 },
  permisos: { h: 190, s: 80, l: 62 },
  keys:     { h: 245, s: 72, l: 70 },
  mcp:      { h: 198, s: 78, l: 66 },
  alertas:  { h: 28,  s: 88, l: 62 },
  voz:      { h: 292, s: 74, l: 70 },
  peligro:  { h: 4,   s: 86, l: 62 }
} as const;

export function getSectionHue(sectionId: string): SectionHue {
  const entry = SECTION_HUES[sectionId] || SECTION_HUES.general;
  return { h: entry.h, s: entry.s, l: entry.l };
}

