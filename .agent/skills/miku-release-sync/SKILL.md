---
name: miku-release-sync
description: >-
  Automatiza el ciclo completo de empaquetado y despliegue de Miku V2 tras cualquier cambio estructural o actualización: compilar el servidor Python ('miku-core.exe'), generar el instalador de escritorio de Windows ('Miku Desktop setup .exe'), compilar el APK de Android ('Miku Mobile'), actualizar la página web de GitHub Pages ('gh-pages') y sincronizar la documentación y el Grafo de Memoria. Úsala proactivamente en lanzamientos y sincronizaciones mayores.
---

# Miku Release & Deployment Sync 🚀

Esta habilidad estandariza y automatiza el flujo completo de empaquetado, compilación y despliegue de **Miku V2** cada vez que se implementen mejoras, nuevas funciones o cambios estructurales en el proyecto.

---

## Flujo de Trabajo Obligatorio

Cuando se complete una sesión de desarrollo o se prepare una nueva versión / release, debes ejecutar los siguientes 5 pasos en orden:

### 1. Compilación del Núcleo Backend (`miku-core.exe`)
El servidor FastAPI de Miku se distribuye como binario autónomo para que el usuario final no necesite tener Python instalado.
* **Comando:**
  ```powershell
  python scripts/build_sidecar.py
  ```
* **Destino:** Genera y actualiza `miku_ui/src-tauri/binaries/miku-core-x86_64-pc-windows-msvc/miku-core.exe`.

### 2. Compilación del Instalador de Windows (`.exe` Desktop)
Construye el ejecutable NSIS y MSI con Tauri 2, vinculando los íconos oficiales y el menú contextual de Windows ("Enviar a Mi teléfono"):
* **Comando:**
  ```powershell
  cd miku_ui
  npm run tauri build
  ```
* **Destino:** `miku_ui/src-tauri/target/release/bundle/nsis/Miku Desktop_{version}_x64-setup.exe`.

### 3. Compilación de la App Móvil Android (`Miku Mobile APK`)
Genera el paquete APK nativo de Kotlin/Compose con los íconos adaptativos y servicios en primer plano:
* **Comando:**
  ```powershell
  cd miku_android
  ./gradlew assembleRelease
  # O en su defecto para pruebas locales rápidas:
  ./gradlew assembleDebug
  ```
* **Destino:** `miku_android/app/build/outputs/apk/release/app-release-unsigned.apk` o `app-debug.apk`.

### 4. Sincronización de la Web Pública (`gh-pages`)
Actualiza los simuladores de la Isla y Ajustes con las últimas funciones de la aplicación y regenera el index de GitHub Pages:
* **Comando:**
  ```powershell
  python scratch/rebuild_gh_pages.py
  ```
* **Verificación:** Asegurar que la tarjeta de Ko-fi esté ubicada en la sección Hero directamente debajo de la descripción de texto de Miku, con adaptación móvil y navbar limpio.

### 5. Documentación y Memoria MCP
* **Obsidian Docs:** Actualizar `docs/` con cualquier nuevo endpoint, herramienta o configuración añadida.
* **Memory MCP:** Notificar y registrar cambios estructurales en el Grafo de Memoria oficial (`memory_sync.md`).
