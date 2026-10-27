/* =========================================================================
   bridge.js — Universal Bridge for Miku Dynamic Island & Settings
   Connects miku_v6.html and miku_settings.html with the Python backend
   (server.py) over WebSocket and REST APIs.
   ========================================================================= */

const Bridge = (() => {
  "use strict";

  // Check if running in Web Showcase / Demo mode (e.g. GitHub Pages or iframe preview)
  const isShowcase = !window.__TAURI__ && !window.pywebview && (
    !!window.IS_WEB_SHOWCASE ||
    (typeof window !== "undefined" && (
      window.location.hostname.includes("github.io") ||
      (window.self !== window.top && (location.protocol === "https:" || location.protocol === "about:"))
    ))
  );

  // In Tauri on Windows, location.hostname is "tauri.localhost", which does NOT resolve in Windows DNS.
  // We must explicitly use 127.0.0.1 for local communication.
  const isLocal = !isShowcase && (!location.hostname || 
                  location.hostname === "localhost" || 
                  location.hostname === "127.0.0.1" || 
                  location.hostname.endsWith(".localhost") || 
                  location.hostname.includes("tauri"));
  const HOST = isLocal ? "127.0.0.1" : (location.hostname || "127.0.0.1");
  const BACKEND_PORT = "8000";
  const PORT = BACKEND_PORT;
  const BASE_URL = `http://${HOST}:${BACKEND_PORT}`;
  const WS_URL = `ws://${HOST}:${BACKEND_PORT}/ws`;
  const API_KEY = (typeof localStorage !== "undefined" && localStorage.getItem("miku_api_key")) || "miku_secure_key_2026";

  let ws = null;
  let reconnectTimer = null;
  let reconnectAttempts = 0;
  const MAX_RECONNECT_DELAY = 8000;

  // BroadcastChannel for cross-window sync (Island <-> Settings)
  const channel = typeof BroadcastChannel !== "undefined" ? new BroadcastChannel("miku") : null;

  async function apiFetch(path, options = {}) {
    if (isShowcase) {
      return new Response(JSON.stringify({ ok: true, status: "showcase" }), {
        status: 200,
        headers: { "Content-Type": "application/json" }
      });
    }
    const url = path.startsWith("http") ? path : `${BASE_URL}${path}`;
    const headers = Object.assign({
      "x-api-key": API_KEY
    }, options.headers || {});
    return fetch(url, { ...options, headers });
  }

  function init() {
    if (isShowcase) {
      console.log("[Bridge] Showcase demo mode active — server connection disabled.");
      window.feed?.({ type: "ws", ok: true });
      window.feed?.({ type: "api", ok: true });
      return;
    }
    connectWS();
    initLocalIp();
    initMouseTracker();
    fetchMediaStatus();
    initSettingsSync();
    fetchAgents();
  }

  function fetchAgents() {
    apiFetch("/api/agents")
      .then(r => r.json())
      .then(data => {
        if (data && Array.isArray(data.agents) && data.agents.length) {
          window.feed?.({ type: "agents", list: data.agents });
        }
      })
      .catch(() => {});
  }

  function fetchMediaStatus() {
    apiFetch("/api/media/status")
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
    if (isShowcase) return;
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

      try {
        channel?.postMessage({ k: "core_connected", ok: true });
      } catch (_) {}

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

  function sendWS(data) {
    if (ws && ws.readyState === WebSocket.OPEN) {
      try {
        ws.send(typeof data === "string" ? data : JSON.stringify(data));
        return true;
      } catch (err) {
        console.warn("[Bridge] ws.send error:", err);
      }
    }
    console.warn("[Bridge] Cannot send WS message (state: " + ws?.readyState + "):", data);
    return false;
  }

  /* ---------------- INCOMING MESSAGE ROUTER ---------------- */
  function handleIncomingMessage(data) {
    if (!data) return;

    // 1. Proactive Alerts from Server (Gaming, Work, Social, etc.)
    if (data.type === "proactive_alert") {
      console.log("[Bridge] Received Proactive Alert:", data);
      window.feed?.({
        type: "scene",
        name: "notify",
        args: {
          title: data.title || "Notificación de Miku",
          text: data.text || data.message || "",
          badge: data.badge || "Salud Digital"
        }
      });
      if (window.buddy?.emote) {
        window.buddy.emote("alert", 2500);
      }
      return;
    }

    // Handle ui_command from backend tools (e.g. hacer_pregunta_opciones)
    if (data.type === "ui_command") {
      if (data.action === "show_scene" && data.scene === "question") {
        const params = data.params || {};
        window.feed?.({
          type: "ask",
          title: params.title || "Pregunta de Miku",
          text: params.q || params.pregunta || "",
          options: params.options || []
        });
        return;
      } else if (data.action === "show_scene" && data.scene === "mail") {
        const params = data.params || {};
        window.feed?.({
          type: "ask",
          title: params.subject || "Borrador de Correo",
          text: `Para: ${params.to}\n\n${params.message}`,
          options: ["enviar_correo", "cancelar"]
        });
        return;
      }
    }

    // 2. Direct feed forward
    if (data.type) {
      if (data.type === "state" && window.buddy?.emote) {
        window.buddy.emote(data.name || "idle", data.dur || 2000);
      }
      if (data.type === "ui_command" && data.action === "status_update") {
        handleStatusUpdate(data.text);
      }
      window.feed?.(data);
      return;
    }

    // 3. Audio Player Event (TTS from Miku)
    if (data.audio_url) {
      console.log("[Bridge] Playing backend TTS audio:", data.audio_url);
      const audio = new Audio(`${BASE_URL}${data.audio_url}`);
      let vVol = 80;
      try {
        const cfg = JSON.parse(localStorage.getItem("miku_cfg") || "{}");
        if (cfg.voice_volume != null) vVol = Number(cfg.voice_volume);
      } catch (_) {}
      audio.volume = Math.max(0, Math.min(1, vVol / 100));
      window.__miku_tts_audio = audio;
      audio.play().catch(e => console.warn("[Bridge] Audio playback blocked:", e));
      window.feed?.({ type: "state", name: "talking" });
      audio.onended = () => {
        window.feed?.({ type: "state", name: "idle" });
      };
      return;
    }

    // 4. Status updates from backend
    if (data.status) {
      handleStatusUpdate(data.status);
    }

    // 5. Hooks / Agent events
    if (data.event) {
      const ev = data.event;
      const agent = data.agent_id || data.agent || "claude";
      const payload = data.payload || {};
      const prompt = payload.prompt || payload.query || "";
      const tool = payload.tool_name || payload.tool || "";

      if (ev === "Notification") {
        window.feed?.({
          type: "scene",
          name: "notify",
          args: {
            title: payload.title || "Notificación",
            text: payload.message || payload.text || ""
          }
        });
      } else if (ev === "PermissionRequest") {
        window.feed?.({
          type: "ask",
          title: "Permiso solicitado",
          text: `${agent} quiere ejecutar: ${tool}`,
          actions: ["Permitir", "Rechazar"],
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
      window.feed?.({ type: "agent_tool_step", name: "Computer Use", detail: rawText });
    } else if (text.includes("error")) {
      window.feed?.({ type: "state", name: "error" });
    } else {
      window.feed?.({ type: "state", name: "working" });
    }
  }

  /* ---------------- MIKU-LINK PAIRING QR ---------------- */
  async function generatePairingUrl() {
    if (isShowcase) {
      const demoUrl = "miku://pair?s=demo_showcase_2026&ip=192.168.1.50";
      window.setPairUrl?.(demoUrl);
      return demoUrl;
    }
    try {
      const infoResponse = await apiFetch("/api/desktop/info");
      if (!infoResponse.ok) {
        throw new Error(`No se pudo obtener la dirección de Miku Desktop (HTTP ${infoResponse.status}).`);
      }
      const info = await infoResponse.json();
      const ip = info.ip;
      if (!ip || ip === "127.0.0.1" || ip === "localhost" || ip === "::1") {
        throw new Error("Miku Desktop no encontró una dirección accesible en la red local.");
      }

      const randomBytes = new Uint8Array(16);
      window.crypto.getRandomValues(randomBytes);
      const sessionId = Array.from(randomBytes, byte => byte.toString(16).padStart(2, "0")).join("");

      const initResponse = await apiFetch("/api/pair/init", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId })
      });
      if (!initResponse.ok) {
        throw new Error(`No se pudo registrar la sesión de vinculación (HTTP ${initResponse.status}).`);
      }

      const pairUrl = `miku://pair?s=${encodeURIComponent(sessionId)}&ip=${encodeURIComponent(ip)}`;
      window.setPairUrl?.(pairUrl);
      return pairUrl;
    } catch (e) {
      console.warn("[Bridge] Error generating pair URL:", e);
      window.setPairUrl?.("");
      window.setPairError?.("No se pudo preparar el QR. Comprueba que Miku Desktop esté conectado al backend y a la red local.");
      return "";
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
          const res = await apiFetch("/mouse");
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

  // 1. Send chat prompt per agent
  function sendChat(text, agent, attachment = null) {
    if (!text || !text.trim()) return;
    const ag = agent || { id: "miku", name: "Miku" };
    window.feed?.({ type: "state", name: "thinking" });

    if (isShowcase) {
      setTimeout(() => {
        window.feed?.({
          type: "agent_reply",
          agent_id: ag.id,
          agent_name: ag.name,
          text: "¡Hola! Estás probando la demostración interactiva en la web de Miku. Para interactuar con modelos locales, ejecutar Computer Use y controlar tu sistema, descarga Miku Desktop para Windows o Miku Mobile para Android."
        });
        window.feed?.({ type: "state", name: "happy" });
        setTimeout(() => window.feed?.({ type: "state", name: "idle" }), 3500);
      }, 700);
      return;
    }

    const payload = {
      message: text,
      source: "desktop",
      agent_id: ag.id,
      agent_name: ag.name,
      agent_prompt: ag.prompt || "",
      agent_mcp: ag.mcp || null,
      silent: (ag.id !== "miku")
    };

    if (attachment) {
      payload.attachment_name = attachment.name;
      payload.attachment_path = attachment.filePath || null;
      payload.attachment_analysis = attachment.analysis || null;
      payload.attachment_data = attachment.dataUrl || null;
      payload.attachment_content = attachment.content || null;
    }

    apiFetch("/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload)
    })
      .then(async (res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        if (data && data.reply && !data.reply.includes("[IGNORAR]")) {
          window.feed?.({
            type: "agent_reply",
            agent_id: ag.id,
            agent_name: ag.name,
            text: data.reply
          });
        }
      })
      .catch((err) => {
        console.warn("[Bridge] Error sending chat:", err);
        const ch = window.getAgChat ? window.getAgChat(ag.id) : null;
        if (ch && !ch.busy && ch.lastA && !ch.lastA.startsWith('Error')) {
          console.log("[Bridge] Reply was already delivered via WebSocket, suppressing HTTP error.");
          return;
        }
        window.feed?.({
          type: "agent_reply",
          agent_id: ag.id,
          agent_name: ag.name,
          error: err.message,
          text: "Error de conexión: " + err.message
        });
      });
  }

  function stopSpeech() {
    apiFetch("/api/speech/stop", { method: "POST" }).catch(() => {});
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

  // 3. Send text directly to the connected phone clipboard
  async function sendToPhone(text) {
    if (!text) throw new Error("No hay texto para enviar.");
    const response = await apiFetch("/api/device/send_to_phone", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text })
    });
    const result = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(result.detail || `HTTP ${response.status}`);
    return result;
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
    apiFetch("/api/stop", {
      method: "POST"
    }).catch(err => console.warn("[Bridge] Stop error:", err));
    window.feed?.({ type: "state", name: "idle" });
  }

  // 5b. Floating question choice
  function choice(id, value) {
    if (isShowcase) {
      window.feed?.({ type: "state", name: "happy" });
      setTimeout(() => window.feed?.({ type: "state", name: "idle" }), 2000);
      return;
    }
    const payload = {
      type: "ui_event",
      action: "button_clicked",
      data: value
    };
    sendWS(payload);
    apiFetch("/api/ui_event", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    }).catch(e => console.warn("[Bridge] HTTP ui_event fallback error:", e));
  }

  // 6. Media / Music controls
  function media(action, param = null) {
    if (isShowcase) {
      if (action === "toggle") {
        window.feed?.({ type: "music", playing: 1, title: "Midnight City", artist: "M83", dur: 244, pos: 45 });
      }
      return;
    }
    apiFetch("/api/media/control", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
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

    apiFetch("/api/secrets", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
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
      const res = await apiFetch("/api/config/keys");
      return res.ok ? await res.json() : { keys: {} };
    } catch (e) {
      console.warn("[Bridge] getConfigKeys error:", e);
      return { keys: {} };
    }
  }

  async function saveConfigKeys(keys) {
    try {
      const res = await apiFetch("/api/config/keys", {
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
      const res = await apiFetch("/api/config/models");
      return res.ok ? await res.json() : { current: {}, available: {} };
    } catch (e) {
      console.warn("[Bridge] getModelsConfig error:", e);
      return { current: {}, available: {} };
    }
  }

  async function saveModelsConfig(models) {
    try {
      const res = await apiFetch("/api/config/models", {
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
      const res = await apiFetch("/api/config/mcp");
      return res.ok ? await res.json() : { servers: [] };
    } catch (e) {
      console.warn("[Bridge] getMcpServers error:", e);
      return { servers: [] };
    }
  }

  async function addMcpServer(name, command, args = []) {
    try {
      const res = await apiFetch("/api/config/mcp", {
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
      const res = await apiFetch(`/api/config/mcp/${encodeURIComponent(name)}`, {
        method: "DELETE"
      });
      return res.ok;
    } catch (e) {
      console.warn("[Bridge] deleteMcpServer error:", e);
      return false;
    }
  }

  async function toggleMcpServer(name, enabled) {
    try {
      const res = await apiFetch(`/api/config/mcp/${encodeURIComponent(name)}/toggle`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ enabled })
      });
      return res.ok;
    } catch (e) {
      console.warn("[Bridge] toggleMcpServer error:", e);
      return false;
    }
  }

  async function getAlertsConfig() {
    try {
      const res = await apiFetch("/api/config/alerts");
      return res.ok ? await res.json() : { alerts: {} };
    } catch (e) {
      console.warn("[Bridge] getAlertsConfig error:", e);
      return { alerts: {} };
    }
  }

  async function saveAlertsConfig(alerts) {
    try {
      const res = await apiFetch("/api/config/alerts", {
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

  async function getDetectableApps() {
    try {
      const res = await apiFetch("/api/apps/detectable");
      return res.ok ? await res.json() : { apps: [] };
    } catch (e) {
      console.warn("[Bridge] getDetectableApps error:", e);
      return { apps: [] };
    }
  }

  async function getRunningApps() {
    try {
      const res = await apiFetch("/api/apps/running");
      return res.ok ? await res.json() : { apps: [] };
    } catch (e) {
      console.warn("[Bridge] getRunningApps error:", e);
      return { apps: [] };
    }
  }

  async function getDesktopStatus() {
    try {
      const res = await apiFetch("/api/desktop/status");
      return res.ok ? await res.json() : {};
    } catch (e) {
      console.warn("[Bridge] getDesktopStatus error:", e);
      return {};
    }
  }

  async function getAudioDevices() {
    try {
      const res = await apiFetch("/api/audio/devices");
      return res.ok ? await res.json() : { devices: [] };
    } catch (e) {
      console.warn("[Bridge] getAudioDevices error:", e);
      return { devices: [] };
    }
  }

  async function setAudioDevice(index) {
    try {
      const res = await apiFetch("/api/audio/device", {
        method: "POST",
        body: JSON.stringify({ index })
      });
      return res.ok ? await res.json() : { status: "error" };
    } catch (e) {
      console.warn("[Bridge] setAudioDevice error:", e);
      return { status: "error", message: String(e) };
    }
  }

  async function browseExe() {
    try {
      const res = await apiFetch("/api/system/browse_exe", { method: "POST" });
      if (res.ok) {
        const data = await res.json();
        return data.path || "";
      }
      return "";
    } catch (e) {
      console.warn("[Bridge] browseExe error:", e);
      return "";
    }
  }

  // 9. Send Dropped File
  async function sendFile(file) {
    if (!file) throw new Error("No hay un archivo para enviar.");
    const formData = new FormData();
    formData.append("file", file);

    const response = await apiFetch("/api/send_to_phone", {
      method: "POST",
      body: formData
    });
    const result = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(result.detail || `HTTP ${response.status}`);
    return result;
  }

  function sendFilePath(filePath) {
    if (!filePath) return;
    apiFetch("/api/desktop/file_drop", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path: filePath })
    })
      .then(async response => {
        const result = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(result.detail || `HTTP ${response.status}`);
        return result;
      })
      .then(result => console.log("[Bridge] File path handled:", result))
      .catch(error => console.warn("[Bridge] Error sending file path:", error));
  }

  async function sendFileToPhonePath(filePath) {
    if (!filePath) throw new Error("No hay una ruta de archivo para enviar.");
    const response = await apiFetch("/api/desktop/send_file_to_phone", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ path: filePath })
    });
    const result = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(result.detail || `HTTP ${response.status}`);
    return result;
  }

  // 10. Open Settings Window
  function openSettings() {
    try {
      if (window.parent && window.parent !== window && window.parent.document && window.parent.document.getElementById('ajustes')) {
        window.parent.document.getElementById('ajustes').scrollIntoView({ behavior: 'smooth', block: 'center' });
        return;
      }
    } catch (_) {}

    function openWebSettings() {
      try {
        if (window.parent && window.parent !== window && window.parent.document && window.parent.document.getElementById('ajustes')) {
          window.parent.document.getElementById('ajustes').scrollIntoView({ behavior: 'smooth', block: 'center' });
          return;
        }
      } catch (_) {}

      let base = '';
      try {
        if (window.parent && window.parent !== window && window.parent.location.href && !window.parent.location.href.startsWith('about:')) {
          base = window.parent.location.href;
        }
      } catch (_) {}
      if (!base || base.startsWith('about:')) {
        base = (location.href && !location.href.startsWith('about:')) ? location.href : window.location.origin;
      }
      base = base.split('?')[0].split('#')[0];
      if (base.endsWith('.html')) {
        base = base.substring(0, base.lastIndexOf('/') + 1);
      } else if (!base.endsWith('/')) {
        base += '/';
      }
      const isIsland = location.pathname.includes('/island');
      const target = isIsland ? 'island/miku_settings.html' : 'miku_settings.html';
      const settingsUrl = new URL(target, base).href;
      window.open(settingsUrl, "miku_settings", "width=1080,height=780");
    }

    if (window.__TAURI__?.core?.invoke) {
      window.__TAURI__.core.invoke('open_settings_window').catch(() => {
        window.__TAURI__.core.invoke('open_settings').catch(() => {
          openWebSettings();
        });
      });
      return;
    }
    const pw = window.pywebview?.api;
    if (pw?.open_settings) {
      pw.open_settings();
    } else {
      openWebSettings();
    }
  }

  function openExternalUrl(url) {
    if (!url) return;
    try {
      if (window.__TAURI__?.shell?.open) {
        window.__TAURI__.shell.open(url).catch(() => window.open(url, "_blank"));
      } else {
        window.open(url, "_blank");
      }
    } catch (_) {
      window.open(url, "_blank");
    }
  }

  // 11. Settings Sync
  function setSetting(k, v) {
    try {
      localStorage.setItem(`miku_${k}`, JSON.stringify(v));
      channel?.postMessage({ k: "cfg_item", key: k, value: v });
      apiFetch("/api/setting", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ key: k, value: v })
      }).catch(() => {});
    } catch (_) {}
  }

  // 12. Volume Control (Solo voz de Miku, sin afectar volumen de música ni Windows)
  function setVolume(val) {
    const v = Math.max(0, Math.min(100, Math.round(Number(val))));
    setSetting("voice_volume", v);
    if (window.__miku_tts_audio) {
      window.__miku_tts_audio.volume = v / 100;
    }
  }

  // 13. Eliminar Clave de API
  async function deleteConfigKey(keyName) {
    try {
      const res = await apiFetch(`/api/config/keys/${keyName}`, {
        method: "DELETE"
      });
      return res.ok ? await res.json() : { error: "Error al eliminar clave" };
    } catch (e) {
      console.warn("[Bridge] deleteConfigKey error:", e);
      return { error: String(e) };
    }
  }

  // 14. Aplicaciones en ejecución (Estilo Discord)
  async function getRunningApps() {
    try {
      const res = await apiFetch("/api/apps/running");
      return res.ok ? await res.json() : { apps: [] };
    } catch (e) {
      console.warn("[Bridge] getRunningApps error:", e);
      return { apps: [] };
    }
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
      const res = await apiFetch("/api/elevenlabs/voices");
      return await res.json();
    } catch (e) {
      return { status: "error", message: e.message, voices: [] };
    }
  }

  async function getExecutionMode() {
    try {
      const res = await apiFetch("/api/config/execution_mode");
      return res.ok ? await res.json() : { current_mode: "full", available_modes: [] };
    } catch (e) {
      console.warn("[Bridge] getExecutionMode error:", e);
      return { current_mode: "full", available_modes: [] };
    }
  }

  async function setExecutionMode(mode) {
    try {
      const res = await apiFetch("/api/config/execution_mode", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mode })
      });
      return res.ok ? await res.json() : null;
    } catch (e) {
      console.warn("[Bridge] setExecutionMode error:", e);
      return null;
    }
  }

  return {
    init,
    sendChat,
    dictate,
    getExecutionMode,
    setExecutionMode,
    sendToPhone,
    chipAction,
    cancel,
    choice,
    media,
    setKey,
    sendFile,
    sendFilePath,
    sendFileToPhonePath,
    openSettings,
    openExternalUrl,
    setSetting,
    setVolume,
    initLocalIp,
    generatePairingUrl,
    getConfigKeys,
    saveConfigKeys,
    deleteConfigKey,
    getModelsConfig,
    saveModelsConfig,
    getMcpServers,
    addMcpServer,
    deleteMcpServer,
    toggleMcpServer,
    getAlertsConfig,
    saveAlertsConfig,
    testAlert: async () => {
      try {
        const res = await apiFetch("/api/alerts/test", { method: "POST" });
        return res.ok;
      } catch (_) {
        return false;
      }
    },
    getDetectableApps,
    getRunningApps,
    getDesktopStatus,
    getAudioDevices,
    setAudioDevice,
    browseExe,
    getElevenLabsVoices,
    stopSpeech,
    stopSpeaking: stopSpeech,
    async getAgents() {
      try {
        const res = await apiFetch("/api/agents");
        return res.ok ? await res.json() : { agents: [] };
      } catch (e) {
        return { agents: [] };
      }
    },
    async getAgents() {
      try {
        const res = await apiFetch("/api/agents");
        return res.ok ? await res.json() : { agents: [] };
      } catch (e) {
        return { agents: [] };
      }
    },
    async saveAgents(agentsList) {
      return this.saveAgentsBackend(agentsList);
    },
    async saveAgentsBackend(agentsList) {
      try {
        const res = await apiFetch("/api/agents", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ agents: agentsList })
        });
        return res.ok;
      } catch (e) {
        return false;
      }
    },
    async uploadFile(filename, content, isBase64 = false) {
      try {
        const res = await apiFetch("/api/upload_file", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ filename, content, is_base64: isBase64 })
        });
        return res.ok ? await res.json() : { status: "error" };
      } catch (e) {
        return { status: "error", message: e.message };
      }
    },
    async checkUpdate() {
      if (window.__TAURI__?.core?.invoke) {
        try {
          const res = await window.__TAURI__.core.invoke("check_update");
          return res || { available: false };
        } catch (err) {
          console.warn("[Bridge] check_update error:", err);
          return { available: false, error: err.toString() };
        }
      }
      try {
        const resp = await fetch("https://api.github.com/repos/cxmlo/miku/releases/latest");
        if (resp.ok) {
          const rel = await resp.json();
          const tag = (rel.tag_name || "").replace(/^v/, "");
          const current = "0.1.7";
          const isNewer = tag && tag !== current && tag > current;
          return { available: !!isNewer, version: tag, url: rel.html_url };
        }
      } catch (_) {}
      return { available: false };
    },
    async installUpdate() {
      if (window.__TAURI__?.core?.invoke) {
        try {
          return await window.__TAURI__.core.invoke("install_update");
        } catch (err) {
          console.warn("[Bridge] install_update error:", err);
          return { error: err.toString() };
        }
      }
      return { error: "Tauri no disponible" };
    }
  };
})();

// Auto-initialize when DOM is ready
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", () => Bridge.init());
} else {
  Bridge.init();
}

window.addEventListener("beforeunload", () => {
  try {
    Bridge.stopSpeech();
  } catch (_) {}
});

window.Bridge = Bridge;
