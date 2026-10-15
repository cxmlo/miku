# Resumen de Herramientas (Tools) 🧰

El ecosistema está construido bajo un patrón fuertemente estructurado de herramientas (Functions / Tools). Todos los archivos que empiezan por `tools_*.py` y dependencias como `computer_use.py` exponen funciones que el LLM (Agente) puede invocar de forma autónoma.

## Módulos de Herramientas
La IA tiene acceso al mapeo directo de funciones (centralizado en `tools.py`) en los siguientes subgrupos:

1. **Interacción con Sistema Operativo y PC Local (`tools_os.py`, `computer_use.py`)**: 
   - Visión artificial global para clics (`hacer_clic_visual`).
   - Gestor de ventanas.
   - Atajos de teclado combinados (`ejecutar_macro_teclado`).
   👉 [[OS_and_Computer]]

2. **Programación y Ejecución de Código (`tools_code.py`)**:
   - `escribir_y_ejecutar_python()`: Sandbox local con timeout de 60s y bloqueos estrictos de seguridad para rutas del SO (`C:\Windows`, `System32`) y comandos peligrosos (`rm -rf`, `format`).

3. **Interacción Web, Multimedia y Spotify (`tools_web.py`, `tools_media.py`, `tools_spotify.py`)**: 
   - Navegación web autónoma (Playwright).
   - Búsqueda en internet invisible.
   - Control de Spotify (pausa, play, saltar).
   👉 [[Web_and_Media]]

4. **Hardware e IoT (`tools_hardware.py`)**:
   - Peticiones asíncronas no bloqueantes (`queue.Queue`) para ESP32, permitiendo que Miku controle servos y expresiones faciales en hardware físico de forma simultánea.

5. **Miku Core Tools (`tools_miku.py`)**: 
   Herramientas meta-cognitivas y de interacción propia de la asistente:
   - `hablar_al_usuario()`: Emite texto a voz.
   - `mostrar_widget_clima()`, `mostrar_widget_reloj()`, `mostrar_tarjeta_visual()`: Llama a los widgets en pantalla vía WebSocket HTTP REST hacia el Server.
   - `aprender_sobre_usuario()`, `guardar_enlace_memoria()`, `buscar_en_memoria()`: Modifican o leen el Knowledge Graph de ChromaDB.
   - `analizar_archivo_silencioso()`: Herramienta interna (usando `fitz` o `Vertex AI Vision`) para RAG automático al arrastrar archivos.
   - `enviar_archivo_a_celular()`, `enviar_imagen_a_chat()`: Transferencia asíncrona (Miku-Link) del escritorio al móvil.
   - `ejecutar_intent_android()`: Lanza un *Intent* nativo en el dispositivo Android vinculado para ejecutar funciones del SO (ej. abrir apps, temporizadores, alarmas).

6. **Protocolo de Servidores (MCP)**:
   - `instalar_skill_mcp()`: Orquesta la instalación en vivo de habilidades nuevas, conectándose asíncronamente con Anthropic MCP.
   - `abrir_panel_secretos_en_app()`: Si el servidor MCP necesita credenciales (como un cliente de Google, Github), envía una orden a la app móvil del usuario para desplegar un panel seguro y solicitar claves/tokens, almacenándolas en `.env`.

## Enlaces Relacionados
- 👉 Volver a [[Home]]
