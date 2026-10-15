# Aplicación Móvil (React Native) 📱

La aplicación móvil (`miku_app/`) es la interfaz primaria a través de la cual interactúas remotamente con Miku. Está construida usando **React Native** con el framework **Expo** (SDK 50+).

## Componentes y Arquitectura de Rutas (`app/`)
- **`_layout.tsx`**: Define el RootLayout. Envuelve todo en el `WebSocketProvider` y crucialmente en el `GestureHandlerRootView` para permitir animaciones de arrastre seguras (como los BottomSheets).
- **`index.tsx`**: Pantalla principal inmersiva.
  - Muestra un visor inmersivo (GIFs de Miku cargados dinámicamente según el estado: idle, listening, thinking).
  - Modal dinámico de Secretos (`open_secrets_panel`): Permite al usuario pegar contraseñas en campos generados dinámicamente, asegurando que las claves complejas (como OAuth de Google) no se rompan, y sin censura para asegurar precisión.
- **`components/AssistantOverlay.tsx`**:
  - Modal dinámico tipo "BottomSheet" (estilo Asistente de Google) con animaciones de arrastre (`react-native-reanimated` y `react-native-gesture-handler`).
  - Cuenta con autoinicio de micrófono para grabaciones de voz fluidas.
  - Muestra ondas de audio animadas cuando el usuario habla.
- **`devices.tsx`**: Administrador de dispositivos vinculados.
  - Utiliza `expo-camera` para escáner QR de emparejamiento.
  - Verifica tokens y esquemas de vinculación profunda (`miku://pair`).
- **`diagnostics.tsx`**: Panel de control técnico y monitoreo.
  - Se comunica mediante la API REST (`/api/desktop/status`) del servidor para obtener información sobre la red, versión del SO del servidor (Python/Windows), y monitorea el estado en vivo de los servidores **MCP (Model Context Protocol)**.
  - Permite eliminar servidores MCP dinámicamente (Llama a `DELETE /api/mcp/{server_name}`).
  - Interfaz responsiva que muestra 3 servidores por defecto y permite expandir para ver todos.
  - Posee una consola en vivo para registrar los eventos locales de conexión.

## Manejo de Estado (Context)
- **`context/WebSocketContext.tsx`**:
  - Proveedor global de conexión en tiempo real (Socket).
  - Mantiene viva la conexión implementando un bucle Ping/Pong automático para evitar desconexiones por inactividad.
  - Evita audios dobles: Implementa caché de 2 segundos para `play_audio` que previene el eco ante reconexiones rápidas de WebSocket.
  - Recibe eventos de sistema como "cambios de portapapeles" (`clipboard_update`) e inyecta texto directamente al portapapeles de iOS/Android usando `expo-clipboard`.
  - Escucha el comando `ejecutar_intent_android` utilizando `expo-intent-launcher` para disparar acciones a nivel de sistema operativo (como configurar alarmas o temporizadores en la aplicación de reloj nativa).
  - Recibe comandos UI directos como estados de pensamiento.

## Enlaces Relacionados
- 👉 Volver a [[Home]]
- Se comunica directamente con: [[Backend_Gateway]]
