"""Circuit breaker and provider fallback router for Miku LLM queries.
Prevents cascading failures on HTTP 429 (rate limits) and 5xx errors by seamlessly rerouting to healthy models.
"""

from __future__ import annotations

import threading
import time
from typing import Dict, List, Optional, Tuple


class ProviderState:
    def __init__(self, name: str, fallback: Optional[str] = None):
        self.name = name
        self.fallback = fallback
        self.state: str = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.failure_count: int = 0
        self.last_failure_time: float = 0.0
        self.last_error: str = ""
        self.consecutive_successes: int = 0


class CircuitBreaker:
    """Manages failure thresholds and automatic failover across LLM providers."""

    def __init__(
        self,
        failure_threshold: int = 3,
        cooldown_seconds: float = 60.0,
    ):
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self._lock = threading.Lock()
        self._providers: Dict[str, ProviderState] = {
            "gemini": ProviderState("gemini", fallback="groq"),
            "groq": ProviderState("groq", fallback="deepseek"),
            "anthropic": ProviderState("anthropic", fallback="gemini"),
            "deepseek": ProviderState("deepseek", fallback="groq"),
        }

    def register_provider(self, name: str, fallback: Optional[str] = None) -> None:
        with self._lock:
            if name not in self._providers:
                self._providers[name] = ProviderState(name, fallback=fallback)

    def record_success(self, provider_name: str) -> None:
        with self._lock:
            p = self._providers.get(provider_name)
            if not p:
                return
            p.consecutive_successes += 1
            if p.state == "HALF_OPEN" and p.consecutive_successes >= 2:
                p.state = "CLOSED"
                p.failure_count = 0
                p.last_error = ""

    def record_failure(self, provider_name: str, status_code: int = 500, error_message: str = "") -> None:
        with self._lock:
            p = self._providers.get(provider_name)
            if not p:
                p = ProviderState(provider_name)
                self._providers[provider_name] = p

            p.failure_count += 1
            p.last_failure_time = time.time()
            p.last_error = f"HTTP {status_code}: {error_message}"
            p.consecutive_successes = 0

            # Trip circuit on 429 (rate limit) immediately, or if threshold reached on 5xx
            if status_code == 429 or p.failure_count >= self.failure_threshold:
                p.state = "OPEN"

    def get_route(self, preferred_provider: str) -> Tuple[str, bool, str]:
        """Returns (effective_provider, is_fallback, reason)."""
        with self._lock:
            p = self._providers.get(preferred_provider)
            if not p:
                return preferred_provider, False, "Provider not tracked"

            now = time.time()
            if p.state == "OPEN":
                # Check if cooldown elapsed to try HALF_OPEN probe
                if now - p.last_failure_time > self.cooldown_seconds:
                    p.state = "HALF_OPEN"
                    p.consecutive_successes = 0
                    return p.name, False, "Attempting half-open probe after cooldown"

                # Otherwise reroute to fallback if available
                if p.fallback and p.fallback in self._providers:
                    fallback_p = self._providers[p.fallback]
                    if fallback_p.state != "OPEN":
                        return (
                            p.fallback,
                            True,
                            f"Rerouted from {preferred_provider} ({p.last_error}) to {p.fallback}",
                        )

            return p.name, False, "Provider healthy"

    def get_status_overview(self) -> List[Dict[str, Any]]:
        with self._lock:
            res = []
            now = time.time()
            for name, p in self._providers.items():
                res.append({
                    "provider": name,
                    "state": p.state,
                    "failure_count": p.failure_count,
                    "last_error": p.last_error,
                    "seconds_since_failure": (now - p.last_failure_time) if p.last_failure_time > 0 else None,
                    "fallback": p.fallback,
                })
            return res


# Global singleton
circuit_breaker = CircuitBreaker()
