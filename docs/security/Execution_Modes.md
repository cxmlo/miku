# Modos de Ejecución y Sandbox (Estilo Antigravity) 🛡️

Miku V2 implementa una arquitectura de permisos granular inspirada en los entornos de ejecución de **Antigravity**. Este sistema permite al usuario controlar de forma dinámica los privilegios que Miku tiene sobre el sistema operativo, los archivos y la consola de comandos.

---

## 🎯 Niveles de Permisos Disponibles

| Modo | Identificador | Icono | Descripción y Límites |
| :--- | :--- | :---: | :--- |
| **Toda mi PC** | `full` | 🌐 | **Acceso Total (Unrestricted):** Miku tiene privilegios completos sobre todas las unidades de disco (`C:\`, `D:\`), la consola de Windows (CMD y PowerShell), ejecución de scripts Python y automatización de interfaz (Computer Use y atajos). |
| **Entorno Sandbox** | `sandbox` | 📦 | **Espacio de Trabajo Seguro (Workspace Only):** Miku trabaja confinada dentro de la carpeta del proyecto (`WORKSPACE_DIR`), la carpeta `%APPDATA%/Miku` y carpetas temporales seguras. Comandos y scripts se ejecutan estrictamente dentro del workspace y se bloquea el acceso a rutas protegidas (`C:\Windows`, `System32`, `Program Files`). |
| **Entorno Restringido** | `restricted` | 🔒 | **Modo de Solo Lectura y Consulta (Safe Mode):** Modo de máxima seguridad. Se bloquea la ejecución de comandos de consola (`ejecutar_comando_sistema`), scripts generados (`escribir_y_ejecutar_python`), borrado de archivos y clics desatendidos. Miku opera exclusivamente como asistente conversacional, análisis seguro y búsquedas web. |

---

## 🏗️ Arquitectura Técnica

### 1. Gestor Centralizado (`security_manager.py`)
Maneja la verificación en tiempo real de permisos:
- `get_execution_mode() -> str`: Obtiene el modo activo (`full`, `sandbox`, `restricted`).
- `set_execution_mode(mode: str) -> bool`: Cambia el modo y sincroniza la persistencia en `%APPDATA%/Miku/settings_config.json` y el workspace.
- `is_path_allowed(path, write=False) -> (bool, str)`: Valida accesos a rutas del sistema de archivos.
- `is_command_allowed(command) -> (bool, str, cwd)`: Evalúa si un comando de consola es seguro y asigna el directorio de trabajo forzado (`cwd`) en modo sandbox.
- `is_code_execution_allowed() -> (bool, str)`: Protege la ejecución de scripts temporales de Python.
- `is_gui_automation_allowed() -> (bool, str)`: Controla clics y escritura en pantalla.

### 2. Puntos de Entrada API REST (`server.py`)
- `GET /api/config/execution_mode`: Consulta el modo activo y el catálogo de modos con sus detalles.
- `POST /api/config/execution_mode`: Cambia el modo en caliente y notifica a la Dynamic Island vía WebSocket (`execution_mode_updated`).

### 3. Interfaz de Usuario (`miku_settings.html` & `bridge.js`)
El Centro de Control incorpora un selector interactivo con tarjetas en la pestaña **General**, permitiendo al usuario cambiar entre los 3 modos con un solo clic y retroalimentación inmediata.

### 4. Consciencia del Agente (`prompt_manager.py`)
El prompt maestro de Miku inyecta dinámicamente el nivel de seguridad activo, asegurando que el LLM comprenda sus límites actuales y guíe al usuario si necesita elevar privilegios.

---

## 🔗 Enlaces Relacionados
- 👉 [[Database_and_Security]]
- 👉 [[Arquitectura_General]]
- 👉 [[OS_and_Computer]]
- 👉 Volver a [[Home]]
