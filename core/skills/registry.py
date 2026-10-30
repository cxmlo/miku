"""
Sistema de Skills Nativas de Miku (core/skills/registry.py).
Gestiona las capacidades especializadas que Miku detecta y activa autonomamente
segun la intencion del usuario, limitando la concurrencia a un maximo de 2 skills
para evitar saturar la ventana de contexto de los modelos LLM.
"""

import json
import os
import re
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

SKILLS_DIR = Path(__file__).resolve().parent / "installed"
SKILLS_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_NATIVE_SKILLS: List[Dict[str, Any]] = [
    {
        "id": "git-code-reviewer",
        "name": "Revisor de Git y Codigo",
        "category": "Desarrollo",
        "description": "Analiza diffs de git, revisa calidad de codigo, sugiere refactorizaciones y detecta fallos de sintaxis.",
        "triggers": ["git diff", "commit", "revisar codigo", "analizar codigo", "pull request", "refactorizar", "branch"],
        "tools_required": ["ejecutar_comando_consola", "solicitar_aprobacion_comando"],
        "max_concurrent": 1,
        "system_prompt_addon": "Especialidad activa: Revisor de Codigo. Analiza diffs con rigor, verifica impacto antes de commits y resume cambios de forma limpia."
    },
    {
        "id": "web-researcher",
        "name": "Investigador Web y Grounding",
        "category": "Investigacion",
        "description": "Realiza busquedas web estructuradas, extrae fuentes confiables y sintetiza reportes actualizados.",
        "triggers": ["busca en internet", "investiga", "ultimas noticias", "fuente web", "documentacion oficial", "grounding"],
        "tools_required": ["consultar_google_grounding", "inspeccionar_url_rapido"],
        "max_concurrent": 1,
        "system_prompt_addon": "Especialidad activa: Investigador Web. Cita fuentes verificadas, sintetiza con datos concretos y reporta hechos recientes."
    },
    {
        "id": "desktop-automation",
        "name": "Automatizacion de Escritorio y CLI",
        "category": "Sistema",
        "description": "Ejecuta tareas en terminal, manipula archivos locales y realiza acciones de sistema con prevencion de bloqueos.",
        "triggers": ["ejecuta en terminal", "corre comando", "instala dependencia", "mover archivos", "crea carpeta", "script bash"],
        "tools_required": ["ejecutar_comando_consola", "solicitar_aprobacion_comando"],
        "max_concurrent": 1,
        "system_prompt_addon": "Especialidad activa: Automatizacion de Escritorio. Usa siempre comandos no bloqueantes e inyecta banderas no interactivas como --yes."
    },
    {
        "id": "phone-link-assistant",
        "name": "Controlador Miku-Link Celular",
        "category": "Dispositivos",
        "description": "Sincroniza portapapeles, envia archivos al telefono y gestiona comandos remotos para Android.",
        "triggers": ["celular", "telefono", "miku-link", "portapapeles movil", "enviar al telefono", "alarma movil"],
        "tools_required": ["enviar_archivo_celular", "sincronizar_portapapeles"],
        "max_concurrent": 1,
        "system_prompt_addon": "Especialidad activa: Miku-Link. Coordina ordenes con la aplicacion movil respetando la conexion en segundo plano."
    },
    {
        "id": "study-pomodoro",
        "name": "Asistente de Enfoque y Pomodoro",
        "category": "Productividad",
        "description": "Temporizadores de concentracion, bloques de estudio y registro de actividad productiva.",
        "triggers": ["pomodoro", "temporizador", "modo estudio", "concentracion", "bloque de trabajo", "descanso"],
        "tools_required": ["gestionar_alerta_actividad"],
        "max_concurrent": 1,
        "system_prompt_addon": "Especialidad activa: Enfoque y Pomodoro. Administra pausas regulares y mantiene respuestas concisas sin distracciones."
    }
]


class SkillRegistry:
    """Registro y despachador de Skills nativas en memoria con recarga dinamica."""

    def __init__(self, directory: Optional[Any] = None, storage_dir: Optional[Any] = None):
        target = storage_dir or directory or SKILLS_DIR
        self.directory = Path(target)
        self.directory.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._skills: Dict[str, Dict[str, Any]] = {}
        self._last_loaded_mtime: float = 0.0
        self.bootstrap_defaults()
        self.reload()

    def bootstrap_defaults(self) -> None:
        """Escribe las skills predefinidas si la carpeta esta vacia."""
        for skill in DEFAULT_NATIVE_SKILLS:
            path = self.directory / f"{skill['id']}.json"
            if not path.exists():
                try:
                    path.write_text(json.dumps(skill, indent=2, ensure_ascii=False), encoding="utf-8")
                except Exception:
                    pass

    def reload(self) -> None:
        """Carga en memoria todos los archivos .json de la carpeta de skills."""
        with self._lock:
            skills = {}
            for path in self.directory.glob("*.json"):
                try:
                    data = json.loads(path.read_text(encoding="utf-8"))
                    if isinstance(data, dict) and "id" in data:
                        skills[data["id"]] = data
                except Exception:
                    continue
            self._skills = skills
            self._last_loaded_mtime = time.time()

    def list_skills(self) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self._skills.values())

    def get_skill(self, skill_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self._skills.get(skill_id)

    def save_skill(self, skill_data: Dict[str, Any]) -> bool:
        """Crea o actualiza una skill en disco y recarga memoria."""
        skill_id = str(skill_data.get("id") or "").strip().lower()
        if not skill_id or not re.match(r"^[a-z0-9\-_]+$", skill_id):
            return False
        with self._lock:
            path = self.directory / f"{skill_id}.json"
            tmp_path = path.with_suffix(".tmp")
            try:
                tmp_path.write_text(json.dumps(skill_data, indent=2, ensure_ascii=False), encoding="utf-8")
                tmp_path.replace(path)
                self._skills[skill_id] = skill_data
                return True
            except Exception:
                if tmp_path.exists():
                    tmp_path.unlink()
                return False

    def delete_skill(self, skill_id: str) -> bool:
        with self._lock:
            path = self.directory / f"{skill_id}.json"
            if path.exists():
                try:
                    path.unlink()
                    self._skills.pop(skill_id, None)
                    return True
                except Exception:
                    return False
            return False

    def match_skills(self, user_prompt: str, max_skills: int = 2) -> List[Dict[str, Any]]:
        """
        Analiza el texto del usuario y activa hasta `max_skills` (maximo 2)
        segun la densidad de palabras clave coincidentes.
        """
        text = (user_prompt or "").lower()
        scored: List[tuple[int, Dict[str, Any]]] = []

        with self._lock:
            for skill in self._skills.values():
                score = 0
                triggers = skill.get("triggers", [])
                for trig in triggers:
                    trig_clean = trig.lower().strip()
                    if trig_clean in text:
                        score += 3
                    else:
                        words = trig_clean.split()
                        if len(words) > 1 and all(w in text for w in words):
                            score += 2
                if score > 0:
                    scored.append((score, skill))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [skill for _, skill in scored[:max_skills]]

    def match_skills_for_prompt(self, user_prompt: str, max_skills: int = 2) -> List[Dict[str, Any]]:
        return self.match_skills(user_prompt, max_skills=max_skills)

    def create_or_update_skill(self, skill_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        ok = self.save_skill(skill_data)
        return skill_data if ok else None


_REGISTRY: Optional[SkillRegistry] = None
_INIT_LOCK = threading.Lock()


def get_skill_registry() -> SkillRegistry:
    global _REGISTRY
    if _REGISTRY is None:
        with _INIT_LOCK:
            if _REGISTRY is None:
                _REGISTRY = SkillRegistry()
    return _REGISTRY
