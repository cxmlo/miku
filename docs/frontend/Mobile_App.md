# Aplicación Móvil Android 📱

El nuevo cliente móvil activo se está reconstruyendo como aplicación Android nativa en `miku_android/`, con Kotlin y Jetpack Compose. Se comunica con el backend FastAPI que alimenta el Island de escritorio Tauri; no reemplaza ni modifica Tauri.

## Objetivo de la app compañera

La app nativa busca que el teléfono sea una extensión de Miku Desktop, no un asistente separado: el escritorio conserva el backend, los modelos y los agentes; Android ofrece una interfaz móvil para continuar conversaciones, recibir eventos y notificaciones, intercambiar texto y archivos, y confirmar acciones compatibles del teléfono.

El flujo esperado es iniciar Miku Desktop, vincular el teléfono escaneando el QR de Miku-Link y dejar que Android mantenga la sesión con un servicio en primer plano. Cerrar la pantalla de la app no debe desvincular el teléfono; **Desvincular** sí borra las credenciales y detiene la conexión. La conexión depende de que Miku Desktop esté activo y accesible por la red local. Android y algunos fabricantes pueden limitar servicios en segundo plano, por lo que la persistencia y el reinicio deben validarse en dispositivos reales.

La migración está en curso: la app Expo de `miku_app/` se conserva como referencia y rollback hasta validar la paridad funcional. La app nativa no ejecuta código arbitrario recibido desde el escritorio; las acciones del teléfono se presentan para confirmación y se limitan a intents permitidos.

## Arquitectura nativa

- **`app/src/main/java/.../MainActivity.kt`**: interfaz Compose para chat, control del PC, eventos de agentes y vinculación.
- **`data/MikuClient.kt`**: cliente HTTP/WebSocket para el Gateway; carga el historial y los agentes, envía chat y archivos, sincroniza texto del portapapeles y procesa eventos del escritorio.
- **`data/PairingLink.kt`**: valida enlaces QR con el esquema `miku://pair?s={session}&ip={host}` generado por el Island.
- **`data/DeviceStore.kt`**: protege el ID del dispositivo y el nombre del PC con AES-GCM respaldado por Android Keystore.
- **`connection/MikuConnectionService.kt`**: mantiene la conexión en primer plano (`connectedDevice`) y publica notificaciones cuando llegan eventos de agentes. `START_STICKY` permite que Android intente recrearlo si recupera el proceso.
- **`connection/MikuBootReceiver.kt`**: reinicia el servicio tras `BOOT_COMPLETED` si el dispositivo conserva credenciales de pairing.
- **`ui/theme/Color.kt` y `ui/theme/Theme.kt`**: paleta semántica y tema Compose compartidos para evitar que los colores de marca se dispersen por las pantallas.
- **`app/src/main/AndroidManifest.xml`**: declara el servicio de conexión, permisos de red/cámara/notificaciones y el enlace de emparejamiento.

La interfaz y la coordinación de acciones todavía están concentradas en `MainActivity.kt`; separar ViewModels y repositorios es una evolución pendiente, no una capa que ya esté implementada. La arquitectura objetivo y las reglas visuales están en [[PROJECT_ARCHITECTURE_AND_DESIGN]].

## Funciones migradas al cliente nativo

- Vincular con el QR del panel Miku-Link del escritorio.
- Solicitar permiso de cámara antes de escanear y aceptar el enlace `miku://pair` abierto desde otra app de cámara.
- Mostrar el resultado de lectura o cancelación del escáner. El QR del Island se renderiza a mayor tamaño y resolución para facilitar su lectura desde el teléfono.
- Mantener WebSocket al backend y cargar el historial de chat y los agentes configurados.
- Enviar mensajes a Miku o a un agente seleccionado.
- Recibir eventos de agentes y mostrarlos en la app y en notificaciones de Android.
- Enviar archivos del teléfono al PC y solicitar el bloqueo del PC.
- Sincronizar texto del portapapeles en ambos sentidos.
- Recibir archivos compartidos desde el Island; Android solicita al usuario dónde guardarlos.
- Recibir acciones destinadas al teléfono, presentarlas para confirmación y ejecutar solo intents de alarma, temporizador o ajustes incluidos en una lista permitida.
- Mantener el enlace al cerrar la pantalla/app: el foreground service sigue activo y reconecta usando el ID/IP guardados; no hace falta volver a escanear el QR mientras el pairing siga guardado.

Cerrar o descartar la actividad no equivale a desvincular. La acción **Desvincular** borra las credenciales y detiene la conexión. Android puede interrumpir el servicio si el usuario fuerza la detención, si el teléfono se apaga o por restricciones de batería del fabricante; un cambio de IP local del escritorio también puede requerir volver a vincular. El receiver de reinicio está implementado, pero su comportamiento debe probarse en un dispositivo real.

El acceso al Gateway desde la app nativa usa `X-Device-Id` tanto para rutas REST protegidas como para el handshake WebSocket. El backend valida que el dispositivo esté registrado en `miku_devices.db`; las apps antiguas que envían `x-api-key` conservan compatibilidad.

El Island marca el teléfono como conectado solo cuando el WebSocket del dispositivo emparejado se establece; al cerrarse la última conexión móvil, refleja la desconexión. La confirmación del QR por sí sola no indica que el teléfono esté en línea. El WebSocket móvil envía el ID de dispositivo en la cabecera y como parámetro de compatibilidad; un HTTP 403 detiene los reintentos automáticos y muestra que hace falta reiniciar/actualizar el backend de escritorio o volver a vincular el teléfono. Los mensajes enviados desde Android se difunden con el agente y un evento explícito de mensaje de usuario para que la Isla inicie su indicador de pensamiento con el tiempo correcto. Si falla la creación de la sesión QR en Windows, el Island muestra el error en vez de presentar un QR fallback que no se puede vincular. Ambos dispositivos deben compartir una red que permita tráfico local.

## App anterior conservada

`miku_app/` continúa siendo el cliente anterior en React Native/Expo. Se conserva sin retirar sus archivos ni modificar su configuración para servir como referencia y rollback hasta validar paridad funcional de la aplicación Android nativa.

La migración nativa todavía no cubre todas las funciones del cliente Expo. Entre las siguientes candidatas están la grabación y envío de voz, el panel de diagnóstico MCP, los ajustes de claves y la sincronización de imágenes del portapapeles.

La aplicación Android todavía no tiene un cargador general de personajes, assets o animaciones personalizados. El documento de arquitectura define una propuesta segura de packs de contenido sin código ejecutable; debe tratarse como diseño futuro hasta implementar y probar el cargador.

## Compilar y distribuir APK a usuarios

### Opción 1: Compilación Local de APK Release (Nativo - Recomendado)
Requisitos: JDK 17, Android SDK Platform 36 y Android Build Tools 36.0.0. Desde la carpeta `miku_android/`:

```powershell
# Para generar el APK de release listo para instalar:
.\gradlew.bat assembleRelease
```
El APK se genera en:
`miku_android/app/build/outputs/apk/release/app-release-unsigned.apk` (o firmado con keystore). Es extremadamente ligero (~15MB), optimizado con ProGuard/R8 y no depende de Node ni Expo.

### Opción 2: Compilación Automatizada en la Nube (GitHub Actions - Sin Android Studio local)
Se puede configurar un flujo en `.github/workflows/build-android.yml` con `actions/setup-java@v3` y `gradle-build-action`. En cada commit o tag, GitHub compila el APK en servidores Linux de alta velocidad y publica el instalador `.apk` directamente en la pestaña "Releases" para que cualquier usuario lo descargue con un clic.

### Opción 3: Aplicación Expo (`miku_app/`)
Para la app alternativa de React Native/Expo:
```bash
npx eas build -p android --profile preview
```
Genera un APK descargable compilado en la nube de Expo.

## Persistencia de Miku-Link con la App Cerrada
1. **En PC (Escritorio)**:
   - Al cerrar la ventana del Island o Configuración, la aplicación intercepta el evento de cierre (`CloseRequested`) y oculta la ventana (`window.hide()`), manteniendo el servidor FastAPI en el puerto 8000 y el túnel Cloudflare activos en la bandeja del sistema (System Tray).
2. **En Android**:
   - `MikuConnectionService.kt` es un `ForegroundService` con `android:stopWithTask="false"` y `START_STICKY`.
   - Cuando el usuario desliza la app o la cierra de la lista de aplicaciones recientes, el servicio permanece conectado mostrando una notificación persistente de bajo perfil.
   - **Ajuste crítico para fabricantes agresivos (Xiaomi/MIUI, Samsung OneUI, Huawei)**: El usuario debe configurar en los ajustes de la app Android la optimización de batería en **"Sin restricciones" (Unrestricted)** y habilitar **"Inicio automático"** para evitar que el sistema operativo mate la conexión WebSocket en reposo.

El protocolo local usa HTTP/WebSocket en la red interna o túnel seguro de Cloudflare si se conecta remotamente.

## Diseño Miku UI y Sincronización QR
- **Diseño Liquid Glass**: La app móvil utiliza la paleta oficial Miku UI (`#06070B` fondo, `#0E111A` tarjetas/superficies translúcidas, `#38BDF8` cian de acento, bordes de 1dp translúcidos y botones píldora `99.dp`).
- **Sincronización QR Canónica**: La sesión de emparejamiento QR está centralizada a través de `get_canonical_pairing_info` en el backend, sincronizando de forma idéntica los códigos QR mostrados en la Isla, Ajustes y la ventana dedicada de Miku-Link.

## Comunicación

- **Emparejamiento y Gateway**: [[Backend_Gateway]]
- **Interfaz de escritorio y generador QR**: [[Desktop_Island_Tauri]]
- **Permisos y dispositivos vinculados**: [[Database_and_Security]]

👉 Volver a [[Home]]
