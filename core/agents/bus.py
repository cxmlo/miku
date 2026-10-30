"""Inter-agent delegation event bus for Miku Companion.
Thread-safe publisher/subscriber pattern for managing agent task delegation and status updates.
"""

from __future__ import annotations

import time
import uuid
import threading
from typing import Any, Callable, Dict, List, Optional


class DelegationEvent:
    def __init__(
        self,
        event_type: str,
        task_id: str,
        from_agent: str,
        to_agent: str,
        payload: Dict[str, Any],
        timestamp: Optional[float] = None,
    ):
        self.event_type = event_type
        self.task_id = task_id
        self.from_agent = from_agent
        self.to_agent = to_agent
        self.payload = payload
        self.timestamp = timestamp or time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "task_id": self.task_id,
            "from_agent": self.from_agent,
            "to_agent": self.to_agent,
            "payload": self.payload,
            "timestamp": self.timestamp,
        }


class AgentBus:
    """Central event bus for coordinating multi-agent actions and status reporting."""

    def __init__(self):
        self._listeners: Dict[str, List[Callable[[DelegationEvent], None]]] = {}
        self._history: List[DelegationEvent] = []
        self._active_tasks: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def subscribe(self, event_type: str, callback: Callable[[DelegationEvent], None]) -> None:
        with self._lock:
            if event_type not in self._listeners:
                self._listeners[event_type] = []
            self._listeners[event_type].append(callback)

    def unsubscribe(self, event_type: str, callback: Callable[[DelegationEvent], None]) -> None:
        with self._lock:
            if event_type in self._listeners:
                self._listeners[event_type] = [cb for cb in self._listeners[event_type] if cb != callback]

    def publish(self, event: DelegationEvent) -> None:
        with self._lock:
            self._history.append(event)
            # Limit history buffer to last 500 events
            if len(self._history) > 500:
                self._history = self._history[-500:]

            # Track task lifecycle
            if event.event_type == "TASK_DELEGATED":
                self._active_tasks[event.task_id] = {
                    "task_id": event.task_id,
                    "from_agent": event.from_agent,
                    "to_agent": event.to_agent,
                    "task": event.payload.get("task", ""),
                    "status": "pending",
                    "phase": event.payload.get("phase", "init"),
                    "start_time": event.timestamp,
                    "progress": 0,
                    "diff": None,
                }
            elif event.event_type == "TASK_PROGRESS" and event.task_id in self._active_tasks:
                task = self._active_tasks[event.task_id]
                task["status"] = "running"
                task["phase"] = event.payload.get("phase", task["phase"])
                task["progress"] = event.payload.get("progress", task["progress"])
                if "diff" in event.payload:
                    task["diff"] = event.payload["diff"]
            elif event.event_type in ("TASK_COMPLETED", "TASK_FAILED") and event.task_id in self._active_tasks:
                task = self._active_tasks[event.task_id]
                task["status"] = "completed" if event.event_type == "TASK_COMPLETED" else "failed"
                task["end_time"] = event.timestamp
                task["result"] = event.payload.get("result", "")

            callbacks = list(self._listeners.get(event.event_type, [])) + list(self._listeners.get("*", []))

        # Notify without holding lock to avoid deadlock
        for cb in callbacks:
            try:
                cb(event)
            except Exception:
                pass

    def delegate(
        self,
        from_agent: str,
        to_agent: str,
        task: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Create and publish a task delegation."""
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        payload = {
            "task": task,
            "context": context or {},
            "phase": "init",
        }
        event = DelegationEvent(
            event_type="TASK_DELEGATED",
            task_id=task_id,
            from_agent=from_agent,
            to_agent=to_agent,
            payload=payload,
        )
        self.publish(event)
        return task_id

    def update_progress(
        self,
        task_id: str,
        agent: str,
        phase: str,
        progress: int,
        diff: Optional[Dict[str, Any]] = None,
        message: str = "",
    ) -> None:
        """Publish a progress update with phase, progress percentage, and optional diff."""
        payload = {
            "phase": phase,
            "progress": progress,
            "message": message,
        }
        if diff:
            payload["diff"] = diff

        event = DelegationEvent(
            event_type="TASK_PROGRESS",
            task_id=task_id,
            from_agent=agent,
            to_agent=agent,
            payload=payload,
        )
        self.publish(event)

    def complete_task(self, task_id: str, agent: str, result: str) -> None:
        event = DelegationEvent(
            event_type="TASK_COMPLETED",
            task_id=task_id,
            from_agent=agent,
            to_agent="miku",
            payload={"result": result},
        )
        self.publish(event)

    def fail_task(self, task_id: str, agent: str, error: str) -> None:
        event = DelegationEvent(
            event_type="TASK_FAILED",
            task_id=task_id,
            from_agent=agent,
            to_agent="miku",
            payload={"error": error},
        )
        self.publish(event)

    def get_active_tasks(self) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self._active_tasks.values())

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self._active_tasks.get(task_id)


# Global singleton instance
agent_bus = AgentBus()
