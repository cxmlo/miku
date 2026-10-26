/* ==========================================================================
   MIKU DESKTOP — OFFICIAL WEBSITE LOGIC
   - Auto-fetches latest GitHub Release .exe and updates download links
   - Interactive Dynamic Island Simulator with 4 state animations
   - Seamless Language Switcher (ES / EN)
   ========================================================================== */

const REPO_OWNER = 'cxmlo';
const REPO_NAME = 'miku';
const DEFAULT_VERSION = 'v0.1.0-beta';
const DEFAULT_SIZE = '2.57 MB';
const FALLBACK_DOWNLOAD_URL = `https://github.com/${REPO_OWNER}/${REPO_NAME}/releases`;

// ── 1. GITHUB RELEASES AUTO-UPDATER ──
async function fetchLatestRelease() {
  const downloadBtns = document.querySelectorAll('.js-download-btn');
  const versionTags = document.querySelectorAll('.js-release-version');
  const sizeTags = document.querySelectorAll('.js-release-size');
  const dateTags = document.querySelectorAll('.js-release-date');

  try {
    const response = await fetch(`https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/releases/latest`, {
      headers: { 'Accept': 'application/vnd.github.v3+json' }
    });

    if (!response.ok) {
      throw new Error(`GitHub API returned status ${response.status}`);
    }

    const data = await response.json();
    const tag = data.tag_name || DEFAULT_VERSION;

    // Search for the Windows .exe installer asset
    let exeAsset = null;
    if (data.assets && data.assets.length > 0) {
      exeAsset = data.assets.find(asset => asset.name.toLowerCase().endsWith('.exe'));
    }

    // Format file size
    let formattedSize = DEFAULT_SIZE;
    if (exeAsset && exeAsset.size) {
      formattedSize = (exeAsset.size / (1024 * 1024)).toFixed(2) + ' MB';
    }

    // Format published date
    let formattedDate = 'Reciente';
    if (data.published_at) {
      const d = new Date(data.published_at);
      formattedDate = d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
    }

    // Update DOM
    versionTags.forEach(el => el.textContent = tag);
    sizeTags.forEach(el => el.textContent = formattedSize);
    dateTags.forEach(el => el.textContent = formattedDate);

    const downloadUrl = exeAsset ? exeAsset.browser_download_url : data.html_url || FALLBACK_DOWNLOAD_URL;
    downloadBtns.forEach(btn => {
      btn.href = downloadUrl;
      btn.setAttribute('target', '_blank');
    });

    console.log(`[Miku] Auto-detected latest release: ${tag} (${formattedSize})`);
  } catch (err) {
    console.warn('[Miku] Using fallback release info:', err.message);
    downloadBtns.forEach(btn => {
      btn.href = FALLBACK_DOWNLOAD_URL;
    });
  }
}

// ── 2. DYNAMIC ISLAND SIMULATOR ──
const islandModes = {
  spotify: {
    avatar: 'assets/app_character.jpg',
    title: 'Anuel AA — Mejor Que Yo',
    sub: 'Spotify • 320kbps • 1:42 / 3:15',
    visualizer: true,
    accentGlow: 'rgba(0, 242, 254, 0.25)',
    borderColor: 'rgba(0, 242, 254, 0.4)'
  },
  vision: {
    avatar: 'assets/app_icon.png',
    title: 'Computer Use: Escaneando pantalla',
    sub: 'Coordenadas: [925, 500] • Clic inteligente',
    visualizer: false,
    accentGlow: 'rgba(56, 239, 125, 0.3)',
    borderColor: 'rgba(56, 239, 125, 0.45)'
  },
  agent: {
    avatar: 'assets/app_character.jpg',
    title: 'Agente DevOps: Claude Code Hook',
    sub: 'Refactorizando backend en FastAPI...',
    visualizer: false,
    accentGlow: 'rgba(139, 92, 246, 0.35)',
    borderColor: 'rgba(139, 92, 246, 0.5)'
  },
  alert: {
    avatar: 'assets/app_icon.png',
    title: 'Alerta Proactiva: Descanso sugerido',
    sub: 'Llevas 3h continuas en VS Code ☕',
    visualizer: false,
    accentGlow: 'rgba(245, 158, 11, 0.3)',
    borderColor: 'rgba(245, 158, 11, 0.5)'
  }
};

function setupSimulator() {
  const island = document.getElementById('dynamicIsland');
  const avatar = document.getElementById('islandAvatar');
  const title = document.getElementById('islandTitle');
  const sub = document.getElementById('islandSub');
  const visualizer = document.getElementById('islandVisualizer');
  const buttons = document.querySelectorAll('.sim-btn');

  if (!island) return;

  buttons.forEach(btn => {
    btn.addEventListener('click', () => {
      buttons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      const modeKey = btn.getAttribute('data-mode');
      const mode = islandModes[modeKey];
      if (!mode) return;

      // Smooth transition
      island.style.transform = 'scale(0.96)';
      setTimeout(() => {
        avatar.src = mode.avatar;
        title.textContent = mode.title;
        sub.textContent = mode.sub;
        visualizer.style.display = mode.visualizer ? 'flex' : 'none';
        island.style.boxShadow = `0 16px 35px -8px rgba(0, 0, 0, 0.8), 0 0 30px ${mode.accentGlow}`;
        island.style.borderColor = mode.borderColor;
        island.style.transform = 'scale(1)';
      }, 140);
    });
  });
}

// ── 3. BILINGUAL TRANSLATION (ES / EN) ──
const i18n = {
  es: {
    heroTag: '⚡ Tu compañera de escritorio inteligente para Windows',
    heroTitle: 'La inteligencia artificial que vive en tu pantalla, <span class="hero-gradient-text">no en una pestaña</span>.',
    heroSubtitle: 'Dynamic Island para Windows, control visual de tu PC en tiempo real, soporte multi-modelo con rotación automática de claves y creación de agentes locales con MCP.',
    downloadBtnText: 'Descargar para Windows',
    downloadMeta: 'v0.1.0-beta • Windows 10/11 x64',
    viewGithub: 'Ver en GitHub',
    featTag: 'Capacidades Únicas',
    featTitle: 'Diseñada para elevar tu flujo diario',
    featDesc: 'Miku se integra orgánicamente en Windows con una isla discreta, automatización visual de tu ratón y la potencia de los mejores modelos del mundo.',
    card1Title: 'Isla Dinámica Nativa',
    card1Text: 'Ubicada discretamente en el notch superior. Se expande con suaves animaciones de resortes al reproducir Spotify, recibir alertas o ejecutar comandos.',
    card2Title: 'Multi-Modelo con Auto-Respaldo',
    card2Text: 'Gemini Flash Lite, Gemini 2.5 Pro, Claude 3.5 Sonnet, GPT-4o y Groq Whisper. Si una API se agota o satura, Miku conmuta al instante a tu clave de respaldo.',
    card3Title: 'Computer Use & Memoria Espacial',
    card3Text: 'Ve tu pantalla, analiza la interfaz y recuerda dónde hacer clic. Automatiza tareas en cualquier app de Windows sin requerir APIs complejas.',
    card4Title: 'Creador de Agentes & MCP',
    card4Text: 'Crea agentes especializados desde la interfaz o conecta herramientas de terminal (Claude Code, Cursor) usando webhooks y servidores MCP oficiales.',
    card5Title: 'Música & Spotify Integrado',
    card5Text: 'Detección automática de reproducción, carátula dinámica en la isla y control total por voz o atajos de teclado sin salir de tu ventana actual.',
    card6Title: '100% Local & Seguro',
    card6Text: 'Tus credenciales y bases de datos se almacenan exclusivamente en tu equipo. Sin intermediarios, sin telemetría intrusiva, código abierto bajo MIT.',
    modelsTag: 'Elección Óptima',
    modelsTitle: 'Matriz de Modelos Recomendados',
    modelsDesc: 'Miku te ayuda a seleccionar el modelo ideal para cada tarea, optimizando velocidad, costo y precisión.',
    agentsTag: 'Ecosistema',
    agentsTitle: 'Crea Agentes o Conecta tu Terminal',
    agentsDesc: 'Extiende Miku como desees: mediante el creador visual o usando el hook de terminal para Claude Code y Cursor.',
    dlTitle: 'Lleva a Miku a tu Escritorio hoy',
    dlDesc: 'Instalador oficial ligero (2.5 MB). Descarga directa, sin instaladores confusos ni paquetes ocultos.',
    rightsReserved: 'Todos los derechos reservados. Licencia MIT.'
  },
  en: {
    heroTag: '⚡ Your Intelligent AI Desktop Companion for Windows',
    heroTitle: 'The artificial intelligence that lives on your screen, <span class="hero-gradient-text">not in a browser tab</span>.',
    heroSubtitle: 'Dynamic Island for Windows, real-time computer use and mouse automation, multi-model AI with fallback rotation, and custom agent creation with MCP.',
    downloadBtnText: 'Download for Windows',
    downloadMeta: 'v0.1.0-beta • Windows 10/11 x64',
    viewGithub: 'View on GitHub',
    featTag: 'Unique Capabilities',
    featTitle: 'Engineered to elevate your daily workflow',
    featDesc: 'Miku blends seamlessly into Windows with a discreet island, visual screen automation, and the power of state-of-the-art AI models.',
    card1Title: 'Native Dynamic Island',
    card1Text: 'Floats subtly at the top notch of your display. Expands with fluid spring animations when playing Spotify, alerting you, or running commands.',
    card2Title: 'Multi-Model with Fallback Rotation',
    card2Text: 'Gemini Flash Lite, Gemini 2.5 Pro, Claude 3.5 Sonnet, GPT-4o, and Groq Whisper. If an API hits rate limits, Miku seamlessly rotates to your backup key.',
    card3Title: 'Computer Use & Spatial Memory',
    card3Text: 'Watches your monitor, inspects UI elements, and remembers click coordinates. Automates tasks across any Windows app without requiring custom APIs.',
    card4Title: 'Agent Builder & MCP Ecosystem',
    card4Text: 'Create purpose-built agents from the visual UI or integrate CLI workflows (Claude Code, Cursor) using lightweight local webhooks and official MCP.',
    card5Title: 'Integrated Spotify & Media',
    card5Text: 'Automatic track detection, dynamic album art in the island, and hands-free voice or keyboard shortcuts without leaving your current window.',
    card6Title: '100% Local & Privacy-First',
    card6Text: 'Your API keys and SQLite/ChromaDB databases reside solely on your drive. Zero telemetry, zero middlemen, open-source under MIT.',
    modelsTag: 'Optimal Choices',
    modelsTitle: 'Recommended Model Matrix',
    modelsDesc: 'Miku guides you to select the best model for each specific task, maximizing speed, cost efficiency, and accuracy.',
    agentsTag: 'Ecosystem',
    agentsTitle: 'Build Custom Agents or Hook CLI Tools',
    agentsDesc: 'Extend Miku effortlessly: use the visual no-code builder or link your terminal using hooks for Claude Code and Cursor.',
    dlTitle: 'Bring Miku to Your Desktop Today',
    dlDesc: 'Lightweight official installer (2.5 MB). Direct download, no bloatware, zero tracking.',
    rightsReserved: 'All rights reserved. MIT License.'
  }
};

let currentLang = 'es';

function setLanguage(lang) {
  currentLang = lang;
  localStorage.setItem('miku_lang', lang);

  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    if (i18n[lang] && i18n[lang][key]) {
      el.innerHTML = i18n[lang][key];
    }
  });

  document.querySelectorAll('.lang-btn').forEach(btn => {
    btn.classList.toggle('active', btn.getAttribute('data-lang') === lang);
  });
}

function setupLangSwitcher() {
  const savedLang = localStorage.getItem('miku_lang') || 'es';
  setLanguage(savedLang);

  document.querySelectorAll('.lang-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const lang = btn.getAttribute('data-lang');
      setLanguage(lang);
    });
  });
}

// ── INITIALIZATION ──
document.addEventListener('DOMContentLoaded', () => {
  fetchLatestRelease();
  setupSimulator();
  setupLangSwitcher();
});
