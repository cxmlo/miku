# Arquitectura General de Miku V2 🏰

Esta es la guía definitiva de la arquitectura de la aplicación Miku V2. El sistema está dividido en tres capas principales que interactúan en tiempo real: El **Cerebro (Backend)**, la **Interfaz Móvil (Frontend)** y la **Interfaz de Escritorio (UI/Widgets)**.

## 1. El Cerebro (Backend)
Escrito completamente en Python (versión 3.10+), reside en el núcleo del proyecto.
- **Gateway Central:** Orquestado por FastAPI (`server.py`), maneja WebSockets bidireccionales, sincronización de portapapeles, y expone APIs REST. 👉 [[Backend_Gateway]]
- **Cerebro LLM:** `brain.py` maneja la conexión con Google Cloud Vertex AI (Gemini 2.5 Flash/Pro). Utiliza un sistema de herramientas y function calling masivo. 👉 [[Main_and_Agents]]
- **Gestor de Prompts:** `prompt_manager.py` inyecta dinámicamente reglas de comportamiento basadas en el contexto del usuario usando *Enrutamiento por Palabras Clave*.
- **Memoria:** Una base de datos SQLite y memoria en JSON que retiene el contexto relacional. 👉 [[Memory_System]]
- **Voz y STT/TTS:** `audio_handler.py` procesa audio usando Groq (Whisper) para STT y Edge TTS para síntesis de voz, con hilos asíncronos para evitar interrupciones. 👉 [[Audio_and_Voice]]

## 2. Interfaz Móvil (Frontend React Native)
La aplicación compañera permite llevar a Miku en el bolsillo e interactuar con el PC de forma remota.
- **Conectividad:** Mantiene un WebSocket vivo con el PC, tolerando desconexiones y reconectándose automáticamente. 👉 [[Mobile_App]]
- **Portapapeles Bidireccional:** El texto copiado en el celular viaja al PC y viceversa.
- **UI Reactiva:** `AssistantOverlay.tsx` provee un panel modal (BottomSheet) donde Miku se manifiesta de forma interactiva (ondas de voz, estados "Pensando...").

## 3. Interfaz de Escritorio (PyQt6 Widgets)
Miku no es solo una IA invisible, tiene presencia física en el escritorio del usuario mediante widgets que flotan sobre las demás ventanas.
- **Gestión Visual:** `ui.py` inicializa una aplicación PyQt6 que controla diferentes paneles (Reloj, Clima, Panel Rápido). 👉 [[Widgets_and_UI]]
- **Herramientas de Visión:** Miku puede usar PyAutoGUI y `mss` para ver la pantalla, hacer clic y escribir como si fuera un humano controlando el mouse. 👉 [[Tools_Overview]]

## 4. Servidores MCP (Model Context Protocol)
El backend utiliza la especificación oficial MCP (`mcp_config.json`) para cargar dinámicamente capacidades adicionales a través del binario `mcp-server` de Anthropic y comunitarios (SQLite, Filesystem).

---
👉 **Volver al Menú Principal:** [[Home]]
👉 **Explorar Estructura de Archivos:** [[Project_Structure]]
