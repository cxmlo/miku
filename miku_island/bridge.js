/* =========================================================================
   bridge.js — Universal Bridge for Miku Dynamic Island & Settings
   Connects miku_v6.html and miku_settings_v6.html with the Python backend
   (server.py) over WebSocket and REST APIs.
   ========================================================================= */

const Bridge = (() => {
  "use strict";

  const HOST = location.hostname && location.hostname !== "localhost" ? location.hostname : "127.0.0.1";
  const BACKEND_PORT = "8000";
  const PORT = BACKEND_PORT;
  const BASE_URL = `http://${HOST}:${BACKEND_PORT}`;
  const WS_URL = `ws://${HOST}:${BACKEND_PORT}/ws`;
  const API_KEY = "miku_secure_key_2026";

  let ws = null;
  let reconnectTimer = null;
  let reconnectAttempts = 0;
  const MAX_RECONNECT_DELAY = 8000;

  // BroadcastChannel for cross-window sync (Island <-> Settings)
  const channel = typeof BroadcastChannel !== "undefined" ? new BroadcastChannel("miku") : null;

  function init() {
    connectWS();
    initLocalIp();
    initMouseTracker();
    fetchMediaStatus();
  }

  function fetchMediaStatus() {
    fetch(`${BASE_URL}/api/media/status`)
      .then(r => r.json())
      .then(data => {
        if (data) {
          window.feed?.({ type: "music", ...data });
        }
      })
      .catch(() => {});
  }

  /* ---------------- WEBSOCKET ---------------- */
  function connectWS() {
    if (ws && ws.readyState <= 1) return;
    try {
      ws = new WebSocket(`${WS_URL}?token=${API_KEY}`);
    } catch (e) {
      console.warn("[Bridge] WebSocket init error:", e);
      scheduleReconnect();
      return;
    }

    ws.onopen = () => {
      console.log("[Bridge] ✅ WebSocket connected to Miku Core");
      reconnectAttempts = 0;
      window.feed?.({ type: "ws", ok: true });
      window.feed?.({ type: "api", ok: true });

      // Emote happy when connected
      if (window.buddy?.emote) {
        window.buddy.emote("happy", 1200);
      }
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        handleIncomingMessage(data);
      } catch (e) {
        console.warn("[Bridge] Failed to parse WS message:", e);
      }
    };

    ws.onclose = () => {
      console.log("[Bridge] WebSocket disconnected");
      window.feed?.({ type: "ws", ok: false });
      scheduleReconnect();
    };

    ws.onerror = (err) => {
      console.warn("[Bridge] WebSocket error:", err);
      try { ws.close(); } catch (_) {}
    };
  }

  function scheduleReconnect() {
    if (reconnectTimer) return;
    reconnectAttempts++;
    const delay = Math.min(1000 * Math.pow(1.5, reconnectAttempts), MAX_RECONNECT_DELAY);
    reconnectTimer = setTimeout(() => {
      reconnectTimer = null;
      connectWS();
    }, delay);
  }

  /* ---------------- INCOMING MESSAGE ROUTER ---------------- */
  function handleIncomingMessage(data) {
    if (!data) return;

    // 1. Miku Chat Response
    if (data.sender === "miku") {
      const text = data.text || "";
      if (text.includes("[IGNORAR]") || !text.trim()) return;

      window.feed?.({ type: "state", name: "happy" });
      window.feed?.({ type: "scene", name: "result", args: { text: text } });
      return;
    }

    // 2. UI Commands from backend
    if (data.type === "ui_command") {
      const action = data.action;
      const text = data.text || "";
      const args = data.args || [];

      switch (action) {
        case "status_update":
          handleStatusUpdate(text);
          break;

        case "tool_use": {
          const label = args[0] || text || "Ejecutando herramienta";
          window.feed?.({ type: "scene", name: "tool_use", args: { label, badge: "Tool" } });
          window.feed?.({ type: "state", name: "working" });
          break;
        }

        case "show_info":
          window.feed?.({
            type: "notify",
            title: args[0] || "Información",
            text: args[1] || text || ""
          });
          break;

        case "island_notify":
          window.feed?.({
            type: "notify",
            title: args.title || text || "Miku",
            text: args.text || ""
          });
          break;

        case "show_quicklook":
          window.feed?.({
            type: "scene",
            name: "quicklook",
            args: {
              title: args[0] || "Archivo",
              text: args[1] || args[0] || "Vista previa"
            }
          });
          break;

        case "miku_link_connected":
          window.feed?.({ type: "miku_link_connected", name: text || "Celular" });
          break;

        case "miku_link_disconnected":
          window.feed?.({ type: "miku_link_disconnected" });
          break;

        case "music":
          window.feed?.({ type: "music", ...args });
          break;

        case "play_audio":
          // If audio is played locally or received, animate talking
          window.feed?.({ type: "state", name: "talking" });
          break;
      }
      return;
    }

    // 3. Agent Hook events (Coucou style: Claude Code, Cursor, Codex, Antigravity)
    if (data.type === "agent_hook") {
      const agent = data.agent || "claude";
      const ev = data.event || "Notification";
      const prompt = data.prompt || "";
      const tool = data.tool || "";
      const payload = data.payload || {};
      console.log(`[Bridge] Agent Hook: ${agent} -> ${ev}`);

      if (ev === "PermissionRequest") {
        window.feed?.({
          type: "approve",
          title: `¿Permitir acción de ${agent}?`,
          text: tool || prompt || "Permiso solicitado",
          id: payload.request_id || "req_1"
        });
      } else if (ev === "UserPromptSubmit") {
        window.feed?.({ type: "state", name: "thinking" });
        window.feed?.({ type: "prompt_active", agent, prompt });
      } else if (ev === "PreToolUse") {
        window.feed?.({ type: "state", name: "working" });
        window.feed?.({ type: "scene", name: "tool_use", args: { label: tool || "Ejecutando herramienta", badge: agent } });
      } else if (ev === "Stop") {
        window.feed?.({ type: "state", name: "happy" });
        setTimeout(() => window.feed?.({ type: "state", name: "idle" }), 4000);
      } else if (ev === "StopFailure") {
        window.feed?.({ type: "state", name: "error" });
        setTimeout(() => window.feed?.({ type: "state", name: "idle" }), 4000);
      }
      return;
    }
  }

  function handleStatusUpdate(rawText) {
    const text = (rawText || "").toLowerCase().trim();
    if (!text || text === "idle" || text === "lista") {
      window.feed?.({ type: "state", name: "idle" });
      window.feed?.({ type: "mic", on: false });
      return;
    }

    if (text.includes("pensando") || text.includes("thinking")) {
      window.feed?.({ type: "state", name: "thinking" });
    } else if (text.includes("escuchando") || text.includes("listening")) {
      window.feed?.({ type: "state", name: "listening" });
      window.feed?.({ type: "mic", on: true });
    } else if (text.includes("hablando") || text.includes("talking")) {
      window.feed?.({ type: "state", name: "talking" });
    } else if (text.includes("buscando") || text.includes("searching")) {
      window.feed?.({ type: "state", name: "searching" });
    } else if (text.includes("pantalla") || text.includes("clic") || text.includes("escribiendo")) {
      window.feed?.({ type: "state", name: "working" });
      window.feed?.({ type: "scene", name: "tool_use", args: { label: rawText, badge: "Computer Use" } });
    } else if (text.includes("error")) {
      window.feed?.({ type: "state", name: "error" });
    } else {
      window.feed?.({ type: "state", name: "working" });
    }
  }

  /* ---------------- MIKU-LINK PAIRING QR ---------------- */
  async function generatePairingUrl() {
    try {
      const res = await fetch(`${BASE_URL}/api/desktop/info`);
      let ip = HOST;
      if (res.ok) {
        const info = await res.json();
        if (info.ip && info.ip !== "127.0.0.1") {
          ip = info.ip;
        }
      }

      // Generar sesión aleatoria de 8 caracteres
      const sessionId = Math.random().toString(36).substring(2, 10);

      // Registrar sesión en backend
      await fetch(`${BASE_URL}/api/pair/init`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId })
      });

      // Formato esperado por miku_app (devices.tsx): miku://pair?s={session}&ip={ip}
      const pairUrl = `miku://pair?s=${sessionId}&ip=${ip}`;
      console.log("[Bridge] Generated valid Miku-Link QR URL:", pairUrl);
      window.setPairUrl?.(pairUrl);
      return pairUrl;
    } catch (e) {
      console.warn("[Bridge] Error generating pair URL:", e);
      const fallbackUrl = `miku://pair?s=offline&ip=${HOST}`;
      window.setPairUrl?.(fallbackUrl);
      return fallbackUrl;
    }
  }

  function initLocalIp() {
    generatePairingUrl();
  }

  /* ---------------- GLOBAL CURSOR TRACKER (Optional) ---------------- */
  function initMouseTracker() {
    let lastX = 0, lastY = 0;
    setInterval(async () => {
      // 1. In Tauri: use instant native Windows API GetCursorPos
      if (window.__TAURI__?.core?.invoke) {
        try {
          const [gx, gy] = await window.__TAURI__.core.invoke('get_cursor_position');
          if (gx !== lastX || gy !== lastY) {
            lastX = gx;
            lastY = gy;
            window.feed?.(gx, gy);
          }
        } catch (_) {}
        return;
      }

      // 2. In pywebview / browser: fallback to backend /mouse
      if (!document.hasFocus() && window.feed) {
        try {
          const res = await fetch(`${BASE_URL}/mouse`);
          if (res.ok) {
            const pt = await res.json();
            if (pt.x !== lastX || pt.y !== lastY) {
              lastX = pt.x;
              lastY = pt.y;
              window.feed(pt.x, pt.y);
            }
          }
        } catch (_) {}
      }
    }, 40);
  }

  /* ---------------- OUTGOING BRIDGE METHODS ---------------- */

  // 1. Send chat prompt
  function sendChat(text) {
    if (!text || !text.trim()) return;
    window.feed?.({ type: "state", name: "thinking" });

    fetch(`${BASE_URL}/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-api-key": API_KEY
      },
      body: JSON.stringify({ message: text, source: "desktop" })
    })
      .then(async (res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        if (data && data.reply && !data.reply.includes("[IGNORAR]")) {
          window.feed?.({ type: "state", name: "happy" });
          window.feed?.({ type: "scene", name: "result", args: { text: data.reply } });
        }
      })
      .catch((err) => {
        console.warn("[Bridge] Error sending chat:", err);
        window.feed?.({ type: "state", name: "error" });
        window.feed?.({ type: "scene", name: "notify", args: { title: "Error de conexión", text: err.message } });
      });
  }

  // 2. Dictate toggle
  function dictate(active) {
    if (active) {
      window.feed?.({ type: "state", name: "listening" });
      window.feed?.({ type: "mic", on: true });
    } else {
      window.feed?.({ type: "state", name: "idle" });
      window.feed?.({ type: "mic", on: false });
    }
  }

  // 3. Send text to phone (via clipboard endpoint)
  function sendToPhone(text) {
    if (!text) return;
    fetch(`${BASE_URL}/api/device/clipboard`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text })
    }).catch(err => console.warn("[Bridge] sendToPhone error:", err));
  }

  // 4. Quick chip action
  function chipAction(action, contextText) {
    if (action === "summarize") {
      sendChat(`Resume en pocas líneas el siguiente resultado:\n${contextText}`);
    } else if (action === "explain") {
      sendChat(`Explícame esto de forma más sencilla:\n${contextText}`);
    }
  }

  // 5. Cancel / Stop
  function cancel() {
    fetch(`${BASE_URL}/api/stop`, {
      method: "POST",
      headers: { "x-api-key": API_KEY }
    }).catch(err => console.warn("[Bridge] Stop error:", err));
    window.feed?.({ type: "state", name: "idle" });
  }

  // 6. Media / Music controls
  function media(action, param = null) {
    fetch(`${BASE_URL}/api/media/control`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-api-key": API_KEY
      },
      body: JSON.stringify({ action, param })
    })
      .then(r => r.json())
      .then(res => {
        if (res && res.current) {
          window.feed?.({ type: "music", ...res.current });
        }
      })
      .catch(err => console.warn("[Bridge] Media control error:", err));
  }

  // 7. Save Keys (API Key Management in settings)
  const KEY_MAPPING = {
    anthropic: "ANTHROPIC_API_KEY",
    google: "GEMINI_API_KEY",
    openai: "OPENAI_API_KEY",
    openrouter: "OPENROUTER_API_KEY",
    groq: "GROQ_API_KEY",
    elevenlabs: "ELEVENLABS_API_KEY",
    github: "GITHUB_TOKEN",
    stripe: "STRIPE_SECRET_KEY"
  };

  function setKey(serviceId, keyValue) {
    const envKey = KEY_MAPPING[serviceId] || `${serviceId.toUpperCase()}_API_KEY`;
    const secrets = {};
    if (Array.isArray(keyValue)) {
      secrets[envKey] = keyValue[0] || "";
    } else {
      secrets[envKey] = keyValue || "";
    }

    fetch(`${BASE_URL}/api/secrets`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-api-key": API_KEY
      },
      body: JSON.stringify({ secrets })
    })
      .then(r => r.json())
      .then(res => console.log("[Bridge] Secret saved:", res))
      .catch(err => console.warn("[Bridge] Error saving secret:", err));
  }

  /* ---------------- CONFIGURATION API ---------------- */
  async function getConfigKeys() {
    try {
      const res = await fetch(`${BASE_URL}/api/config/keys`);
      return res.ok ? await res.json() : { keys: {} };
    } catch (e) {
      console.warn("[Bridge] getConfigKeys error:", e);
      return { keys: {} };
    }
  }

  async function saveConfigKeys(keys) {
    try {
      const res = await fetch(`${BASE_URL}/api/config/keys`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ keys })
      });
      return res.ok;
    } catch (e) {
      console.warn("[Bridge] saveConfigKeys error:", e);
      return false;
    }
  }

  async function getModelsConfig() {
    try {
      const res = await fetch(`${BASE_URL}/api/config/models`);
      return res.ok ? await res.json() : { current: {}, available: {} };
    } catch (e) {
      console.warn("[Bridge] getModelsConfig error:", e);
      return { current: {}, available: {} };
    }
  }

  async function saveModelsConfig(models) {
    try {
      const res = await fetch(`${BASE_URL}/api/config/models`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(models)
      });
      return res.ok;
    } catch (e) {
      console.warn("[Bridge] saveModelsConfig error:", e);
      return false;
    }
  }

  async function getMcpServers() {
    try {
      const res = await fetch(`${BASE_URL}/api/config/mcp`);
      return res.ok ? await res.json() : { servers: [] };
    } catch (e) {
      console.warn("[Bridge] getMcpServers error:", e);
      return { servers: [] };
    }
  }

  async function addMcpServer(name, command, args = []) {
    try {
      const res = await fetch(`${BASE_URL}/api/config/mcp`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, command, args })
      });
      return res.ok;
    } catch (e) {
      console.warn("[Bridge] addMcpServer error:", e);
      return false;
    }
  }

  async function deleteMcpServer(name) {
    try {
      const res = await fetch(`${BASE_URL}/api/config/mcp/${encodeURIComponent(name)}`, {
        method: "DELETE"
      });
      return res.ok;
    } catch (e) {
      console.warn("[Bridge] deleteMcpServer error:", e);
      return false;
    }
  }

  async function getAlertsConfig() {
    try {
      const res = await fetch(`${BASE_URL}/api/config/alerts`);
      return res.ok ? await res.json() : { alerts: {} };
    } catch (e) {
      console.warn("[Bridge] getAlertsConfig error:", e);
      return { alerts: {} };
    }
  }

  async function saveAlertsConfig(alerts) {
    try {
      const res = await fetch(`${BASE_URL}/api/config/alerts`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ alerts })
      });
      return res.ok;
    } catch (e) {
      console.warn("[Bridge] saveAlertsConfig error:", e);
      return false;
    }
  }

  async function getDesktopStatus() {
    try {
      const res = await fetch(`${BASE_URL}/api/desktop/status`);
      return res.ok ? await res.json() : {};
    } catch (e) {
      console.warn("[Bridge] getDesktopStatus error:", e);
      return {};
    }
  }


  // 9. Send Dropped File
  function sendFile(file) {
    if (!file) return;
    const formData = new FormData();
    formData.append("file", file);

    fetch(`${BASE_URL}/api/send_to_phone`, {
      method: "POST",
      body: formData
    })
      .then(r => r.json())
      .then(res => console.log("[Bridge] File sent:", res))
      .catch(err => console.warn("[Bridge] sendFile error:", err));
  }

  function sendFilePath(filePath) {
    if (!filePath) return;
    fetch(`${BASE_URL}/api/desktop/file_drop`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-api-key": API_KEY
      },
      body: JSON.stringify({ path: filePath })
    })
      .then(r => r.json())
      .then(res => console.log("[Bridge] File path handled:", res))
      .catch(e => console.warn("[Bridge] Error sending file path:", e));
  }

  // 10. Open Settings Window
  function openSettings() {
    if (window.__TAURI__?.core?.invoke) {
      window.__TAURI__.core.invoke('open_settings_window').catch(() => {
        window.__TAURI__.core.invoke('open_settings').catch(() => {
          window.open("miku_settings.html", "miku_settings", "width=920,height=720");
        });
      });
      return;
    }
    const pw = window.pywebview?.api;
    if (pw?.open_settings) {
      pw.open_settings();
    } else {
      window.open("miku_settings.html", "miku_settings", "width=920,height=720");
    }
  }

  // 11. Settings Sync
  function setSetting(k, v) {
    try {
      localStorage.setItem(`miku_${k}`, JSON.stringify(v));
      channel?.postMessage({ k: "cfg_item", key: k, value: v });
      fetch(`${BASE_URL}/api/setting`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "x-api-key": API_KEY
        },
        body: JSON.stringify({ key: k, value: v })
      }).catch(() => {});
    } catch (_) {}
  }

  // 12. Volume Control
  function setVolume(val) {
    const v = Math.max(0, Math.min(100, Math.round(Number(val))));
    media("vol", v);
    setSetting("voice_volume", v);
  }

  function initSettingsSync() {
    if (channel) {
      channel.onmessage = (e) => {
        const msg = e.data;
        if (msg && msg.k === "cfg_item") {
          window.feed?.({ type: "cfg_updated", key: msg.key, value: msg.value });
        }
      };
    }
  }

  async function getElevenLabsVoices() {
    try {
      const res = await fetch(`${BASE_URL}/api/elevenlabs/voices`);
      return await res.json();
    } catch (e) {
      return { status: "error", message: e.message, voices: [] };
    }
  }

  return {
    init,
    sendChat,
    dictate,
    sendToPhone,
    chipAction,
    cancel,
    media,
    setKey,
    sendFile,
    sendFilePath,
    openSettings,
    setSetting,
    setVolume,
    initLocalIp,
    generatePairingUrl,
    getConfigKeys,
    saveConfigKeys,
    getModelsConfig,
    saveModelsConfig,
    getMcpServers,
    addMcpServer,
    deleteMcpServer,
    getAlertsConfig,
    saveAlertsConfig,
    getDesktopStatus,
    getElevenLabsVoices
  };
})();

// Auto-initialize when DOM is ready
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", () => Bridge.init());
} else {
  Bridge.init();
}

window.Bridge = Bridge;
