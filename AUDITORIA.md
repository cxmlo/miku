# Auditoría Fase 0 — Rediseño de Configuración y Miku-Link

> **Alcance de la auditoría**: Solo lectura. No se ha modificado ningún archivo funcional del proyecto en esta fase.
> **Exclusiones estrictas**: La Isla Dinámica (`miku_ui/src/index.html`, `island.js`, `island.css`) y el motor de dibujo Canvas del personaje (`MK` / `MA`) quedan intactos y fuera del alcance de modificación.

---

## 1. Inventario de Pantallas, Secciones y Componentes Actuales

### 1.1 Ventanas Tauri (`miku_ui/src-tauri/tauri.conf.json` y `src/lib.rs`)
| Label | HTML | Dimensiones actuales | Estado de redimensionado | Observaciones |
|---|---|---|---|---|
| `main` | `index.html` | `800×580` (transparente, sin bordes, `alwaysOnTop`) | `resizable: false` | **Isla Dinámica — NO TOCAR.** |
| `settings` | `miku_settings.html` | `1080×780` (`decorations: false`, `transparent: true`) | `resizable: false` en `tauri.conf.json:33`, `lib.rs:311` y forzado en `settings.js:8` (`setResizable(false)`) | Contradice la nueva regla §8 (ventana libremente redimensionable con mínimo `720×520`). |
| `link` | `miku_link.html` | `960×620` (creada bajo demanda en `lib.rs:334`) | `resizable: false` | Ventana independiente heredada. La nueva regla §8 establece que **Miku-Link es una sección más dentro de Configuración**, no una ventana aparte. |

### 1.2 Secciones Actuales de Configuración (`miku_ui/src/settings.js`)
Actualmente `NAV_GROUPS` / `CATS` define **7 secciones visibles** (con 2 alias internos `V.island = V.general` y `V.permisos = V.general`):

1. **`general` (General — incluye Isla Dinámica y Permisos y PC)**:
   - **Tarjeta Isla Dinámica**: Switches (`autostart`, `always_on`, `focus`, `notif`), `GlideSelect` para `size` (`compact`/`normal`/`large`) y `pos` (`center`/`left`/`right`).
   - **Tarjeta Nivel de Permisos (Seguridad)**: Grid `.exec-mode-grid` con 3 modos (`safe`, `confirm`, `autonomous`) + switch `killswitch` (`F9`).
   - **Tarjeta Actualizaciones de Software**: Versión actual (`v0.1.8`), botón `Buscar Actualizaciones` (`check_update` / `install_update` en Tauri).
   - **Banner Ko-fi**: Tarjeta con colores hardcodeados `#ff5e5b`.
   - **Pie de sección**: `HoldButton` (`Restablecer valores de fábrica`).
2. **`agentes` (Agentes)**:
   - **Hero Card `.ach`**: Canvas `MK.live` (`86×86`) con accesorios, nombre, badge `Principal`/`Agente`, estado en la isla, botón `Invocar en la isla` / `Quitar de la isla`, y dock lateral `En la isla · X/3` (`.isl-dock`).
   - **Selector de agentes (`.apg`)**: Tarjetas `.apc` con mini-canvas `42×42` y botón `+ Crear`.
   - **Formulario del agente seleccionado**:
     - Input `Nombre`.
     - Selector `Color distintivo` (`PRESET` de 8 colores + `<input type="color">`).
     - `GlideSelect` para `Servidor MCP Asignado`.
     - Sub-tarjeta `Generador de Prompt con IA` (input + botón `#generate-prompt-btn` que llama a `POST /api/generate_prompt`).
     - `<textarea>` para `Instrucciones / Rol` (`#agent-prompt-textarea`).
     - `HoldButton` para `Quitar agente` (si no es Miku) y botón `+ Crear agente`.
     - **Bug crítico detectado**: En `settings.js:2447-2492`, cuando un agente está activo en la isla o se re-renderiza la vista, un error o retorno prematuro en el montaje de sub-tarjetas / estilos de contenedor recorta o deja ocultas las opciones debajo del Hero Card (como se aprecia en las capturas del usuario).
3. **`modelos` (Modelos de IA)**:
   - Banner de advertencia (con colores hardcodeados `#ffd166`) cuando no hay API keys activas.
   - Píldoras de filtro por proveedor (`all`, `google`, `groq`, `openai`, `deepseek`, `anthropic`, `ollama`) usando `.sec-btn.primary` (actualmente pintadas de azul `#3B9EFF`).
   - 4 selectores `GlideSelect` (`model_chat`, `model_pro`, `model_vision`, `model_stt`) alimentados desde `GET /api/models` y `GET /api/models/available`.
   - `HoldButton` (`Guardar modelos`) que envía `POST /api/models`.
4. **`keys` (Claves de API)**:
   - Lista de 12 proveedores (`GEMINI_API_KEY`, `GROQ_API_KEY`, `DEEPSEEK_API_KEY`, `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `ELEVENLABS_API_KEY`, `OPENROUTER_API_KEY`, `MISTRAL_API_KEY`, `COHERE_API_KEY`, `TOGETHER_API_KEY`, `FIREWORKS_API_KEY`, `PERPLEXITY_API_KEY`).
   - Cada fila tiene: etiqueta, píldora de estado (`Activa` / `Sin configurar`), `<input type="password|text">`, botón ojo (mostrar/ocultar) y `HoldButton` (`Guardar` / `Eliminar`) conectado a `GET/POST/DELETE /api/keys`.
5. **`mcp` (Servidores MCP)**:
   - Grid de 5 servidores recomendados (`RECOMMENDED_MCPS`: GitHub, Filesystem, Memory, Brave Search, SQLite) con instalación 1-clic.
   - Lista de servidores configurados (`GET/POST/DELETE /api/mcp`) con badge de tokens estimados (`~1,600 tokens`), switch de activación y `HoldButton` de borrado.
   - Formulario para añadir servidor MCP personalizado (`id`, `command`, `args`, `env`).
6. **`alertas` (Notificaciones y Juegos)**:
   - Selector `GlideSelect` de juegos/procesos activos (`GET /api/active_windows`) + botón `Examinar .exe` + botón `+ Añadir`.
   - Lista de apps monitoreadas (`GET/POST /api/settings/apps`) con `GlideSelect` de límite de tiempo (`15m` a `180m`), switch y botón eliminar.
   - Botón `Probar Alerta en Vivo` (`POST /api/settings/test_alert`).
7. **`voz` (Sonido y Voz)**:
   - `SmoothSlider` para `vol` (Volumen de Voz de Miku) y `fx` (Alertas y Efectos).
   - Switches para `voice` (Respuestas habladas), `barge_in` (Interrupción por voz) y `wake_paused` (Modo Privacidad / Pausar micrófono).
   - `GlideSelect` para `mic` (Dispositivo de entrada).
8. **`link` (Miku-Link)**:
   - **En `settings.js` (`V.link`)**: Solo muestra una tarjeta de estado simple + canvas QR (`#settings-qr-canvas`) y un botón que abre la ventana separada `miku_link.html`.
   - **En `miku_link.html` + `bridge.js`**: Ventana aparte con 2 columnas y 3 pestañas (`Resumen`, `Funciones`, `Vincular`), muy lejos del flujo completo tipo Microsoft Phone Link de `miku-catalogo.html` (estados `Desconectado` con QR/PIN, `Emparejando` con anillos concéntricos y `Conectado` con cabecera del dispositivo + 6 pestañas: `Inicio`, `Mensajes`, `Llamadas`, `Fotos`, `Avisos`, `Apps`).

### 1.3 Componentes UI Actuales (`miku_ui/src/miku_ui.js` y `settings.js`)
| Componente | Ubicación actual | Estado frente a `miku-catalogo.html` |
|---|---|---|
| `IndicatorNav` | `miku_ui.js:23-98` | Implementado, pero sus estilos están duplicados y pisados entre `miku_ui.css` y `settings.css`. |
| `SmoothSlider` | `miku_ui.js:104-199` | Usa `setTimeout` (línea 186) en lugar de solo `requestAnimationFrame` / transiciones CSS. |
| `HoldButton` | `miku_ui.js:206-291` y `settings.js:3454` | **Definido 3 veces en CSS** (`miku_ui.css:486`, `settings.css:756`, `settings.css:1581`) con estilos de onda líquida antiguos que entran en conflicto con el catálogo. |
| `GlideSelect` | `miku_ui.js:297-428` y `settings.js:152-248` | **Duplicado en dos archivos JS** con implementaciones distintas. |
| `Particles` (Banners) | `settings.js:1994-2120` (`GALAXY_PARTICLES`) | Versión reducida en blanco y negro (`rgba(255,255,255,...)`), sin aurora de 3 capas, sin orbe radial, sin estrellas fugaces ni `SECTION_HUES` por sección. |
| `Iconos SVG` | `settings.js:36-78` (`IC`) | Strings SVG inline mezclados con iconos con `fill="currentColor"` en lugar de trazos puros `stroke="currentColor"`. |

---

## 2. Estilos Duplicados, Inconsistentes y Valores Hardcodeados

### 2.1 Duplicación Masiva entre `miku_ui.css` (1,062 líneas) y `settings.css` (1,703 líneas)
`miku_settings.html` carga ambos archivos (`<link rel="stylesheet" href="miku_ui.css">` y `<link rel="stylesheet" href="settings.css">`), redefiniendo las mismas clases con reglas contradictorias:
- `.nav`, `.seg`, `.chips`, `.ind` (`miku_ui.css:86-210` vs `settings.css:620-715`).
- `.bt`, `.ib`, `.sec-btn` (`miku_ui.css:215-310` vs `settings.css:485-590`).
- `.cb`, `.rd`, `.sw` (`miku_ui.css:315-420` vs `settings.css:720-755`).
- `.sl` (`miku_ui.css:425-480` vs `settings.css:830-895`).
- `.hb` (`miku_ui.css:486-610` vs `settings.css:756-828` vs `settings.css:1581-1703`).
- `.sel`, `.gs-wrap`, `.gs-trig`, `.gs-menu`, `.gs-opt` (`miku_ui.css:615-760` vs `settings.css:896-995`).
- `.tag`, `.pill`, `.tx`, `.fld` (`miku_ui.css:765-920` vs `settings.css:996-1120`).

### 2.2 Causa Raíz de los Colores Azules (`#3B9EFF`) y Filtros Incorrectos
1. **`settings.js:103` (`theme()`)**: En cada llamada a `render()`, ejecuta `r.setProperty('--ac', '#3B9EFF')`, sobrescribiendo el token `--ac: #f5f5f7` de `settings.css` y forzando que botones `.primary`, bordes activos y estados seleccionados se vuelvan azules (`#3B9EFF`).
2. **`.agent/rules/design_system.md` (Regla antigua activa)**: Instruía explícitamente usar `--ac: #3B9EFF` (azul iOS), `--wa: #FF9F0A`, `--vz: #a88cff` y tarjetas `.gl` Liquid Glass, contradiciendo la estética monocroma con verde `#30d158` único de `miku-design-rule.md`.
3. **Banners monocromos**: En `settings.js:2017-2110`, se reemplazó el motor `Particles` con `SECTION_HUES` del catálogo por partículas blancas estáticas sin aurora ni orbe de color por sección.

### 2.3 Colores Hexadecimales, Tamaños y Sombras Hardcodeados
- **`settings.js`**:
  - Línea 103: `r.setProperty('--ac','#3B9EFF')`
  - Línea 106: `PRESET=['#f4a261','#e879f9','#6e7bf2','#ff6b6b','#3ee2ab','#3B9EFF','#ffd166','#a3e635']`
  - Línea 2170-2177: Banner Ko-fi con `#ff5e5b`, `rgba(255,94,91,0.14)`, `rgba(255,94,91,0.35)`.
  - Línea 2423-2439: `background:#14161f`, `background:#090a0f`, `background:#0c0d12`.
  - Línea 2504: Banner warning con `#ffd166`, `rgba(255,209,102,0.08)`, `rgba(255,209,102,0.25)`.
- **`settings.css`**:
  - Más de 45 colores hexadecimales fuera de `:root`: `#141414`, `#1c1e26`, `#d6d8de`, `#ff8f87`, `#3ce085`, `#3ee2ab`, `#0a0a0c`, `#18181b`, `#27272a`, `#111115`.
- **`miku_link.html` y `miku_link.css`**:
  - Colores inline `#30D158`, `#3B9EFF`, `#FF9F0A`, `#FF453A` y estilos hardcoded en `miku_link.html:19-45`.
- **Fuentes remotas (`Google Fonts CDN`)**:
  - `miku_settings.html:8`, `miku_link.html:10` y `miku_ui.css:3` cargan `Nunito` y `JetBrains Mono` desde `https://fonts.googleapis.com`, incumpliendo la regla de empaquetar las fuentes localmente.

---

## 3. Reglas, Skills y Workflows Existentes en el Proyecto

### 3.1 Archivos en `.agent/rules/`
| Ruta exacta | Resumen | Acción requerida en Fase 1 |
|---|---|---|
| `.agent/rules/design_system.md` | **Regla de diseño antigua ("iOS Liquid Glass Oscuro")**: Define `--ac: #3B9EFF`, `.gl` liquid glass, `.hb` con cresta de ola, etc. Contradice el nuevo diseño. | **Reemplazar / Eliminar** y sustituir por `.agent/rules/miku-design-system.md` (`miku-design-rule.md`). |
| `.agent/rules/action_verification_and_error_reporting.md` | Regla de veracidad técnica, diferenciación de estados (intentado/ejecutado/confirmado) y prohibición de falsos positivos. | **Conservar intacta** (no es regla de diseño). |
| `.agent/rules/memory_sync.md` | Regla de sincronización del grafo MCP `memory` (`Miku 1.0`) ante cambios estructurales. | **Conservar intacta**. |
| `.agent/rules/docs_sync.md` | Regla de actualización de `docs/` cuando cambia la arquitectura. | **Conservar intacta**. |
| `.agent/rules/obsidian_sync.md` | Regla de lectura y sincronización con el grafo documental en `docs/`. | **Conservar intacta**. |
| `.agent/rules/release_descriptions.md` | Formato para notas de lanzamiento de versiones. | **Conservar intacta**. |
| `.agent/rules/thorough_planning.md` | Directrices de planificación e investigación antes de implementar. | **Conservar intacta**. |

### 3.2 Archivos en `.agent/skills/` y Otros Archivos de Agentes
- **Skills en `.agent/skills/`** (ninguna define un sistema de diseño contradictorio; todas son de ingeniería general o empaquetado):
  - `ai-engineer`, `code-refactoring-refactor-clean`, `code-reviewer`, `error-detective`, `llm-application-dev-ai-assistant`, `miku-release-sync`, `obsidian-docs-sync`, `pragmatic-programmer`, `prompt-engineer`, `prompt-engineering-patterns`, `python-pro`, `python-testing-patterns`.
- **Otros archivos de contexto**:
  - `miku_app/AGENTS.md` y `miku_app/CLAUDE.md`: Notas de Expo SDK 54 para el proyecto móvil antiguo (`miku_app`).
  - `archivos para que uses/`: Carpeta con referencias previas (`miku-catalogo.html`, `miku-componentes.md`, `miku-componentes-v2.md`, `miku-boton-mantener.html`, `miku-iconos.html`, `miku-iconos.svg`).

---

## 4. Comandos Tauri, Eventos, Stores y Persistencia Actuales

### 4.1 Comandos Tauri (`miku_ui/src-tauri/src/lib.rs`)
- **Ventana Principal (`main` — Isla Dinámica)**:
  - `check_and_set_click_through`, `position_top_center`, `resize_window`, `get_cursor_position`, `hide_main_window`.
- **Ventana Configuración (`settings`)**:
  - `open_settings_window(app)` / `open_settings(app)`: Muestra/enfoca `settings`. **Nota**: En `lib.rs:311` tiene `.resizable(false)` que deberá pasarse a `.resizable(true)` con `.min_inner_size(720.0, 520.0)` en la Fase 4.
  - `close_settings(app)`: Oculta la ventana `settings` (`w.hide()`).
  - `minimize_settings(app)`: Minimiza `settings` (`w.minimize()`).
- **Ventana Miku-Link (`link`)**:
  - `open_link_window(app)` y `close_link(app)`.
- **Actualizador (`tauri-plugin-updater`)**:
  - `check_update(app)` -> devuelve `{ available, version, body }`.
  - `install_update(app)` -> descarga e instala el update.

### 4.2 Eventos, IPC y Endpoints Backend (`http://127.0.0.1:8000`)
- **Eventos Tauri / BroadcastChannel**:
  - `emit('miku', payload)` y `new BroadcastChannel('miku')` sincronizan en vivo `cfg` (volumen, tamaño de isla, posición, modo de permisos) y `agents` (agentes activos en la isla, color, outfit) entre Configuración y la Isla Dinámica.
- **Persistencia Local (`localStorage`)**:
  - `miku_cfg`: Objeto de configuración general, audio e isla.
  - `miku_agents`: Lista de agentes, asignación a la isla (`island: 0..3`), `color`, `outfit`, `prompt`, `mcp`.
  - `miku_cat`: Última categoría visitada en Configuración.
  - `miku_outfit`: Accesorios del personaje principal.
  - `miku_link_features`: Preferencias de funciones de Miku-Link.
- **API REST del Backend Python (`server.py`, puerto `8000`)**:
  - `GET / POST /api/settings/general` -> `settings_config.json`
  - `GET / POST / DELETE /api/keys` -> `.env` + validación en vivo (`key_validator.py`)
  - `GET / POST /api/models` y `GET /api/models/available` -> `models_config.json`
  - `GET / POST / DELETE /api/agents` y `POST /api/generate_prompt` -> `agents_config.json`
  - `GET / POST / DELETE /api/mcp` -> `mcp_config.json`
  - `GET / POST /api/settings/apps`, `GET /api/active_windows`, `POST /api/settings/test_alert` -> `settings_config.json`
  - `GET /api/link/status`, `GET /api/link/qr_data`, `POST /api/link/unpair`, `POST /api/link/upload_to_phone`, `POST /api/pair/init`, `POST /api/pair/confirm`, `POST /api/device/lock`, `POST /api/device/clipboard`, `POST /api/device/upload`.

---

## 5. Estado Actual de Miku-Link y Protocolo Móvil

### 5.1 Arquitectura Móvil Existente
El repositorio cuenta con:
1. **`miku_android/` (App Android nativa activa en Kotlin + Jetpack Compose)**:
   - `PairingLink.kt`: Escáner QR (`CameraX` + `MLKit`) que lee `miku://pair?s={session}&ip={host}`, llama a `POST /api/pair/confirm` y guarda `device_id`, `device_name` y `server_ip`.
   - `MikuClient.kt`: Cliente OkHttp + WebSocket (`/ws?device_id=...` con cabecera `X-Device-Id`) que soporta:
     - Chat con Miku y recepción de alertas/notificaciones del agente.
     - Envío de comandos rápidos: `lockPc()` (`POST /api/device/lock`), `sendClipboard()` (`POST /api/device/clipboard`), `uploadFile()` (`POST /api/device/upload`).
     - Recepción por WebSocket de eventos desde la PC: `clipboard_from_pc` (copia al portapapeles de Android) y `file_from_pc` (descarga archivo desde `/api/temp_media/{filename}`).
     - Reporte de telemetría básica en la conexión o mensajes (nombre del modelo Android).
2. **`miku_app/` (App Expo React Native heredada)**: Mantenida como referencia secundaria.

### 5.2 Brecha entre el Protocolo Actual y el Diseño Phone Link (`miku-catalogo.html`)
| Capacidad en la UI de Miku-Link (Catálogo) | Estado en Backend (`server.py`) y App Móvil (`miku_android`) |
|---|---|
| **Emparejamiento por QR (`miku://pair?...`)** | **Implementado y funcional** (`/api/link/qr_data`, `/api/pair/init`, `/api/pair/confirm`). |
| **Emparejamiento por código PIN de 6 dígitos** | **Falta endpoint en backend/móvil** (solo existe sesión por token QR; se puede añadir soporte de PIN de 6 dígitos en `/api/pair/init` y `/api/pair/confirm`). |
| **Estado de conexión, nombre del dispositivo e IP** | **Implementado** (`GET /api/link/status` + SQLite `miku_devices.db`). |
| **Telemetría (batería, red Wi-Fi/5G, almacenamiento, sonido/DND)** | **Parcial**: el móvil aún no envía el payload periódico de batería/red/almacenamiento por WebSocket. |
| **Portapapeles compartido y Envío de archivos PC ↔ Móvil** | **Implementado y funcional** (`/api/device/clipboard`, `/api/device/upload`, `/api/link/upload_to_phone`). |
| **Pestaña Inicio (Acciones rápidas: Sonar móvil, No molestar, Enviar archivo, Bloquear pantalla, Portapapeles, Espejo de pantalla + Actividad reciente)** | **Parcial**: Enviar archivo, Portapapeles y Bloquear PC existen; Sonar móvil, No molestar y Espejo de pantalla requieren comandos WS hacia `miku_android` o estado explícito "No disponible en el dispositivo". |
| **Pestaña Mensajes (SMS / Hilos y envío)** | **No implementado en `miku_android`** (requiere permisos de SMS/Notificaciones en Android y eventos WS). |
| **Pestaña Llamadas (Recientes y teclado numérico)** | **No implementado en `miku_android`** (requiere permisos de CallLog/Telephony en Android). |
| **Pestaña Fotos (Galería reciente del móvil y descarga)** | **Parcial**: existe subida de archivos del móvil al PC (`/api/device/upload`), pero no listado automático de miniaturas del carrete. |
| **Pestaña Avisos (Notificaciones del móvil en tiempo real)** | **Parcial**: requiere `NotificationListenerService` en Android reenviando al WS. |
| **Pestaña Apps (Lista de apps instaladas / abrir en espejo)** | **No implementado en `miku_android`**. |

> En cumplimiento de la Regla §9 (*"Si el transporte real con el móvil aún no soporta alguna capacidad, muestra un estado vacío honesto ('No disponible en el dispositivo' o 'Requiere permiso en el teléfono') conectado a una función real de verificación de capacidades — nunca datos inventados como si fueran reales"*), todas las pestañas de Miku-Link se construirán con su UI completa del catálogo y consultarán un objeto real de capacidades/datos del dispositivo conectado.

---

## 6. Estado Final Tras Ejecución de Fases 1 a 7 (Completado)

| Fase | Estado | Resumen de Resolución |
|---|---|---|
| **Fase 1 — Reglas y Gobernanza** | Completada | Regla `.agent/rules/miku-design-system.md` y skills `.agent/skills/miku-design-system/SKILL.md` / `.github/skills/miku-project-design/SKILL.md` activas como única ley visual para Configuración y Miku-Link. |
| **Fase 2 — Tokens, Base CSS e i18n** | Completada | Creados `styles/tokens.css`, `styles/base.css`, `styles/components.css`, `styles/miku-link.css` y diccionario completo `i18n/es.js` (`window.MikuI18n.t`). Empaquetadas fuentes locales `@font-face` (`Nunito` y `JetBrains Mono`) sin CDN externo. |
| **Fase 3 — Componentes Canónicos** | Completada | Implementados en `components/`: `IndicatorNav`, `SmoothSlider` (basado en `requestAnimationFrame`), `HoldButton` (`.hb` unificado con `.hb.sm` y `.dn.d`), `GlideSelect` (con portal flotante), `Particles` (aurora 3 capas + orbe + `SECTION_HUES`), `QR` / `Phone` y `toast` compatible con ambas firmas. |
| **Fase 4 — Rediseño de Configuración** | Completada | Ventana `settings` redimensionable (`1080×780`, mín `720×520`), 14 secciones conectadas a `MikuI18n`, encabezados `Particles` con `--h` dinámico y transición `MikuMotion.enter`, y bug `DEF_AG` corregido a `structuredClone(DEFAULT_AGENTS)`. |
| **Fase 5 — Miku-Link Integrado** | Completada | Integrado en `sections/mikuLinkSection.js` + `services/mikuLinkService.js` + endpoints reales `/api/link/*` en `server.py` (3 estados: `Desconectado` QR/PIN 120s, `Emparejando` y `Conectado` con 6 pestañas `Inicio`, `Mensajes`, `Llamadas`, `Fotos`, `Avisos`, `Apps`). |
| **Fase 6 — Limpieza y Cero Hex Hardcodeados** | Completada | Eliminados todos los colores hexadecimales fuera de `tokens.css` en `settings.css` y `miku_ui.css`, retirada la ventana duplicada `"link"` de `tauri.conf.json` y `lib.rs`, y eliminados `miku_link.css`, `miku_link.html` y carpetas `backup_*`. |
| **Fase 7 — Verificación y Documentación** | Completada | Suite de pruebas `pytest` (`test_island_sync.py` y `test_api_endpoints.py`) y documentación `docs/` sincronizada. Isla Dinámica (`index.html`, `island.js`, `island.css`) intacta al 100%. |

