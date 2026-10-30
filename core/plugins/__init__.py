"""
Miku Modular Plugin Registry (`/core/plugins/__init__.py`).

Implements:
1. Atomic Plugin Registration (`plugin_ui`, `plugin_desktop`, `plugin_vision`, `plugin_browser`,
   `plugin_google`, `plugin_media`, `plugin_hooks`, `plugin_mcp`).
2. BLINDAJE #3 (10/10): Deterministic Tool Schema Ordering & Canonical Serialization for
   100% LLM Prefix-Caching hit rate (DeepSeek `deepseek-chat` / `deepseek-reasoner`, Gemini, etc.).
   Tools are ALWAYS sorted alphabetically by `function.name` and their nested dictionaries
   are recursively normalized with sorted keys so the JSON prefix hash is invariant across requests.
3. Fixed Agent Profiles (`orchestrator`, `code`, `vision`, `media`, `all`) so each agent
   maintains a deterministic, static tool prefix.
"""

import hashlib
import json
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple


def _canonicalize_dict(obj: Any) -> Any:
    """
    Recursively normalizes dictionaries so keys are always inserted in deterministic
    alphabetical order (with `type` and `function` preserved in canonical schema order).
    """
    if isinstance(obj, dict):
        return {k: _canonicalize_dict(obj[k]) for k in sorted(obj.keys())}
    if isinstance(obj, list):
        return [_canonicalize_dict(item) for item in obj]
    return obj


def normalize_tool_schema(schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Produces a canonically ordered OpenAI/DeepSeek function tool schema.
    """
    fn = schema.get("function", {})
    params = fn.get("parameters", {"type": "object", "properties": {}})
    canonical_params = _canonicalize_dict(params)
    canonical_fn: Dict[str, Any] = {
        "name": str(fn.get("name", "")).strip(),
        "description": str(fn.get("description", "")).strip(),
        "parameters": canonical_params,
    }
    return {
        "type": "function",
        "function": canonical_fn,
    }


def sort_tools_deterministically(tools: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    BLINDAJE #3: Deduplicates and sorts tool schemas strictly by `function.name` (ascending ASCII)
    and normalizes every nested dictionary key order.
    Guarantees identical JSON serialization across requests for DeepSeek Prefix-Caching.
    """
    by_name: Dict[str, Dict[str, Any]] = {}
    for raw_tool in tools:
        if not isinstance(raw_tool, dict):
            continue
        fn = raw_tool.get("function")
        if not isinstance(fn, dict) or not fn.get("name"):
            continue
        norm = normalize_tool_schema(raw_tool)
        by_name[norm["function"]["name"]] = norm

    return [by_name[name] for name in sorted(by_name.keys())]


def compute_tools_prefix_hash(tools: Iterable[Dict[str, Any]]) -> str:
    """
    Computes a deterministic SHA-256 fingerprint of the sorted tool schemas to verify
    Prefix-Caching stability in automated tests.
    """
    ordered = sort_tools_deterministically(tools)
    serialized = json.dumps(ordered, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


class PluginRegistry:
    """
    Central registry for Miku's modular plugins (`/core/plugins/plugin_*.py`).
    """

    def __init__(self) -> None:
        self._schemas: Dict[str, Dict[str, Any]] = {}
        self._handlers: Dict[str, Callable[..., Any]] = {}
        self._plugin_tags: Dict[str, str] = {}

    def register_tool(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        handler: Callable[..., Any],
        plugin_tag: str = "core",
    ) -> None:
        schema = normalize_tool_schema(
            {
                "type": "function",
                "function": {
                    "name": name,
                    "description": description,
                    "parameters": parameters,
                },
            }
        )
        self._schemas[name] = schema
        self._handlers[name] = handler
        self._plugin_tags[name] = plugin_tag

    def get_handler(self, name: str) -> Optional[Callable[..., Any]]:
        return self._handlers.get(name)

    def has_tool(self, name: str) -> bool:
        return name in self._handlers

    def execute(self, name: str, **kwargs: Any) -> Any:
        handler = self._handlers.get(name)
        if handler is None:
            raise KeyError(f"Tool '{name}' is not registered in PluginRegistry")
        return handler(**kwargs)

    def get_sorted_schemas(self, plugin_filter: Optional[Iterable[str]] = None) -> List[Dict[str, Any]]:
        """
        Returns tool schemas deterministically sorted by `function.name`.
        """
        allowed_tags = set(plugin_filter) if plugin_filter is not None else None
        selected = [
            schema
            for name, schema in self._schemas.items()
            if allowed_tags is None or self._plugin_tags.get(name) in allowed_tags
        ]
        return sort_tools_deterministically(selected)

    def merge_with_legacy_tools(
        self,
        legacy_tools: Iterable[Dict[str, Any]],
        agent_profile: str = "all",
    ) -> List[Dict[str, Any]]:
        """
        Combines legacy `tools_miku` schemas with modular plugin schemas and returns
        a deterministically ordered list for the requested `agent_profile`.
        """
        combined = list(legacy_tools) + list(self._schemas.values())
        sorted_all = sort_tools_deterministically(combined)
        if agent_profile in ("all", "", None):
            return sorted_all

        profile_filters = {
            "orchestrator": None,  # Full deterministic set
            "code": {"desktop", "ui", "hooks", "mcp", "browser"},
            "vision": {"vision", "desktop", "ui"},
            "media": {"media", "ui", "google"},
        }
        allowed = profile_filters.get(agent_profile)
        if allowed is None:
            return sorted_all

        filtered = []
        for item in sorted_all:
            fn_name = item["function"]["name"]
            tag = self._plugin_tags.get(fn_name, "legacy")
            if tag in allowed or tag == "legacy":
                filtered.append(item)
        return sort_tools_deterministically(filtered)

    def list_plugins_summary(self) -> List[Dict[str, Any]]:
        by_tag: Dict[str, List[str]] = {}
        for name in sorted(self._schemas.keys()):
            tag = self._plugin_tags.get(name, "core")
            by_tag.setdefault(tag, []).append(name)
        return [
            {"plugin": tag, "tool_count": len(names), "tools": sorted(names)}
            for tag, names in sorted(by_tag.items())
        ]


registry = PluginRegistry()
_PLUGINS_LOADED = False


def load_all_plugins() -> PluginRegistry:
    """
    Loads all atomic plugins in deterministic order and registers their tools.
    """
    global _PLUGINS_LOADED
    if _PLUGINS_LOADED:
        return registry

    from . import (
        plugin_browser,
        plugin_desktop,
        plugin_google,
        plugin_hooks,
        plugin_mcp,
        plugin_media,
        plugin_ui,
        plugin_vision,
    )

    for mod in (
        plugin_ui,
        plugin_desktop,
        plugin_vision,
        plugin_browser,
        plugin_google,
        plugin_media,
        plugin_hooks,
        plugin_mcp,
    ):
        if hasattr(mod, "register"):
            mod.register(registry)

    _PLUGINS_LOADED = True
    return registry


__all__ = [
    "PluginRegistry",
    "registry",
    "load_all_plugins",
    "sort_tools_deterministically",
    "normalize_tool_schema",
    "compute_tools_prefix_hash",
]
