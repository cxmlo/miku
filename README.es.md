<div align="center">

<img src="assets/github_banner.png" width="128" alt="Miku GitHub" style="border-radius: 28px; box-shadow: 0 12px 32px rgba(0,0,0,0.35);">

# Miku Desktop

**Una compañera de escritorio inteligente que vive en una Isla Dinámica en tu pantalla — orquestando modelos de IA, controlando tu PC y monitoreando tus agentes de código.**

Supervisa las sesiones de tus agentes, aprueba permisos con un clic, escucha música en Spotify, arrastra archivos y chatea con tus modelos favoritos — todo desde una isla flotante no intrusiva.

[![Windows 10/11](https://img.shields.io/badge/Windows-10%2F11-0078D4?logo=windows&logoColor=white)](https://github.com/cxmlo/miku)
[![Tauri 2](https://img.shields.io/badge/Tauri-2-FFC131?logo=tauri&logoColor=black)](https://tauri.app)
[![Python 3.12+](https://img.shields.io/badge/Python-3.12%2B-3776AB?logo=python&logoColor=white)](https://python.org)
[![Licencia: MIT](https://img.shields.io/badge/licencia-MIT-green)](LICENSE)
[![Versión](https://img.shields.io/badge/Versi%C3%B3n-v0.1.7--Beta-cyan)](https://github.com/cxmlo/miku/releases)
[![Ko-fi](https://img.shields.io/badge/Ko--fi-Apoyar-ff5e5b?style=flat&logo=kofi&logoColor=white)](https://ko-fi.com/cxmlo)

**[English](README.md)** · **[Español](README.es.md)**

</div>

> [!NOTE]
> **Fase Beta**: Miku se encuentra en fase Beta pública activa hasta la versión 1.0.0. Tanto la aplicación de escritorio (Windows) como la aplicación compañera móvil (Android APK) están disponibles para pruebas.
>
> **Novedades en v0.1.7 Beta**: Motor de optimización radical de tokens (>95% de ahorro), cero herramientas inyectadas en saludos/charla casual, agrupamiento dinámico y tope de 2-5 herramientas por petición, protección de bucles de error, capturas visuales comprimidas a JPEG 45%, conmutador de Modo Bajo Costo en el System Tray y resolución de errores 409 en transferencias de Miku-Link.

---

## Por qué Miku

La mayoría de los asistentes de IA para escritorio son ventanas gigantescas que saturan tu pantalla o aplicaciones corporativas sin personalidad.
**Miku es la alternativa de código abierto centrada en el personaje.** Cada línea de código, animación e integración es libre para usar, personalizar, aprender y bifurcar.

Conoce a **Miku**: una suave nube brillante que asoma en la parte superior de tu pantalla, te saluda, sigue el puntero de tu ratón con mirada esférica, reacciona si le haces clic, detecta la música que suena en tu computadora y te notifica en cuanto tus agentes de programación necesitan tu atención.

---

## Características

- **Isla Dinámica en Windows**: Flota en el borde superior de tu pantalla. Pasa el cursor para verla asomar; haz clic para expandirla. Nunca roba el foco de tus ventanas activas.
- **Actualizaciones Automáticas Integradas**: Comprueba e instala actualizaciones oficiales firmadas criptográficamente con un solo clic desde Ajustes.
- **Chat Multagente con Contexto Aislado**: Comunícate con agentes especializados (GitHub, Programador, Investigador, etc.). Cada agente conserva su propio historial y buzón de respuestas sin mezclar contextos.
- **Menú Líquido Desplegable (`+`)**: Adjunta archivos, activa visión de pantalla o pega del portapapeles con animaciones elásticas de resorte.
- **Alertas Proactivas de Tiempo en Pantalla**: Configura avisos o pausas para aplicaciones como VS Code, Chrome, Spotify, Discord o juegos con sus iconos oficiales y umbrales en minutos.
- **Cerebro Multi-LLM con Rotación Automática**: Conecta Google Gemini (Flash / Pro), Groq (Llama 3.3 70B y Whisper), Claude 3.5 Sonnet u OpenAI GPT-4o. Puedes colocar múltiples claves de respaldo por proveedor (`clave1, clave2`) y Miku rotará automáticamente ante errores de límite de peticiones (Error 429).
- **Estudio de Creación de Agentes**: Diseña tus propios agentes directamente en Ajustes: asígnales un prompt de personalidad personalizado, herramientas, servidores MCP exclusivos y claves de API dedicadas.
- **Hooks en Vivo para Agentes de Código**: Monitorea **Claude Code**, **Cursor**, **Codex** o tus propios scripts en tiempo real:
  - ¿Pensando? Miku entra en estado `thinking`.
  - ¿Petición de permisos para ejecutar comandos o editar archivos? Aparece una tarjeta de aprobación directamente en la Isla con atajos de teclado (`Y`/`N`).
  - ¿Finalizado? Miku muestra una insignia de aviso y celebra con un gesto animado.
- **Spotify y Multimedia sin Configuración**: Detecta automáticamente canciones y artistas de Spotify, YouTube o navegadores sin necesidad de claves de desarrollador de Spotify. Pausa, reanuda o cambia de pista con arrastre de volumen fluido.
- **Arrastrar y Soltar Archivos**: Arrastra cualquier archivo o imagen sobre la Isla. Miku lo analiza de forma silenciosa, despliega una vista previa instantánea y responde tus preguntas sobre él.
- **Model Context Protocol (MCP)**: Conecta bases de datos SQLite, exploradores del sistema de archivos, Google Drive o memoria semántica de largo plazo.
- **App compañera Miku-Link para Android (en migración)**: La app nativa Kotlin en `miku_android/` conecta el celular con la instancia de Miku Desktop mediante el QR de Miku-Link. Busca que puedas continuar el chat con los mismos agentes, recibir sus notificaciones, sincronizar texto y archivos y confirmar acciones permitidas para el teléfono. Un servicio en primer plano conserva el enlace al cerrar la pantalla; **Desvincular** lo detiene. No es un backend independiente ni reemplaza Tauri: Miku Desktop debe estar ejecutándose y ambos dispositivos deben poder comunicarse por la red local. La app Expo anterior permanece en `miku_app/` como referencia y rollback durante la migración. Consulta la [guía de la app móvil](docs/frontend/Mobile_App.md).
- **Personalidades Intercambiables**:
  - **Calma**: Serena, madura, analítica y reflexiva.
  - **Casual**: Amigable, entusiasta, divertida y con tono gamer.
  - **Código**: Copiloto senior de programación, concisa, técnica y directa al grano.

---

## Cosas para Probar

| Acción | Lo que hace Miku |
| :--- | :--- |
| **Pasa el cursor por el borde superior** | Se asoma y te saluda |
| **Mueve el ratón por la pantalla** | Sus ojos siguen tu cursor en 3D en tiempo real |
| **Haz clic sobre Miku** | Se comprime, reacciona y muestra gestos animados |
| **Pon música en Spotify** | Muestra la portada, título, artista y controles de reproducción |
| **Arrastra un archivo sobre la Isla** | Se transforma en caja, absorbe el archivo y muestra su análisis |
| **Ejecuta Claude Code en la consola** | Notifica el uso de herramientas y solicita permisos en pantalla |

---

## Instalación

### Instalador Oficial para Windows (.exe — Recomendado)

1. Descarga **[Miku_Setup.exe](https://github.com/cxmlo/miku/releases/latest/download/Miku_Setup.exe)** desde la sección oficial de [Releases](https://github.com/cxmlo/miku/releases/latest).
2. Ejecuta el instalador y abre **Miku Desktop**.
3. Haz clic en **Ajustes** en la Isla Dinámica para ingresar tu primera API Key (por ejemplo, Gemini Flash gratuito desde Google AI Studio).

### Compilar desde el Código Fuente

**Requisitos**:
- Windows 10/11 x64
- [Python 3.12+](https://python.org)
- [Node.js 18+](https://nodejs.org)
- [Rust y Cargo](https://rustup.rs)

```powershell
# 1. Clonar el repositorio
git clone https://github.com/cxmlo/miku.git
cd miku

# 2. Configurar entorno de Python
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt

# 3. Configurar variables de entorno
cp .env.example .env
# Edita .env con tus claves de API

# 4. Iniciar la aplicación en modo desarrollo
cd miku_ui
npm install
npm run tauri dev
```

**Cliente móvil Android nativo** (requiere JDK 17 y Android SDK 36):

```powershell
cd miku_android
.\gradlew.bat testDebugUnitTest assembleDebug
```

---

## Creación e Integración de Agentes Personalizados

### Opción 1: Creador Visual No-Code (En la propia aplicación)
1. Abre la Isla y haz clic en **Ajustes → Agentes**.
2. Ve a la sección **Crear agente**:
   - Asigna un nombre (ej. *DevOps Bot*, *Escritor*, *Compañero Gamer*).
   - Escribe sus **Instrucciones / Prompt del sistema**.
   - Asigna un servidor **MCP** (Filesystem, SQLite, Google Drive, etc.).
   - (Opcional) Asigna una clave de API dedicada.
3. ¡Tu agente aparecerá de inmediato en el dock de la Isla listo para usar!

### Opción 2: Hooks de Terminal y CLI (Claude Code, Cursor, scripts)
Puedes conectar cualquier herramienta de terminal o script a Miku con el comando incluido:

```bash
# Notificar a Miku que tu agente está trabajando:
python scripts/miku_hook.py "Refactorizando módulo de autenticación..." --agent "MiAgente" --event PreToolUse

# Solicitar permiso al usuario desde la Isla:
python scripts/miku_hook.py "¿Autorizar borrado de carpeta temporal?" --event PermissionRequest

# Notificar finalización de tarea:
python scripts/miku_hook.py "¡Despliegue finalizado con éxito!" --event Stop
```

En **Claude Code**, solo agrega esto a tu archivo `~/.claude/settings.json`:
```json
{
  "hooks": {
    "UserPromptSubmit": "python \"C:\\ruta\\a\\miku\\scripts\\miku_hook.py\" \"$PROMPT\" -e UserPromptSubmit -a claude",
    "PreToolUse": "python \"C:\\ruta\\a\\miku\\scripts\\miku_hook.py\" \"$TOOL\" -e PreToolUse -a claude",
    "Stop": "python \"C:\\ruta\\a\\miku\\scripts\\miku_hook.py\" \"Listo\" -e Stop -a claude"
  }
}
```

---

## Cómo Funciona la Arquitectura

- **Frontend de la Isla**: Desarrollado con [Tauri 2](https://tauri.app) (Rust + Webview). El personaje se renderiza a 60 fps en un Canvas 2D con físicas de resortes, seguimiento suave de mirada y sin sobrecargar la CPU.
- **Gateway de Python (`server.py`)**: Un servicio FastAPI y WebSocket que gestiona el reconocimiento de voz, detección de palabra de activación offline, herramientas MCP y streaming de LLMs.
- **Orquestador Multi-LLM (`brain.py`)**: Enruta semánticamente las peticiones según la complejidad de la tarea (razonamiento, visión de pantalla, código) y gestiona el pool de claves con failover.
- **Privacidad Local**: Tus claves de API se almacenan localmente en `.env` y `settings_config.json`. Miku solo se conecta a los servicios que tú configures.

---

## Contribuciones

¡Las contribuciones, reportes de fallos e ideas de nuevas funciones son bienvenidas!
Si encuentras un error o deseas sugerir una mejora, por favor abre un Issue o envía un Pull Request.

---

## Apoyo y Comunidad

Si te gusta Miku y deseas apoyar el desarrollo continuo, el coste de pruebas de APIs y mantener el proyecto 100% libre, abierto y sin publicidad:

<div align="center">

<a href="https://ko-fi.com/cxmlo" target="_blank" rel="noopener noreferrer">
  <img src="assets/kofi_badge.png" width="220" alt="Apoyo en Ko-fi" style="border-radius: 20px; margin: 12px 0; box-shadow: 0 8px 24px rgba(255,94,91,0.25);">
</a>

<br>

[![Ko-fi](https://img.shields.io/badge/Ko--fi-Apoyar%20el%20proyecto-ff5e5b?style=for-the-badge&logo=kofi&logoColor=white)](https://ko-fi.com/cxmlo)

</div>

---

## Créditos

- Creado y mantenido por **[cxmlo](https://github.com/cxmlo)**.

---

## Licencia

Este proyecto es de código abierto bajo la **[Licencia MIT](LICENSE)**. Eres libre de usarlo, modificarlo, aprender de él y distribuirlo, siempre que se conserve el aviso de copyright original.
