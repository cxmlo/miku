# Guía Oficial: Firma de APK con Keystore en GitHub Actions

Esta guía explica cómo compilar y firmar automáticamente el APK de **Miku-Link** en **GitHub Actions** con una huella digital criptográfica (SHA-256) oficial para que **Google Play Protect** lo reconozca como una app segura y no bloquee su instalación en tu teléfono.

---

## ¿Por qué es necesaria la firma oficial?

Cuando un APK se compila sin clave de producción, Android lo etiqueta como `Android Debug`. Google Play Protect desconfía por defecto de las apps de depuración instaladas fuera de la tienda oficial. Al firmarlo con tu propio **Keystore Release (SHA-256)**:
- El sistema operativo y Play Protect verifican la autenticidad del autor.
- Permite actualizar la app en tu teléfono en futuras versiones sin perder la configuración ni tener que desinstalarla.
- No se expone ninguna clave ni información sensible.

---

## Paso 1: Generar tu clave Keystore (1 solo clic)

En la carpeta del proyecto, ejecuta el script automatizado:

### En Windows:
Haz doble clic en:
```
scripts\generate_keystore.bat
```
1. Te pedirá una contraseña (o puedes presionar Enter para usar la recomendada).
2. Creará el archivo `miku-release.jks`.
3. Creará el archivo `keystore_base64.txt` y **copiará su contenido automáticamente al portapapeles de Windows**.

### En Linux / macOS:
```bash
chmod +x scripts/generate_keystore.sh
./scripts/generate_keystore.sh
```

*(Nota de seguridad: El archivo `.gitignore` ya está configurado para ignorar automáticamente `*.jks`, `*.keystore` y `keystore_base64.txt`, evitando que se suban por error a tu repositorio).*

---

## Paso 2: Configurar los 4 Secretos en GitHub

1. Entra a tu repositorio en GitHub desde tu navegador:
   `https://github.com/<tu-usuario>/miku/settings/secrets/actions`
2. Pulsa el botón verde **«New repository secret»** y añade los siguientes 4 secretos:

| Nombre del Secreto | Valor |
| :--- | :--- |
| **`KEYSTORE_BASE64`** | Pega el texto que el script copió a tu portapapeles (o el contenido de `keystore_base64.txt`). |
| **`KEYSTORE_PASSWORD`** | La contraseña que elegiste al generar la clave (ej. `MikuSecureKey2026!`). |
| **`KEY_ALIAS`** | `miku` |
| **`KEY_PASSWORD`** | La misma contraseña que pusiste en `KEYSTORE_PASSWORD`. |

---

## Paso 3: Compilar el APK Firmado en GitHub

1. En tu repositorio de GitHub, ve a la pestaña superior **«Actions»**.
2. En el menú lateral izquierdo, selecciona el flujo: **«Build Miku Android APK»**.
3. Haz clic en el botón desplegable **«Run workflow»** (a la derecha).
4. Elige `release` y pulsa **«Run workflow»**.

El workflow de GitHub Actions:
- Descifrará temporalmente la clave en la memoria protegida del runner (`$RUNNER_TEMP`).
- Compilará y firmará el APK con `apksigner`.
- Imprimirá la huella SHA-256 de verificación.
- Destruirá inmediatamente la clave temporal al terminar.
- Guardará el archivo **`miku-mobile.apk`** firmado en la sección **Artifacts** y en las **Releases** de tu repositorio.

---

## Paso 4: Instalar en tu teléfono

1. Descarga el archivo `miku-mobile.apk` generado directamente a tu teléfono Redmi/Xiaomi.
2. Ábrelo y pulsa **Instalar**.
3. La aplicación se instalará directamente sin pantallas de bloqueo de Play Protect.
4. Al abrir Miku-Link, pulsa **«Escanear QR»** desde la pestaña **Miku-Link** de tu PC para sincronizar portapapeles, fotos, mensajes y llamadas al instante.
