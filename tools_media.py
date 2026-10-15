import webbrowser
import urllib.parse
import time
import pyautogui

def reproducir_en_spotify(busqueda: str) -> str:
    """Abre Spotify y busca la canción/artista."""
    try:
        query_encoded = urllib.parse.quote(busqueda)
        webbrowser.open(f'spotify:search:{query_encoded}')
        time.sleep(2) 
        return f"Spotify abierto con la búsqueda '{busqueda}'. [INSTRUCCIÓN OBLIGATORIA]: No escribas texto de respuesta todavía. Llama AHORA MISMO a la herramienta 'hacer_clic_visual' con intencion: 'reproducir la primera canción de los resultados de búsqueda'. Haz la llamada a la herramienta en este mismo instante."
    except Exception as e:
        return f"Error al abrir Spotify: {e}"

def reproducir_en_youtube(busqueda: str) -> str:
    """Abre YouTube en el navegador y busca el video."""
    try:
        query_encoded = urllib.parse.quote(busqueda)
        webbrowser.open(f'https://www.youtube.com/results?search_query={query_encoded}')
        time.sleep(2.5) 
        return f"YouTube abierto con la búsqueda '{busqueda}'. [INSTRUCCIÓN OBLIGATORIA]: No escribas texto de respuesta todavía. Llama AHORA MISMO a la herramienta 'hacer_clic_visual' con intencion: 'reproducir el primer video de los resultados de búsqueda'. Haz la llamada a la herramienta en este mismo instante."
    except Exception as e:
        return f"Error al abrir YouTube: {e}"

def controlar_multimedia(accion: str) -> str:
    """Controla la reproducción de medios en Windows (pausa, play, siguiente, anterior)."""
    accion = accion.lower()
    if accion in ['play', 'pausa', 'playpause']:
        pyautogui.press('playpause')
        return "Comando Play/Pausa enviado."
    elif accion in ['siguiente', 'next']:
        pyautogui.press('nexttrack')
        return "Comando Siguiente Canción enviado."
    elif accion in ['anterior', 'prev']:
        pyautogui.press('prevtrack')
        return "Comando Canción Anterior enviado."
    else:
        return "Acción multimedia no reconocida."
