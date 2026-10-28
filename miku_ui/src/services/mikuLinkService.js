/**
 * Miku-Link Transport Service (`LinkTransport` — Fase 5, §7.4)
 * Capa de transporte aislada para comunicar la sección Miku-Link de Configuración
 * con el backend real de Miku (HTTP REST + WebSocket + progreso real de subida).
 * Prohibido inventar datos locales o simular progreso con setTimeout/Math.random.
 */

const DEFAULT_BASE_URL = 'http://127.0.0.1:8000';

export class LinkTransport {
  constructor(baseUrl = DEFAULT_BASE_URL) {
    this.baseUrl = baseUrl.replace(/\/+$/, '');
    this._listeners = new Set();
    this._ws = null;
    this._reconnectTimer = null;
    this._bc = null;
    try {
      this._bc = new BroadcastChannel('miku');
      this._bc.onmessage = (ev) => {
        if (ev?.data) this._emit(ev.data);
      };
    } catch (_) {}
  }

  onEvent(listener) {
    if (typeof listener !== 'function') return () => {};
    this._listeners.add(listener);
    return () => this._listeners.delete(listener);
  }

  _emit(event) {
    this._listeners.forEach((fn) => {
      try {
        fn(event);
      } catch (_) {}
    });
  }

  async _json(path, options = {}) {
    const res = await fetch(`${this.baseUrl}${path}`, {
      headers: {
        'Content-Type': 'application/json',
        ...(options.headers || {})
      },
      ...options
    });
    if (!res.ok) {
      let detail = `HTTP ${res.status}`;
      try {
        const errBody = await res.json();
        if (errBody?.detail) detail = errBody.detail;
        else if (errBody?.message) detail = errBody.message;
      } catch (_) {}
      throw new Error(detail);
    }
    return res.json();
  }

  /** Estado general de Miku-Link y telemetría real del teléfono */
  async getStatus() {
    return this._json('/api/link/status');
  }

  /** Obtiene un nuevo token efímero de un solo uso (120 s) y PIN de 6 dígitos del backend */
  async requestPairingToken() {
    return this._json('/api/link/qr_data');
  }

  /** Cancela la sesión de vinculación activa en el backend */
  async cancelPairing() {
    return this._json('/api/link/cancel_pair', { method: 'POST' });
  }

  /** Desvincula el dispositivo móvil y revoca sus credenciales en base de datos */
  async unpairDevice(deviceId = null) {
    const res = await this._json('/api/link/unpair', {
      method: 'POST',
      body: JSON.stringify(deviceId ? { device_id: deviceId } : {})
    });
    try {
      this._bc?.postMessage({ k: 'unpair' });
    } catch (_) {}
    return res;
  }

  /** Hace sonar el teléfono vinculado */
  async ringPhone() {
    return this._json('/api/link/ring', { method: 'POST' });
  }

  /** Activa o desactiva el modo No molestar y lo persiste */
  async setDoNotDisturb(enabled) {
    return this._json('/api/link/dnd', {
      method: 'POST',
      body: JSON.stringify({ enabled: Boolean(enabled) })
    });
  }

  /** Sube y persiste un nuevo fondo de pantalla para la maqueta del teléfono */
  async uploadWallpaper(file) {
    const fd = new FormData();
    fd.append('file', file);
    const res = await fetch(`${this.baseUrl}/api/link/phone_wallpaper`, {
      method: 'POST',
      body: fd
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    if (data.wallpaper_url && data.wallpaper_url.startsWith('/')) {
      data.wallpaper_url = `${this.baseUrl}${data.wallpaper_url}`;
    }
    return data;
  }

  /** Elimina el fondo de pantalla guardado */
  async removeWallpaper() {
    return this._json('/api/link/phone_wallpaper', { method: 'DELETE' });
  }

  /** Abre la carpeta de archivos recibidos en el explorador del sistema */
  async openReceivedFolder() {
    return this._json('/api/link/open-folder', { method: 'POST' });
  }

  /**
   * Envía un archivo real al teléfono con progreso real por bytes (XMLHttpRequest upload.onprogress).
   * @param {File} file
   * @param {(percent: number, loaded: number, total: number) => void} onProgress
   */
  sendFileToPhone(file, onProgress) {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      const fd = new FormData();
      fd.append('file', file);

      xhr.open('POST', `${this.baseUrl}/api/link/upload_to_phone`, true);

      if (xhr.upload && typeof onProgress === 'function') {
        xhr.upload.onprogress = (ev) => {
          if (ev.lengthComputable && ev.total > 0) {
            const pct = Math.min(100, Math.round((ev.loaded / ev.total) * 100));
            onProgress(pct, ev.loaded, ev.total);
          }
        };
      }

      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          if (typeof onProgress === 'function') onProgress(100, file.size || 1, file.size || 1);
          try {
            resolve(JSON.parse(xhr.responseText));
          } catch (_) {
            resolve({ status: 'ok', filename: file.name });
          }
        } else {
          reject(new Error(`Error HTTP ${xhr.status} al enviar archivo`));
        }
      };

      xhr.onerror = () => reject(new Error('Error de red al transferir archivo al teléfono'));
      xhr.send(fd);
    });
  }

  /** Mensajes: obtiene conversaciones reales sincronizadas desde el teléfono */
  async getMessages() {
    return this._json('/api/link/messages');
  }

  /** Mensajes: envía un mensaje real al teléfono */
  async sendMessage({ threadId, recipient, text }) {
    return this._json('/api/link/messages/send', {
      method: 'POST',
      body: JSON.stringify({
        thread_id: String(threadId),
        recipient: recipient || String(threadId),
        text: String(text)
      })
    });
  }

  /** Mensajes: marca una conversación como leída */
  async markThreadRead(threadId) {
    return this._json('/api/link/messages/read', {
      method: 'POST',
      body: JSON.stringify({ thread_id: String(threadId) })
    });
  }

  /** Llamadas: obtiene historial de llamadas recientes y estado de llamada activa */
  async getCalls() {
    return this._json('/api/link/calls');
  }

  /** Llamadas: inicia una llamada hacia el número indicado */
  async dialCall(number) {
    return this._json('/api/link/calls/dial', {
      method: 'POST',
      body: JSON.stringify({ number: String(number) })
    });
  }

  /** Llamadas: ejecuta acción en llamada activa (hangup, mute, speaker, answer, reject) */
  async callAction(action, value = null) {
    return this._json('/api/link/calls/action', {
      method: 'POST',
      body: JSON.stringify({ action, value })
    });
  }

  /** Fotos: obtiene cuadrícula de fotos reales recibidas del teléfono */
  async getPhotos() {
    const data = await this._json('/api/link/photos');
    if (Array.isArray(data.photos)) {
      data.photos = data.photos.map((p) => ({
        ...p,
        fullUrl: p.url?.startsWith('http') ? p.url : `${this.baseUrl}${p.url}`
      }));
    }
    return data;
  }

  /** Fotos: guarda una foto recibida en la carpeta Imágenes/Miku-Link de la PC */
  async savePhotoToPc(filename) {
    return this._json(`/api/link/photos/save/${encodeURIComponent(filename)}`, {
      method: 'POST'
    });
  }

  /** Avisos: obtiene notificaciones reales del teléfono */
  async getNotifications() {
    return this._json('/api/link/notifications');
  }

  /** Avisos: descarta una notificación individual */
  async dismissNotification(notifId) {
    return this._json(`/api/link/notifications/${encodeURIComponent(notifId)}`, {
      method: 'DELETE'
    });
  }

  /** Avisos: descarta todas las notificaciones */
  async clearNotifications() {
    return this._json('/api/link/notifications', {
      method: 'DELETE'
    });
  }

  /** Apps: obtiene lista de apps del teléfono y estado de espejo */
  async getApps() {
    return this._json('/api/link/apps');
  }

  /** Apps: solicita abrir/transmitir una app del teléfono */
  async openApp(appId, name) {
    return this._json('/api/link/apps/open', {
      method: 'POST',
      body: JSON.stringify({ app_id: String(appId), name: name || String(appId) })
    });
  }

  /** Apps: cierra la app transmitida actualmente */
  async closeApp() {
    return this._json('/api/link/apps/close', { method: 'POST' });
  }

  /** Apps: solicita una captura de pantalla de la app transmitida */
  async captureAppScreenshot() {
    return this._json('/api/link/apps/screenshot', { method: 'POST' });
  }
}

export const mikuLinkTransport = new LinkTransport();

if (typeof window !== 'undefined') {
  window.MikuLinkTransport = mikuLinkTransport;
}

