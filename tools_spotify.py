import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
from dotenv import load_dotenv

load_dotenv()

sp = None

def init_spotify():
    global sp
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI", "http://localhost:8080")
    
    if not client_id or not client_secret or client_id == "tu_client_id_aqui":
        return False
        
    scopes = "user-read-playback-state user-modify-playback-state playlist-read-private user-library-read"
    
    try:
        # Check if cache exists with old scopes, and optionally delete it, but spotipy usually handles it
        sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope=scopes
        ))
        return True
    except Exception as e:
        print(f"Error inicializando Spotify: {e}")
        return False

def _get_active_device():
    devices = sp.devices()
    if not devices or not devices.get('devices'):
        import subprocess
        import time
        try:
            if hasattr(os, "startfile"):
                os.startfile("spotify:")
            else:
                subprocess.Popen(["xdg-open", "spotify:"])
            time.sleep(4) # Esperar a que se abra en Windows
            devices = sp.devices()
        except:
            pass
            
    if not devices or not devices.get('devices'):
        return None
        
    device_id = None
    for d in devices['devices']:
        if d['is_active']:
            device_id = d['id']
            break
    if not device_id:
        device_id = devices['devices'][0]['id']
    return device_id

def buscar_y_reproducir_spotify(busqueda: str, tipo: str = "track") -> str:
    global sp
    if not sp:
        if not init_spotify():
            return "Error: Credenciales de Spotify no configuradas correctamente en el archivo .env."
            
    try:
        device_id = _get_active_device()
        if not device_id:
            return "Error: No se encontró ningún dispositivo de Spotify activo. Abre Spotify en tu PC y vuelve a intentarlo."

        if tipo == "playlist":
            # Buscar en las playlists del usuario actual primero
            playlists = sp.current_user_playlists(limit=50)
            for pl in playlists['items']:
                if busqueda.lower() in pl['name'].lower():
                    sp.start_playback(device_id=device_id, context_uri=pl['uri'])
                    return f"Reproduciendo tu playlist '{pl['name']}' en Spotify."
            
            # Si no la encuentra, buscar en playlists públicas
            results = sp.search(q=busqueda, limit=1, type='playlist')
            if results['playlists']['items']:
                pl_uri = results['playlists']['items'][0]['uri']
                pl_name = results['playlists']['items'][0]['name']
                sp.start_playback(device_id=device_id, context_uri=pl_uri)
                return f"Reproduciendo la playlist pública '{pl_name}' en Spotify."
            return f"No encontré ninguna playlist llamada '{busqueda}'."

        elif tipo == "artist":
            results = sp.search(q=busqueda, limit=1, type='artist')
            if results['artists']['items']:
                artist_uri = results['artists']['items'][0]['uri']
                artist_name = results['artists']['items'][0]['name']
                sp.start_playback(device_id=device_id, context_uri=artist_uri)
                return f"Reproduciendo música de {artist_name} en Spotify."
            return f"No encontré al artista '{busqueda}'."

        elif tipo == "album":
            results = sp.search(q=busqueda, limit=1, type='album')
            if results['albums']['items']:
                album_uri = results['albums']['items'][0]['uri']
                album_name = results['albums']['items'][0]['name']
                sp.start_playback(device_id=device_id, context_uri=album_uri)
                return f"Reproduciendo el álbum '{album_name}' en Spotify."
            return f"No encontré el álbum '{busqueda}'."

        else: # track (por defecto)
            results = sp.search(q=busqueda, limit=1, type='track')
            if results['tracks']['items']:
                track_uri = results['tracks']['items'][0]['uri']
                track_name = results['tracks']['items'][0]['name']
                artist_name = results['tracks']['items'][0]['artists'][0]['name']
                sp.start_playback(device_id=device_id, uris=[track_uri])
                return f"Reproduciendo la canción '{track_name}' de {artist_name} en Spotify."
            return f"No encontré la canción '{busqueda}'."
            
    except Exception as e:
        return f"Error al intentar reproducir en Spotify: {e}"

def controlar_spotify(accion: str) -> str:
    global sp
    if not sp:
        if not init_spotify():
            return "Error: Credenciales de Spotify no configuradas."
            
    try:
        device_id = _get_active_device()
        if not device_id:
            return "Error: No hay dispositivo activo."

        if accion == "pause":
            sp.pause_playback(device_id=device_id)
            return "Música pausada."
        elif accion == "play":
            sp.start_playback(device_id=device_id)
            return "Música reanudada."
        elif accion == "next":
            sp.next_track(device_id=device_id)
            return "Siguiente canción."
        elif accion == "previous":
            sp.previous_track(device_id=device_id)
            return "Canción anterior."
        elif accion == "shuffle_on":
            sp.shuffle(True, device_id=device_id)
            return "Modo aleatorio activado."
        elif accion == "shuffle_off":
            sp.shuffle(False, device_id=device_id)
            return "Modo aleatorio desactivado."
        elif accion == "repeat_track":
            sp.repeat('track', device_id=device_id)
            return "Repitiendo canción actual."
        elif accion in ["repeat_off"]:
            sp.repeat('off', device_id=device_id)
            return "Repetición desactivada."
        elif accion in ["vol", "volume"]:
            # Default action handled if needed
            return "Volumen controlado."
        else:
            return f"Acción '{accion}' no reconocida."
            
    except Exception as e:
        return f"Error controlando Spotify: {e}"

def cambiar_volumen_spotify(vol: int) -> str:
    """Ajusta el volumen de reproducción en Spotify (0 a 100)."""
    global sp
    if not sp and not init_spotify():
        return "Error: Credenciales de Spotify no configuradas."
    try:
        vol = max(0, min(100, int(vol)))
        device_id = _get_active_device()
        sp.volume(vol, device_id=device_id)
        return f"Volumen de Spotify establecido en {vol}%."
    except Exception as e:
        return f"Error ajustando volumen de Spotify: {e}"

def que_suena_en_spotify() -> str:
    global sp
    if not sp:
        if not init_spotify():
            return "Error: Credenciales de Spotify no configuradas."
            
    try:
        playback = sp.current_playback()
        if not playback or not playback.get('item'):
            return "No hay ninguna canción reproduciéndose actualmente en Spotify."
            
        is_playing = playback['is_playing']
        item = playback['item']
        track_name = item['name']
        artist_name = item['artists'][0]['name']
        
        estado = "sonando" if is_playing else "pausada"
        return f"Actualmente está {estado} la canción '{track_name}' de {artist_name}."
        
    except Exception as e:
        return f"Error consultando Spotify: {e}"
