import json
import threading

class MemoriaTemporal:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(MemoriaTemporal, cls).__new__(cls)
                cls._instance._inicializar()
            return cls._instance

    def _inicializar(self):
        self.tarea_actual = None
        self.paso_actual = None
        self.parametros_pendientes = {}
        self.historial_reciente = []

    def actualizar_estado(self, tarea: str = None, paso: str = None, parametros: dict = None):
        """Actualiza el estado actual de la tarea que Miku está realizando."""
        if tarea is not None:
            self.tarea_actual = tarea
        if paso is not None:
            self.paso_actual = paso
        if parametros is not None:
            # Mezclar parámetros nuevos con los existentes
            self.parametros_pendientes.update(parametros)

    def limpiar_estado(self):
        """Limpia el estado cuando la tarea se completa o se aborta."""
        self.tarea_actual = None
        self.paso_actual = None
        self.parametros_pendientes = {}

    def obtener_resumen_contexto(self) -> str:
        """Devuelve un string formateado para inyectar en el prompt del LLM."""
        if not self.tarea_actual:
            return "[MEMORIA TEMPORAL]: Ninguna tarea en progreso. Miku está libre."
        
        estado = f"[MEMORIA TEMPORAL]\n- Tarea actual: {self.tarea_actual}\n"
        if self.paso_actual:
            estado += f"- Paso actual (Última acción): {self.paso_actual}\n"
        
        if self.parametros_pendientes:
            estado += f"- Datos recolectados/pendientes: {json.dumps(self.parametros_pendientes, ensure_ascii=False)}\n"
            
        return estado

# Instancia global para ser importada por otros módulos
memoria_temporal_global = MemoriaTemporal()
