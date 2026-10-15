# Interacción OS y Computadora (OS & Computer Tools) 💻

Estos archivos agrupan las habilidades de Miku para controlar y observar físicamente la computadora.

## `tools_os.py`
Provee comandos de sistema a bajo nivel:
- `gestionar_ventana(titulo, accion)`: Minimiza, maximiza o cierra ventanas.
- `abrir_aplicacion(nombre)`: Ejecuta programas.
- `escribir_texto(texto)` y `atajo_teclado(teclas)`: Simula pulsaciones físicas de teclado mediante librerías como `pyautogui`.
- `ejecutar_comando_sistema(comando)`: Acceso al CMD/PowerShell.
- `guardar_captura_en_escritorio()`: Toma un pantallazo y lo guarda localmente.

## `computer_use.py`
El módulo de interacción "Visual". Permite a Miku actuar sobre coordenadas exactas de la pantalla, ideal para cuando no existen atajos de teclado.
- `escanear_ventana_activa()`: Obtiene un screenshot y contexto de lo que el usuario está viendo ahora mismo.
- `_capturar_pantalla_base64()`: Para enviar imágenes al LLM de visión.
- `hacer_clic_visual()` / `hacer_clic_elemento()`: Encuentra elementos en la pantalla mediante IA o coordenadas espaciales y mueve el ratón físicamente a hacer clic.
- `hacer_scroll()`: Control de scroll.

## Enlaces Relacionados
- 👉 Volver a [[Tools_Overview]]
