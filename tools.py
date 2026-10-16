from tools_os import (
    gestionar_ventana, abrir_aplicacion, escribir_texto, atajo_teclado, ejecutar_macro_teclado,
    borrar_archivo, borrar_archivo_confirmado, tomar_captura_pantalla, ejecutar_comando_sistema, esperar_segundos
)
from tools_code import escribir_y_ejecutar_python
from tools_web import buscar_en_internet, leer_pagina_web, navegar_web_autonomo
from tools_media import reproducir_en_youtube, controlar_multimedia
from tools_spotify import buscar_y_reproducir_spotify as reproducir_en_spotify, controlar_spotify, que_suena_en_spotify
from tools_miku import (
    analizar_archivo_silencioso,
    ver_pantalla, delegar_tarea, delegar_a_agente, listar_agentes_disponibles,
    abrir_chat_con_agente, crear_o_actualizar_agente, guardar_ultimo_reporte_en_escritorio,
    aprender_sobre_usuario, guardar_enlace_memoria, buscar_en_memoria,
    hablar_al_usuario, enviar_mensaje_a_agente, mostrar_widget_info, mostrar_widget_clima, mostrar_widget_reloj,
    modificar_estado_widget, obtener_clima, enviar_archivo_a_celular, enviar_imagen_a_chat,
    instalar_skill_mcp, solicitar_permiso_instalacion_mcp, abrir_panel_secretos_en_app, ejecutar_intent_android,
    monitorear_actividad_pc, hacer_pregunta_opciones, preparar_correo
)

def _actualizar_estado_wrapper(tarea_actual=None, paso_actual=None, parametros_json=None):
    from memory_temporal import memoria_temporal_global
    import json
    params = {}
    if parametros_json:
        try:
            params = json.loads(parametros_json)
        except:
            pass
    memoria_temporal_global.actualizar_estado(tarea=tarea_actual, paso=paso_actual, parametros=params)
    return "Estado de tarea actualizado correctamente en la memoria temporal."

available_functions = {
    "actualizar_estado_tarea": _actualizar_estado_wrapper,
    "enviar_mensaje_a_agente": enviar_mensaje_a_agente,
    "gestionar_ventana": gestionar_ventana,
    "abrir_aplicacion": abrir_aplicacion,
    "buscar_en_internet": buscar_en_internet,
    "leer_pagina_web": leer_pagina_web,
    "navegar_web_autonomo": navegar_web_autonomo,
    "escribir_texto": escribir_texto,

    "borrar_archivo": borrar_archivo,
    "borrar_archivo_confirmado": borrar_archivo_confirmado,
    "ver_pantalla": ver_pantalla,
    "hacer_pregunta_opciones": hacer_pregunta_opciones,
    "preparar_correo": preparar_correo,
    "monitorear_actividad_pc": monitorear_actividad_pc,
    "tomar_captura_pantalla": tomar_captura_pantalla,
    "delegar_tarea": delegar_tarea,
    "delegar_a_agente": delegar_a_agente,
    "listar_agentes_disponibles": listar_agentes_disponibles,
    "abrir_chat_con_agente": abrir_chat_con_agente,
    "crear_o_actualizar_agente": crear_o_actualizar_agente,
    "enviar_archivo_a_celular": enviar_archivo_a_celular,
    "enviar_imagen_a_chat": enviar_imagen_a_chat,
    "ejecutar_intent_android": ejecutar_intent_android,
    "guardar_ultimo_reporte_en_escritorio": guardar_ultimo_reporte_en_escritorio,
    "ejecutar_comando_sistema": ejecutar_comando_sistema,
    "reproducir_en_spotify": reproducir_en_spotify,
    "controlar_spotify": controlar_spotify,
    "que_suena_en_spotify": que_suena_en_spotify,
    "reproducir_en_youtube": reproducir_en_youtube,
    "controlar_multimedia": controlar_multimedia,
    "aprender_sobre_usuario": aprender_sobre_usuario,
    "obtener_clima": obtener_clima,
    "guardar_enlace_memoria": guardar_enlace_memoria,
    "buscar_en_memoria": buscar_en_memoria,
    "escanear_ventana_activa": __import__('computer_use').escanear_ventana_activa,
    "hacer_clic_visual": __import__('computer_use').hacer_clic_visual,
    "escribir_en_elemento": __import__('computer_use').escribir_en_elemento,
    "mover_raton_visual": __import__('computer_use').mover_raton_visual,
    "instalar_skill_mcp": instalar_skill_mcp,
    "solicitar_permiso_instalacion_mcp": solicitar_permiso_instalacion_mcp,
    "hacer_scroll": __import__('computer_use').hacer_scroll,
    "atajo_teclado": atajo_teclado,
    "ejecutar_macro_teclado": ejecutar_macro_teclado,
    "esperar_segundos": esperar_segundos,
    "memorizar_leccion": __import__('prompt_manager').memorizar_leccion,
    "cambiar_personalidad": __import__('prompt_manager').cambiar_personalidad,
    "hablar_al_usuario": hablar_al_usuario,
    "analizar_archivo_silencioso": analizar_archivo_silencioso,
    "asociar_contacto_app": __import__('contacts_memory').asociar_contacto_app,
    "mostrar_widget_info": mostrar_widget_info,
    "mostrar_widget_clima": mostrar_widget_clima,
    "mostrar_widget_reloj": mostrar_widget_reloj,
    "mostrar_tarjeta_visual": __import__('tools_miku').mostrar_tarjeta_visual,
    "modificar_estado_widget": modificar_estado_widget,
    "escribir_y_ejecutar_python": escribir_y_ejecutar_python,
    "abrir_panel_secretos_en_app": abrir_panel_secretos_en_app
}

tools_schema = [
    {
        "type": "function",
        "function": {
            "name": "abrir_panel_secretos_en_app",
            "description": "Abre un panel seguro en la aplicaciÃ³n mÃ³vil del usuario para que pueda ingresar contraseÃ±as o API Keys privadas sin que pasen por el chat. DEBES USAR esta herramienta SIEMPRE que vayas a instalar un MCP Server (ej. Pinterest, Google Drive, Github) que requiera credenciales o tokens de acceso. Dile al usuario por quÃ© necesitas la clave y espera a que te diga que ya la introdujo antes de continuar con la instalaciÃ³n.",
            "parameters": {
                "type": "object",
                "properties": {
                    "servicio": {
                        "type": "string",
                        "description": "El nombre del servicio para el cual necesitas la clave (ej. 'Pinterest', 'Google Drive')."
                    },
                    "campos_requeridos": {
                        "type": "array",
                        "items": { "type": "string" },
                        "description": "Una lista de los nombres exactos de las variables o claves requeridas por el servicio. Miku lee esto de la documentaciÃ³n (ej. ['GOOGLE_CLIENT_ID', 'GOOGLE_CLIENT_SECRET'])."
                    }
                },
                "required": ["servicio", "campos_requeridos"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "ejecutar_intent_android",
            "description": "Lanza un Intent nativo en el dispositivo Android del usuario. Ãšsalo cuando el usuario pida controlar funciones de su celular, como configurar alarmas (android.intent.action.SET_ALARM), crear cronÃ³metros (android.intent.action.SET_TIMER) o abrir aplicaciones especÃ­ficas. Requiere que Miku estÃ© conectada desde el celular.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "El nombre del intent (ej. 'android.intent.action.SET_ALARM' o 'android.intent.action.SET_TIMER')."
                    },
                    "extras": {
                        "type": "object",
                        "description": "Diccionario clave-valor con los extras requeridos por el intent (ej. {'android.intent.extra.alarm.HOUR': 7, 'android.intent.extra.alarm.MINUTES': 30, 'android.intent.extra.alarm.MESSAGE': 'Despertar'})."
                    }
                },
                "required": ["action"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "instalar_skill_mcp",
            "description": "Instala un nuevo servidor MCP dinÃ¡micamente y lo enciende para que puedas usar sus herramientas al instante sin pedir ayuda. Si el usuario te pide instalar una skill (ej. Notion o Github) pero no te da el comando exacto, DEBES usar primero 'buscar_en_internet' para buscar '[nombre] mcp server npm o uvx', leer la documentaciÃ³n, averiguar el comando, y luego usar esta herramienta. Â¡ATENCIÃ“N! Si descubres que la skill requiere de una API KEY o Token de autenticaciÃ³n, ANTES de instalarla DEBES usar la herramienta 'abrir_panel_secretos_en_app' para pedirle al usuario que ingrese sus credenciales de forma segura.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre_servidor": {
                        "type": "string",
                        "description": "El nombre clave del servidor (ej. 'sqlite', 'github', 'postgres')."
                    },
                    "comando": {
                        "type": "string",
                        "description": "El comando principal para ejecutarlo (usualmente 'npx' o 'uvx')."
                    },
                    "argumentos": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "Lista de argumentos para el comando, por ejemplo ['-y', '@modelcontextprotocol/server-sqlite', '--db-path', 'miku.db']."
                    }
                },
                "required": [
                    "nombre_servidor",
                    "comando",
                    "argumentos"
                ]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "solicitar_permiso_instalacion_mcp",
            "description": "IMPORTANTE: Ãšsalo OBLIGATORIAMENTE cuando necesites descargar e instalar un nuevo servidor MCP o software de terceros desde internet. Esta funciÃ³n enviarÃ¡ una solicitud de autorizaciÃ³n al celular del usuario y pausarÃ¡ tu ejecuciÃ³n. DevolverÃ¡ la decisiÃ³n del usuario, la cual DEBES respetar. NUNCA instales software sin llamar a esta herramienta primero.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre": {
                        "type": "string",
                        "description": "Nombre de la herramienta o servidor MCP (ej. 'Notion MCP', 'GitHub integration')."
                    },
                    "proposito": {
                        "type": "string",
                        "description": "Para quÃ© sirve y por quÃ© lo necesitas."
                    },
                    "github_url": {
                        "type": "string",
                        "description": "URL del repositorio o paquete (ej. 'https://github.com/org/repo')."
                    },
                    "comandos_instalacion": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Los comandos exactos que planeas usar para instalar (ej. ['npx', '-y', 'paquete'])."
                    }
                },
                "required": [
                    "nombre",
                    "proposito",
                    "github_url",
                    "comandos_instalacion"
                ]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "mostrar_tarjeta_visual",
            "description": "Muestra una tarjeta visual flotante en la pantalla con una vista previa de archivos (como imÃ¡genes) o respuestas cortas. Ãšsalo SIEMPRE que encuentres archivos o quieras mostrar imÃ¡genes para no tener que leer la ruta absoluta en voz alta.",
            "parameters": {
                "type": "object",
                "properties": {
                    "archivos": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Lista de rutas absolutas de los archivos a mostrar en miniatura. DÃ©jalo vacÃ­o si solo quieres enviar un mensaje de texto."
                    },
                    "mensaje": {
                        "type": "string",
                        "description": "Un mensaje o descripciÃ³n MUY CORTO que acompaÃ±a la tarjeta visual."
                    }
                },
                "required": ["archivos", "mensaje"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "modificar_estado_widget",
            "description": "Modifica el estado de un widget en pantalla. Ãšsalo si el usuario te pide fijar, desfijar, maximizar, minimizar o cerrar un widget.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tipo_widget": {
                        "type": "string",
                        "enum": ["clima", "reloj", "musica", "info", "tarjeta"],
                        "description": "El tipo de widget que se desea modificar."
                    },
                    "accion": {
                        "type": "string",
                        "enum": ["fijar", "desfijar", "maximizar", "minimizar", "cerrar"],
                        "description": "La acciÃ³n a realizar sobre el widget."
                    }
                },
                "required": ["tipo_widget", "accion"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "mostrar_widget_reloj",
            "description": "Muestra un hermoso reloj analÃ³gico en tiempo real en la pantalla. Ãšsalo SIEMPRE que el usuario te pida la hora actual. No uses la tarjeta de informaciÃ³n genÃ©rica.",
            "parameters": {
                "type": "object",
                "properties": {
                    "titulo": {
                        "type": "string",
                        "description": "El tÃ­tulo de la tarjeta, por ejemplo 'Hora Actual' o 'La hora es:'."
                    },
                    "hora_digital": {
                        "type": "string",
                        "description": "La hora en formato digital AM/PM, por ejemplo '06:30 PM'."
                    }
                },
                "required": ["titulo", "hora_digital"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "escribir_y_ejecutar_python",
            "description": "Â¡TU HERRAMIENTA MÃS PODEROSA! Escribe y ejecuta cÃ³digo Python autÃ³nomo. Ãšsalo cuando no tengas una herramienta (ej. web scraping, anÃ¡lisis, automatizaciÃ³n). REGLAS: 1) Â¡NUNCA uses plt.show(), input() ni time.sleep()! Bloquean el sistema. 2) NUNCA guardes archivos .py en el disco ni en el Escritorio; el sistema ya ejecuta tu cÃ³digo en un entorno temporal automÃ¡tico. 3) Si generas un grÃ¡fico, guÃ¡rdalo como imagen (ej. plt.savefig('C:/Users/cxmluwu/Desktop/grafico.png')) y usa 'mostrar_tarjeta_visual'. Usa 'print()' para devolver texto.",
            "parameters": {
                "type": "object",
                "properties": {
                    "codigo": {
                        "type": "string",
                        "description": "El cÃ³digo Python completo a ejecutar. No necesitas escribirlo a un archivo, solo mÃ¡ndalo aquÃ­."
                    }
                },
                "required": ["codigo"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "enviar_mensaje_a_agente",
            "description": "EnvÃ­a una nueva instrucciÃ³n, correcciÃ³n o aclaraciÃ³n al agente autÃ³nomo que actualmente estÃ¡ trabajando en segundo plano. ÃšSALO INMEDIATAMENTE si el usuario te pide que el agente cambie su enfoque, aborte o modifique lo que estÃ¡ haciendo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "mensaje": {
                        "type": "string",
                        "description": "El mensaje o correcciÃ³n que quieres transmitirle al agente."
                    }
                },
                "required": ["mensaje"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "gestionar_ventana",
            "description": "Controla el estado de cualquier ventana abierta (ej. maximizar, minimizar, restaurar, cerrar). Ãšsalo cuando el usuario te pida explÃ­citamente realizar una de estas acciones sobre un programa.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre": {
                        "type": "string",
                        "description": "El nombre de la aplicaciÃ³n (ej. 'Spotify', 'Chrome', 'Discord')"
                    },
                    "accion": {
                        "type": "string",
                        "description": "La acciÃ³n a realizar. Valores permitidos: 'maximizar', 'minimizar', 'restaurar', 'cerrar'."
                    }
                },
                "required": ["nombre", "accion"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "abrir_aplicacion",
            "description": "Abre CUALQUIER aplicaciÃ³n instalada en el PC del usuario buscÃ¡ndola en el menÃº de inicio de Windows. Funciona con todo: Discord, Opera GX, Notepad, Chrome, Visual Studio, juegos, etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre": {
                        "type": "string",
                        "description": "El nombre de la aplicaciÃ³n tal como aparece en el menÃº de inicio (ej. 'Discord', 'Opera GX', 'Visual Studio Code', 'Steam')"
                    }
                },
                "required": ["nombre"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "buscar_en_internet",
            "description": "Busca en Google de forma invisible y devuelve una lista de resultados con URLs. Ãšsalo siempre para buscar informaciÃ³n. Si necesitas leer la pÃ¡gina completa de uno de los resultados, usa luego la herramienta 'leer_pagina_web' pasando la URL.",
            "parameters": {
                "type": "object",
                "properties": {
                    "consulta": {
                        "type": "string",
                        "description": "Lo que se va a buscar en Google (ej. 'clima en Madrid', 'noticias de hoy')"
                    },
                    "abrir_navegador": {
                        "type": "boolean",
                        "description": "True para forzar abrir Chrome/Edge con los resultados. Falso para modo silencioso. Opcional."
                    },
                    "timelimit": {
                        "type": "string",
                        "description": "Filtro de fecha opcional: 'd' (Ãºltimo dÃ­a), 'w' (Ãºltima semana), 'm' (Ãºltimo mes), 'y' (Ãºltimo aÃ±o). Ãšsalo SIEMPRE que el usuario pregunte por noticias de hoy o eventos recientes."
                    }
                },
                "required": ["consulta"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "leer_pagina_web",
            "description": "Descarga y extrae todo el texto de una pÃ¡gina web especÃ­fica de forma invisible. Ãšsalo DESPUÃ‰S de buscar en internet si el resumen no es suficiente y necesitas leer el artÃ­culo completo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "La URL completa de la pÃ¡gina a leer (obtenida de buscar_en_internet)"
                    }
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "navegar_web_autonomo",
            "description": "Navega de forma autÃ³noma e invisible usando un navegador Chromium headless completo (Playwright). Ejecuta JavaScript moderno, resuelve SPAs, puede rellenar formularios, hacer clic en botones, desplazarse y extraer contenido estructurado o capturas.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "La URL a visitar (ej. 'https://github.com/trending', 'https://es.wikipedia.org')"
                    },
                    "acciones_json": {
                        "type": "string",
                        "description": "Lista JSON opcional de acciones interactivas a ejecutar en orden. Ejemplo: '[{\"tipo\": \"escribir\", \"selector\": \"input#search\", \"texto\": \"AI\"}, {\"tipo\": \"tecla\", \"tecla\": \"Enter\"}, {\"tipo\": \"esperar\", \"segundos\": 2}]'. Tipos: 'click', 'escribir', 'tecla', 'scroll', 'esperar'."
                    },
                    "esperar_selector": {
                        "type": "string",
                        "description": "Selector CSS opcional que debe aparecer antes de extraer el contenido (ej. 'div.main-content', 'article')."
                    },
                    "capturar_pantalla": {
                        "type": "boolean",
                        "description": "Si es true, toma una captura de pantalla de la pÃ¡gina web renderizada y la guarda en el escritorio."
                    }
                },
                "required": ["url"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "escribir_texto",
            "description": "Escribe un texto en la computadora simulando pulsaciones de teclado, Ãºtil para escribir mensajes en chats, barras de bÃºsqueda, etc. AsegÃºrate de hacer clic primero en la caja de texto usando hacer_clic_visual si no estÃ¡ enfocada.",
            "parameters": {
                "type": "object",
                "properties": {
                    "texto": {
                        "type": "string",
                        "description": "El texto que se va a escribir"
                    },
                    "presionar_enter": {
                        "type": "boolean",
                        "description": "Si es true, presiona la tecla Enter justo despuÃ©s de escribir el texto (Ãºtil para enviar mensajes o buscar)."
                    },
                    "limpiar_antes": {
                        "type": "boolean",
                        "description": "Si es true, presiona Ctrl+A y Delete para borrar todo el texto existente antes de escribir. Ãšsalo SIEMPRE que vayas a escribir en una barra de bÃºsqueda (Spotify, Chrome, YouTube) para no mezclar palabras. DÃ©jalo en false si estÃ¡s continuando un texto (ej. en Word o bloc de notas)."
                    }
                },
                "required": ["texto"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "borrar_archivo",
            "description": "Inicia el proceso para borrar un archivo del ordenador. El asistente DEBE usar esta funciÃ³n si se le pide borrar algo, para solicitar confirmaciÃ³n.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ruta": {
                        "type": "string",
                        "description": "La ruta absoluta del archivo a borrar"
                    }
                },
                "required": ["ruta"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "borrar_archivo_confirmado",
            "description": "Borra un archivo SOLO SI el usuario ya confirmÃ³ expresamente la eliminaciÃ³n.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ruta": {
                        "type": "string",
                        "description": "La ruta absoluta del archivo a borrar"
                    }
                },
                "required": ["ruta"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "ver_pantalla",
            "description": "Toma una fotografÃ­a de la pantalla del ordenador en este momento exacto para que puedas verla. Ãšsalo de manera PROACTIVA antes de responder si el usuario utiliza palabras demostrativas ambiguas ('esto', 'aquÃ­', 'esta imagen', 'mi cÃ³digo') o si te pide ayuda con algo que estÃ¡ viendo. NUNCA respondas a ciegas si el usuario hace referencia a algo visual.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "monitorear_actividad_pc",
            "description": "Ãšsala EXCLUSIVAMENTE cuando el usuario te pregunte quÃ© estÃ¡ haciendo, quÃ© aplicaciones estÃ¡ usando, o si puedes monitorear su actividad. Reemplaza el uso de ver_pantalla para esta tarea especÃ­fica.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "tomar_captura_pantalla",
            "description": "Toma una captura de pantalla y la guarda como archivo de imagen (.png) en la carpeta compartida. Ãšsalo cuando el usuario pida explÃ­citamente guardar, sacar o tomar una captura de pantalla.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre_archivo": {
                        "type": "string",
                        "description": "Nombre opcional del archivo (ej. 'captura_juego', 'prueba1'). Si no se provee, se usarÃ¡ 'captura'."
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "enviar_archivo_a_celular",
            "description": "EnvÃ­a un archivo directamente al celular del usuario para que lo abra. NUNCA lo uses si el usuario estÃ¡ en la PC.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ruta": {
                        "type": "string",
                        "description": "Ruta absoluta del archivo a enviar."
                    }
                },
                "required": ["ruta"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "enviar_imagen_a_chat",
            "description": "EnvÃ­a una imagen local junto con un mensaje al chat (App MÃ³vil). NUNCA lo uses si el usuario estÃ¡ en la PC.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ruta_imagen": {
                        "type": "string",
                        "description": "Ruta absoluta de la imagen a enviar."
                    },
                    "mensaje": {
                        "type": "string",
                        "description": "Mensaje que acompaÃ±a la imagen."
                    }
                },
                "required": ["ruta_imagen", "mensaje"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "listar_agentes_disponibles",
            "description": "Lista todos los agentes secundarios configurados en el ecosistema Miku (ej. Antigravity, GitHub, Claude Code, Vercel), detallando su rol, especialidad y si están libres o trabajando.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delegar_a_agente",
            "description": "Delega una tarea técnica o especializada a un agente secundario específico (ej. 'antigravity', 'github'). El agente ejecutará la tarea en segundo plano con herramientas autónomas. Al terminar, le notificará al usuario y a Miku.",
            "parameters": {
                "type": "object",
                "properties": {
                    "agente": {
                        "type": "string",
                        "description": "Nombre o ID del agente ('antigravity', 'github')"
                    },
                    "tarea": {
                        "type": "string",
                        "description": "Instrucción técnica detallada o tarea a ejecutar en segundo plano"
                    }
                },
                "required": ["agente", "tarea"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "abrir_chat_con_agente",
            "description": "Cambia la vista activa de la interfaz de la isla dinámica al chat de un agente específico (ej. 'antigravity', 'github', o 'miku' para la orquestadora principal).",
            "parameters": {
                "type": "object",
                "properties": {
                    "agente": {
                        "type": "string",
                        "description": "Nombre o ID del agente al cual cambiar la pantalla ('antigravity', 'github', 'miku')"
                    }
                },
                "required": ["agente"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "crear_o_actualizar_agente",
            "description": "Crea un nuevo agente secundario o actualiza el rol de uno existente en el ecosistema Miku.",
            "parameters": {
                "type": "object",
                "properties": {
                    "id": {
                        "type": "string",
                        "description": "Identificador único en minúsculas (ej. 'designer', 'tester')"
                    },
                    "nombre": {
                        "type": "string",
                        "description": "Nombre visible del agente"
                    },
                    "rol": {
                        "type": "string",
                        "description": "Rol, especialidad o descripción de funciones del agente"
                    },
                    "color": {
                        "type": "string",
                        "description": "Color hexadecimal para su avatar (opcional, ej. '#4FD3B1')"
                    }
                },
                "required": ["id", "nombre", "rol"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delegar_tarea",
            "description": "Inicia un agente de Inteligencia Artificial en segundo plano (paralelo) para realizar tareas largas (como investigar en la web profundamente, resumir datos largos, o escribir un documento grande). Miku te avisarÃ¡ en unos segundos cuando el agente termine.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tarea": {
                        "type": "string",
                        "description": "La instrucciÃ³n detallada que el agente debe ejecutar en paralelo"
                    }
                },
                "required": ["tarea"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "guardar_ultimo_reporte_en_escritorio",
            "description": "Crea un archivo de texto (.txt) en el escritorio y guarda automÃ¡ticamente el texto del ÃšLTIMO reporte generado por el agente de fondo. Ãšsalo si el usuario te pide guardar o exportar la investigaciÃ³n a un bloc de notas.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre_archivo": {
                        "type": "string",
                        "description": "El nombre que se le darÃ¡ al archivo (sin la extensiÃ³n .txt)"
                    }
                },
                "required": ["nombre_archivo"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "ejecutar_comando_sistema",
            "description": "Ejecuta un comando nativo en la consola de Windows (PowerShell/CMD) de la PC del usuario. Ãšsalo para controlar aplicaciones (ej. 'start spotify:search:joji'), abrir webs ('start https://netflix.com'), o controlar el sistema operativo en general de forma rÃ¡pida y confiable.",
            "parameters": {
                "type": "object",
                "properties": {
                    "comando": {
                        "type": "string",
                        "description": "El script o comando de consola a ejecutar"
                    }
                },
                "required": ["comando"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "reproducir_en_spotify",
            "description": "Busca y reproduce mÃºsica en la cuenta de Spotify vinculada del usuario. Ãšsalo SIEMPRE que el usuario te pida escuchar mÃºsica de forma genÃ©rica, o si menciona Spotify, Ã¡lbumes, canciones o playlists.",
            "parameters": {
                "type": "object",
                "properties": {
                    "busqueda": {
                        "type": "string",
                        "description": "El nombre del artista, canciÃ³n, Ã¡lbum o playlist a buscar."
                    },
                    "tipo": {
                        "type": "string",
                        "description": "El tipo de bÃºsqueda. Opciones vÃ¡lidas: 'track' (canciÃ³n individual, por defecto), 'artist' (artista), 'album' (Ã¡lbum), 'playlist' (lista de reproducciÃ³n).",
                        "enum": ["track", "artist", "album", "playlist"]
                    }
                },
                "required": ["busqueda"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "controlar_spotify",
            "description": "Controla la reproducciÃ³n actual de Spotify (pausa, play, saltar, volver, modos aleatorios). ÃšSALO cuando el usuario te pida pausar, continuar, pasar de canciÃ³n, o poner aleatorio EN SPOTIFY.",
            "parameters": {
                "type": "object",
                "properties": {
                    "accion": {
                        "type": "string",
                        "description": "La acciÃ³n a realizar. Valores permitidos: 'play', 'pause', 'next', 'previous', 'shuffle_on', 'shuffle_off', 'repeat_track', 'repeat_off'.",
                        "enum": ["play", "pause", "next", "previous", "shuffle_on", "shuffle_off", "repeat_track", "repeat_off"]
                    }
                },
                "required": ["accion"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "que_suena_en_spotify",
            "description": "Consulta quÃ© canciÃ³n y artista se estÃ¡n reproduciendo actualmente en Spotify. Ãšsalo si el usuario pregunta 'Â¿quÃ© estoy escuchando?' o 'Â¿quÃ© canciÃ³n es esta?'.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "reproducir_en_youtube",
            "description": "Abre YouTube en el navegador web, busca el video o canciÃ³n especificada, y hace clic en el primer resultado. Ãšsalo SÃ“LO si el usuario pide explÃ­citamente buscar o poner algo en YouTube.",
            "parameters": {
                "type": "object",
                "properties": {
                    "busqueda": {
                        "type": "string",
                        "description": "La consulta de bÃºsqueda para YouTube (ej. 'tutorial de python', 'canciÃ³n de cuna')"
                    }
                },
                "required": ["busqueda"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "controlar_multimedia",
            "description": "Pausa, reproduce o salta canciones en la PC usando las teclas multimedia. Ãšsalo SOLO si la mÃºsica YA ESTÃ SONANDO y el usuario te pide pausar o saltar. NO lo uses si el usuario te pide buscar o poner una canciÃ³n nueva (para eso usa reproducir_en_spotify).",
            "parameters": {
                "type": "object",
                "properties": {
                    "accion": {
                        "type": "string",
                        "description": "La acciÃ³n a realizar: 'play', 'pausa', 'siguiente', 'anterior'"
                    }
                },
                "required": ["accion"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "aprender_sobre_usuario",
            "description": "Guarda permanentemente en tu memoria a largo plazo CUALQUIER informaciÃ³n importante que el usuario te pida recordar: tutoriales, guÃ­as paso a paso de cÃ³mo hacer algo (ej. cÃ³mo enviar mensajes en Instagram), reglas, datos personales o preferencias. ÃšSALO SIEMPRE que el usuario diga 'recuerda esto', 'te enseÃ±arÃ©', o te explique cÃ³mo funciona algo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "dato": {
                        "type": "string",
                        "description": "El hecho, tutorial o regla a recordar detalladamente (ej. 'Para enviar mensajes en Instagram debo abrir instagram.com y buscar el icono del aviÃ³n')"
                    }
                },
                "required": ["dato"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "guardar_enlace_memoria",
            "description": "Guarda permanentemente una URL, enlace, o imagen de referencia en tu colecciÃ³n de enlaces. Ãšsalo para recordar pÃ¡ginas, productos, imÃ¡genes o artÃ­culos.",
            "parameters": {
                "type": "object",
                "properties": {
                    "contexto": {
                        "type": "string",
                        "description": "DescripciÃ³n clara de quÃ© es esta URL (ej. 'Imagen del ojo con el corazÃ³n en Pinterest', 'ArtÃ­culo sobre gatos')"
                    },
                    "url": {
                        "type": "string",
                        "description": "La URL completa a guardar (ej. 'https://pinterest...')"
                    }
                },
                "required": ["contexto", "url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "buscar_en_memoria",
            "description": "Busca en tu memoria vectorial a largo plazo. Ãšsalo cuando el usuario te pregunte por algo que le gusta, algo que guardaste antes o un enlace viejo que no estÃ¡ en tu memoria reciente. Usa bÃºsqueda semÃ¡ntica, asÃ­ que puedes buscar conceptos y no palabras exactas.",
            "parameters": {
                "type": "object",
                "properties": {
                    "consulta": {
                        "type": "string",
                        "description": "Lo que quieres buscar (ej. 'dibujo de ojo anime', 'color favorito', 'mÃºsica relax')"
                    }
                },
                "required": ["consulta"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "escanear_ventana_activa",
            "description": "(HERRAMIENTA LIMITADA) Escanea SOLO la ventana activa usando cÃ³digo. NO ve la pantalla completa. Solo Ãºsala para apps nativas de Windows simples. Para TODO lo demÃ¡s (navegadores, Spotify, hacer clic en pestaÃ±as, barra de tareas, etc.) usa 'hacer_clic_visual' que ve TODA la pantalla.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "hacer_clic_visual",
            "description": "(HERRAMIENTA PRINCIPAL DE INTERACCIÃ“N) Toma una foto de TODA la pantalla completa (incluyendo barra de tareas, pestaÃ±as del navegador, ventanas inactivas, TODO), analiza visualmente la imagen con IA, y hace clic donde sea necesario. Usa esta herramienta SIEMPRE que el usuario te pida hacer clic, cambiar de pestaÃ±a, abrir algo en la barra de tareas, interactuar con cualquier programa, etc. Funciona con CUALQUIER aplicaciÃ³n y CUALQUIER parte de la pantalla. DespuÃ©s de hacer clic, VERIFICA automÃ¡ticamente si la acciÃ³n funcionÃ³.",
            "parameters": {
                "type": "object",
                "properties": {
                    "intencion": {
                        "type": "string",
                        "description": "La intenciÃ³n del usuario (ej. 'cambiar a la pestaÃ±a que dice Cyberpunk', 'reproducir la primera canciÃ³n', 'hacer clic en el icono de Chrome en la barra de tareas', 'abrir el primer video')"
                    },
                    "verificar_exito": {
                        "type": "boolean",
                        "description": "Si es True, tomarÃ¡ una segunda foto DESPUÃ‰S del clic para confirmar que funcionÃ³. Si fallÃ³, intentarÃ¡ hacer clic en otro lado para arreglarlo. OBLIGATORIO usar True en clics complejos y propensos a fallar (seleccionar animes, resultados de bÃºsqueda). Usa False en clics simples y seguros."
                    }
                },
                "required": ["intencion"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "escribir_en_elemento",
            "description": "Hace clic en una caja de texto (usando su ID) y escribe un texto en ella (opcionalmente presionando Enter al final).",
            "parameters": {
                "type": "object",
                "properties": {
                    "element_id": {
                        "type": "string",
                        "description": "El ID numÃ©rico de la caja de texto (ej. '12')"
                    },
                    "texto": {
                        "type": "string",
                        "description": "El texto que se va a escribir"
                    },
                    "presionar_enter": {
                        "type": "boolean",
                        "description": "true si quieres presionar la tecla Enter despuÃ©s de escribir, false en caso contrario"
                    }
                },
                "required": ["element_id", "texto"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "memorizar_leccion",
            "description": "Si cometes un error (ej. una herramienta falla), analiza por quÃ© fallaste y usa esta funciÃ³n para guardar una regla de comportamiento permanente en tu cerebro para no volver a cometer el mismo error.",
            "parameters": {
                "type": "object",
                "properties": {
                    "leccion": {
                        "type": "string",
                        "description": "La regla que debes seguir en el futuro (ej. 'Al usar spotify, no debo enviar comillas')."
                    }
                },
                "required": ["leccion"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "mover_raton_visual",
            "description": "Usa visiÃ³n de IA para encontrar un elemento en pantalla y SOLO mueve el ratÃ³n sobre Ã©l, SIN hacer clic. Ideal para preparar el cursor antes de hacer scroll (ej. posicionarse sobre un panel de lista o fuera de Ã©l).",
            "parameters": {
                "type": "object",
                "properties": {
                    "intencion": {
                        "type": "string",
                        "description": "La descripciÃ³n del lugar donde quieres colocar el ratÃ³n (ej. 'el recuadro de la lista de capÃ­tulos', 'fuera del reproductor de video')."
                    }
                },
                "required": ["intencion"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "hacer_scroll",
            "description": "Hace scroll (rueda del ratÃ³n) en la posiciÃ³n actual del cursor. Usa 'mover_raton_visual' antes si necesitas asegurarte de que el ratÃ³n estÃ© sobre un elemento o lista especÃ­fica que tenga su propia barra de scroll.",
            "parameters": {
                "type": "object",
                "properties": {
                    "direccion": {
                        "type": "string",
                        "description": "La direcciÃ³n del scroll: 'abajo' o 'arriba'."
                    },
                    "cantidad": {
                        "type": "integer",
                        "description": "La cantidad de scroll (por defecto 500. Valores mayores son scrolls mÃ¡s largos)."
                    }
                },
                "required": ["direccion"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "atajo_teclado",
            "description": "Ejecuta atajos de teclado rÃ¡pidos sin necesitar visiÃ³n. Permite navegar, cerrar cosas o enviar mensajes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "accion": {
                        "type": "string",
                        "description": "La acciÃ³n a realizar. Puede ser un alias ('enter', 'atras', 'cerrar_pestana', 'buscar_navegador', 'copiar', 'pegar', 'seleccionar_todo', etc.) O CUALQUIER combinaciÃ³n de teclas separada por '+' (ej. 'ctrl+j', 'win+d', 'alt+tab', 'ctrl+shift+esc')."
                    }
                },
                "required": ["accion"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "ejecutar_macro_teclado",
            "description": "Ejecuta una lista rÃ¡pida de atajos de teclado y escrituras de texto EN UN SOLO PASO. Ãšsalo SIEMPRE que necesites hacer secuencias (ej. abrir pestaÃ±a nueva, escribir url, presionar enter) para ahorrar peticiones a la API y hacerlo mÃ¡s rÃ¡pido.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pasos": {
                        "type": "array",
                        "description": "Lista de pasos a ejecutar en orden.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "accion": {
                                    "type": "string",
                                    "enum": ["atajo", "escribir", "esperar"],
                                    "description": "El tipo de acciÃ³n."
                                },
                                "valor": {
                                    "type": "string",
                                    "description": "El atajo de teclado (ej. 'ctrl+t', 'enter'), el texto a escribir, o los segundos a esperar (ej. '1.5')."
                                },
                                "presionar_enter": {
                                    "type": "boolean",
                                    "description": "Opcional. Solo vÃ¡lido si accion es 'escribir'. true para presionar Enter despuÃ©s del texto."
                                }
                            },
                            "required": ["accion", "valor"]
                        }
                    }
                },
                "required": ["pasos"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "esperar_segundos",
            "description": "Cierra los ojos y espera pacientemente sin hacer NADA durante un tiempo. ÃšSALO OBLIGATORIAMENTE cuando estÃ©s esperando a que cargue una pÃ¡gina web, una animaciÃ³n, o un programa lento, para evitar tomar mÃºltiples capturas de pantalla innecesarias que saturen tu cuota.",
            "parameters": {
                "type": "object",
                "properties": {
                    "segundos": {
                        "type": "number",
                        "description": "Cantidad de segundos a esperar. Por defecto usa 2.0 si no estÃ¡s segura."
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "cambiar_personalidad",
            "description": "Reescribe tu propia personalidad de forma permanente. Ãšsalo SI Y SOLO SI el usuario te pide explÃ­citamente que cambies tu forma de ser o hablar.",
            "parameters": {
                "type": "object",
                "properties": {
                    "instruccion": {
                        "type": "string",
                        "description": "Lo que el usuario pidiÃ³ cambiar sobre ti."
                    }
                },
                "required": ["instruccion"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "hablar_al_usuario",
            "description": "Usa esta herramienta para decirle una frase corta al usuario MIENTRAS realizas una secuencia de tareas. Por ejemplo, decir 'Ya abrÃ­ Discord, ahora buscarÃ© a Rubius' antes de llamar a la herramienta de visiÃ³n. Te permite dar retroalimentaciÃ³n de voz sin romper la cadena de ejecuciÃ³n.",
            "parameters": {
                "type": "object",
                "properties": {
                    "texto": {
                        "type": "string",
                        "description": "El texto que quieres decirle en voz alta al usuario."
                    }
                },
                "required": ["texto"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "asociar_contacto_app",
            "description": "Asocia el nombre de un contacto con la aplicaciÃ³n en la que se comunican. Usa esto de fondo cuando el usuario mencione un contacto nuevo y la aplicaciÃ³n (ej. 'EnvÃ­ale un mensaje a Juan por WhatsApp').",
            "parameters": {
                "type": "object",
                "properties": {
                    "contacto": {
                        "type": "string",
                        "description": "El nombre del contacto (ej. 'Rubius', 'Jerson')."
                    },
                    "app": {
                        "type": "string",
                        "description": "El nombre de la aplicaciÃ³n (ej. 'Discord', 'WhatsApp', 'Telegram')."
                    },
                    "nombre_en_interfaz": {
                        "type": "string",
                        "description": "OPCIONAL: Si el contacto tiene un apodo o nombre diferente en la UI de la app (ej. si el usuario le dice 'Jerson' pero en WhatsApp sale como 'David Ultimo')."
                    }
                },
                "required": ["contacto", "app"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "mostrar_widget_info",
            "description": "Muestra un widget o ventanita invisible elegante con texto en la pantalla del usuario. Ãšsalo SIEMPRE que te pida el clima, la hora actual, un dato corto, o para notificaciones visuales, en lugar de (o ademÃ¡s de) hablarle.",
            "parameters": {
                "type": "object",
                "properties": {
                    "titulo": {
                        "type": "string",
                        "description": "El tÃ­tulo en grande de la ventana (ej. 'Clima en BogotÃ¡', 'Hora Actual')."
                    },
                    "contenido": {
                        "type": "string",
                        "description": "La informaciÃ³n a mostrar en la ventana."
                    },
                    "icono": {
                        "type": "string",
                        "description": "Un emoji grande que represente la informaciÃ³n (ej. 'â˜€ï¸' para sol, 'ðŸŒ§ï¸' para lluvia, 'â°' para hora). Â¡Siempre incluye uno acorde al tema!"
                    },
                    "duracion_segundos": {
                        "type": "integer",
                        "description": "Opcional. Tiempo que la ventana estarÃ¡ visible antes de cerrarse sola. Por defecto es 15."
                    }
                },
                "required": ["titulo", "contenido"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "mostrar_widget_clima",
            "description": "DEBES usar esta herramienta ESPECÃFICA cuando quieras mostrar el CLIMA al usuario. Nunca uses mostrar_widget_info para el clima.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ciudad": {
                        "type": "string",
                        "description": "La ciudad de la que se muestra el clima (ej. 'Bucaramanga')"
                    },
                    "temperatura": {
                        "type": "string",
                        "description": "La temperatura formateada con el sÃ­mbolo de grados (ej. '26Â°C')"
                    },
                    "estado": {
                        "type": "string",
                        "description": "DescripciÃ³n del clima (ej. 'Mayormente nublado', 'Lluvia ligera')"
                    },
                    "viento": {
                        "type": "string",
                        "description": "Velocidad del viento (ej. '15 km/h')"
                    },
                    "humedad": {
                        "type": "string",
                        "description": "Porcentaje de humedad (ej. '68%')"
                    },
                    "icono_nombre": {
                        "type": "string",
                        "description": "Nombre del archivo SVG a usar. Opciones vÃ¡lidas: 'sunny', 'clear_day', 'clear_night', 'partly_cloudy_day', 'mostly_cloudy_day', 'cloudy', 'rain_showers', 'heavy_rain', 'thunderstorms', 'snow_showers', 'heavy_snow', 'haze_fog', 'windy'. Selecciona el mÃ¡s parecido al clima actual."
                    }
                },
                "required": ["ciudad", "temperatura", "estado", "viento", "humedad", "icono_nombre"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "actualizar_estado_tarea",
            "description": "Actualiza la Memoria Temporal. Ãšsala para registrar quÃ© estÃ¡s intentando hacer, en quÃ© paso vas, o guardar parÃ¡metros extraÃ­dos de la conversaciÃ³n (ej. 'destinatario': 'Carolina'). Muy Ãºtil antes de empezar una macro compleja.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tarea_actual": {
                        "type": "string",
                        "description": "DescripciÃ³n general (ej. 'Enviar mensaje por WhatsApp')"
                    },
                    "paso_actual": {
                        "type": "string",
                        "description": "El paso que estÃ¡s a punto de realizar (ej. 'Abriendo WhatsApp')"
                    },
                    "parametros_json": {
                        "type": "string",
                        "description": "Un JSON en string con parÃ¡metros clave (ej. '{\"destinatario\": \"Carolina\", \"plataforma\": \"WhatsApp\"}')"
                    }
                }
            }
        }
    }
]


tools_schema.extend([{
    "type": "function",
    "function": {
        "name": "hacer_pregunta_opciones",
        "description": "Muestra una interfaz interactiva con botones para hacerle una pregunta de opcion multiple al usuario. Usa esta herramienta para solicitar decisiones, permisos (como Autorizar/Rechazar) o cuando necesites que el usuario elija entre varias plataformas o acciones. El modelo esperara a que el usuario presione un boton.",
        "parameters": {
            "type": "object",
            "properties": {
                "pregunta": {
                    "type": "string",
                    "description": "La pregunta clara y concisa que se le hara al usuario."
                },
                "opciones": {
                    "type": "array",
                    "items": { "type": "string" },
                    "description": "Lista de textos cortos para los botones."
                },
                "titulo": {
                    "type": "string",
                    "description": "Un titulo corto para la ventana flotante."
                }
            },
            "required": ["pregunta", "opciones", "titulo"]
        }
    }
}, {
    "type": "function",
    "function": {
        "name": "preparar_correo",
        "description": "Abre una tarjeta interactiva de borrador de correo para que el usuario pueda revisarlo y confirmar el envio. Usa esta herramienta en lugar de enviar un correo directamente para darle al usuario la ultima palabra. Si el usuario acepta, la herramienta retornara exito.",
        "parameters": {
            "type": "object",
            "properties": {
                "destinatario": {
                    "type": "string",
                    "description": "El correo electronico del destinatario."
                },
                "asunto": {
                    "type": "string",
                    "description": "El asunto del correo."
                },
                "mensaje": {
                    "type": "string",
                    "description": "El cuerpo o contenido del correo electronico."
                }
            },
            "required": ["destinatario", "asunto", "mensaje"]
        }
    }
}])
