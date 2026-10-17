# Estructura del Proyecto 🗂️

Esta guía mapea el directorio raíz de `miku V2` y orienta a desarrolladores y agentes de IA sobre el propósito de cada directorio y archivo principal.

---

## 🏛️ Directorios Principales
- **`miku_ui/`**: **Interfaz Oficial de Escritorio (Tauri 2)**.
  - `src-tauri/`: Aplicación nativa en Rust, configuración de ventanas, bandeja del sistema, actualizador criptográfico y orquestación del sidecar `miku-core.exe`.
  - `src/`: fuente canónica del frontend Tauri: Dynamic Island (`index.html`), Centro de Control (`miku_settings.html`), puente (`bridge.js`) y efectos de sonido (`sound_fx.js`). 👉 [[Desktop_Island_Tauri]]
- **`miku_android/`**: Nueva app móvil Android nativa (Kotlin/Jetpack Compose). Se conecta al Island mediante HTTP y WebSocket, con emparejamiento QR, chat, eventos de agentes y controles del teléfono. 👉 [[Mobile_App]]
- **`miku_app/`**: Cliente anterior React Native/Expo, conservado intacto como legado y rollback durante la migración a Android nativo. No es la ruta activa para nuevas funciones móviles. 👉 [[Mobile_App]]
- **`miku_island/`**: Espejo de compatibilidad que el backend aún publica en `/island`. Los archivos compartidos se verifican con `python scripts/sync_island.py` y se sincronizan desde `miku_ui/src/` con `python scripts/sync_island.py --sync`; no borrar mientras siga montado por FastAPI.
- **`docs/`**: Grafo de conocimiento y documentación técnica en formato Obsidian. 👉 [[Home]]
- **`scripts/`**: Scripts de construcción y automatización (`build_sidecar.py`).
- **`assets/`**: Iconos, imágenes oficiales de la aplicación e ilustraciones de Miku.
- **`venv/`**: Entorno virtual de Python local; no forma parte del código fuente.

La guía común de arquitectura, diseño, estructura objetivo de Android y propuesta de packs de contenido está en [[PROJECT_ARCHITECTURE_AND_DESIGN]].

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
