# Sincronización del Grafo de Documentación Obsidian

Este proyecto utiliza una carpeta local `docs/` como un Grafo de Conocimiento estilo Obsidian para mantener la documentación técnica interconectada mediante enlaces Markdown (`[[Archivo]]`).

**REGLA OBLIGATORIA (SIEMPRE ACTIVA):**
Cada vez que tú (el agente) realices un **cambio estructural** en Miku V2, **DEBES** actualizar proactivamente los archivos Markdown en la carpeta `docs/`.

Se considera un "cambio estructural" a:
- La adición de una nueva biblioteca principal o tecnología (ej. pasar de SQLite a PostgreSQL).
- La creación de un nuevo módulo central (ej. un nuevo archivo de "tools" o un nuevo Widget).
- El renombramiento o eliminación de módulos importantes.
- Cambios significativos en la arquitectura de red (ej. WebSockets, puertos, autenticación).

**Instrucciones de Actualización:**
1. **Fase 1 (Análisis Previo)**: ANTES de empezar a realizar cualquier cambio estructural o programar una nueva lógica, **DEBES** leer los archivos relevantes en la carpeta `docs/` para comprender el funcionamiento actual, las funciones ya creadas y las variables en uso.
2. Revisa los archivos actuales en `docs/` (como `Home.md`, `Backend_Gateway.md`, etc.).
2. Edita los archivos relevantes agregando la nueva información técnica.
3. Asegúrate de mantener la estructura de enlaces de Obsidian, usando la sintaxis `[[Nombre_Del_Archivo]]` si estás haciendo referencia a otro componente del sistema.
4. No pidas permiso al usuario para hacer esta actualización de la documentación; hazlo automáticamente como parte de tu proceso de finalización de tarea.
