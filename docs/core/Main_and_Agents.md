# Mente y Agentes (Main & Agents) 🤖

Este módulo orquesta la lógica de inteligencia artificial y la delegación de tareas. Define cómo "piensa" Miku.

## `main.py`
El ciclo vital del agente.
- Inicializa los servidores, la interfaz gráfica (`ui.py`), los administradores de audio y arranca el loop de eventos asíncronos.
- Es donde Miku toma consciencia y empieza a unir los eventos del Gateway (`server.py`) con la lógica del `AgentManager`.

## `agents.py` y `agents_config.json`
- **Configuración Multigente (`agents_config.json`)**:
  - Almacena de forma persistente los agentes disponibles (`antigravity`, `github`, `claude`, `vercel`), sus roles especializados, modelos asignados y paletas de color.
  - Sincronizado dinámicamente con el frontend mediante los endpoints `/api/agents` en `server.py` y `bridge.js`.
- **Clase `AgentManager`**:
  - `delegate(task, agent_id, agent_name)`: Permite a Miku (el orquestador principal) delegar tareas especializadas a sub-agentes en segundo plano con prompts de rol dedicados.
  - Emite eventos WebSocket `agent_busy` (activando el borde arcoíris y animación de trabajo en la UI) y `agent_reply` (notificando a Miku y completando el chat del sub-agente).
  - Maneja la llamada de Herramientas (Tool Calling) a través de [[Tools_Overview]].

## Herramientas de Delegación (`tools_miku.py`)
- `listar_agentes_disponibles`: Permite a Miku inspeccionar qué agentes tiene en su equipo y sus roles.
- `delegar_a_agente`: Delega una tarea técnica al agente correspondiente (`antigravity`, `github`).
- `abrir_chat_con_agente`: Cambia la interfaz visual al chat del agente solicitado cuando el usuario dice "llévame al chat con ese agente".

## `proactive_agent.py`
- **Clase `ProactiveAgent`**:
  - Miku no solo reacciona, también actúa. Este script maneja bucles paralelos que revisan el contexto actual (`get_active_window_title()`, portapapeles) y pueden detonar interacciones hacia el usuario sin que este haya hablado primero.

## `prompt_manager.py`
- El gestor de la "Personalidad" y "Reglas" de Miku.
- `load_personality()` / `save_personality()`: Lee y escribe `miku_personality.json`.
- `memorizar_leccion()`: Función vital donde Miku modifica su propio prompt en tiempo de ejecución. Si le dices "no me hables de usted, háblame de tú", Miku usa esta función para agregar una regla persistente en `miku_learned_rules.json`.
- `get_system_prompt()`: Ensambla dinámicamente la memoria, personalidad, reglas aprendidas, estado del equipo multigente y el contexto actual (hora, ventana activa) antes de pasarlo al LLM. Establece con claridad que Miku es la asistente blanca y orquestadora principal impulsada por Gemini.

## Enlaces Relacionados
- 👉 Volver a [[Home]]
- 👉 Entender la memoria: [[Memory_System]]
- 👉 Catálogo de herramientas: [[Tools_Overview]]
