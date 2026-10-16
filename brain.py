import os
import json
import logging
import openai
import google.auth
import google.auth.transport.requests
from config import NVIDIA_API_KEY, GOOGLE_CLOUD_PROJECT, GOOGLE_CLOUD_LOCATION
from tools import tools_schema, available_functions

logger = logging.getLogger("Cerebro")

vertex_credentials = None
auth_req = None

def get_vertex_client():
    global vertex_credentials, auth_req
    if not GOOGLE_CLOUD_PROJECT:
        return None
        
    if not vertex_credentials:
        vertex_credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
        auth_req = google.auth.transport.requests.Request()
        
    if not vertex_credentials.valid:
        vertex_credentials.refresh(auth_req)
        
    # El proxy de OpenAI no soporta location 'global'. Forzamos us-central1 para la API REST si está en global.
    location = GOOGLE_CLOUD_LOCATION
    if location.lower() == "global":
        location = "us-central1"
        
    return openai.OpenAI(
        base_url=f"https://{location}-aiplatform.googleapis.com/v1/projects/{GOOGLE_CLOUD_PROJECT}/locations/{location}/endpoints/openapi",
        api_key=vertex_credentials.token,
        max_retries=6
    )

_current_gemini_key_idx = 0
_current_groq_key_idx = 0

def get_gemini_client():
    global _current_gemini_key_idx
    from config import GEMINI_API_KEY
    if not GEMINI_API_KEY:
        return None, None
    keys = [k.strip() for k in GEMINI_API_KEY.split(",") if k.strip()]
    if not keys:
        return None, None
    selected_key = keys[_current_gemini_key_idx % len(keys)]
    try:
        cl = openai.OpenAI(
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            api_key=selected_key,
            max_retries=2
        )
        return cl, "gemini-flash-lite-latest"
    except Exception as e:
        logger.error(f"Error inicializando Google AI Studio Gemini: {e}")
        return None, None

def rotate_gemini_key():
    global _current_gemini_key_idx
    from config import GEMINI_API_KEY
    keys = [k.strip() for k in GEMINI_API_KEY.split(",") if k.strip()]
    if len(keys) > 1:
        _current_gemini_key_idx = (_current_gemini_key_idx + 1) % len(keys)
        logger.info(f"Rotando a clave Gemini de respaldo #{_current_gemini_key_idx + 1}")
        return True
    return False

def get_groq_client():
    global _current_groq_key_idx
    from config import GROQ_API_KEY
    if not GROQ_API_KEY:
        return None, None
    keys = [k.strip() for k in GROQ_API_KEY.split(",") if k.strip()]
    if not keys:
        return None, None
    selected_key = keys[_current_groq_key_idx % len(keys)]
    try:
        from groq import Groq
        return Groq(api_key=selected_key), "llama-3.3-70b-versatile"
    except Exception as e:
        logger.error(f"Error inicializando Groq: {e}")
        return None, None

def rotate_groq_key():
    global _current_groq_key_idx
    from config import GROQ_API_KEY
    keys = [k.strip() for k in GROQ_API_KEY.split(",") if k.strip()]
    if len(keys) > 1:
        _current_groq_key_idx = (_current_groq_key_idx + 1) % len(keys)
        logger.info(f"Rotando a clave Groq de respaldo #{_current_groq_key_idx + 1}")
        return True
    return False


def load_llm_history(target_agent="miku"):
    import os
    import json
    from miku_paths import get_daily_chat_history_file
    file_path = get_daily_chat_history_file()
    if not os.path.exists(file_path):
        return []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        llm_hist = []
        for msg in data[-20:]:  # Solo los últimos 20 para no saturar tokens
            sender = msg.get("sender")
            msg_agent = msg.get("agent_id") or ("miku" if sender == "user" else sender)
            
            if sender == "user":
                # Cada agente solo debe cargar mensajes que el usuario le envió a él
                target_match = (msg_agent == target_agent) or (target_agent == "miku" and not msg.get("agent_id"))
                if target_match:
                    llm_hist.append({"role": "user", "content": msg.get("text", "")})
            else:
                if target_agent == "miku":
                    if msg_agent == "miku" or sender == "miku":
                        llm_hist.append({"role": "assistant", "content": msg.get("text", "")})
                else:
                    if msg_agent == target_agent or sender == target_agent:
                        llm_hist.append({"role": "assistant", "content": msg.get("text", "")})
        return llm_hist
    except:
        return []

conversation_history = load_llm_history("miku")
agent_conversation_histories = {}

def get_llm_response(user_input: str, system_prompt: str = "", status_callback=None, interrupt_event=None, agent_id: str = "miku", agent_mcp: str = None) -> str:
    global conversation_history, agent_conversation_histories
    
    if agent_id and agent_id != "miku":
        if agent_id not in agent_conversation_histories:
            agent_conversation_histories[agent_id] = load_llm_history(agent_id)
        active_hist = agent_conversation_histories[agent_id]
    else:
        active_hist = conversation_history
    
    if user_input.startswith("[SILENT_DROP]"):
        import os
        from tools_miku import analizar_archivo_silencioso
        file_path = user_input.replace("[SILENT_DROP]", "").strip()
        if status_callback: status_callback("Analizando...")
        analysis = analizar_archivo_silencioso(file_path)
        user_input = f"El usuario acaba de arrastrar el archivo '{os.path.basename(file_path)}'.\nContenido extraído del archivo: {analysis}\nOBLIGATORIO: Usa la herramienta 'mostrar_tarjeta_visual' pasándole un mensaje resumido. Háblame brevemente (sin usar asteriscos ni markdown)."
    
    if not active_hist:
        if system_prompt:
            active_hist.append({"role": "system", "content": system_prompt})
    else:
        if system_prompt and len(active_hist) > 0 and active_hist[0].get("role") == "system":
            active_hist[0] = {"role": "system", "content": system_prompt}
            
    active_hist.append({"role": "user", "content": user_input})
    
    # Mantener el historial acotado para no exceder tokens (Aumentado a 40 para multitasking)
    if len(active_hist) > 41:
        active_hist[:] = [active_hist[0]] + active_hist[-40:]
        
    active_client = None
    active_model = None
    provider_name = "unknown"
    use_fallback = False

    # 1. Obtener cliente y modelo según la configuración activa (models_config.json)
    try:
        from models_provider import get_client_and_model
        active_client, active_model, provider_name = get_client_and_model(category="chat")
        if active_client:
            logger.info(f"Cerebro activo: {provider_name.upper()} ({active_model})")
    except Exception as e:
        logger.warning(f"Error resolviendo cliente desde models_provider: {e}")

    # Si no se pudo obtener cliente del proveedor configurado, intentar los fallbacks tradicionales
    if not active_client:
        gemini_cl, gemini_mod = get_gemini_client()
        if gemini_cl:
            active_client = gemini_cl
            active_model = gemini_mod
            provider_name = "google"
            logger.info(f"Cerebro activo (fallback directo): Google AI Studio ({active_model})")
        else:
            try:
                active_client = get_vertex_client()
                if active_client:
                    active_model = "google/gemini-2.5-flash"
                    provider_name = "vertex"
            except Exception as e:
                logger.warning(f"No se pudo inicializar Vertex AI: {e}")
                use_fallback = True

    # 2. Router Semántico dinámico si estamos en Google
    if active_client and provider_name == "google" and not use_fallback:
        try:
            router_prompt = f"""Eres el instinto de Miku. Analiza la petición del usuario: "{user_input}"
Responde ÚNICAMENTE con UNA de estas 3 palabras:
PRO: Si el usuario pide escribir código, scripts, o resolver problemas de programación.
COMPUTE: Si el usuario pide interactuar con la pantalla, usar el ratón, abrir navegadores, buscar imágenes o usar programas.
BASE: Para saludos, conversaciones generales, o si no estás seguro.
NO DIGAS NADA MÁS, SÓLO LA PALABRA."""

            router_resp = active_client.chat.completions.create(
                model=active_model,
                messages=[{"role": "user", "content": router_prompt}],
                max_tokens=10,
                temperature=0.0
            )
            message = router_resp.choices[0].message
            content = getattr(message, 'content', None)
            decision = content.strip().upper() if content else "BASE"
            
            if "PRO" in decision:
                active_model = "gemini-2.5-pro"
            elif "COMPUTE" in decision:
                active_model = "gemini-2.5-flash"
            else:
                active_model = active_model or "gemini-2.5-flash"
                
            logger.info(f"Router Semántico: Decisión '{decision}' -> Activando modo {active_model}")
        except Exception as e:
            err_str = str(e)
            logger.warning(f"Error en router semántico: {err_str}")
            if "403" in err_str or "BILLING_DISABLED" in err_str or "PERMISSION_DENIED" in err_str or "503" in err_str or "429" in err_str:
                logger.info("Cambiando al motor de respaldo Groq...")
                use_fallback = True

    if use_fallback or not active_client:
        groq_cl, groq_mod = get_groq_client()
        if groq_cl:
            active_client = groq_cl
            active_model = "llama-3.3-70b-versatile"
            provider_name = "groq"
            logger.info(f"Cerebro activo: Groq ({active_model})")
        else:
            return "Error: No se encontró ningún cliente de IA activo. Por favor configura tu API Key en Ajustes."
    
    import time
    try:
        from mcp_client import mcp_manager
        if not agent_id or agent_id == "miku":
            combined_tools = tools_schema + mcp_manager.get_dynamic_tools_schema()
        else:
            # Sub-agentes especializados: herramientas base del sistema para trabajar
            sub_allowed = [
                "ejecutar_comando_sistema", "escribir_y_ejecutar_python",
                "buscar_en_internet", "leer_pagina_web", "navegar_web_autonomo",
                "abrir_aplicacion", "tomar_captura_pantalla"
            ]
            base_tools = [t for t in tools_schema if t.get("function", {}).get("name") in sub_allowed]
            
            target_mcp = agent_mcp
            if not target_mcp or target_mcp.lower() in ("none", "ninguno", ""):
                if agent_id.lower() == "github":
                    target_mcp = "github"
            
            mcp_tools = []
            if target_mcp and target_mcp.lower() not in ("none", "ninguno", ""):
                mcp_tools = mcp_manager.get_dynamic_tools_schema(server_filter=target_mcp)
            
            combined_tools = base_tools + mcp_tools
        
        def _execute_completion(cl, mod, hist):
            # Limpiar mensajes para evitar error 400 en Groq o Vertex por campos extraños
            clean_messages = []
            for m in hist:
                if isinstance(m, dict):
                    clean_m = {}
                    for k in ("role", "content", "name", "tool_calls", "tool_call_id"):
                        if k in m and m[k] is not None:
                            clean_m[k] = m[k]
                    if "content" not in clean_m or clean_m["content"] is None:
                        clean_m["content"] = ""
                    clean_messages.append(clean_m)
                else:
                    clean_messages.append(m)

            call_kwargs = {
                "messages": clean_messages,
                "model": mod,
                "temperature": 0.4,
                "max_tokens": 4096
            }
            if combined_tools:
                call_kwargs["tools"] = combined_tools
            return cl.chat.completions.create(**call_kwargs)

        consecutive_errors = 0
        for iteration in range(15): # Límite a 15 para tareas complejas sin llegar al infinito
            
            if interrupt_event and interrupt_event.is_set():
                logger.info("Interrupción detectada en brain.py. Abortando bucle de herramientas.")
                return "[INTERRUPTED]"

            # Limpiar imágenes antiguas del historial en CADA iteración para evitar error 429 por acumulación de fotos
            image_count = 0
            for msg in reversed(active_hist):
                if isinstance(msg, dict):
                    if msg.get("role") == "user" and isinstance(msg.get("content"), list):
                        for i in range(len(msg["content"])):
                            if isinstance(msg["content"][i], dict) and msg["content"][i].get("type") == "image_url":
                                image_count += 1
                                if image_count > 1:
                                    msg["content"][i] = {"type": "text", "text": "[Imagen antigua liberada de la memoria para no saturar]"}
                                
            try:
                response = _execute_completion(active_client, active_model, active_hist)
            except Exception as client_err:
                err_text = str(client_err)
                response = None
                if ("429" in err_text or "RESOURCE_EXHAUSTED" in err_text or "rate limit" in err_text.lower()) and not use_fallback:
                    if rotate_gemini_key():
                        gemini_cl, _ = get_gemini_client()
                        if gemini_cl:
                            active_client = gemini_cl
                            logger.info("Reintentando petición con clave Gemini de respaldo...")
                            try:
                                response = _execute_completion(active_client, active_model, active_hist)
                            except Exception as re_err:
                                err_text = str(re_err)
                                use_fallback = True
                        else:
                            use_fallback = True
                    else:
                        use_fallback = True

                if not response and ("403" in err_text or "BILLING_DISABLED" in err_text or "PERMISSION_DENIED" in err_text or use_fallback):
                    logger.warning(f"Cambiando inmediatamente a Groq por: {err_text}")
                    use_fallback = True
                    groq_cl, groq_mod = get_groq_client()
                    if groq_cl:
                        active_client = groq_cl
                        active_model = groq_mod
                        response = _execute_completion(active_client, active_model, active_hist)
                    else:
                        raise client_err
            
            if not response.choices:
                return "Error: El cerebro devolvió una respuesta vacía (posible filtro de seguridad)."
                
            response_message = response.choices[0].message
            
            if response_message is None:
                if response.choices[0].finish_reason == "malformed_function_call":
                    # Forzar un reintento pidiéndole al LLM que corrija su JSON
                    active_hist.append({
                        "role": "user",
                        "content": "SISTEMA: Tuviste un error 'malformed_function_call'. Seguramente olvidaste escapar comillas o saltos de línea en el JSON de la herramienta. Corrige la sintaxis y vuelve a intentar la llamada."
                    })
                    continue
                return f"Error: Mensaje bloqueado o nulo. Razón: {response.choices[0].finish_reason}"
            
            # OpenAI SDK y Gemini esperan el objeto original para preservar firmas internas como thought_signature
            tool_calls = response_message.tool_calls
                
            if not tool_calls:
                content_resp = response_message.content or ""
                if "[IGNORAR]" in content_resp or content_resp.strip() == "":
                    # Si fue ignorado, borramos el último mensaje de usuario del historial para no contaminar
                    if active_hist and active_hist[-1].get("role") == "user":
                        active_hist.pop()
                else:
                    active_hist.append(response_message)
                    
                if status_callback:
                    try:
                        status_callback("")
                    except Exception as cb_err:
                        logger.error(f"Error in status_callback: {cb_err}")
                return content_resp
                
            active_hist.append(response_message)
            
            extra_messages_to_append = []
            
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                
                function_to_call = None
                is_mcp_tool = function_name.startswith("mcp_")
                if not is_mcp_tool:
                    function_to_call = available_functions.get(function_name)
                
                if function_to_call or is_mcp_tool:
                    try:
                        args_raw = tool_call.function.arguments
                        function_args = json.loads(args_raw) if args_raw else {}
                        if function_args is None:
                            function_args = {}
                    except json.JSONDecodeError as json_err:
                        logger.error(f"Error parseando JSON de {function_name}: {json_err}")
                        function_args = {}
                    logger.info(f"Ejecutando: {function_name}")
                    
                    try:
                        if status_callback:
                            if function_name == "ver_pantalla":
                                status_callback("Analizando pantalla...")
                            elif function_name == "hacer_clic_visual":
                                status_callback("Haciendo clic...")
                            elif function_name == "escribir_texto":
                                status_callback("Escribiendo texto...")
                            elif function_name == "buscar_en_internet":
                                status_callback("Buscando en internet...")
                            elif function_name == "enviar_archivo_a_celular":
                                status_callback("Enviando archivo...")
                            elif is_mcp_tool:
                                status_callback(f"Llamando a plugin MCP {function_name.replace('mcp_', '')}...")
                            else:
                                status_callback(f"{function_name.replace('_', ' ').capitalize()}...")
                    except Exception as e:
                        logger.error(f"Error en status_callback: {e}")
                    
                    if is_mcp_tool:
                        import asyncio
                        import concurrent.futures
                        if mcp_manager.main_loop:
                            future = asyncio.run_coroutine_threadsafe(
                                mcp_manager.execute_tool(function_name, function_args),
                                mcp_manager.main_loop
                            )
                            try:
                                function_response = future.result(timeout=30) # Esperar max 30s
                            except concurrent.futures.TimeoutError:
                                function_response = "Error: Timeout esperando la herramienta MCP."
                            except Exception as e:
                                function_response = f"Error ejecutando MCP: {e}"
                        else:
                            function_response = "Error: MCP Manager no está conectado al loop principal."
                    else:
                        function_response = function_to_call(**function_args)
                    
                    if function_response == "MIKU_VISION_REQUEST":
                        print("[Sistema] Miku ha solicitado ver la pantalla...")
                        try:
                            import pyautogui
                            import base64
                            from io import BytesIO
                            
                            screenshot = pyautogui.screenshot()
                            buffered = BytesIO()
                            screenshot.save(buffered, format="JPEG", quality=60)
                            base64_image = base64.b64encode(buffered.getvalue()).decode('utf-8')
                            
                            extra_messages_to_append.append({
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": "Aquí tienes la captura de mi pantalla actual para que la analices."},
                                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                                ]
                            })
                            function_response = "Captura tomada y enviada exitosamente. Revisa el último mensaje con la imagen."
                        except Exception as e:
                            function_response = f"Falló la visión local: {e}"
                    
                    # Detectar si fue un error para el contador de aborto de seguridad
                    resp_str = str(function_response)
                    if "Error" in resp_str or "Falló" in resp_str or "FAIL" in resp_str:
                        consecutive_errors += 1
                    else:
                        consecutive_errors = 0 # Resetea si hizo algo bien
                        
                    active_hist.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": resp_str,
                    })
                else:
                    consecutive_errors += 1
                    active_hist.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": "Función no encontrada.",
                    })
                    
            for msg in extra_messages_to_append:
                active_hist.append(msg)
                
            if consecutive_errors >= 4:
                return "Me he encontrado con demasiados errores consecutivos intentando hacer esto. Me detuve por seguridad para no hacer un bucle infinito."
                
        # Si superó las 15 iteraciones
        return "He realizado una cadena de tareas bastante larga (15 pasos). Me he detenido por seguridad para no saturar el sistema."

    except Exception as e:
        error_str = str(e)
        print(f"\n[ERROR GENERAL DE IA]: {error_str}\n")
        
        # Extraer el código del error si existe
        code = "desconocido"
        if "'code':" in error_str:
            try:
                code = error_str.split("'code':")[1].split(',')[0].strip().strip("'\"")
            except:
                pass
        elif "Error code:" in error_str:
            try:
                code = error_str.split("Error code:")[1].split('-')[0].strip()
            except:
                pass
                
        return f"Error al contactar al cerebro principal. Código del error: {code}."
