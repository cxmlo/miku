# Actualización de Documentación (Obsidian Docs Sync)

Este proyecto cuenta con un grafo de conocimiento en formato Markdown (Obsidian) ubicado en la carpeta `docs/`. Es fundamental que la documentación técnica siempre esté alineada con el código fuente.

**Regla de Obligatorio Cumplimiento:**
Cada vez que tú (el agente de IA) realices un **cambio estructural** en el proyecto, DEBES actualizar la carpeta `docs/`.

Se considera un "cambio estructural":
- Crear un nuevo archivo, módulo o clase importante.
- Modificar la firma de funciones críticas (ej. añadir nuevos parámetros en `server.py` o `brain.py`).
- Eliminar o depreciar lógica existente.
- Cambiar la arquitectura o forma en que se comunican dos componentes (ej. de REST a WebSockets).

**Procedimiento:**
1. **Fase 1 (Pre-Programación)**: ANTES de empezar a programar o investigar, DEBES leer los archivos relevantes en la carpeta `docs/` para comprender las variables, funciones y la arquitectura general.
2. **Fase 2 (Programación)**: Realiza el cambio estructural en el código.
3. Identifica qué parte del sistema modificaste (Frontend, Frontend móvil, Backend, Audio, Tools).
4. Localiza el archivo Markdown correspondiente en `docs/` (ej. `docs/core/Backend_Gateway.md`).
5. Usa la herramienta de edición para actualizar la descripción de la arquitectura, funciones y variables en el documento `.md`.
6. Asegúrate de mantener los enlaces cruzados de Obsidian intactos (formato `[[Nombre_Del_Documento]]`).
7. NO es necesario preguntar al usuario; hazlo automáticamente como parte de tus tareas de cierre.
