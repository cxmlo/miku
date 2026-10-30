"""Local token telemetry and cost accounting for Miku.
Tracks prompt tokens, completion tokens, response latency, and estimated USD costs per model and agent.
"""

from __future__ import annotations

import json
import os
import threading
import time
from typing import Any, Dict, List, Optional


# Pricing in USD per 1,000,000 tokens
MODEL_PRICING: Dict[str, Dict[str, float]] = {
    "gemini-2.5-flash": {"input": 0.075, "output": 0.30},
    "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
    "gemini-1.5-pro": {"input": 1.25, "output": 5.00},
    "claude-3-7-sonnet": {"input": 3.00, "output": 15.00},
    "claude-3-5-sonnet": {"input": 3.00, "output": 15.00},
    "deepseek-coder": {"input": 0.14, "output": 0.28},
    "deepseek-chat": {"input": 0.14, "output": 0.28},
    "groq-llama-3.3-70b": {"input": 0.59, "output": 0.79},
    "default": {"input": 0.50, "output": 1.50},
}


class UsageTelemetry:
    """Tracks token consumption, latency, and estimated costs."""

    def __init__(self, storage_path: str = "data/usage_telemetry.json"):
        self.storage_path = storage_path
        self._lock = threading.Lock()
        self._data: Dict[str, Any] = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_prompt_tokens": 0,
            "total_completion_tokens": 0,
            "total_tokens": 0,
            "total_estimated_cost_usd": 0.0,
            "total_latency_ms": 0.0,
            "by_model": {},
            "by_agent": {},
            "recent_events": [],
        }
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
                        loaded = json.loads(content)
                        if isinstance(loaded, dict):
                            self._data.update(loaded)
            except Exception:
                pass

    def _save(self) -> bool:
        try:
            self._ensure_dir()
            tmp = f"{self.storage_path}.tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, self.storage_path)
            return True
        except Exception:
            if os.path.exists(tmp):
                try:
                    os.remove(tmp)
                except Exception:
                    pass
            return False

    @staticmethod
    def calculate_cost(model_name: str, prompt_tokens: int, completion_tokens: int) -> float:
        clean_model = model_name.lower().split("/")[-1]
        pricing = MODEL_PRICING.get(clean_model, MODEL_PRICING["default"])
        cost_in = (prompt_tokens / 1_000_000.0) * pricing["input"]
        cost_out = (completion_tokens / 1_000_000.0) * pricing["output"]
        return round(cost_in + cost_out, 6)

    def record_request(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        latency_ms: float,
        success: bool = True,
        agent_id: str = "miku",
    ) -> Dict[str, Any]:
        """Record an API inference event and calculate cost."""
        total_tokens = prompt_tokens + completion_tokens
        cost = self.calculate_cost(model, prompt_tokens, completion_tokens) if success else 0.0

        with self._lock:
            self._data["total_requests"] += 1
            if success:
                self._data["successful_requests"] += 1
                self._data["total_prompt_tokens"] += prompt_tokens
                self._data["total_completion_tokens"] += completion_tokens
                self._data["total_tokens"] += total_tokens
                self._data["total_estimated_cost_usd"] = round(
                    self._data["total_estimated_cost_usd"] + cost, 6
                )
                self._data["total_latency_ms"] += latency_ms
            else:
                self._data["failed_requests"] += 1

            # Model breakdown
            by_model = self._data["by_model"]
            if model not in by_model:
                by_model[model] = {
                    "requests": 0,
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0,
                    "estimated_cost_usd": 0.0,
                    "total_latency_ms": 0.0,
                }
            m_stat = by_model[model]
            m_stat["requests"] += 1
            if success:
                m_stat["prompt_tokens"] += prompt_tokens
                m_stat["completion_tokens"] += completion_tokens
                m_stat["total_tokens"] += total_tokens
                m_stat["estimated_cost_usd"] = round(m_stat["estimated_cost_usd"] + cost, 6)
                m_stat["total_latency_ms"] += latency_ms

            # Agent breakdown
            by_agent = self._data["by_agent"]
            if agent_id not in by_agent:
                by_agent[agent_id] = {
                    "requests": 0,
                    "total_tokens": 0,
                    "estimated_cost_usd": 0.0,
                }
            a_stat = by_agent[agent_id]
            a_stat["requests"] += 1
            if success:
                a_stat["total_tokens"] += total_tokens
                a_stat["estimated_cost_usd"] = round(a_stat["estimated_cost_usd"] + cost, 6)

            # Keep last 50 events in telemetry ring buffer
            event = {
                "timestamp": time.time(),
                "model": model,
                "agent_id": agent_id,
                "tokens": total_tokens,
                "cost_usd": cost,
                "latency_ms": round(latency_ms, 1),
                "success": success,
            }
            recent = self._data.get("recent_events", [])
            recent.append(event)
            if len(recent) > 50:
                recent = recent[-50:]
            self._data["recent_events"] = recent

            self._save()

        return {
            "tokens": total_tokens,
            "cost_usd": cost,
            "latency_ms": latency_ms,
        }

    def get_dashboard_summary(self) -> Dict[str, Any]:
        with self._lock:
            succ = self._data["successful_requests"]
            avg_lat = round(self._data["total_latency_ms"] / succ, 1) if succ > 0 else 0.0
            return {
                "total_requests": self._data["total_requests"],
                "successful_requests": succ,
                "failed_requests": self._data["failed_requests"],
                "total_tokens": self._data["total_tokens"],
                "prompt_tokens": self._data["total_prompt_tokens"],
                "completion_tokens": self._data["total_completion_tokens"],
                "total_cost_usd": round(self._data["total_estimated_cost_usd"], 4),
                "avg_latency_ms": avg_lat,
                "by_model": self._data["by_model"],
                "by_agent": self._data["by_agent"],
                "recent_events": self._data.get("recent_events", [])[-10:],
            }


# Global telemetry singleton
usage_telemetry = UsageTelemetry()
