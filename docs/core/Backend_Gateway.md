# Backend y Gateway 🧠

Ubicado en `server.py`, el Gateway es el corazón de las comunicaciones de Miku. Todo el ecosistema (celular, UI local, servicios externos) pasa por este servidor FastAPI con WebSockets asíncronos.

## `server.py` (FastAPI + WebSockets)
- **Clase `ConnectionManager`**:
  - `connect()`, `disconnect()`: Gestiona clientes WebSocket activos.
  - `_lock`: Utiliza un candado `asyncio.Lock()` para garantizar seguridad en hilos (thread-safety). Evita caídas (crashes ASGI) cuando múltiples tareas concurrentes (como el portapapeles y el LLM) intentan enviar mensajes por el mismo WebSocket simultáneamente.
  - `broadcast_status()`, `broadcast_message()`: Funciones para emitir el estado interno de Miku ("pensando", "escuchando") y comandos directos a las UI conectadas usando el `_lock`.

- **Arquitectura de WebSockets (`/ws`)**:
  - Al conectarse, el servidor **acepta primero** el socket y luego envía inmediatamente el estado más reciente del portapapeles (vía `LAST_CLIPBOARD`).
  - Mantiene un bucle de latido (Ping/Pong) manejando excepciones de desconexión sin hacer crash del servidor.

- **Endpoints HTTP (REST)**:
  - `GET /history`: Devuelve el historial de chat para que la app móvil se sincronice al arrancar. Utiliza un sistema de persistencia diario (`chat_history_YYYY-MM-DD.json`) para no perder la memoria.
  - `POST /chat`: Procesa texto o comandos de los usuarios, interactúa con el cerebro (`brain.py`), y devuelve la síntesis de audio (`tts`). Antes de enviar al TTS, pasa por `clean_text_for_speech` para eliminar sintaxis Markdown (*sonríe*, emojis) asegurando voces naturales. Emite actualizaciones de estado ("Escribiendo...", "Pensando...") por el WebSocket en tiempo real.
  - `POST /audio`: Recibe audio desde el móvil para procesamiento STT y orquesta el flujo hacia el cerebro.
  - `GET /audio_temp`: Sirve el archivo de audio sintetizado a la app móvil.
  - `POST /api/secrets`: Guarda diccionarios enteros de credenciales para servicios (dinámicamente) de forma masiva en el `.env`.
  - `DELETE /api/mcp/{server_name}`: Detiene y elimina un servidor MCP de la memoria del cliente MCP dinámicamente y sin reiniciar.
  - `POST /pair_init`, `POST /pair_confirm`: Endpoints de vinculación de dispositivos seguros usando JWT y llaves públicas. 👉 [[Database_and_Security]]
  - `GET /api/config/models`, `POST /api/config/models`: Motor de descubrimiento en vivo de modelos de IA (`models_provider.py`). Consulta los endpoints oficiales de Google Gemini, Groq, DeepSeek, OpenAI, Anthropic y Ollama local para listar únicamente modelos 100% reales asociados a las API Keys configuradas en el `.env`.
  - **Aislamiento Multi-Agente (`brain.py`)**: `load_llm_history(target_agent)` filtra estrictamente los mensajes de usuario y respuestas por `agent_id`, impidiendo que un agente (como Antigravity) responda a solicitudes previas dirigidas a Miku u otros agentes.
  - **Persistencia en AppData (`miku_paths.py`)**: Centraliza las rutas de datos en `%APPDATA%/Miku` (`.env`, `chat_history/`, `models_config.json`, `agents_config.json`, `mcp_config.json`), asegurando que las API keys y conversaciones sobrevivan intactas a actualizaciones o reinstalaciones del ejecutable compilado. Soporta modo congelado (`sys.frozen`) con PyInstaller.
  - **Apagado Limpio (`POST /api/system/shutdown`)**: Permite a Tauri solicitar el cierre controlado del servidor FastAPI y liberación del puerto 8000 al cerrar la ventana o salir de la bandeja del sistema.
  - **Tauri Sidecar (`scripts/build_sidecar.py`)**: Empaqueta el Gateway completo en `miku-core-x86_64-pc-windows-msvc.exe` mediante PyInstaller, permitiendo que la aplicación instalada funcione sin requerir Python en la máquina del usuario. `lib.rs` gestiona su inicio invisible (`CREATE_NO_WINDOW`) y ciclo de vida.

- **Autenticación del cliente Android (`X-Device-Id`)**: Las rutas protegidas por la dependencia de API key y el handshake de `/ws` aceptan el identificador de un dispositivo ya emparejado en la cabecera `X-Device-Id`. Los clientes antiguos que usan `x-api-key` siguen siendo compatibles. Las rutas de emparejamiento registran el dispositivo antes de habilitar esta autenticación.

- **Endpoints Nativos / PC**:
  - `GET /wallpaper`: Devuelve el fondo de pantalla actual de Windows en Base64 (vía `ctypes`).
  - `GET /miku_gif`: Devuelve los GIFs dinámicos (idle, thinking, talking) alojados en el servidor local.

- **Hilos Secundarios (Background Threads)**:
  - `clipboard_monitor()`: Usa un hilo asíncrono para vigilar constantemente si hay cambios en el portapapeles de Windows (usando `win32clipboard`) y notificarlos a los clientes conectados de manera no bloqueante.
  - `pc_mic_worker()`: Lanza el detector continuo del micrófono de PC (openwakeword).

- **Clase `StdoutHook`**:
  - Intercepta la salida de consola (`sys.stdout`) para reenviar logs al sistema UI PyQt6 en tiempo real.

## Enlaces Relacionados
- 👉 Volver a [[Home]]
- Relacionado con: [[Main_and_Agents]]
- Relacionado con: [[Project_Structure]]
