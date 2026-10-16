# Regla de Diseño y Estándares de Interfaz de Miku 1.0 / Miku V2

Esta regla es de cumplimiento **OBLIGATORIO** para cualquier modificación en la interfaz gráfica (Tauri, WebViews, `miku_ui`, `miku_island`, HTML, CSS y JS).

---

## 1. Botones de Acción Crítica: Paradigma `HoldButton`
- **Todos los botones de instalación, adición, eliminación o guardado crítico DEBEN ser `HoldButton`.**
  - **Servidores MCP**: Al añadir o instalar MCPs recomendados, se usa siempre `HoldButton` (`.hb-mcp-inst`, etc.). Cuando el usuario completa el hold, la instalación se ejecuta **inmediatamente** en segundo plano (`Bridge.installMcp` o `Bridge.addMcpServer`) y actualiza el estado visual al terminar.
  - **Alertas Proactivas**: El botón "+ Añadir" para procesos o ejecutables personalizados debe ser un `HoldButton`.
  - **Claves de API y Modelos**: El guardado y borrado de variables del entorno `.env` y modelos usa `HoldButton` para prevenir modificaciones accidentales.
- **NUNCA** sustituir un `HoldButton` por un `<button>` estándar de click simple en estas operaciones.

---

## 2. Paleta de Color: OLED Deep Pitch Black
- **Fondo principal**: `#040507` (negro profundo, no gris apagado).
- **Tarjetas y contenedores**: `#08090d` y gradientes sutiles a `#0c0d12`.
- **Bordes y divisores**: `rgba(255, 255, 255, 0.07)` a `rgba(255, 255, 255, 0.12)`.
- **Textos secundarios / Muted**: `#8d92a4` y `#5c6070`.
- **Acentos**:
  - Miku Cyan: `#4FD3B1` / `#2dd4a0`
  - Violeta IA: `#6C63FF`
  - Estados activos/conectados: `#2dd4a0`
- **Prohibido**: Utilizar grises lavados tipo `#222`, `#2d2d30` o `#333` como fondo de pantalla o tarjetas principales.

---

## 3. Barras de Desplazamiento y Sliders (Sin bolitas)
- **Eliminar todas las bolitas/knobs circulares**:
  - En sliders de volumen y ajustes (`.so-slider-thumb`, `.so-knob`), el círculo indicador debe tener `display: none !important`.
  - La interacción debe ser a través de la barra de relleno (`.so-fill`) con feedback de color y cursor `pointer` / `ew-resize`.
- **Selección de minutos/tiempo para Alertas Proactivas**:
  - **NO usar sliders continuos para minutos**.
  - Utilizar el selector fluido `GlideSelect` con opciones discretas claras y legibles:
    `15m`, `30m`, `45m`, `1h`, `1.5h`, `2h`, `3h`, `4h`.

---

## 4. Distribución y Layouts
- **Distribución del Chat**:
  - Columna izquierda (`.chat-mascot-side`): Reservada exclusivamente para el avatar interactivo del muñeco / mascota.
  - Columna derecha (`.chat-main-side`): Para el historial de mensajes, globos de conversación, menú expandible `+` y el input de texto.
  - El menú `+` (adjuntar archivo, analizar pantalla, agentes, etc.) **NUNCA debe superponerse ni tapar a la mascota**.
  - **Selector de Agente en Chat**: Al pulsar el selector de agentes en la cabecera del chat, el cambio debe ocurrir *in-situ* dentro del chat, sin expulsar al usuario a la pantalla principal de overview.
- **Alertas Proactivas**:
  - Las aplicaciones detectadas en ejecución deben mostrarse en una **cuadrícula moderna y organizada (`.apps-grid`, `.app-grid-card`)**, nunca en carruseles estrechos o desalineados.
  - Espaciado generoso entre el campo de ruta, el botón "Examinar..." y el botón "+ Añadir".

---

## 5. Ventana y Comportamiento Nativo en Windows
- **Esquinas redondeadas sin artefactos negros**:
  - En ventanas Tauri borderless transparentes en Windows, `shadow` debe ser `false` (tanto en `tauri.conf.json` como en `lib.rs`) y la sombra debe ser gestionada por CSS en el elemento contenedor con padding en `body`. De lo contrario, el DWM de Windows dibuja un recuadro negro opaco detrás de las esquinas transparentes.
- **Procesos en segundo plano silenciosos**:
  - Todo script de PowerShell o invocación auxiliar (e.g. matar sintetizadores de voz al cerrar, abrir el selector de ejecutables nativo) debe invocar `CREATE_NO_WINDOW (0x08000000)` en el backend de Rust y Python para no abrir jamás ventanas de consola negras al usuario.

---

## 6. Dispositivos de Audio y Micrófono Real
- **Nombres reales de hardware**:
  - Nunca depender únicamente de `navigator.mediaDevices.enumerateDevices()` en WebViews de Tauri, pues reporta etiquetas vacías ("Micrófono 1").
  - Siempre consultar los nombres y canales reales al backend de Python mediante `/api/audio/devices` (`sounddevice.query_devices()`).
  - Al cambiar de micrófono, notificar al backend (`/api/audio/device`) para reconfigurar el listener del wake word ("Miku") y la grabación STT de manera inmediata.

---

## 7. Versionado Visible
- La versión oficial del sistema debe reflejarse visiblemente en el pie de la barra lateral de configuración (`v0.1.1`) y en el verificador de actualizaciones.
