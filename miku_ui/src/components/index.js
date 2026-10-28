/**
 * Miku Design System — Unified Component Library Barrel (Fases 3 & 5)
 * Exports every reusable component from miku-catalogo.html and attaches window.MikuComponents,
 * window.MikuLinkTransport, and window.MikuLinkSection.
 */

import * as Primitives from './primitives.js';
import * as Feedback from './feedback.js';
import * as Overlays from './overlays.js';
import * as Interactive from './interactive.js';
import * as ParticlesHeader from './particlesHeader.js';
import * as QrPhone from './qrPhone.js';
import { mikuLinkTransport, LinkTransport } from '../services/mikuLinkService.js';
import * as MikuLinkSection from '../sections/mikuLinkSection.js';

export const MikuComponents = Object.freeze({
  ...Primitives,
  ...Feedback,
  ...Overlays,
  ...Interactive,
  ...ParticlesHeader,
  ...QrPhone,
  LinkTransport,
  mikuLinkTransport,
  MikuLinkSection
});

if (typeof window !== 'undefined') {
  window.MikuComponents = MikuComponents;
  window.MikuLinkTransport = mikuLinkTransport;
  window.MikuLinkSection = MikuLinkSection;
  window.mikuToast = Feedback.toast;
  window.mikuHold = Primitives.mountHoldButton;
}

export default MikuComponents;
