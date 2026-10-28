# Guía de arquitectura y diseño de Miku

Este documento es la referencia compartida para desarrollar Miku, revisar cambios y dar contexto a Antigravity u otros agentes. Describe lo que existe, las decisiones vigentes y una ruta gradual para ampliar el proyecto sin romper las interfaces que ya funcionan.

## Decisiones vigentes

- **Escritorio oficial:** Tauri 2 en `miku_ui/`. No reemplazarlo por PyQt, PyWebView ni otro frontend.
- **Frontend Tauri canónico:** `miku_ui/src/`.
- **Compatibilidad del backend:** FastAPI todavía publica `/island` desde `miku_island/`. Esa carpeta se conserva como espejo compatible mientras existan consumidores; no editar ambas copias a mano.
- **Android:** `miku_android/` es el cliente nativo nuevo, aún en migración; compilación y pruebas JVM ya pasan, pero falta validación visual y de red en un dispositivo.
- **Rollback móvil:** `miku_app/` (Expo) se conserva hasta validar las funciones necesarias en Android. No borrarlo como parte de una tarea de ordenamiento.
- **Backend:** `server.py` es la puerta de entrada HTTP/WebSocket y coordina servicios Python; Tauri y Android son clientes distintos del mismo backend.
- **Legado:** `ui.py`, `widgets/` y `start_ui.py` no son rutas de desarrollo activo.

## Mapa de responsabilidades

| Área | Ruta | Responsabilidad |
| --- | --- | --- |
| Escritorio nativo | `miku_ui/src-tauri/` | Ventanas, integración con Windows, ciclo de vida y empaquetado del sidecar |
| Dynamic Island y ajustes | `miku_ui/src/` | Presentación web, canvas, animaciones y comunicación del cliente de escritorio |
| Espejo servido por FastAPI | `miku_island/` | Copia de compatibilidad de los puntos de entrada y recursos compartidos |
| Gateway y lógica | `server.py`, `brain.py`, `tools_*.py` y módulos de dominio | API, coordinación de agentes, herramientas y servicios |
| Aplicación Android | `miku_android/app/src/main/java/com/cxmlo/miku/android/` | Cliente nativo, interfaz Compose y conexión móvil |
| Expo anterior | `miku_app/` | Referencia de funciones y rollback temporal |
| Documentación | `docs/` | Arquitectura, contratos y notas de migración |

## Fuente canónica del Island

`miku_ui/src/` es la fuente que empaqueta Tauri. `server.py` también sirve el directorio `miku_island/` en `/island`; por eso el segundo directorio no es seguro de eliminar todavía. Los archivos compartidos se mantienen alineados mediante:

```powershell
# Verificar el espejo; no modifica archivos
python scripts/sync_island.py

# Actualizar el espejo desde la fuente canónica
python scripts/sync_island.py --sync
```

La prueba `tests/test_island_sync.py` detecta divergencias. Para cambios visuales del escritorio, editar `miku_ui/src/` primero, sincronizar y verificar. Los archivos exclusivos de `miku_island/` —como `island.js`, `miku.js`, `island.css` y `index.html.bak`— se consideran legado pendiente de inventario; no incorporarlos al frontend Tauri ni borrarlos sin comprobar consumidores.

## Arquitectura Android objetivo

La aplicación todavía está en una primera iteración. Al ampliarla, separar responsabilidades progresivamente; no mover todo en una sola refactorización:

```text
com.cxmlo.miku.android/
  data/
    local/       almacenamiento seguro y preferencias
    remote/      API HTTP/WebSocket
    repository/  coordinación de fuentes de datos
  domain/
    model/       modelos de negocio independientes de Compose
    repository/  contratos consumidos por la UI
    usecase/     operaciones con reglas de negocio, cuando aporten claridad
  connection/    servicio y ciclo de vida de conexión en segundo plano
  ui/
    theme/       paleta, tipografía y formas compartidas
    components/  componentes Compose reutilizables
    screens/     pantallas y estado presentado
    ...ViewModel.kt
```

Reglas para esta evolución:

1. `Activity` maneja integración del sistema y navegación de nivel superior; no debe convertirse en el contenedor de la lógica de cada pantalla.
2. Cada pantalla compleja recibe estado observable y callbacks desde un `ViewModel`; la UI Compose renderiza estado y emite intenciones.
3. El acceso remoto y local se expone mediante repositorios. No llamar al servidor directamente desde composables.
4. Crear clases para responsabilidades y límites reales, no por obligación. Evitar singletons globales nuevos y una capa de casos de uso que solo reenvíe parámetros.
5. Mantener el WebSocket y las credenciales fuera de la UI; conservar secretos en Android Keystore y no registrar tokens.
6. Añadir pruebas a los parsers, repositorios y cambios de estado antes de extraer más capas.

**Estado actual:** existen `data/MikuClient.kt`, `data/DeviceStore.kt`, `connection/MikuConnectionService.kt` y una interfaz concentrada en `MainActivity.kt`. El primer paso visual de esta guía ya se aplicó: la paleta Compose está en `ui/theme/Color.kt` y el tema común en `ui/theme/Theme.kt`. El resto de la separación MVVM/repositorio es trabajo futuro, no se debe dar por completado.

## Dirección visual

- **Configuración y Miku-Link (`miku-design-system`)**: Siguen estrictamente `.agent/rules/miku-design-system.md` y su fuente de verdad `miku-catalogo.html` (monocromo sobre negro `#000`/`#0e0f11`/`#17181b`, verde `#30d158` como único acento de confirmación/estado activo, rojo `#ff453a` solo para peligro/error, encabezados de partículas con `SECTION_HUES` por sección, movimiento con `--spring` y `--e`, blur de entrada/salida y cero valores hardcodeados).
- **Isla Dinámica (`index.html`)**: Conserva su lenguaje visual propio y su motor Canvas `MK` sin tocarse durante el rediseño de Configuración.

Android debe conservar esa identidad con patrones nativos de Compose: jerarquía tipográfica legible, targets táctiles adecuados, navegación del sistema, contraste accesible y estados de carga/error vacíos explícitos. Compartir roles y significado de tokens no obliga a copiar literalmente cada layout del escritorio.

En Android, usar `MikuPalette` y `MikuTheme` como punto de entrada para colores. Antes de introducir un color, tamaño o forma repetidos, decidir si corresponde a un token semántico. No crear estilos por pantalla para valores compartidos.

### Movimiento y estados

- Las animaciones deben corresponder a un estado o evento identificable, tener duración/fin definidos y no competir con acciones urgentes.
- Respetar el ciclo de vida: pausar trabajo visual fuera de pantalla cuando sea posible y evitar bucles permanentes sin necesidad.
- Ofrecer una alternativa comprensible sin movimiento ni sonido; el color nunca debe ser el único indicador.
- En web Canvas/SVG, evitar trabajo costoso por frame, cancelar `requestAnimationFrame` al destruir la vista y no animar simultáneamente varias copias de la misma entidad.
- En Compose, preferir animaciones Compose ligadas a estado y evitar cargar un motor externo si las primitivas nativas bastan.

## Extensión futura de assets y animaciones

El sistema actual ya dibuja el personaje y permite algunos accesorios y expresiones en ajustes, pero **no existe todavía un cargador general de packs instalado**. No presentar esta propuesta como funcionalidad ya disponible.

Estructura recomendada para assets incluidos con el escritorio:

```text
miku_ui/src/assets/packs/<pack-id>/
  manifest.json
  preview.png
  character/
  accessories/
  animations/
  sounds/
```

El manifiesto debería declarar como mínimo `schemaVersion`, `id`, `name`, `version`, compatibilidad de aplicación, créditos/licencia y referencias relativas a cada recurso. Las animaciones deben nombrar estados o eventos conocidos (por ejemplo `idle`, `thinking`, `working`, `error`) y declarar duración, repetición y alternativa estática.

Antes de implementar un cargador, acordar y validar un esquema versionado. El cargador futuro debe:

- aceptar solo formatos y propiedades declarados; no ejecutar JavaScript, HTML ni código incluido por un pack;
- impedir rutas absolutas, traversal (`..`) y recursos externos no autorizados;
- validar tamaño, MIME/decodificación, versión y referencias existentes;
- mantener un pack base integrado y volver a él ante un pack inválido;
- separar los recursos incluidos con la aplicación de los importados por el usuario, y permitir desactivar o retirar estos últimos;
- respetar licencia, autoría, accesibilidad y rendimiento.

No agregar dependencias de animación ni formatos complejos hasta que exista un primer caso de uso y una prueba de rendimiento en la ventana real.

## Flujo de trabajo para cambios

1. Identificar cuál cliente consume el archivo y comprobar si pertenece a escritorio, Android, backend o legado.
2. Leer el contrato existente antes de modificar API, eventos o formato de assets.
3. Mantener las fronteras de las áreas y preferir cambios aditivos y pequeños.
4. Si se modifica el frontend Tauri, editar `miku_ui/src/` y ejecutar la verificación/sincronización de `miku_island/`.
5. Si se modifica Android, ejecutar desde `miku_android/`:

   ```powershell
   .\gradlew.bat testDebugUnitTest assembleDebug
   ```

6. Si se modifica el backend o el espejo, ejecutar las pruebas Python pertinentes, incluyendo `tests/test_island_sync.py` para cambios web compartidos.
7. Actualizar la documentación y describir expresamente las validaciones bloqueadas. No declarar una función migrada solo porque exista código sin compilar o probar.
8. No retirar Expo ni las interfaces de respaldo hasta que se hayan comprobado sus consumidores y la paridad requerida.

## Estado del trabajo documentado

### Cambios ya presentes en este checkout

| Cambio | Ubicación | Estado |
| --- | --- | --- |
| Primer cliente Android nativo con pantallas de chat, control, eventos y ajustes | `miku_android/app/src/main/java/com/cxmlo/miku/android/MainActivity.kt` | Implementado y compilado como APK debug |
| Emparejamiento QR, cliente REST/WebSocket, credenciales cifradas y servicio de conexión | `miku_android/.../data/`, `miku_android/.../connection/` | Implementado; pendiente prueba extremo a extremo |
| Acceso del dispositivo emparejado mediante `X-Device-Id` con compatibilidad para clientes API key anteriores | `server.py` | Cubierto por pruebas de API |
| Solicitud explícita del permiso de cámara, rechazo de hosts loopback y soporte del enlace de pairing `miku://` | `miku_android/.../MainActivity.kt`, `data/PairingLink.kt`, `AndroidManifest.xml` | Implementado; requiere comprobar cámara y deep link en dispositivo |
| Estado de conexión del teléfono en el Island | `server.py`, `miku_ui/src/index.html` | Se basa en WebSocket activo, incluye reconexiones y desconexión del último socket |
| Animación original de entrada con partículas restaurada y un poco más densa; después aparece Miku en el lateral de una tarjeta de arranque más ancha que espera el WebSocket real | `miku_ui/src/index.html` | Implementado; requiere comprobación visual en una sesión Tauri |
| Sombra de la Isla y su halo de estado reducidos; sombra nativa de Tauri desactivada | `miku_ui/src/index.html`, `miku_ui/src-tauri/tauri.conf.json` | CSS actualizado; Tauri ya declara `shadow: false` |
| Envío directo de texto y archivos al teléfono conectado, con errores explícitos si no está conectado | `server.py`, `miku_ui/src/bridge.js`, `miku_ui/src/index.html` | Cubierto por pruebas de API; falta validación extremo a extremo en Android |
| Herramienta del agente para enviar desde escritorio un archivo adjunto al teléfono | `tools.py`, `tools_miku.py`, `server.py` | El agente puede invocarla desde PC; cubierto por pruebas del contrato API/herramienta |
| Avatar del agente en lateral propio dentro del chat; panel ampliado para conservar el espacio de conversación, con límite de altura y scroll para mensajes largos | `miku_ui/src/index.html` | Implementado; requiere comprobación visual con mensajes largos |
| Cerrar la ventana de escritorio la oculta en la bandeja; “Abrir Miku” la restaura y “Salir” detiene el Core | `miku_ui/src-tauri/src/lib.rs` | Implementado; `cargo check` bloqueado al procesar el binario sidecar por `Access denied`; falta prueba en sesión de escritorio |
| Servicio Android de dispositivo conectado, reconexión persistente y reinicio tras arranque con pairing guardado | `miku_android/.../connection/`, `AndroidManifest.xml` | Build Android y pruebas JVM pasan; falta prueba en teléfono |
| Posición inicial de la Dynamic Island | `miku_ui/src-tauri/tauri.conf.json`, `src-tauri/src/lib.rs` | La ventana se posiciona centrada arriba antes de mostrarse; compilación debug verificada |
| QR de pairing con generación criptográfica, mayor tamaño/resolución y error visible en lugar de QR falso | `miku_ui/src/bridge.js`, `miku_ui/src/index.html` | Implementado y sincronizado al espejo `/island`; falta validar lectura óptica en un dispositivo |
| Pruebas unitarias del enlace QR (incluye rechazo de localhost) | `miku_android/app/src/test/.../PairingLinkTest.kt` | Ejecutadas correctamente con las pruebas JVM de Android |
| Paleta y tema Compose centralizados | `miku_android/.../ui/theme/Color.kt`, `Theme.kt` | Añadido en este corte |
| Comprobación/sincronización del espejo `/island` desde el frontend Tauri canónico | `scripts/sync_island.py`, `tests/test_island_sync.py` | Añadido; la copia actual está sincronizada |
| Regla de diseño oficial (`miku-design-system`) y skill para agentes | `.agent/rules/miku-design-system.md`, `.agent/skills/miku-design-system/SKILL.md`, `.github/skills/miku-project-design/SKILL.md` | Actualizada y activa |
| Guía de arquitectura, diseño, migración y packs futuros | Este documento | Añadida y enlazada desde el grafo `docs/` |

### Límites y validación

- La migración móvil nativa está en marcha; Expo continúa disponible como rollback.
- La autenticación del nuevo cliente Android usa `X-Device-Id`; las credenciales se guardan cifradas con Android Keystore.
- La API y WebSocket siguen usando HTTP/WS en la red local del pairing; solo deben probarse en redes de confianza hasta diseñar TLS.
- Las pruebas enfocadas del backend, la herramienta de envío al móvil y el espejo `/island` pasan en este checkout (**21 passed**). Hay dos avisos deprecando `FastAPI.on_event`.
- El entorno local ya tiene JDK 17, Android SDK Platform 36 y Build Tools 36.0.0 configurados para el usuario.
- En esta validación, `.\gradlew.bat testDebugUnitTest assembleDebug` terminó correctamente con JDK 17 y Android SDK configurados en la sesión.
- `.\gradlew.bat testDebugUnitTest assembleDebug` en `miku_android/` termina correctamente; el APK se genera en `miku_android/app/build/outputs/apk/debug/app-debug.apk`.
- No había teléfono ni emulador conectado al ejecutar el build. El APK y las pruebas unitarias están validados; el flujo visual, pairing con QR y comunicación real todavía requieren dispositivo o emulador.
- El escáner ahora pide permiso explícito antes de abrir la cámara y la app acepta enlaces `miku://pair` lanzados desde otra app. El hardware de cámara aún no pudo validarse en un teléfono.
- Android informa si el escaneo se cancela o no detecta un código; el QR de escritorio se muestra a 144 px con un bitmap de mayor resolución para mejorar el enfoque/lectura.
- El Island refleja el estado de conexiones WebSocket móviles reales (no solo la confirmación del QR); falta comprobarlo en la sesión Tauri activa y en un teléfono conectado.
- Si el WebSocket móvil recibe HTTP 403, Android informa que el backend rechazó el dispositivo y detiene los reintentos automáticos. Se envía el ID tanto en la cabecera como en el parámetro de compatibilidad `device_id`.
- El backend difunde `user_message` con el agente y el identificador al iniciar un chat; la Isla reinicia su cronómetro de pensamiento por mensaje y no reutiliza el inicio de una conversación anterior.
- El envío TTS móvil ya usa el `tempfile` importado a nivel de módulo y registra explícitamente errores de generación/transmisión sin dejar una tarea asíncrona fallida sin recuperar.
- El texto enviado desde la Isla se entrega mediante `sync_clipboard` al Android conectado, mientras que el portapapeles del PC conserva su endpoint independiente. Los archivos adjuntos se pueden enviar al móvil desde la píldora del archivo; el teléfono recibe una solicitud para guardar el archivo.
- Al iniciar, la Isla reproduce la animación original de entrada con partículas y Miku; el burst conserva el mismo efecto Canvas, con un aumento moderado de puntos y trazos. Al terminar, la misma ventana, ahora algo más ancha, muestra a Miku en un lateral y una lista de inicio/recursos/WebSocket. Las primeras fases son indicadores visuales temporizados; el paso a conectado y la salida al overview dependen de la confirmación WebSocket real. La sombra exterior y el halo de estado se mantienen muy cortos y discretos; Tauri no añade sombra nativa. El chat sigue la composición compacta anterior: Miku se dibuja con el canvas animado principal usando el agente y atuendo activos, sobre una columna izquierda separada por un divisor; al pulsar su avatar se abre el agente con notificaciones pendientes. A la derecha se apilan la burbuja del usuario, el resumen de pensamiento, la respuesta y el compositor, sin un panel interior que separe el historial. Los mensajes extensos conservan scroll y límites de altura.
- Cerrar la ventana principal de Tauri la oculta, no detiene el sidecar; la bandeja ofrece “Abrir Miku” y “Salir”. En Android, el servicio foreground mantiene el WebSocket aunque se cierre la actividad, guarda el pairing cifrado y usa `START_STICKY`; el usuario debe desvincular desde la app para borrar las credenciales y parar la conexión explícitamente.
- La persistencia Android no puede superar “Forzar detención”, apagado del teléfono, restricciones del fabricante ni cambios de IP del PC. El receiver de arranque vuelve a iniciar el servicio solo si siguen guardadas credenciales válidas; verificarlo en un dispositivo real.
- Si el backend no puede registrar una sesión de QR o detectar una IP LAN, el Island ya no genera un código falso que termina en “sesión inválida”; muestra el problema en su lugar.
- AGP 8.13 muestra un aviso de que encuentra XML SDK versión 4 con soporte de lectura hasta la versión 3. No bloqueó la compilación; conviene actualizar AGP/Android tooling en una tarea separada y probada, no como cambio incidental.
- Todavía no se ha extraído MVVM/repositorios, no existe un cargador de asset packs, no se ha alcanzado paridad total con Expo y no se han retirado archivos legacy.
- El árbol de trabajo puede contener otros cambios locales de Tauri/Island y backend previos a esta guía. Revisarlos antes de agruparlos en un commit; no asumir que todos pertenecen a la migración Android.

---

## Subsistema Computer Use por Niveles, Memoria Espacial V2 y Modelos Resilientes

### 1. Computer Use por Niveles (Ahorro de Tokens y Verificación Real)

El subsistema de interacción de escritorio (`computer_use.py`, `action_result.py`) opera mediante una arquitectura de tres niveles deterministas, reduciendo drásticamente el consumo de tokens y evitando la ejecución de modelos de visión locales pesados en el PC:

```mermaid
flowchart TD
    A[Intención del Usuario / Brain] --> B{¿Acción Sensible?\npassword, 2FA, PIN, pagos, UAC}
    B -- Sí --> C[Detener inmediatamente\nActionStatus.REQUIRES_USER]
    B -- No --> D[Nivel 1: UI Automation Windows\n0 tokens API]
    D -- Encontrado y Clicked --> E[Confirmar cambio\nActionStatus.CONFIRMED]
    D -- No encontrado --> F[Nivel 2: Memoria Espacial V2\n0 tokens API]
    F -- Coordenadas en Caché --> G[Verificar Ventana y Clic\nActionStatus.CONFIRMED]
    F -- Cache Miss --> H[Nivel 3: Visión API Multimodal\nGemini 1.5 Flash / GPT-4o-mini]
    H -- Elemento Detectado --> I[Clic y Guardar en Memoria Espacial V2]
    H -- No detectado / Error --> J[ActionStatus.FAILED con diagnóstico]
```

#### Contrato de Verdad: `ActionResult` y `ActionStatus`
Definido en `action_result.py`:
- `CONFIRMED`: Acción ejecutada y verificada mediante cambios observables en pantalla, ventana activa o control UIA.
- `EXECUTED_UNVERIFIED`: Acción física emitida (clic/tecla) pero sin evidencia concreta de cambio. **Nunca se almacena en la Memoria Espacial** para evitar contaminación de coordenadas erróneas.
- `REQUIRES_USER`: Detección preventiva de credenciales maestras, códigos 2FA, contraseñas de cuentas, pasarelas de pago o elevación UAC. Miku se detiene de inmediato y solicita intervención manual.
- `FAILED`: Error técnico devuelto sin enmascarar ni simular éxito falso al usuario.

---

### 2. Memoria Espacial V2 (`spatial_memory.py` y `spatial_memory.json`)

La memoria espacial aprende las ubicaciones de elementos interactivos recurrentes para evitar llamadas de visión API continuas:
- **Esquema versionado `version: 2`**: Migración automática y transparente desde esquemas anteriores sin pérdida de datos aprendidos.
- **Eliminación del borrado destructivo**: Las discrepancias de título de ventana ya no borran irreversibles entradas de la memoria (`del cache[intent]` eliminado); ahora se tratan como *cache-misses* temporales.
- **Matching tolerante de ventanas**: Coincidencia por patrones y expresiones regulares (`extract_window_pattern`), permitiendo que cambios dinámicos (ej. canción en Spotify o pestaña en Chrome) sigan reutilizando las coordenadas de la aplicación.
- **Normalización de intenciones**: Limpieza semántica (`normalize_intent_key`) para unificar consultas equivalentes.
- **Estadísticas de ahorro**: Función `get_memory_stats()` que expone el total de elementos aprendidos y métricas de aciertos de caché.

---

### 3. Resiliencia de Proveedores y Catálogo de Modelos (`models_provider.py`)

- **Desacople limpio**: `identify_provider()` y resolución de modelos sin acoplamiento rígido de strings.
- **Clasificación de errores (`classify_api_error`)**:
  - `429 / 503` (*transient*): Se reintentan automáticamente con backoff y **rotación cíclica de API Keys** (`rotate_provider_key`) si hay múltiples claves configuradas separadas por comas en `.env`.
  - `401 / 403` (*auth*): Errores de credenciales inválidas no se disfrazan ni se reintentan ciegamente; se comunican al usuario de forma transparente.
  - `404` (*not_found*): Notificación explícita de modelo inexistente o sin acceso en la cuenta del usuario.
- **Catálogo explícito de capacidades**:
  Cada modelo declara sus capacidades reales (`vision`, `tools`, `native_computer_use`, `audio_stt`, `reasoning`), su origen (`verified`, `catalog`, `custom`) y su ventana de contexto (`context_window`).
- **Endpoints de conectividad y modelos personalizados**:
  - `POST /api/config/models/test`: Prueba la conectividad en vivo de cualquier modelo y devuelve `latency_ms` y mensaje de éxito o error real.
  - `POST /api/config/models/custom`: Valida la conectividad del modelo antes de registrarlo en `models_config.json`, garantizando que nunca se guarden modelos rotos o inaccesibles.
  - `POST /api/config/models/discover/{provider}`: Consulta en vivo las APIs oficiales del proveedor (Google, Groq, DeepSeek, OpenAI, Anthropic, OpenRouter, NVIDIA) y devuelve los modelos reales autorizados en la cuenta del usuario.
  - `POST /api/config/models/discover-all`: Consulta en tiempo real todos los proveedores configurados y refresca el catálogo general en caliente.

---

### 4. Ajustes de Usuario en Frontend Tauri (`miku_ui/src/`)

- **Diligenciamiento de Modelos en Tiempo Real y Clasificación por Categorías**:
  - Clasificación en 6 categorías funcionales: `Solo Chat & Texto`, `Fotos & Visión`, `Control de PC & Visión`, `Código & Razonamiento Pro`, `Creación de Imágenes` y `Voz / Audio (STT)`.
  - Barra de filtros interactivos en el frontend (`Todos`, `Solo Chat`, `Fotos / Visión`, `Control de PC`, `Código / Pro`, `Creación de Img`, `Voz / STT`) para encontrar al instante el modelo deseado.
  - Tarjetas de modelos enriquecidas con insignias de categoría, descripciones de utilidad en español y botones de acción contextuales (`Usar en Chat`, `Usar en CU`, `Usar en Pro`, `Usar en STT`).
  - Protección de protocolo LLM ante `REQUIRES_USER`: sellado de mensajes de herramientas y respuesta de asistente en el historial para prevenir errores HTTP 400 en OpenAI, DeepSeek y Google Gemini.
- **Badges de capacidades y origen**: Fichas técnicas dinámicas para cada uno de los 4 cerebros activos (`Chat`, `Pro / Código`, `Computer Use`, `STT`), indicando insignias visuales (`👁️ Visión`, `🛠️ Tools`, `🖥️ Computer Use`, `🎙️ Audio STT`, `🧠 Razonamiento`, `✓ Verificado`, `Catálogo`, `★ Personalizado`) y el tamaño de ventana de contexto.
- **Prueba de latencia con un clic**: Botón `[⚡ Probar]` por cada modelo en tiempo real; envía el identificador que espera el endpoint (`model_id`) y muestra la latencia devuelta por el backend o el mensaje real de error.
- **Formulario de Registro Custom**: Permite añadir modelos locales (Ollama/vLLM) o de APIs emergentes con prueba de verificación inmediata antes de guardar.
- **Sincronización Canónica**: Todo cambio frontend se realiza en `miku_ui/src/` y se verifica con `tests/test_island_sync.py`.

