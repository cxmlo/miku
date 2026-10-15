import asyncio
import threading
from winrt.windows.media.control import GlobalSystemMediaTransportControlsSessionManager, GlobalSystemMediaTransportControlsSessionPlaybackStatus
from winrt.windows.storage.streams import Buffer
import time

# Estado compartido en memoria
media_state = {
    "is_playing": False,
    "has_session": False,
    "title": "",
    "artist": "",
    "position_sec": 0,
    "end_time_sec": 0,
    "last_update_time": 0,
    "app_id": "",
    "thumbnail_bytes": None,
    "session_id": ""
}

manager = None
_loop = None

def _get_target_session(mgr):
    try:
        sessions = mgr.get_sessions()
        if not sessions:
            return None
        # Prioridad 1: Reproductores de música nativos (Spotify, iTunes, Windows Media)
        for s in sessions:
            if s and hasattr(s, 'source_app_user_model_id') and s.source_app_user_model_id:
                app_id = str(s.source_app_user_model_id).lower()
                if "spotify" in app_id or "music" in app_id or "itunes" in app_id or "aimp" in app_id:
                    return s
        # Prioridad 2: Si no hay música nativa, tomar el reproductor por defecto activo
        return mgr.get_current_session()
    except Exception:
        return mgr.get_current_session()

async def _media_loop():
    global manager
    try:
        manager = await GlobalSystemMediaTransportControlsSessionManager.request_async()
    except Exception as e:
        print("MUSIC ERROR: No se pudo obtener el SessionManager", e)
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
            
            is_playing = (playback.playback_status == GlobalSystemMediaTransportControlsSessionPlaybackStatus.PLAYING)
            
            # Detectar cambio a "Play" para reiniciar el timer
            if is_playing and not media_state["is_playing"]:
                media_state["last_update_time"] = time.time()
                
            media_state["is_playing"] = is_playing
            media_state["title"] = info.title if info.title else "Desconocido"
            media_state["artist"] = info.artist if info.artist else ""
            
            # Los tiempos en winrt vienen en ticks de 100 nanosegundos.
            # 1 segundo = 10,000,000 ticks.
            import datetime
            pos = timeline.position
            end = timeline.end_time
            
            if isinstance(pos, datetime.timedelta):
                new_pos_sec = pos.total_seconds()
            else:
                pos_val = pos.duration if hasattr(pos, 'duration') else pos
                new_pos_sec = pos_val / 10000000.0 if pos_val else 0
                
            if isinstance(end, datetime.timedelta):
                media_state["end_time_sec"] = end.total_seconds()
            else:
                end_val = end.duration if hasattr(end, 'duration') else end
                media_state["end_time_sec"] = end_val / 10000000.0 if end_val else 0
                
            # Solo actualizar timestamp si el OS realmente actualizó la posición (ej. cada 5 seg o al saltar)
            if abs(new_pos_sec - media_state["position_sec"]) > 0.5:
                media_state["position_sec"] = new_pos_sec
                media_state["last_update_time"] = time.time()
                
            media_state["app_id"] = session.source_app_user_model_id
            
            # Solo actualizar la carátula si cambió la canción para no saturar memoria
            session_id = f"{info.title}-{info.artist}"
            if session_id != media_state["session_id"]:
                media_state["session_id"] = session_id
                if info.thumbnail:
                    stream = await info.thumbnail.open_read_async()
                    buffer = Buffer(stream.size)
                    await stream.read_async(buffer, buffer.capacity, 0)
                    media_state["thumbnail_bytes"] = bytes(buffer)
                else:
                    media_state["thumbnail_bytes"] = None
                    
        except Exception as e:
            # Ignorar errores silenciosos que ocurren si el reproductor se cierra abruptamente
            pass
            
        await asyncio.sleep(0.5) # Consultar cada 500ms

def _run_loop():
    global _loop
    # Crear un nuevo event loop para este thread
    _loop = asyncio.new_event_loop()
    asyncio.set_event_loop(_loop)
    _loop.run_until_complete(_media_loop())

def start_media_listener():
    global _loop
    t = threading.Thread(target=_run_loop, daemon=True)
    t.start()

async def _do_toggle():
    session = _get_target_session(manager)
    if session: await session.try_toggle_play_pause_async()

async def _do_next():
    session = _get_target_session(manager)
    if session: await session.try_skip_next_async()

async def _do_prev():
    session = _get_target_session(manager)
    if session: await session.try_skip_previous_async()

def toggle_play_pause():
    if manager and _loop:
        asyncio.run_coroutine_threadsafe(_do_toggle(), _loop)

def next_track():
    if manager and _loop:
        asyncio.run_coroutine_threadsafe(_do_next(), _loop)

def prev_track():
    if manager and _loop:
        asyncio.run_coroutine_threadsafe(_do_prev(), _loop)
