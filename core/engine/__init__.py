"""
Miku Engine Subsystem: Lazy Loader & Startup Telemetry (<1.5s target).
"""

from .lazy_loader import (
    LazyModuleProxy,
    get_startup_metrics,
    is_module_loaded,
    lazy_import,
    mark_boot_complete,
    preload_in_background,
)

__all__ = [
    "LazyModuleProxy",
    "lazy_import",
    "is_module_loaded",
    "get_startup_metrics",
    "mark_boot_complete",
    "preload_in_background",
]
