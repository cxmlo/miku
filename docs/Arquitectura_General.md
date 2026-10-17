# Arquitectura General de Miku V2 🏰

Esta es la guía definitiva de la arquitectura de la aplicación Miku V2. El sistema está dividido en tres capas principales que interactúan en tiempo real: El **Cerebro y Gateway (Backend Python)**, la **Interfaz de Escritorio Oficial (Tauri 2 & Dynamic Island)** y la **Interfaz Móvil (React Native)**.

---

## 1. El Cerebro y Gateway (Backend Python)
Escrito en Python (versión 3.12+), reside en el núcleo del proyecto y se empaqueta en el ejecutable autónomo `miku-core.exe` (sidecar de Tauri).
- **Gateway Central:** Orquestado por FastAPI (`server.py`), maneja WebSockets bidireccionales en `/ws`, rutas REST, extrapolación en vivo de reproducción multimedia (`music_controller.py`), conexión en caliente de servidores MCP y detección ultrarrápida de juegos (<20ms). 👉 [[Backend_Gateway]]
- **Cerebro LLM Multi-Agente:** `brain.py` administra los modelos configurados (Google Gemini, Groq, OpenAI, DeepSeek, Anthropic, Ollama) y el enrutamiento de agentes autónomos con prompts y memorias aisladas. 👉 [[Main_and_Agents]]
- **Gestor de Proveedores de Modelos:** `models_provider.py` categoriza modelos en Chat, Pro/Código, Visión/Computer Use y STT con filtrado por proveedor.
- **Gestor de Prompts:** `prompt_manager.py` inyecta dinámicamente reglas de comportamiento y contexto.
- **Memoria:** Base de datos SQLite y memoria vectorial en ChromaDB para retención semántica y grafo de conocimiento. 👉 [[Memory_System]]
- **Audio y Voz:** `audio_handler.py` procesa audio pasivo/activo usando Whisper (Groq) para STT y Edge TTS para síntesis de voz sin bloqueo del hilo principal. 👉 [[Audio_and_Voice]]

---

## 2. Interfaz Oficial de Escritorio (Tauri 2 & Dynamic Island) 🏝️
**Esta es la interfaz de escritorio oficial y activa del proyecto Miku.**
- **Código Fuente:** `miku_ui/` (código nativo en Rust en `src-tauri` e interfaz web en `src/`).
- **Dynamic Island (`index.html`):** Píldora interactiva superior con micro-animaciones en Canvas/SVG, selector de agentes, chat con razonamiento y herramientas colapsables, visualizador de Computer Use y control multimedia.
- **Centro de Control (`miku_settings.html`):** Panel modular para agentes, modelos de IA, claves de API, servidores MCP, alertas de tiempo de uso y actualizaciones en 1 clic.
- **Documentación Completa:** 👉 [[Desktop_Island_Tauri]]

---

## 3. Interfaz Móvil (React Native Expo) 📱
La aplicación compañera permite llevar a Miku en el bolsillo e interactuar con el PC de forma remota.
- **Conectividad:** Mantiene un WebSocket vivo con el PC (`127.0.0.1:8000` / IP local o túnel Cloudflare). 👉 [[Mobile_App]]
- **Portapapeles Bidireccional:** El texto copiado en el celular viaja al PC y viceversa.
- **UI Reactiva:** `AssistantOverlay.tsx` provee un panel modal donde Miku se manifiesta de forma interactiva.

---

## 4. Servidores MCP (Model Context Protocol) 🔌
El backend utiliza la especificación oficial MCP (`mcp_config.json`) para cargar dinámicamente capacidades adicionales a través del binario `mcp-server` de Anthropic y comunitarios (`filesystem`, `memory`, `sqlite`, `github`, `google-drive`), ejecutándose en caliente al instalarse.

---

## ⚠️ Componentes Legado / Fallback (Deprecados)
- **`ui.py` y `widgets/` (PyQt6):** Interfaz de escritorio de versiones tempranas (V1). Mantenida únicamente como referencia histórica. 👉 [[Widgets_and_UI]]
- **`start_ui.py` (PyWebView):** Lanzador experimental anterior a la migración a Tauri 2.
- **`main.py`:** Prototipo CLI temprano; reemplazado completamente por `server.py` + `brain.py`.

---
👉 **Volver al Menú Principal:** [[Home]]
👉 **Explorar Estructura de Archivos:** [[Project_Structure]]
