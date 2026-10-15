import tempfile
import subprocess
import os
import sys

def escribir_y_ejecutar_python(codigo: str) -> str:
    """Escribe código Python en un archivo temporal y lo ejecuta, devolviendo la salida."""
    
    # === PROTECCIÓN DE SEGURIDAD ===
    codigo_lower = codigo.lower()
    rutas_protegidas = [
        "c:\\windows", 
        "c:\\program files", 
        "c:\\programdata", 
        "system32",
        "appdata"
    ]
    comandos_peligrosos = [
        "format c:",
        "rm -rf /",
        "del /f /s /q c:\\",
    ]
    
    for ruta in rutas_protegidas:
        if ruta in codigo_lower:
            return f"Error de Seguridad: Miku tiene prohibido interactuar o borrar datos en rutas críticas del sistema operativo ({ruta}). Ejecución bloqueada."
            
    for cmd in comandos_peligrosos:
        if cmd in codigo_lower:
            return f"Error de Seguridad: Intento de comando destructivo bloqueado."
    # ================================
    
    try:
        # Guardar el código generado por la IA en un archivo temporal
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
            # Asegurarnos de que el código tenga los imports necesarios si la IA los olvidó
            if "import " not in codigo:
                pass
            f.write(codigo)
            temp_file_path = f.name
            
        print(f"\n=========================================")
        print(f"[Miku ha escrito y ejecutado este script]")
        print(f"=========================================\n{codigo}\n=========================================\n")
        
        # Ejecutar usando el ejecutable actual de Python (el del entorno virtual)
        python_exe = sys.executable
        
        # Timeout de 60 segundos por si hace un bucle infinito
        result = subprocess.run([python_exe, temp_file_path], capture_output=True, text=True, timeout=60)
        
        try:
            os.remove(temp_file_path)
        except:
            pass
            
        salida = result.stdout.strip()
        error = result.stderr.strip()
        
        if result.returncode == 0:
            if not salida:
                return "Código ejecutado con éxito, pero no hubo salida (stdout vacío). Asegúrate de usar print() si quieres ver resultados."
            return f"Ejecución exitosa. Salida:\n{salida}"
        else:
            return f"El script falló con código {result.returncode}.\nStderr:\n{error}\nStdout:\n{salida}\n\nPor favor, corrige el error y vuelve a intentarlo."
            
    except subprocess.TimeoutExpired:
        return "Error: El script tardó más de 60 segundos y fue cancelado. Evita bucles infinitos."
    except Exception as e:
        return f"Error crítico del sistema al ejecutar: {e}"
