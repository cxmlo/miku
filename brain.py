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
        for msg in data[-6:]:  # Solo los últimos 6 mensajes (3 turnos) para minimizar tokens
            sender = msg.get("sender")
            msg_agent = msg.get("agent_id") or ("miku" if sender == "user" else sender)
            raw_text = msg.get("text", "") or ""
            # Podar textos gigantes heredados de volcados de archivos o errores
            if len(raw_text) > 400:
                raw_text = raw_text[:350] + "... [truncado de historial]"
            
            if sender == "user":
                target_match = (msg_agent == target_agent) or (target_agent == "miku" and not msg.get("agent_id"))
                if target_match:
                    llm_hist.append({"role": "user", "content": raw_text})
            else:
                if target_agent == "miku":
                    if msg_agent == "miku" or sender == "miku":
                        llm_hist.append({"role": "assistant", "content": raw_text})
                else:
                    if msg_agent == target_agent or sender == target_agent:
                        llm_hist.append({"role": "assistant", "content": raw_text})
        return llm_hist
    except:
        return []

conversation_history = load_llm_history("miku")
agent_conversation_histories = {}

def get_llm_response(user_input: str, system_prompt: str = "", status_callback=None, interrupt_event=None, agent_id: str = "miku", agent_mcp: str = None) -> str:
    global conversation_history, agent_conversation_histories
    
    # Determinar si el modo bajo costo está activo
    is_low_cost = False
    try:
        import server
        is_low_cost = getattr(server, "LOW_COST_MODE", False)
    except Exception:
        pass

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
        if len(analysis) > 800:
            analysis = analysis[:800] + "... [resumen acotado]"
        user_input = f"El usuario acaba de arrastrar el archivo '{os.path.basename(file_path)}'.\nContenido extraído del archivo: {analysis}\nOBLIGATORIO: Usa la herramienta 'mostrar_tarjeta_visual' pasándole un mensaje resumido. Háblame brevemente (sin usar asteriscos ni markdown)."
    
    if not active_hist or active_hist[0].get("role") != "system":
        if system_prompt:
            active_hist.insert(0, {"role": "system", "content": system_prompt})
    else:
        if system_prompt:
            active_hist[0] = {"role": "system", "content": system_prompt}
            
    active_hist.append({"role": "user", "content": user_input})
    
    # Mantener el historial estrictamente acotado (máximo 4 mensajes en bajo costo, 6 en normal)
    max_h_keep = 4 if is_low_cost else 6
    if len(active_hist) > max_h_keep + 1:
        active_hist[:] = [active_hist[0]] + active_hist[-max_h_keep:]
        
    active_client = None
    active_model = None
    provider_name = "unknown"
    use_fallback = False

    # 1. Obtener cliente y modelo según la configuración activa (models_config.json)
    try:
        from models_provider import get_client_and_model
        req_cat = "pro" if (agent_id and agent_id.lower() in ("github", "antigravity")) else "chat"
        active_client, active_model, provider_name = get_client_and_model(category=req_cat)
        if not active_client and req_cat == "pro":
            active_client, active_model, provider_name = get_client_and_model(category="chat")
        if active_client:
            logger.info(f"Cerebro activo para '{agent_id or 'miku'}': {provider_name.upper()} ({active_model})")
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

    # 2. Router Semántico dinámico si estamos en Google y el agente es Miku
    if active_client and provider_name == "google" and not use_fallback and (not agent_id or agent_id == "miku"):
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
        
        # Verificar estado de Modo Bajo Costo
        is_low_cost = False
        try:
            import server
            is_low_cost = getattr(server, "LOW_COST_MODE", False)
        except Exception:
            pass

        u_low = (user_input or "").lower()
        
        # Agrupaciones temáticas de herramientas para optimización extrema de tokens:
        TOOL_CLUSTERS = {
            "music": {
                "keywords": ["cancion", "canción", "musica", "música", "spotify", "youtube", "reproduce", "reproducir", "pausa", "play", "volumen", "tema", "pista"],
                "tools": ["reproducir_en_spotify", "controlar_spotify", "que_suena_en_spotify", "reproducir_en_youtube", "controlar_multimedia"]
            },
            "mobile": {
                "keywords": ["celular", "telefono", "teléfono", "miku-link", "mikulink", "enviar al cel", "enviar a cel", "enviar archivo", "apk", "compartir", "android", "alarma", "cronometro", "cronómetro", "archivo adjuntado"],
                "tools": ["enviar_archivo_a_celular", "enviar_imagen_a_chat", "ejecutar_intent_android", "abrir_panel_secretos_en_app"]
            },
            "system_os": {
                "keywords": ["abre", "abrir", "cierra", "cerrar", "minimiza", "maximiza", "programa", "aplicacion", "aplicación", "app", "consola", "powershell", "cmd", "comando", "terminal", "bloquear", "apagar", "reiniciar"],
                "tools": ["abrir_aplicacion", "gestionar_ventana", "ejecutar_comando_sistema", "atajo_teclado", "ejecutar_macro_teclado", "esperar_segundos", "monitorear_actividad_pc"]
            },
            "web": {
                "keywords": ["busca", "buscar", "google", "investiga", "internet", "web", "pagina", "página", "enlace", "link", "noticia", "clima"],
                "tools": ["buscar_en_internet", "leer_pagina_web", "navegar_web_autonomo", "mostrar_widget_clima"]
            },
            "vision": {
                "keywords": ["pantalla", "mira", "ver", "captura", "screenshot", "foto", "clic", "click", "pulsa", "presiona", "boton", "botón", "scroll", "raton", "ratón", "mouse"],
                "tools": ["ver_pantalla", "hacer_clic_visual", "mover_raton_visual", "hacer_scroll", "escribir_en_elemento", "tomar_captura_pantalla", "escanear_ventana_activa", "escribir_texto"]
            },
            "agents": {
                "keywords": ["antigravity", "github", "agente", "delegar", "subagente", "sub-agente", "equipo"],
                "tools": ["delegar_a_agente", "listar_agentes_disponibles", "abrir_chat_con_agente", "delegar_tarea", "enviar_mensaje_a_agente"]
            },
            "memory": {
                "keywords": ["recuerda", "memoria", "acuérdate", "guardar dato", "aprende", "mi nombre es", "preferencia"],
                "tools": ["aprender_sobre_usuario", "guardar_enlace_memoria", "buscar_en_memoria"]
            },
            "widgets": {
                "keywords": ["widget", "reloj", "hora", "tarjeta visual"],
                "tools": ["mostrar_widget_reloj", "mostrar_widget_clima", "mostrar_widget_info", "mostrar_tarjeta_visual", "modificar_estado_widget"]
            }
        }
        
        if not agent_id or agent_id == "miku":
            # Detección inmediata de conversación casual / saludos (0 herramientas = 0 tokens desperdiciados)
            CASUAL_GREETINGS = {
                "hola", "buenos dias", "buenos días", "buenas tardes", "buenas noches",
                "como estas", "cómo estás", "que tal", "qué tal", "quien eres", "quién eres",
                "gracias", "muchas gracias", "ok", "vale", "perfecto", "listo", "jaja", "jajaja",
                "adios", "adiós", "chao", "bye", "buenas", "hola miku", "hola miku!"
            }
            clean_u = u_low.strip().rstrip("!?.,:;")
            if clean_u in CASUAL_GREETINGS or (len(clean_u.split()) <= 3 and any(g in clean_u for g in ["hola", "como estas", "cómo estás", "que tal", "qué tal", "gracias"])):
                logger.info("Conversación casual detectada: 0 herramientas cargadas para ahorrar tokens.")
                combined_tools = []
            else:
                # Puntuar clusters y tomar solo el cluster más relevante
                cluster_scores = []
                for c_name, c_info in TOOL_CLUSTERS.items():
                    score = sum(1 for kw in c_info["keywords"] if kw in u_low)
                    if score > 0:
                        cluster_scores.append((score, c_info["tools"]))
                
                cluster_scores.sort(key=lambda x: x[0], reverse=True)
                matched_tool_names = set()
                # Seleccionar solo el top 1 o 2 clusters más relevantes
                for _, tools in cluster_scores[:2]:
                    matched_tool_names.update(tools)
                    if len(matched_tool_names) >= (3 if is_low_cost else 5):
                        break

                # Carga inteligente de herramientas MCP con límite estricto
                mcp_tools = []
                mcp_keywords = {
                    "github": ["git commit", "git push", "repositorio", "branch", "pull request", "github"],
                    "sqlite": ["sql query", "base de datos", "database", "select * from"],
                    "filesystem": ["crear carpeta", "leer archivo", "guardar archivo", "filesystem"],
                    "memory": ["grafo de memoria", "knowledge graph"]
                }
                active_servers = list(mcp_manager.servers_config.keys()) if hasattr(mcp_manager, "servers_config") else []
                for s_name in active_servers:
                    kws = mcp_keywords.get(s_name.lower(), [s_name.lower()])
                    if any(k in u_low for k in kws):
                        mcp_tools.extend(mcp_manager.get_dynamic_tools_schema(server_filter=s_name))
                        break # Máximo 1 servidor MCP a la vez

                if not matched_tool_names and not mcp_tools:
                    logger.info("Modo Conversacional Puro activado: 0 herramientas cargadas.")
                    combined_tools = []
                else:
                    base_selected = [t for t in tools_schema if t.get("function", {}).get("name") in matched_tool_names]
                    # Limitar estrictamente combined_tools a máximo 4 herramientas (o 2 en bajo costo)
                    max_tools_allowed = 2 if is_low_cost else 5
                    combined_tools = (base_selected + mcp_tools)[:max_tools_allowed]
                    logger.info(f"Router dinámico: Cargadas {len(combined_tools)} herramientas seleccionadas para '{user_input[:40]}'")
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
            
            combined_tools = (base_tools + mcp_tools)[:6]
        
        def _execute_completion(cl, mod, hist):
            clean_messages = []
            hist_len = len(hist)
            for idx, m in enumerate(hist):
                is_latest_turn = (idx >= hist_len - 2)
                clean_m = {}
                
                # Normalizar tanto objetos del SDK como diccionarios
                if isinstance(m, dict):
                    role = m.get("role", "user")
                    content = m.get("content", "")
                    name = m.get("name")
                    tool_calls = m.get("tool_calls")
                    tool_call_id = m.get("tool_call_id")
                else:
                    role = getattr(m, "role", "assistant")
                    content = getattr(m, "content", "")
                    name = getattr(m, "name", None)
                    tool_calls = getattr(m, "tool_calls", None)
                    tool_call_id = getattr(m, "tool_call_id", None)
                
                clean_m["role"] = role
                
                # Podar imágenes masivas en mensajes pasados
                if isinstance(content, list):
                    pruned_list = []
                    for item in content:
                        if isinstance(item, dict) and item.get("type") == "image_url":
                            if is_latest_turn:
                                pruned_list.append(item)
                            else:
                                pruned_list.append({"type": "text", "text": "[Captura anterior procesada]"})
                        else:
                            pruned_list.append(item)
                    clean_m["content"] = pruned_list
                elif isinstance(content, str):
                    # Podar textos largos de turnos pasados para no reenviar volcados gigantes
                    if not is_latest_turn:
                        limit = 250 if role == "tool" else (350 if role == "user" else 450)
                        if len(content) > limit:
                            content = content[:limit] + "... [resumido para ahorro de tokens]"
                    clean_m["content"] = content
                else:
                    clean_m["content"] = str(content) if content is not None else ""
                
                if name:
                    clean_m["name"] = name
                if tool_calls:
                    clean_m["tool_calls"] = tool_calls
                if tool_call_id:
                    clean_m["tool_call_id"] = tool_call_id
                
                clean_messages.append(clean_m)

            call_kwargs = {
                "messages": clean_messages,
                "model": mod,
                "temperature": 0.4,
                "max_tokens": 768 if is_low_cost else 1536
            }
            if combined_tools:
                call_kwargs["tools"] = combined_tools
            return cl.chat.completions.create(**call_kwargs)

        consecutive_errors = 0
        max_loop = 2 if is_low_cost else 3
        for iteration in range(max_loop):
            
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

                if use_fallback and not response:
                    groq_cl, groq_mod = get_groq_client()
                    if groq_cl:
                        active_client = groq_cl
                        active_model = "llama-3.3-70b-versatile"
                        logger.info("Reintentando con motor Groq de respaldo...")
                        try:
                            response = _execute_completion(active_client, active_model, active_hist)
                        except Exception as groq_err:
                            err_text = str(groq_err)

                if not response:
                    logger.error(f"[Brain] Error final de cliente: {err_text}")
                    low_err = err_text.lower()
                    if "429" in err_text or "resource_exhausted" in low_err or "rate limit" in low_err:
                        return "⚠️ Límite de peticiones alcanzado (Rate Limit 429). Has excedido la cuota gratuita por minuto de este modelo. Por favor espera unos momentos o añade claves de respaldo en Ajustes."
                    elif "billing" in low_err or "quota" in low_err or "credit" in low_err or "402" in err_text:
                        return "💳 Error al contactar la API: Falta de crédito o cuota en tu cuenta del proveedor. Este modelo requiere una cuenta con facturación activa."
                    elif "401" in err_text or "invalid_api_key" in low_err or "unauthorized" in low_err:
                        return "🔑 API Key no válida o revocada. Revisa la clave configurada para este proveedor en Ajustes."
                    elif "not found" in low_err or "model_not_found" in low_err or "404" in err_text:
                        return f"🔍 El modelo '{active_model}' no fue encontrado o no está disponible para tu cuenta en este proveedor."
                    elif "400" in err_text:
                        return f"⚠️ Petición rechazada por la API (Error 400). Es posible que el modelo '{active_model}' no soporte esta función o requiera una cuenta con facturación activa."
                    return f"⚠️ Error al contactar a la API ({active_model}): {err_text}"
            
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
                            # Redimensionar a resolución eficiente para no saturar tokens
                            screenshot.thumbnail((1024, 576))
                            buffered = BytesIO()
                            screenshot.save(buffered, format="JPEG", quality=45)
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
                    # Truncar salidas de herramientas para proteger el contexto y la cuota de tokens
                    max_resp = 350 if is_low_cost else 700
                    if len(resp_str) > max_resp:
                        resp_str = resp_str[:max_resp] + f"\n[... Salida truncada para ahorrar tokens. Original: {len(str(function_response))} chars]"

                    low_resp = resp_str.lower()
                    if "error" in low_resp or "falló" in low_resp or "fail" in low_resp:
                        consecutive_errors += 1
                        if "bloqueada por seguridad" in low_resp or "acceso denegado" in low_resp or "seguridad" in low_resp:
                            consecutive_errors += 2 # Acelerar aborto temprano si el sandbox de seguridad bloqueó la ruta
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
                
            if consecutive_errors >= 2:
                if "seguridad" in resp_str.lower() or "bloqueada" in resp_str.lower():
                    return "El sistema de seguridad ha bloqueado el acceso a esa ruta protegida. Me he detenido para evitar consumir tokens en reintentos fallidos."
                return "Me he encontrado con errores consecutivos intentando ejecutar la acción. Me detuve para evitar consumir tokens en bucles de error."
                
        return "He completado las acciones solicitadas."

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
