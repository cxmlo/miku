# Arquitectura de Firma de APK (Keystore en GitHub Actions) y Seguridad

Plan de implementación detallado para habilitar la firma de release oficial en GitHub Actions, eliminar los bloqueos de Google Play Protect y garantizar el 100% de las funciones del móvil, incorporando directivas estrictas de seguridad para que ninguna clave ni credencial quede expuesta.

---

## Seguridad de las Claves y del Workflow

> [!NOTE]
> **¿Es seguro almacenar el Keystore en GitHub?**
> **Sí, es el estándar de la industria utilizado por proyectos de código abierto y empresas.**
> 
> 1. **Cifrado de Secretos (NaCl/libsodium)**: Los valores guardados en *GitHub Actions Secrets* se cifran en el navegador antes de enviarse a GitHub. Nadie (ni visitantes, ni usuarios, ni siquiera tú una vez guardados) puede ver el contenido en texto plano. Solo la máquina virtual de compilación puede descifrarlo en memoria.
> 2. **Enmascaramiento automático de logs**: GitHub Actions detecta automáticamente los secretos y los reemplaza por `***` en cualquier registro o consola.
> 3. **Máquinas virtuales efímeras (Runners desechables)**: El archivo `.jks` se decodifica únicamente dentro de `$RUNNER_TEMP` (memoria temporal aislada) y toda la máquina virtual de Ubuntu se destruye y borra por completo al finalizar la compilación.
> 4. **Protección contra Pull Requests externos**: El workflow solo tiene acceso a los secretos cuando se ejecuta en tu propia rama `main` o mediante activación manual (`workflow_dispatch`), impidiendo que un tercero intente acceder a ellos.
> 5. **Naturaleza del Keystore**: Un `.jks` de Android no contiene dinero, tokens de pago ni contraseñas de cuentas personales; es simplemente un certificado digital de autoría para certificar a Android que el APK proviene de ti.

```
┌────────────────────────────────────────────────────────────────────────┐
│                   AISLAMIENTO Y SEGURIDAD DEL RUNNER                   │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│   [ GitHub Secrets (Cifrado NaCl) ]                                    │
│                 │                                                      │
│                 v (Inyección en memoria cifrada)                       │
│   ┌────────────────────────────────────────────────────────────────┐   │
│   │ Runner Efímero de Ubuntu (GitHub Actions)                      │   │
│   │                                                                │   │
│   │  • $RUNNER_TEMP/miku.jks (Existe solo durante la compilación) │   │
│   │  • apksigner firma el binario .apk                            │   │
│   │  • Logs enmascarados con '***' para evitar fugas               │   │
│   │  • Destrucción inmediata del runner y archivos temporales      │   │
│   └────────────────────────────────────────────────────────────────┘   │
│                 │                                                      │
│                 v (Solo sale el binario compilado)                     │
│   [ miku-mobile.apk Firmado ] ──> [ Tu Teléfono ]                      │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 1. Configuración de Firma Criptográfica (Release Keystore)

### A. Generación del Keystore
Proveeremos un script automatizado (`scripts/generate_keystore.bat` y `.sh`) que ejecuta:
```bash
keytool -genkey -v -keystore miku-release.jks -alias miku -keyalg RSA -keysize 2048 -validity 10000
```
El script exporta el archivo a Base64 listo para copiar y pegar en GitHub sin exponer la clave en el historial de Git.

### B. Secretos requeridos en GitHub
En `Repositorio > Settings > Secrets and variables > Actions`:
- `KEYSTORE_BASE64`: Cadena codificada del archivo de firma.
- `KEYSTORE_PASSWORD`: Contraseña del almacén.
- `KEY_ALIAS`: Alias de la clave (ej. `miku`).
- `KEY_PASSWORD`: Contraseña de la clave privada.

*(Ninguno de estos valores se sube a archivos `.git` ni a ramas públicas; se ignoran explícitamente en `.gitignore`).*

### C. Actualización de `.github/workflows/build-android.yml`
- Decodificación segura en `$RUNNER_TEMP` (aislado del código fuente).
- Parámetros de firma inyectados mediante variables de entorno en el paso de `assembleRelease`.
- Eliminación explícita del keystore temporal al concluir el job.
- Adjunto del APK firmado a los Releases públicos y a los artefactos de la compilación.

---

## 2. Arquitectura de Sincronización sin Bloqueo de Play Protect

Para mantener el 100% de las funciones solicitadas ("Todas") sin disparar la heurística de fraude financiero de Play Protect:

1. **Notificaciones y Mensajes (WhatsApp, Telegram, SMS, Llamadas)**:
   - Canal: `MikuNotificationListenerService` (`BIND_NOTIFICATION_LISTENER_SERVICE`).
   - Android entrega legítimamente cualquier mensaje o aviso recibido en la barra de estado mediante el permiso seguro de sistema *Acceso a notificaciones*.
   - No requiere permisos de SMS invasivos (`READ_SMS`/`SEND_SMS`), los cuales eran los causantes del bloqueo duro de Play Protect.

2. **Fotos y Archivos**:
   - Canal: Android Photo Picker (`ActivityResultContracts.PickVisualMedia`) y `READ_MEDIA_IMAGES`.
   - Transferencia bidireccional inmediata con Miku Desktop a través del WebSocket seguro.

3. **Acciones Rápidas (Phone Link)**:
   - Modo No Molestar (`ACCESS_NOTIFICATION_POLICY`).
   - Hacer sonar el móvil con vibración y alarma continua (`VIBRATE` + `STREAM_ALARM`).
   - Control de música y sincronización de volumen de la PC.

---

## 3. Plan de Ejecución por Fases

### Fase 1: Blindaje en Gradle y Android (`miku_android`)
- Configurar `miku_android/app/build.gradle.kts` para leer los secretos de firma desde variables de entorno con fallback limpio.
- Asegurar que `.gitignore` excluya cualquier archivo `.jks`, `.keystore` o `.p12` local.

### Fase 2: Actualización Segura del Workflow de GitHub Actions
- Actualizar `.github/workflows/build-android.yml` con decodificación en `$RUNNER_TEMP` y paso de firma blindado.
- Validar que no haya comandos `echo` ni impresiones de variables en consola.

### Fase 3: Script Asistente y Documentación
- Crear `scripts/generate_keystore.bat` y `scripts/generate_keystore.sh` para generar el certificado en 1 clic.
- Redactar `docs/FIRMA_ANDROID_GITHUB.md` con las instrucciones ilustradas paso a paso para añadir los 4 secretos en GitHub.

---

## 4. Verificación

1. **Validación de Sintaxis**: Probar `build.gradle.kts` y la sintaxis del workflow.
2. **Inspección de Seguridad**: Verificar que ningún secreto ni archivo de firma quede rastreado por git.
3. **Instalación limpia**: Comprobar que el APK firmado resultante se instale sin bloqueos de Play Protect en el dispositivo.
