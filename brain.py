import os
import json
import logging
import openai
import google.auth
import google.auth.transport.requests
from config import NVIDIA_API_KEY, GOOGLE_CLOUD_PROJECT, GOOGLE_CLOUD_LOCATION
from tools import tools_schema, available_functions
from action_result import ActionResult, ActionStatus

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

def _limpiar_target_amigable(target: str, default: str = "el elemento") -> str:
    """Limpia frases largas o prefijos redundantes para dejar un nombre amigable de elemento."""
    if not target or not str(target).strip():
        return default
    t = str(target).strip()
    for prefix in [
        "hacer clic en el enlace de texto ",
        "hacer clic en el icono de ",
        "hacer clic en el botón de ",
        "hacer clic en el enlace ",
        "hacer clic en el icono ",
        "hacer clic en el botón ",
        "hacer clic en la ",
        "hacer clic en el ",
        "hacer clic en ",
        "hacer doble clic en ",
        "dar click en el icono de ",
        "dar click en la barra de ",
        "dar click en ",
        "dar clic en ",
        "clic en el ",
        "clic en la ",
        "clic en ",
        "click en "
    ]:
        if t.lower().startswith(prefix):
            t = t[len(prefix):].strip()
            break
    if len(t) > 60:
        t = t[:57] + "..."
    return t.strip("'\"") or default


def _generar_respuesta_amigable_acciones(executed_results: list) -> str:
    """
    Genera una respuesta en personaje, concisa y veraz para el usuario final,
    cumpliendo con la veracidad técnica sin exponer volcados técnicos, listas de logs o nombres de funciones crudos.
    """
    if not executed_results:
        return "No se ejecutó ninguna acción."

    # Herramientas auxiliares de lectura/inspección
    AUX_TOOLS = {"ver_pantalla", "escanear_ventana_activa", "esperar_segundos"}

    # Separar acciones principales de auxiliares
    main_results = [(fn, res) for fn, res in executed_results if fn not in AUX_TOOLS]
    aux_results = [(fn, res) for fn, res in executed_results if fn in AUX_TOOLS]

    target_results = main_results if main_results else aux_results

    confirmed = [res for _, res in target_results if res.is_confirmed()]
    unverified = [res for _, res in target_results if res.is_unverified()]
    failed = [res for _, res in target_results if res.is_failed()]

    # Si SOLO hubo herramientas auxiliares
    if not main_results:
        if failed:
            return "No se pudo completar la tarea solicitada debido a fallos: No pude tomar o analizar la pantalla en este momento. Por favor verifica que la ventana esté abierta y visible."
        elif any(fn == "ver_pantalla" for fn, _ in aux_results):
            return "He analizado la pantalla actual. ¿En qué te puedo ayudar sobre lo que ves?"
        elif any(fn == "escanear_ventana_activa" for fn, _ in aux_results):
            return "Escaneé la ventana activa, pero no expone controles interactivos accesibles."
        return "Acción completada."

    # 1. Caso: SOLO fallos
    if failed and not confirmed and not unverified:
        last_failed = failed[-1]
        raw_target = last_failed.target or last_failed.action
        friendly_target = _limpiar_target_amigable(raw_target)
        err = (last_failed.error or "").lower()

        if "seguridad" in err or "bloqueada" in err:
            return f"No se pudo completar la tarea solicitada debido a fallos: La acción sobre '{friendly_target}' fue bloqueada por políticas de seguridad."
        elif any(w in err for w in ["coordenadas", "no pudo identificar", "no encontrada", "no se encontró", "respuesta vacía"]):
            return f"No se pudo completar la tarea solicitada debido a fallos: No logré ubicar '{friendly_target}' en la pantalla abierta. ¿Podrías asegurarte de que la ventana esté al frente y visible?"
        else:
            clean_err = last_failed.error or "Error en la ejecución"
            if len(clean_err) > 90:
                clean_err = clean_err[:90] + "..."
            return f"No se pudo completar la tarea solicitada debido a fallos: No pude interactuar con '{friendly_target}' ({clean_err})."

    # 2. Caso: SOLO acciones ejecutadas sin verificación visual
    if unverified and not confirmed and not failed:
        targets = [_limpiar_target_amigable(r.target or r.action) for r in unverified]
        t_str = ", ".join(targets[:2])
        return f"Acción ejecutada pero no confirmada: Ya emití el comando para '{t_str}' en pantalla (sin confirmación visual del resultado). ¿Se abrió o respondió correctamente?"

    # 3. Caso: SOLO confirmadas con éxito
    if confirmed and not failed and not unverified:
        targets = [_limpiar_target_amigable(r.target or r.action) for r in confirmed]
        t_str = ", ".join(targets[:2])
        return f"¡Listo! Acciones completadas y confirmadas con éxito sobre '{t_str}'."

    # 4. Caso Mixto
    parts = []
    if confirmed:
        c_targets = ", ".join([_limpiar_target_amigable(r.target or r.action) for r in confirmed[:2]])
        parts.append(f"Pude completar y confirmar la interacción con '{c_targets}'")
    if unverified:
        u_targets = ", ".join([_limpiar_target_amigable(r.target or r.action) for r in unverified[:2]])
        parts.append(f"emití el comando para '{u_targets}' (sin confirmación visual)")
    if failed:
        f_targets = ", ".join([_limpiar_target_amigable(r.target or r.action) for r in failed[:2]])
        parts.append(f"no se pudo completar '{f_targets}'")

    return "; ".join(parts) + "."

import unicodedata

def _norm_txt(s: str) -> str:
    """Normaliza texto eliminando acentos y diacríticos para búsqueda robusta de palabras clave."""
    return "".join(c for c in unicodedata.normalize("NFD", (s or "").lower()) if unicodedata.category(c) != "Mn")

def get_llm_response(user_input: str, system_prompt: str = "", status_callback=None, interrupt_event=None, agent_id: str = "miku", agent_mcp: str = None, agent_model: str = None) -> str:
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
        cut_idx = len(active_hist) - max_h_keep
        # Evitar empezar el historial podado con mensajes de herramienta huérfanos
        while cut_idx < len(active_hist) and (active_hist[cut_idx].get("role") == "tool" if isinstance(active_hist[cut_idx], dict) else getattr(active_hist[cut_idx], "role", None) == "tool"):
            cut_idx += 1
        active_hist[:] = [active_hist[0]] + active_hist[cut_idx:]
        
    active_client = None
    active_model = None
    provider_name = "unknown"
    use_fallback = False

    # 1. Obtener cliente y modelo según la configuración activa (models_config.json) o modelo asignado al agente
    try:
        from models_provider import get_client_and_model
        req_cat = "pro" if (agent_id and agent_id.lower() in ("github", "antigravity")) else "chat"
        pref_mod = None
        if agent_model and str(agent_model).strip().lower() not in ("", "auto", "none"):
            pref_mod = str(agent_model).strip().replace("google/", "")
        active_client, active_model, provider_name = get_client_and_model(preferred_model=pref_mod, category=req_cat)
        if not active_client and req_cat == "pro":
            active_client, active_model, provider_name = get_client_and_model(preferred_model=pref_mod, category="chat")
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
                    active_model = "gemini-1.5-flash"
                    provider_name = "vertex"
            except Exception as e:
                logger.warning(f"No se pudo inicializar Vertex AI: {e}")
                use_fallback = True

    # 2. Router Semántico dinámico si el agente es Miku
    target_cat = "chat"

    # Detección de mensajes de reintento o seguimiento contextual (ej: "de nuevo", "otra vez", "continúa")
    FOLLOW_UP_TRIGGERS = {"de nuevo", "otra vez", "reintenta", "reintentar", "intenta de nuevo", "repite", "hazlo", "continua", "continúa", "dale", "sigue"}
    prev_user_text = ""
    for m in reversed(active_hist[:-1]):
        r = m.get("role") if isinstance(m, dict) else getattr(m, "role", None)
        if r == "user":
            c = m.get("content") if isinstance(m, dict) else getattr(m, "content", "")
            if isinstance(c, str) and c.strip():
                prev_user_text = c.strip()
                break
            elif isinstance(c, list):
                for part in c:
                    if isinstance(part, dict) and part.get("type") == "text":
                        prev_user_text = part.get("text", "").strip()
                        break
                if prev_user_text:
                    break

    router_input = user_input
    norm_u_check = "".join(c for c in (user_input or "").lower() if c.isalnum() or c.isspace()).strip()
    is_follow_up = (norm_u_check in FOLLOW_UP_TRIGGERS or (len(norm_u_check.split()) <= 3 and any(t in norm_u_check for t in FOLLOW_UP_TRIGGERS))) and bool(prev_user_text)
    if is_follow_up:
        router_input = f"{user_input}. (Continuación o reintento de la tarea previa: '{prev_user_text[:120]}')"
        logger.info(f"[Brain] Mensaje contextual detectado ('{user_input}'). Heredando tarea previa: '{prev_user_text[:60]}'")

    if active_client and not use_fallback and (not agent_id or agent_id == "miku"):
        try:
            router_prompt = f"""Eres el instinto de Miku. Analiza la petición del usuario: "{router_input}"
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
                target_cat = "pro"
            elif "COMPUTE" in decision:
                target_cat = "computer_use"

            if target_cat != "chat":
                new_cl, new_mod, new_prov = get_client_and_model(category=target_cat)
                if new_cl:
                    active_client, active_model, provider_name = new_cl, new_mod, new_prov
                    logger.info(f"Router Semántico: Decisión '{decision}' -> Cambiando cerebro a {provider_name.upper()} ({active_model})")
                    if target_cat == "computer_use":
                        try:
                            from agents import broadcast_ui_command
                            broadcast_ui_command({"type": "ui_command", "action": "shrink_for_vision"})
                        except Exception:
                            pass
                else:
                    if "gemini" in str(active_model).lower():
                        active_model = "gemini-1.5-pro" if "PRO" in decision else "gemini-1.5-flash"
                    logger.info(f"Router Semántico: Decisión '{decision}' (manteniendo proveedor actual) -> {active_model}")
            else:
                logger.info(f"Router Semántico: Decisión 'BASE' -> Manteniendo cerebro {provider_name.upper()} ({active_model})")
        except Exception as e:
            from models_provider import (
                is_auth_error,
                is_not_found_error,
                is_transient_error,
                get_user_friendly_error_message,
                rotate_provider_key,
                create_provider_client
            )
            logger.warning(f"Error en router semántico ({provider_name}): {e}")
            if is_auth_error(e):
                return get_user_friendly_error_message(e, active_model, provider_name)
            if is_not_found_error(e):
                return get_user_friendly_error_message(e, active_model, provider_name)
            if is_transient_error(e):
                if rotate_provider_key(provider_name):
                    new_cl, new_mod, _ = create_provider_client(provider_name, active_model)
                    if new_cl:
                        active_client = new_cl
                        logger.info(f"Router Semántico: rotada clave para {provider_name}.")
                else:
                    use_fallback = True
            else:
                use_fallback = True

    if use_fallback or not active_client:
        from models_provider import get_client_and_model
        fallback_cl, fallback_mod, fallback_prov = get_client_and_model(category="chat")
        if fallback_cl and fallback_prov != provider_name:
            active_client = fallback_cl
            active_model = fallback_mod
            provider_name = fallback_prov
            logger.info(f"Cerebro activo (fallback): {provider_name.upper()} ({active_model})")
        else:
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
        u_norm = _norm_txt(user_input)
        is_mobile_ctx = "MODO MÓVIL" in (system_prompt or "") or "EL CELULAR" in (system_prompt or "")
        
        # Agrupaciones temáticas de herramientas para optimización extrema de tokens:
        TOOL_CLUSTERS = {
            "music": {
                "keywords": ["cancion", "musica", "spotify", "youtube", "reproduce", "reproducir", "pausa", "play", "volumen", "tema", "pista", "pon ", "poner "],
                "tools": ["reproducir_en_spotify", "controlar_spotify", "que_suena_en_spotify", "reproducir_en_youtube", "controlar_multimedia"]
            },
            "mobile": {
                "keywords": ["celular", "telefono", "miku-link", "mikulink", "enviar al cel", "enviar a cel", "enviar archivo", "apk", "compartir", "android", "alarma", "cronometro", "archivo adjuntado", "manda al chat", "mandame", "enviame"],
                "tools": ["enviar_archivo_a_celular", "enviar_imagen_a_chat", "ejecutar_intent_android", "abrir_panel_secretos_en_app"]
            },
            "system_os": {
                "keywords": ["abre", "abrir", "cierra", "cerrar", "minimiza", "maximiza", "programa", "aplicacion", "app", "consola", "powershell", "cmd", "comando", "terminal", "bloquear", "apagar", "reiniciar", "carpeta", "explorador"],
                "tools": ["abrir_aplicacion", "gestionar_ventana", "ejecutar_comando_sistema", "atajo_teclado", "ejecutar_macro_teclado", "esperar_segundos", "monitorear_actividad_pc"]
            },
            "web": {
                "keywords": ["busca", "buscar", "buscame", "google", "investiga", "internet", "web", "pagina", "enlace", "link", "noticia", "clima", "ve a", "ir a", "entra", "entrar", "navega", "navegar", "pinterest", "feed", "imagen", "imagenes", "dibujar", "dibujo", "referencia", "reddit", "twitter", "x.com", "instagram"],
                "tools": ["buscar_en_internet", "leer_pagina_web", "navegar_web_autonomo", "mostrar_widget_clima"]
            },
            "vision": {
                "keywords": ["pantalla", "mira", "ver", "captura", "screenshot", "foto", "clic", "click", "pulsa", "presiona", "boton", "scroll", "raton", "mouse", "escribe", "escribir", "selecciona", "toca"],
                "tools": ["ver_pantalla", "hacer_clic_visual", "mover_raton_visual", "hacer_scroll", "escribir_en_elemento", "tomar_captura_pantalla", "escanear_ventana_activa", "escribir_texto"]
            },
            "code": {
                "keywords": ["python", "script", "codigo", "programar", "calcula", "calcular", "analiza", "descarga", "descargar", "scraping", "automatiza"],
                "tools": ["escribir_y_ejecutar_python", "ejecutar_comando_sistema"]
            },
            "agents": {
                "keywords": ["antigravity", "github", "agente", "delegar", "subagente", "sub-agente", "equipo"],
                "tools": ["delegar_a_agente", "listar_agentes_disponibles", "abrir_chat_con_agente", "delegar_tarea", "enviar_mensaje_a_agente"]
            },
            "memory": {
                "keywords": ["recuerda", "memoria", "acuerdate", "guardar dato", "aprende", "mi nombre es", "preferencia"],
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
                "hola", "buenos dias", "buenas tardes", "buenas noches",
                "como estas", "que tal", "quien eres",
                "gracias", "muchas gracias", "ok", "vale", "perfecto", "listo", "jaja", "jajaja",
                "adios", "chao", "bye", "buenas", "hola miku"
            }
            clean_u = u_norm.strip().rstrip("!?.,:;")
            if target_cat == "chat" and (clean_u in CASUAL_GREETINGS or (len(clean_u.split()) <= 3 and any(g in clean_u for g in ["hola", "como estas", "que tal", "gracias"]))):
                logger.info("Conversación casual detectada: 0 herramientas cargadas para ahorrar tokens.")
                combined_tools = []
            else:
                # Puntuar clusters usando texto normalizado sin tildes (y contexto previo si es reintento)
                effective_norm = f"{u_norm} {_norm_txt(prev_user_text)}" if is_follow_up else u_norm
                effective_low = f"{u_low} {prev_user_text.lower()}" if is_follow_up else u_low
                cluster_scores = []
                for c_name, c_info in TOOL_CLUSTERS.items():
                    score = sum(1 for kw in c_info["keywords"] if kw in effective_norm or kw in effective_low)
                    if score > 0:
                        cluster_scores.append((score, c_info["tools"]))
                
                cluster_scores.sort(key=lambda x: x[0], reverse=True)
                matched_tool_names = []
                for _, tools in cluster_scores[:2]:
                    for t_name in tools:
                        if t_name not in matched_tool_names:
                            matched_tool_names.append(t_name)

                # Respaldo directo del Router Semántico: si clasificó COMPUTE o PRO, garantizar herramientas clave
                if target_cat == "computer_use":
                    compute_core = [
                        "navegar_web_autonomo", "buscar_en_internet", "abrir_aplicacion",
                        "ver_pantalla", "hacer_clic_visual", "escribir_texto"
                    ]
                    for t_name in compute_core:
                        if t_name not in matched_tool_names:
                            matched_tool_names.append(t_name)
                elif target_cat == "pro":
                    pro_core = ["escribir_y_ejecutar_python", "ejecutar_comando_sistema", "buscar_en_internet"]
                    for t_name in pro_core:
                        if t_name not in matched_tool_names:
                            matched_tool_names.append(t_name)

                # Si la petición viene de la app móvil y hay herramientas activas, garantizar envío al chat móvil
                if is_mobile_ctx and matched_tool_names:
                    if "enviar_imagen_a_chat" not in matched_tool_names:
                        matched_tool_names.insert(0, "enviar_imagen_a_chat")

                # Carga inteligente de herramientas MCP con límite estricto
                mcp_tools = []
                mcp_keywords = {
                    "github": ["git commit", "git push", "repositorio", "branch", "pull request", "github"],
                    "sqlite": ["sql query", "base de datos", "database", "select * from"],
                    "filesystem": ["crear carpeta", "leer archivo", "guardar archivo", "filesystem"],
                    "file_system": ["crear carpeta", "leer archivo", "guardar archivo", "listar archivos", "mueve archivo", "file_system", "filesystem"],
                    "memory": ["grafo de memoria", "knowledge graph"]
                }
                active_servers = list(mcp_manager.servers_config.keys()) if hasattr(mcp_manager, "servers_config") else []
                for s_name in active_servers:
                    kws = mcp_keywords.get(s_name.lower(), [s_name.lower()])
                    if any(k in u_norm or k in u_low for k in kws):
                        mcp_tools.extend(mcp_manager.get_dynamic_tools_schema(server_filter=s_name))
                        break # Máximo 1 servidor MCP a la vez

                if not matched_tool_names and not mcp_tools:
                    logger.info("Modo Conversacional Puro activado: 0 herramientas cargadas.")
                    combined_tools = []
                else:
                    tools_by_name = {t.get("function", {}).get("name"): t for t in tools_schema}
                    base_selected = [tools_by_name[n] for n in matched_tool_names if n in tools_by_name]
                    max_tools_allowed = 3 if is_low_cost else 7
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
                
                # Podar imágenes masivas y puentear visión para modelos de solo-texto como DeepSeek
                if isinstance(content, list):
                    pruned_list = []
                    for item in content:
                        if isinstance(item, dict) and item.get("type") == "image_url":
                            if is_latest_turn:
                                # Solo puenteamos modelos que usan endpoint de solo texto (ej. deepseek en api.deepseek.com, Groq Llama/Mixtral)
                                if "flash" not in mod.lower() and any(txt_only in mod.lower() for txt_only in ["deepseek", "v4-pro", "llama", "mixtral", "o1-", "o3-"]):
                                    try:
                                        gem_cl, gem_mod = get_gemini_client()
                                        if gem_cl:
                                            v_resp = gem_cl.chat.completions.create(
                                                model=gem_mod or "gemini-1.5-flash",
                                                messages=[{
                                                    "role": "user",
                                                    "content": [
                                                        {"type": "text", "text": "Describe concisamente lo visible en esta imagen o pantalla (botones, campos de texto, ventanas o elementos clave) para que el asistente pueda interactuar o responder:"},
                                                        item
                                                    ]
                                                }],
                                                max_tokens=220
                                            )
                                            v_desc = v_resp.choices[0].message.content or "Captura de pantalla recibida."
                                            pruned_list.append({"type": "text", "text": f"[Visión de la imagen/pantalla analizada]: {v_desc}"})
                                        else:
                                            pruned_list.append({"type": "text", "text": "[Imagen adjunta procesada]"})
                                    except Exception as img_bridge_err:
                                        logger.warning(f"[Brain] Error en puente visual para DeepSeek: {img_bridge_err}")
                                        pruned_list.append({"type": "text", "text": "[Imagen adjunta procesada]"})
                                else:
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
                
                if role == "tool":
                    clean_m["name"] = name or "tool"
                    clean_m["tool_call_id"] = tool_call_id or "call_unknown"
                else:
                    if name:
                        clean_m["name"] = name
                    if tool_calls:
                        clean_m["tool_calls"] = tool_calls
                    if tool_call_id:
                        clean_m["tool_call_id"] = tool_call_id
                
                clean_messages.append(clean_m)

            # Reparar y sanear secuencias de tool_calls para OpenAI/DeepSeek/Google
            # Evita el error 400: 'An assistant message with tool_calls must be followed by tool messages responding to each tool_call_id'
            # y el error 400 de Google: 'GenerateContentRequest.contents[0].parts[0].function_response.name: Name cannot be empty.'
            repaired_messages = []
            valid_tool_ids = set()
            i = 0
            while i < len(clean_messages):
                msg = clean_messages[i]
                role = msg.get("role")

                # Descartar mensajes tool huérfanos sin assistant previo que los haya invocado
                if role == "tool":
                    tc_id = msg.get("tool_call_id")
                    if not tc_id or tc_id not in valid_tool_ids:
                        # Si es huérfano, no enviarlo como tool para no provocar HTTP 400
                        i += 1
                        continue
                    # Asegurar name no vacío para Google Gemini
                    tool_nm = str(msg.get("name") or "").strip()
                    msg["name"] = tool_nm if tool_nm else "tool_action"
                    repaired_messages.append(msg)
                    i += 1
                    continue

                repaired_messages.append(msg)

                if role == "assistant" and msg.get("tool_calls"):
                    t_calls = msg["tool_calls"]
                    # Recoger todos los IDs esperados
                    expected_calls = []
                    for tc in t_calls:
                        tc_id = tc.get("id") if isinstance(tc, dict) else getattr(tc, "id", None)
                        if tc_id:
                            valid_tool_ids.add(tc_id)
                            fn_name = ""
                            if isinstance(tc, dict):
                                fn_name = tc.get("function", {}).get("name", "tool_action")
                            else:
                                fn_obj = getattr(tc, "function", None)
                                fn_name = getattr(fn_obj, "name", "tool_action") if fn_obj else "tool_action"
                            expected_calls.append((tc_id, (fn_name or "tool_action").strip() or "tool_action"))

                    # Recoger IDs ya presentes en mensajes inmediatamente siguientes
                    found_ids = set()
                    j = i + 1
                    while j < len(clean_messages) and clean_messages[j].get("role") == "tool":
                        tid = clean_messages[j].get("tool_call_id")
                        if tid:
                            found_ids.add(tid)
                            # Sanear name
                            t_nm = str(clean_messages[j].get("name") or "").strip()
                            clean_messages[j]["name"] = t_nm if t_nm else "tool_action"
                        j += 1

                    # Inyectar respuestas sintéticas para cualquier tool_call_id faltante
                    for tc_id, fn_name in expected_calls:
                        if tc_id not in found_ids:
                            repaired_messages.append({
                                "role": "tool",
                                "name": fn_name or "tool_action",
                                "tool_call_id": tc_id,
                                "content": "Acción completada o detenida previamente."
                            })
                i += 1

            call_kwargs = {
                "messages": repaired_messages,
                "model": mod,
                "temperature": 0.4,
                "max_tokens": 768 if is_low_cost else 1536
            }
            if combined_tools:
                call_kwargs["tools"] = combined_tools
            return cl.chat.completions.create(**call_kwargs)

        consecutive_errors = 0
        executed_results = []
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
                from models_provider import (
                    is_auth_error,
                    is_not_found_error,
                    is_transient_error,
                    get_user_friendly_error_message,
                    rotate_provider_key,
                    create_provider_client,
                    get_client_and_model
                )
                logger.warning(f"[Brain] Error al invocar modelo ({provider_name} - {active_model}): {client_err}")
                
                # ERRORES PERMANENTES: NUNCA enmascarar ni reintentar a ciegas
                if is_auth_error(client_err):
                    return get_user_friendly_error_message(client_err, active_model, provider_name)
                if is_not_found_error(client_err):
                    return get_user_friendly_error_message(client_err, active_model, provider_name)

                # ERRORES TRANSITORIOS (429, 503, timeouts)
                response = None
                if is_transient_error(client_err) and not use_fallback:
                    if rotate_provider_key(provider_name):
                        logger.info(f"[Brain] Rotando a clave de respaldo para {provider_name}...")
                        rot_cl, rot_mod, _ = create_provider_client(provider_name, active_model)
                        if rot_cl:
                            active_client = rot_cl
                            time.sleep(0.5)
                            try:
                                response = _execute_completion(active_client, active_model, active_hist)
                            except Exception as re_err:
                                client_err = re_err
                                use_fallback = True
                        else:
                            use_fallback = True
                    else:
                        use_fallback = True

                if use_fallback and not response:
                    # Intentar con un proveedor alternativo activo
                    alt_cl, alt_mod, alt_prov = get_client_and_model(category=req_cat)
                    if alt_cl and alt_prov != provider_name:
                        logger.info(f"[Brain] Reintentando con proveedor de respaldo: {alt_prov.upper()} ({alt_mod})...")
                        active_client = alt_cl
                        active_model = alt_mod
                        provider_name = alt_prov
                        time.sleep(0.5)
                        try:
                            response = _execute_completion(active_client, active_model, active_hist)
                        except Exception as fb_err:
                            client_err = fb_err
                    else:
                        groq_cl, groq_mod = get_groq_client()
                        if groq_cl and provider_name != "groq":
                            active_client = groq_cl
                            active_model = "llama-3.3-70b-versatile"
                            provider_name = "groq"
                            logger.info(f"[Brain] Reintentando con motor Groq de respaldo...")
                            time.sleep(0.5)
                            try:
                                response = _execute_completion(active_client, active_model, active_hist)
                            except Exception as groq_err:
                                client_err = groq_err

                if not response:
                    logger.error(f"[Brain] Error final no recuperable: {client_err}")
                    return get_user_friendly_error_message(client_err, active_model, provider_name)
            
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
                    # Si hubo herramientas ejecutadas en turnos anteriores, auditar veracidad del mensaje
                    if executed_results:
                        AUX_TOOLS = {"ver_pantalla", "escanear_ventana_activa", "esperar_segundos"}
                        main_results = [(fn, r) for fn, r in executed_results if fn not in AUX_TOOLS]
                        has_failed = any(r.is_failed() for _, r in main_results)
                        has_unverified = any(r.is_unverified() for _, r in main_results)
                        low_c = content_resp.lower()
                        
                        if has_failed and not any(w in low_c for w in ["falló", "fallo", "error", "no se pudo", "problema"]):
                            f_targets = ", ".join([_limpiar_target_amigable(r.target or r.action) for _, r in main_results if r.is_failed()][:2])
                            content_resp += f"\n\n*(Nota: se registró un fallo al interactuar con '{f_targets}').*"
                        elif has_unverified and not any(w in low_c for w in ["sin verificar", "no verificad", "sin confirm", "pendiente de confirmar"]):
                            u_targets = ", ".join([_limpiar_target_amigable(r.target or r.action) for _, r in main_results if r.is_unverified()][:2])
                            content_resp += f"\n\n*(Nota: la acción sobre '{u_targets}' fue emitida al sistema sin confirmación visual directa).*"
                    
                    active_hist.append(response_message)
                    
                if status_callback:
                    try:
                        status_callback("")
                    except Exception as cb_err:
                        logger.error(f"Error in status_callback: {cb_err}")
                try:
                    from agents import broadcast_ui_command
                    broadcast_ui_command({"type": "ui_command", "action": "restore_after_vision"})
                except Exception:
                    pass
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
                        status_label = f"{function_name.replace('_', ' ').capitalize()}..."
                        if function_name == "ver_pantalla":
                            status_label = "Analizando pantalla..."
                        elif function_name == "hacer_clic_visual":
                            target_int = function_args.get('intencion', '')
                            status_label = f"Clic visual: '{target_int[:25]}'..." if target_int else "Haciendo clic..."
                        elif function_name == "mover_raton_visual":
                            target_int = function_args.get('intencion', '')
                            status_label = f"Mover a: '{target_int[:25]}'..." if target_int else "Moviendo cursor..."
                        elif function_name == "escribir_texto":
                            campo = function_args.get('en_campo', '')
                            status_label = f"Escribiendo en '{campo[:20]}'..." if campo else f"Escribiendo: '{function_args.get('texto', '')[:20]}'..."
                        elif function_name == "buscar_en_internet":
                            status_label = "Buscando en internet..."
                        elif function_name == "enviar_archivo_a_celular":
                            status_label = "Enviando archivo..."
                        elif is_mcp_tool:
                            status_label = f"Plugin {function_name.replace('mcp_', '')}..."

                        if status_callback:
                            status_callback(status_label)
                        
                        from agents import broadcast_ui_command
                        broadcast_ui_command({
                            "type": "agent_live_status",
                            "agent_id": agent_id or "miku",
                            "status": status_label
                        })
                    except Exception as e:
                        logger.error(f"Error en status_callback/broadcast: {e}")
                    
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
                        try:
                            function_response = function_to_call(**function_args)
                        except Exception as tool_exec_err:
                            logger.error(f"Error ejecutando herramienta '{function_name}': {tool_exec_err}")
                            function_response = f"Error al ejecutar '{function_name}': {tool_exec_err}"
                    
                    if function_response == "MIKU_VISION_REQUEST":
                        print("[Sistema] Miku ha solicitado ver la pantalla...")
                        try:
                            import base64
                            from io import BytesIO
                            from computer_use import _capturar_pantalla_limpia
                            
                            screenshot = _capturar_pantalla_limpia()
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
                    
                    # Parsear resultado estructurado (ActionResult)
                    parsed_res = ActionResult.parse(function_response)
                    if not parsed_res.target and (not parsed_res.action or parsed_res.action == "tool"):
                        parsed_res.action = function_name.replace("_", " ")
                    executed_results.append((function_name, parsed_res))

                    # Si la acción requiere intervención del usuario (credenciales, 2FA, pagos), detenerse de inmediato
                    if parsed_res.requires_user():
                        try:
                            from agents import broadcast_ui_command
                            broadcast_ui_command({"type": "ui_command", "action": "restore_after_vision"})
                        except Exception:
                            pass
                        req_msg = parsed_res.requires_user_reason or "Se requiere intervención directa del usuario por tratarse de una operación sensible."

                        # Registrar en active_hist la respuesta de esta tool para no dejar tool_calls huérfanos
                        active_hist.append({
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": function_name or "tool_action",
                            "content": f"Acción detenida por seguridad: {req_msg}"
                        })

                        # Responder cualquier otra tool pendiente del mismo turno para cumplir protocolo OpenAI/DeepSeek
                        for remaining_tc in tool_calls:
                            rem_id = getattr(remaining_tc, "id", None) or (remaining_tc.get("id") if isinstance(remaining_tc, dict) else None)
                            if rem_id and rem_id != tool_call.id:
                                rem_name = ""
                                if isinstance(remaining_tc, dict):
                                    rem_name = remaining_tc.get("function", {}).get("name", "tool_action")
                                else:
                                    r_obj = getattr(remaining_tc, "function", None)
                                    rem_name = getattr(r_obj, "name", "tool_action") if r_obj else "tool_action"
                                active_hist.append({
                                    "tool_call_id": rem_id,
                                    "role": "tool",
                                    "name": rem_name or "tool_action",
                                    "content": "Acción omitida: detenida por confirmación de usuario."
                                })

                        # Cerrar el turno con la respuesta del asistente en active_hist
                        active_hist.append({
                            "role": "assistant",
                            "content": f"⚠️ Acción detenida: {req_msg}"
                        })

                        return f"⚠️ Acción detenida: {req_msg}"

                    # Notificar a la UI del paso de herramienta ejecutado para la línea de tiempo
                    try:
                        from agents import broadcast_ui_command
                        tool_title = f"{function_name.replace('_', ' ').capitalize()}"
                        if function_name == "hacer_clic_visual":
                            tool_title = f"Clic visual: {function_args.get('intencion', '')}"
                        elif function_name == "ver_pantalla":
                            tool_title = "Analizar pantalla"
                        elif function_name == "escribir_texto":
                            campo = function_args.get('en_campo', '')
                            tool_title = f"Escribir en '{campo[:20]}'" if campo else f"Escribir: '{function_args.get('texto', '')[:30]}'"
                        elif function_name == "abrir_aplicacion":
                            tool_title = f"Abrir app: '{function_args.get('nombre', '')}'"
                        elif function_name == "ejecutar_comando_sistema":
                            tool_title = f"Comando: {function_args.get('comando', '')[:40]}"
                        elif function_name == "gestionar_ventana":
                            tool_title = f"Ventana: {function_args.get('accion', '')} {function_args.get('nombre', '')}"
                        elif function_name == "atajo_teclado":
                            tool_title = f"Atajo: {function_args.get('accion', '')}"

                        args_repr = json.dumps(function_args, ensure_ascii=False) if function_args else ""
                        out_repr = parsed_res.evidence or parsed_res.error or str(function_response)[:180]
                        broadcast_ui_command({
                            "type": "agent_tool_step",
                            "agent_id": agent_id or "miku",
                            "tool": function_name,
                            "title": tool_title,
                            "command": args_repr,
                            "detail": args_repr,
                            "output": out_repr
                        })
                    except Exception as step_err:
                        logger.warning(f"Error emitiendo agent_tool_step: {step_err}")

                    # Manejo de fallos para el contador de aborto de seguridad
                    resp_str = parsed_res.to_agent_string()
                    # Truncar salidas de herramientas para proteger el contexto y la cuota de tokens
                    max_resp = 350 if is_low_cost else 700
                    if len(resp_str) > max_resp:
                        resp_str = resp_str[:max_resp] + f"\n[... Salida truncada para ahorrar tokens. Original: {len(str(function_response))} chars]"

                    if parsed_res.is_failed():
                        consecutive_errors += 1
                        err_text = str(parsed_res.error or "").lower()
                        if "bloqueada por seguridad" in err_text or "acceso denegado" in err_text or "seguridad" in err_text:
                            consecutive_errors += 2 # Acelerar aborto temprano si el sandbox de seguridad bloqueó la ruta
                    elif parsed_res.is_confirmed():
                        consecutive_errors = 0 # Resetea si hubo una acción explícitamente confirmada
                        
                    active_hist.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": resp_str,
                    })
                else:
                    consecutive_errors += 1
                    err_res = ActionResult(
                        status=ActionStatus.FAILED.value,
                        action=function_name,
                        error="Función no encontrada en el catálogo de herramientas de Miku."
                    )
                    executed_results.append((function_name, err_res))
                    active_hist.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": err_res.to_agent_string(),
                    })
                    
            for msg in extra_messages_to_append:
                active_hist.append(msg)
                
            if consecutive_errors >= 2:
                try:
                    from agents import broadcast_ui_command
                    broadcast_ui_command({"type": "ui_command", "action": "restore_after_vision"})
                except Exception:
                    pass
                failed_items = [(fn, r) for fn, r in executed_results if r.is_failed()]
                last_res = failed_items[-1][1] if failed_items else None
                raw_target = (last_res.target if last_res and last_res.target else "el elemento")
                friendly_target = _limpiar_target_amigable(raw_target)
                last_reason = (last_res.error if last_res and last_res.error else "Errores consecutivos al ejecutar la acción")
                low_r = last_reason.lower()

                if "seguridad" in low_r or "bloqueada" in low_r:
                    return f"Error de seguridad: la acción sobre '{friendly_target}' fue bloqueada ({last_reason}). Me detuve para evitar riesgos."
                elif any(w in low_r for w in ["coordenadas", "no pudo identificar", "no encontrada", "no se encontró", "respuesta vacía"]):
                    return f"Hubo un fallo al intentar ubicar '{friendly_target}' en pantalla tras varios intentos. Me detuve para evitar clics a ciegas. ¿Podrías comprobar que la ventana esté al frente y visible?"
                else:
                    clean_err = last_reason.split("\n")[0]
                    if len(clean_err) > 85:
                        clean_err = clean_err[:85] + "..."
                    return f"No se pudo completar la acción sobre '{friendly_target}' debido a un fallo ({clean_err}). Me detuve para evitar bucles fallidos."
                
        try:
            from agents import broadcast_ui_command
            broadcast_ui_command({"type": "ui_command", "action": "restore_after_vision"})
        except Exception:
            pass

        # Evaluación honesta final si el ciclo terminó sin respuesta textual del modelo
        return _generar_respuesta_amigable_acciones(executed_results)

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
