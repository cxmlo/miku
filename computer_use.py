import uiautomation as auto
import pyautogui
import time
import json
import ctypes
import base64
import re
from io import BytesIO
from google import genai
from google.genai import types
import google.auth
from config import GOOGLE_CLOUD_PROJECT
import spatial_memory
import security_manager

try:
    # Hace que las coordenadas de pyautogui coincidan con la resolución real (ignora la escala de Windows al 125% o 150%)
    ctypes.windll.user32.SetProcessDPIAware()
except:
    pass

# Memoria temporal para mapear IDs a controles
_element_map = {}

def escanear_ventana_activa() -> str:
    """Escanea la ventana activa actual de Windows y devuelve una lista de elementos interactuables con un ID."""
    global _element_map
    _element_map.clear()
    
    # Obtener ventana activa
    # En uiautomation, podemos buscar la ventana de primer plano
    active_window = auto.GetForegroundControl()
    if not active_window:
        return "No hay ninguna ventana activa detectada."
        
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
        return f"Error al escanear ventana: {e}"
        
    if element_id == 1:
        resultado += "No se encontraron elementos interactivos visibles en esta ventana."
        
    return resultado

def hacer_clic_elemento(element_id: str) -> str:
    """Hace clic izquierdo en el elemento especificado por su ID."""
    allowed, reason = security_manager.is_gui_automation_allowed()
    if not allowed:
        return f"Operación denegada: {reason}"

    global _element_map
    if str(element_id) not in _element_map:
        return f"Error: El ID {element_id} no existe en el último escaneo."
        
    elemento = _element_map[str(element_id)]
    rect = elemento["rect"]
    
    # Calcular centro
    center_x = rect.left + (rect.width() // 2)
    center_y = rect.top + (rect.height() // 2)
    
    # Mover suavemente y clicar (pyautogui es más robusto a nivel OS que uiautomation click)
    pyautogui.moveTo(center_x, center_y, duration=0.3)
    pyautogui.click()
    
    return f"Clic realizado en {elemento['type']} '{elemento['name']}'."

def escribir_en_elemento(element_id: str, texto: str, presionar_enter: bool = True) -> str:
    """Hace clic en un elemento y escribe el texto especificado."""
    allowed, reason = security_manager.is_gui_automation_allowed()
    if not allowed:
        return f"Operación denegada: {reason}"

    global _element_map
    if str(element_id) not in _element_map:
        return f"Error: El ID {element_id} no existe en el último escaneo."
        
    elemento = _element_map[str(element_id)]
    rect = elemento["rect"]
    
    # Calcular centro y clicar para enfocar
    center_x = rect.left + (rect.width() // 2)
    center_y = rect.top + (rect.height() // 2)
    
    pyautogui.moveTo(center_x, center_y, duration=0.3)
    pyautogui.click()
    time.sleep(0.2)
    
    # Escribir usando el teclado (más universal)
    pyautogui.write(texto, interval=0.01)
    
    if presionar_enter:
        time.sleep(0.1)
        pyautogui.press('enter')
        time.sleep(1.0) # Esperar a que la página o búsqueda cargue
        return f"Texto escrito en '{elemento['name']}' y presionado Enter."
    
    return f"Texto escrito en '{elemento['name']}' sin presionar Enter."

def _capturar_pantalla_base64():
    """Toma una captura de pantalla optimizada y la devuelve como string base64 en JPEG."""
    screenshot = pyautogui.screenshot()
    screenshot.thumbnail((1280, 720))
    buffered = BytesIO()
    screenshot.save(buffered, format="JPEG", quality=50)
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

def _pedir_coordenadas(img, intencion):
    """Pide a Gemini 3.5 las coordenadas del elemento a clickear usando la API oficial Computer Use."""
    
    try:
        credentials, _ = google.auth.default()
        client = genai.Client(enterprise=True, project=GOOGLE_CLOUD_PROJECT, location='northamerica-northeast1')
        
        try:
            from ui import ui_comm
            ui_comm.agent_status_signal.emit(f"👁️ Visión | 🎯 {intencion[:40]}...")
        except:
            pass
        
        # Cargar lecciones aprendidas para dárselas a la IA visual
        from prompt_manager import load_learned_rules
        rules = load_learned_rules()
        contexto_visual = f"Find and interact with: '{intencion}'. You MUST output a tool call with screen coordinates (e.g., click, left_click, double_click) on the requested element. DO NOT use 'type_text', 'open_web_browser' or other generic actions. Your ONLY job is to return the exact screen coordinates to click."
        if rules:
            contexto_visual += "\n\nCRITICAL RULES TO FOLLOW:\n"
            for rule in rules:
                contexto_visual += f"- {rule}\n"
                
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = client.models.generate_content(
                    model='gemini-3.5-flash',
                    contents=[contexto_visual, img],
                    config=types.GenerateContentConfig(
                        tools=[types.Tool(computer_use=types.ComputerUse())],
                        temperature=0.0
                    )
                )
                
                for part in response.candidates[0].content.parts:
                    if part.function_call:
                        name = part.function_call.name
                        args = part.function_call.args

                        
                        # Gemini devuelve las coordenadas en escala 0-1000
                        x = int(args.get('x', -1))
                        y = int(args.get('y', -1))
                        
                        if x == -1 or y == -1:

                            return None
                            
                        clicks = 1
                        intencion_lower = intencion.lower()
                        if "doble clic" in intencion_lower or "2 clic" in intencion_lower:
                            clicks = 2
                        elif "triple clic" in intencion_lower or "3 clic" in intencion_lower:
                            clicks = 3
                            
                        return {
                            "box": (y, x, y, x), # Solo pasamos el punto exacto para mantener compatibilidad con el resto del código
                            "clicks": clicks,
                            "app": "API Nativa",
                            "target": args.get('intent', intencion)
                        }

                return None
                
            except Exception as e:
                err_str = str(e)
                if "not supported for this model in this region" in err_str and attempt < max_retries - 1:
                    print(f"Reintentando API Computer Use (intento {attempt + 2}/{max_retries}) debido a balanceo de carga global...")
                    time.sleep(1.5)
                else:
                    print(f"Error en API Computer Use: {e}")
                    return None
                    
    except Exception as e:
        print(f"Error fatal en _pedir_coordenadas: {e}")
        return None

def _verificar_accion(client, img_antes_str, img_despues_str, intencion):
    """Pregunta a Gemini si la acción tuvo éxito comparando antes y después."""
    
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

    response = client.chat.completions.create(
        model="google/gemini-2.5-flash",
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
    
    text_response = response.choices[0].message.content
    print(f"\n[DEBUG VERIFICACIÓN] Gemini respondió:\n{text_response}\n")
    
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

def mover_raton_visual(intencion: str) -> str:
    """Usa la visión de Gemini para encontrar el punto óptimo y solo MUEVE el ratón allí (sin clic)."""
    allowed, reason = security_manager.is_gui_automation_allowed()
    if not allowed:
        return f"Operación denegada: {reason}"

    from brain import get_vertex_client
    client = get_vertex_client()
    if not client:
        return "Error: No se pudo conectar a la IA para usar la visión."
        
    try:
        mouse_w, mouse_h = pyautogui.size()
        
        # === PASO 1: Capturar pantalla y pedir coordenadas ===
        img = pyautogui.screenshot()
        resultado = _pedir_coordenadas(img, intencion)
        
        if not resultado:
            return f"La IA no pudo encontrar un elemento para: '{intencion}'."
        
        ymin, xmin, ymax, xmax = resultado["box"]
        app_name = resultado["app"]
        target_name = resultado["target"]
        
        click_x = int(((xmin + xmax) / 2) / 1000.0 * mouse_w)
        click_y = int(((ymin + ymax) / 2) / 1000.0 * mouse_h)

        
        # === PASO 2: Mover el ratón ===
        pyautogui.moveTo(click_x, click_y, duration=0.4)
        
        return f"Ratón movido exitosamente a '{target_name}' (coordenadas {click_x}, {click_y}). No se hizo clic."
        
    except Exception as e:
        return f"Error en la visión al mover: {e}"

def hacer_scroll(direccion: str, cantidad: int = 500) -> str:
    """Hace scroll con la rueda del ratón en la posición actual."""
    try:
        if direccion.lower() in ['abajo', 'down']:
            pyautogui.scroll(-cantidad)
            return f"Scroll hacia abajo realizado ({cantidad} unidades) en la posición actual del ratón."
        elif direccion.lower() in ['arriba', 'up']:
            pyautogui.scroll(cantidad)
            return f"Scroll hacia arriba realizado ({cantidad} unidades) en la posición actual del ratón."
        else:
            return "Dirección no válida. Usa 'abajo' o 'arriba'."
    except Exception as e:
        return f"Error al hacer scroll: {e}"

def hacer_clic_visual(intencion: str, verificar_exito: bool = False) -> str:
    """Usa la visión de Gemini para analizar la pantalla, identificar la app activa,
    encontrar el punto óptimo para cumplir la intención del usuario, y hacer clic.
    Si verificar_exito es True, verifica si funcionó y reintenta.
    Funciona con cualquier aplicación: Spotify, YouTube, Netflix, navegadores, etc.
    """
    allowed, reason = security_manager.is_gui_automation_allowed()
    if not allowed:
        return f"Operación denegada: {reason}"

    from brain import get_vertex_client
    client = get_vertex_client()
    if not client:
        return "Error: No se pudo conectar a la IA para usar la visión."
        
    try:
        mouse_w, mouse_h = pyautogui.size()
        
        # === PASO 0: Comprobar Memoria Espacial Inteligente ===
        cached_coords = spatial_memory.get_cached_coordinates(intencion)
        
        if cached_coords:
            ymin, xmin, ymax, xmax = cached_coords
            
            # Si ya sabemos dónde está, NO perdemos tiempo verificando visualmente
            verificar_exito = False
            
            num_clicks = 1
            intencion_lower = intencion.lower()
            if "doble clic" in intencion_lower or "2 clic" in intencion_lower:
                num_clicks = 2
            elif "triple clic" in intencion_lower or "3 clic" in intencion_lower:
                num_clicks = 3
                
            app_name = "Memoria Espacial"
            target_name = intencion
            click_x = int(((xmin + xmax) / 2) / 1000.0 * mouse_w)
            click_y = int(((ymin + ymax) / 2) / 1000.0 * mouse_h)

        else:
            # === PASO 1: Capturar pantalla y pedir coordenadas ===
            # Gemini API Nativa requiere objeto PIL Image o Bytes, usaremos PIL
            img = pyautogui.screenshot()
            
            resultado = _pedir_coordenadas(img, intencion)
            
            if not resultado:
                return f"La IA no pudo encontrar un elemento para: '{intencion}'."
            
            ymin, xmin, ymax, xmax = resultado["box"]
            num_clicks = resultado["clicks"]
            app_name = resultado["app"]
            target_name = resultado["target"]
            
            click_x = int(((xmin + xmax) / 2) / 1000.0 * mouse_w)
            click_y = int(((ymin + ymax) / 2) / 1000.0 * mouse_h)

            
            pass # Guardado diferido hasta verificar
        
        img_antes_base64 = None
        if verificar_exito:
            img_antes_base64 = _capturar_pantalla_base64()
            
        # === PASO 2: Hacer clic ===
        pyautogui.moveTo(click_x, click_y, duration=0.5)
        if num_clicks == 2:
            pyautogui.doubleClick()
        else:
            pyautogui.click()
        
        if not verificar_exito:
            if not cached_coords:
                spatial_memory.save_coordinates(intencion, [ymin, xmin, ymax, xmax])
            return f"Clic visual completado en {app_name}: '{target_name}' (coordenadas {click_x}, {click_y})."
            
        # === PASO 3: Verificación ===
        time.sleep(1.2) # Esperar a que la página cargue o la acción surta efecto
        img_despues_base64 = _capturar_pantalla_base64()
        
        success, reason, retry_box = _verificar_accion(client, img_antes_base64, img_despues_base64, intencion)
        
        if success:
            if not cached_coords:
                spatial_memory.save_coordinates(intencion, [ymin, xmin, ymax, xmax])
            return f"Clic visual completado y VERIFICADO CON ÉXITO: {reason}"
        else:

            if retry_box:
                ymin, xmin, ymax, xmax = retry_box
                click_x2 = int(((xmin + xmax) / 2) / 1000.0 * mouse_w)
                click_y2 = int(((ymin + ymax) / 2) / 1000.0 * mouse_h)
                pyautogui.moveTo(click_x2, click_y2, duration=0.4)
                pyautogui.click()
                if num_clicks == 2:
                    time.sleep(0.08)
                    pyautogui.click()
                if not cached_coords:
                    spatial_memory.save_coordinates(intencion, [ymin, xmin, ymax, xmax])
                return f"Clic visual original falló ({reason}). Se realizó un SEGUNDO INTENTO de corrección en nuevas coordenadas."
            return f"Clic visual ejecutado pero la VERIFICACIÓN FALLÓ: {reason}. No se pudo corregir automáticamente."
        
        
    except Exception as e:
        return f"Error en la visión: {e}"
