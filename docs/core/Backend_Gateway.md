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
  - `GET /api/config/models`, `POST /api/config/models`: Motor de descubrimiento en vivo de modelos de IA (`models_provider.py`). Precarga por defecto un catálogo 100% real de todos los proveedores soportados (DeepSeek, Groq, Google, OpenAI, Anthropic, OpenRouter, Ollama) incluso sin claves configuradas, marcándolos como `[Requiere Clave]` para evitar selects vacíos o bloqueos en la interfaz. Detecta capacidades avanzadas de modelos en vivo (ej. `deepseek-flash` con modalidades de visión y texto para Computer Use).
  - **Aislamiento Multi-Agente (`brain.py`)**: `load_llm_history(target_agent)` filtra estrictamente los mensajes de usuario y respuestas por `agent_id`, impidiendo que un agente (como Antigravity) responda a solicitudes previas dirigidas a Miku u otros agentes.
  - **Persistencia en AppData (`miku_paths.py`)**: Centraliza las rutas de datos en `%APPDATA%/Miku` (`.env`, `chat_history/`, `models_config.json`, `agents_config.json`, `mcp_config.json`), asegurando que las API keys y conversaciones sobrevivan intactas a actualizaciones o reinstalaciones del ejecutable compilado. Soporta modo congelado (`sys.frozen`) con PyInstaller.
  - **Apagado Limpio (`POST /api/system/shutdown`)**: Permite a Tauri solicitar el cierre controlado del servidor FastAPI y liberación del puerto 8000 al cerrar la ventana o salir de la bandeja del sistema.
  - **Miku-Link & Transferencia Directa (`POST /api/desktop/send_file_to_phone`, `GET /api/temp_media/{filename}`)**: Permite compartir archivos desde la PC al celular tanto mediante el menú contextual de Windows ("Enviar a Mi teléfono") como mediante las herramientas del agente. Notifica a la Dynamic Island y emite el comando WebSocket `download_file` al companion móvil.
  - **Gestión de Enlace Móvil (`GET /api/link/status`, `POST /api/link/unpair`, `POST /api/link/open-folder`)**: Consulta el estado de emparejamiento, IP local del Gateway y desvinculación en tiempo real.
  - **Modo Bajo Costo / Ahorro (`POST /api/settings/low_cost_toggle`, `GET /api/settings/low_cost`)**: Activa/desactiva el modo de máxima economía en tokens y recursos, sincronizado con el System Tray (indicador 🟢/🔴) y el cierre de la Isla Dinámica.
  - **Optimizador de Tokens y Enrutador de Herramientas (`brain.py`)**: Reduce el consumo en más de un 80% mediante:
    1. Enrutamiento por clusters: En conversaciones casuales/chat no se inyecta ninguna herramienta (0 herramientas, ~1.7k tokens vs >16k de la lista completa de 54 tools).
    2. Ventana deslizante estricta: Limita el historial activo a los últimos 8 mensajes (4 turnos) y trunca salidas técnicas previas a un máximo de 200 caracteres.
    3. Reglas consolidadas: Sustitución de 61 reglas dispersas por 6 principios maestros (~120 tokens en vez de ~4,750).
  - **Tauri Sidecar y Empaquetado (`scripts/build_sidecar.py`)**: Empaqueta el Gateway completo en `miku-core-x86_64-pc-windows-msvc.exe`. Genera el ejecutable autónomo con PyInstaller para el empaquetador de Tauri 2 (`externalBin`), asegurando que todas las librerías nativas, modelos ONNX y endpoints residan en el instalador final de Windows. `lib.rs` gestiona su inicio invisible (`CREATE_NO_WINDOW`) y ciclo de vida.

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
