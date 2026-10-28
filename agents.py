import os
import json
import threading
import logging
import requests

logger = logging.getLogger("Agentes")
from miku_paths import get_agents_config_path
AGENTS_CONFIG_FILE = get_agents_config_path()

DEFAULT_AGENTS = [
    {
        "id": "github",
        "name": "GitHub",
        "c": "#39D353",
        "role": "Control de versiones, commits, ramas, pull requests y estado de repositorios",
        "model": "google/gemini-1.5-flash",
        "hooks": 1,
        "active": 1,
        "isl": 1,
        "outfit": "shades"
    },
    {
        "id": "antigravity",
        "name": "Antigravity",
        "c": "#00D2FF",
        "role": "Desarrollo frontend, interfaz reactiva, animación y diseño UI/UX",
        "model": "google/gemini-1.5-pro",
        "hooks": 1,
        "active": 1,
        "isl": 2,
        "outfit": "crown"
    }
]

def load_agents_config() -> list:
    if not os.path.exists(AGENTS_CONFIG_FILE):
        save_agents_config(DEFAULT_AGENTS)
        return DEFAULT_AGENTS
    try:
        with open(AGENTS_CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list) and len(data) > 0:
                return data
            return DEFAULT_AGENTS
    except Exception as e:
        logger.error(f"Error cargando {AGENTS_CONFIG_FILE}: {e}")
        return DEFAULT_AGENTS

def save_agents_config(agents: list) -> bool:
    try:
        with open(AGENTS_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(agents, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error guardando {AGENTS_CONFIG_FILE}: {e}")
        return False

def broadcast_ui_command(payload: dict):
    """Envía un comando al WebSocket de la UI de Miku."""
    try:
        requests.post(
            "http://127.0.0.1:8000/broadcast_command",
            json={"payload": payload},
            headers={"x-api-key": "miku_secure_key_2026"},
            timeout=1.5
        )
    except Exception:
        pass

class AgentManager:
    def __init__(self):
        self.callback = None
        self.agent_counter = 0
        self.last_result = ""
        self.active_agents = set() # ids o nombres de agentes activos
        self.agent_messages = {} # Buzón para mensajes entrantes por agente
        self.agent_statuses = {} # agent_id -> {"busy": bool, "task": str, "name": str}

    def get_agent_info(self, ref: str) -> dict:
        """Busca un agente por ID o nombre."""
        ref_norm = (ref or "").strip().lower()
        agents = load_agents_config()
        # Coincidencia exacta de ID
        for a in agents:
            if a.get("id", "").lower() == ref_norm:
                return a
        # Coincidencia exacta o parcial de Nombre
        for a in agents:
            if ref_norm in a.get("name", "").lower() or a.get("name", "").lower() in ref_norm:
                return a
        # Fallback antigravity
        return agents[0] if agents else DEFAULT_AGENTS[0]

    def send_message(self, message: str, agent_id: str = None) -> str:
        if not self.active_agents:
            return "No hay ningún agente activo en segundo plano."
        targets = [agent_id] if agent_id and agent_id in self.active_agents else list(self.active_agents)
        for aid in targets:
            if aid not in self.agent_messages:
                self.agent_messages[aid] = []
            self.agent_messages[aid].append(message)
        return f"Mensaje entregado al agente ({', '.join(targets)}). Modificará su comportamiento."

    def cancel_all(self):
        if not self.active_agents:
            return "No hay agentes para cancelar."
        for aid in list(self.active_agents):
            if aid not in self.agent_messages:
                self.agent_messages[aid] = []
            self.agent_messages[aid].append("[CANCELAR_TAREA]")
            broadcast_ui_command({"type": "agent_busy", "agent_id": aid, "busy": False})
        return "Se solicitó cancelación a todos los agentes."

    def is_agent_busy(self, agent_id: str) -> bool:
        return agent_id in self.active_agents

    def delegate(self, task: str, agent_id: str = "antigravity", agent_name: str = None) -> str:
        info = self.get_agent_info(agent_id)
        final_id = info.get("id", agent_id or "antigravity")
        final_name = agent_name or info.get("name", final_id.capitalize())
        role_desc = info.get("role", "Especialista técnico")
        model_name = info.get("model", "google/gemini-1.5-flash")

        self.agent_counter += 1
        self.active_agents.add(final_id)
        self.agent_messages[final_id] = []
        self.agent_statuses[final_id] = {"busy": True, "task": task, "name": final_name}

        # Notificar a la UI inmediatamente para que el avatar muestre animación working y borde arcoíris
        broadcast_ui_command({
            "type": "agent_busy",
            "agent_id": final_id,
            "agent_name": final_name,
            "busy": True,
            "task": task
        })
        broadcast_ui_command({
            "type": "ui_command",
            "action": "status_update",
            "text": f"{final_name} trabajando...",
            "agent_id": final_id
        })

        def run_task():
            logger.info(f"Iniciando tarea en paralelo para {final_name} ({final_id}): '{task}'...")
            try:
                # Usar el proveedor configurado en Ajustes (no solo Vertex AI)
                gemini_client = None
                try:
                    from models_provider import get_client_and_model
                    gemini_client, resolved_model, _prov = get_client_and_model(category="pro")
                    if not gemini_client:
                        gemini_client, resolved_model, _prov = get_client_and_model(category="chat")
                    if gemini_client and resolved_model:
                        model_name_resolved = resolved_model
                    else:
                        model_name_resolved = None
                except Exception as prov_err:
                    logger.warning(f"No se pudo resolver proveedor para agente {final_name}: {prov_err}")
                    model_name_resolved = None
                if not gemini_client:
                    from brain import get_vertex_client
                    gemini_client = get_vertex_client()
                    model_name_resolved = None
                if not gemini_client:
                    raise Exception("No hay ningún proveedor de IA disponible. Configura una API Key en Ajustes.")
                effective_model = model_name_resolved or model_name

                from tools import tools_schema, available_functions
                herramientas_prohibidas = [
                    "delegar_tarea", "delegar_a_agente", "hacer_clic_visual",
                    "escribir_en_elemento", "escanear_ventana_activa", "hablar_al_usuario"
                ]
                agent_tools_schema = [t for t in tools_schema if t["function"]["name"] not in herramientas_prohibidas]
                agent_available_functions = {k: v for k, v in available_functions.items() if k not in herramientas_prohibidas}

                system_prompt = (
                    f"Eres {final_name}, un agente técnico altamente capacitado del ecosistema de Miku.\n"
                    f"Tu rol y especialidad: {role_desc}.\n"
                    "Tienes herramientas técnicas a tu disposición (ejecutar comandos del sistema, buscar en internet, inspeccionar archivos).\n"
                    "No tienes acceso a controlar el ratón directamente. Tu único objetivo es resolver la tarea asignada y retornar el reporte final concreto y bien estructurado.\n"
                    "IMPORTANTE: NO devuelvas un simple 'he completado la tarea', DEBES devolver EL RESULTADO COMPLETO Y EXPLICACIÓN DE LO REALIZADO."
                )

                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": task}
                ]

                import time
                result = ""
                for step in range(30):
                    if self.agent_messages.get(final_id):
                        cancelado = False
                        while self.agent_messages[final_id]:
                            new_msg = self.agent_messages[final_id].pop(0)
                            if new_msg == "[CANCELAR_TAREA]":
                                cancelado = True
                                break
                            logger.info(f"Agente {final_name} recibió interrupción: {new_msg}")
                            messages.append({
                                "role": "user",
                                "content": f"[INTERRUPCIÓN / CORRECCIÓN DEL USUARIO]: {new_msg}. Adapta tu plan inmediatamente."
                            })
                        if cancelado:
                            result = "Tarea abortada manualmente por el usuario."
                            break

                    time.sleep(1.5)
                    response = gemini_client.chat.completions.create(
                        messages=messages,
                        model=effective_model,
                        temperature=0.3,
                        max_tokens=3000,
                        tools=agent_tools_schema
                    )

                    response_message = response.choices[0].message
                    if response_message.content is None:
                        response_message.content = ""

                    tool_calls = response_message.tool_calls
                    if not tool_calls:
                        result = response_message.content
                        break

                    messages.append(response_message)
                    for tool_call in tool_calls:
                        func_name = tool_call.function.name
                        func_to_call = agent_available_functions.get(func_name)
                        if func_to_call:
                            try:
                                args_raw = tool_call.function.arguments
                                func_args = json.loads(args_raw) if args_raw else {}
                            except Exception:
                                func_args = {}
                            try:
                                func_response = func_to_call(**func_args)
                            except Exception as e:
                                func_response = str(e)
                            messages.append({
                                "tool_call_id": tool_call.id,
                                "role": "tool",
                                "name": func_name,
                                "content": str(func_response)
                            })
                        else:
                            messages.append({
                                "tool_call_id": tool_call.id,
                                "role": "tool",
                                "name": func_name,
                                "content": "Función no disponible."
                            })
                else:
                    result = "Me detuve por seguridad después de 30 acciones."

                logger.info(f"Agente {final_name} finalizó tarea con éxito.")
                self.last_result = result
                self.agent_statuses[final_id] = {"busy": False, "task": "", "name": final_name}

                # 1. Enviar respuesta directamente al chat del agente en la UI
                broadcast_ui_command({
                    "type": "agent_reply",
                    "agent_id": final_id,
                    "agent_name": final_name,
                    "text": result
                })
                # 2. Desactivar estado busy en la UI
                broadcast_ui_command({
                    "type": "agent_busy",
                    "agent_id": final_id,
                    "agent_name": final_name,
                    "busy": False
                })

                # 3. Guardar en historial diario
                try:
                    from server import append_to_chat_history
                    append_to_chat_history({
                        "type": "agent_reply",
                        "sender": final_id,
                        "agent_id": final_id,
                        "agent_name": final_name,
                        "text": result,
                        "timestamp": time.time()
                    })
                except Exception:
                    pass

                # 4. Notificar a Miku para que avise por voz y en el chat principal
                if self.callback:
                    self.callback(f"[SISTEMA_AGENTE]: El agente '{final_name}' ({final_id}) acaba de terminar la tarea delegada: '{task}'.\nReporte del agente:\n{result}")

            except Exception as e:
                logger.error(f"Error en ejecución del agente {final_name}: {e}")
                self.agent_statuses[final_id] = {"busy": False, "task": "", "name": final_name}
                broadcast_ui_command({
                    "type": "agent_busy",
                    "agent_id": final_id,
                    "agent_name": final_name,
                    "busy": False
                })
                broadcast_ui_command({
                    "type": "agent_reply",
                    "agent_id": final_id,
                    "agent_name": final_name,
                    "text": f"Error técnico al ejecutar la tarea: {e}"
                })
                if self.callback:
                    self.callback(f"[SISTEMA_AGENTE]: El agente '{final_name}' falló al realizar la tarea '{task}'. Error técnico: {e}")
            finally:
                if final_id in self.active_agents:
                    self.active_agents.remove(final_id)
                if final_id in self.agent_messages:
                    del self.agent_messages[final_id]

        t = threading.Thread(target=run_task, daemon=True)
        t.start()
        return f"Tarea delegada exitosamente al agente {final_name}. Está ejecutándola en segundo plano y te avisará cuando termine."

# Instancia global
agent_manager = AgentManager()

