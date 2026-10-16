/* =========================================================================
   miku.js — Miku Character Canvas Renderer
   Native vanilla JS Canvas2D Engine for Miku V2 Dynamic Island
   ========================================================================= */

const miku = (() => {
  "use strict";

  // ── State definitions ────────────────────────────────────────────────
  const STATES = {
    idle:      { eyes: "normal",   mouth: "smile",    glow: "#3B9EFF", breathe: true  },
    thinking:  { eyes: "look-up",  mouth: "flat",     glow: "#A78BFA", breathe: false, wobble: true },
    working:   { eyes: "focused",  mouth: "flat",     glow: "#34D399", breathe: false, spin: true },
    talking:   { eyes: "happy",    mouth: "open",     glow: "#F472B6", breathe: true,  bounce: true },
    listening: { eyes: "normal",   mouth: "o",        glow: "#2DD4A7", breathe: true,  bounce: false, wobble: true },
    happy:     { eyes: "arc",      mouth: "big-smile", glow: "#34D399", breathe: true,  bounce: true },
    laughing:  { eyes: "arc",      mouth: "open",     glow: "#F472B6", breathe: false, shake: true },
    approval:  { eyes: "arc",      mouth: "big-smile", glow: "#34D399", breathe: true },
    surprised: { eyes: "wide",     mouth: "open",     glow: "#FBBF24", breathe: false, bounce: true },
    question:  { eyes: "wide",     mouth: "o",        glow: "#FBBF24", breathe: true },
    error:     { eyes: "x",        mouth: "zigzag",   glow: "#F44F5E", breathe: false, shake: true },
    dizzy:     { eyes: "spiral",   mouth: "wave",     glow: "#A78BFA", breathe: false, spin: true },
    sleeping:  { eyes: "closed",   mouth: "flat",     glow: "#6B7280", breathe: true,  slow: true },
    love:      { eyes: "hearts",   mouth: "big-smile", glow: "#F472B6", breathe: true },
    proud:     { eyes: "star",     mouth: "smile",    glow: "#FBBF24", breathe: true },
    searching: { eyes: "look-side", mouth: "flat",    glow: "#38BDF8", breathe: false, scan: true },
    annoyed:   { eyes: "half",     mouth: "frown",    glow: "#F97316", breathe: false, shake: true },
  };

  // ── Animation state ──────────────────────────────────────────────────
  let canvas = null;
  let ctx = null;
  let glowEl = null;
  let currentState = "idle";
  let targetState = "idle";
  let t = 0;
  let frameId = null;
  let blinkTimer = 0;
  let blinkDuration = 0;
  let isBlinking = false;
  let squish = { x: 1, y: 1 };
  let squishTarget = { x: 1, y: 1 };
  let emoteTick = 0;

  // Transition animation
  let transitionProgress = 1;
  const TRANSITION_SPEED = 0.06;

  // ── Colors ────────────────────────────────────────────────────────
  const BODY_COLOR = "#F5F6F8";
  const BODY_SHADOW = "rgba(0,0,0,.12)";
  const BODY_DARK = "#E4E6EB";
  const CHEEK_COLOR = "rgba(255,180,180,.25)";
  const EYE_COLOR = "#16171B";

  // ── Ease helpers ──────────────────────────────────────────────────
  function lerp(a, b, t) { return a + (b - a) * t; }
  function ease(t) { return t < 0.5 ? 2*t*t : -1+(4-2*t)*t; }

  // ── Init ──────────────────────────────────────────────────────────
  function init(canvasEl, glowElement) {
    canvas = canvasEl;
    ctx = canvas.getContext("2d");
    glowEl = glowElement;

    // HiDPI
    const resize = () => {
      const rect = canvas.getBoundingClientRect();
      const dpr = window.devicePixelRatio || 1;
      canvas.width = rect.width * dpr;
      canvas.height = rect.height * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };
    resize();
    new ResizeObserver(resize).observe(canvas);

    loop();
  }

  // ── State API ─────────────────────────────────────────────────────
  function setState(name) {
    if (!STATES[name]) name = "idle";
    if (name === currentState) return;
    targetState = name;
    transitionProgress = 0;
    // Squish on state change
    squishTarget = { x: 1.12, y: 0.88 };
    setTimeout(() => { squishTarget = { x: 0.95, y: 1.06 }; }, 100);
    setTimeout(() => { squishTarget = { x: 1, y: 1 }; }, 220);
    // Update glow
    if (glowEl) {
      glowEl.style.setProperty("--glow-color", STATES[name].glow);
    }
  }

  function getState() { return currentState; }

  // ── Click handler (triple-click = dizzy emote) ────────────────────
  let clickCount = 0;
  let clickTimeout = null;
  function onTap() {
    clickCount++;
    clearTimeout(clickTimeout);
    clickTimeout = setTimeout(() => { clickCount = 0; }, 600);
    if (clickCount >= 3) {
      clickCount = 0;
      triggerEmote("dizzy", 2000);
    } else {
      // Single click: squish
      squishTarget = { x: 1.2, y: 0.8 };
      setTimeout(() => { squishTarget = { x: 0.9, y: 1.1 }; }, 80);
      setTimeout(() => { squishTarget = { x: 1, y: 1 }; }, 200);
    }
  }

  // ── Emote (temporary expression) ─────────────────────────────────
  let emoteTimeout = null;
  let savedState = null;
  function triggerEmote(name, durationMs = 1500) {
    if (!STATES[name]) return;
    clearTimeout(emoteTimeout);
    if (!savedState) savedState = currentState;
    setState(name);
    emoteTimeout = setTimeout(() => {
      setState(savedState || "idle");
      savedState = null;
    }, durationMs);
  }

  // ── Main loop ─────────────────────────────────────────────────────
  function loop() {
    t += 0.016;  // ~60fps
    emoteTick += 0.016;

    // Transition
    if (transitionProgress < 1) {
      transitionProgress = Math.min(1, transitionProgress + TRANSITION_SPEED);
      if (transitionProgress >= 0.5 && currentState !== targetState) {
        currentState = targetState;
      }
    }

    // Blinking
    blinkTimer -= 0.016;
    if (blinkTimer <= 0 && !isBlinking) {
      isBlinking = true;
      blinkDuration = 0;
    }
    if (isBlinking) {
      blinkDuration += 0.016;
      if (blinkDuration > 0.15) {
        isBlinking = false;
        blinkTimer = 2 + Math.random() * 4;
      }
    }

    // Squish interpolation
    squish.x = lerp(squish.x, squishTarget.x, 0.12);
    squish.y = lerp(squish.y, squishTarget.y, 0.12);

    draw();
    frameId = requestAnimationFrame(loop);
  }

  // ── Drawing ───────────────────────────────────────────────────────
  function draw() {
    if (!ctx) return;
    const w = canvas.getBoundingClientRect().width;
    const h = canvas.getBoundingClientRect().height;
    const cx = w / 2;
    const cy = h / 2;
    const r = Math.min(w, h) * 0.38;
    const state = STATES[currentState] || STATES.idle;

    ctx.clearRect(0, 0, w, h);
    ctx.save();
    ctx.translate(cx, cy);

    // Apply state-based animations
    let offsetX = 0, offsetY = 0, rot = 0;

    if (state.breathe) {
      const speed = state.slow ? 0.4 : 1;
      offsetY = Math.sin(t * 1.6 * speed) * r * 0.04;
    }
    if (state.wobble) {
      rot = Math.sin(t * 3) * 0.06;
      offsetY = Math.sin(t * 2) * r * 0.03;
    }
    if (state.shake) {
      offsetX = Math.sin(t * 18) * r * 0.05 * Math.max(0, 1 - emoteTick * 0.5);
    }
    if (state.spin) {
      rot = Math.sin(t * 2) * 0.1;
    }
    if (state.bounce) {
      offsetY += Math.abs(Math.sin(t * 3.5)) * r * -0.06;
    }
    if (state.scan) {
      offsetX = Math.sin(t * 1.8) * r * 0.1;
    }

    ctx.translate(offsetX, offsetY);
    ctx.rotate(rot);
    ctx.scale(squish.x, squish.y);

    // ── Body ──
    drawBody(ctx, r);

    // ── Cheeks ──
    drawCheeks(ctx, r, state);

    // ── Eyes ──
    const blinkFactor = isBlinking ? Math.max(0, 1 - blinkDuration / 0.06) : 1;
    drawEyes(ctx, r, state.eyes, blinkFactor);

    // ── Mouth ──
    drawMouth(ctx, r, state.mouth);

    ctx.restore();
  }

  function drawBody(ctx, r) {
    const rx = r * 1.14;
    const ry = r * 0.88;

    // Helper to draw the squircle path
    const drawSquircle = (ctx, offsetY = 0) => {
      ctx.beginPath();
      for (let i = 0; i <= 72; i++) {
        const a = (i / 72) * Math.PI * 2;
        const ca = Math.cos(a);
        const sa = Math.sin(a);
        const px = rx * Math.sign(ca) * Math.pow(Math.abs(ca), 2 / 2.7);
        const py = ry * Math.sign(sa) * Math.pow(Math.abs(sa), 2 / 2.7) + offsetY;
        if (i === 0) {
          ctx.moveTo(px, py);
        } else {
          ctx.lineTo(px, py);
        }
      }
      ctx.closePath();
    };

    // Shadow
    drawSquircle(ctx, r * 0.12);
    ctx.fillStyle = BODY_SHADOW;
    ctx.fill();

    // Main body blob (Superellipse Squircle)
    drawSquircle(ctx, 0);
    ctx.fillStyle = BODY_COLOR;
    ctx.fill();

    // Subtle inner highlight
    const grad = ctx.createRadialGradient(-r * 0.2, -r * 0.3, 0, 0, 0, r);
    grad.addColorStop(0, "rgba(255,255,255,.35)");
    grad.addColorStop(1, "rgba(255,255,255,0)");
    
    drawSquircle(ctx, 0);
    ctx.fillStyle = grad;
    ctx.fill();
  }

  function drawCheeks(ctx, r, state) {
    if (state.eyes === "x" || state.eyes === "spiral") return;
    const alpha = (state.mouth === "big-smile" || state.eyes === "hearts") ? 0.35 : 0.2;
    ctx.globalAlpha = alpha;
    // Left cheek
    ctx.beginPath();
    ctx.ellipse(-r * 0.52, r * 0.12, r * 0.15, r * 0.1, 0, 0, Math.PI * 2);
    ctx.fillStyle = CHEEK_COLOR;
    ctx.fill();
    // Right cheek
    ctx.beginPath();
    ctx.ellipse(r * 0.52, r * 0.12, r * 0.15, r * 0.1, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.globalAlpha = 1;
  }

  function drawEyes(ctx, r, type, blinkFactor) {
    const eyeSpacing = r * 0.28;
    const eyeY = -r * 0.1;
    const eyeR = r * 0.09;

    ctx.fillStyle = EYE_COLOR;
    ctx.strokeStyle = EYE_COLOR;
    ctx.lineWidth = r * 0.04;
    ctx.lineCap = "round";
    ctx.lineJoin = "round";

    switch(type) {
      case "normal":
        drawNormalEye(ctx, -eyeSpacing, eyeY, eyeR, blinkFactor);
        drawNormalEye(ctx, eyeSpacing, eyeY, eyeR, blinkFactor);
        break;

      case "happy":
      case "arc":
        drawArcEye(ctx, -eyeSpacing, eyeY, eyeR);
        drawArcEye(ctx, eyeSpacing, eyeY, eyeR);
        break;

      case "wide":
        drawNormalEye(ctx, -eyeSpacing, eyeY, eyeR * 1.3, blinkFactor);
        drawNormalEye(ctx, eyeSpacing, eyeY, eyeR * 1.3, blinkFactor);
        break;

      case "closed":
        drawClosedEye(ctx, -eyeSpacing, eyeY, eyeR);
        drawClosedEye(ctx, eyeSpacing, eyeY, eyeR);
        break;

      case "look-up":
        drawNormalEye(ctx, -eyeSpacing, eyeY - eyeR * 0.3, eyeR, blinkFactor);
        drawNormalEye(ctx, eyeSpacing, eyeY - eyeR * 0.3, eyeR, blinkFactor);
        break;

      case "look-side":
        drawOffsetEye(ctx, -eyeSpacing, eyeY, eyeR, Math.sin(t * 1.8) * eyeR * 0.4, blinkFactor);
        drawOffsetEye(ctx, eyeSpacing, eyeY, eyeR, Math.sin(t * 1.8) * eyeR * 0.4, blinkFactor);
        break;

      case "focused":
        drawNormalEye(ctx, -eyeSpacing, eyeY, eyeR * 0.8, blinkFactor);
        drawNormalEye(ctx, eyeSpacing, eyeY, eyeR * 0.8, blinkFactor);
        break;

      case "half":
        drawHalfEye(ctx, -eyeSpacing, eyeY, eyeR);
        drawHalfEye(ctx, eyeSpacing, eyeY, eyeR);
        break;

      case "x":
        drawXEye(ctx, -eyeSpacing, eyeY, eyeR);
        drawXEye(ctx, eyeSpacing, eyeY, eyeR);
        break;

      case "spiral":
        drawSpiralEye(ctx, -eyeSpacing, eyeY, eyeR);
        drawSpiralEye(ctx, eyeSpacing, eyeY, eyeR);
        break;

      case "hearts":
        drawHeartEye(ctx, -eyeSpacing, eyeY, eyeR);
        drawHeartEye(ctx, eyeSpacing, eyeY, eyeR);
        break;

      case "star":
        drawStarEye(ctx, -eyeSpacing, eyeY, eyeR);
        drawStarEye(ctx, eyeSpacing, eyeY, eyeR);
        break;
    }
  }

  // ── Eye primitives ────────────────────────────────────────────────
  function drawNormalEye(ctx, x, y, r, blinkFactor) {
    ctx.beginPath();
    if (blinkFactor < 0.3) {
      // Blink: draw line
      ctx.moveTo(x - r, y);
      ctx.lineTo(x + r, y);
      ctx.stroke();
    } else {
      ctx.ellipse(x, y, r, r * blinkFactor, 0, 0, Math.PI * 2);
      ctx.fill();
      // Eye shine
      ctx.fillStyle = "#fff";
      ctx.beginPath();
      ctx.ellipse(x + r * 0.3, y - r * 0.3, r * 0.25, r * 0.25 * blinkFactor, 0, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = EYE_COLOR;
    }
  }

  function drawOffsetEye(ctx, x, y, r, offsetX, blinkFactor) {
    ctx.beginPath();
    if (blinkFactor < 0.3) {
      ctx.moveTo(x - r, y);
      ctx.lineTo(x + r, y);
      ctx.stroke();
    } else {
      ctx.ellipse(x + offsetX, y, r, r * blinkFactor, 0, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = "#fff";
      ctx.beginPath();
      ctx.ellipse(x + offsetX + r * 0.3, y - r * 0.3, r * 0.25, r * 0.25, 0, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = EYE_COLOR;
    }
  }

  function drawArcEye(ctx, x, y, r) {
    ctx.beginPath();
    ctx.arc(x, y + r * 0.3, r, Math.PI * 1.15, Math.PI * 1.85);
    ctx.stroke();
  }

  function drawClosedEye(ctx, x, y, r) {
    ctx.beginPath();
    ctx.moveTo(x - r, y);
    ctx.lineTo(x + r, y);
    ctx.stroke();
  }

  function drawHalfEye(ctx, x, y, r) {
    ctx.save();
    ctx.beginPath();
    ctx.rect(x - r * 1.2, y - r * 0.2, r * 2.4, r * 1.5);
    ctx.clip();
    ctx.beginPath();
    ctx.ellipse(x, y, r, r, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
  }

  function drawXEye(ctx, x, y, r) {
    const s = r * 0.7;
    ctx.beginPath();
    ctx.moveTo(x - s, y - s);
    ctx.lineTo(x + s, y + s);
    ctx.moveTo(x + s, y - s);
    ctx.lineTo(x - s, y + s);
    ctx.stroke();
  }

  function drawSpiralEye(ctx, x, y, r) {
    const angle = t * 4;
    ctx.beginPath();
    for (let i = 0; i < 20; i++) {
      const a = angle + i * 0.5;
      const sr = (i / 20) * r * 1.2;
      const px = x + Math.cos(a) * sr;
      const py = y + Math.sin(a) * sr;
      if (i === 0) ctx.moveTo(px, py);
      else ctx.lineTo(px, py);
    }
    ctx.stroke();
  }

  function drawHeartEye(ctx, x, y, r) {
    ctx.save();
    ctx.fillStyle = "#F472B6";
    ctx.translate(x, y);
    const s = r * 0.09;
    ctx.scale(s, s);
    ctx.beginPath();
    ctx.moveTo(0, 3);
    ctx.bezierCurveTo(0, -2, -10, -6, -10, -2);
    ctx.bezierCurveTo(-10, 2, 0, 8, 0, 12);
    ctx.bezierCurveTo(0, 8, 10, 2, 10, -2);
    ctx.bezierCurveTo(10, -6, 0, -2, 0, 3);
    ctx.fill();
    ctx.restore();
  }

  function drawStarEye(ctx, x, y, r) {
    ctx.save();
    ctx.fillStyle = "#FBBF24";
    ctx.translate(x, y);
    ctx.beginPath();
    for (let i = 0; i < 5; i++) {
      const outerAngle = (i * 2 * Math.PI / 5) - Math.PI / 2;
      const innerAngle = outerAngle + Math.PI / 5;
      ctx.lineTo(Math.cos(outerAngle) * r, Math.sin(outerAngle) * r);
      ctx.lineTo(Math.cos(innerAngle) * r * 0.45, Math.sin(innerAngle) * r * 0.45);
    }
    ctx.closePath();
    ctx.fill();
    ctx.restore();
  }

  // ── Mouth ─────────────────────────────────────────────────────────
  function drawMouth(ctx, r, type) {
    const y = r * 0.25;
    ctx.strokeStyle = EYE_COLOR;
    ctx.fillStyle = EYE_COLOR;
    ctx.lineWidth = r * 0.035;
    ctx.lineCap = "round";

    switch(type) {
      case "smile":
        ctx.beginPath();
        ctx.arc(0, y - r * 0.06, r * 0.14, 0.15, Math.PI - 0.15);
        ctx.stroke();
        break;

      case "big-smile":
        ctx.beginPath();
        ctx.arc(0, y - r * 0.06, r * 0.18, 0.1, Math.PI - 0.1);
        ctx.stroke();
        break;

      case "flat":
        ctx.beginPath();
        ctx.moveTo(-r * 0.1, y);
        ctx.lineTo(r * 0.1, y);
        ctx.stroke();
        break;

      case "open":
        ctx.beginPath();
        ctx.ellipse(0, y, r * 0.1, r * 0.08 + Math.sin(t * 6) * r * 0.02, 0, 0, Math.PI * 2);
        ctx.fill();
        break;

      case "o":
        ctx.beginPath();
        ctx.ellipse(0, y, r * 0.08, r * 0.1, 0, 0, Math.PI * 2);
        ctx.stroke();
        break;

      case "zigzag":
        ctx.beginPath();
        const zw = r * 0.2;
        ctx.moveTo(-zw, y);
        ctx.lineTo(-zw * 0.5, y - r * 0.05);
        ctx.lineTo(0, y);
        ctx.lineTo(zw * 0.5, y - r * 0.05);
        ctx.lineTo(zw, y);
        ctx.stroke();
        break;

      case "wave":
        ctx.beginPath();
        ctx.moveTo(-r * 0.15, y);
        ctx.bezierCurveTo(-r * 0.08, y - r * 0.06, r * 0.08, y + r * 0.06, r * 0.15, y);
        ctx.stroke();
        break;

      case "frown":
        ctx.beginPath();
        ctx.arc(0, y + r * 0.12, r * 0.12, Math.PI + 0.3, -0.3);
        ctx.stroke();
        break;
    }
  }

  // ── Destroy ───────────────────────────────────────────────────────
  function destroy() {
    if (frameId) cancelAnimationFrame(frameId);
    frameId = null;
    canvas = null;
    ctx = null;
  }

  // ── Public API ────────────────────────────────────────────────────
  return {
    init,
    setState,
    getState,
    triggerEmote,
    onTap,
    destroy,
    STATES,
  };
})();
