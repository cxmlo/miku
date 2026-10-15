# Estructura del Proyecto 🗂️

Esta guía mapea el directorio raíz de `miku V2` y orienta a desarrolladores y agentes de IA sobre el propósito de cada directorio y archivo principal.

## Directorios Principales
- **`miku_app/`**: Contiene todo el código fuente del frontend móvil. Es un proyecto de React Native construido con Expo (SDK 54). Contiene la lógica del chat, reproducción de GIFs (estados) y vinculación por QR. 👉 [[Mobile_App]]
- **`widgets/`**: Contiene la lógica visual de los paneles semitransparentes (HUDs) para el escritorio, escritos en Python con PyQt6 (`devices.py`, `music.py`, `clock.py`, `weather.py`). 👉 [[Widgets_and_UI]]
- **`brain/`**: Directorio donde Miku almacena estados persistentes, memorias de conversación, y archivos temporales vitales para su ciclo de vida lógico. 👉 [[Memory_System]]
- **`db/`** *(si aplica)*: Dónde reside `miku_devices.db` (SQLite). 👉 [[Database_and_Security]]
- **`esp32_firmware/`**: Código C++ (Arduino) para hardware periférico de Miku.
- **`venv/`**: Entorno virtual de Python.

## Archivos Principales del Backend Python
- **`server.py`**: El Gateway FastAPI. Expone WebSockets y REST. 👉 [[Backend_Gateway]]
- **`main.py`**: El punto de entrada para la mente de Miku (Agentic Loop). 👉 [[Main_and_Agents]]
- **`ui.py`**: Interfaz PyQt6, controla la System Tray. 👉 [[Widgets_and_UI]]
- **`agents.py`**: Define el `AgentManager`.
- **`proactive_agent.py`**: Define el comportamiento proactivo en el background.
- **`prompt_manager.py`**: Gestor de la personalidad y reglas (system prompt).
- **`memory.py`, `memory_temporal.py`, `contacts_memory.py`, `spatial_memory.py`**: Sistemas de retención. 👉 [[Memory_System]]
- **`audio_handler.py`**: Escucha pasiva, STT (Speech-to-Text) y TTS (Text-to-Speech). 👉 [[Audio_and_Voice]]
- **`miku_db.py`**: Operaciones de base de datos para dispositivos y seguridad. 👉 [[Database_and_Security]]
- **`send_to_miku.py`**: Hook del menú contextual de Windows ("Enviar a Miku").

## Archivos de Herramientas (`tools_*.py`)
- Mapeados a fondo en 👉 [[Tools_Overview]]

## Enlaces Relacionados
- 👉 Volver a [[Home]]
