# Interfaz de Escritorio (Widgets y UI) 🖥️

La interfaz visual de Miku en la PC está construida utilizando `PyQt6`, lo que permite crear interfaces aceleradas por hardware, con fondos transparentes y que "flotan" sobre otras ventanas (`WindowStaysOnTopHint`).

El orquestador principal es `ui.py`.

## Arquitectura de PyQt6 (`ui.py`)
- **`MikuFace (QMainWindow)`:** Es la ventana principal que contiene el GIF animado de Miku (modo mascota o modo escritorio) y la barra de entrada de texto. Se inicializa en `run_ui()`.
- **`UIComm`:** Un bus de eventos mediante `pyqtSignal`. Permite que los hilos en segundo plano (como `server.py` o los agentes) envíen comandos (ej. `show_card_signal`, `change_state_signal`) al hilo principal (Main Thread) de la GUI de forma segura sin causar crashes de C++.
- **Widgets Flotantes (`/widgets/`)**:
  - `MusicWidget`: Se alimenta en tiempo real de `music_controller.py` que a su vez usa `winrt.windows.media.control` para interceptar la sesión de música del sistema operativo (Spotify, Chrome, YouTube) mostrando la carátula, título y barra de progreso.
  - `WeatherWidget` y `ClockWidget`: Muestran información vital requerida por el usuario con animaciones de opacidad (fade-in) y posiciones calculadas para no estorbar.
  - `QuickLookWidget`: Intenta usar el software nativo `QuickLook` de Windows (vía Named Pipes) para previsualizar PDFs o imágenes de golpe. Si no está instalado, hace un fallback interno.
  - `UniversalCardWidget`: Un HUD para mostrar listas cortas de archivos e imágenes resultado de investigaciones del agente.

## Intercepción de Hardware y SO
- **`music_controller.py`:** Utiliza `winrt` (Windows Runtime) nativo. Crea un bucle asíncrono para escuchar cambios en el sistema multimedia de Windows, extrayendo incluso el `thumbnail_bytes` de la canción actual.
- **`send_to_miku.py`:** Un script puente que permite que otras aplicaciones de Windows llamen a Miku rápidamente inyectando comandos REST al Gateway.
- **Manejo de Arrastrar y Soltar (Drag & Drop):** `ui.py` implementa `dragEnterEvent` y `dropEvent`. Cuando arrastras un PDF o Imagen sobre Miku, ella extrae la ruta y lanza una orden `[SILENT_DROP]` al cerebro para que aplique RAG invisiblemente usando `analizar_archivo_silencioso`.

## Dynamic Island v6 & WebView (`miku_island/` & `miku_ui/`)
Además de la interfaz original PyQt6, Miku cuenta con una **Isla Dinámica fluida e interactiva (v6)**:
- **`miku_island/index.html` (v6)**: Isla dinámica interactiva en la parte superior central de la pantalla con micro-animaciones SVG/Canvas de Miku, estados reactivos (pensando, escuchando, trabajando, hablar), escenas (reproductor de música, previsualización de archivos QuickLook, aprobación de acciones, escaneo de herramientas) y selector magnético de agentes.
- **`miku_island/miku_settings.html` (v6)**: Panel completo de configuración y agentes sincronizado en tiempo real vía `BroadcastChannel('miku')` con la isla principal. Permite gestionar API Keys (Google Gemini, Anthropic, OpenAI, Groq), conectar LLMs locales (Ollama, LM Studio) y configurar la voz y atajos.
- **`miku_island/bridge.js`**: Puente universal bidireccional entre la interfaz web y el backend Python (`server.py`) vía WebSockets y llamadas REST autenticadas.
- **Ejecución de escritorio:**
  - `start_ui.py`: Utiliza `pywebview` sin bordes y transparente (`frameless=True`, `transparent=True`, `on_top=True`), redimensionando dinámicamente y recentrando la ventana en pantalla.
  - `miku_ui/` (Tauri 2): Binario nativo ultraligero en Rust con WebView2 para empaquetado de producción e instalador Windows.

---
👉 **Volver al Menú Principal:** [[Home]]
