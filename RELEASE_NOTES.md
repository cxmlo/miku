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
