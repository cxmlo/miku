import threading
import logging
from groq import Groq
from config import GROQ_API_KEY

logger = logging.getLogger("Agentes")

class AgentManager:
    def __init__(self):
        self.callback = None
        self.agent_counter = 0
        self.last_result = ""
        self.active_agents = set()
        self.agent_messages = {} # Buzón para mensajes entrantes por agente

    def send_message(self, message: str) -> str:
        if not self.active_agents:
            return "No hay ningún agente activo en segundo plano."
        for agent_id in self.active_agents:
            if agent_id not in self.agent_messages:
                self.agent_messages[agent_id] = []
            self.agent_messages[agent_id].append(message)
        return "Mensaje entregado al agente en segundo plano. Modificará su comportamiento."

    def cancel_all(self):
        if not self.active_agents:
            return "No hay agentes para cancelar."
        for agent_id in list(self.active_agents):
            if agent_id not in self.agent_messages:
                self.agent_messages[agent_id] = []
            self.agent_messages[agent_id].append("[CANCELAR_TAREA]")
        return "Se solicitó cancelación a todos los agentes."

    def _update_ui(self):
        try:
            from ui import ui_comm
            if not self.active_agents:
                ui_comm.agent_status_signal.emit("")
            else:
                text = "\n".join([f"⚙️ Agente {id} trabajando..." for id in sorted(self.active_agents)])
                ui_comm.agent_status_signal.emit(text)
        except Exception:
            pass

    def delegate(self, task: str):
        self.agent_counter += 1
        agent_id = self.agent_counter
        self.active_agents.add(agent_id)
        self.agent_messages[agent_id] = [] # Inicializar buzón
        self._update_ui()
        
        def run_task():
            logger.info(f"Iniciando tarea en paralelo para Agente {agent_id}: {task}...")
            try:
                # Usamos NVIDIA directamente ya que Groq no tiene tokens (como en brain.py)
                from brain import get_vertex_client
                gemini_client = get_vertex_client()
                
                if not gemini_client:
                    raise Exception("No hay GOOGLE_CLOUD_PROJECT configurado.")
                
                # Importar herramientas para que el agente pueda hacer cosas
                from tools import tools_schema, available_functions
                import json
                
                # Filtrar herramientas: Un agente NUNCA debe poder delegar a otro agente (evita bucle infinito), ni usar visión.
                herramientas_prohibidas = ["delegar_tarea", "hacer_clic_visual", "escribir_en_elemento", "escanear_ventana_activa", "hablar_al_usuario"]
                agent_tools_schema = [t for t in tools_schema if t["function"]["name"] not in herramientas_prohibidas]
                agent_available_functions = {k: v for k, v in available_functions.items() if k not in herramientas_prohibidas}
                
                messages = [
                    {"role": "system", "content": "Eres un agente de fondo autónomo de Miku. Tienes herramientas a tu disposición. Usa 'ejecutar_comando_sistema' para descargar archivos con powershell o curl si te lo piden, y 'buscar_en_internet' para buscar información. No puedes controlar el ratón. TU ÚNICO OBJETIVO ES RESOLVER LA TAREA Y RETORNAR EL TEXTO FINAL. IMPORTANTE: NO devuelvas un mensaje diciendo 'he completado la tarea', DEBES devolver EL RESULTADO DE LA TAREA (ej. si te piden un ensayo, tu respuesta final DEBE SER el ensayo completo)."},
                    {"role": "user", "content": task}
                ]
                
                import time
                for _ in range(30): # Aumentado a 30 para tareas largas y complejas
                    # Revisar si hay mensajes nuevos del usuario para este agente
                    if self.agent_messages.get(agent_id):
                        cancelado = False
                        while self.agent_messages[agent_id]:
                            new_msg = self.agent_messages[agent_id].pop(0)
                            if new_msg == "[CANCELAR_TAREA]":
                                cancelado = True
                                break
                            logger.info(f"Agente {agent_id} recibió interrupción: {new_msg}")
                            messages.append({"role": "user", "content": f"[INTERRUPCIÓN / CORRECCIÓN DEL USUARIO]: {new_msg}. Adapta tu plan y comportamiento inmediatamente basado en esta nueva instrucción."})
                        if cancelado:
                            result = "Tarea abortada manualmente por el usuario."
                            break
                            
                    time.sleep(2) # Pausa para evitar error 429 de Vertex AI
                    response = gemini_client.chat.completions.create(
                        messages=messages,
                        model="google/gemini-2.5-flash",
                        temperature=0.5,
                        max_tokens=2048,
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
                            except json.JSONDecodeError as json_err:
                                logger.error(f"Agente {agent_id} Error parseando JSON: {json_err}")
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
                                "content": "Función no encontrada."
                            })
                else:
                    result = "Me detuve por seguridad después de 30 acciones."
                
                logger.info(f"Agente {agent_id} Tarea finalizada con éxito.")
                self.last_result = result
                
                if self.callback:
                    # Notificar al cerebro principal
                    self.callback(f"[SISTEMA_AGENTE] Tu agente de fondo {agent_id} acaba de terminar la tarea '{task}'. Aquí está su reporte:\n{result}")
            except Exception as e:
                logger.error(f"Agente {agent_id} Error: {e}")
                if self.callback:
                    self.callback(f"[SISTEMA_AGENTE] El agente de fondo {agent_id} falló al realizar la tarea '{task}'. Error técnico: {e}")
            finally:
                if agent_id in self.active_agents:
                    self.active_agents.remove(agent_id)
                if agent_id in self.agent_messages:
                    del self.agent_messages[agent_id]
                self._update_ui()

        # Iniciar el agente en un hilo paralelo
        t = threading.Thread(target=run_task, daemon=True)
        t.start()
        return f"Tarea delegada con éxito al Agente {agent_id}. Te avisará cuando termine."

# Instancia global
agent_manager = AgentManager()
