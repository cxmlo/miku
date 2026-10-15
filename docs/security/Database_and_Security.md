# Base de Datos y Seguridad 🛡️

Todo el sistema de autorización y la identidad del ecosistema recae en estos componentes para garantizar que nadie externo pueda tomar control de Miku.

## Base de Datos Central

- **`miku_db.py`**:
  - `init_db()`: Inicializa o migra la estructura en SQLite (`miku_devices.db`).
  - `add_device()`, `remove_device()`, `get_device()`, `get_all_devices()`: CRUD de dispositivos vinculados.
  - `update_last_seen()`: Lleva el rastreo de actividad de la app móvil.
  - `is_valid_device()`: Comprueba un token en tiempo real cada vez que la app envía un request o mensaje por WebSocket.
  - `get_server_identity()`, `get_server_public_key_b64()`: Expone la llave criptográfica generada aleatoriamente al arrancar (`miku_identity.json`).

## Seguridad Móvil (React Native)
En la app móvil (👉 [[Mobile_App]]), los secretos de emparejamiento (ej. el token `miku_secret_identity`) se almacenan utilizando `expo-secure-store`, lo que asegura que estén guardados en la bóveda de hardware del dispositivo móvil (Keychain/Keystore).

## Protocolo de Vinculación Segura (Pairing Flow)
1. **[[Widgets_and_UI]]** genera un código QR que contiene la firma pública y la IP local.
2. **[[Mobile_App]]** escanea el QR.
3. El móvil envía su petición a `/pair_init` y `/pair_confirm` (endpoints de `server.py`).
4. `miku_db.py` valida la criptografía, registra la nueva identidad y emite un JWT permanente (JSON Web Token).

## Enlaces Relacionados
- 👉 Volver a [[Home]]
