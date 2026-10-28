/**
 * Miku Design System — Diccionario de textos i18n (Español)
 * Regla §9: Todo texto visible en componentes y vistas sale de este módulo.
 */

export const ES = Object.freeze({
  app: Object.freeze({
    suiteTag: 'MIKU DESKTOP SUITE',
    windowTitle: 'Configuración · Miku',
    statusReady: 'Listo',
    close: 'Cerrar',
    minimize: 'Minimizar',
    cancel: 'Cancelar',
    confirm: 'Confirmar',
    retry: 'Reintentar',
    retrying: 'Reintentando',
    copy: 'Copiar',
    save: 'Guardar',
    saved: 'Cambios guardados',
    savedSub: 'Se aplicaron al instante',
    delete: 'Eliminar',
    loading: 'Cargando…',
    searchEmptyTitle: 'Sin resultados',
    searchEmptyDesc: 'Prueba con otro nombre.'
  }),
  nav: Object.freeze({
    groups: Object.freeze({
      base: 'BASE',
      inteligencia: 'INTELIGENCIA',
      asistencia: 'ASISTENCIA'
    }),
    sections: Object.freeze({
      general: 'General',
      agentes: 'Agentes',
      modelos: 'Modelos de IA',
      keys: 'Claves de API',
      mcp: 'Servidores MCP',
      alertas: 'Notificaciones y Juegos',
      voz: 'Sonido y voz',
      link: 'Miku-Link',
      peligro: 'Zona de peligro'
    })
  }),
  headers: Object.freeze({
    general: Object.freeze({
      title: 'Ajustes generales',
      desc: 'Inicio, Isla Dinámica, permisos del equipo y actualizaciones de Miku.'
    }),
    agentes: Object.freeze({
      title: 'Agentes Autónomos',
      desc: 'Configura agentes especializados, personalidades, herramientas MCP y presencia en la isla.'
    }),
    modelos: Object.freeze({
      title: 'Modelos de Lenguaje & Visión',
      desc: 'Asigna el cerebro para chat, programación, visión de PC y transcripción de voz.'
    }),
    keys: Object.freeze({
      title: 'Claves de API',
      desc: 'Credenciales locales para conectar a Miku con tus proveedores de IA.'
    }),
    mcp: Object.freeze({
      title: 'Servidores MCP',
      desc: 'Extiende las habilidades del agente con servidores Model Context Protocol.'
    }),
    alertas: Object.freeze({
      title: 'Notificaciones y Juegos',
      desc: 'Supervisión de sesiones de juego, enfoque saludable y alertas en tiempo real.'
    }),
    voz: Object.freeze({
      title: 'Sonido y voz',
      desc: 'Síntesis vocal, volumen de alertas, micrófono e interrupción por voz.'
    }),
    link: Object.freeze({
      title: 'Miku-Link',
      desc: 'Usa tu teléfono desde Miku: mensajes, llamadas, fotos, avisos y apps.'
    }),
    peligro: Object.freeze({
      title: 'Zona de peligro',
      desc: 'Acciones destructivas que restablecen ajustes o borran la memoria local.'
    })
  }),
  hold: Object.freeze({
    saveRest: 'Mantén para guardar',
    saveHold: 'Guardando',
    saveDone: 'Guardado',
    confirmRest: 'Mantén para confirmar',
    confirmHold: 'Confirmando',
    confirmDone: 'Confirmado',
    deleteRest: 'Mantén para eliminar',
    deleteHold: 'Sigue manteniendo',
    deleteDone: 'Eliminado',
    resetRest: 'Mantén para restablecer',
    resetHold: 'Sigue manteniendo',
    resetDone: 'Restablecido',
    unlinkRest: 'Mantén para desvincular',
    unlinkHold: 'Sigue manteniendo',
    unlinkDone: 'Desvinculado'
  }),
  mikuLink: Object.freeze({
    unpairedTitle: 'Vincula tu teléfono',
    unpairedDesc: 'Funciona como Phone Link: mensajes, llamadas, fotos, avisos y apps de tu teléfono, aquí.',
    step1: 'Abre Miku en tu teléfono',
    step2: 'Ve a Ajustes › Vincular computadora',
    step3: 'Escanea el código o escribe este PIN',
    expiresIn: 'Expira en {time}',
    codeRenewed: 'Código renovado',
    pinCopied: 'PIN copiado',
    pairingTitle: 'Vinculando tu teléfono',
    pairingDesc: 'Confirma en el teléfono para terminar.',
    connectedSub: 'Conectado por Wi‑Fi · Miku-Link',
    tabs: Object.freeze({
      home: 'Inicio',
      messages: 'Mensajes',
      calls: 'Llamadas',
      photos: 'Fotos',
      notices: 'Avisos',
      apps: 'Apps'
    }),
    phoneNoImage: 'Sin imagen',
    changeWallpaper: 'Cambiar fondo',
    removeWallpaper: 'Quitar fondo',
    ringPhone: 'Hacer sonar',
    ringingToast: 'Sonando teléfono…',
    ringingSub: 'Se detiene al tocar la pantalla',
    dndTitle: 'No molestar',
    dndDesc: 'Silencia los avisos del teléfono.',
    dropFilesPrompt: 'Arrastra archivos para enviarlos al teléfono',
    capabilityUnavailableTitle: 'No disponible en el dispositivo',
    capabilityUnavailableDesc: 'Tu teléfono está conectado para archivos, portapapeles y control de PC, pero aún no transmite esta sección.'
  })
});

export function t(path, params = {}) {
  const parts = String(path).split('.');
  let cur = ES;
  for (const p of parts) {
    if (cur && typeof cur === 'object' && p in cur) {
      cur = cur[p];
    } else {
      return path;
    }
  }
  if (typeof cur !== 'string') return path;
  return cur.replace(/\{(\w+)\}/g, (_, k) => (k in params ? String(params[k]) : `{${k}}`));
}

if (typeof window !== 'undefined') {
  window.MikuI18n = { ES, t };
}

