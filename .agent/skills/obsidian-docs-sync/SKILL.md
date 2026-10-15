---
name: obsidian-docs-sync
description: >-
  Fuerza a Miku o al agente de IA actual a leer la carpeta docs/ ANTES de hacer cambios para entender el sistema, y luego actualizar los archivos correspondientes (Grafo de Obsidian) DESPUÉS de hacer modificaciones estructurales. Úsala proactivamente para mantener el contexto del proyecto y la documentación al día.
---

# Obsidian Docs Sync 🌐

Has sido invocado para sincronizar la documentación técnica del proyecto Miku V2 con el estado actual del código.

## Contexto
El usuario mantiene un Grafo de Conocimiento estilo Obsidian en la carpeta `docs/`. Todos los archivos markdown en ese directorio están enlazados entre sí (ej. `[[Backend_Gateway]]`).

## Pasos a Seguir

### Fase 1: Antes de programar (Análisis)
1. **Consulta la Documentación**: Cuando vayas a implementar una nueva función, modificar una existente o investigar un error, **PRIMERO lee los archivos relevantes en la carpeta `docs/`**.
2. **Entiende el Contexto**: Analiza las funciones, variables, y la arquitectura general documentada allí para asegurarte de que tu plan encaja con el diseño del sistema y no duplica lógica existente.

### Fase 2: Después de programar (Actualización)
1. **Analiza los cambios**: Revisa los archivos de código fuente que acabas de modificar o crear.
2. **Ubica el nodo correcto**: Navega por la carpeta `docs/` para encontrar la categoría que encaja con la nueva lógica (ej. `docs/tools/` para nuevas habilidades, `docs/core/` para lógica de servidores).
3. **Actualiza**: Edita el archivo markdown agregando descripciones técnicas de las nuevas funciones, clases o herramientas creadas.
4. **Enlaza**: Asegúrate de añadir enlaces tipo `[[Nombre_Del_Archivo]]` si las nuevas funciones se relacionan con otras partes del sistema.

Al finalizar, repórtale al usuario qué archivos de la carpeta `docs/` fueron analizados y actualizados.
