## 🚀 Novedades Principales en v0.1.2
- **Servidor Core Autónomo Integrado (Tauri Sidecar)**: El Gateway Python (`server.py`) ahora está empaquetado directamente en un binario autónomo (`miku-core.exe`) dentro del instalador. Ya no es necesario tener Python instalado ni abrir terminales manualmente; Miku arranca y apaga su propio servidor en segundo plano de manera 100% invisible.
- **Sincronización en Vivo de Guardarropa**: La apariencia y accesorios de Miku (blanco) en la ventana de Ajustes y barra lateral ahora se sincronizan en tiempo real con las selecciones de la Isla Dinámica.
- **Apagado Limpio y Seguro**: Cierre automático de procesos en segundo plano y liberación inmediata del puerto 8000 al cerrar la aplicación o salir desde la bandeja del sistema (`/api/system/shutdown`).

## 🛠️ Mejoras y Optimización
- **Versión Consistente**: Actualización integral de números de versión a `v0.1.2` en todos los paneles, barra de título e indicadores de la interfaz.
- **Detección Inteligente de Entorno**: Capacidad en Rust (`lib.rs`) para detectar automáticamente ejecuciones locales en desarrollo (usando `venv`) o ejecuciones empaquetadas en producción (`miku-core.exe`).

## 🐛 Correcciones de Errores
- Corregido el problema donde la insignia `Core 8000` permanecía en rojo al abrir el `.exe` instalado por falta del servidor activo.
- Soporte para rutas en ejecutables congelados con PyInstaller mediante `sys._MEIPASS` en `miku_paths.py` y `audio_handler.py`.

---
**Instalación:** Descarga `Miku_Setup.exe` a continuación o usa el botón de "Buscar actualización" directamente desde **Ajustes → General** en tu app instalada.
