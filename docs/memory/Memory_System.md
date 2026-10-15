# Sistema de Memoria 🧠💾

Miku posee un ecosistema de memoria fragmentado, diseñado para mimetizar la retención cognitiva humana. Todas estas funciones están integradas dinámicamente en el `system_prompt` generado por el [[Main_and_Agents]].

## `memory.py` (Memoria a Largo Plazo y Vectorial)
El Knowledge Graph persistente de la inteligencia artificial. Ahora cuenta con **ChromaDB** para realizar búsquedas semánticas (RAG) ultra rápidas.
- Posee rutinas de migración automática (`_migrate_old_data()`) desde los antiguos JSON (`miku_memory.json`) a colecciones vectoriales locales.
- `add_memory()`, `get_all_memories()`: Guarda fragmentos importantes del usuario con IDs generados por UUID.
- `guardar_enlace()`, `get_all_links()`: Almacena URLs valiosas y su contexto textual asociado en metadatos.
- `buscar_en_memoria()`: Recuperación semántica de datos pasados utilizando embedding distances, consultando sobre colecciones de "usuarios" o "enlaces" según la petición, lo que previene el desbordamiento de tokens de los LLMs.

## `memory_temporal.py` (Memoria de Trabajo)
Contexto conversacional efímero.
- Clase `MemoriaTemporal`: Mantiene el hilo de las últimas interacciones (`actualizar_estado`, `obtener_resumen_contexto`). Se resetea explícitamente al perder el contexto (`limpiar_estado`) o al dormir.

## `spatial_memory.py` (Memoria Espacial)
Vital para la automatización de la UI (Visión Artificial).
- `save_coordinates()`, `get_cached_coordinates()`: Si Miku aprende (mediante análisis de LLM Vision) que "El botón de Enviar" en cierta aplicación está en las coordenadas (X,Y), lo guarda en caché (`spatial_memory.json`) para no tener que usar el LLM la próxima vez que necesite hacer clic ahí, ahorrando cientos de milisegundos y reduciendo el costo de llamadas API.
- Usa `get_active_window_rect()` para escalar y ajustar coordenadas independientemente de si la ventana de destino fue redimensionada o movida.

## `contacts_memory.py` (Memoria Social)
- `_load_contacts()`, `_save_contacts()`: Gestiona localmente `miku_contacts.json`.
- `asociar_contacto_app()`, `obtener_contactos_str()`: Conoce a los amigos del usuario y sabe por qué aplicación (WhatsApp, Discord) debe enviar el mensaje.

## Enlaces Relacionados
- 👉 Volver a [[Home]]
