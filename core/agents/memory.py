"""Per-agent isolated memory store with atomic persistence and compaction.
Safeguards memory integrity via atomic writes (.tmp + os.replace) and thread safety.
"""

from __future__ import annotations

import json
import os
import threading
import time
from typing import Any, Dict, List, Optional


class AgentMemory:
    """Manages an isolated memory partition for a specific agent."""

    def __init__(self, agent_id: str, storage_dir: str = "data/agents_memory"):
        self.agent_id = agent_id
        self.storage_dir = storage_dir
        self.file_path = os.path.join(self.storage_dir, f"{self.agent_id}.json")
        self._lock = threading.Lock()
        self._data: Dict[str, Any] = {
            "agent_id": self.agent_id,
            "created_at": time.time(),
            "updated_at": time.time(),
            "summary": "",
            "facts": {},
            "history": [],
        }
        self._load()

    def _ensure_dir(self) -> None:
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir, exist_ok=True)

    def _load(self) -> None:
        with self._lock:
            if not os.path.exists(self.file_path):
                return
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    if content.strip():
                        loaded = json.loads(content)
                        if isinstance(loaded, dict):
                            self._data.update(loaded)
            except Exception:
                # If reading fails or file is corrupt, retain initial default state
                pass

    def save(self) -> bool:
        """Atomically persist memory data using a temporary file and os.replace."""
        with self._lock:
            try:
                self._ensure_dir()
                self._data["updated_at"] = time.time()
                tmp_path = f"{self.file_path}.tmp"
                with open(tmp_path, "w", encoding="utf-8") as f:
                    json.dump(self._data, f, indent=2, ensure_ascii=False)
                    f.flush()
                    os.fsync(f.fileno())
                os.replace(tmp_path, self.file_path)
                return True
            except Exception:
                if os.path.exists(tmp_path):
                    try:
                        os.remove(tmp_path)
                    except Exception:
                        pass
                return False

    def add_interaction(self, role: str, content: str, meta: Optional[Dict[str, Any]] = None) -> None:
        """Record an interaction entry and compact if token budget is exceeded."""
        entry = {
            "role": role,
            "content": content,
            "timestamp": time.time(),
            "meta": meta or {},
        }
        with self._lock:
            self._data["history"].append(entry)
            self._check_and_compact()
        self.save()

    def set_fact(self, key: str, value: Any) -> None:
        """Store or update a key-value fact."""
        with self._lock:
            self._data["facts"][key] = value
        self.save()

    def get_fact(self, key: str, default: Any = None) -> Any:
        with self._lock:
            return self._data["facts"].get(key, default)

    def clear(self) -> None:
        """Clear memory for this agent."""
        with self._lock:
            self._data["facts"] = {}
            self._data["history"] = []
            self._data["summary"] = ""
            self._data["updated_at"] = time.time()
        self.save()

    def get_context_prompt(self, max_entries: int = 10) -> str:
        """Generate a summarized context prompt for LLM injection."""
        with self._lock:
            lines = []
            if self._data.get("summary"):
                lines.append(f"Context Summary: {self._data['summary']}")

            facts = self._data.get("facts", {})
            if facts:
                fact_strs = [f"- {k}: {v}" for k, v in list(facts.items())[:15]]
                lines.append("Persisted Facts:\n" + "\n".join(fact_strs))

            recent = self._data.get("history", [])[-max_entries:]
            if recent:
                hist_strs = [f"[{item['role']}]: {item['content']}" for item in recent]
                lines.append("Recent History:\n" + "\n".join(hist_strs))

            return "\n\n".join(lines)

    def _estimate_tokens(self) -> int:
        total_chars = len(self._data.get("summary", ""))
        for f, v in self._data.get("facts", {}).items():
            total_chars += len(str(f)) + len(str(v))
        for item in self._data.get("history", []):
            total_chars += len(item.get("content", ""))
        return total_chars // 4

    def _check_and_compact(self) -> None:
        """Compact memory if estimated token count exceeds 4000 or history > 30 entries."""
        history = self._data.get("history", [])
        if len(history) <= 15 and self._estimate_tokens() < 4000:
            return

        # Keep the latest 10 items pristine, summarize older items
        older = history[:-10]
        recent = history[-10:]

        summary_snippets = []
        for item in older:
            text = item.get("content", "").strip()
            if text:
                snippet = text if len(text) <= 100 else f"{text[:97]}..."
                summary_snippets.append(f"{item.get('role', 'user')}: {snippet}")

        if summary_snippets:
            compact_note = "; ".join(summary_snippets[-15:])
            existing = self._data.get("summary", "")
            if existing:
                self._data["summary"] = f"{existing} | Previous: {compact_note}"
            else:
                self._data["summary"] = f"Previous context: {compact_note}"

        self._data["history"] = recent


class MemoryManager:
    """Manages active memory partitions for all agents."""

    def __init__(self, storage_dir: str = "data/agents_memory"):
        self.storage_dir = storage_dir
        self._pools: Dict[str, AgentMemory] = {}
        self._lock = threading.Lock()

    def get_memory(self, agent_id: str) -> AgentMemory:
        with self._lock:
            if agent_id not in self._pools:
                self._pools[agent_id] = AgentMemory(agent_id, self.storage_dir)
            return self._pools[agent_id]


# Global memory manager
memory_manager = MemoryManager()
