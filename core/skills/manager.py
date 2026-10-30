"""
Gestor de Skills Nativas de Miku (core/skills/manager.py)
Permite a Miku activar habilidades especializadas de forma autonoma segun la tarea,
con limite concurrente de maximo 2 skills para evitar saturar el contexto,
recarga en caliente (hot-reload), y soporte para importar desde GitHub o crear en vivo.
"""

import json
import os
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

SKILLS_DIR = Path(__file__).resolve().parent / "definitions"
SKILLS_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_SKILLS: List[Dict[str, Any]] = [
    {
        "id": "git_reviewer",
        "name": "Revisor de Git y Commits",
        "category": "code",
        "description": "Audita cambios en el repositorio, analiza diffs y redacta mensajes de commit profesionales siguiendo Conventional Commits.",
        "triggers": ["git", "commit", "diff", "branch", "rama", "pull request", "revisar cambios"],
        "tools_required": ["ejecutar_comando_consola", "solicitar_aprobacion_comando"],
        "system_prompt_addon": "Eres el Revisor de Git. Analiza los diffs con precision, verifica que no existan credenciales expuestas y formula commits semanticos (feat, fix, refactor, docs).",
        "author": "Miku Team",
        "version": "1.0.0"
    },
    {
        "id": "web_researcher",
        "name": "Investigador Web y Sintesis",
        "category": "research",
        "description": "Realiza busquedas estructuradas, extrae contenido de paginas y sintetiza reportes completos citando fuentes verificadas.",
        "triggers": ["investiga", "busca en internet", "google", "noticias", "que paso con", "resumen web"],
        "tools_required": ["consultar_google_grounding", "inspeccionar_url_rapido"],
        "system_prompt_addon": "Eres el Investigador Web. Busca fuentes veraces, contrasta informacion y genera resumenes claros con citas y datos comprobados.",
        "author": "Miku Team",
        "version": "1.0.0"
    },
    {
        "id": "pc_controller",
        "name": "Controlador del Sistema y Atajos",
        "category": "desktop",
        "description": "Automatiza la apertura de aplicaciones, control de ventanas, exploracion de carpetas y acciones rapidas de escritorio.",
        "triggers": ["abre", "cierra", "busca archivo", "carpeta", "captura", "pantalla", "bateria"],
        "tools_required": ["ejecutar_comando_consola", "describir_pantalla_multimodal"],
        "system_prompt_addon": "Eres el Controlador de PC. Asiste al usuario en tareas de escritorio de forma rapida y segura, respetando los modos de ejecucion.",
        "author": "Miku Team",
        "version": "1.0.0"
    },
    {
        "id": "code_refactor",
        "name": "Refactorizacion y Arquitectura",
        "category": "code",
        "description": "Reestructura codigo para mejorar legibilidad, desacoplamiento y rendimiento, aplicando principios SOLID y modularidad.",
        "triggers": ["refactoriza", "limpia este codigo", "modulariza", "optimiza", "arquitectura"],
        "tools_required": ["ejecutar_comando_consola", "solicitar_aprobacion_comando"],
        "system_prompt_addon": "Eres el Arquitecto de Software. Sugiere y ejecuta refactorizaciones limpias, dividiendo responsabilidades y manteniendo pruebas intactas.",
        "author": "Miku Team",
        "version": "1.0.0"
    }
]


class SkillManager:
    """Gestiona el registro, persistencia y auto-activacion de Skills Nativas de Miku."""

    def __init__(self, definitions_dir: Path = SKILLS_DIR) -> None:
        self.definitions_dir = definitions_dir
        self.definitions_dir.mkdir(parents=True, exist_ok=True)
        self._skills: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()
        self._last_scan_time = 0.0
        self._seed_default_skills()
        self.reload_skills()

    def _seed_default_skills(self) -> None:
        """Crea los archivos iniciales si no existen aun."""
        for skill in DEFAULT_SKILLS:
            skill_file = self.definitions_dir / f"{skill['id']}.json"
            if not skill_file.exists():
                skill_file.write_text(json.dumps(skill, indent=2, ensure_ascii=False), encoding="utf-8")

    def reload_skills(self) -> None:
        """Carga o recarga en caliente todas las Skills en disco."""
        with self._lock:
            loaded: Dict[str, Dict[str, Any]] = {}
            for path in self.definitions_dir.glob("*.json"):
                try:
                    data = json.loads(path.read_text(encoding="utf-8"))
                    if isinstance(data, dict) and "id" in data:
                        loaded[data["id"]] = data
                except Exception:
                    continue
            self._skills = loaded
            self._last_scan_time = time.time()

    def get_all_skills(self) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self._skills.values())

    def get_skill(self, skill_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self._skills.get(skill_id)

    def save_skill(self, skill_data: Dict[str, Any]) -> bool:
        """Guarda o actualiza una Skill de forma atomica."""
        skill_id = str(skill_data.get("id", "")).strip().lower()
        if not skill_id:
            return False
        skill_data["id"] = skill_id
        target = self.definitions_dir / f"{skill_id}.json"
        tmp = target.with_suffix(".tmp")
        with self._lock:
            tmp.write_text(json.dumps(skill_data, indent=2, ensure_ascii=False), encoding="utf-8")
            tmp.replace(target)
            self._skills[skill_id] = skill_data
            return True

    def delete_skill(self, skill_id: str) -> bool:
        target = self.definitions_dir / f"{skill_id}.json"
        with self._lock:
            if target.exists():
                target.unlink(missing_ok=True)
            removed = self._skills.pop(skill_id, None)
            return removed is not None

    def dispatch_skills_for_prompt(self, user_prompt: str, max_concurrent: int = 2) -> List[Dict[str, Any]]:
        """
        Analiza el texto del usuario y selecciona de forma autonoma las Skills mas relevantes,
        respetando un limite estricto de concurrencia para proteger el contexto.
        """
        p_low = (user_prompt or "").lower()
        scored: List[tuple[int, Dict[str, Any]]] = []

        with self._lock:
            for skill in self._skills.values():
                score = 0
                triggers = skill.get("triggers", [])
                for trig in triggers:
                    t_clean = str(trig).lower().strip()
                    if t_clean and t_clean in p_low:
                        score += 2
                name_words = skill.get("name", "").lower().split()
                for nw in name_words:
                    if len(nw) > 3 and nw in p_low:
                        score += 1
                if score > 0:
                    scored.append((score, skill))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored[:max_concurrent]]


_GLOBAL_SKILL_MANAGER: Optional[SkillManager] = None
_INIT_LOCK = threading.Lock()


def get_skill_manager() -> SkillManager:
    global _GLOBAL_SKILL_MANAGER
    if _GLOBAL_SKILL_MANAGER is None:
        with _INIT_LOCK:
            if _GLOBAL_SKILL_MANAGER is None:
                _GLOBAL_SKILL_MANAGER = SkillManager()
    return _GLOBAL_SKILL_MANAGER
