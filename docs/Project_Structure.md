# Estructura del Proyecto 🗂️

Esta guía mapea el directorio raíz de `miku V2` y orienta a desarrolladores y agentes de IA sobre el propósito de cada directorio y archivo principal.

---

## 🏛️ Directorios Principales
- **`miku_ui/`**: **Interfaz Oficial de Escritorio (Tauri 2)**.
  - `src-tauri/`: Aplicación nativa en Rust, configuración de ventanas, bandeja del sistema, actualizador criptográfico y orquestación del sidecar `miku-core.exe`.
  - `src/`: Dynamic Island (`index.html`), Centro de Control (`miku_settings.html`), lógica de comunicación (`bridge.js`) y efectos de sonido (`sound_fx.js`). 👉 [[Desktop_Island_Tauri]]
- **`miku_island/`**: Copia espejo directa de los assets estáticos de `miku_ui/src/`.
- **`miku_app/`**: Aplicación móvil para Android e iOS en React Native (Expo SDK 54). Contiene la lógica del chat, sincronización de portapapeles y vinculación mediante QR. 👉 [[Mobile_App]]
- **`docs/`**: Grafo de conocimiento y documentación técnica en formato Obsidian. 👉 [[Home]]
- **`scripts/`**: Scripts de construcción y automatización (`build_sidecar.py`).
- **`assets/`**: Iconos, imágenes oficiales de la aplicación e ilustraciones de Miku.
- **`venv/`**: Entorno virtual de Python con todas las dependencias del backend instaladas.

---

## 🧠 Archivos Principales del Backend Python (En Raíz)
- **`server.py`**: **El Gateway Central FastAPI**. Expone WebSockets bidireccionales en `/ws`, endpoints REST de configuración, conexión en caliente de MCPs, y detector ultrarrápido de juegos (<20ms). 👉 [[Backend_Gateway]]
- **`brain.py`**: Motor de razonamiento LLM y orquestador multi-agente con aislamiento estricto de prompts y memoria. 👉 [[Main_and_Agents]]
- **`models_provider.py`**: Catálogo dinámico de modelos por proveedor y función (Chat, Pro/Código, Computer Use, STT).
- **`music_controller.py`**: Controlador multimedia universal de Windows (GSMTC vía `winsdk`) para sincronización de audio y carátulas sin requerir Spotify.
- **`audio_handler.py`**: Escucha activa/pasiva de micrófono (Groq Whisper) y síntesis de voz (Edge TTS). 👉 [[Audio_and_Voice]]
- **`prompt_manager.py`**: Gestor de plantillas y reglas de personalidad de Miku.
- **`memory.py`, `memory_temporal.py`, `contacts_memory.py`, `spatial_memory.py`**: Sistemas de retención vectorial (ChromaDB) y base de datos relacional. 👉 [[Memory_System]]
- **`activity_monitor.py`**: Monitoreo de actividad de usuario y alertas proactivas.
- **`miku_paths.py`**: Rutas centralizadas y seguras hacia `%LOCALAPPDATA%/Miku Desktop/`.
- **`tools_*.py`**: Módulos de herramientas del sistema (código, archivos, web, periféricos, Spotify, etc.). 👉 [[Tools_Overview]]

---

## ⚠️ Componentes Legado / Fallback (No usar para desarrollo activo)
- **`ui.py` & `widgets/`**: Interfaz antigua basada en PyQt6. 👉 [[Widgets_and_UI]]
- **`start_ui.py`**: Lanzador anterior basado en PyWebView.
- **`main.py`**: Prototipo CLI temprano ya no presente en la raíz (reemplazado por `server.py`).

---
👉 **Volver al Menú Principal:** [[Home]]
👉 **Ver Arquitectura General:** [[Arquitectura_General]]
