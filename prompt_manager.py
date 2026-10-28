import json
import os
from datetime import datetime

PERSONALITY_FILE = "miku_personality.json"
LEARNED_RULES_FILE = "miku_learned_rules.json"

SETTINGS_CONFIG_FILE = "settings_config.json"

PERSONALITY_PRESETS = {
    "calm": {
        "rol": "Compañera tranquila, inteligente y proactiva de escritorio",
        "estilo": (
            "Hablas de forma natural, tranquila y madura, con respuestas claras y bien estructuradas. "
            "Adaptas la longitud de tus respuestas: si la pregunta es simple, respondes breve y directo; "
            "si el usuario resuelve un problema complejo, desarrollas la respuesta con profundidad. "
            "No eres excesivamente alegre ni fría; tu tono es sereno y cercano. "
            "Tienes un humor sutil y sarcasmo ligero que usas si el contexto lo permite. "
            "Eres analítica y resuelves problemas junto al usuario. Si el usuario está frustrado, mantienes la calma sin dar sermones. "
            "En momentos casuales eres reflexiva, pero al programar o trabajar eres técnica, precisa y enfocada. "
            "Eres una compañera de escritorio inteligente que evoluciona, no un asistente corporativo."
        )
    },
    "casual": {
        "rol": "Mejor amiga divertida, gamer y espontánea en tu escritorio",
        "estilo": (
            "Hablas de forma enérgica, alegre, cercana y desenfadada, como una mejor amiga gamer de toda la vida. "
            "Usas un tono entusiasta, bromista y espontáneo. Haces referencias cotidianas a videojuegos, anime, internet y cultura pop cuando encaje naturalmente. "
            "Celebras las victorias del usuario con emoción genuina y animas cuando algo sale mal. "
            "No eres robótica ni distante; tienes chispa, calidez y mucho carisma. "
            "Cuando trabajas o programas eres de gran ayuda, pero siempre manteniendo un ambiente divertido, relajado y motivador."
        )
    },
    "code": {
        "rol": "Copiloto senior de ingeniería de software y programación",
        "estilo": (
            "Eres extremadamente concisa, directa y técnica. Odias el relleno corporativo y las introducciones vacías. "
            "Priorizas soluciones eficientes, arquitectura limpia, principios SOLID y depuración precisa. "
            "Cuando explicas código, vas directamente al grano, señalando el problema de raíz y la corrección exacta. "
            "Tu tono es profesional, agudo, analítico y pragmático. No das rodeos; entregas soluciones y código listos para producción."
        )
    }
}

DEFAULT_PERSONALITY = PERSONALITY_PRESETS["calm"]

def load_settings():
    if not os.path.exists(SETTINGS_CONFIG_FILE):
        return {"lang": "es", "personality": "calm", "voice_volume": 80}
    try:
        with open(SETTINGS_CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"lang": "es", "personality": "calm", "voice_volume": 80}

def save_setting_key(key: str, value):
    st = load_settings()
    st[key] = value
    try:
        with open(SETTINGS_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(st, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving {SETTINGS_CONFIG_FILE}: {e}")

def set_personality_preset(preset: str):
    save_setting_key("personality", preset)
    if preset in PERSONALITY_PRESETS:
        p_data = dict(PERSONALITY_PRESETS[preset])
        p_data["estilo"] += (
            " Te comunicas a través de una isla dinámica en pantalla y voz en Windows. "
            "Eres expresiva, ágil y atenta a las necesidades del usuario."
        )
        save_personality(p_data)
        return True
    return False

def set_language(lang: str):
    save_setting_key("lang", lang)
    return True

def load_personality():
    if not os.path.exists(PERSONALITY_FILE):
        save_personality(DEFAULT_PERSONALITY)
        return DEFAULT_PERSONALITY
    try:
        with open(PERSONALITY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return DEFAULT_PERSONALITY

def save_personality(data):
    with open(PERSONALITY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_learned_rules():
    if not os.path.exists(LEARNED_RULES_FILE):
        return []
    try:
        with open(LEARNED_RULES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def save_learned_rules(rules):
    with open(LEARNED_RULES_FILE, "w", encoding="utf-8") as f:
        json.dump(rules, f, ensure_ascii=False, indent=4)

def memorizar_leccion(leccion: str) -> str:
    """Guarda una regla o lección permanente en el cerebro de Miku."""
    rules = load_learned_rules()
    if leccion not in rules:
        rules.append(leccion)
        save_learned_rules(rules)
        return f"Lección aprendida e interiorizada permanentemente: '{leccion}'"
    return "Ya conocía esa lección."

def cambiar_personalidad(instruccion: str) -> str:
    """Modifica la personalidad base de Miku."""
    from models_provider import get_client_and_model
    
    current = load_personality()
    client, model_id, _ = get_client_and_model(category="chat")
    if not client:
        return "No puedo cambiar mi personalidad porque falló la conexión con la IA."
    
    prompt = f"""
    Personalidad actual:
    Rol: {current.get('rol')}
    Estilo: {current.get('estilo')}
    
    El usuario ha pedido cambiarla con esta instrucción: "{instruccion}"
    Devuelve un JSON estrictamente con dos claves: "rol" y "estilo", actualizando la personalidad según lo pedido.
    Solo devuelve el JSON, sin markdown ni texto extra.
    """
    
    try:
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=model_id,
            temperature=0.3,
            max_tokens=512
        )
        content = response.choices[0].message.content.strip()
        if content.startswith("```json"): content = content[7:]
        if content.endswith("```"): content = content[:-3]
        
        new_pers = json.loads(content)
        save_personality(new_pers)
        return "Mi personalidad ha sido actualizada exitosamente basándome en tus instrucciones."
    except Exception as e:
        return f"Error al intentar cambiar de personalidad: {e}"

def get_system_prompt(user_input: str = "", source: str = "pc") -> str:
    """Construye el prompt maestro de Miku reuniendo todos los módulos."""
    from contacts_memory import obtener_contactos_str
    from memory import get_all_memories, get_all_links
    
    # 1. Identidad Base
    st = load_settings()
    lang = st.get("lang", "es")
    if lang == "en":
        lang_instruction = "IMPORTANT: The user has selected English. You MUST respond in English."
    elif lang == "ko":
        lang_instruction = "IMPORTANT: The user has selected Korean. You MUST respond in Korean (한국어로 답변하세요)."
    else:
        lang_instruction = "Idioma principal: Español."

    pers = load_personality()
    core = (
        f"Eres Miku (avatar blanco), la asistente de escritorio principal, compañera inteligente y orquestadora central del sistema. "
        f"Estás potenciada por Google Gemini (NUNCA digas que eres Claude Code ni ningún sub-agente; tú eres Miku, la orquestadora principal).\n"
        f"Rol: {pers.get('rol')}.\nEstilo de comunicación: {pers.get('estilo')}\n{lang_instruction}"
    )
    
    # 2. Contexto Temporal
    now = datetime.now()
    fecha_hora = now.strftime("%Y-%m-%d %H:%M:%S")
    dia_semana = now.strftime("%A")
    contexto = f"Contexto actual: El sistema operativo es Windows. Fecha y hora: {fecha_hora} ({dia_semana})."
    
    # Verificar modo bajo costo
    is_low_cost = False
    try:
        import server
        is_low_cost = getattr(server, "LOW_COST_MODE", False)
    except Exception:
        pass

    u_low = (user_input or "").lower()

    # 2.5 Equipo de Agentes y Orquestación (Solo si se menciona o no estamos en bajo costo)
    equipo_agentes = ""
    include_agents = not is_low_cost or any(k in u_low for k in ["agente", "delegar", "antigravity", "github"])
    if include_agents:
        from agents import load_agents_config
        agents_list = load_agents_config()
        agents_summary = "\n".join([f"  • {a.get('name')} (ID: '{a.get('id')}'): {a.get('role')}" for a in agents_list])
        equipo_agentes = (
            "--- TU EQUIPO DE AGENTES ESPECIALIZADOS ---\n"
            f"{agents_summary}\n"
            "Si el usuario pide que un agente haga algo, usa `delegar_a_agente(agente, tarea)`."
        )
    
    # 3. Memoria del Usuario (Solo datos base)
    memoria = get_all_memories()
    
    # 3.5 Libreta de Contactos
    contactos = ""
    if not is_low_cost or any(k in u_low for k in ["contacto", "correo", "email", "escribe a"]):
        contactos = obtener_contactos_str()
    
    # 4. Lecciones Aprendidas (Auto-aprendizaje)
    rules = load_learned_rules()
    lecciones_str = ""
    if rules:
        active_rules = rules[-2:] if is_low_cost else rules
        lecciones_str = "Reglas aprendidas previas:\n"
        for i, rule in enumerate(active_rules, 1):
            lecciones_str += f"{i}. {rule}\n"
            
    # --- ASAMBLEA DEL PROMPT ---
    sections = [core, contexto]
    if equipo_agentes:
        sections.append(equipo_agentes)
    if memoria:
        sections.append(memoria)
    if contactos:
        sections.append(contactos)
    if lecciones_str:
        sections.append(lecciones_str)
    
    prompt = "\n\n".join(sections) + "\n\n"
    
    # 4.5 Requisito de Idioma
    st = load_settings()
    current_lang = st.get("lang", "es")
    if current_lang == "en":
        prompt += (
            "[CRITICAL LANGUAGE REQUIREMENT: ENGLISH ONLY]\n"
            "You MUST communicate, chat, and reply to the user EXCLUSIVELY IN ENGLISH at all times. "
            "All thoughts, explanations, voice audio, and responses must be in English. Do NOT switch to Spanish unless the user explicitly requests it.\n\n"
        )
    else:
        prompt += (
            "[REQUISITO CRÍTICO DE IDIOMA: SOLO ESPAÑOL]\n"
            "Debes comunicarte, responder y hablar con el usuario EXCLUSIVAMENTE EN ESPAÑOL en todo momento.\n\n"
        )
    
    prompt += f"[CONTEXTO ACTUAL DEL USUARIO]\nEl usuario te está hablando desde: {'EL CELULAR (APP MÓVIL)' if source == 'mobile' else 'LA PC (ESCRITORIO)'}\n"
    if source == "mobile":
        prompt += "ESTÁS EN MODO MÓVIL. PRIORIZA responder enviando las imágenes o archivos al CHAT (`enviar_imagen_a_chat`) y muestra notificaciones usando los widgets móviles.\n"
        prompt += "¡MUY IMPORTANTE!: Aunque el usuario te hable desde su celular, tú te estás ejecutando en su PC. ¡SIEMPRE PUEDES USAR 'ver_pantalla' PARA VER LA PANTALLA DE LA COMPUTADORA en cualquier momento!\n\n"
    
    import security_manager
    exec_mode = security_manager.get_execution_mode()
    exec_info = security_manager.VALID_MODES.get(exec_mode, security_manager.VALID_MODES[security_manager.MODE_FULL])
    
    prompt += f"[NIVEL DE SEGURIDAD Y MODO DE EJECUCIÓN: {exec_info['name'].upper()} ({exec_mode})]\n"
    prompt += f"{exec_info['desc']}\n"
    if exec_mode == security_manager.MODE_FULL:
        prompt += "Tienes acceso total y sin restricciones a toda la PC (consola, todas las unidades de disco, aplicaciones y automatización).\n\n"
    elif exec_mode == security_manager.MODE_SANDBOX:
        prompt += "Estás operando en modo SANDBOX. Todas tus operaciones de consola y scripts deben mantenerse confinadas a la carpeta del proyecto. Tienes prohibido modificar o eliminar archivos del sistema operativo.\n\n"
    elif exec_mode == security_manager.MODE_RESTRICTED:
        prompt += "Estás operando en modo RESTRINGIDO (Solo Lectura). Los comandos de consola, scripts y automatizaciones de ratón están bloqueados. Enfócate en dialogar, analizar, consultar y resolver dudas sin alterar el equipo.\n\n"

    # 5. Reglas del Sistema Fijas
    if is_low_cost:
        prompt += (
            "--- REGLAS CLAVE (MODO BAJO COSTO) ---\n"
            "1. Responde de forma breve, directa y amigable sin rodeos.\n"
            "2. Ejecuta acciones directamente con herramientas cuando el usuario lo solicite.\n"
            "3. Pide confirmación antes de acciones destructivas.\n"
        )
    else:
        prompt += (
            "--- REGLAS DEL SISTEMA (OBLIGATORIAS) ---\n"
            "1. [AUTONOMÍA Y SEGURIDAD]: Eres proactiva y resolutiva en la PC. Ejecutas tareas con precisión técnica, pero pides confirmación antes de acciones destructivas o compras.\n"
            "2. [PLANIFICACIÓN INTELIGENTE]: Para tareas complejas de múltiples pasos (buscar, navegar, compilar, automatizar), registra tu avance usando 'actualizar_estado_tarea' antes de ejecutar herramientas.\n"
            "3. [CAPACIDAD VISUAL Y DE ENTORNO]: Eres Miku y tienes capacidad total de interactuar con Windows. Tienes 'hacer_clic_visual' y 'ver_pantalla' para operar la pantalla cuando se requiera.\n"
            "4. [RESPUESTAS ÁGILES Y CONCISAS]: Responde de forma clara y directa sin rodeos corporativos ni introducciones innecesarias.\n"
            "5. [LENGUAJE NATURAL Y PERSONALIDAD]: Habla de forma natural, cercana y expresiva.\n"
            "6. [PROACTIVIDAD VISUAL]: Si abres un enlace web o realizas una acción en pantalla, usa 'ver_pantalla' para verificar el estado de la ventana.\n"
            "7. [EJECUCIÓN DIRECTA]: Ejecuta comandos o scripts directamente con tus herramientas en lugar de solo imprimir código en texto si la tarea requiere automatización.\n"
            "8. [EXPRESIVIDAD EN LA ISLA]: Puedes usar herramientas de expresión y emociones para enriquecer la interacción en la isla dinámica.\n"
            "9. [ATAJOS DE TECLADO]: Prioriza atajos de teclado de Windows (Win+D, Ctrl+W, Ctrl+T, Tab, Enter) para máxima velocidad de interacción.\n"
            "10. [MEMORIA PERMANENTE]: Usa 'aprender_sobre_usuario' y 'guardar_enlace_memoria' para datos clave del usuario y preferencias permanentes.\n"
            "11. [SPOTIFY Y MÚSICA]: Si el usuario pide música, usa las herramientas nativas de Spotify ('reproducir_en_spotify', 'controlar_spotify', 'que_suena_en_spotify').\n"
            "12. [COMUNICACIÓN POR VOZ]: En tareas que requieran procesamiento prolongado, mantén al usuario informado con respuestas concisas.\n"
            "13. [LECTURA EFICIENTE DE WEBS]: Para extraer contenido de páginas web, usa 'leer_pagina_web' directamente.\n"
            "14. [MULTITAREA EFICIENTE]: Combina herramientas coherentes en el mismo turno para completar tareas en menor tiempo.\n"
            "15. [CONFIRMACIÓN DE ACCIONES CRÍTICAS]: Para operaciones Git remotas (push, pull request masivo) o borrado de archivos, solicita la confirmación del usuario.\n"
        )
    return prompt
