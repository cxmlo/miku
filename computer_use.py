import uiautomation as auto
import pyautogui
import time
import json
import ctypes
import base64
import re
from io import BytesIO
import logging
from typing import Optional, Dict, Any, Tuple
import spatial_memory
import security_manager
from action_result import ActionResult, ActionStatus, check_sensitive_action

logger = logging.getLogger("ComputerUse")

try:
    # Hace que las coordenadas de pyautogui coincidan con la resolución real (ignora la escala de Windows al 125% o 150%)
    ctypes.windll.user32.SetProcessDPIAware()
except:
    pass

# Memoria temporal para mapear IDs a controles
_element_map = {}

def escanear_ventana_activa() -> ActionResult:
    """Escanea la ventana activa actual de Windows y devuelve una lista de elementos interactuables con un ID."""
    global _element_map
    _element_map.clear()
    
    # Obtener ventana activa
    try:
        active_window = auto.GetForegroundControl()
    except Exception as e:
        return ActionResult(
            status=ActionStatus.FAILED.value,
            action="scan",
            error=f"Error obteniendo control de primer plano: {e}"
        )

    if not active_window:
        return ActionResult(
            status=ActionStatus.FAILED.value,
            action="scan",
            error="No hay ninguna ventana activa detectada."
        )
        
    resultado = f"Ventana activa: '{active_window.Name}'\nElementos disponibles:\n"
    element_id = 1
    
    # Tipos de controles que nos interesa que la IA pueda clicar
    tipos_interes = [
        auto.ControlType.ButtonControl,
        auto.ControlType.EditControl,
        auto.ControlType.MenuItemControl,
        auto.ControlType.TabItemControl,
        auto.ControlType.ListItemControl,
        auto.ControlType.HyperlinkControl,
        auto.ControlType.DocumentControl,
        auto.ControlType.ComboBoxControl,
        auto.ControlType.CheckBoxControl,
    ]
    
    try:
        # Recorrer los hijos de la ventana activa (profundidad 4 para no tardar años)
        for control, depth in auto.WalkControl(active_window, maxDepth=4):
            if control.ControlType in tipos_interes:
                # Solo controles visibles y que tengan dimensiones
                rect = control.BoundingRectangle
                if rect.width() > 0 and rect.height() > 0:
                    nombre = control.Name or "Sin nombre"
                    tipo = control.ControlTypeName
                    
                    # Guardar en el mapa
                    _element_map[str(element_id)] = {
                        "name": nombre,
                        "type": tipo,
                        "rect": rect,
                        "control": control
                    }
                    
                    resultado += f"[ID: {element_id}] {tipo} - '{nombre}'\n"
                    element_id += 1
                    
                    if element_id > 100:
                        break # Limitar a 100 para no abrumar al LLM
    except Exception as e:
        return ActionResult(
            status=ActionStatus.FAILED.value,
            action="scan",
            error=f"Error al escanear ventana activa: {e}"
        )
        
    total_found = element_id - 1
    if total_found == 0:
        return ActionResult(
            status=ActionStatus.CONFIRMED.value,
            action="scan",
            target=active_window.Name or "Ventana activa",
            evidence=f"Ventana '{active_window.Name}' escaneada pero no expone controles interactivos accesibles por UI Automation.",
            data={"count": 0, "window": active_window.Name}
        )
        
    return ActionResult(
        status=ActionStatus.CONFIRMED.value,
        action="scan",
        target=active_window.Name or "Ventana activa",
        evidence=f"Escaneo UIA completado en ventana '{active_window.Name}': {total_found} controles interactivos catalogados.",
        data={"count": total_found, "window": active_window.Name, "details": resultado}
    )

def hacer_clic_elemento(element_id: str) -> ActionResult:
    """Hace clic izquierdo en el elemento especificado por su ID."""
    allowed, reason = security_manager.is_gui_automation_allowed()
    if not allowed:
        return ActionResult(
            status=ActionStatus.FAILED.value,
            action="click_element",
            error=f"Operación denegada por seguridad: {reason}"
        )

    global _element_map
    if str(element_id) not in _element_map:
        return ActionResult(
            status=ActionStatus.FAILED.value,
            action="click_element",
            error=f"El ID {element_id} no existe en el último escaneo de la ventana activa."
        )
        
    elemento = _element_map[str(element_id)]
    target_desc = f"{elemento['type']} '{elemento['name']}'"

    # Verificar si el control representa un paso sensible que requiere usuario
    sensitive_reason = check_sensitive_action(target=elemento['name'])
    if sensitive_reason:
        return ActionResult(
            status=ActionStatus.REQUIRES_USER.value,
            action="click_element",
            target=target_desc,
            requires_user_reason=sensitive_reason
        )

    rect = elemento["rect"]
    
    # Calcular centro
    center_x = rect.left + (rect.width() // 2)
    center_y = rect.top + (rect.height() // 2)
    
    try:
        # Mover suavemente y clicar
        pyautogui.moveTo(center_x, center_y, duration=0.3)
        pyautogui.click()
    except Exception as e:
        return ActionResult(
            status=ActionStatus.FAILED.value,
            action="click_element",
            target=target_desc,
            error=f"Fallo al emitir evento de clic con pyautogui: {e}"
        )
    
    return ActionResult(
        status=ActionStatus.EXECUTED_UNVERIFIED.value,
        action="click_element",
        target=target_desc,
        evidence=f"Clic emitido en coordenadas ({center_x}, {center_y}) sobre el control UIA '{elemento['name']}'. El cambio resultante no ha sido verificado visualmente.",
        data={"x": center_x, "y": center_y, "type": elemento["type"]}
    )

def escribir_en_elemento(element_id: str, texto: str, presionar_enter: bool = True) -> ActionResult:
    """Hace clic en un elemento y escribe el texto especificado."""
    allowed, reason = security_manager.is_gui_automation_allowed()
    if not allowed:
        return ActionResult(
            status=ActionStatus.FAILED.value,
            action="type_element",
            error=f"Operación denegada por seguridad: {reason}"
        )

    global _element_map
    if str(element_id) not in _element_map:
        return ActionResult(
            status=ActionStatus.FAILED.value,
            action="type_element",
            error=f"El ID {element_id} no existe en el último escaneo."
        )
        
    elemento = _element_map[str(element_id)]
    target_desc = f"{elemento['type']} '{elemento['name']}'"

    # Verificación de credenciales / texto sensible
    sensitive_reason = check_sensitive_action(target=elemento['name'], text=texto)
    if sensitive_reason:
        return ActionResult(
            status=ActionStatus.REQUIRES_USER.value,
            action="type_element",
            target=target_desc,
            requires_user_reason=sensitive_reason
        )

    rect = elemento["rect"]
    center_x = rect.left + (rect.width() // 2)
    center_y = rect.top + (rect.height() // 2)
    
    try:
        pyautogui.moveTo(center_x, center_y, duration=0.3)
        pyautogui.click()
        time.sleep(0.2)
        pyautogui.write(texto, interval=0.01)
        if presionar_enter:
            time.sleep(0.1)
            pyautogui.press('enter')
            time.sleep(0.5)
    except Exception as e:
        return ActionResult(
            status=ActionStatus.FAILED.value,
            action="type_element",
            target=target_desc,
            error=f"Fallo al escribir en el elemento: {e}"
        )
    
    return ActionResult(
        status=ActionStatus.EXECUTED_UNVERIFIED.value,
        action="type_element",
        target=target_desc,
        evidence=f"Texto enviado al control UIA '{elemento['name']}' (enter={presionar_enter}). No se ha inspeccionado el resultado posterior.",
        data={"length": len(texto), "enter": presionar_enter}
    )

def _capturar_pantalla_limpia():
    """Asegura que la isla de Miku esté encogida en modo píldora compacta para no tapar la pantalla ni interferir con los clics."""
    try:
        from agents import broadcast_ui_command
        broadcast_ui_command({"type": "ui_command", "action": "shrink_for_vision"})
        time.sleep(0.18)
    except Exception:
        pass
    return pyautogui.screenshot()

def _capturar_pantalla_base64():
    """Toma una captura de pantalla limpia y optimizada, y la devuelve como string base64 en JPEG."""
    screenshot = _capturar_pantalla_limpia()
    screenshot.thumbnail((1280, 720))
    buffered = BytesIO()
    screenshot.save(buffered, format="JPEG", quality=55)
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

def _pedir_coordenadas(img, intencion):
    """Pide las coordenadas del elemento a clickear usando el modelo de visión configurado en Ajustes (DeepSeek Flash, Gemini, etc.)."""
    try:
        from agents import broadcast_ui_command
        broadcast_ui_command({"type": "agent_live_status", "status": f"Buscando '{intencion[:24]}'..."})
    except Exception:
        pass

    try:
        from models_provider import get_client_and_model, get_active_providers
        
        # Preparar captura en base64 con alta fidelidad (sin distorsionar texto ni botones pequeños)
        buffered = BytesIO()
        img_copy = img.copy()
        img_copy.thumbnail((1600, 1000))
        img_copy.save(buffered, format="JPEG", quality=82)
        img_b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

        prompt = f"""You are an expert GUI visual grounding agent.
Screen resolution: {img.width}x{img.height}.
The user wants to interact with: "{intencion}".
Identify the EXACT element (button, link, input, tab, icon) to click.
Respond ONLY with a raw JSON object (coordinates scaled 0-1000):
{{
  "target": "<element name or text>",
  "box": [ymin, xmin, ymax, xmax],
  "clicks": 1
}}
Axis rules (normalized 0-1000):
- X axis (horizontal): 0 is FAR LEFT (izquierda), 500 is CENTER, 1000 is FAR RIGHT (derecha).
- Y axis (vertical): 0 is TOP (arriba/superior), 500 is CENTER, 1000 is BOTTOM (abajo/inferior).
CRITICAL: If the user says 'izquierda' (left), x MUST be < 500 (typically 50-350). If 'derecha' (right), x MUST be > 500.
If you prefer single center point, you may provide "x" and "y" (0-1000).
Output pure JSON only without markdown or commentary."""

        # Usar el modelo configurado por el usuario en Ajustes para Computer Use, con respaldo multimodal real si el proveedor falla con imágenes (ej. api.deepseek.com)
        client_primary, model_primary, prov_primary = get_client_and_model(category="computer_use")
        if not client_primary:
            print("[Computer Use] Error: No hay cliente disponible para el modelo de Computer Use.")
            return None

        candidates = [(client_primary, model_primary, prov_primary)]
        if prov_primary in ("deepseek", "groq"):
            try:
                from models_provider import create_provider_client
                for fb_prov, fb_mod in [("google", "gemini-flash-latest"), ("openai", "gpt-4o-mini"), ("openrouter", "google/gemini-2.0-flash-001")]:
                    fb_cl, fb_clean, fb_p = create_provider_client(fb_prov, fb_mod)
                    if fb_cl:
                        candidates.append((fb_cl, fb_clean, fb_p))
            except Exception:
                pass

        last_err = None
        for cl, mod, prov in candidates:
            try:
                try:
                    from agents import broadcast_ui_command
                    broadcast_ui_command({"type": "agent_live_status", "status": f"Analizando con {prov.capitalize()}..."})
                except Exception:
                    pass

                response = cl.chat.completions.create(
                    model=mod,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}
                                }
                            ]
                        }
                    ],
                    temperature=0.0,
                    max_tokens=1500
                )

                content = response.choices[0].message.content or ""
                print(f"[Computer Use] Respuesta visual de {prov} ({mod}):\n{content.strip()}\n")
                json_match = re.search(r'\{[\s\S]*\}', content)
                if json_match:
                    try:
                        data = json.loads(json_match.group(0))
                        clicks = int(data.get("clicks", 1))
                        if any(w in intencion.lower() for w in ["doble clic", "2 clic"]):
                            clicks = 2
                        target_name = data.get("target", intencion)

                        # Formato 1: Bounding box explícito [ymin, xmin, ymax, xmax]
                        if "box" in data and isinstance(data["box"], (list, tuple)) and len(data["box"]) == 4:
                            ymin, xmin, ymax, xmax = [int(v) for v in data["box"]]
                            print(f"[Computer Use] Bounding box detectado por {prov}: [{ymin}, {xmin}, {ymax}, {xmax}] -> centro ({int((xmin+xmax)/2)}, {int((ymin+ymax)/2)})")
                            return {
                                "box": (ymin, xmin, ymax, xmax),
                                "clicks": clicks,
                                "app": f"{prov.capitalize()} ({mod})",
                                "target": target_name
                            }

                        # Formato 2: Coordenadas directas x, y
                        x = int(data.get("x", -1))
                        y = int(data.get("y", -1))
                        if x >= 0 and y >= 0:
                            print(f"[Computer Use] Coordenadas directas por {prov}: ({x}, {y})")
                            return {
                                "box": (y, x, y, x),
                                "clicks": clicks,
                                "app": f"{prov.capitalize()} ({mod})",
                                "target": target_name
                            }
                        else:
                            print(f"[Computer Use] {prov} ({mod}) devolvió coordenadas inválidas: {data}")
                    except Exception as parse_err:
                        print(f"[Computer Use] Error parseando JSON de {prov}: {parse_err}")
                else:
                    print(f"[Computer Use] {prov} ({mod}) no incluyó un objeto JSON válido.")
            except Exception as candidate_err:
                last_err = candidate_err
                if is_auth_error(candidate_err):
                    print(f"[Computer Use] Error de autenticación en {prov} ({mod}): clave inválida o permisos denegados.")
                elif is_transient_error(candidate_err):
                    print(f"[Computer Use] Error transitorio en {prov} ({mod}) (rate limit o sobrecarga): {candidate_err}")
                else:
                    print(f"[Computer Use] Error en {prov} ({mod}): {candidate_err}")
                continue

        if last_err:
            print(f"[Computer Use] Error final en Visual Grounding: {last_err}")
        return None
    except Exception as e:
        print(f"[Computer Use] Excepción general en _pedir_coordenadas: {e}")
        return None

def _verificar_accion(client, img_antes_str, img_despues_str, intencion, model_name=None):
    """Pregunta al modelo de visión si la acción tuvo éxito comparando antes y después."""
    
    prompt = f"""I tried to: "{intencion}"
The FIRST image is BEFORE the click. The SECOND image is AFTER the click.

Compare both screenshots and determine if the action was SUCCESSFUL.
For example:
- If the intention was to play a song: is there a progress bar moving, a pause button visible, or any sign the song is now playing?
- If the intention was to open a video: is a video now playing or loading?

Return your answer in this EXACT format (no markdown, no extra text):

RESULT: SUCCESS or FAIL
REASON: <brief explanation of what you see>
BOX: [ymin, xmin, ymax, xmax]

RULES:
- If RESULT is SUCCESS, BOX should be [0, 0, 0, 0].
- If RESULT is FAIL, BOX should contain corrected coordinates (scaled 0-1000) of where to click instead to achieve the intention. Apply the same rules as before (avoid album art in Spotify, etc).
- Return ONLY the 3 lines above. No other text."""

    effective_model = model_name or "gemini-flash-latest"
    response = client.chat.completions.create(
        model=effective_model,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{img_antes_str}"}
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{img_despues_str}"}
                    }
                ]
            }
        ],
        temperature=0.0,
    )
    
    text_response = response.choices[0].message.content or ""
    print(f"\n[DEBUG VERIFICACIÓN] Modelo ({effective_model}) respondió:\n{text_response}\n")
    
    success = "SUCCESS" in text_response.upper().split("RESULT:")[-1].split("\n")[0] if "RESULT:" in text_response.upper() else False
    
    box_match = re.search(r'\[(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\]', text_response)
    retry_box = None
    if box_match and not success:
        ymin, xmin, ymax, xmax = map(int, box_match.groups())
        if not (ymin == 0 and xmin == 0 and ymax == 0 and xmax == 0):
            retry_box = (ymin, xmin, ymax, xmax)
    
    reason_match = re.search(r'REASON:\s*(.+)', text_response)
    reason = reason_match.group(1).strip() if reason_match else ""
    
    return success, reason, retry_box

def mover_raton_visual(intencion: str) -> ActionResult:
    """Usa la visión de IA para encontrar el punto óptimo y solo MUEVE el ratón allí (sin clic)."""
    allowed, reason = security_manager.is_gui_automation_allowed()
    if not allowed:
        return ActionResult(
            status=ActionStatus.FAILED.value,
            action="move_visual",
            target=intencion,
            error=f"Operación denegada por seguridad: {reason}"
        )

    # Detección de paso sensible
    sensitive_reason = check_sensitive_action(intent=intencion)
    if sensitive_reason:
        return ActionResult(
            status=ActionStatus.REQUIRES_USER.value,
            action="move_visual",
            target=intencion,
            requires_user_reason=sensitive_reason
        )

    from models_provider import get_client_and_model
    client, model_name, prov = get_client_and_model(category="computer_use")
    if not client:
        client, model_name, prov = get_client_and_model(category="chat")
    if not client:
        return ActionResult(
            status=ActionStatus.FAILED.value,
            action="move_visual",
            target=intencion,
            error="Error: No se pudo conectar a un proveedor de IA para usar la visión."
        )
        
    try:
        mouse_w, mouse_h = pyautogui.size()
        img = _capturar_pantalla_limpia()
        resultado = _pedir_coordenadas(img, intencion)
        
        if not resultado:
            return ActionResult(
                status=ActionStatus.FAILED.value,
                action="move_visual",
                target=intencion,
                error=f"El modelo visual ({prov}) no pudo identificar un elemento para: '{intencion}'."
            )
        
        ymin, xmin, ymax, xmax = resultado["box"]
        app_name = resultado["app"]
        target_name = resultado["target"]
        
        click_x = int(((xmin + xmax) / 2) / 1000.0 * mouse_w)
        click_y = int(((ymin + ymax) / 2) / 1000.0 * mouse_h)

        try:
            from agents import broadcast_ui_command
            broadcast_ui_command({"type": "agent_live_status", "status": f"Moviendo a '{target_name[:22]}'..."})
        except Exception:
            pass

        pyautogui.moveTo(click_x, click_y, duration=0.4)
        
        return ActionResult(
            status=ActionStatus.EXECUTED_UNVERIFIED.value,
            action="move_visual",
            target=target_name,
            evidence=f"Cursor posicionado en ({click_x}, {click_y}) sobre elemento sugerido por {app_name}. No se emitió clic.",
            data={"x": click_x, "y": click_y, "app": app_name}
        )
        
    except Exception as e:
        return ActionResult(
            status=ActionStatus.FAILED.value,
            action="move_visual",
            target=intencion,
            error=f"Excepción en visión al mover ratón: {e}"
        )

def hacer_scroll(direccion: str, cantidad: int = 500) -> ActionResult:
    """Hace scroll con la rueda del ratón en la posición actual."""
    dir_clean = direccion.lower().strip()
    if dir_clean not in ['abajo', 'down', 'arriba', 'up']:
        return ActionResult(
            status=ActionStatus.FAILED.value,
            action="scroll",
            error="Dirección no válida. Usa 'abajo' o 'arriba'."
        )

    try:
        if dir_clean in ['abajo', 'down']:
            pyautogui.scroll(-cantidad)
            msg = f"Scroll hacia abajo ({cantidad} unidades) emitido en la posición actual del cursor."
        else:
            pyautogui.scroll(cantidad)
            msg = f"Scroll hacia arriba ({cantidad} unidades) emitido en la posición actual del cursor."
        
        return ActionResult(
            status=ActionStatus.EXECUTED_UNVERIFIED.value,
            action="scroll",
            evidence=msg,
            data={"direction": dir_clean, "amount": cantidad}
        )
    except Exception as e:
        return ActionResult(
            status=ActionStatus.FAILED.value,
            action="scroll",
            error=f"Error al hacer scroll: {e}"
        )


def limpiar_intencion(intencion: str) -> str:
    """Limpia palabras de relleno de la intención para mejorar la búsqueda por accesibilidad UIA."""
    if not intencion:
        return ""
    texto = intencion.lower().strip()
    
    # 1. Eliminar verbos de acción al inicio
    verbos = [
        "hacer triple clic", "haz triple clic", "triple clic",
        "hacer doble clic", "haz doble clic", "doble clic",
        "hacer clic", "haz clic", "clic", "click",
        "pulsa", "presiona", "toca", "selecciona", "abre", "abrir"
    ]
    for v in verbos:
        if texto.startswith(v):
            texto = texto[len(v):].strip()
            break
            
    # 2. Eliminar preposiciones intermedias ("en", "sobre", "a")
    for prep in ["en ", "sobre ", "a "]:
        if texto.startswith(prep):
            texto = texto[len(prep):].strip()
            break

    # 3. Eliminar sustantivos de tipo de control ("el botón", "la pestaña", "el menú", "el icono", etc.)
    sustantivos_tipo = [
        "el botón de ", "el boton de ", "el botón ", "el boton ", "botón de ", "boton de ", "botón ", "boton ",
        "la pestaña de ", "la pestana de ", "la pestaña ", "la pestana ", "pestaña de ", "pestana de ", "pestaña ", "pestana ",
        "el menú de ", "el menu de ", "el menú ", "el menu ", "menú de ", "menu de ", "menú ", "menu ",
        "el icono de ", "el ícono de ", "el icono ", "el ícono ", "icono de ", "ícono de ", "icono ", "ícono ",
        "el enlace de ", "el enlace ", "enlace de ", "enlace ",
        "el campo de ", "el campo ", "campo de ", "campo ",
        "la caja de ", "la caja ", "caja de ", "caja ",
        "el elemento ", "elemento ", "la opción de ", "la opcion de ", "la opción ", "la opcion "
    ]
    for s in sustantivos_tipo:
        if texto.startswith(s):
            texto = texto[len(s):].strip()
            break

    # 4. Eliminar artículos restantes
    for art in ["el ", "la ", "los ", "las ", "un ", "una "]:
        if texto.startswith(art):
            texto = texto[len(art):].strip()
            break

    return texto.strip().strip("'\"")


def buscar_control_uia(intencion: str, active_window: Optional[Any] = None) -> Optional[Dict[str, Any]]:
    """
    Nivel 1 de Computer Use: Busca un control en la ventana activa mediante UI Automation de Windows.
    0 llamadas a APIs externas, 0 tokens de visión consumidos, latencia ultra baja.
    """
    limpio = limpiar_intencion(intencion)
    if not limpio:
        return None

    try:
        win = active_window or auto.GetForegroundControl()
    except Exception as e:
        logger.debug(f"No se pudo obtener ventana activa para UIA: {e}")
        return None

    if not win:
        return None

    tipos_interactivos = [
        auto.ControlType.ButtonControl,
        auto.ControlType.MenuItemControl,
        auto.ControlType.TabItemControl,
        auto.ControlType.HyperlinkControl,
        auto.ControlType.CheckBoxControl,
        auto.ControlType.RadioButtonControl,
        auto.ControlType.EditControl,
        auto.ControlType.ListItemControl,
        auto.ControlType.ComboBoxControl,
        auto.ControlType.SplitButtonControl,
    ]

    candidatos = []
    try:
        for control, _ in auto.WalkControl(win, maxDepth=4):
            if control.ControlType in tipos_interactivos:
                rect = control.BoundingRectangle
                if rect and rect.width() > 0 and rect.height() > 0:
                    c_name = (control.Name or "").strip().lower()
                    c_auto_id = getattr(control, "AutomationId", "").strip().lower()
                    
                    # 1. Coincidencia exacta de nombre
                    if c_name == limpio:
                        return {
                            "control": control,
                            "name": control.Name,
                            "type": control.ControlTypeName,
                            "automation_id": getattr(control, "AutomationId", ""),
                            "rect": rect,
                            "center": (rect.left + rect.width() // 2, rect.top + rect.height() // 2),
                            "exact": True
                        }
                    
                    # 2. Coincidencia parcial
                    if limpio in c_name or (c_auto_id and limpio in c_auto_id):
                        candidatos.append({
                            "control": control,
                            "name": control.Name,
                            "type": control.ControlTypeName,
                            "automation_id": getattr(control, "AutomationId", ""),
                            "rect": rect,
                            "center": (rect.left + rect.width() // 2, rect.top + rect.height() // 2),
                            "exact": False
                        })
    except Exception as e:
        logger.debug(f"Excepción en WalkControl de UIA: {e}")

    if candidatos:
        candidatos.sort(key=lambda c: len(c["name"]) if c["name"] else 999)
        return candidatos[0]

    return None


def hacer_clic_visual(intencion: str, verificar_exito: bool = False, usar_niveles: bool = True) -> ActionResult:
    """Usa el subsistema por niveles de Computer Use:
    Nivel 1: UI Automation local (0 tokens de visión).
    Nivel 2: Memoria Espacial persistida confirmada.
    Nivel 3: Visión multimodal API (sólo si Nivel 1 y 2 no resolvieron).
    Si verificar_exito es True, verifica si funcionó con una segunda captura.
    """
    allowed, reason = security_manager.is_gui_automation_allowed()
    if not allowed:
        return ActionResult(
            status=ActionStatus.FAILED.value,
            action="click_visual",
            target=intencion,
            error=f"Operación denegada por seguridad: {reason}"
        )

    # Paso de autenticación o credenciales sensibles: detenerse y pedir usuario
    sensitive_reason = check_sensitive_action(intent=intencion)
    if sensitive_reason:
        return ActionResult(
            status=ActionStatus.REQUIRES_USER.value,
            action="click_visual",
            target=intencion,
            requires_user_reason=sensitive_reason
        )

    mouse_w, mouse_h = pyautogui.size()
    num_clicks = 1
    intencion_lower = intencion.lower()
    if "doble clic" in intencion_lower or "2 clic" in intencion_lower:
        num_clicks = 2
    elif "triple clic" in intencion_lower or "3 clic" in intencion_lower:
        num_clicks = 3

    # =========================================================================
    # NIVEL 1: Intento de resolución local vía UI Automation de Windows (0 tokens)
    # =========================================================================
    if usar_niveles:
        uia_match = buscar_control_uia(intencion)
        if uia_match:
            cx, cy = uia_match["center"]
            control_name = uia_match["name"] or intencion
            ctrl_type = uia_match["type"]
            
            try:
                from agents import broadcast_ui_command
                action_desc = "Doble clic en" if num_clicks == 2 else "Clic en"
                broadcast_ui_command({"type": "agent_live_status", "status": f"{action_desc} '{control_name[:20]}' (UIA)..."})
            except Exception:
                pass

            print(f"[Computer Use] Nivel 1 UIA: Moviendo ratón a '{control_name}' en ({cx}, {cy})...")
            pyautogui.moveTo(cx, cy, duration=0.25)
            if num_clicks == 2:
                pyautogui.doubleClick()
            else:
                pyautogui.click()
            print(f"[Computer Use] Clic Nivel 1 UIA completado en ({cx}, {cy}).")

            # Persistir en Memoria Espacial V2 si es coincidencia exacta y tiene rectángulo válido
            try:
                if uia_match.get("exact") and mouse_w > 0 and mouse_h > 0:
                    r = uia_match.get("rect")
                    if r:
                        box_scaled = [
                            int(r.top / mouse_h * 1000),
                            int(r.left / mouse_w * 1000),
                            int(r.bottom / mouse_h * 1000),
                            int(r.right / mouse_w * 1000)
                        ]
                    else:
                        box_scaled = [
                            int(cy / mouse_h * 1000),
                            int(cx / mouse_w * 1000),
                            int(cy / mouse_h * 1000),
                            int(cx / mouse_w * 1000)
                        ]
                    spatial_memory.save_coordinates(
                        intencion,
                        box_scaled,
                        automation_id=uia_match.get("automation_id", ""),
                        control_type=str(ctrl_type or "")
                    )
            except Exception:
                pass

            if not verificar_exito:
                return ActionResult(
                    status=ActionStatus.EXECUTED_UNVERIFIED.value,
                    action="click_visual",
                    target=control_name,
                    evidence=f"Clic emitido en ({cx}, {cy}) sobre el control UIA '{control_name}' ({ctrl_type}). Nivel 1 (0 tokens).",
                    data={"x": cx, "y": cy, "tier": 1, "source": "uia", "type": ctrl_type, "clicks": num_clicks}
                )

    # =========================================================================
    # RESOLUCIÓN DE CLIENTE PARA NIVEL 2 Y 3
    # =========================================================================
    from models_provider import get_client_and_model
    client, model_name, prov = get_client_and_model(category="computer_use")
    if not client:
        client, model_name, prov = get_client_and_model(category="chat")
    if not client:
        return ActionResult(
            status=ActionStatus.FAILED.value,
            action="click_visual",
            target=intencion,
            error="Error: No se pudo conectar a ningún proveedor de IA configurado para visión."
        )
        
    try:
        # === NIVEL 2: Comprobar Memoria Espacial ===
        cached_coords = spatial_memory.get_cached_coordinates(intencion)
        
        if cached_coords:
            ymin, xmin, ymax, xmax = cached_coords
            app_name = "Memoria Espacial"
            target_name = intencion
            click_x = int(((xmin + xmax) / 2) / 1000.0 * mouse_w)
            click_y = int(((ymin + ymax) / 2) / 1000.0 * mouse_h)
            tier_used = 2
            source_used = "spatial_memory"

        else:
            # === NIVEL 3: Capturar pantalla limpia y pedir coordenadas a API multimodal ===
            img = _capturar_pantalla_limpia()
            resultado = _pedir_coordenadas(img, intencion)
            
            if not resultado:
                return ActionResult(
                    status=ActionStatus.FAILED.value,
                    action="click_visual",
                    target=intencion,
                    error=f"El modelo visual ({prov} - {model_name}) no pudo identificar coordenadas para: '{intencion}'."
                )
            
            ymin, xmin, ymax, xmax = resultado["box"]
            num_clicks = resultado["clicks"]
            app_name = resultado["app"]
            target_name = resultado["target"]
            
            click_x = int(((xmin + xmax) / 2) / 1000.0 * mouse_w)
            click_y = int(((ymin + ymax) / 2) / 1000.0 * mouse_h)
            tier_used = 3
            source_used = "vision_api"

        img_antes_base64 = None
        if verificar_exito:
            img_antes_base64 = _capturar_pantalla_base64()
            
        # Emitir clic
        try:
            from agents import broadcast_ui_command
            action_desc = "Doble clic en" if num_clicks == 2 else "Clic en"
            broadcast_ui_command({"type": "agent_live_status", "status": f"{action_desc} '{target_name[:20]}'..."})
        except Exception:
            pass

        print(f"[Computer Use] Ejecutando pyautogui.moveTo({click_x}, {click_y}, duration=0.4) y click...")
        pyautogui.moveTo(click_x, click_y, duration=0.4)
        if num_clicks == 2:
            pyautogui.doubleClick()
        else:
            pyautogui.click()
        print(f"[Computer Use] Clic físico emitido en ({click_x}, {click_y}) ({app_name}).")
        
        if not verificar_exito:
            return ActionResult(
                status=ActionStatus.EXECUTED_UNVERIFIED.value,
                action="click_visual",
                target=target_name,
                evidence=f"Clic emitido en ({click_x}, {click_y}) según {app_name}. No se solicitó verificación de pantalla.",
                data={"x": click_x, "y": click_y, "app": app_name, "clicks": num_clicks, "tier": tier_used, "source": source_used}
            )
            
        # Verificación con captura posterior
        try:
            from agents import broadcast_ui_command
            broadcast_ui_command({"type": "agent_live_status", "status": "Verificando resultado en pantalla..."})
        except Exception:
            pass

        time.sleep(1.2)
        img_despues_base64 = _capturar_pantalla_base64()
        
        success, reason, _ = _verificar_accion(client, img_antes_base64, img_despues_base64, intencion, model_name=model_name)

        if success:
            if not cached_coords:
                spatial_memory.save_coordinates(intencion, [ymin, xmin, ymax, xmax])
            return ActionResult(
                status=ActionStatus.CONFIRMED.value,
                action="click_visual",
                target=target_name,
                evidence=f"Clic en ({click_x}, {click_y}) ejecutado y confirmado por inspección visual: {reason}",
                data={"x": click_x, "y": click_y, "reason": reason, "tier": tier_used, "source": source_used}
            )
        else:
            return ActionResult(
                status=ActionStatus.FAILED.value,
                action="click_visual",
                target=target_name,
                error=f"Clic emitido en ({click_x}, {click_y}), pero la verificación visual posterior determinó que el objetivo no se cumplió ({reason}). Se detuvo para evitar clics ciegos.",
                data={"tier": tier_used, "source": source_used}
            )
        
    except Exception as e:
        return ActionResult(
            status=ActionStatus.FAILED.value,
            action="click_visual",
            target=intencion,
            error=f"Error en ejecución visual: {e}"
        )


def interactuar_elemento(intencion: str, accion: str = "click", texto: Optional[str] = None, verificar_exito: bool = False) -> ActionResult:
    """Orquestador unificado por niveles de Computer Use:
    Nivel 1: UI Automation local de Windows (0 tokens).
    Nivel 2: Memoria Espacial con ahorro de tokens.
    Nivel 3: Visión Multimodal API (sólo si Nivel 1 y 2 no están disponibles).
    """
    if accion == "type" and texto:
        # Intento UIA directo para escritura
        uia_match = buscar_control_uia(intencion)
        if uia_match and uia_match.get("type") in ("EditControl", "ComboBoxControl", "DocumentControl"):
            cx, cy = uia_match["center"]
            c_name = uia_match["name"] or intencion
            sensitive_reason = check_sensitive_action(target=c_name, text=texto)
            if sensitive_reason:
                return ActionResult(
                    status=ActionStatus.REQUIRES_USER.value,
                    action="type_element",
                    target=c_name,
                    requires_user_reason=sensitive_reason
                )
            try:
                pyautogui.moveTo(cx, cy, duration=0.25)
                pyautogui.click()
                time.sleep(0.15)
                try:
                    import pyperclip
                    pyperclip.copy(texto)
                    pyautogui.hotkey('ctrl', 'v')
                except Exception:
                    pyautogui.write(texto, interval=0.01)
                time.sleep(0.15)
                pyautogui.press('enter')
                return ActionResult(
                    status=ActionStatus.EXECUTED_UNVERIFIED.value,
                    action="type_element",
                    target=c_name,
                    evidence=f"Texto escrito en control UIA '{c_name}' en ({cx}, {cy}) y Enter presionado. Nivel 1 (0 tokens).",
                    data={"tier": 1, "source": "uia", "x": cx, "y": cy}
                )
            except Exception as e:
                logger.debug(f"Error escribiendo en control UIA: {e}")

    # Para clics, delegar al orquestador por niveles hacer_clic_visual
    return hacer_clic_visual(intencion=intencion, verificar_exito=verificar_exito, usar_niveles=True)


