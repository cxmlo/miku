"""
Plugin Media (`core/plugins/plugin_media.py`):
Spotify Web API + Native Windows System Media Transport Controls (SMTC) Fallback.

Implements BLINDAJE #1 (10/10):
Windows Runtime (`winsdk` / `pywinrt`) media control APIs often freeze or fail to emit
track-change events if invoked directly from FastAPI's asyncio event loop because COM
requires a Single-Threaded Apartment (STA) thread with an active Win32 message pump.
This module isolates all Windows SMTC & native media operations inside a dedicated
`SMTCWorkerThread` initialized with `CoInitializeEx(None, COINIT_APARTMENTTHREADED=0x2)`
and communicates strictly via thread-safe `queue.Queue` request/response channels.
"""

import asyncio
import ctypes
import platform
import queue
import threading
import time
from typing import Any, Callable, Dict, Optional

from action_result import ActionResult, ActionStatus

COINIT_APARTMENTTHREADED = 0x2


class SMTCWorkerThread:
    """
    BLINDAJE #1: Dedicated Single-Threaded Apartment (STA) Worker Thread for Windows SMTC.
    Guarantees that `winsdk.windows.media.control` / Win32 media keys never touch or block
    FastAPI's main asyncio event loop.
    """

    def __init__(self) -> None:
        self._cmd_queue: "queue.Queue[Dict[str, Any]]" = queue.Queue()
        self._started = False
        self._lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None
        self._sta_initialized = False
        self._last_track_snapshot: Dict[str, Any] = {
            "playing": False,
            "title": "",
            "artist": "",
            "album": "",
            "source": "smtc_idle",
            "sta_thread": True,
            "thread_name": "",
        }
        self._track_listeners: list[Callable[[Dict[str, Any]], None]] = []

    def ensure_started(self) -> None:
        if self._started and self._thread and self._thread.is_alive():
            return
        with self._lock:
            if self._started and self._thread and self._thread.is_alive():
                return
            self._thread = threading.Thread(
                target=self._sta_loop,
                name="MikuSMTC_STA_Worker",
                daemon=True,
            )
            self._started = True
            self._thread.start()

    @property
    def is_alive(self) -> bool:
        return bool(self._thread and self._thread.is_alive())

    @property
    def thread_name(self) -> str:
        return self._thread.name if self._thread else ""

    def add_track_listener(self, cb: Callable[[Dict[str, Any]], None]) -> None:
        self._track_listeners.append(cb)

    def _init_com_sta(self) -> bool:
        """Initializes COM in Single-Threaded Apartment (STA) mode on Windows."""
        if platform.system().lower() != "windows":
            return True
        try:
            ole32 = ctypes.windll.ole32
            hr = ole32.CoInitializeEx(None, COINIT_APARTMENTTHREADED)
            # S_OK (0) or S_FALSE (1) both mean STA is active on this thread
            return hr in (0, 1)
        except Exception:
            return False

    def _uninit_com_sta(self) -> None:
        if platform.system().lower() != "windows":
            return
        try:
            ctypes.windll.ole32.CoUninitialize()
        except Exception:
            pass

    def _pump_win32_messages(self) -> None:
        """Non-blocking PeekMessageW pump so Windows COM STA callbacks are dispatched."""
        if platform.system().lower() != "windows":
            return
        try:
            user32 = ctypes.windll.user32

            class MSG(ctypes.Structure):
                _fields_ = [
                    ("hwnd", ctypes.c_void_p),
                    ("message", ctypes.c_uint),
                    ("wParam", ctypes.c_size_t),
                    ("lParam", ctypes.c_ssize_t),
                    ("time", ctypes.c_uint),
                    ("pt_x", ctypes.c_long),
                    ("pt_y", ctypes.c_long),
                ]

            msg = MSG()
            PM_REMOVE = 0x0001
            while user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, PM_REMOVE):
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
        except Exception:
            pass

    async def _query_winsdk_smtc_async(self, action: str) -> Dict[str, Any]:
        """Runs inside the STA thread's dedicated asyncio loop when `winsdk` is installed."""
        try:
            from winsdk.windows.media.control import (
                GlobalSystemMediaTransportControlsSessionManager as MediaManager,
                GlobalSystemMediaTransportControlsSessionPlaybackStatus as PlaybackStatus,
            )

            mgr = await MediaManager.request_async()
            session = mgr.get_current_session()
            if session is None:
                return {
                    "ok": False,
                    "playing": False,
                    "title": "Sin reproducción activa",
                    "artist": "Windows SMTC",
                    "source": "windows_smtc",
                    "sta_thread": True,
                    "thread_name": threading.current_thread().name,
                }

            if action == "play":
                await session.try_play_async()
            elif action in ("pause", "pausa"):
                await session.try_pause_async()
            elif action == "toggle":
                await session.try_toggle_play_pause_async()
            elif action in ("next", "siguiente"):
                await session.try_skip_next_async()
            elif action in ("prev", "previous", "anterior"):
                await session.try_skip_previous_async()

            props = await session.try_get_media_properties_async()
            playback_info = session.get_playback_info()
            is_playing = bool(
                playback_info and playback_info.playback_status == PlaybackStatus.PLAYING
            )
            title = getattr(props, "title", "") or "Pista del sistema"
            artist = getattr(props, "artist", "") or "Reproductor local"
            album = getattr(props, "album_title", "") or ""
            return {
                "ok": True,
                "playing": is_playing,
                "title": title,
                "artist": artist,
                "album": album,
                "source": "windows_smtc",
                "sta_thread": True,
                "thread_name": threading.current_thread().name,
            }
        except ImportError:
            return self._fallback_win32_media_key(action)
        except Exception as exc:
            fallback = self._fallback_win32_media_key(action)
            fallback["smtc_note"] = str(exc)
            return fallback

    def _fallback_win32_media_key(self, action: str) -> Dict[str, Any]:
        """Win32 Virtual-Key fallback executed on the STA worker thread."""
        VK_MEDIA_NEXT_TRACK = 0xB0
        VK_MEDIA_PREV_TRACK = 0xB1
        VK_MEDIA_STOP = 0xB2
        VK_MEDIA_PLAY_PAUSE = 0xB3

        vk_map = {
            "play": VK_MEDIA_PLAY_PAUSE,
            "pause": VK_MEDIA_PLAY_PAUSE,
            "pausa": VK_MEDIA_PLAY_PAUSE,
            "toggle": VK_MEDIA_PLAY_PAUSE,
            "next": VK_MEDIA_NEXT_TRACK,
            "siguiente": VK_MEDIA_NEXT_TRACK,
            "prev": VK_MEDIA_PREV_TRACK,
            "previous": VK_MEDIA_PREV_TRACK,
            "anterior": VK_MEDIA_PREV_TRACK,
            "stop": VK_MEDIA_STOP,
        }

        dispatched = False
        if action in vk_map and platform.system().lower() == "windows":
            try:
                vk = vk_map[action]
                KEYEVENTF_EXTENDEDKEY = 0x0001
                KEYEVENTF_KEYUP = 0x0002
                ctypes.windll.user32.keybd_event(vk, 0, KEYEVENTF_EXTENDEDKEY, 0)
                ctypes.windll.user32.keybd_event(vk, 0, KEYEVENTF_EXTENDEDKEY | KEYEVENTF_KEYUP, 0)
                dispatched = True
            except Exception:
                dispatched = False

        if action in ("play", "toggle"):
            self._last_track_snapshot["playing"] = True
        elif action in ("pause", "pausa", "stop"):
            self._last_track_snapshot["playing"] = False

        return {
            "ok": True,
            "dispatched_vk": dispatched,
            "action": action,
            "playing": self._last_track_snapshot.get("playing", False),
            "title": self._last_track_snapshot.get("title") or "Multimedia del Sistema",
            "artist": self._last_track_snapshot.get("artist") or "Control Nativo STA",
            "source": "sta_win32_smtc",
            "sta_thread": True,
            "thread_name": threading.current_thread().name,
        }

    def _sta_loop(self) -> None:
        self._sta_initialized = self._init_com_sta()
        sta_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(sta_loop)
        try:
            while True:
                self._pump_win32_messages()
                try:
                    item = self._cmd_queue.get(timeout=0.1)
                except queue.Empty:
                    continue

                if item.get("op") == "shutdown":
                    break

                action = item.get("action", "status")
                reply_q: Optional["queue.Queue[Dict[str, Any]]"] = item.get("reply_queue")
                try:
                    res = sta_loop.run_until_complete(self._query_winsdk_smtc_async(action))
                    self._last_track_snapshot.update(res)
                except Exception as exc:
                    res = {
                        "ok": False,
                        "error": str(exc),
                        "sta_thread": True,
                        "thread_name": threading.current_thread().name,
                    }

                if reply_q is not None:
                    reply_q.put(res)
        finally:
            try:
                sta_loop.close()
            except Exception:
                pass
            self._uninit_com_sta()

    def execute_on_sta(self, action: str = "status", timeout: float = 4.0) -> Dict[str, Any]:
        """
        Submits a media command or status query to the isolated STA worker thread
        and waits on a thread-safe queue without blocking COM on the caller's thread.
        """
        self.ensure_started()
        reply_q: "queue.Queue[Dict[str, Any]]" = queue.Queue(maxsize=1)
        self._cmd_queue.put({"op": "media", "action": action, "reply_queue": reply_q})
        try:
            return reply_q.get(timeout=timeout)
        except queue.Empty:
            return {
                "ok": False,
                "error": f"STA worker timeout ({timeout}s)",
                "sta_thread": True,
                "thread_name": self.thread_name,
            }


_SMTC_WORKER = SMTCWorkerThread()


def get_smtc_worker() -> SMTCWorkerThread:
    _SMTC_WORKER.ensure_started()
    return _SMTC_WORKER


def obtener_estado_multimedia_unificado() -> Dict[str, Any]:
    """
    Queries Spotify Web API first (if configured) and seamlessly falls back to the
    isolated STA Windows SMTC worker thread.
    """
    try:
        from spotify_client import spotify_manager

        if getattr(spotify_manager, "sp", None) is not None:
            current = spotify_manager.sp.current_playback()
            if current and current.get("item"):
                item = current["item"]
                artists = ", ".join(a["name"] for a in item.get("artists", []))
                album_images = item.get("album", {}).get("images", [])
                return {
                    "ok": True,
                    "playing": bool(current.get("is_playing")),
                    "title": item.get("name", "Spotify"),
                    "artist": artists or "Spotify",
                    "album": item.get("album", {}).get("name", ""),
                    "cover": album_images[0]["url"] if album_images else "",
                    "progress_ms": current.get("progress_ms", 0),
                    "duration_ms": item.get("duration_ms", 0),
                    "source": "spotify_api",
                    "sta_thread": False,
                }
    except Exception:
        pass

    return get_smtc_worker().execute_on_sta("status")


def controlar_multimedia_nativo_sta(accion: str = "status") -> str:
    """
    Tool handler for native media controls routed through the isolated STA worker thread.
    """
    clean_action = (accion or "status").strip().lower()
    res = get_smtc_worker().execute_on_sta(clean_action)
    if res.get("ok"):
        return ActionResult(
            status=ActionStatus.CONFIRMED,
            action="controlar_multimedia_nativo_sta",
            message=(
                f"Acción multimedia '{clean_action}' ejecutada en hilo STA aislado "
                f"(`{res.get('thread_name')}`). Pista: {res.get('title')} — {res.get('artist')}"
            ),
            evidence=f"thread={res.get('thread_name')} source={res.get('source')}",
            data=res,
        ).to_tool_response()

    return ActionResult(
        status=ActionStatus.FAILED,
        action="controlar_multimedia_nativo_sta",
        message=f"No se pudo completar la acción multimedia '{clean_action}'.",
        error=res.get("error", "Error desconocido en SMTC STA worker"),
        data=res,
    ).to_tool_response()


def register(reg: Any) -> None:
    reg.register_tool(
        name="controlar_multimedia_nativo_sta",
        description=(
            "Controla la reproducción multimedia de Windows (SMTC / Spotify / navegador) desde un hilo "
            "STA (Single-Threaded Apartment) aislado que nunca congela el bucle de eventos. "
            "Acciones: 'status', 'play', 'pause', 'toggle', 'next', 'previous'."
        ),
        parameters={
            "type": "object",
            "properties": {
                "accion": {
                    "type": "string",
                    "enum": ["status", "play", "pause", "toggle", "next", "previous"],
                    "description": "Acción multimedia a ejecutar en el worker STA.",
                }
            },
            "required": ["accion"],
        },
        handler=controlar_multimedia_nativo_sta,
        plugin_tag="media",
    )
