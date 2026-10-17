import os
import subprocess
import requests
from agents import agent_manager
from memory import add_memory, guardar_enlace, buscar_en_memoria as db_buscar

def _emitir_comando_ui(action: str, args: list = None, **kwargs):
    payload = {"type": "ui_command", "action": action}
    if args is not None:
        payload["args"] = args
    payload.update(kwargs)
    try:
        requests.post("http://127.0.0.1:8000/broadcast_command", 
                      json={"payload": payload}, 
                      headers={"x-api-key": "miku_secure_key_2026"}, 
                      timeout=2)
    except:
        pass

def ver_pantalla() -> str:
    """Toma una captura de la pantalla actual. El LLM usarÃ¡ esto para ver."""
    return "MIKU_VISION_REQUEST" 

def monitorear_actividad_pc() -> str:
    """Monitorea pasivamente quÃ© aplicaciones estÃ¡ usando el usuario en su PC ahora mismo y cuÃ¡nto tiempo lleva en cada una, sin tomar capturas de pantalla."""
    try:
        from activity_monitor import get_activity_context_str
        act = get_activity_context_str()
        if not act:
            return "No se detectaron aplicaciones en primer plano."
        return act
    except Exception as e:
        return f"Error monitoreando actividad: {e}"

def listar_agentes_disponibles() -> str:
    """Lista todos los agentes secundarios configurados en el sistema (Antigravity, GitHub, Claude Code, Vercel, etc.) con sus roles y estado actual."""
    try:
        from agents import load_agents_config, agent_manager
        agents = load_agents_config()
        if not agents:
            return "No hay agentes secundarios configurados en el sistema."
        
        lines = ["Agentes disponibles en el ecosistema Miku:"]
        for i, a in enumerate(agents, 1):
            aid = a.get("id", "desconocido")
            aname = a.get("name", aid.capitalize())
            arole = a.get("role", "Sin rol especificado")
            amodel = a.get("model", "Gemini Flash").replace("google/", "").replace("groq/", "")
            is_busy = agent_manager.is_agent_busy(aid)
            status = "⚙️ TRABAJANDO EN SEGUNDO PLANO" if is_busy else "🟢 LISTO / DISPONIBLE"
            lines.append(f"{i}. {aname} (ID: {aid}) - Estado: {status}\n   • Rol/Especialidad: {arole}\n   • Modelo: {amodel}")
        return "\n".join(lines)
    except Exception as e:
        return f"Error consultando agentes: {e}"

def delegar_a_agente(agente: str, tarea: str) -> str:
    """Delega una tarea específica a un agente secundario (ej. 'antigravity', 'github').
    El agente ejecutará la tarea en segundo plano con herramientas autónomas. Al terminar, le notificará al usuario y a Miku."""
    return agent_manager.delegate(task=tarea, agent_id=agente)

def abrir_chat_con_agente(agente: str) -> str:
    """Cambia la vista activa de la interfaz de la isla dinámica al chat de un agente específico (ej. 'antigravity', 'github', o 'miku' para la orquestadora principal)."""
    try:
        from agents import load_agents_config, broadcast_ui_command
        target = (agente or "").strip().lower()
        if target in ("miku", "principal", "orquestador", "blanco", "blanca"):
            broadcast_ui_command({"type": "switch_agent_chat", "agent_id": "miku"})
            return "Cambiando la interfaz al chat principal de Miku."
        
        agents = load_agents_config()
        matched = None
        for a in agents:
            if a.get("id", "").lower() == target or target in a.get("name", "").lower():
                matched = a
                break
        
        if not matched:
            matched = agents[0] if agents else {"id": "antigravity", "name": "Antigravity"}
            
        broadcast_ui_command({"type": "switch_agent_chat", "agent_id": matched["id"]})
        return f"Abriendo la pantalla de chat con el agente {matched.get('name', matched['id'])}."
    except Exception as e:
        return f"Error al abrir chat con agente: {e}"

def crear_o_actualizar_agente(id: str, nombre: str, rol: str, color: str = None) -> str:
    """Crea un nuevo agente secundario o actualiza el rol de uno existente en el ecosistema Miku."""
    try:
        from agents import load_agents_config, save_agents_config, broadcast_ui_command
        agents = load_agents_config()
        clean_id = id.strip().lower().replace(" ", "_")
        found = False
        for a in agents:
            if a.get("id", "").lower() == clean_id:
                a["name"] = nombre.strip()
                a["role"] = rol.strip()
                if color:
                    a["c"] = color.strip()
                found = True
                break
        
        if not found:
            preset_colors = ["#4FD3B1", "#3B9EFF", "#FFD84D", "#9BE15D", "#F06CF0", "#FF5C66"]
            chosen_col = color if color else preset_colors[len(agents) % len(preset_colors)]
            new_ag = {
                "id": clean_id,
                "name": nombre.strip(),
                "role": rol.strip(),
                "c": chosen_col,
                "model": "google/gemini-2.5-flash",
                "hooks": 1,
                "active": 1,
                "outfit": "none"
            }
            agents.append(new_ag)
            
        save_agents_config(agents)
        broadcast_ui_command({"type": "agents", "list": agents})
        action = "actualizado" if found else "creado"
        return f"Agente '{nombre}' ({clean_id}) {action} exitosamente con el rol: {rol}."
    except Exception as e:
        return f"Error guardando agente: {e}"

def delegar_tarea(tarea: str) -> str:
    """Delega una tarea larga a un agente de fondo (compatibilidad)."""
    return agent_manager.delegate(task=tarea, agent_id="antigravity")

def guardar_ultimo_reporte_en_escritorio(nombre_archivo: str) -> str:
    """Guarda el texto completo del Ãºltimo reporte generado por un agente en un bloc de notas en el escritorio."""
    if not agent_manager.last_result:
        return "No hay ningÃºn reporte reciente de agentes para guardar."
        
    try:
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        file_path = os.path.join(desktop_path, f"{nombre_archivo}.txt")
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(agent_manager.last_result)
            
        subprocess.Popen(['notepad.exe', file_path])
        return f"Reporte guardado con Ã©xito en tu escritorio como '{nombre_archivo}.txt' y abierto en el bloc de notas."
    except Exception as e:
        return f"Error al guardar el reporte: {e}"

def aprender_sobre_usuario(dato: str) -> str:
    """Guarda un dato personal, gusto o preferencia del usuario en la memoria a largo plazo."""
    return add_memory(dato)

def guardar_enlace_memoria(contexto: str, url: str) -> str:
    """Guarda permanentemente una URL y su contexto descriptivo en la colecciÃ³n de enlaces de Miku."""
    return guardar_enlace(contexto, url)

def buscar_en_memoria(consulta: str) -> str:
    """Busca en la base de datos vectorial recuerdos o enlaces guardados usando similitud semÃ¡ntica."""
    return db_buscar(consulta)

def hablar_al_usuario(texto: str) -> str:
    """Usa esta herramienta si quieres decirle algo al usuario MIENTRAS estÃ¡s en medio de realizar mÃºltiples tareas encadenadas."""
    import os
    import threading
    source = os.environ.get("MIKU_CURRENT_SOURCE", "pc")
    
    if source == "mobile":
        # En mÃ³vil, preferimos una experiencia fluida sin superponer audios intermedios
        # SÃ³lo actualizamos el estado de texto para que el usuario sepa quÃ© pasa
        _emitir_comando_ui('status_update', None, text=texto)
        return f"Dicho al usuario mÃ³vil: {texto}"
        
    def worker():
        try:
            from audio_handler import speak
            speak(texto)
        except:
            pass
            
    threading.Thread(target=worker, daemon=True).start()
    return "El usuario ha escuchado el mensaje. [INSTRUCCIÃ“N OBLIGATORIA]: ContinÃºa INMEDIATAMENTE llamando a la siguiente herramienta de tu lista de tareas. NO devuelvas texto, solo llama a la herramienta."

def enviar_mensaje_a_agente(mensaje: str) -> str:
    """EnvÃ­a una instrucciÃ³n, correcciÃ³n o mensaje al agente que estÃ¡ trabajando en segundo plano."""
    try:
        return agent_manager.send_message(mensaje)
    except Exception as e:
        return f"Error al comunicar con el agente: {e}"

def abrir_panel_secretos_en_app(servicio: str, campos_requeridos: list) -> str:
    """EnvÃ­a un comando a la aplicaciÃ³n mÃ³vil del usuario para que se abra automÃ¡ticamente el Panel de Secretos y puedan ingresar las claves requeridas."""
    _emitir_comando_ui('open_secrets_panel', [servicio, campos_requeridos])
    return f"Se ha abierto el panel de secretos en el dispositivo del usuario solicitando los campos {campos_requeridos} para '{servicio}'. Dile al usuario que ingrese las claves en el panel de su celular y espera a que te confirme que lo hizo."

def ejecutar_intent_android(action: str, extras: dict = None) -> str:
    """Ejecuta un Intent nativo en el dispositivo Android del usuario (como configurar una alarma o temporizador)."""
    if extras is None:
        extras = {}
    
    _emitir_comando_ui('ejecutar_intent_android', None, intent_action=action, extras=extras)
    
    return f"Se ha enviado el comando al dispositivo Android para ejecutar el intent '{action}'. Confirma al usuario que lo has hecho."

def mostrar_widget_info(titulo: str, contenido: str, icono: str = "â„¹ï¸", duracion_segundos: int = 15) -> str:
    """Muestra un widget invisible/semitransparente estilo HUD en la pantalla con informaciÃ³n dinÃ¡mica (clima, hora, alertas)."""
    try:
        original_icono = icono
        
        # Mapeo automÃ¡tico de emojis a los hermosos SVG de Google
        emoji_to_svg = {
            "â˜€ï¸": "https://www.gstatic.com/weather/conditions/v1/svg/sunny_light.svg",
            "ðŸŒ¤ï¸": "https://www.gstatic.com/weather/conditions/v1/svg/partly_cloudy_light.svg",
            "â›…": "https://www.gstatic.com/weather/conditions/v1/svg/mostly_cloudy_day_light.svg",
            "â˜ï¸": "https://www.gstatic.com/weather/conditions/v1/svg/cloudy_light.svg",
            "ðŸŒ§ï¸": "https://www.gstatic.com/weather/conditions/v1/svg/heavy_rain_light.svg",
            "ðŸŒ¦ï¸": "https://www.gstatic.com/weather/conditions/v1/svg/heavy_rain_light.svg",
            "â›ˆï¸": "https://www.gstatic.com/weather/conditions/v1/svg/heavy_rain_light.svg",
            "ðŸŒ©ï¸": "https://www.gstatic.com/weather/conditions/v1/svg/heavy_rain_light.svg"
        }
        
        for k, v in emoji_to_svg.items():
            if k in icono:
                icono = v
                break

        if icono.startswith("http"):
            import requests
            try:
                resp = requests.get(icono, timeout=3)
                if resp.status_code == 200:
                    icono = "SVG:" + resp.text
                else:
                    icono = original_icono
            except:
                icono = original_icono
            
        _emitir_comando_ui('show_info', [titulo, contenido, duracion_segundos, icono])
        return f"Widget de informaciÃ³n mostrado con tÃ­tulo '{titulo}' y se auto-ocultarÃ¡ en {duracion_segundos} segundos. El usuario ya lo estÃ¡ leyendo."
    except Exception as e:
        return f"Error al mostrar widget: {e}"

def mostrar_widget_clima(ciudad: str, temperatura: str, estado: str, viento: str, humedad: str, icono_nombre: str) -> str:
    """Muestra un widget interactivo avanzado dedicado exclusivamente a la informaciÃ³n del clima."""
    try:
        import os
        from ui import ui_comm
        
        # Mapeo a los SVGs locales. Si icono_nombre no coincide exactamente, usamos un fallback.
        base_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "widget", "google-weather-icons-main", "icons", "weather", "v1", "light")
        svg_file = f"{icono_nombre}.svg"
        full_path = os.path.join(base_path, svg_file)
        
        if not os.path.exists(full_path):
            full_path = os.path.join(base_path, "cloudy.svg") # fallback seguro
            
        source = os.environ.get("MIKU_CURRENT_SOURCE", "pc")
        
        if source == "mobile":
            import requests
            # Convertir ruta absoluta a ruta relativa montada en el servidor (ej: /assets/widget/...)
            relative_path = "/assets/" + full_path.split("assets\\")[-1].replace("\\", "/") if "assets" in full_path else full_path
            API_KEY = os.getenv("MIKU_API_KEY", "miku_secure_key_2026")
            payload = {
                "type": "ui_command",
                "action": "mobile_widget",
                "args": ["weather", ciudad, temperatura, estado, viento, humedad, relative_path]
            }
            try:
                requests.post("http://127.0.0.1:8000/broadcast_command", 
                              json={"payload": payload}, 
                              headers={"x-api-key": API_KEY})
            except Exception:
                pass
            return f"Widget del clima enviado a la App para {ciudad}."
            
        _emitir_comando_ui('show_weather', [f"Clima en {ciudad}", temperatura, estado, viento, humedad, full_path])
        
        return f"Widget del clima mostrado para {ciudad}."
    except Exception as e:
        return f"Error al mostrar widget del clima: {e}"

def modificar_estado_widget(tipo_widget: str, accion: str) -> str:
    """Modifica el estado visual de un widget (clima, reloj, musica, info, tarjeta)."""
    try:
        _emitir_comando_ui('modify_widget', [tipo_widget, accion])
        return f"Se ha ordenado {accion} el widget de {tipo_widget}."
    except Exception as e:
        return f"Error al modificar el widget: {e}"

def mostrar_widget_reloj(titulo: str, hora_digital: str) -> str:
    """Muestra un widget con la hora en la pantalla usando el reloj animado."""
    try:
        _emitir_comando_ui('show_clock', [titulo, hora_digital])
        return f"Widget de reloj mostrado exitosamente: {titulo} - {hora_digital}"
    except Exception as e:
        return f"Error al mostrar el widget del reloj: {str(e)}"

def mostrar_tarjeta_visual(archivos: list, mensaje: str) -> str:
    """Muestra una tarjeta visual en la pantalla con archivos e imÃ¡genes."""
    try:
        import os
        source = os.environ.get("MIKU_CURRENT_SOURCE", "pc")
        if source == "mobile":
            for f in archivos:
                try:
                    enviar_imagen_a_chat(f, mensaje)
                except:
                    pass
            return "ImÃ¡genes enviadas directamente al chat del celular. Ya NO necesitas leer las rutas en voz alta."
            
        _emitir_comando_ui('show_card', ["Archivos Encontrados" if archivos else "Miku", mensaje, archivos])
        return "Se ha mostrado la tarjeta visual en pantalla correctamente. Ya NO necesitas leer en voz alta las rutas de estos archivos, el usuario ya los estÃ¡ viendo."
    except Exception as e:
        return f"Error al mostrar la tarjeta: {e}"

def analizar_archivo_silencioso(ruta: str) -> str:
    """Analiza el contenido de un archivo local (PDF o Imagen) en segundo plano de forma totalmente silenciosa sin abrirlo fÃ­sicamente en la pantalla. Ãšsalo SIEMPRE que el usuario te envÃ­e o suelte un archivo [SILENT_DROP]."""
    import os
    if not os.path.exists(ruta):
        return "El archivo no existe."
    
    ext = os.path.splitext(ruta)[1].lower()
    
    if ext == '.pdf':
        try:
            import fitz
            doc = fitz.open(ruta)
            text = ""
            for i in range(min(3, len(doc))):
                text += doc[i].get_text()
            if not text.strip():
                try:
                    _emitir_comando_ui('show_quicklook', [ruta])
                except: pass
                return f"El PDF '{os.path.basename(ruta)}' parece estar escaneado o vacÃ­o de texto."
            try:
                _emitir_comando_ui('show_quicklook', [ruta])
            except: pass
            return f"Extracto de las primeras pÃ¡ginas del PDF '{os.path.basename(ruta)}':\n{text[:2000]}..."
        except Exception as e:
            return f"Error leyendo PDF: {e}"
            
    elif ext in ['.jpg', '.jpeg', '.png', '.webp', '.bmp', '.jfif']:
        try:
            import brain
            import base64
            client = brain.get_vertex_client()
            if not client:
                return "Error: Vertex AI no configurado."
                
            with open(ruta, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                
            mime_type = "image/jpeg"
            if ext == '.png': mime_type = "image/png"
            elif ext == '.webp': mime_type = "image/webp"
            
            response = client.chat.completions.create(
                model="google/gemini-3.5-flash",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Describe de forma muy concisa y directa quÃ© hay en esta imagen."},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{encoded_string}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=250
            )
            try:
                _emitir_comando_ui('show_quicklook', [ruta])
            except: pass
            return f"AnÃ¡lisis de imagen de {os.path.basename(ruta)}: {response.choices[0].message.content}"
        except Exception as e:
            return f"Error analizando imagen por IA: {e}"
            
    else:
        try:
            _emitir_comando_ui('show_quicklook', [ruta])
        except: pass
        return f"Es un archivo de tipo {ext}. No tengo un parser silencioso para su contenido, pero su nombre es {os.path.basename(ruta)}."

import uuid

import uuid

def enviar_archivo_a_celular(ruta: str) -> str:
    """Envía un archivo local al teléfono Miku conectado, tanto desde PC como desde móvil."""
    import json
    import os
    import urllib.error
    import urllib.request

    if not os.path.isfile(ruta):
        return f"Error: no se encontró un archivo válido en {ruta}"

    api_key = os.getenv("MIKU_API_KEY", "miku_secure_key_2026")
    url = "http://127.0.0.1:8000/api/desktop/send_file_to_phone"
    data = json.dumps({"path": os.path.abspath(ruta)}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "x-api-key": api_key},
    )

    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            result = json.loads(response.read().decode("utf-8"))
        return f"Archivo {result.get('filename', os.path.basename(ruta))} listo para guardar en el teléfono."
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        return f"Error al enviar el archivo (HTTP {exc.code}): {detail}"
    except Exception as e:
        return f"Error al enviar el archivo al teléfono: {e}"

def enviar_imagen_a_chat(ruta_imagen: str, mensaje: str) -> str:
    """EnvÃ­a una imagen (con un mensaje) directamente al chat de la aplicaciÃ³n mÃ³vil del usuario. NUNCA lo uses para PC."""
    import os, shutil, requests, tempfile
    if not os.path.exists(ruta_imagen): return f"Error: No se encontrÃ³ {ruta_imagen}"
    
    temp_dir = tempfile.gettempdir()
    filename = os.path.basename(ruta_imagen)
    dest_path = os.path.join(temp_dir, filename)
    
    if os.path.abspath(ruta_imagen) != os.path.abspath(dest_path):
        shutil.copy2(ruta_imagen, dest_path)
        
    API_KEY = os.getenv("MIKU_API_KEY", "miku_secure_key_2026")
    image_url = f"/api/temp_media/{filename}"
    
    payload = {
        "type": "chat",
        "sender": "miku",
        "text": mensaje,
        "image_url": image_url,
        "id": str(uuid.uuid4())
    }
    
    try:
        requests.post("http://127.0.0.1:8000/broadcast_command", 
                      json={"payload": payload}, 
                      headers={"x-api-key": API_KEY})
        return "Imagen enviada al chat correctamente."
    except Exception as e:
        return f"Error enviando imagen: {e}"

def obtener_clima(ciudad: str) -> str:
    """Obtiene el clima actual de una ciudad al instante sin abrir el navegador."""
    import requests
    try:
        # Usar wttr.in para obtener el clima rÃ¡pido en formato de texto corto
        # format=4 da algo como: "Ciudad: â›…ï¸ +22Â°C ðŸŒ¬ 15km/h"
        url = f"https://wttr.in/{ciudad}?format=4"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            return f"El clima actual en {ciudad} es: {resp.text.strip()}"
        return f"No se pudo obtener el clima para {ciudad}. Intenta con el navegador."
    except Exception as e:
        return f"Error obteniendo clima: {e}"

def instalar_skill_mcp(nombre_servidor: str, comando: str, argumentos: list) -> str:
    """Instala y conecta un nuevo servidor MCP dinÃ¡micamente sin reiniciar Miku."""
    import asyncio

def instalar_skill_mcp(nombre_servidor: str, comando: str, argumentos: list) -> str:
    """Instala y conecta un nuevo servidor MCP dinÃ¡micamente sin reiniciar Miku."""
    import asyncio
    import concurrent.futures
    from mcp_client import mcp_manager
    if not mcp_manager.main_loop:
        return "El servidor MCP no estÃ¡ inicializado correctamente en el loop principal."
    
    future = asyncio.run_coroutine_threadsafe(
        mcp_manager.add_server(nombre_servidor, comando, argumentos),
        mcp_manager.main_loop
    )
    try:
        resultado = future.result(timeout=45)
        return resultado
    except Exception as e:
        return f"Error instalando skill: {e}"

def solicitar_permiso_instalacion_mcp(nombre: str, proposito: str, github_url: str, comandos_instalacion: list) -> str:
    """
    IMPORTANTE: Ãšsalo cuando necesites descargar e instalar un nuevo servidor MCP o software de terceros desde internet.
    Esta funciÃ³n pausarÃ¡ tu razonamiento y enviarÃ¡ una solicitud de autorizaciÃ³n al celular del usuario.
    DevolverÃ¡ la decisiÃ³n del usuario, la cual DEBES respetar. No procedas sin que esta funciÃ³n devuelva 'Permiso concedido'.
    """
    import os
    import time
    import requests
    import uuid
    
    task_id = str(uuid.uuid4())
    
    # Emitir comando a UI mÃ³vil
    _emitir_comando_ui('mobile_widget', ["mcp_auth", task_id, nombre, proposito, github_url, comandos_instalacion])
    
    # Hablar o notificar
    hablar_al_usuario("He encontrado un mÃ³dulo que nos servirÃ¡. Te he enviado una tarjeta de autorizaciÃ³n a tu celular para que la revises.")
    
    # Polling the server waiting for user response
    max_wait_seconds = 180
    start_time = time.time()
    
    while time.time() - start_time < max_wait_seconds:
        try:
            resp = requests.get(f"http://127.0.0.1:8000/api/mcp/auth_status/{task_id}", timeout=2)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status") == "ok":
                    decision = data.get("decision")
                    if decision == "approve":
                        return "Permiso concedido por el usuario. Procede a ejecutar los comandos de instalaciÃ³n."
                    elif decision == "reject":
                        return "Permiso DENEGADO por el usuario. NO instales esto y aborta la operaciÃ³n."
                    elif decision == "search_another":
                        return "Permiso DENEGADO. El usuario te ha pedido explÃ­citamente que busques OTRA opciÃ³n o repositorio diferente. Busca otra alternativa."
        except:
            pass
        time.sleep(1.5)
        
    # Ocultar widget por timeout
    _emitir_comando_ui('mobile_widget', ["none"])
    return "Tiempo de espera agotado (3 minutos). El usuario no respondiÃ³ a la solicitud de autorizaciÃ³n. Asume permiso DENEGADO y aborta."

def mostrar_en_isla(titulo: str, subtitulo: str = "", mood: str = "soft", expresion: str = "idle", duracion: int = 6000, componentes: list = None) -> str:
    """Muestra una notificaciÃ³n procedural en la Isla DinÃ¡mica de Miku.
    
    Args:
        titulo: TÃ­tulo principal de la notificaciÃ³n.
        subtitulo: SubtÃ­tulo o descripciÃ³n breve.
        mood: Color/ambiente de la notificaciÃ³n. Opciones: soft, red, green, amber, cyan, indigo, pink.
        expresion: Estado del personaje Mochi. Opciones: idle, thinking, working, talking, listening, happy, laughing, approval, surprised, question, error, dizzy, sleeping, love, proud, searching, annoyed.
        duracion: DuraciÃ³n en milisegundos (0 = persistente).
        componentes: Lista opcional de componentes extra. Cada componente es un dict con:
            - {"type": "text", "content": "texto"}
            - {"type": "progress", "value": 75, "label": "Cargando..."}
            - {"type": "actions", "buttons": [{"label": "SÃ­", "action": "approve"}, {"label": "No", "action": "reject"}]}
            - {"type": "chips", "items": ["tag1", "tag2"]}
            - {"type": "code", "content": "print('hola')"}
    
    Returns:
        ConfirmaciÃ³n de que la notificaciÃ³n fue enviada.
    """
    try:
        payload = {
            "mood": mood,
            "bot_state": expresion,
            "duration": duracion,
            "layout": {
                "title": titulo,
                "subtitle": subtitulo,
                "components": componentes or []
            }
        }
        resp = requests.post(
            "http://127.0.0.1:8000/island_notify",
            json=payload,
            headers={"x-api-key": "miku_secure_key_2026"},
            timeout=2
        )
        if resp.status_code == 200:
            return f"NotificaciÃ³n mostrada en la isla: '{titulo}'"
        return f"Error al enviar notificaciÃ³n: HTTP {resp.status_code}"
    except Exception as e:
        return f"Error al enviar notificaciÃ³n a la isla: {e}"



def hacer_pregunta_opciones(pregunta: str, opciones: list, titulo: str = "Miku Assistant") -> str:
    _emitir_comando_ui("show_scene", scene="question", params={"title": titulo, "q": pregunta, "options": opciones})
    from ui_events import wait_for_ui_event
    respuesta = wait_for_ui_event(timeout=120)
    if respuesta: return f"El usuario selecciono: {respuesta}"
    return "Timeout."

def preparar_correo(destinatario: str, asunto: str, mensaje: str) -> str:
    _emitir_comando_ui("show_scene", scene="mail", params={"to": destinatario, "subject": asunto, "message": mensaje})
    from ui_events import wait_for_ui_event
    respuesta = wait_for_ui_event(timeout=120)
    if respuesta == "enviar_correo": return "El usuario APROBO el correo. Procede a enviar el correo."
    elif respuesta == "cancelar": return "El usuario RECHAZO el borrador del correo. Cancela la accion."
    return "Timeout."
