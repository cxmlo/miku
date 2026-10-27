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
- **Rediseño Apple Dark Glass & Efecto Lente**:
  - Acabado translúcido con efecto lente (`backdrop-filter: blur(36px-40px) saturate(210%)`), bisel especular superior de 1px (`rgba(255, 255, 255, 0.22)`), y gradientes radiales sutiles.
  - **Cierre universal al hacer clic afuera**: Cierre instantáneo a `compact` al perder foco o pulsar en cualquier ventana o monitor (`window-blur`, `tauri://blur`, `onFocusChanged`).
  - **Animación "Pensando" compacta**: Al enviar un mensaje, la isla se minimiza inmediatamente mostrando el cronómetro y la animación de Miku pensando, expandiéndose directamente al chat (`result`) al llegar la respuesta.
  - **Burbujas de Chat estilo Apple iOS & Siri**: Tarjetas de respuesta translúcidas (`backdrop-filter: blur(20px) saturate(180%)`), radio de borde asimétrico estilo iPhone (`18px 18px 18px 5px`), cabecera con badge de agente y punto brillante, formateo enriquecido de markdown (`**negrita**`, viñetas `•` alineadas, código en píldora) y burbuja de usuario en azul iMessage (`linear-gradient(145deg, #0A84FF, #0066d6)`).
  - **Orejas de la Isla Sin Costuras (Seamless Ears)**: Unificación matemática del arco de 1px (`radial-gradient`) y eliminación de la espiga vertical superior mediante sombreado de inserción y `border-top: none !important`.
  - **Tipografía Minimalista Apple SF Pro / Inter**: Pila tipográfica limpia con renderizado optimizado y tracking de `-0.012em` que reemplaza por completo la tipografía por defecto de Windows.
  - **Motor de Efectos de Sonido Táctil (`sound_fx.js`)**: Módulo sin dependencias que sintetiza en tiempo real mediante Web Audio API micro-sonidos Apple (clics mecánicos, pops de menús, alternadores de switch, pestañas, envío de mensajes y campana armónica de dos tonos al recibir respuestas de IA).
  - **Deslizamiento Marquee en Selectores (`GlideSelect`)**: Estructura desacoplada `.gs-wrap` + `.gs-track` con cálculo dinámico de `scrollWidth` que elimina el corte brusco con puntos suspensivos (`...`) y genera un paneo infinito suave de extremo a extremo.
  - **Chat ampliado verticalmente con Liquid Create Menu**: Panel de respuesta ampliado (580px ancho, min-height 230px, hasta 380px de lectura) para una visualización holgada y cómoda; se eliminó el modal de opciones de mensaje y se incorporó el **Liquid Create Menu** en el botón `+` del chat, con animación elástica de resorte y esquinas concéntricas para adjuntar archivos, analizar pantalla (visión), pegar del portapapeles y alternar agentes.
  - **Componentes unificados con `HoldButton` por defecto**: Todos los botones de acción crítica en la configuración (crear agente, eliminar agente, guardar/eliminar claves API, añadir/quitar servidores MCP, activar alertas y restablecer) utilizan `HoldButton` con retroalimentación háptica visual progresiva.
  - **Paleta de colores fríos y bloqueo de tema**: Colores de halo y acento actualizados a tonos fríos, opacos y mate (Nordic slate, ámbar frío, lavanda helada, esmeralda nórdico, carmesí apagado, etc.) que se fijan y bloquean como tema activo de toda la ventana de ajustes (`--ac`).
  - **Control de volumen `SmoothSlider` cápsula**: Barra de volumen horizontal refinada con arrastre continuo (`pointerdown` + `pointermove`), salto inmediato al clic y sincronización visual sin errores.
  - **Preguntas interactivas flotantes**: Soporte de eventos bidireccionales WebSocket y HTTP (`/api/ui_event`) para selección instantánea en `hacer_pregunta_opciones`.
  - **Botón `+` y Liquid Create Menu**: Botón `+` visible y estilizado en el input de chat con rotación a 45°, menú desplegable elástico (`initLiquidMenu`) con adjuntar archivo, visión de pantalla, portapapeles y agentes.
  - **Alertas Proactivas Limpias y Personalizadas**: Eliminadas las apps por defecto (`DEFAULT_ALERTS = {}`); selección directa de apps en ejecución al pulsar sus tarjetas, botón para eliminar alertas existentes (`✕`), y selector de ruta ejecutable con botón `Examinar...` (`.exe`).
  - **Separación visual de Sliders**: Sliders de minutos limpios sin iconos de bocina (los iconos de altavoz son exclusivos de volumen).
  - **Arrastre Continuo de Volumen**: `SmoothSlider` y `Slosh` en la isla admiten clic sostenido y arrastre libre a nivel de ventana (`window.pointermove`/`pointerup`) con thumb visible y hitbox ampliado de 28px para fácil manipulación.
  - **Exclusividad de Servidores MCP en Agentes**: Selector de servidor MCP en la edición de cada agente con bloqueo inteligente `[Nombre] 🔒 (En uso por [Agente])` que impide que dos agentes compartan el mismo servidor MCP simultáneamente.
  - **Chat Multagente con Contexto Aislado (`AGENT_CHATS`)**:
    - Cada agente (GitHub, Claude, Coder, etc.) cuenta con su propia memoria persistente y buzón de conversación (`lastQ`, `lastA`, `history`).
    - Al cambiar de agente en la isla o el menú, el chat recupera automáticamente la última pregunta y respuesta de ese agente específico.
    - Ejecución silenciosa: Los agentes secundarios trabajan puramente en texto y llamadas a herramientas (MCP/sistema) sin emitir voz por altavoces (`silent: true`).
  - **Insignia de Notificación en la Mascota (`MascotNotificationBadge`)**:
    - Cuando un agente completa una tarea en segundo plano mientras el usuario atiende a otro agente o la isla está compacta, aparece una insignia circular púrpura `(...)` sobre la cabeza/oreja de la mascota y su pill brilla con animación de pulso.
    - Al hacer clic en la mascota o en la pill, la isla salta instantáneamente al chat de ese agente y limpia la notificación.
  - **Escena de Permisos y Atajos de Teclado**:
    - Al requerir aprobación para comandos (`SC.approve`), la mascota luce un halo ámbar con insignia de advertencia `(!)`.
    - Botones estilizados `Deny [N]`, `Allow [Y]` y `Always`, con atajos nativos directos de teclado (`Y` para permitir, `N` para denegar).
  - **Sistema de Actualización Automática (Tauri v2 Updater)**:
    - Integración de `tauri-plugin-updater = "2"` en `Cargo.toml`, `tauri.conf.json`, `capabilities/default.json` y `lib.rs`.
    - Claves criptográficas Minisign / Ed25519 (`miku_updater.key.pub`) configuradas para validación de integridad y autenticidad del binario.
    - Comandos nativos en Rust (`check_update`, `install_update`) expuestos a través de `Bridge.checkUpdate()` y `Bridge.installUpdate()`.
    - Detección y gestión tolerante a fallos: respuesta 404 de GitHub tratada como sistema al día en lugar de arrojar error.
    - Interfaz gráfica en Configuración (`miku_settings.html`): tarjeta en la sección General con botón interactivo, spinner de búsqueda, aviso de versión y botón de instalación con reinicio asistido.
    - CI/CD en GitHub Actions (`.github/workflows/release.yml`): generación de `latest.json`, firma automática del instalador y creación del alias `Miku_Setup.exe` para descarga directa desde la landing page al empujar etiquetas `v*`.

  - **Refinamiento Miku 2.0 (Desplegables `GlideSelect`)**:
    - Se resolvió el solapamiento de menús con secciones y tarjetas inferiores mediante elevación de contexto de apilamiento dinámico (`section:has(.gs-m.open), .card:has(.gs-m.open) { z-index: 999999 !important; }`), despliegue inteligente hacia arriba (`.gs-m.up`) y escucha de clics directa.
    - Se eliminó el cuadro/pill flotante desalineado de hover (`.gs-p { display: none !important }`) y se implementó hover nativo Apple Liquid Glass (`rgba(255,255,255,0.14)`) con resplandor superior de 1px.
  - **Paridad de Paleta de Color de Agentes**:
    - La sección de personalización de agentes en `miku_settings.html` utiliza exactamente los 8 tonos vibrantes de la isla dinámica (`['#F2A765','#F06CF0','#6C63FF','#FF5C66','#4FD3B1','#3B9EFF','#FFD84D','#9BE15D']`).
  - **Control de Volumen con Clic Sostenido (`SmoothSlider`) en Isla y Ajustes**:
    - Arrastre continuo mejorado: la captura de puntero y los listeners `pointermove` y `pointerup` en `window` se activan desde cualquier punto de la barra del control de volumen (excluyendo solo los iconos de silenciar/100%), permitiendo deslizar fluidamente manteniendo pulsado el clic en tiempo real.
    - La vista de ajustes rápidos de la isla (`scene: 'settings'`) ahora integra el mismo componente `SmoothSlider` para la fila "Sonido y voz", reemplazando el slider anterior y ofreciendo paridad visual total.
  - **Formateo de Micrófonos idéntico a Discord**:
    - Detección de dispositivos mediante `DirectSound` para evitar nombres truncados de 32 caracteres de MME y permitir sample rates nativos de 16 kHz.
    - Formato desacoplado: `Windows Default (Controlador)`, `Controlador · Endpoint` (ej. `Realtek(R) Audio · Micrófono`, `Realtek(R) Audio · Varios micrófonos`), replicando fielmente la interfaz de Discord.
  - **Envío Instantáneo y Lectura de Archivos para Modelos de IA**:
    - Lectura instantánea en frontend con `f.text()` para archivos de código, HTML y texto, evitando desfases asíncronos y pasando el contenido por `attachment_content` directamente a la petición `/chat` para que Gemini/LLM reciba el 100% del archivo.
  - **Aislamiento Multagente y Control de Voz**:
    - Corte instantáneo de voz (`stopSpeaking()`) al alternar entre agentes o recibir respuestas en segundo plano.
    - La animación de "pensando" se encuentra ligada al estado `busy` del agente en pantalla (`curAg().id`), impidiendo que el agente entrante herede la animación de pensando de otro agente.
  - **Burbuja de Chat Dinámica con el Color del Agente Activo**:
    - La burbuja del usuario ya no es azul iMessage estático: se vincula dinámicamente al color del agente activo (`style="--pc:${agentColor}"`), luciendo un acabado Liquid Frosted Glass con gradiente perlado o del tono del agente (blanco para Miku, esmeralda para GitHub, cian para Antigravity) con reborde y resplandor a tono.
    - El archivo adjunto se presenta como un chip compacto Apple dentro de la burbuja y la píldora previa en la barra de entrada se elimina inmediatamente tras pulsar enviar.
  - **Protección de la Isla Dinámica al Adjuntar Archivos y Contexto LLM**:
    - Apertura del selector de archivos nativo protegida con `window.__pickingFile = true` y validación centralizada mediante `collapse()`, impidiendo que la isla se cierre o repliegue al perder foco por abrir el explorador de Windows.
    - El endpoint `/chat` en `server.py` y `bridge.js` recibe `attachment_name`, `attachment_path` y `attachment_data`, guardando si es necesario en almacenamiento temporal e inyectando `[ARCHIVO ADJUNTADO]` junto con el análisis de contenido generado por `analizar_archivo_silencioso` directamente en el prompt del LLM.
  - **Ventana de Ajustes Movible pero No Redimensionable**:
    - Bloqueo estricto del redimensionado (`resizable: false` tanto en `tauri.conf.json` como en `WebviewWindowBuilder::new(...).resizable(false)` en `lib.rs`), conservando el arrastre fluido desde la cabecera minimalista (`data-tauri-drag-region` y `startDragging()`).
    - Componentes renovados a **Apple Liquid Glass** sobre fondo negro puro (`#000000`), con gradientes de refracción curvados estilo gota de agua y biselado especular.
  - **Modalidad Web Showcase / Sandbox Aislada**:
    - Detección automática en `bridge.js` y `settings.js` de entornos web/demostración (GitHub Pages, `srcdoc` iframes o `window.IS_WEB_SHOWCASE = true`).
    - Desconexión completa de WebSockets y peticiones REST hacia `127.0.0.1:8000` en la web pública para evitar que las pruebas interactivas de visitantes en la landing page controlen su servidor backend local o ejecuten acciones en su PC real.
    - Carga estática interactiva de datos simulados (mock data) para todos los paneles de ajustes (General, Agentes, Modelos IA, Keys, MCP, Alertas de enfoque, Centro de Audio y Miku-Link) con iconos y estilos 100% integrados sin dependencias externas.

---
👉 **Volver al Menú Principal:** [[Home]]
