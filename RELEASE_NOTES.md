## 🚀 Novedades Principales en v0.1.3
- **Auto-Actualizador Fluido y Proactivo**: La aplicación ahora verifica automáticamente si existe una nueva versión nada más abrir la ventana de Ajustes o hacer clic en la alerta de la Isla Dinámica, permitiendo actualizar e instalar en 1 clic sin tener que descargar archivos manualmente desde la web.
- **Servidor Core Autónomo Verificado (Puerto 8000)**: Corrección completa del empaquetado del sidecar `miku-core.exe`. Se resolvieron las dependencias dinámicas de ChromaDB (`chromadb.telemetry.product.posthog`) y los descriptores estándar I/O en Windows. Al iniciar Miku, el servidor arranca de forma 100% invisible y el indicador **Core 8000** se conecta en verde de inmediato.

## 🛠️ Mejoras y Optimización
- **Navegación Inteligente de Actualizaciones**: Al pulsar el badge de actualización en la Isla, ahora te lleva directamente a la pestaña **General** de Ajustes con la tarjeta de actualización visible y lista para instalar.
- **Sincronización de Versión**: Unificación de la versión `v0.1.3` en todos los archivos de configuración (`tauri.conf.json`, `Cargo.toml`, `package.json`, `miku_settings.html` y `bridge.js`).
- **Resiliencia de Base de Datos Vectorial**: Inicialización tolerante a fallos en `memory.py` con telemetría desactivada y ruta persistente en `AppData/Miku Desktop/db`.

## 🐛 Correcciones de Errores (Fixes)
- **Corrección en Menús Desplegables**: Solucionado el problema en todos los menús desplegables (`GlideSelect`) donde al hacer clic en una opción se seleccionaba erróneamente la de abajo debido a un desfase de cálculo en el índice.
- **Descriptores I/O en PyInstaller**: Configuración de consola nativa oculta (`CREATE_NO_WINDOW`) que previene fallos silenciosos de Uvicorn y Logging en Windows.
- **Importaciones Estáticas en Tools**: Sustitución de `__import__` dinámicos por importaciones estáticas para garantizar total compatibilidad con ejecutables congelados.

---
**Instalación:** Si ya tienes Miku instalada, ve a **Ajustes → General** y pulsa **Instalar v0.1.3**, o descarga directamente `Miku_Setup.exe` abajo.
