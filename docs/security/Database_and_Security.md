# Base de Datos y Seguridad 🛡️

Todo el sistema de autorización y la identidad del ecosistema recae en estos componentes para garantizar que nadie externo pueda tomar control de Miku.

## Base de Datos Central

- **`miku_db.py`**:
  - `init_db()`: Inicializa o migra la estructura en SQLite (`miku_devices.db`).
  - `add_device()`, `remove_device()`, `get_device()`, `get_all_devices()`: CRUD de dispositivos vinculados.
  - `update_last_seen()`: Lleva el rastreo de actividad de la app móvil.
  - `is_valid_device()`: Comprueba un token en tiempo real cada vez que la app envía un request o mensaje por WebSocket.
  - `get_server_identity()`, `get_server_public_key_b64()`: Expone la llave criptográfica generada aleatoriamente al arrancar (`miku_identity.json`).

## Credenciales Móviles

- El cliente nativo Android (👉 [[Mobile_App]]) cifra el identificador emparejado con AES-GCM y una clave del Android Keystore.
- El cliente anterior `miku_app/` permanece en Expo y conserva su almacenamiento SecureStore durante la migración.
- La app nativa presenta el identificador emparejado como `X-Device-Id` en REST y en el handshake WebSocket. El servidor acepta solo IDs registrados, además del mecanismo de API key usado por clientes anteriores.

El ID funciona actualmente como una credencial bearer: el protocolo local usa HTTP/WebSocket sin TLS cuando el QR contiene una IP local. No debe interpretarse como firma criptográfica de cada solicitud.

## Protocolo de Vinculación (Pairing Flow)
1. El Island de escritorio registra una sesión temporal en `/api/pair/init` y genera un QR `miku://pair?s={session}&ip={host}`.
2. La app nativa (`miku_android/`) escanea el QR y envía un ID aleatorio y una clave pública declarada a `/api/pair/confirm`.
3. El backend comprueba que la sesión coincida, consume la sesión y registra el ID con `miku_db.add_device()`.
4. El ID registrado habilita las peticiones del cliente; la app lo cifra localmente con Android Keystore.

El backend mantiene una identidad Ed25519 y devuelve su clave pública en el emparejamiento, pero el flujo actual no firma solicitudes ni valida una prueba de posesión de la clave pública del teléfono. Por tanto, el enlace de emparejamiento y el control de acceso son mecanismos de confianza local, no un protocolo de autenticación criptográfica completo.

## Enlaces Relacionados
- 👉 Volver a [[Home]]
