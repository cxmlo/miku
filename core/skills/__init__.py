"""
core/skills/__init__.py
Punto de entrada para el sistema de skills nativas de Miku.
"""

from .registry import SkillRegistry, get_skill_registry

skill_registry = get_skill_registry()

__all__ = ["SkillRegistry", "get_skill_registry", "skill_registry"]
