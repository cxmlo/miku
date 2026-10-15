# Web y Multimedia 🌍🎵

Herramientas para interactuar con internet, navegadores web y sistemas de música.

## `tools_web.py` y `web_browser.py`
Manejo de internet. Miku puede navegar sin necesidad de que el usuario vea un navegador usando `HeadlessBrowser`.
- `buscar_en_internet(query)`: Utiliza APIs como DuckDuckGo/Tavily para encontrar información rápida.
- `leer_pagina_web(url)`: Descarga el texto crudo de una URL.
- `navegar_web_autonomo(tarea)` / `navegar_y_extraer()`: Inicia un navegador controlado por Playwright/Selenium para buscar y extraer información de forma autónoma.

## `tools_spotify.py` y `music_controller.py`
Interacción con el reproductor de música.
- `buscar_y_reproducir_spotify(query)`: Se conecta a la API de Spotify o simula clics para buscar y reproducir un artista/canción.
- `music_controller.py`: Modulo asíncrono avanzado (`_media_loop`, `_do_toggle`, `_do_next`, `_do_prev`) que se integra con las APIs de Windows Media (SMTC) para capturar la canción actual (metadatos) y controlar pausar/reproducir de manera nativa sin importar qué app está sonando.
- `tools_media.py`: 
  - `reproducir_en_youtube(query)`: Abre el navegador en un enlace de Youtube.
  - `controlar_multimedia(accion)`: Delega a `music_controller.py`.

## Enlaces Relacionados
- 👉 Volver a [[Tools_Overview]]
