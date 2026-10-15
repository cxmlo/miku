import os
import time
import requests
import logging
from bs4 import BeautifulSoup
try:
    from duckduckgo_search import DDGS
except ImportError:
    try:
        from ddgs import DDGS
    except ImportError:
        DDGS = None
from web_browser import navegar_web

logger = logging.getLogger("ToolsWeb")

def buscar_en_internet(consulta: str, abrir_navegador: bool = False, timelimit: str = None) -> str:
    """Realiza una búsqueda web de forma silenciosa y devuelve títulos, URLs y resúmenes cortos."""
    try:
        import webbrowser
        if abrir_navegador:
            # Si se solicita abrir el navegador, abrimos una búsqueda real en la PC del usuario
            url = f"https://www.google.com/search?q={consulta.replace(' ', '+')}"
            webbrowser.open(url)
            return f"Búsqueda abierta exitosamente en el navegador web del usuario para: '{consulta}'."

        resultados = []
        with DDGS() as ddgs:
            results = list(ddgs.text(consulta, max_results=5, timelimit=timelimit))
            
        for idx, result in enumerate(results):
            resultados.append(f"{idx+1}. Título: {result.get('title', '')}\n   URL: {result.get('href', '')}\n   Resumen: {result.get('body', '')}\n")
            
        if not resultados:
            return f"No se encontraron resultados para '{consulta}'."
            
        texto_resultados = f"Resultados de búsqueda para '{consulta}':\n\n" + "\n".join(resultados)
        texto_resultados += "\n(INSTRUCCIÓN: Si necesitas leer el contenido completo de una de estas páginas para responder, usa 'leer_pagina_web' o 'navegar_web_autonomo' si la página requiere JavaScript)."
        
        return texto_resultados
    except Exception as e:
        logger.error(f"Error al buscar en internet: {e}")
        return f"Error al buscar en internet: {e}"

def leer_pagina_web(url: str) -> str:
    """
    Descarga y lee el texto principal de una página web en segundo plano.
    Si la página requiere JavaScript dinámico (React/Vue/SPAs) o devuelve bloqueo 403,
    usa automáticamente Playwright Headless como fallback transparente.
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=8)
        
        # Si devuelve error de autorización/Cloudflare/antibot, usar fallback Playwright
        if response.status_code in (403, 401, 503):
            logger.info(f"Petición HTTP dio {response.status_code}. Activando fallback con Playwright Headless...")
            return navegar_web(url)

        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for script in soup(["script", "style", "nav", "header", "footer", "aside", "noscript", "iframe"]):
            script.extract()
            
        texto = soup.get_text(separator=' ')
        lineas = (line.strip() for line in texto.splitlines())
        chunks = (phrase.strip() for line in lineas for phrase in line.split("  "))
        texto_limpio = '\n'.join(chunk for chunk in chunks if chunk)
        
        # Si el texto es sospechosamente corto (< 150 caracteres), probablemente es una SPA que requiere JS
        if len(texto_limpio) < 150:
            logger.info("El texto extraído por HTTP es muy corto (posible SPA de JS). Activando fallback Playwright...")
            return navegar_web(url)
            
        if len(texto_limpio) > 8000:
            texto_limpio = texto_limpio[:8000] + "\n... (texto truncado por longitud)"
            
        return f"Contenido extraído de {url}:\n\n{texto_limpio}"
    except Exception as e:
        logger.warning(f"Error con requests en {url} ({e}). Intentando con Playwright Headless...")
        try:
            return navegar_web(url)
        except Exception as err_pw:
            return f"Error al intentar leer la página web {url}: {err_pw}"

def navegar_web_autonomo(url: str, acciones_json: str = None, esperar_selector: str = None, capturar_pantalla: bool = False) -> str:
    """
    Navega de forma autónoma e invisible a una página web usando el motor de Playwright Chromium.
    Permite interactuar con páginas dinámicas, hacer scroll, hacer clic en botones, rellenar formularios
    y esperar elementos antes de extraer el contenido estructurado.
    
    Parámetros:
      url: La URL a visitar (ej: 'https://es.wikipedia.org' o 'https://github.com').
      acciones_json: Lista opcional en formato JSON de acciones a ejecutar en orden.
        Ejemplo: '[{"tipo": "escribir", "selector": "input[name=q]", "texto": "Python"}, {"tipo": "tecla", "tecla": "Enter"}, {"tipo": "esperar", "segundos": 2}]'
        Tipos soportados: 'click' (selector), 'escribir' (selector, texto), 'tecla' (tecla), 'scroll' (pixeles), 'esperar' (segundos).
      esperar_selector: Selector CSS opcional a esperar antes de extraer el contenido.
      capturar_pantalla: Booleano. Si es True, guarda una captura de la página en el escritorio.
    """
    return navegar_web(
        url=url,
        acciones=acciones_json,
        esperar_selector=esperar_selector,
        capturar_pantalla=capturar_pantalla
    )
