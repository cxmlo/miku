"""
Lazy Module Loader & Startup Profiler for Miku Companion Runtime.
Ensures core startup completes in <1.5s by deferring heavy imports
(torch, whisper, playwright, pyautogui, chromadb, cv2, etc.) until first attribute access.
"""

import importlib
import sys
import threading
import time
from types import ModuleType
from typing import Any, Callable, Dict, Iterable, Optional

_BOOT_START_MONOTONIC = time.perf_counter()
_BOOT_COMPLETE_MONOTONIC: Optional[float] = None
_LAZY_REGISTRY: Dict[str, "LazyModuleProxy"] = {}
_LOAD_TIMES_MS: Dict[str, float] = {}
_LOCK = threading.RLock()

HEAVY_MODULES_DEFERRED_BY_DEFAULT = (
    "torch",
    "whisper",
    "faster_whisper",
    "playwright",
    "pyautogui",
    "chromadb",
    "cv2",
    "onnxruntime",
    "scipy",
    "matplotlib",
)


class LazyModuleProxy(ModuleType):
    """
    Transparent module proxy that imports the underlying module only when an attribute
    is accessed for the first time. Thread-safe and compatible with isinstance(x, ModuleType).
    """

    def __init__(self, module_name: str, fallback_factory: Optional[Callable[[], Any]] = None):
        super().__init__(module_name)
        object.__setattr__(self, "_lazy_module_name", module_name)
        object.__setattr__(self, "_lazy_target", None)
        object.__setattr__(self, "_lazy_loaded", False)
        object.__setattr__(self, "_lazy_error", None)
        object.__setattr__(self, "_lazy_fallback_factory", fallback_factory)

    def _resolve(self) -> Any:
        loaded = object.__getattribute__(self, "_lazy_loaded")
        target = object.__getattribute__(self, "_lazy_target")
        if loaded and target is not None:
            return target

        with _LOCK:
            loaded = object.__getattribute__(self, "_lazy_loaded")
            target = object.__getattribute__(self, "_lazy_target")
            if loaded and target is not None:
                return target

            mod_name = object.__getattribute__(self, "_lazy_module_name")
            t0 = time.perf_counter()
            try:
                mod = importlib.import_module(mod_name)
                elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)
                _LOAD_TIMES_MS[mod_name] = elapsed_ms
                object.__setattr__(self, "_lazy_target", mod)
                object.__setattr__(self, "_lazy_loaded", True)
                return mod
            except Exception as exc:
                object.__setattr__(self, "_lazy_error", exc)
                fallback_factory = object.__getattribute__(self, "_lazy_fallback_factory")
                if fallback_factory is not None:
                    mod = fallback_factory()
                    object.__setattr__(self, "_lazy_target", mod)
                    object.__setattr__(self, "_lazy_loaded", True)
                    return mod
                raise

    def is_loaded(self) -> bool:
        return bool(object.__getattribute__(self, "_lazy_loaded"))

    def __getattr__(self, item: str) -> Any:
        if item in ("__path__", "__file__", "__spec__", "__loader__", "__package__"):
            if not self.is_loaded():
                return None
        target = self._resolve()
        return getattr(target, item)

    def __dir__(self):
        target = self._resolve()
        return dir(target)

    def __repr__(self) -> str:
        mod_name = object.__getattribute__(self, "_lazy_module_name")
        status = "loaded" if self.is_loaded() else "deferred"
        return f"<LazyModuleProxy '{mod_name}' ({status})>"


def lazy_import(module_name: str, fallback_factory: Optional[Callable[[], Any]] = None) -> LazyModuleProxy:
    """
    Return a cached LazyModuleProxy for `module_name` without importing the module at call time.
    """
    with _LOCK:
        if module_name in _LAZY_REGISTRY:
            return _LAZY_REGISTRY[module_name]
        proxy = LazyModuleProxy(module_name, fallback_factory=fallback_factory)
        _LAZY_REGISTRY[module_name] = proxy
        return proxy


def is_module_loaded(module_name: str) -> bool:
    """
    Returns True if `module_name` is already imported in `sys.modules` as a real module
    (or if its LazyModuleProxy has resolved).
    """
    proxy = _LAZY_REGISTRY.get(module_name)
    if proxy is not None:
        return proxy.is_loaded()
    mod = sys.modules.get(module_name)
    if mod is None:
        return False
    if isinstance(mod, LazyModuleProxy):
        return mod.is_loaded()
    return True


def mark_boot_complete() -> float:
    """
    Marks the end of core boot and returns total boot time in milliseconds.
    """
    global _BOOT_COMPLETE_MONOTONIC
    if _BOOT_COMPLETE_MONOTONIC is None:
        _BOOT_COMPLETE_MONOTONIC = time.perf_counter()
    return round((_BOOT_COMPLETE_MONOTONIC - _BOOT_START_MONOTONIC) * 1000.0, 2)


def get_startup_metrics() -> Dict[str, Any]:
    """
    Returns real startup telemetry including boot duration and deferred vs loaded heavy modules.
    """
    now = _BOOT_COMPLETE_MONOTONIC or time.perf_counter()
    boot_ms = round((now - _BOOT_START_MONOTONIC) * 1000.0, 2)
    deferred = []
    loaded = []
    for name in set(list(HEAVY_MODULES_DEFERRED_BY_DEFAULT) + list(_LAZY_REGISTRY.keys())):
        if is_module_loaded(name):
            loaded.append({"name": name, "load_ms": _LOAD_TIMES_MS.get(name, 0.0)})
        else:
            deferred.append(name)

    return {
        "boot_ms": boot_ms,
        "target_ms": 1500.0,
        "within_budget": boot_ms < 1500.0,
        "deferred_modules": sorted(deferred),
        "loaded_modules": sorted(loaded, key=lambda x: x["name"]),
    }


def preload_in_background(module_names: Iterable[str], delay_seconds: float = 2.5) -> threading.Thread:
    """
    Optionally warms up specified lazy modules on a low-priority daemon thread after UI is interactive.
    """
    def _worker():
        if delay_seconds > 0:
            time.sleep(delay_seconds)
        for name in module_names:
            try:
                proxy = lazy_import(name)
                proxy._resolve()
            except Exception:
                pass

    t = threading.Thread(target=_worker, name="MikuLazyPreloader", daemon=True)
    t.start()
    return t
