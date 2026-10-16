import os
import ctypes
import pyautogui
import time
import subprocess

def gestionar_ventana(nombre: str, accion: str) -> str:
    """Gestiona el estado de una ventana abierta (maximizar, minimizar, cerrar, restaurar)."""
    user32 = ctypes.windll.user32
    EnumWindows = user32.EnumWindows
    EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))
    GetWindowText = user32.GetWindowTextW
    GetWindowTextLength = user32.GetWindowTextLengthW
    IsWindowVisible = user32.IsWindowVisible

    found_hwnd = 0
    n = nombre.lower()
    palabra_clave = n.split()[0] if ' ' in n else n

    def foreach_window(hwnd, lParam):
        nonlocal found_hwnd
        if IsWindowVisible(hwnd):
            length = GetWindowTextLength(hwnd)
            if length > 0:
                buff = ctypes.create_unicode_buffer(length + 1)
                GetWindowText(hwnd, buff, length + 1)
                if palabra_clave in buff.value.lower():
                    found_hwnd = hwnd
                    return False
        return True

    EnumWindows(EnumWindowsProc(foreach_window), 0)

    if not found_hwnd:
        return f"No se encontró ninguna ventana abierta que coincida con '{nombre}'."

    accion = accion.lower()
    if accion == "maximizar":
        user32.ShowWindow(found_hwnd, 3) # SW_MAXIMIZE
        user32.SetForegroundWindow(found_hwnd)
        return f"Ventana de '{nombre}' maximizada."
    elif accion == "minimizar":
        user32.ShowWindow(found_hwnd, 6) # SW_MINIMIZE
        return f"Ventana de '{nombre}' minimizada."
    elif accion == "restaurar":
        user32.ShowWindow(found_hwnd, 9) # SW_RESTORE
        user32.SetForegroundWindow(found_hwnd)
        return f"Ventana de '{nombre}' restaurada."
    elif accion == "cerrar":
        user32.PostMessageW(found_hwnd, 0x0010, 0, 0) # WM_CLOSE
        return f"Comando de cierre enviado a la ventana de '{nombre}'."
    else:
        return "Acción no reconocida. Usa 'maximizar', 'minimizar', 'restaurar' o 'cerrar'."

def abrir_aplicacion(nombre: str, maximizar: bool = False) -> str:
    """Abre una aplicación buscándola en el menú de inicio de Windows, o la trae al frente si ya está abierta. Si maximizar es True, la ventana se maximizará."""
    n = nombre.lower()
    
    # === 1. VERIFICAR SI YA ESTÁ ABIERTA ===
    try:
        user32 = ctypes.windll.user32
        EnumWindows = user32.EnumWindows
        EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))
        GetWindowText = user32.GetWindowTextW
        GetWindowTextLength = user32.GetWindowTextLengthW
        IsWindowVisible = user32.IsWindowVisible

        found_hwnd = 0
        palabra_clave = n.split()[0] if ' ' in n else n

        def foreach_window(hwnd, lParam):
            nonlocal found_hwnd
            if IsWindowVisible(hwnd):
                length = GetWindowTextLength(hwnd)
                if length > 0:
                    buff = ctypes.create_unicode_buffer(length + 1)
                    GetWindowText(hwnd, buff, length + 1)
                    title = buff.value.lower()
                    if palabra_clave in title:
                        found_hwnd = hwnd
                        return False # Detener
            return True

        EnumWindows(EnumWindowsProc(foreach_window), 0)

        if found_hwnd:
            IsIconic = user32.IsIconic
            if maximizar:
                user32.ShowWindow(found_hwnd, 3) # SW_MAXIMIZE
            elif IsIconic(found_hwnd):
                user32.ShowWindow(found_hwnd, 9) # SW_RESTORE si está minimizada
            else:
                user32.ShowWindow(found_hwnd, 5) # SW_SHOW si está normal/maximizada
            user32.SetForegroundWindow(found_hwnd)
            time.sleep(0.5)
            return f"La aplicación '{nombre}' ya estaba abierta. La he traído al frente{' y maximizado' if maximizar else ''}."
    except Exception as e:
        print(f"Error checking window: {e}")
        pass
    
    # === 2. ABRIR SI NO ESTÁ ABIERTA ===
    
    protocolos = {
        'spotify': 'spotify:',
    }
    
    for key, proto in protocolos.items():
        if key in n:
            try:
                os.system(f'start {proto}')
                time.sleep(2.0)
                if maximizar:
                    pyautogui.hotkey('win', 'up')
                return f"{nombre} abriéndose mediante protocolo{' y maximizando' if maximizar else ''}."
            except:
                pass 
    
    try:
        pyautogui.hotkey('win')
        time.sleep(0.7)
        pyautogui.write(nombre, interval=0.03)
        time.sleep(0.8)
        pyautogui.press('enter')
        
        # Espera dinámica inteligente: verificar si la ventana ya aparece (hasta 10 segundos máximo)
        start_wait = time.time()
        window_appeared = False
        while time.time() - start_wait < 10.0:
            found_new = False
            def check_new_window(hwnd, lParam):
                nonlocal found_new
                if IsWindowVisible(hwnd):
                    length = GetWindowTextLength(hwnd)
                    if length > 0:
                        buff = ctypes.create_unicode_buffer(length + 1)
                        GetWindowText(hwnd, buff, length + 1)
                        if palabra_clave in buff.value.lower():
                            found_new = True
                            return False
                return True
            EnumWindows(EnumWindowsProc(check_new_window), 0)
            
            if found_new:
                window_appeared = True
                time.sleep(0.8) # Pausa final cortita para la animación de apertura
                break
            time.sleep(0.5)
            
        if not window_appeared:
            # Si no la detectó, de todas formas hacemos una pausa estándar por si acaso es una app invisible
            time.sleep(2.0)
            
        if maximizar:
            pyautogui.hotkey('win', 'up')
            time.sleep(0.5)
        return f"Buscando y abriendo '{nombre}' desde el menú de inicio de Windows. Esperé de forma dinámica a que cargara."
    except Exception as e:
        return f"Error al intentar abrir {nombre}: {e}"

def escribir_texto(texto: str, presionar_enter: bool = False, limpiar_antes: bool = False) -> str:
    """Escribe el texto en donde esté el foco actual, tecla por tecla como un humano."""
    if limpiar_antes:
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.1)
        pyautogui.press('backspace')
        time.sleep(0.1)
        
    pyautogui.write(texto, interval=0.015)
    
    if presionar_enter:
        time.sleep(0.1)
        pyautogui.press('enter')
        time.sleep(1.0) 
    
    msg1 = " (texto previo limpiado)" if limpiar_antes else ""
    msg2 = " y se presionó Enter" if presionar_enter else ""
    return f"Texto escrito a mano alzada (longitud: {len(texto)} caracteres){msg1}{msg2}."

def atajo_teclado(accion: str) -> str:
    """Ejecuta atajos de teclado rápidos. Soporta alias comunes o combinaciones directas (ej. 'ctrl+j')."""
    accion = accion.lower().strip()
    
    alias = {
        "enter": (['enter'], "Tecla Enter presionada. [INSTRUCCIÓN]: Confírmale verbalmente al usuario que has enviado el mensaje o ejecutado la acción (ej. 'Mensaje enviado')."),
        "atras": (['alt', 'left'], "Navegación: Atrás (Alt+Izquierda)"),
        "adelante": (['alt', 'right'], "Navegación: Adelante (Alt+Derecha)"),
        "cerrar_pestana": (['ctrl', 'w'], "Pestaña cerrada (Ctrl+W)"),
        "nueva_pestana": (['ctrl', 't'], "Nueva pestaña abierta (Ctrl+T)"),
        "recargar": (['f5'], "Página recargada (F5)"),
        "buscar_navegador": (['ctrl', 'e'], "Barra de búsqueda del navegador seleccionada (Ctrl+E)"),
        "deshacer": (['ctrl', 'z'], "Acción deshecha (Ctrl+Z)"),
        "rehacer": (['ctrl', 'y'], "Acción rehecha (Ctrl+Y)"),
        "copiar": (['ctrl', 'c'], "Copiado al portapapeles (Ctrl+C)"),
        "pegar": (['ctrl', 'v'], "Pegado (Ctrl+V)"),
        "cortar": (['ctrl', 'x'], "Cortado (Ctrl+X)"),
        "guardar": (['ctrl', 's'], "Guardado ejecutado (Ctrl+S)"),
        "borrar": (['backspace'], "Borrado un carácter (Backspace)"),
        "suprimir": (['delete'], "Borrado hacia adelante (Delete)")
    }
    
    if accion == "seleccionar_todo":
        pyautogui.hotkey('ctrl', 'a')
        pyautogui.hotkey('ctrl', 'e')
        return "Seleccionar todo ejecutado (Ctrl+A / Ctrl+E)"
        
    if accion in alias:
        keys, msg = alias[accion]
        pyautogui.hotkey(*keys)
        return msg
        
    try:
        keys = [k.strip() for k in accion.split('+')]
        pyautogui.hotkey(*keys)
        return f"Atajo de teclado ejecutado: {accion}"
    except Exception as e:
        return f"Error ejecutando atajo '{accion}': {e}"

def ejecutar_macro_teclado(pasos: list) -> str:
    """Ejecuta una secuencia de acciones de teclado y escritura de una sola vez."""
    resultados = []
    for paso in pasos:
        try:
            accion = paso.get("accion", "").lower()
            if accion == "atajo":
                res = atajo_teclado(paso.get("valor", ""))
                resultados.append(f"Atajo: {res}")
            elif accion == "escribir":
                texto = paso.get("valor", "")
                enter = paso.get("presionar_enter", False)
                res = escribir_texto(texto, presionar_enter=enter)
                resultados.append(f"Escribir: {res}")
            elif accion == "esperar":
                segundos = float(paso.get("valor", 1.0))
                time.sleep(segundos)
                resultados.append(f"Esperar: {segundos}s")
            time.sleep(0.3) # Pequeña pausa natural entre acciones
        except Exception as e:
            resultados.append(f"Error en paso {paso}: {e}")
            break
    
    return "Macro ejecutada. Resultados:\n" + "\n".join(resultados)

def borrar_archivo(ruta: str) -> str:
    """Borra un archivo del sistema. Requiere la ruta absoluta."""
    return f"ACCIÓN PELIGROSA: Por favor, pídele al usuario que confirme verbalmente que realmente desea borrar el archivo en {ruta} antes de hacerlo."

def borrar_archivo_confirmado(ruta: str) -> str:
    """Borra un archivo una vez que el usuario ha dado su confirmación explícita."""
    try:
        ruta_lower = ruta.lower()
        rutas_protegidas = ["c:\\windows", "c:\\program files", "c:\\programdata", "system32", "appdata"]
        for p in rutas_protegidas:
            if p in ruta_lower:
                return f"Error de Seguridad: Miku tiene prohibido borrar archivos en rutas del sistema ({p}). Operación cancelada."
                
        if os.path.exists(ruta):
            os.remove(ruta)
            return f"El archivo {ruta} ha sido eliminado permanentemente."
        else:
            return f"El archivo {ruta} no existe."
    except Exception as e:
        return f"Error al intentar borrar el archivo: {e}"

def tomar_captura_pantalla(nombre_archivo: str = "captura") -> str:
    """Toma una captura de la pantalla actual y la guarda como archivo de imagen (.png) en una carpeta temporal invisible."""
    import tempfile
    import base64
    import io
    try:
        if not nombre_archivo.endswith(".png"):
            nombre_archivo += ".png"
        temp_dir = tempfile.gettempdir()
        file_path = os.path.join(temp_dir, nombre_archivo)
        
        screenshot = pyautogui.screenshot()
        screenshot.save(file_path)

        # Generar thumbnail ligero para la interfaz de chat (click-to-zoom)
        try:
            thumb = screenshot.copy()
            thumb.thumbnail((280, 160))
            buf = io.BytesIO()
            thumb.save(buf, format="JPEG", quality=75)
            thumb_b64 = "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")

            import requests
            API_KEY = os.getenv("MIKU_API_KEY", "miku_secure_key_2026")
            requests.post("http://127.0.0.1:8000/broadcast_command",
                          json={"payload": {
                              "type": "agent_tool_step",
                              "tool": "tomar_captura_pantalla",
                              "name": "Captura de pantalla",
                              "detail": f"Pantalla guardada en {nombre_archivo}",
                              "screenshot": thumb_b64
                          }},
                          headers={"x-api-key": API_KEY}, timeout=0.5)
        except Exception:
            pass

        return f"Captura de pantalla tomada con éxito y guardada en {file_path}. (Ruta absoluta temporal, el sistema la borrará luego automáticamente)."
    except Exception as e:
        return f"Error al intentar guardar la captura: {e}"

def ejecutar_comando_sistema(comando: str) -> str:
    """Ejecuta un comando en la consola de Windows (PowerShell/CMD)."""
    try:
        # Prevenir que comandos de PowerShell se queden congelados pidiendo confirmación al usuario
        if comando.strip().lower().startswith("powershell"):
            if "-NonInteractive" not in comando:
                comando = comando.replace("powershell", "powershell -NonInteractive -ExecutionPolicy Bypass", 1)

        # Notificar paso de comando a la UI del chat
        try:
            import requests
            API_KEY = os.getenv("MIKU_API_KEY", "miku_secure_key_2026")
            requests.post("http://127.0.0.1:8000/broadcast_command",
                          json={"payload": {
                              "type": "agent_tool_step",
                              "tool": "ejecutar_comando_sistema",
                              "name": "Ejecutó un comando",
                              "detail": comando[:100] + ("..." if len(comando) > 100 else "")
                          }},
                          headers={"x-api-key": API_KEY}, timeout=0.4)
        except Exception:
            pass

        resultado = subprocess.run(comando, shell=True, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=15)
        out = resultado.stdout.strip()
        err = resultado.stderr.strip()
        if resultado.returncode == 0:
            return f"Comando ejecutado con éxito. Salida:\n{out}"
        else:
            return f"El comando falló con código {resultado.returncode}. Error:\n{err}"
    except Exception as e:
        return f"Excepción al ejecutar comando: {e}"

def esperar_segundos(segundos: float = 2.0) -> str:
    """Pausa la ejecución del agente (cierra los ojos) por un tiempo determinado."""
    import time
    try:
        s = float(segundos)
        if s > 10.0: s = 10.0 # Límite de seguridad
        time.sleep(s)
        return f"He esperado {s} segundos en silencio."
    except Exception as e:
        return f"Error al esperar: {e}"
