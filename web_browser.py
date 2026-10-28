import os
import json
import logging
import logging
import time
import concurrent.futures
from typing import Optional, List, Dict, Union

logger = logging.getLogger("WebBrowser")

class HeadlessBrowser:
    def __init__(self):
        pass

    def navegar_y_extraer(
        self,
        url: str,
        acciones: Optional[Union[List[Dict], str]] = None,
        esperar_selector: Optional[str] = None,
        extraer_markdown: bool = True,
        capturar_pantalla: bool = False,
        ruta_captura: Optional[str] = None,
        timeout: int = 25000
    ) -> str:
        """
        Navega de forma autónoma a una URL usando Playwright Chromium headless.
        Ejecuta JavaScript, resuelve SPAs dinámicas, puede ejecutar secuencias de acciones interactivas
        (clic, escribir, scroll, esperar) y devuelve el texto limpio y estructurado de la página.
        """
        from playwright.sync_api import sync_playwright

        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url

        if isinstance(acciones, str):
            try:
                acciones = json.loads(acciones)
            except Exception:
                acciones = []

        resultado_acciones = []

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    args=[
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-blink-features=AutomationControlled"
                    ]
                )
                
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                    viewport={"width": 1280, "height": 800},
                    locale="es-ES"
                )
                
                page = context.new_page()
                
                logger.info(f"Navegando a {url} con Playwright Headless...")
                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=timeout)
                except Exception as e:
                    logger.warning(f"Timeout en domcontentloaded ({e}), intentando continuar...")

                # Dar un breve tiempo para que JavaScript termine de renderizar el DOM
                time.sleep(1.0)

                if esperar_selector:
                    try:
                        page.wait_for_selector(esperar_selector, timeout=6000)
                    except Exception as e:
                        logger.warning(f"No se encontró el selector '{esperar_selector}' a tiempo: {e}")

                # Ejecutar acciones interactivas si se especificaron
                if acciones and isinstance(acciones, list):
                    for idx, acc in enumerate(acciones):
                        tipo = acc.get("tipo", "").lower()
                        sel = acc.get("selector", "")
                        try:
                            if tipo in ("click", "clic"):
                                page.click(sel, timeout=5000)
                                resultado_acciones.append(f"Paso {idx+1}: Clic en '{sel}' exitoso.")
                                time.sleep(0.8)
                            elif tipo in ("escribir", "type", "fill"):
                                txt = acc.get("texto", "")
                                page.fill(sel, txt, timeout=5000)
                                resultado_acciones.append(f"Paso {idx+1}: Escribir '{txt}' en '{sel}' exitoso.")
                                time.sleep(0.4)
                            elif tipo in ("tecla", "press"):
                                key = acc.get("tecla", "Enter")
                                page.keyboard.press(key)
                                resultado_acciones.append(f"Paso {idx+1}: Tecla '{key}' presionada.")
                                time.sleep(1.0)
                            elif tipo == "scroll":
                                pixeles = acc.get("pixeles", 500)
                                page.evaluate(f"window.scrollBy(0, {pixeles});")
                                resultado_acciones.append(f"Paso {idx+1}: Scroll de {pixeles}px realizado.")
                                time.sleep(0.5)
                            elif tipo in ("esperar", "wait"):
                                segs = acc.get("segundos", 1)
                                time.sleep(segs)
                                resultado_acciones.append(f"Paso {idx+1}: Espera de {segs}s completada.")
                        except Exception as acc_err:
                            resultado_acciones.append(f"Paso {idx+1}: Fallo en acción '{tipo}' ({acc_err})")

                titulo = page.title()
                url_final = page.url

                # Captura de pantalla si fue solicitada
                captura_info = ""
                if capturar_pantalla:
                    if not ruta_captura:
                        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
                        ruta_captura = os.path.join(desktop, f"captura_web_{int(time.time())}.png")
                    page.screenshot(path=ruta_captura, full_page=False)
                    captura_info = f"\n[Captura guardada en: {ruta_captura}]"

                # Limpieza de elementos molestos antes de extraer texto
                try:
                    page.evaluate("""() => {
                        const selectors = ['script', 'style', 'noscript', 'iframe', 'svg', 'header', 'footer', 'nav', 'aside', '.cookie-banner', '#cookie-banner'];
                        selectors.forEach(sel => {
                            document.querySelectorAll(sel).forEach(el => el.remove());
                        });
                    }""")
                except Exception:
                    pass

                # Extraer texto limpio
                texto_crudo = page.evaluate("() => document.body ? document.body.innerText : ''")
                lineas = [l.strip() for l in texto_crudo.splitlines() if l.strip()]
                texto_limpio = "\n".join(lineas)

                if len(texto_limpio) > 9000:
                    texto_limpio = texto_limpio[:9000] + "\n\n... [Contenido truncado por longitud]"

                browser.close()

                salida = [f"=== NAVEGACIÓN WEB COMPLETADA ==="]
                salida.append(f"Título: {titulo}")
                salida.append(f"URL: {url_final}")
                if resultado_acciones:
                    salida.append(f"Acciones ejecutadas:\n" + "\n".join(f" - {r}" for r in resultado_acciones))
                if captura_info:
                    salida.append(captura_info)
                salida.append(f"\n--- CONTENIDO PRINCIPAL EXTRAÍDO ---\n{texto_limpio}")

                return "\n".join(salida)

        except Exception as e:
            logger.error(f"Error en navegar_y_extraer con Playwright: {e}")
            return f"Error al navegar con Playwright a {url}: {e}"

# Instancia global del navegador
browser_instance = HeadlessBrowser()

def navegar_web(url: str, acciones=None, esperar_selector=None, capturar_pantalla=False) -> str:
    """Función de nivel superior para navegación web autónoma con Playwright."""
    with concurrent.futures.ThreadPoolExecutor() as pool:
        future = pool.submit(
            browser_instance.navegar_y_extraer,
            url,
            acciones,
            esperar_selector,
            True,
            capturar_pantalla,
            None,
            25000
        )
        return future.result()
