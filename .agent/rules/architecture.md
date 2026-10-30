---
description: Reglas de arquitectura modular, arranque instantáneo, aislamiento STA y Prefix-Caching determinista para Miku Companion & Runtime.
trigger: always_on
---

# Reglas de Arquitectura Modular de Miku (Google Standard)

1. **Prohibición de Archivos Monolíticos (`>600` líneas)**:
   - Ningún nuevo módulo de capacidades o plugin en `core/plugins/` debe superar las 600 líneas.
   - Cada dominio funcional (UI interactiva, Desktop CLI, SMTC Media, Vision Bridge, Browser, Google Ecosystem, Hooks IDE, Catálogo MCP) debe permanecer desacoplado en su propio plugin dentro de `core/plugins/`.

2. **Arranque Instantáneo (`<1.5s`) y Lazy Loading**:
   - Queda prohibido importar librerías pesadas (`playwright`, `onnxruntime`, `scipy`, `cv2`, `winsdk`) en el nivel superior de `main.py` o `server.py`.
   - Toda librería pesada debe cargarse bajo demanda mediante `core.engine.lazy_loader.lazy_import`.

3. **Bóveda Cifrada de Credenciales (`core/security/vault.py`)**:
   - Las claves de API (`GEMINI_API_KEY`, `DEEPSEEK_API_KEY`, `GROQ_API_KEY`, `OPENAI_API_KEY`, etc.) deben gestionarse a través de `SecretVault` (OS Keyring / Windows DPAPI).
   - Nunca devolver claves en texto plano en endpoints HTTP; usar siempre `get_masked_status()`.

4. **Los 3 Blindajes Críticos (10/10)**:
   - **Blindaje #1 (Windows SMTC en Hilo STA Dedicado)**: Las llamadas a `winsdk` / `pywinrt` para controles multimedia de Windows jamás deben ejecutarse directamente sobre el event loop asíncrono de FastAPI. Deben despacharse exclusivamente al hilo STA dedicado (`SMTCWorkerThread` con `CoInitializeEx(None, COINIT_APARTMENTTHREADED=0x2)` en `core/plugins/plugin_media.py`).
   - **Blindaje #2 (Supervivencia a Android Doze Mode)**: `MikuConnectionService` y los widgets 2x2 / 4x2 deben contar con `REQUEST_IGNORE_BATTERY_OPTIMIZATIONS`, `WAKE_LOCK` y el asistente `BiometricAuthHelper.requestIgnoreBatteryOptimizations(context)` para evitar desconexiones a los 15 minutos de apagar la pantalla.
   - **Blindaje #3 (Orden Determinista de Herramientas para Prefix-Caching)**: Todos los esquemas JSON de herramientas enviados a proveedores LLM (especialmente DeepSeek `deepseek-chat` y `deepseek-reasoner`) deben ordenarse alfabéticamente por `function.name` y serializarse canónicamente mediante `sort_tools_deterministically` (`core/plugins/__init__.py`) para garantizar un hash de prefijo 100% estable.

5. **Preservación de la Mascota Miku 2D Canvas**:
   - El motor procedural 2D Canvas (`<canvas id="mk">` en `miku_ui/src/island.js`) y sus estados (`idle`, `listening`, `thinking`, `talking`, `searching`, `working`, `error`), auras de color y atuendos son parte esencial de la identidad visual de Miku y deben mantenerse intactos.
