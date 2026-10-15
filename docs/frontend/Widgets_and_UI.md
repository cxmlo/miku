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
- **`miku_island/index.html` (v6)**: Isla dinámica interactiva en la parte superior central de la pantalla con micro-animaciones SVG/Canvas de Miku, estados reactivos (pensando, escuchando, trabajando, hablar), escenas (reproductor de música con soporte multimedia universal Windows, previsualización de archivos QuickLook, aprobación de acciones, escaneo de herramientas) y selector magnético de agentes. Incluye un sistema de redimensionado no destructivo que mantiene la ventana nativa transparente amplia durante el colapso (420ms) para evitar cortes bruscos de animación.
- **`miku_island/miku_settings.html` (v6)**: Panel amplio (880px) de configuración y agentes sincronizado en tiempo real vía `BroadcastChannel('miku')`:
  - **Selector paralelo de agentes**: Gran avatar y los 3 slots de la isla en paralelo, con **Miku (Blanco/Original)** siempre seleccionable en la primera posición.
  - **Componente `WheelDial`**: Indicador circular de 60 divisiones sobre 300° con simulación de resorte fluido (spring overshoot) y ondas dinámicas para ajuste de volumen de voz y notificaciones.
  - **Alertas Proactivas por Aplicación**: Detección de aplicaciones activas (VS Code, Discord, Chrome, Spotify, Steam, Telegram, etc.) con sus iconos oficiales e umbrales configurables en minutos.
  - **Catálogo MCP con 1 Clic**: Instalación guiada e inmediata de servidores esenciales (`file_system`, `memory`, `sqlite`, `github`, `google-drive`) y configuración persistente en `.env`.
  - **Soporte Bilingüe Completo**: Conmutación instantánea entre español e inglés.
- **`miku_island/bridge.js`**: Puente universal bidireccional entre la interfaz web y el backend Python (`server.py`) vía WebSockets y llamadas REST autenticadas (`127.0.0.1` DNS-safe).
- **Ejecución de escritorio y Control de Instancias:**
  - **Bloqueo de Instancia Única (Mutex Global)**: Implementado tanto en Rust (`Global\MikuDynamicIslandSingleInstanceMutex`) como en Python (`start_ui.py`) para impedir la apertura de múltiples instancias simultáneas. Al intentar abrir Miku nuevamente, enfoca y restaura la ventana activa existente.
  - `start_ui.py`: Utiliza `pywebview` sin bordes y transparente (`frameless=True`, `transparent=True`, `on_top=True`), redimensionando dinámicamente y recentrando la ventana en pantalla.
  - `miku_ui/` (Tauri 2): Binario nativo ultraligero en Rust con WebView2, menú de bandeja del sistema limpio (`Configuración` y `Salir`), y ventana de configuración optimizada (980x740).

---
👉 **Volver al Menú Principal:** [[Home]]
