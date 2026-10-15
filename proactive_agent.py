"""
proactive_agent.py — Miku Proactive Agent v2
Sistema de alertas proactivas que usa activity_monitor.py como fuente de datos.
Clasifica apps en categorías y envía alertas al celular con voz cuando detecta
patrones de uso excesivo o eventos importantes.
"""
import threading
import time
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# ─── Clasificación de aplicaciones ─────────────────────────────────────────────

APP_CATEGORIES = {
    # Juegos
    "valorant.exe":         "juego",
    "riotclientservices.exe": "juego",
    "leagueclient.exe":     "juego",
    "league of legends.exe": "juego",
    "minecraft.exe":        "juego",
    "javaw.exe":            "juego",  # Minecraft Java
    "genshinimpact.exe":    "juego",
    "robloxplayerbeta.exe": "juego",
    "steamwebhelper.exe":   "juego",
    "csgo.exe":             "juego",
    "cs2.exe":              "juego",
    "fortnite.exe":         "juego",
    "epicgameslauncher.exe": "juego",
    
    # Ocio / Redes sociales
    "discord.exe":          "ocio",
    "telegram.exe":         "ocio",
    "whatsapp.exe":         "ocio",
    
    # Trabajo / Productividad
    "code.exe":             "trabajo",
    "antigravity.exe":      "trabajo",
    "devenv.exe":           "trabajo",
    "pycharm64.exe":        "trabajo",
    "idea64.exe":           "trabajo",
    "notepad++.exe":        "trabajo",
    "winword.exe":          "trabajo",
    "excel.exe":            "trabajo",
    "powerpnt.exe":         "trabajo",
    "powershell.exe":       "trabajo",
    "windowsterminal.exe":  "trabajo",
    "python.exe":           "trabajo",
    
    # Navegadores (neutro, depende del contenido)
    "chrome.exe":           "navegador",
    "firefox.exe":          "navegador",
    "msedge.exe":           "navegador",
    "opera.exe":            "navegador",
    "brave.exe":            "navegador",
    
    # Multimedia
    "spotify.exe":          "multimedia",
    "vlc.exe":              "multimedia",
    "obs64.exe":            "multimedia",
}

# ─── Umbrales de alerta (en minutos) ──────────────────────────────────────────

ALERT_THRESHOLDS = {
    "juego":      120,   # 2 horas de juego → alerta
    "ocio":       180,   # 3 horas de redes sociales → alerta
    "trabajo":    120,   # 2 horas de trabajo sin parar → recordar descanso
    "navegador":  180,   # 3 horas navegando → alerta suave
}

# Cooldown entre alertas de la misma categoría (en segundos)
ALERT_COOLDOWN = 7200  # 2 horas entre alertas del mismo tipo


class ProactiveAgent:
    def __init__(self, message_callback):
        """
        message_callback: función que recibe un prompt string y lo envía al LLM
                         para generar una respuesta proactiva de Miku.
        """
        self.message_callback = message_callback
        self.running = True
        
        # Timestamps de la última alerta por categoría
        self.last_alert_time: dict[str, float] = {}
        
        # Saludos diarios
        self.has_said_good_morning = False
        self.has_said_good_night = False
        self._last_greeting_date = None
        
    def _reset_daily_flags(self):
        """Resetea flags de saludos al cambiar de día."""
        today = datetime.now().date()
        if self._last_greeting_date != today:
            self.has_said_good_morning = False
            self.has_said_good_night = False
            self._last_greeting_date = today
    
    def _get_category_time(self, summary: list[dict]) -> dict[str, float]:
        """
        Dado el resumen de activity_monitor, calcula el tiempo total 
        por categoría de app.
        """
        category_minutes: dict[str, float] = {
            "juego": 0, "ocio": 0, "trabajo": 0, 
            "navegador": 0, "multimedia": 0, "otro": 0
        }
        
        for item in summary:
            proc = item.get("process", "").lower()
            category = APP_CATEGORIES.get(proc, "otro")
            category_minutes[category] += item.get("minutes", 0)
        
        return category_minutes
    
    def _can_send_alert(self, category: str) -> bool:
        """Verifica si ya pasó suficiente tiempo desde la última alerta de esta categoría."""
        now = time.time()
        last = self.last_alert_time.get(category, 0)
        return (now - last) >= ALERT_COOLDOWN
    
    def _mark_alert_sent(self, category: str):
        """Registra que se envió una alerta para esta categoría."""
        self.last_alert_time[category] = time.time()
    
    def _get_top_apps_in_category(self, summary: list[dict], category: str) -> list[str]:
        """Devuelve las apps más usadas de una categoría."""
        apps = []
        for item in summary:
            proc = item.get("process", "").lower()
            if APP_CATEGORIES.get(proc) == category:
                apps.append(f"{item['app']} ({item['time_display']})")
        return apps
    
    def run(self):
        """Loop principal del agente proactivo."""
        # Esperar 2 minutos al iniciar para que el sistema se estabilice
        time.sleep(120)
        
        while self.running:
            try:
                self._reset_daily_flags()
                now = datetime.now()
                current_hour = now.hour
                
                # ─── 1. Saludos espontáneos ───────────────────────
                if 7 <= current_hour <= 10 and not self.has_said_good_morning:
                    self.has_said_good_morning = True
                    prompt = (
                        "[SISTEMA INTERNO - ALERTA PROACTIVA]: "
                        "Dile los buenos días al usuario de forma muy alegre y motivadora. "
                        "Pregúntale qué van a hacer hoy. No uses asteriscos."
                    )
                    self.message_callback(prompt)
                    time.sleep(60)
                    continue
                    
                if 22 <= current_hour <= 23 and not self.has_said_good_night:
                    self.has_said_good_night = True
                    prompt = (
                        "[SISTEMA INTERNO - ALERTA PROACTIVA]: "
                        "Dile las buenas noches al usuario de forma cariñosa. "
                        "Coméntale que ya es tarde y debería ir pensando en dormir. "
                        "No uses asteriscos."
                    )
                    self.message_callback(prompt)
                    time.sleep(60)
                    continue
                
                # ─── 2. Analizar actividad con activity_monitor ───
                try:
                    from activity_monitor import get_activity_summary, get_current_activity
                    summary = get_activity_summary()
                    current = get_current_activity()
                except Exception:
                    time.sleep(60)
                    continue
                
                if not summary:
                    time.sleep(60)
                    continue
                
                category_time = self._get_category_time(summary)
                
                # ─── 3. Alertas por categoría ─────────────────────
                
                # 🎮 Alerta de juegos
                if (category_time["juego"] >= ALERT_THRESHOLDS["juego"] 
                    and self._can_send_alert("juego")):
                    
                    self._mark_alert_sent("juego")
                    apps = self._get_top_apps_in_category(summary, "juego")
                    apps_str = ", ".join(apps[:3])
                    hours = round(category_time["juego"] / 60, 1)
                    
                    prompt = (
                        f"[SISTEMA INTERNO - ALERTA PROACTIVA]: "
                        f"El usuario lleva {hours} horas jugando hoy ({apps_str}). "
                        f"Hazle un comentario divertido pero firme diciéndole que ya está muy "
                        f"viciado y que debería hacer algo productivo o al menos estirar "
                        f"y tomar agua. Sé juguetona pero insistente. No uses asteriscos."
                    )
                    self.message_callback(prompt)
                    time.sleep(300)  # Esperar 5 min antes de volver a chequear
                    continue
                
                # 💬 Alerta de redes sociales / ocio
                if (category_time["ocio"] >= ALERT_THRESHOLDS["ocio"]
                    and self._can_send_alert("ocio")):
                    
                    self._mark_alert_sent("ocio")
                    apps = self._get_top_apps_in_category(summary, "ocio")
                    apps_str = ", ".join(apps[:3])
                    hours = round(category_time["ocio"] / 60, 1)
                    
                    prompt = (
                        f"[SISTEMA INTERNO - ALERTA PROACTIVA]: "
                        f"El usuario lleva {hours} horas en redes sociales/chat ({apps_str}). "
                        f"Coméntale de forma amigable que ha estado mucho rato chateando "
                        f"y que tal vez debería hacer algo más productivo. "
                        f"Sé amigable y no regañona. No uses asteriscos."
                    )
                    self.message_callback(prompt)
                    time.sleep(300)
                    continue
                
                # 💻 Alerta de trabajo excesivo (descanso)
                if (category_time["trabajo"] >= ALERT_THRESHOLDS["trabajo"]
                    and self._can_send_alert("trabajo")):
                    
                    self._mark_alert_sent("trabajo")
                    apps = self._get_top_apps_in_category(summary, "trabajo")
                    apps_str = ", ".join(apps[:3])
                    hours = round(category_time["trabajo"] / 60, 1)
                    
                    prompt = (
                        f"[SISTEMA INTERNO - ALERTA PROACTIVA]: "
                        f"El usuario lleva {hours} horas trabajando sin parar ({apps_str}). "
                        f"Dile de forma cariñosa pero firme que debería descansar los ojos, "
                        f"estirar la espalda y tomar agua. Reconoce su esfuerzo y motívalo. "
                        f"No uses asteriscos."
                    )
                    self.message_callback(prompt)
                    time.sleep(300)
                    continue
                
            except Exception as e:
                logger.error(f"Error en ProactiveAgent: {e}")
            
            # Chequear cada 60 segundos
            time.sleep(60)
    
    def stop(self):
        self.running = False


def get_app_category(process_name: str) -> str:
    """Devuelve la categoría de una app dado su nombre de proceso."""
    return APP_CATEGORIES.get(process_name.lower(), "otro")


def start_proactive_agent(message_callback):
    """Inicia el agente proactivo en un hilo daemon."""
    agent = ProactiveAgent(message_callback)
    thread = threading.Thread(target=agent.run, daemon=True)
    thread.start()
    logger.info("Agente proactivo iniciado (alertas de actividad, saludos, descansos).")
    return agent
