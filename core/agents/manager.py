"""Agent Manager for Miku Companion.
Coordinates built-in and user-defined custom agents, keyword routing, and vault credential bindings.
"""

from __future__ import annotations

import json
import os
import re
import threading
import time
from typing import Any, Dict, List, Optional


BUILTIN_AGENTS: List[Dict[str, Any]] = [
    {
        "id": "korus",
        "name": "Korus",
        "role": "Claude Code",
        "category": "code",
        "system_prompt": "You are Korus, a specialized Claude Code agent for architecture refactoring, bug fixes, and patch drafting.",
        "model": "claude-3-7-sonnet",
        "api_key_env_var": "ANTHROPIC_API_KEY",
        "requires_api_key": True,
        "temperature": 0.2,
        "autonomy_level": "semi_autonomous",
        "cli_permissions": True,
        "assigned_skills": ["git-code-reviewer"],
        "assigned_mcp_servers": ["github-mcp", "filesystem-mcp"],
        "isolated_memory": True,
        "trigger_keywords": ["korus", "claude", "patch", "refactor", "bugfix"],
        "avatar_color": "#7c3aed",
        "is_builtin": True,
        "phases": ["Read", "Edit", "Bash", "Done"],
    },
    {
        "id": "antigravity",
        "name": "Antigravity",
        "role": "Project Architect",
        "category": "code",
        "system_prompt": "You are Antigravity, an advanced coding agent that analyzes complex multi-file structures and designs robust software architecture.",
        "model": "gemini-2.5-flash",
        "api_key_env_var": "GEMINI_API_KEY",
        "requires_api_key": False,
        "temperature": 0.3,
        "autonomy_level": "semi_autonomous",
        "cli_permissions": True,
        "assigned_skills": ["git-code-reviewer", "desktop-automation"],
        "assigned_mcp_servers": ["filesystem-mcp"],
        "isolated_memory": True,
        "trigger_keywords": ["antigravity", "architect", "estructura", "diseño de sistema"],
        "avatar_color": "#06b6d4",
        "is_builtin": True,
        "phases": ["Read", "Edit", "Bash", "Done"],
    },
    {
        "id": "codex",
        "name": "Codex",
        "role": "Autonomous Code Generator",
        "category": "code",
        "system_prompt": "You are Codex, high-speed code generation specialist for quick scripts, algorithms, and microservices.",
        "model": "deepseek-coder",
        "api_key_env_var": "DEEPSEEK_API_KEY",
        "requires_api_key": True,
        "temperature": 0.2,
        "autonomy_level": "semi_autonomous",
        "cli_permissions": True,
        "assigned_skills": ["git-code-reviewer"],
        "assigned_mcp_servers": ["filesystem-mcp"],
        "isolated_memory": True,
        "trigger_keywords": ["codex", "code", "generar codigo", "algoritmo", "script"],
        "avatar_color": "#10b981",
        "is_builtin": True,
        "phases": ["Read", "Edit", "Bash", "Done"],
    },
    {
        "id": "scholar",
        "name": "Scholar",
        "role": "Research Analyst",
        "category": "research",
        "system_prompt": "You are Scholar, an academic and technical research agent specialized in synthesis, citations, and doc scraping.",
        "model": "gemini-2.5-flash",
        "api_key_env_var": "GEMINI_API_KEY",
        "requires_api_key": False,
        "temperature": 0.4,
        "autonomy_level": "supervised",
        "cli_permissions": False,
        "assigned_skills": ["web-researcher"],
        "assigned_mcp_servers": ["web-search-mcp"],
        "isolated_memory": True,
        "trigger_keywords": ["scholar", "research", "investigar", "paper", "documentacion", "resumen"],
        "avatar_color": "#3b82f6",
        "is_builtin": True,
        "phases": ["Search", "Extract", "Synthesize", "Done"],
    },
    {
        "id": "indexer",
        "name": "Indexer",
        "role": "Data & SQL Engineer",
        "category": "data",
        "system_prompt": "You are Indexer, specializing in data parsing, database migrations, SQL queries, and CSV/JSON analysis.",
        "model": "groq-llama-3.3-70b",
        "api_key_env_var": "GROQ_API_KEY",
        "requires_api_key": True,
        "temperature": 0.1,
        "autonomy_level": "supervised",
        "cli_permissions": False,
        "assigned_skills": ["desktop-automation"],
        "assigned_mcp_servers": ["sqlite-mcp"],
        "isolated_memory": True,
        "trigger_keywords": ["indexer", "sql", "database", "datos", "migracion", "csv"],
        "avatar_color": "#f59e0b",
        "is_builtin": True,
        "phases": ["Scan", "Process", "Write", "Done"],
    },
    {
        "id": "sentinel",
        "name": "Sentinel",
        "role": "Operations & Watchdog",
        "category": "general",
        "system_prompt": "You are Sentinel, an operations watchdog that monitors uptime, processes, resource consumption, and alerts.",
        "model": "gemini-2.5-flash",
        "api_key_env_var": "GEMINI_API_KEY",
        "requires_api_key": False,
        "temperature": 0.1,
        "autonomy_level": "autonomous",
        "cli_permissions": True,
        "assigned_skills": ["desktop-automation"],
        "assigned_mcp_servers": [],
        "isolated_memory": True,
        "trigger_keywords": ["sentinel", "guard", "monitor", "alerta", "vigilar"],
        "avatar_color": "#ef4444",
        "is_builtin": True,
        "phases": ["Listen", "Think", "Action", "Done"],
    },
]


class AgentManager:
    """Manages agents repository, custom creation, and dispatch routing."""

    def __init__(self, storage_path: str = "data/custom_agents.json"):
        self.storage_path = storage_path
        self._custom_agents: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self._load()

    def _ensure_dir(self) -> None:
        folder = os.path.dirname(self.storage_path)
        if folder and not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)

    def _load(self) -> None:
        with self._lock:
            if not os.path.exists(self.storage_path):
                return
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    if content.strip():
                        items = json.loads(content)
                        if isinstance(items, list):
                            for item in items:
                                if isinstance(item, dict) and "id" in item:
                                    self._custom_agents[item["id"]] = item
            except Exception:
                pass

    def _save(self) -> bool:
        try:
            self._ensure_dir()
            tmp_path = f"{self.storage_path}.tmp"
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(list(self._custom_agents.values()), f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, self.storage_path)
            return True
        except Exception:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
            return False

    @staticmethod
    def generate_vault_env_var(agent_id: str) -> str:
        clean = re.sub(r"[^A-Za-z0-9_]+", "_", agent_id).upper().strip("_")
        return f"MIKU_AGENT_{clean}_KEY"

    @staticmethod
    def default_phases_for_category(category: str) -> List[str]:
        cat = category.lower()
        if cat == "code":
            return ["Read", "Edit", "Bash", "Done"]
        elif cat == "research":
            return ["Search", "Extract", "Synthesize", "Done"]
        elif cat == "data":
            return ["Scan", "Process", "Write", "Done"]
        else:
            return ["Listen", "Think", "Action", "Done"]

    def create_agent(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new custom agent with automated ID and Vault token binding."""
        with self._lock:
            raw_name = data.get("name", "").strip() or "Custom Agent"
            agent_id = data.get("id") or re.sub(r"[^a-z0-9]+", "-", raw_name.lower()).strip("-")
            if not agent_id:
                agent_id = f"agent_{int(time.time())}"

            # Avoid ID collision with built-in or existing
            builtin_ids = {a["id"] for a in BUILTIN_AGENTS}
            if agent_id in builtin_ids or agent_id in self._custom_agents:
                agent_id = f"{agent_id}_{int(time.time()) % 1000}"

            category = data.get("category", "general")
            phases = data.get("phases") or self.default_phases_for_category(category)

            agent_record = {
                "id": agent_id,
                "name": raw_name,
                "role": data.get("role", "Specialized Assistant"),
                "category": category,
                "system_prompt": data.get("system_prompt", ""),
                "model": data.get("model", "gemini-2.5-flash"),
                "api_key_env_var": data.get("api_key_env_var") or self.generate_vault_env_var(agent_id),
                "requires_api_key": bool(data.get("requires_api_key", False)),
                "temperature": float(data.get("temperature", 0.3)),
                "autonomy_level": data.get("autonomy_level", "supervised"),
                "cli_permissions": bool(data.get("cli_permissions", False)),
                "assigned_skills": list(data.get("assigned_skills", [])),
                "assigned_mcp_servers": list(data.get("assigned_mcp_servers", [])),
                "isolated_memory": bool(data.get("isolated_memory", True)),
                "trigger_keywords": list(data.get("trigger_keywords", [])),
                "avatar_color": data.get("avatar_color", "#8b5cf6"),
                "is_builtin": False,
                "phases": phases,
                "created_at": time.time(),
            }

            self._custom_agents[agent_id] = agent_record
            self._save()
            return agent_record

    def update_agent(self, agent_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        with self._lock:
            if agent_id not in self._custom_agents:
                return None
            agent = self._custom_agents[agent_id]
            for key, val in updates.items():
                if key not in ("id", "is_builtin", "created_at"):
                    agent[key] = val
            self._save()
            return agent

    def delete_agent(self, agent_id: str) -> bool:
        with self._lock:
            if agent_id in self._custom_agents:
                del self._custom_agents[agent_id]
                self._save()
                return True
            return False

    def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            for b in BUILTIN_AGENTS:
                if b["id"] == agent_id:
                    return dict(b)
            if agent_id in self._custom_agents:
                return dict(self._custom_agents[agent_id])
            return None

    def list_all_agents(self) -> List[Dict[str, Any]]:
        with self._lock:
            all_agents = [dict(b) for b in BUILTIN_AGENTS]
            all_agents.extend([dict(c) for c in self._custom_agents.values()])
            return all_agents

    def match_agent_for_prompt(self, text: str) -> Optional[Dict[str, Any]]:
        """Identify if a prompt targets a specific agent via /mention or keywords."""
        lower_text = text.lower().strip()

        # Check explicit slash command: e.g. "/antigravity refactor index.ts"
        slash_match = re.match(r"^/([a-zA-Z0-9_\-]+)", lower_text)
        if slash_match:
            slug = slash_match.group(1).lower()
            agent = self.get_agent(slug)
            if agent:
                return agent

        # Check keywords
        all_agents = self.list_all_agents()
        for agent in all_agents:
            # Check agent name directly
            if agent["name"].lower() in lower_text:
                return agent
            # Check registered keywords
            for kw in agent.get("trigger_keywords", []):
                if kw.lower() in lower_text:
                    return agent

        return None


# Global agent manager singleton
agent_manager = AgentManager()
