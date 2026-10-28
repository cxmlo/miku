## Novedades Principales en v0.2.0 (Beta)

### 1. Firma Criptográfica Oficial de Android en CI/CD (GitHub Actions)
- **Automatización de Keystore Release (SHA-256)**:
  - Configurado en Gradle (`miku_android/app/build.gradle.kts`) el bloque `signingConfigs.create("release")` que detecta y aplica variables de entorno (`KEYSTORE_PATH`, `KEYSTORE_PASSWORD`, `KEY_ALIAS`, `KEY_PASSWORD`) con fallback transparente a debug para pruebas locales.
  - Workflow de GitHub Actions (`.github/workflows/build-android.yml`) actualizado con el paso `Preparar Keystore de Firma Release` que decodifica de forma segura el certificado desde `secrets.KEYSTORE_BASE64` directamente a `$RUNNER_TEMP/miku-release.jks`.
  - Aislamiento de seguridad y destrucción automática: paso `Limpiar archivo de firma temporal` ejecutado con `if: always()` para asegurar que ningún archivo de firma permanezca en disco tras la compilación.
  - Inspección de integridad: paso automatizado con `keytool -printcert` que imprime la huella digital SHA-256 en los registros de GitHub Actions para verificación pública.
  - Scripts de generación en 1 clic:
    - **`scripts/generate_keystore.bat`**: Script interactivo para Windows que crea el almacén de claves RSA de 2048 bits con validez de 25 años y copia automáticamente la cadena Base64 al portapapeles del sistema.
    - **`scripts/generate_keystore.sh`**: Script homólogo para entornos Linux y macOS.
  - Guía oficial ilustrada paso a paso: **`docs/FIRMA_ANDROID_GITHUB.md`**.
  - Protección de secretos en Git: `.gitignore` blindado con exclusión obligatoria para `*.jks`, `*.keystore` y `*.p12`.

### 2. Cumplimiento Estricto con Google Play Protect
- **Eliminación de Heurísticas de Fraude Financiero**:
  - Removidos los permisos invasivos de lectura/envío directo de SMS (`READ_SMS`, `SEND_SMS`), registro de llamadas (`READ_CALL_LOG`), marcado directo (`CALL_PHONE`) y consulta global de paquetes (`QUERY_ALL_PACKAGES`) en `miku_android/app/src/main/AndroidManifest.xml` y `MainActivity.kt`.
  - Estos permisos activaban el bloqueo estricto sin botón de instalación en Android 13/14/15 (HyperOS / MIUI) para APKs instalados fuera de Google Play Store.
- **Canal Seguro de Notificaciones y Mensajes**:
  - Migración al servicio estándar del sistema Android **`MikuNotificationListenerService`** (`BIND_NOTIFICATION_LISTENER_SERVICE`).
  - Sincronización en tiempo real hacia Miku Desktop de mensajes entrantes (WhatsApp, Telegram, SMS), alertas de llamadas y notificaciones de aplicaciones mediante el permiso nativo y seguro de *Acceso a notificaciones*.

### 3. Miku-Link: Visor Centrado y Barra Rápida Phone Link
- **Visor Modal de Fotos Centrado y Funcional**:
  - Visor de fotos (`#ml-photo-ov`) con centrado absoluto en pantalla (`display: grid; place-items: center`).
  - Corregido el bloqueo de cierre: ahora cierra fluidamente al pulsar `Escape`, hacer clic en el botón `×` o hacer clic en el fondo exterior.
  - Eliminado el botón superfluo "Guardar en Imágenes", dejando como acción primaria y funcional el botón **"Abrir carpeta"** conectado al endpoint `/api/link/open-folder` para abrir el explorador de archivos de Windows.
- **Barra de Acciones Rápidas (Estilo Windows Phone Link)**:
  - 4 botones de acción rápida con iconos interactivos:
    - **No molestar**: Alterna el modo silencio/prioridad del móvil (`ACCESS_NOTIFICATION_POLICY`).
    - **Vibración**: Conmuta el perfil de vibración háptica.
    - **Audio / Música**: Control de reproducción multimedia y volumen.
    - **Hacer sonar**: Hace sonar el teléfono con vibración continua reactiva y animación pulsante sincronizada en la maqueta.
- **Maqueta Móvil Optimizada**:
  - Altura del contenedor adaptada a 136px para eliminar por completo el desplazamiento vertical (scroll) dentro de la pestaña Miku-Link.

### 4. Refinamientos de UI/UX y Corrección de Errores Visuales
- **Ajustes de Claves de API**:
  - Sustituidos los botones anchos de texto por botones compactos de iconos (`✓` guardar, `🗑` eliminar) y campos de entrada expandidos a 210px para evitar que el texto de las claves quede comprimido o recortado.
- **Añadir Servidor MCP**:
  - Distribución reorganizada en cuadrícula flexible que elimina el desbordamiento de botones y cortes de texto.
- **Selector de Juegos y Aplicaciones Activas**:
  - Corregido el solapamiento visual entre el selector desplegable `#gs-app-select` y el botón `+ Añadir app`.
  - Configurado con `flex: 1 1 0; min-width: 0; width: 100%;` para garantizar que nombres largos de ejecutables (ej. `Wallpaper Engine (wallpaper64.exe)`) se trunquen con puntos suspensivos o marquesina sin invadir botones adyacentes.
- **Botón de Confirmación Sostenida (Restablecer)**:
  - Corregido el bug donde el botón `.hb` renderizaba una cápsula blanca sólida sin texto legible.
  - Rediseñado con estilo dark glass translúcido (`rgba(255, 255, 255, 0.05)`), borde sutil, icono circular de recarga `↺` y barra de llenado progresivo al mantener presionado.
- **Isla Dinámica (Rendimiento y Clics Fantasma)**:
  - Eliminado el área transparente residual que bloqueaba clics en ventanas o pestañas inferiores cuando la isla estaba en estado compacto.
  - Aceleración por GPU activada (`translateZ(0)` y `will-change`) para eliminar micro-parpadeos y caídas de fotogramas en animaciones de apertura y cierre.

### 5. Actualización Global de Versión a v0.2.0
- Sincronización completa de la versión `0.2.0` (código de versión Android 5) en `package.json`, `tauri.conf.json`, `Cargo.toml`, `build.gradle.kts`, `miku_settings.html`, `settings.js`, `island.js` y `dev_server.js`.

---

## Novedades Principales en v0.1.7
- **Aislamiento Seguro en Demostración Web (Sandbox Mode)**:
  - Desconexión completa de WebSockets y peticiones REST hacia `127.0.0.1:8000` en la web pública para evitar que las pruebas de visitantes afecten al PC local.
  - Simulador de Configuración interactivo con datos mock completos y estables en navegador.
- **Reducción de Consumo de Tokens e Inferencia Eficiente**:
  - Filtrado dinámico de herramientas y reglas del sistema según contexto para reducir el coste de tokens por conversación al mínimo.
  - Sincronización en tiempo real del menú contextual de Windows con Miku-Link.
- **Sincronización Automática de Lanzamientos**:
  - Actualización continua de la landing page con la última versión directamente desde GitHub Releases.

---

## Novedades Principales en v0.1.6
- **Nueva Identidad Visual y Paquete de Iconos Oficiales**:
  - Iconos dedicados y personalizados para cada componente del sistema:
    - **Isla Dinámica / App Principal**: Nuevo icono representativo de Miku Desktop (`icon.ico`, `icon.png`, `32x32.png`, `128x128.png`).
    - **Ventana de Ajustes**: Icono distintivo en la barra superior y selector de ventanas (`icon_settings.png`).
    - **Ventana de Miku-Link**: Identidad visual dedicada para el enlace móvil (`icon_link.png`).
    - **Instalador de Windows (NSIS)**: Nuevas ilustraciones oficiales para el asistente de instalación (`installer_sidebar.bmp`, `installer_header.bmp` e `installer_icon.ico`).
- **Optimización Radical de Consumo de CPU (WebView2 en Reposo < 0.2%)**:
  - Eliminado el intervalo de 30ms que consultaba las APIs de Win32 para el seguimiento del cursor; reemplazado por eventos nativos del DOM con 0% de CPU.
  - Pausa automática de bucles de animación Canvas (estrellas y partículas) al minimizar la ventana o detener la música (`document.hidden`).
- **Puntos de Color Lumínicos en Ajustes**:
  - Reemplazo de textos planos ("Activado/Desactivado") por puntos de estado brillantes (verde esmeralda para activo/en línea, rojo para inactivo/pausado y ámbar para sincronización).
  - Switches deslizantes modernizados con indicación lumínica dinámica.
- **Soporte de la Comunidad · Ko-fi**:
  - Integración oficial del canal de apoyo en Ko-fi (`https://ko-fi.com/cxmlo`).
  - Tarjeta de apoyo en el panel de Ajustes y banner de la comunidad en el repositorio.

---

## Novedades Principales en v0.1.5
- **Modos de Ejecucion y Permisos (Estilo Antigravity)**:
  - Selector de 3 niveles en Ajustes: **Toda mi PC** (acceso total a consola y automatizaciones), **Sandbox** (confinamiento estricto a la carpeta del espacio de trabajo del proyecto), y **Restringido** (solo lectura segura; comandos de consola y clics bloqueados).
  - Los cambios aplican de forma inmediata sin reiniciar el servidor core.
- **Catalogo Completo y Resiliente de Modelos IA**:
  - Incorporacion nativa de modelos de **DeepSeek** (`deepseek-chat`, `deepseek-reasoner`, `deepseek-coder`).
  - Carga por defecto de modelos 100% reales aunque no se disponga de API keys configuradas previamente, eliminando errores de facturacion en frio.
  - Sincronizacion directa con litellm y fallback automatico de nombres.
- **Navegacion Inteligente de Ajustes en la Web**:
  - Corregido el bug donde hacer clic en "Configuracion" dentro del simulador web abria una ventana externa 404. Ahora detecta la pagina y realiza un scroll suave hacia el panel de configuracion integrado.
  - Disponibilidad de `miku_settings.html` independiente en la raiz del sitio web para accesos directos.
- **Compilacion Unificada CI/CD (Desktop + Mobile APK)**:
  - Generacion automatizada de APK firmado de Android listo para instalar mediante GitHub Actions (`build-android.yml`).
  - Flujo de Release unificado (`release.yml`) que publica simultaneamente el instalador de Windows (`Miku_Setup.exe`) y el APK movil (`miku-mobile.apk`).

---

## Novedades Principales en v0.1.4
- **Reproductor Multimedia Universal Windows (GSMTC)**: Soporte completo para cualquier reproductor activo en Windows (Chrome, Edge, YouTube, VLC, Spotify Web o App de escritorio) sin necesidad de tener Spotify instalado. Muestra carátula, título, artista y segundos transcurridos/totales 100% sincronizados en tiempo real mediante APIs nativas de Windows (`winsdk`).
- **Selector Jerárquico de Modelos de IA con Filtrado por Proveedor**: Menú organizado por pestañas de proveedores (Google Gemini, Groq, OpenAI, DeepSeek, Anthropic, Ollama / Local). Nueva categoría **Pro / Código** para modelos especializados de programación, además de Chat, Computer Use y STT. Cambio de modelo en caliente sin tener que reiniciar el servidor.
- **Proceso de Pensamiento y Herramientas Colapsables en el Chat**:
  - Visualización del razonamiento interno del agente colapsable (`Pensó durante Xs` / `Pensando...`).
  - Historial colapsable de comandos y herramientas ejecutadas (`Ejecutó X acciones v`).
  - Vistas previas en miniatura con número (`Captura #1`, `Captura #2`) de Computer Use directamente en el chat, con visualizador a pantalla completa al hacer clic (Zoom).
- **Detección Ultrarrápida de Juegos (<20ms) y Alertas de Tiempo de Uso**: Detección nativa estilo Discord que lista al instante los juegos y ventanas activas sin congelar el sistema. Alertas proactivas mediante notificación toast de Windows y aviso de la mascota en la Isla cuando se excede el límite de tiempo.
- **Conexión Instantánea de Servidores MCP**: Al pulsar "+ Instalar" en un servidor MCP recomendado o personalizado, se conecta y corre de inmediato en segundo plano con retroalimentación visual en vivo.

## Mejoras y Optimización
- **Arranque y Auto-Sincronización del Servidor Core**: Eliminada la necesidad de cerrar y volver a abrir la ventana de Ajustes. El frontend detecta automáticamente la señal de vida del servidor y recarga modelos, claves y agentes de forma transparente.
- **Aislamiento Estricto de Agentes (GitHub, Antigravity, Miku)**: Cada subagente mantiene su propio prompt de sistema, memoria y personalidad sin filtraciones del asistente principal.
- **Borde de Arcoíris Más Delgado**: El contorno animado de los agentes en ejecución se refinó a una línea ultradelgada de 1.1px con brillo sutil para un aspecto moderno y premium.

## Correcciones de Errores (Fixes)
- **Corrección de Desbordamiento de Texto en Selectores**: Eliminado el bug donde los nombres largos de modelos se desplazaban fuera del menú y tapaban el botón "Guardar modelos". Opciones con fondo opaco y z-index prioritario.
- **Animación de Pensando Atascada**: Corregido el bug donde Miku se quedaba en estado de pensamiento al cambiar entre agentes. Ahora el estado de la mascota se sincroniza inmediatamente con el agente seleccionado.
- **Mensajes de Error Amigables de APIs**: Sustitución de excepciones crudas por mensajes explicativos en español para códigos 400, 401, 402/429 (créditos o cuota insuficiente) y 404.

---
**Instalación:** Si ya tienes Miku instalada, ve a **Ajustes → General** y pulsa **Instalar v0.1.5**, o descarga y ejecuta el instalador `Miku_Setup.exe` abajo.
