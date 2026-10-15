# Mente y Agentes (Main & Agents) 🤖

Este módulo orquesta la lógica de inteligencia artificial y la delegación de tareas. Define cómo "piensa" Miku.

## `main.py`
El ciclo vital del agente.
- Inicializa los servidores, la interfaz gráfica (`ui.py`), los administradores de audio y arranca el loop de eventos asíncronos.
- Es donde Miku toma consciencia y empieza a unir los eventos del Gateway (`server.py`) con la lógica del `AgentManager`.

## `agents.py`
- **Clase `AgentManager`**:
  - `run_task()` / `delegate()`: Son las funciones responsables de invocar el LLM (LangChain / Gemini / Vertex AI) y pasarle el `system_prompt`. 
  - Maneja la llamada de Herramientas (Tool Calling o ReAct), analizando la petición del usuario y decidiendo qué herramienta ejecutar.

## `proactive_agent.py`
- **Clase `ProactiveAgent`**:
  - Miku no solo reacciona, también actúa. Este script maneja bucles paralelos que revisan el contexto actual (`get_active_window_title()`, portapapeles) y pueden detonar interacciones hacia el usuario sin que este haya hablado primero.

## `prompt_manager.py`
- El gestor de la "Personalidad" y "Reglas" de Miku.
- `load_personality()` / `save_personality()`: Lee y escribe `miku_personality.json`.
- `memorizar_leccion()`: Función vital donde Miku modifica su propio prompt en tiempo de ejecución. Si le dices "no me hables de usted, háblame de tú", Miku usa esta función para agregar una regla persistente en `miku_learned_rules.json`.
- `get_system_prompt()`: Ensambla dinámicamente la memoria, personalidad, reglas aprendidas y el contexto actual (hora, ventana activa) antes de pasarlo al LLM.

## Enlaces Relacionados
- 👉 Volver a [[Home]]
- 👉 Entender la memoria: [[Memory_System]]
