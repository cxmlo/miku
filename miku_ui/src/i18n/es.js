/**
 * Miku UI — Diccionario Español (es)
 * Fase 2 & 5: Internacionalización centralizada para Configuración y Miku-Link.
 * Ningún componente ni sección debe contener textos hardcodeados fuera de este módulo.
 */

export const es = {
  app: {
    settingsTitle: 'Miku — Configuración',
    searchPlaceholder: 'Buscar ajuste o comando…',
    searchShortcut: 'Ctrl K',
    saveChanges: 'Guardar cambios',
    savedSuccess: 'Ajustes guardados',
    savedSubtitle: 'Sincronizados con el servidor local',
    unsavedWarning: 'Cambios sin guardar',
    loading: 'Cargando…',
    close: 'Cerrar',
    retry: 'Reintentar',
    cancel: 'Cancelar',
  },

  common: {
    copy: 'Copiar',
    cancel: 'Cancelar',
    close: 'Cerrar',
    save: 'Guardar',
    delete: 'Eliminar',
    edit: 'Editar',
    add: 'Añadir',
    refresh: 'Actualizar',
    enabled: 'Activo',
    disabled: 'Inactivo',
  },

  empty: {
    title: 'Todo al día',
    subtitle: 'No tienes notificaciones pendientes',
  },

  nav: {
    general: 'General',
    agentes: 'Agentes',
    modelos: 'Modelos',
    keys: 'Claves',
    mcp: 'Extensiones',
    alertas: 'Alertas',
    voz: 'Voz y audio',
    link: 'Miku-Link',
    peligro: 'Zona de peligro',
  },

  sections: {
    general: {
      tag: 'General',
      title: 'Preferencias del sistema',
      desc: 'Idioma, arranque automático, comportamiento de la isla y atajos globales.',
    },
    agentes: {
      tag: 'Agentes',
      title: 'Especialistas activos',
      desc: 'Asigna roles, herramientas y prioridades de ejecución a cada agente.',
    },
    modelos: {
      tag: 'Modelos',
      title: 'Enrutamiento de modelos',
      desc: 'Elige qué proveedor responde en conversación, código, visión y voz.',
    },
    keys: {
      tag: 'Claves',
      title: 'Credenciales de proveedores',
      desc: 'Almacenadas localmente en tu llavero del sistema; nunca salen de tu equipo.',
    },
    mcp: {
      tag: 'Extensiones',
      title: 'Servidores MCP conectados',
      desc: 'Conecta herramientas externas: archivos, navegador, terminal y calendario.',
    },
    alertas: {
      tag: 'Alertas',
      title: 'Avisos y recordatorios',
      desc: 'Controla qué eventos pueden interrumpirte y con qué prioridad.',
    },
    voz: {
      tag: 'Voz y audio',
      title: 'Síntesis y micrófono',
      desc: 'Timbre de voz, velocidad de lectura, detección de activación y dispositivo de entrada.',
    },
    link: {
      tag: 'Miku-Link',
      title: 'Teléfono vinculado',
      desc: 'Notificaciones, mensajes, llamadas, fotos y archivos entre tu móvil y el escritorio.',
    },
    peligro: {
      tag: 'Zona de peligro',
      title: 'Restablecer y borrar datos',
      desc: 'Acciones irreversibles: requieren mantener pulsado para confirmar.',
    },
  },

  hold: {
    idle: 'Mantén para confirmar',
    holding: 'Manteniendo…',
    done: 'Confirmado',
    confirmRest: 'Mantén para confirmar',
    confirmHold: 'Manteniendo…',
    confirmDone: 'Confirmado',
    deleteRest: 'Mantén para borrar',
    deleteHold: 'Borrando…',
    deleteDone: 'Borrado',
    unpairIdle: 'Mantén para desvincular',
    unpairHolding: 'Desvinculando…',
    unpairDone: 'Desvinculado',
    resetIdle: 'Mantén para restablecer',
    resetHolding: 'Restableciendo…',
    resetDone: 'Restablecido',
  },

  qr: {
    expiresIn: 'Expira en',
    renewed: 'Código renovado',
    copied: 'Código copiado',
    copyBtn: 'Copiar',
    newCodeBtn: 'Nuevo código',
    simulateScanBtn: 'Simular escaneo',
  },

  phone: {
    noWallpaper: 'Sin fondo de pantalla',
    changeWallpaper: 'Cambiar fondo',
    removeWallpaper: 'Quitar fondo',
    ringPhone: 'Hacer sonar',
    ringingToast: 'Haciendo sonar tu teléfono…',
    ringingSub: 'Sonará incluso en modo silencio',
    wallpaperUpdated: 'Fondo actualizado',
    wallpaperRemoved: 'Fondo eliminado',
  },

  mikuLink: {
    // Claves planas de compatibilidad para componentes primitivos (qrPhone.js)
    phoneNoImage: 'Sin imagen',
    unpairedTitle: 'Ningún dispositivo vinculado',
    unpairedDesc:
      'Escanea el código desde la app Miku-Link en tu teléfono o introduce el código de 6 dígitos.',
    step1: 'Abre Miku-Link en tu teléfono',
    step2: 'Toca Vincular con escritorio',
    step3: 'Apunta la cámara al código o escribe los 6 dígitos',
    linkingTitle: 'Confirmando en tu teléfono…',
    linkingDesc:
      'Toca Permitir en la pantalla de tu dispositivo para completar la vinculación.',
    cancelBtn: 'Cancelar',
    connectedBadge: 'Conectado',
    syncRealtime: 'Sincronizado en tiempo real por Wi-Fi local',
    linkedToast: 'Teléfono vinculado',
    linkedSub: 'Sincronización activa',
    unlinkedToast: 'Teléfono desvinculado',
    dndLabel: 'No molestar en el teléfono',
    dndDesc: 'Silenciar avisos entrantes mientras trabajas',
    dropzoneHint:
      'Soltar archivos aquí para enviarlos al teléfono — o clic para elegir',
    receivedToday: 'Recibidas hoy',
    clearAll: 'Borrar todo',
    allCaughtUp: 'Todo al día',
    noPendingNotifs: 'No tienes notificaciones pendientes',
    notifsClearedToast: 'Notificaciones borradas',
    replySentToast: 'Respuesta enviada',

    // Claves estructuradas por sub-vista (mikuLinkSection.js)
    unpaired: {
      title: 'Ningún dispositivo vinculado',
      subtitle:
        'Escanea el código desde la app Miku-Link en tu teléfono o introduce el código de 6 dígitos.',
      step1: 'Abre Miku-Link en tu teléfono',
      step2: 'Toca Vincular con escritorio',
      step3: 'Apunta la cámara al código o escribe los 6 dígitos',
      expiresIn: 'Expira en',
      codeRenewed: 'Código renovado',
      pinCopied: 'Código copiado',
    },
    linking: {
      title: 'Confirmando en tu teléfono…',
      subtitle:
        'Toca Permitir en la pantalla de tu dispositivo para completar la vinculación.',
      connectedToast: 'Teléfono vinculado',
      connectedSub: 'Sincronización activa',
    },
    connected: {
      defaultName: 'Teléfono vinculado',
      subtitle: 'Sincronizado en tiempo real por Wi-Fi local',
    },
    tabs: {
      home: 'Inicio',
      messages: 'Mensajes',
      calls: 'Llamadas',
      photos: 'Fotos',
      notifications: 'Notificaciones',
      apps: 'Apps',
    },
    home: {
      changeWallpaper: 'Cambiar fondo',
      removeWallpaper: 'Quitar fondo',
      ringPhone: 'Hacer sonar',
      ringingToast: 'Haciendo sonar tu teléfono…',
      ringingSub: 'Sonará incluso en modo silencio',
      wallpaperRemoved: 'Fondo eliminado',
      wallpaperUpdated: 'Fondo actualizado',
      dndTitle: 'No molestar en el teléfono',
      dndDesc: 'Silenciar avisos entrantes mientras trabajas',
      dropzoneText:
        'Soltar archivos aquí para enviarlos al teléfono — o clic para elegir',
      unpairIdle: 'Mantén para desvincular',
      unpairHold: 'Desvinculando…',
      unpairDone: 'Desvinculado',
    },
    messages: {
      threadsTitle: 'Conversaciones',
      emptyThreads: 'Sin mensajes recientes',
      emptyThreadsSub:
        'Los SMS recibidos en tu teléfono vinculado aparecerán aquí en tiempo real.',
      emptyChat: 'Aún no hay mensajes en esta conversación.',
      inputLabel: 'Escribir mensaje…',
      send: 'Enviar',
      sentToast: 'Mensaje enviado',
    },
    calls: {
      activeCall: 'Llamada en curso',
      dialing: 'Llamando…',
      mute: 'Silenciar',
      unmute: 'Activar voz',
      speaker: 'Altavoz',
      hangup: 'Colgar',
      endedToast: 'Llamada finalizada',
      numberLabel: 'Número o contacto',
      callBtn: 'Llamar',
      recentTitle: 'Recientes',
      emptyRecent: 'Sin llamadas recientes',
    },
    photos: {
      title: 'Fotos recientes del teléfono',
      openFolder: 'Abrir carpeta',
      emptyTitle: 'Sin fotos recibidas',
      emptySub:
        'Comparte fotos desde la app Miku-Link de tu teléfono y aparecerán aquí al instante.',
      copyToast: 'Foto copiada al portapapeles',
      savedToast: 'Guardada en Imágenes',
    },
    notifications: {
      title: 'Recibidas hoy',
      clearAll: 'Borrar todo',
      clearedToast: 'Notificaciones borradas',
      emptyTitle: 'Todo al día',
      emptySub: 'No tienes notificaciones pendientes',
    },
    apps: {
      streamNote: 'Transmisión de pantalla desde el dispositivo vinculado',
      screenshot: 'Capturar',
      screenshotToast: 'Captura guardada',
      close: 'Cerrar app',
      title: 'Aplicaciones del teléfono',
      emptyTitle: 'Sin aplicaciones transmitidas',
      emptySub:
        'Las aplicaciones disponibles de tu teléfono aparecerán aquí al conectar Miku-Link.',
    },
  },
};

/**
 * Obtiene una cadena localizada por ruta con puntos (ej: t('sections.link.title'))
 * @param {string} keyPath
 * @param {string} [fallback]
 * @returns {string}
 */
export function t(keyPath, fallback = '') {
  if (!keyPath || typeof keyPath !== 'string') return fallback;
  const parts = keyPath.split('.');
  let current = es;
  for (const part of parts) {
    if (current && typeof current === 'object' && part in current) {
      current = current[part];
    } else {
      return fallback || keyPath;
    }
  }
  return typeof current === 'string' ? current : fallback || keyPath;
}

if (typeof window !== 'undefined') {
  window.MikuI18n = { es, t };
}
