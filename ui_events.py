import threading

_ui_event = threading.Event()
_ui_data = None

def wait_for_ui_event(timeout=120):
    """Bloquea el hilo actual hasta que el usuario haga clic en la UI."""
    global _ui_data
    _ui_event.clear()
    _ui_data = None
    _ui_event.wait(timeout)
    return _ui_data

def set_ui_event(data):
    """Se llama desde server.py cuando llega un mensaje ws_send por WebSocket."""
    global _ui_data
    _ui_data = data
    _ui_event.set()
