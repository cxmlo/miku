import notifee, { AndroidImportance, AndroidCategory } from '@notifee/react-native';

const CHANNEL_ID = 'miku-link-service';
const NOTIFICATION_ID = 'miku-foreground';

/**
 * Inicia el Foreground Service de Miku Link.
 * Esto muestra una notificación persistente (como Phone Link / Spotify)
 * que le dice a Android: "No mates esta app, está haciendo trabajo en tiempo real."
 */
export async function startMikuForegroundService() {
  try {
    // 1. Pedir permisos de notificación (obligatorio en Android 13+, en Android no devuelve status)
    await notifee.requestPermission();

    // 2. Crear el canal de notificación (solo necesario una vez, Android lo ignora si ya existe)
    await notifee.createChannel({
      id: CHANNEL_ID,
      name: 'Miku Link',
      description: 'Mantiene la conexión con tu PC activa en segundo plano',
      importance: AndroidImportance.LOW, // LOW = sin sonido, sin vibración, solo icono persistente
    });

    // Lanzar la notificación de foreground service
    await notifee.displayNotification({
      id: NOTIFICATION_ID,
      title: 'Miku Link activo',
      body: 'Conectada a tu PC en segundo plano',
      android: {
        channelId: CHANNEL_ID,
        asForegroundService: true,
        category: AndroidCategory.SERVICE,
        ongoing: true, // No se puede deslizar para cerrar
        pressAction: { id: 'default' }, // Al tocar, abre la app
        actions: [
          {
            title: 'Desconectar',
            pressAction: { id: 'stop' },
          },
        ],
      },
    });

    console.log('[MikuFG] Foreground service iniciado');
  } catch (e) {
    console.warn('[MikuFG] Error iniciando foreground service:', e);
  }
}

/**
 * Actualiza el texto de la notificación persistente (ej. estado de conexión).
 */
export async function updateForegroundNotification(body: string) {
  try {
    await notifee.displayNotification({
      id: NOTIFICATION_ID,
      title: 'Miku Link activo',
      body,
      android: {
        channelId: CHANNEL_ID,
        asForegroundService: true,
        category: AndroidCategory.SERVICE,
        ongoing: true,
        pressAction: { id: 'default' },
        actions: [
          {
            title: 'Desconectar',
            pressAction: { id: 'stop' },
          },
        ],
      },
    });
  } catch (e) {
    // Silenciar errores de actualización
  }
}

/**
 * Detiene el Foreground Service y quita la notificación persistente.
 */
export async function stopMikuForegroundService() {
  try {
    await notifee.stopForegroundService();
    console.log('[MikuFG] Foreground service detenido');
  } catch (e) {
    console.warn('[MikuFG] Error deteniendo foreground service:', e);
  }
}
