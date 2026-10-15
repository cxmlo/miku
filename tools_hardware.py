import requests
import logging
import threading
import queue

ESP32_IP = "192.168.40.25"

# Cola para manejar peticiones de hardware en segundo plano
hardware_queue = queue.Queue()

def hardware_worker():
    """Hilo en segundo plano que procesa las peticiones al ESP32 sin bloquear a Miku."""
    while True:
        try:
            task = hardware_queue.get()
            if task is None:
                break # Para detener el hilo si fuera necesario
                
            url, params = task
            try:
                # El timeout puede ser corto porque no nos importa esperar,
                # pero al estar en otro hilo, no bloquea el cerebro de Miku.
                # requests.get(url, params=params, timeout=2) # DESACTIVADO POR AHORA
                logging.getLogger("Miku").info(f"[HARDWARE SIMULADO] Petición a {url} con {params} omitida.")
            except Exception as e:
                # Silenciamos el error para no spamear la consola constantemente si el robot está apagado
                pass
            finally:
                hardware_queue.task_done()
        except Exception:
            pass

# Iniciamos el hilo trabajador una sola vez al importar este módulo
worker_thread = threading.Thread(target=hardware_worker, daemon=True)
worker_thread.start()

def mover_cabeza_miku(pan: int, tilt: int) -> str:
    """
    Mueve la cabeza física de Miku usando los servomotores.
    'pan' controla izquierda/derecha (0 a 180, 90 es el centro).
    'tilt' controla arriba/abajo (0 a 180, 90 es el centro).
    """
    url = f"http://{ESP32_IP}/servo"
    params = {"pan": pan, "tilt": tilt}
    
    # En lugar de hacer requests.get() aquí, lo enviamos al hilo de fondo
    hardware_queue.put((url, params))
    
    # Retornamos éxito inmediato para que Miku siga pensando sin pausas
    return f"Se envió la orden de mover la cabeza a pan={pan}, tilt={tilt}."

def cambiar_expresion_miku(emocion: str) -> str:
    """
    Cambia la expresión facial de Miku en su pantalla OLED física.
    'emocion' debe ser "happy" (feliz) o "normal".
    """
    url = f"http://{ESP32_IP}/face"
    params = {"emotion": emocion}
    
    # En lugar de bloquear, lo enviamos a la cola asíncrona
    hardware_queue.put((url, params))
    
    # Retornamos éxito inmediato
    return f"Se envió la orden de cambiar expresión a {emocion}."
