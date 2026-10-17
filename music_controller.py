import asyncio
import threading
import time
import ctypes

WINRT_AVAILABLE = False
try:
    from winsdk.windows.media.control import GlobalSystemMediaTransportControlsSessionManager, GlobalSystemMediaTransportControlsSessionPlaybackStatus
    from winsdk.windows.storage.streams import Buffer, DataReader
    WINRT_AVAILABLE = True
except Exception:
    try:
        from winrt.windows.media.control import GlobalSystemMediaTransportControlsSessionManager, GlobalSystemMediaTransportControlsSessionPlaybackStatus
        from winrt.windows.storage.streams import Buffer, DataReader
        WINRT_AVAILABLE = True
    except Exception:
        WINRT_AVAILABLE = False

# Estado compartido en memoria
media_state = {
    "is_playing": False,
    "has_session": False,
    "title": "Sin música",
    "artist": "",
    "position_sec": 0,
    "end_time_sec": 0,
    "last_update_time": 0,
    "app_id": "",
    "thumbnail_bytes": None,
    "session_id": "",
    "volume": 70
}

manager = None
_loop = None

# Windows Virtual Keys for media
VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_MEDIA_STOP = 0xB2
VK_MEDIA_PLAY_PAUSE = 0xB3
VK_VOLUME_MUTE = 0xAD
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_UP = 0xAF

def _send_vk(code):
    try:
        user32 = ctypes.windll.user32
        user32.keybd_event(code, 0, 0, 0)
        time.sleep(0.05)
        user32.keybd_event(code, 0, 2, 0) # KEYEVENTF_KEYUP
    except Exception as e:
        print("[Music] Error sending key event:", e)

def _get_target_session(mgr):
    if not mgr:
        return None
    try:
        cur = mgr.get_current_session()
        if cur:
            try:
                playback = cur.get_playback_info()
                if playback and playback.playback_status == GlobalSystemMediaTransportControlsSessionPlaybackStatus.PLAYING:
                    return cur
            except Exception:
                pass

        sessions = mgr.get_sessions()
        if sessions:
            for s in sessions:
                if s:
                    try:
                        playback = s.get_playback_info()
                        if playback and playback.playback_status == GlobalSystemMediaTransportControlsSessionPlaybackStatus.PLAYING:
                            return s
                    except Exception:
                        pass
            return cur or sessions[0]
        return cur
    except Exception:
        try:
            return mgr.get_current_session()
        except Exception:
            return None

async def _media_loop():
    global manager
    if not WINRT_AVAILABLE:
        # Fallback polling loop when winrt is not installed
        while True:
            try:
                # Check running processes with psutil for known media players
                import psutil
                running_players = []
                for p in psutil.process_iter(['name']):
                    pname = (p.info['name'] or '').lower()
                    if 'spotify' in pname:
                        running_players.append('Spotify')
                    elif 'itunes' in pname:
                        running_players.append('iTunes')
                if running_players:
                    media_state["has_session"] = True
                    if media_state["title"] == "Sin música":
                        media_state["title"] = f"{running_players[0]}"
                        media_state["artist"] = "Reproductor activo"
                else:
                    if not media_state.get("manual_play"):
                        media_state["has_session"] = False
            except Exception:
                pass
            await asyncio.sleep(2)
        return

    try:
        manager = await GlobalSystemMediaTransportControlsSessionManager.request_async()
    except Exception as e:
        print("[Music] No se pudo obtener SessionManager WinRT:", e)
        return

    while True:
        try:
            session = _get_target_session(manager)
            if not session:
                media_state["is_playing"] = False
                media_state["has_session"] = False
                await asyncio.sleep(1)
                continue
                
            media_state["has_session"] = True
            
            info = await session.try_get_media_properties_async()
            timeline = session.get_timeline_properties()
            playback = session.get_playback_info()
            
            is_playing = (playback.playback_status == GlobalSystemMediaTransportControlsSessionPlaybackStatus.PLAYING) if playback else False
            
            if is_playing and not media_state["is_playing"]:
                media_state["last_update_time"] = time.time()
                
            media_state["is_playing"] = is_playing
            media_state["title"] = (info.title if (info and info.title) else "Desconocido")
            media_state["artist"] = (info.artist if (info and info.artist) else "")
            
            if timeline:
                import datetime
                pos = timeline.position
                end = timeline.end_time
                if isinstance(pos, datetime.timedelta):
                    new_pos_sec = pos.total_seconds()
                else:
                    pos_val = getattr(pos, 'duration', pos)
                    new_pos_sec = pos_val / 10000000.0 if pos_val else 0
                    
                if isinstance(end, datetime.timedelta):
                    media_state["end_time_sec"] = end.total_seconds()
                else:
                    end_val = getattr(end, 'duration', end)
                    media_state["end_time_sec"] = end_val / 10000000.0 if end_val else 0
                    
                if abs(new_pos_sec - media_state["position_sec"]) > 0.5:
                    media_state["position_sec"] = new_pos_sec
                    media_state["last_update_time"] = time.time()
                    
            if session:
                media_state["app_id"] = getattr(session, 'source_app_user_model_id', '')
                
            if info:
                session_id = f"{info.title}-{info.artist}"
                if session_id != media_state["session_id"]:
                    media_state["session_id"] = session_id
                    if getattr(info, 'thumbnail', None):
                        try:
                            stream = await info.thumbnail.open_read_async()
                            size = stream.size
                            if size > 0:
                                buffer = Buffer(size)
                                await stream.read_async(buffer, buffer.capacity, 0)
                                try:
                                    reader = DataReader.from_buffer(buffer)
                                    out_b = bytearray(buffer.length)
                                    reader.read_bytes(out_b)
                                    media_state["thumbnail_bytes"] = bytes(out_b)
                                except Exception:
                                    media_state["thumbnail_bytes"] = bytes(buffer)
                            else:
                                media_state["thumbnail_bytes"] = None
                        except Exception:
                            media_state["thumbnail_bytes"] = None
                    else:
                        media_state["thumbnail_bytes"] = None
                        
        except Exception:
            pass
            
        await asyncio.sleep(0.5)

def _run_loop():
    global _loop
    _loop = asyncio.new_event_loop()
    asyncio.set_event_loop(_loop)
    _loop.run_until_complete(_media_loop())

def start_media_listener():
    global _loop
    t = threading.Thread(target=_run_loop, daemon=True)
    t.start()

async def _do_toggle():
    if WINRT_AVAILABLE and manager:
        session = _get_target_session(manager)
        if session:
            try:
                await session.try_toggle_play_pause_async()
                return
            except Exception:
                pass
    _send_vk(VK_MEDIA_PLAY_PAUSE)
    media_state["is_playing"] = not media_state["is_playing"]

async def _do_next():
    if WINRT_AVAILABLE and manager:
        session = _get_target_session(manager)
        if session:
            try:
                await session.try_skip_next_async()
                return
            except Exception:
                pass
    _send_vk(VK_MEDIA_NEXT_TRACK)

async def _do_prev():
    if WINRT_AVAILABLE and manager:
        session = _get_target_session(manager)
        if session:
            try:
                await session.try_skip_previous_async()
                return
            except Exception:
                pass
    _send_vk(VK_MEDIA_PREV_TRACK)

def toggle_play_pause():
    if _loop and _loop.is_running():
        asyncio.run_coroutine_threadsafe(_do_toggle(), _loop)
    else:
        _send_vk(VK_MEDIA_PLAY_PAUSE)
        media_state["is_playing"] = not media_state["is_playing"]

def next_track():
    if _loop and _loop.is_running():
        asyncio.run_coroutine_threadsafe(_do_next(), _loop)
    else:
        _send_vk(VK_MEDIA_NEXT_TRACK)

def prev_track():
    if _loop and _loop.is_running():
        asyncio.run_coroutine_threadsafe(_do_prev(), _loop)
    else:
        _send_vk(VK_MEDIA_PREV_TRACK)

def get_current_playback_info() -> dict:
    """Retorna el estado de reproducción normalizado para UI y pruebas"""
    return {
        "title": media_state.get("title", "Sin música"),
        "artist": media_state.get("artist", ""),
        "playing": bool(media_state.get("is_playing", False)),
        "position_sec": float(media_state.get("position_sec", 0)),
        "duration_sec": float(media_state.get("end_time_sec", 0)),
        "thumbnail_b64": media_state.get("thumbnail_bytes")
    }
