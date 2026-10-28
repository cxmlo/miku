# Decisiones de Arquitectura y Diseño — Rediseño de Configuración y Miku-Link

Este documento registra las preguntas abiertas de la **Fase 0** (según la sección §10 de `prompt-antigravity-rediseno-config.md`) y las decisiones de alineación técnica con el repositorio actual de **Miku V2**.

---

## Preguntas Abiertas para Confirmar antes de Iniciar la Fase 1

### 1. Alcance de las Secciones de Configuración (9 secciones del Catálogo vs Secciones actuales de Miku)
En `miku-catalogo.html` y `miku-design-rule.md` (§8) aparecen las 9 secciones del catálogo base (`General`, `Sonido y voz`, `Apariencia`, `Notificaciones`, `Miku-Link`, `Privacidad`, `Almacenamiento`, `Atajos`, `Acerca de`).
Por otro lado, tu aplicación actual en `settings.js` tiene las secciones críticas del motor de IA de Miku (`Agentes`, `Modelos de IA`, `Claves de API`, `Servidores MCP`), además de `General` (que agrupa Isla Dinámica, Permisos de PC y Actualizaciones), `Notificaciones y Juegos`, `Sonido y voz` y `Miku-Link`.

- **Opción A (Recomendada — Fusión Completa con Estética 100% Catálogo)**:
  Mantener la barra lateral con todas las funciones reales de tu Miku Desktop Suite (`General`, `Agentes`, `Modelos de IA`, `Claves de API`, `Servidores MCP`, `Notificaciones y Juegos`, `Sonido y voz`, `Miku-Link`, `Acerca de`), aplicando **exactamente** la arquitectura visual, banners `Particles` con `SECTION_HUES`, componentes (`IndicatorNav`, `SmoothSlider`, `HoldButton`, `GlideSelect`) y paleta monocroma + `#30d158` del catálogo a cada una, y **corrigiendo el bug de Agentes** para que siempre se vean sus funciones (Nombre, Color distintivo, Servidor MCP, Generador de Prompt con IA e Instrucciones/Rol).
- **Opción B**:
  Usar únicamente las 9 secciones literales del catálogo (`General`, `Sonido y voz`, `Apariencia`, `Notificaciones`, `Miku-Link`, `Privacidad`, `Almacenamiento`, `Atajos`, `Acerca de`) y reubicar `Agentes`, `Modelos de IA`, `Claves de API` y `Servidores MCP` dentro de alguna de ellas.

### 2. Colores en la Sección de Agentes y Banners
En tus mensajes anteriores mencionaste que ciertas partes debían conservar su color:
- **Banners de sección**: Usar el motor `Particles` completo de `miku-catalogo.html` con su `SECTION_HUES` (aurora multicapa, orbe radial y partículas con el matiz de cada sección: azul en General, violeta en Sonido/Agentes, verde en Miku-Link, ámbar en Notificaciones, etc.).
- **Agentes**: Conservar los colores distintivos del halo/ojos del agente (`PRESET` + selector de color) y el dibujo Canvas de Miku (`MK`), mientras que **todos los botones, selectores, pills de filtro de proveedores y controles de la interfaz** pasan al estilo monocromo neutro (`--ac: #f5f5f7`) + verde (`#30d158` solo para estados activos/conectados) del catálogo, eliminando por completo el azul `#3B9EFF` de botones y píldoras.
- ¿Confirmas este criterio de color?

### 3. Miku-Link: Integración en Configuración vs Ventana Separada (`miku_link.html`)
La nueva regla `miku-design-rule.md` (§8) especifica que **Miku-Link es una sección más dentro de Configuración (no una ventana aparte)**, con los 3 estados del catálogo (`Desconectado` QR/PIN, `Emparejando` con anillos concéntricos y `Conectado` con las 6 pestañas `Inicio`, `Mensajes`, `Llamadas`, `Fotos`, `Avisos`, `Apps`).
- **Propuesta**: Integrar Miku-Link al 100% dentro de la sección `Miku-Link` de Configuración y hacer que cualquier llamada antigua a abrir Miku-Link abra Configuración directamente en la sección `Miku-Link` (retirando la ventana suelta `miku_link.html`). ¿Estás de acuerdo?

### 4. Protocolo de Transporte Móvil para Miku-Link (§10.1 del Prompt)
Actualmente `server.py` + `miku_android` se comunican por **HTTP REST + WebSocket (`ws://127.0.0.1:8000/ws`)** con emparejamiento QR (`miku://pair`), bloqueo de PC, portapapeles bidireccional y transferencia de archivos bidireccional.
- **Pregunta**: Para las pestañas del diseño Phone Link que el cliente Android actual aún no transmite (`Mensajes SMS`, `Llamadas`, `Galería de Fotos en vivo`, `Espejo de pantalla` y `Apps`), ¿deseas que en esta iteración mostremos los estados honestos de verificación de capacidades en el escritorio (*"Requiere permiso en el teléfono / No disponible en el dispositivo"*) mientras conectamos al 100% las funciones reales existentes (QR, PIN de 6 dígitos, Estado del dispositivo, Portapapeles, Envío de archivos y Bloqueo de PC), o quieres que también ampliemos el código Kotlin de `miku_android` en la Fase 5?

### 5. Estructura Modular en `miku_ui/src/` (§10.3 del Prompt)
El frontend de `miku_ui` se sirve directamente como ES Modules / HTML estático hacia Tauri (`frontendDist: "../src"` en `tauri.conf.json`, sin bundler Webpack/Vite intermedio).
- **Propuesta**: Estructurar `miku_ui/src/` en módulos ES limpios (`styles/tokens.css`, `styles/base.css`, `styles/components.css`, `styles/miku-link.css`, `components/`, `sections/`, `services/settingsStore.js`, `services/mikuLinkService.js`) importados nativamente con `<script type="module">`, garantizando que Tauri funcione directamente sin romper el empaquetado de producción. ¿De acuerdo?

---

## Registro de Decisiones Confirmadas y Estado de Ejecución (Fases 0–7 Completadas)

1. **Secciones de Configuración (Confirmado — Opción A + 14 secciones completas)**:
   - Se unificaron las secciones del catálogo base (`General`, `Sonido y voz`, `Apariencia`, `Notificaciones`, `Miku-Link`, `Privacidad`, `Almacenamiento`, `Atajos`, `Acerca de`, `Zona de peligro`) junto con los motores de IA de Miku Desktop (`Agentes`, `Modelos de IA`, `Claves de API`, `Servidores MCP`), todas organizadas bajo los 3 grupos de barra lateral (`APLICACIÓN`, `CONECTIVIDAD`, `SISTEMA`) y encabezados de partículas `Particles` con su matiz `SECTION_HUES`.
   - Se corrigió el renderizado completo de la sección `Agentes` y el restablecimiento en `Zona de peligro` (`structuredClone(DEFAULT_AGENTS)`).
2. **Sistema de Color y Tokens (`miku-design-system`)**:
   - Eliminado el acento azul `#3B9EFF` de controles y botones. Todos los controles interactivos usan `--ac: #f5f5f7` (con `--ink: #0a0a0c`), reservando `--ok: #30d158` exclusivamente para confirmación/conectado y `--er: #ff453a` para peligro/error.
   - Los colores distintivos de agentes (`PRESET`) se conservan únicamente en el halo/avatar del personaje (`MK`), nunca en botones o píldoras de la interfaz.
3. **Integración de Miku-Link dentro de Configuración**:
   - Retirada la ventana independiente `miku_link.html` y su entrada `"link"` en `tauri.conf.json`.
   - Miku-Link vive al 100% dentro de la sección `Miku-Link` de `miku_settings.html` (`sections/mikuLinkSection.js` + `services/mikuLinkService.js`), implementando los 3 estados del catálogo (`Desconectado` QR/PIN con temporizador real de 120s, `Emparejando` con anillos concéntricos y `Conectado` con cabecera del dispositivo y las 6 pestañas `Inicio`, `Mensajes`, `Llamadas`, `Fotos`, `Avisos`, `Apps`).
   - El comando Tauri `open_link_window` abre o enfoca la ventana `settings` directamente en la sección `#link`.
4. **Arquitectura Modular ES + i18n en Español (`miku_ui/src/`)**:
   - `styles/tokens.css`, `styles/base.css`, `styles/components.css`, `styles/miku-link.css`.
   - `i18n/es.js` con diccionario completo en español (`sections.*`, `nav.*`, `mikuLink.*`, `common.*`, `empty.*`, `hold.*`, `app.*`) y función `window.MikuI18n.t(path, vars)`.
   - `components/` (`primitives.js`, `feedback.js`, `overlays.js`, `interactive.js`, `particlesHeader.js`, `qrPhone.js`, `index.js`).
   - Eliminadas todas las carpetas temporales `backup_*` y archivos obsoletos (`miku_link.html`, `miku_link.css`), y verificados cero colores hexadecimales hardcodeados fuera de `tokens.css`.

