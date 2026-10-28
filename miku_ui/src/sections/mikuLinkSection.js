/**
 * Miku-Link Section Controller (Fase 5 — Miku-Link dentro de Configuración)
 * Replica la experiencia visual y de movimiento de miku-catalogo.html (Phone Link)
 * conectada 100 % a LinkTransport (mikuLinkService.js) sin datos falsos ni setTimeout de simulación.
 */

import { mikuLinkTransport } from '../services/mikuLinkService.js';
import { renderQrSvg, renderPhoneMockup } from '../components/qrPhone.js';
import { escapeHtml, mountHoldButton, mountGroup } from '../components/primitives.js';
import { renderEmptyState, renderErrorState, arcLoader } from '../components/feedback.js';
import { icon } from '../design/icons.js';
import { enter, collapseOut } from '../design/motion.js';
import { t } from '../i18n/es.js';

function pad2(n) {
  return n < 10 ? '0' + n : String(n);
}

function formatNowHm() {
  const d = new Date();
  return pad2(d.getHours()) + ':' + pad2(d.getMinutes());
}

export const ML_STATE = {
  view: 'off', // 'off' | 'linking' | 'error' | 'on'
  errorMsg: '',
  tab: 0, // 0: Inicio, 1: Mensajes, 2: Llamadas, 3: Fotos, 4: Avisos, 5: Apps
  connected: false,
  hasPairedDevice: false,
  deviceName: 'Mi teléfono',
  ip: '127.0.0.1',
  tunnelUrl: '',
  hostname: '',
  battery: null,
  charging: false,
  signal: 'Wi‑Fi',
  dnd: false,
  wallpaperUrl: null,
  qr: {
    url: '',
    pin: '--- ---',
    issuedAt: 0,
    expiresAt: 0,
    ttlSeconds: 120,
    serverOffsetSec: 0
  },
  threads: [],
  selectedThreadIdx: 0,
  msgSearch: '',
  calls: [],
  activeCall: null,
  dialNumber: '',
  photos: [],
  selectedPhoto: null,
  notifications: [],
  apps: [],
  activeApp: null,
  _qrTimer: null,
  _clkTimer: null,
  _callTimer: null,
  _pollTimer: null,
  _unsubTransport: null
};

function notifyToast(title, variant = 'n', sub = '') {
  if (window.MikuComponents?.toast?.show) {
    window.MikuComponents.toast.show(title, variant, sub);
  }
}

export function stopMikuLinkTimers() {
  if (ML_STATE._qrTimer) {
    clearInterval(ML_STATE._qrTimer);
    ML_STATE._qrTimer = null;
  }
  if (ML_STATE._clkTimer) {
    clearInterval(ML_STATE._clkTimer);
    ML_STATE._clkTimer = null;
  }
  if (ML_STATE._callTimer) {
    clearInterval(ML_STATE._callTimer);
    ML_STATE._callTimer = null;
  }
  if (ML_STATE._pollTimer) {
    clearInterval(ML_STATE._pollTimer);
    ML_STATE._pollTimer = null;
  }
}

function updateClockDom(root) {
  const scope = root || document;
  const now = new Date();
  const hm = formatNowHm();
  scope.querySelectorAll('.pt, .pclk').forEach((el) => {
    el.textContent = hm;
  });
  const dateStr = now.toLocaleDateString('es', {
    weekday: 'long',
    day: 'numeric',
    month: 'long'
  });
  scope.querySelectorAll('.pdt').forEach((el) => {
    el.textContent = dateStr;
  });
}

function renderPhoneNotifCard(n) {
  const appName = n.app || n.title || 'Aviso';
  const text = n.text || n.body || '';
  const initial = (appName[0] || 'A').toUpperCase();
  return (
    `<div class="pn" data-id="${escapeHtml(n.id)}">` +
      `<span class="ai">${escapeHtml(initial)}</span>` +
      `<div><b>${escapeHtml(appName)}</b><br>${escapeHtml(text)}</div>` +
    `</div>`
  );
}

function renderNotifListItem(n) {
  const appName = n.app || n.title || 'Aviso';
  const text = n.text || n.body || '';
  const initial = (appName[0] || 'A').toUpperCase();
  return (
    `<div class="tw in" data-id="${escapeHtml(n.id)}">` +
      `<div>` +
        `<div class="ni">` +
          `<span class="ai">${escapeHtml(initial)}</span>` +
          `<div><b>${escapeHtml(appName)}</b><small class="mu" style="display:block">${escapeHtml(text)}</small></div>` +
          `<button class="btn i q" data-a="rm-notif" data-id="${escapeHtml(n.id)}" aria-label="${escapeHtml(t('mikuLink.notifications.dismissAria'))}" style="margin-left:auto;width:28px;height:28px">${icon('x')}</button>` +
        `</div>` +
      `</div>` +
    `</div>`
  );
}

function renderOffView() {
  const qrHtml = ML_STATE.qr.url
    ? renderQrSvg(ML_STATE.qr.url)
    : `<div style="padding:40px 10px;display:grid;place-items:center">${arcLoader()}</div>`;

  const pairedBanner = ML_STATE.hasPairedDevice
    ? `<div class="al ok" style="margin-bottom:14px">` +
        `${icon('phone')}` +
        `<div style="flex:1"><b>${escapeHtml(ML_STATE.deviceName)}</b> está registrado en este equipo. Abre la app móvil en la misma red Wi‑Fi (${escapeHtml(ML_STATE.ip)}) o abre el panel del dispositivo.</div>` +
        `<button class="btn sm p" data-a="open-registered">Abrir panel</button>` +
      `</div>`
    : '';

  return (
    `${pairedBanner}` +
    `<div class="two">` +
      `<div>` +
        `<div class="qr" id="qr" style="margin:0 auto">${qrHtml}</div>` +
        `<div class="bar sm" style="margin:14px auto 0;max-width:208px"><i id="qb" style="width:100%"></i></div>` +
        `<p class="cap" style="text-align:center" id="qt">Expira en 2:00</p>` +
      `</div>` +
      `<div class="col">` +
        `<div>` +
          `<b style="font-size:17px">${escapeHtml(t('mikuLink.unpaired.title'))}</b>` +
          `<p class="mu" style="margin:4px 0 0">${escapeHtml(t('mikuLink.unpaired.subtitle'))}</p>` +
        `</div>` +
        `<div class="col" style="gap:10px">` +
          `<div class="stl"><span class="ai">1</span>${escapeHtml(t('mikuLink.unpaired.step1'))}</div>` +
          `<div class="stl"><span class="ai">2</span>${escapeHtml(t('mikuLink.unpaired.step2'))}</div>` +
          `<div class="stl"><span class="ai">3</span>${escapeHtml(t('mikuLink.unpaired.step3'))}</div>` +
        `</div>` +
        `<div class="row">` +
          `<span class="cd" id="qcode">${escapeHtml(ML_STATE.qr.pin)}</span>` +
          `<button class="btn sm" data-a="copy">${escapeHtml(t('common.copy'))}</button>` +
          `<button class="btn sm q" data-a="refresh-qr">Renovar QR</button>` +
        `</div>` +
        `<div class="row" style="gap:8px;flex-wrap:wrap">` +
          `<span class="chip"><i class="dt"></i>Wi‑Fi local: ${escapeHtml(ML_STATE.ip)}:8000</span>` +
          (ML_STATE.tunnelUrl
            ? `<span class="chip g" title="${escapeHtml(ML_STATE.tunnelUrl)}"><i class="dt"></i>Túnel Datos Móviles (4G/5G): Activo</span>`
            : `<span class="chip" title="Instala cloudflared o define MIKU_TUNNEL_URL en .env para conectar fuera de casa">Túnel remoto: Wi‑Fi local</span>`) +
          `<button class="btn q sm" data-a="check-pair">Comprobar vinculación</button>` +
        `</div>` +
      `</div>` +
    `</div>`
  );
}

function renderLinkingView() {
  const phoneIconLg = icon('phone').replace('class="ic"', 'class="ic" style="width:30px;height:30px"');
  return (
    `<div style="text-align:center;padding:18px 0">` +
      `<div class="pr"><i></i><i></i><i></i>${phoneIconLg}</div>` +
      `<div class="row" style="justify-content:center;margin-top:10px">` +
        `<div class="wv"><i></i><i></i><i></i></div>` +
        `<b>${escapeHtml(t('mikuLink.linking.title'))}</b>` +
      `</div>` +
      `<p class="mu" style="margin:4px 0 14px">${escapeHtml(t('mikuLink.linking.subtitle'))}</p>` +
      `<button class="btn q" data-a="cancel">${escapeHtml(t('common.cancel'))}</button>` +
    `</div>`
  );
}

function renderErrorView() {
  return renderErrorState({
    title: 'No se pudo completar la vinculación',
    desc: ML_STATE.errorMsg || 'El código expiró o el teléfono canceló la solicitud.',
    retryAction: 'retry-pair'
  });
}

function renderConnectedView() {
  const tabs = [
    t('mikuLink.tabs.home'),
    t('mikuLink.tabs.messages'),
    t('mikuLink.tabs.calls'),
    t('mikuLink.tabs.photos'),
    t('mikuLink.tabs.notifications'),
    t('mikuLink.tabs.apps')
  ];
  const hasBat = typeof ML_STATE.battery === 'number' && ML_STATE.battery >= 0;
  const batPct = hasBat ? Math.min(100, Math.max(0, ML_STATE.battery)) : 100;
  const batLabel = hasBat
    ? `${batPct}%${ML_STATE.charging ? ' · Cargando' : ''}`
    : (ML_STATE.connected ? 'En línea' : 'Registrado');
  const connSubtitle = ML_STATE.connected
    ? `${t('mikuLink.connected.subtitle')} (${ML_STATE.tunnelUrl ? 'Wi‑Fi + Túnel 4G/5G' : ML_STATE.ip})`
    : `Dispositivo vinculado · Esperando conexión (${ML_STATE.ip}:8000${ML_STATE.tunnelUrl ? ' / Túnel activo' : ''})`;

  return (
    `<div class="mlh">` +
      `<span class="av ${ML_STATE.connected ? 'on' : ''}">${icon('phone')}</span>` +
      `<div>` +
        `<b>${escapeHtml(ML_STATE.deviceName || t('mikuLink.connected.defaultName'))}</b>` +
        `<span class="mu">${escapeHtml(connSubtitle)}</span>` +
      `</div>` +
      `<span class="batt"><i style="--b:${batPct}%"></i>${escapeHtml(batLabel)}</span>` +
    `</div>` +
    `<div class="tabs" id="mlt">` +
      tabs.map((label, idx) => `<button type="button" aria-pressed="${idx === ML_STATE.tab}">${escapeHtml(label)}</button>`).join('') +
    `</div>` +
    `<div id="mlp" style="padding-top:16px"></div>`
  );
}

function renderTabHome() {
  const hasBat = typeof ML_STATE.battery === 'number' && ML_STATE.battery >= 0;
  const sbRight = hasBat ? `${ML_STATE.battery}%` : (ML_STATE.connected ? (ML_STATE.signal || 'Wi‑Fi') : 'Offline');
  const innerPhone =
    `<div class="sb"><span class="pt">${formatNowHm()}</span><span>${escapeHtml(sbRight)}</span></div>` +
    `<div class="cl"><b class="pclk">${formatNowHm()}</b><span class="pdt"></span></div>` +
    `<div class="nts" id="pnts">${ML_STATE.notifications.slice(-2).map(renderPhoneNotifCard).join('')}</div>`;

  return (
    `<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,200px),1fr));gap:20px;align-items:start">` +
      `<div style="display:flex;justify-content:center">` +
        renderPhoneMockup({
          id: 'ph',
          wallpaperUrl: ML_STATE.wallpaperUrl,
          innerHtml: innerPhone
        }) +
      `</div>` +
      `<div class="col" style="grid-column:span 2;min-width:260px">` +
        `<div class="row" style="gap:8px">` +
          `<button type="button" class="btn sm" data-a="wp">${escapeHtml(t('mikuLink.home.changeWallpaper'))}</button>` +
          `<button type="button" class="btn sm q" data-a="wpx">${escapeHtml(t('mikuLink.home.removeWallpaper'))}</button>` +
          `<button type="button" class="btn sm" data-a="ring">${escapeHtml(t('mikuLink.home.ringPhone'))}</button>` +
          `<button type="button" class="btn sm q" data-a="open-folder">Recibidos</button>` +
          `<input type="file" id="wpf" accept="image/*" hidden>` +
        `</div>` +
        `<div class="line" style="padding:10px 0;border-top:1px solid var(--ln);border-bottom:1px solid var(--ln)">` +
          `<div>` +
            `<b style="display:block;font-size:13.5px;color:var(--tx)">${escapeHtml(t('mikuLink.home.dndTitle'))}</b>` +
            `<span class="d" style="display:block;font-size:12px;color:var(--mu);margin-top:2px">${escapeHtml(t('mikuLink.home.dndDesc'))}</span>` +
          `</div>` +
          `<button type="button" class="tg" id="dnd" role="switch" data-a="dnd" aria-checked="${ML_STATE.dnd ? 'true' : 'false'}" aria-label="${escapeHtml(t('mikuLink.home.dndTitle'))}"></button>` +
        `</div>` +
        `<div class="dz" id="ml-dropzone" tabindex="0">` +
          `<input type="file" id="ml-file-input" multiple hidden>` +
          `<div>${escapeHtml(t('mikuLink.home.dropzoneText'))}</div>` +
          `<div class="fl" id="ml-file-list"></div>` +
        `</div>` +
        `<div style="display:flex;align-items:center;justify-content:space-between;gap:12px;padding-top:4px;flex-wrap:wrap">` +
          `<button type="button" class="hb r sm" id="unl" data-r="${escapeHtml(t('mikuLink.home.unpairIdle'))}" data-h="${escapeHtml(t('mikuLink.home.unpairHold'))}" data-d="${escapeHtml(t('mikuLink.home.unpairDone'))}"></button>` +
          `<button type="button" class="btn q sm" data-a="lock-pc">Bloquear PC ahora</button>` +
        `</div>` +
      `</div>` +
    `</div>`
  );
}

function renderMessageBubble(m) {
  const isOut = m.dir === 'out' || m[0] === 'o';
  const text = m.text ?? m[1] ?? '';
  const time = m.time ?? m[2] ?? '';
  const status = m.status ?? m[3] ?? '';
  return (
    `<div class="bb${isOut ? ' o' : ''}">` +
      `${escapeHtml(text)}` +
      `<small>${escapeHtml(time)}${status ? ' · ' + escapeHtml(status) : ''}</small>` +
    `</div>`
  );
}

function renderTabMessages() {
  const q = (ML_STATE.msgSearch || '').trim().toLowerCase();
  const threads = ML_STATE.threads.filter((th) => {
    if (!q) return true;
    return (th.name || '').toLowerCase().includes(q);
  });

  if (!ML_STATE.threads.length) {
    return (
      `<div class="col" style="gap:12px">` +
        renderEmptyState({
          iconName: 'msg',
          title: 'Sin mensajes sincronizados',
          subtitle: 'Cuando el teléfono envíe conversaciones o recibas SMS por Miku-Link, aparecerán aquí. También puedes iniciar un mensaje nuevo hacia el teléfono.'
        }) +
        `<div class="row" style="justify-content:center">` +
          `<input class="tx-in" id="ml-new-recipient" type="text" placeholder="Nombre o número de destino…" style="max-width:220px;height:36px">` +
          `<input class="tx-in" id="ml-new-msg-text" type="text" placeholder="Escribe un mensaje…" style="flex:1;max-width:300px;height:36px">` +
          `<button type="button" class="btn p" data-a="send-new-thread">${icon('send')}Enviar</button>` +
        `</div>` +
      `</div>`
    );
  }

  const selIdx = Math.min(ML_STATE.selectedThreadIdx, Math.max(0, threads.length - 1));
  const activeThread = threads[selIdx] || threads[0];
  const msgs = activeThread?.messages || activeThread?.m || [];

  return (
    `<div class="msg">` +
      `<div class="ctl">` +
        `<div style="padding:0 4px 6px">` +
          `<input class="tx-in" id="ml-msg-search" type="text" value="${escapeHtml(ML_STATE.msgSearch)}" placeholder="Buscar conversación…" style="width:100%;height:32px;font-size:12px">` +
        `</div>` +
        threads.map((c, i) => {
          const listMsgs = c.messages || c.m || [];
          const last = listMsgs[listMsgs.length - 1];
          const lastText = last ? (last.text ?? last[1] ?? '') : 'Sin mensajes';
          const unread = c.unread ?? c.u ?? 0;
          const name = c.name || c.n || 'Contacto';
          return (
            `<button type="button" class="ct" data-a="th" data-i="${i}" aria-pressed="${i === selIdx}">` +
              `<span class="av">${escapeHtml((name[0] || '?').toUpperCase())}</span>` +
              `<div><b>${escapeHtml(name)}</b><small>${escapeHtml(lastText)}</small></div>` +
              `${unread ? `<span class="bdg">${escapeHtml(unread)}</span>` : ''}` +
            `</button>`
          );
        }).join('') +
      `</div>` +
      `<div class="thr">` +
        `<div class="thh">${escapeHtml(activeThread?.name || activeThread?.n || '')}</div>` +
        `<div class="bbs" id="bbs">${msgs.map(renderMessageBubble).join('')}</div>` +
        `<div class="cmp">` +
          `<input id="cin" placeholder="${escapeHtml(t('mikuLink.messages.placeholder'))}" autocomplete="off" aria-label="${escapeHtml(t('mikuLink.messages.ariaInput'))}">` +
          `<button type="button" class="btn p i" data-a="send" aria-label="${escapeHtml(t('mikuLink.messages.sendAria'))}">${icon('send')}</button>` +
        `</div>` +
      `</div>` +
    `</div>`
  );
}

function renderTabCalls() {
  if (ML_STATE.activeCall) {
    const c = ML_STATE.activeCall;
    const contactName = c.name || c.number || 'Llamada';
    const initial = (contactName[0] || '#').toUpperCase();
    const isDialing = c.state === 'dialing';
    const elapsed = Math.max(0, Math.floor(Date.now() / 1000) - (c.started_at || Math.floor(Date.now() / 1000)));
    const timerStr = isDialing ? t('mikuLink.calls.calling') : `${pad2(Math.floor(elapsed / 60))}:${pad2(elapsed % 60)}`;
    return (
      `<div class="cll">` +
        (isDialing
          ? `<div class="pr" style="width:96px;height:96px"><i></i><i></i><i></i><span class="av">${escapeHtml(initial)}</span></div>`
          : `<span class="av">${escapeHtml(initial)}</span>`) +
        `<b style="font-size:18px">${escapeHtml(contactName)}</b>` +
        `<span class="mu" id="ctm">${escapeHtml(timerStr)}</span>` +
        `<div class="row" style="justify-content:center">` +
          `<button type="button" class="btn" data-a="mute" aria-pressed="${c.muted ? 'true' : 'false'}">${escapeHtml(t('mikuLink.calls.mute'))}</button>` +
          `<button type="button" class="btn" data-a="spk" aria-pressed="${c.speaker ? 'true' : 'false'}">${escapeHtml(t('mikuLink.calls.speaker'))}</button>` +
          `<button type="button" class="btn r" data-a="hang">${escapeHtml(t('mikuLink.calls.hangup'))}</button>` +
        `</div>` +
      `</div>`
    );
  }

  const keys = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '*', '0', '#'];
  const recentHtml = ML_STATE.calls.length
    ? ML_STATE.calls.map((c, i) => {
        const name = c.name || c.number || c[0] || 'Desconocido';
        const dir = c.dir || c[1] || 'out';
        const time = c.time || c[2] || '';
        const dirLabel = dir === 'in'
          ? t('mikuLink.calls.incoming')
          : dir === 'miss'
          ? t('mikuLink.calls.missed')
          : t('mikuLink.calls.outgoing');
        return (
          `<button type="button" class="ct" data-a="rc" data-i="${i}">` +
            `<span class="av">${escapeHtml((name[0] || '#').toUpperCase())}</span>` +
            `<div>` +
              `<b>${escapeHtml(name)}</b>` +
              `<small${dir === 'miss' ? ' class="er"' : ''}>${escapeHtml(dirLabel)} · ${escapeHtml(time)}</small>` +
            `</div>` +
          `</button>`
        );
      }).join('')
    : `<p class="mu" style="margin-top:8px">Sin llamadas recientes registradas en esta sesión.</p>`;

  return (
    `<div class="two" style="align-items:start">` +
      `<div style="margin:0 auto">` +
        `<div class="num" id="num">${escapeHtml(ML_STATE.dialNumber)}</div>` +
        `<div class="dial">` +
          keys.map((k) => `<button type="button" class="key" data-a="k" data-k="${k}">${k}</button>`).join('') +
        `</div>` +
        `<div class="row" style="margin-top:10px;max-width:240px">` +
          `<button type="button" class="btn g" style="flex:1" data-a="dial">${icon('phone')}${escapeHtml(t('mikuLink.calls.callBtn'))}</button>` +
          `<button type="button" class="btn i q" data-a="del" aria-label="${escapeHtml(t('mikuLink.calls.deleteAria'))}">${icon('back')}</button>` +
        `</div>` +
      `</div>` +
      `<div>` +
        `<b>${escapeHtml(t('mikuLink.calls.recentTitle'))}</b>` +
        `<div class="col" style="gap:4px;margin-top:8px">${recentHtml}</div>` +
      `</div>` +
    `</div>`
  );
}

function renderTabPhotos() {
  if (!ML_STATE.photos.length) {
    return (
      `<div class="col" style="gap:12px">` +
        renderEmptyState({
          iconName: 'img',
          title: 'Sin fotos recibidas aún',
          subtitle: 'Envía fotos o capturas desde Miku en tu teléfono y aparecerán automáticamente en esta galería.'
        }) +
        `<div class="row" style="justify-content:center">` +
          `<button type="button" class="btn sm" data-a="refresh-photos">Actualizar galería</button>` +
          `<button type="button" class="btn sm q" data-a="open-folder">Abrir carpeta Descargas/miku-link</button>` +
        `</div>` +
      `</div>`
    );
  }

  return (
    `<div class="phg">` +
      ML_STATE.photos.map((p, i) => (
        `<button type="button" class="pho" data-a="pho" data-i="${i}" aria-label="${escapeHtml(p.filename)}" style="background-image:url('${escapeHtml(p.fullUrl)}');background-size:cover;background-position:center">` +
          `<span style="background:rgba(0,0,0,.65);padding:3px 8px;border-radius:8px;font-size:11px;max-width:90%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${escapeHtml(p.filename)}</span>` +
        `</button>`
      )).join('') +
    `</div>` +
    `<div class="row" style="justify-content:space-between;margin-top:10px">` +
      `<p class="cap" style="margin:0">${escapeHtml(t('mikuLink.photos.caption'))}</p>` +
      `<button type="button" class="btn sm q" data-a="refresh-photos">Actualizar</button>` +
    `</div>`
  );
}

function renderTabNotifications() {
  const list = ML_STATE.notifications.slice().reverse();
  return (
    `<div class="row" style="justify-content:space-between;margin-bottom:10px">` +
      `<b>${escapeHtml(t('mikuLink.notifications.title'))} (${list.length})</b>` +
      `<div class="row" style="gap:8px">` +
        `<button type="button" class="btn sm q" data-a="refresh-notifs">Actualizar</button>` +
        `<button type="button" class="btn sm" data-a="clr-notifs" ${list.length ? '' : 'disabled'}>${escapeHtml(t('mikuLink.notifications.clear'))}</button>` +
      `</div>` +
    `</div>` +
    `<div id="nl">` +
      (list.length
        ? list.map(renderNotifListItem).join('')
        : renderEmptyState({
            iconName: 'bell',
            title: t('empty.title'),
            subtitle: t('empty.subtitle')
          })) +
    `</div>`
  );
}

function renderTabApps() {
  if (ML_STATE.activeApp) {
    const appName = ML_STATE.activeApp.name || ML_STATE.activeApp.id || 'App';
    const innerScreen =
      `<div class="scr" id="scr" style="align-items:center;justify-content:center">` +
        `<b style="font-size:17px">${escapeHtml(appName)}</b>` +
        `<span class="mu" style="font-size:12px;text-align:center">${escapeHtml(t('mikuLink.apps.streamingFromPhone'))}</span>` +
        `<span style="flex:1"></span>` +
        `<div class="row" style="justify-content:space-around;width:100%">` +
          `<button type="button" class="btn i q sm" data-a="mclose" aria-label="${escapeHtml(t('mikuLink.apps.backAria'))}">${icon('back')}</button>` +
          `<button type="button" class="btn i q sm" data-a="mclose" aria-label="${escapeHtml(t('mikuLink.apps.homeAria'))}">${icon('home')}</button>` +
        `</div>` +
      `</div>`;
    return (
      `<div class="two" style="align-items:start">` +
        renderPhoneMockup({
          id: 'ph-app',
          wallpaperUrl: ML_STATE.wallpaperUrl,
          innerHtml: innerScreen
        }) +
        `<div class="col">` +
          `<div>` +
            `<b style="font-size:16px">${escapeHtml(appName)}</b>` +
            `<span class="mu" style="display:block">${escapeHtml(t('mikuLink.apps.streamingFromPhone'))}</span>` +
          `</div>` +
          `<div class="row">` +
            `<button type="button" class="btn" data-a="shot">${escapeHtml(t('mikuLink.apps.screenshot'))}</button>` +
            `<button type="button" class="btn r" data-a="mclose">${escapeHtml(t('mikuLink.apps.closeApp'))}</button>` +
          `</div>` +
        `</div>` +
      `</div>`
    );
  }

  if (!ML_STATE.apps.length) {
    return (
      `<div class="col" style="gap:12px">` +
        renderEmptyState({
          iconName: 'phone',
          title: 'Lanzador Rápido de Apps del Teléfono',
          subtitle: 'Permite abrir cualquier app instalada en tu teléfono directamente desde tu PC (WhatsApp, Spotify, Cámara, etc.) o pedirle por voz a Miku que la inicie en tu móvil.'
        }) +
        `<div class="row" style="justify-content:center">` +
          `<button type="button" class="btn sm" data-a="refresh-apps">Sincronizar apps del teléfono</button>` +
        `</div>` +
      `</div>`
    );
  }

  return (
    `<div class="apps">` +
      ML_STATE.apps.map((a, i) => {
        const name = typeof a === 'string' ? a : (a.name || a.id || 'App');
        return (
          `<button type="button" class="app" data-a="app" data-i="${i}">` +
            `<span class="ai">${escapeHtml((name[0] || 'A').toUpperCase())}</span>` +
            `${escapeHtml(name)}` +
          `</button>`
        );
      }).join('') +
    `</div>` +
    `<p class="cap">${escapeHtml(t('mikuLink.apps.caption'))}</p>`
  );
}

/** Devuelve el HTML contenedor de la sección Miku-Link para V.link() */
export function renderMikuLinkSectionHtml() {
  return (
    `<section class="card" style="padding:20px">` +
      `<div id="ml"></div>` +
    `</section>` +
    `<div class="ov" id="ml-photo-ov" data-open="false" role="dialog" aria-modal="true" aria-label="Vista previa de foto">` +
      `<div class="md" style="max-width:520px">` +
        `<div class="mh">` +
          `<h3 id="ml-photo-title">Foto</h3>` +
          `<button type="button" class="btn i q sm" data-a="close-photo-modal" aria-label="Cerrar">${icon('x')}</button>` +
        `</div>` +
        `<div style="border-radius:14px;overflow:hidden;background:var(--s2);border:1px solid var(--ln);max-height:360px;display:grid;place-items:center">` +
          `<img id="ml-photo-img" src="" alt="" style="max-width:100%;max-height:360px;object-fit:contain">` +
        `</div>` +
        `<div class="mf">` +
          `<button type="button" class="btn q" data-a="open-folder">Abrir carpeta</button>` +
          `<button type="button" class="btn p" data-a="save-photo">Guardar en Imágenes</button>` +
        `</div>` +
      `</div>` +
    `</div>`
  );
}

function startQrExpirationLoop() {
  if (ML_STATE._qrTimer) clearInterval(ML_STATE._qrTimer);
  const tick = async () => {
    const qrEl = document.getElementById('qr');
    const qtEl = document.getElementById('qt');
    const qbEl = document.getElementById('qb');
    if (!qrEl || ML_STATE.view !== 'off') {
      clearInterval(ML_STATE._qrTimer);
      ML_STATE._qrTimer = null;
      return;
    }
    if (!ML_STATE.qr.expiresAt) return;
    const nowServerSec = Date.now() / 1000 + (ML_STATE.qr.serverOffsetSec || 0);
    const rem = Math.max(0, Math.ceil(ML_STATE.qr.expiresAt - nowServerSec));
    const ttl = Math.max(1, ML_STATE.qr.ttlSeconds || 120);
    if (qtEl) {
      qtEl.textContent = `${t('mikuLink.unpaired.expiresIn')} ${Math.floor(rem / 60)}:${pad2(rem % 60)}`;
    }
    if (qbEl) {
      qbEl.style.width = `${Math.min(100, Math.max(0, (rem / ttl) * 100))}%`;
    }
    if (rem <= 0) {
      await fetchNewQrToken(true, true);
    }
  };
  tick();
  ML_STATE._qrTimer = setInterval(tick, 1000);
}

function applyQrDataToDom(d, announce = false) {
  if (!d || !d.url) return;
  const clientNowSec = Date.now() / 1000;
  ML_STATE.qr.url = d.url || '';
  if (d.pin) ML_STATE.qr.pin = d.pin;
  ML_STATE.qr.issuedAt = d.issued_at || Math.floor(clientNowSec);
  ML_STATE.qr.expiresAt = d.expires_at || Math.floor(clientNowSec) + 120;
  ML_STATE.qr.ttlSeconds = d.ttl_seconds || 120;
  ML_STATE.qr.serverOffsetSec = (d.issued_at || clientNowSec) - clientNowSec;
  if (d.ip) ML_STATE.ip = d.ip;
  if (d.tunnel_url !== undefined) ML_STATE.tunnelUrl = d.tunnel_url || '';

  const qrEl = document.getElementById('qr');
  const pinEl = document.getElementById('qcode');
  if (qrEl) {
    qrEl.innerHTML = renderQrSvg(ML_STATE.qr.url);
    enter(qrEl);
  }
  if (pinEl && ML_STATE.qr.pin) pinEl.textContent = ML_STATE.qr.pin;
  if (announce) notifyToast(t('mikuLink.unpaired.codeRenewed'), 'n');
  startQrExpirationLoop();
}

async function fetchNewQrToken(announce = false, force = false) {
  try {
    const d = await mikuLinkTransport.requestPairingToken(force);
    applyQrDataToDom(d, announce);
  } catch (err) {
    notifyToast('Error al obtener código QR del servidor', 'er', err.message);
  }
}

function mountDropzone(root) {
  const dz = root.querySelector('#ml-dropzone');
  const fileInp = root.querySelector('#ml-file-input');
  const fl = root.querySelector('#ml-file-list');
  if (!dz || !fileInp || !fl) return;

  const uploadFiles = (fileList) => {
    Array.from(fileList || []).forEach((file) => {
      const item = document.createElement('div');
      item.className = 'fi bi';
      const kb = Math.max(1, Math.round((file.size || 1024) / 1024));
      item.innerHTML =
        `<span style="flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;text-align:left">${escapeHtml(file.name)}</span>` +
        `<div class="bar sm" style="max-width:90px"><i style="width:0%"></i></div>` +
        `<span class="mu" data-st>${kb} KB</span>`;
      fl.appendChild(item);
      const barFill = item.querySelector('i');
      const stLabel = item.querySelector('[data-st]');

      mikuLinkTransport
        .sendFileToPhone(file, (pct) => {
          if (barFill) barFill.style.width = `${pct}%`;
        })
        .then(() => {
          if (barFill) {
            barFill.style.width = '100%';
            barFill.style.background = 'var(--ok)';
          }
          if (stLabel) stLabel.textContent = 'Enviado';
          notifyToast(`Archivo '${file.name}' enviado al teléfono`, 'ok');
        })
        .catch((err) => {
          if (barFill) {
            barFill.style.width = '100%';
            barFill.style.background = 'var(--er)';
          }
          if (stLabel) stLabel.textContent = 'Error';
          notifyToast(`No se pudo enviar '${file.name}'`, 'er', err.message);
        });
    });
  };

  dz.addEventListener('click', (e) => {
    if (e.target.tagName !== 'INPUT' && !e.target.closest('.fl')) {
      fileInp.click();
    }
  });
  fileInp.addEventListener('change', () => {
    if (fileInp.files?.length) {
      uploadFiles(fileInp.files);
      fileInp.value = '';
    }
  });
  ['dragenter', 'dragover'].forEach((evName) => {
    dz.addEventListener(evName, (e) => {
      e.preventDefault();
      dz.classList.add('on');
    });
  });
  dz.addEventListener('dragleave', (e) => {
    if (!dz.contains(e.relatedTarget)) dz.classList.remove('on');
  });
  dz.addEventListener('drop', (e) => {
    e.preventDefault();
    dz.classList.remove('on');
    if (e.dataTransfer?.files?.length) {
      uploadFiles(e.dataTransfer.files);
    }
  });
}

function renderActiveTabContent() {
  const mlp = document.getElementById('mlp');
  if (!mlp) return;
  const renderers = [
    renderTabHome,
    renderTabMessages,
    renderTabCalls,
    renderTabPhotos,
    renderTabNotifications,
    renderTabApps
  ];
  const fn = renderers[ML_STATE.tab] || renderTabHome;
  mlp.innerHTML = fn();
  updateClockDom(mlp);

  if (ML_STATE.tab === 0) {
    const unlHost = mlp.querySelector('#unl');
    if (unlHost) {
      mountHoldButton(unlHost, async () => {
        try {
          await mikuLinkTransport.unpairDevice();
          ML_STATE.connected = false;
          ML_STATE.hasPairedDevice = false;
          notifyToast('Teléfono desvinculado', 'ok');
          transitionMikuLinkView('off');
        } catch (err) {
          notifyToast('Error al desvincular', 'er', err.message);
        }
      });
    }
    mountDropzone(mlp);
  }

  if (ML_STATE.tab === 1) {
    const bbs = mlp.querySelector('#bbs');
    if (bbs) bbs.scrollTop = bbs.scrollHeight;
    const searchInp = mlp.querySelector('#ml-msg-search');
    if (searchInp) {
      searchInp.addEventListener('input', () => {
        ML_STATE.msgSearch = searchInp.value;
        renderActiveTabContent();
      });
    }
  }
}

function switchTabWithBlur(nextTabIdx) {
  const mlp = document.getElementById('mlp');
  ML_STATE.tab = nextTabIdx;
  ML_STATE.activeApp = null;
  if (!mlp) return;
  mlp.classList.remove('bi');
  mlp.classList.add('bo');
  setTimeout(() => {
    const cur = document.getElementById('mlp');
    if (!cur) return;
    cur.classList.remove('bo');
    renderActiveTabContent();
    enter(cur);
  }, 190);
}

function renderMikuLinkRoot() {
  const root = document.getElementById('ml');
  if (!root) return;

  if (ML_STATE.view === 'off') {
    root.innerHTML = renderOffView();
    fetchNewQrToken(false);
  } else if (ML_STATE.view === 'linking') {
    root.innerHTML = renderLinkingView();
  } else if (ML_STATE.view === 'error') {
    root.innerHTML = renderErrorView();
  } else {
    root.innerHTML = renderConnectedView();
    const tabsEl = document.getElementById('mlt');
    if (tabsEl) {
      mountGroup(tabsEl, (idx) => {
        switchTabWithBlur(idx);
      });
    }
    renderActiveTabContent();
  }
}

export function transitionMikuLinkView(nextView) {
  const root = document.getElementById('ml');
  if (!root) {
    ML_STATE.view = nextView;
    return;
  }
  if (ML_STATE.view === nextView) {
    renderMikuLinkRoot();
    return;
  }
  root.classList.remove('bi');
  root.classList.add('bo');
  setTimeout(() => {
    ML_STATE.view = nextView;
    const r2 = document.getElementById('ml');
    if (!r2) return;
    if (nextView !== 'off' && ML_STATE._qrTimer) {
      clearInterval(ML_STATE._qrTimer);
      ML_STATE._qrTimer = null;
    }
    r2.classList.remove('bo');
    renderMikuLinkRoot();
    enter(r2);
  }, 190);
}

async function syncAllConnectedData() {
  try {
    const [msgRes, callRes, phoRes, notRes, appRes] = await Promise.all([
      mikuLinkTransport.getMessages().catch(() => null),
      mikuLinkTransport.getCalls().catch(() => null),
      mikuLinkTransport.getPhotos().catch(() => null),
      mikuLinkTransport.getNotifications().catch(() => null),
      mikuLinkTransport.getApps().catch(() => null)
    ]);
    if (msgRes && Array.isArray(msgRes.threads)) ML_STATE.threads = msgRes.threads;
    if (callRes) {
      if (Array.isArray(callRes.recent)) ML_STATE.calls = callRes.recent;
      ML_STATE.activeCall = callRes.active_call || null;
    }
    if (phoRes && Array.isArray(phoRes.photos)) ML_STATE.photos = phoRes.photos;
    if (notRes && Array.isArray(notRes.notifications)) ML_STATE.notifications = notRes.notifications;
    if (appRes) {
      if (Array.isArray(appRes.apps)) ML_STATE.apps = appRes.apps;
      if (appRes.active_app) ML_STATE.activeApp = appRes.active_app;
    }
    if (ML_STATE.view === 'on') {
      renderActiveTabContent();
    }
  } catch (_) {}
}

async function refreshStatusFromBackend() {
  try {
    const st = await mikuLinkTransport.getStatus();
    ML_STATE.connected = Boolean(st.connected);
    ML_STATE.hasPairedDevice = Boolean(st.has_paired_device || (st.devices && st.devices.length));
    ML_STATE.deviceName = st.device_name || 'Mi teléfono';
    if (st.ip) ML_STATE.ip = st.ip;
    if (st.tunnel_url !== undefined) ML_STATE.tunnelUrl = st.tunnel_url || '';
    if (st.hostname) ML_STATE.hostname = st.hostname;
    ML_STATE.battery = typeof st.battery === 'number' ? st.battery : null;
    ML_STATE.charging = Boolean(st.charging);
    ML_STATE.signal = st.signal || 'Wi‑Fi';
    ML_STATE.dnd = Boolean(st.dnd);
    ML_STATE.wallpaperUrl = st.wallpaper_url
      ? (st.wallpaper_url.startsWith('http') ? st.wallpaper_url : `${mikuLinkTransport.baseUrl}${st.wallpaper_url}`)
      : null;

    if (st.connected && ML_STATE.view !== 'on') {
      transitionMikuLinkView('on');
      await syncAllConnectedData();
    } else if (st.pairing_status === 'linking' && ML_STATE.view === 'off') {
      transitionMikuLinkView('linking');
    } else if (st.pairing_status === 'expired' && ML_STATE.view === 'linking') {
      ML_STATE.errorMsg = 'El tiempo de confirmación en el teléfono expiró.';
      transitionMikuLinkView('error');
    }
    return st;
  } catch (_) {
    return null;
  }
}

async function handleSendCurrentMessage() {
  const inp = document.getElementById('cin');
  if (!inp || !inp.value.trim()) return;
  const text = inp.value.trim();
  const thread = ML_STATE.threads[ML_STATE.selectedThreadIdx];
  if (!thread) return;
  inp.value = '';
  try {
    const res = await mikuLinkTransport.sendMessage({
      threadId: thread.id || thread.name,
      recipient: thread.name,
      text
    });
    if (res?.message) {
      thread.messages = thread.messages || [];
      thread.messages.push(res.message);
      renderActiveTabContent();
    }
    if (!res?.delivered) {
      notifyToast('Teléfono sin conexión activa', 'er', 'El mensaje quedó registrado como fallido');
    }
  } catch (err) {
    notifyToast('Error al enviar mensaje', 'er', err.message);
  }
}

export async function mountMikuLinkSection() {
  stopMikuLinkTimers();
  const root = document.getElementById('ml');
  if (!root) return;

  const st = await refreshStatusFromBackend();
  if (st?.connected || st?.has_paired_device) {
    ML_STATE.view = 'on';
  } else if (st?.pairing_status === 'linking') {
    ML_STATE.view = 'linking';
  } else {
    ML_STATE.view = 'off';
  }

  renderMikuLinkRoot();
  if (ML_STATE.view === 'on') {
    await syncAllConnectedData();
  }

  ML_STATE._clkTimer = setInterval(() => {
    updateClockDom(root);
    if (ML_STATE.activeCall && ML_STATE.view === 'on' && ML_STATE.tab === 2) {
      const ctm = document.getElementById('ctm');
      if (ctm && ML_STATE.activeCall.state !== 'dialing') {
        const elapsed = Math.max(0, Math.floor(Date.now() / 1000) - (ML_STATE.activeCall.started_at || Math.floor(Date.now() / 1000)));
        ctm.textContent = `${pad2(Math.floor(elapsed / 60))}:${pad2(elapsed % 60)}`;
      }
    }
  }, 1000);

  ML_STATE._pollTimer = setInterval(() => {
    if (document.getElementById('ml')) {
      refreshStatusFromBackend();
    } else {
      stopMikuLinkTimers();
    }
  }, 4000);

  if (ML_STATE._unsubEvents) {
    try { ML_STATE._unsubEvents(); } catch (_) {}
  }
  ML_STATE._unsubEvents = mikuLinkTransport.onEvent(async (ev) => {
    if (!ev || !document.getElementById('ml')) return;
    if ((ev.k === 'pair' || ev.type === 'miku_link_qr_updated') && ev.url) {
      if (ev.url !== ML_STATE.qr.url || (ev.pin && ev.pin !== ML_STATE.qr.pin)) {
        applyQrDataToDom(ev, false);
      }
    } else if (ev.type === 'miku_link_connected' || (ev.k === 'link' && ev.ok)) {
      await refreshStatusFromBackend();
      if (ML_STATE.view !== 'on') {
        transitionMikuLinkView('on');
        await syncAllConnectedData();
      }
    } else if (ev.type === 'miku_link_unpaired' || ev.k === 'unpair') {
      ML_STATE.connected = false;
      ML_STATE.hasPairedDevice = false;
      transitionMikuLinkView('off');
    }
  });

  const sectionEl = root.closest('section') || root;

  sectionEl.addEventListener('click', async (e) => {
    const btn = e.target.closest('[data-a]');
    if (!btn) return;
    const action = btn.dataset.a;
    const idx = Number(btn.dataset.i || 0);

    switch (action) {
      case 'copy': {
        const rawPin = (ML_STATE.qr.pin || '').replace(/\s+/g, '');
        try {
          await navigator.clipboard.writeText(rawPin);
          notifyToast(t('mikuLink.unpaired.pinCopied'), 'ok');
        } catch (_) {
          notifyToast(rawPin, 'n', 'PIN de emparejamiento');
        }
        break;
      }
      case 'refresh-qr':
        await fetchNewQrToken(true, true);
        break;
      case 'check-pair': {
        const cur = await refreshStatusFromBackend();
        if (cur?.connected) {
          notifyToast(t('mikuLink.linking.connectedToast'), 'ok', t('mikuLink.linking.connectedSub'));
        } else if (cur?.has_paired_device) {
          transitionMikuLinkView('on');
          await syncAllConnectedData();
        } else {
          notifyToast('Esperando escaneo desde el teléfono', 'n', `Red local ${ML_STATE.ip}:8000`);
        }
        break;
      }
      case 'open-registered':
        transitionMikuLinkView('on');
        await syncAllConnectedData();
        break;
      case 'cancel':
        await mikuLinkTransport.cancelPairing().catch(() => {});
        transitionMikuLinkView('off');
        break;
      case 'retry-pair':
        ML_STATE.errorMsg = '';
        transitionMikuLinkView('off');
        break;
      case 'wp':
        document.getElementById('wpf')?.click();
        break;
      case 'wpx':
        try {
          await mikuLinkTransport.removeWallpaper();
          ML_STATE.wallpaperUrl = null;
          document.querySelectorAll('.ph').forEach((p) => {
            p.dataset.w = '0';
            const wp = p.querySelector('.wp');
            if (wp) wp.style.backgroundImage = '';
          });
          notifyToast(t('mikuLink.home.wallpaperRemoved'), 'n');
        } catch (err) {
          notifyToast('No se pudo quitar el fondo', 'er', err.message);
        }
        break;
      case 'ring': {
        const ph = document.getElementById('ph');
        if (ph) {
          ph.classList.remove('rng');
          void ph.offsetWidth;
          ph.classList.add('rng');
        }
        try {
          const r = await mikuLinkTransport.ringPhone();
          notifyToast(t('mikuLink.home.ringingToast'), r?.delivered ? 'ok' : 'n', t('mikuLink.home.ringingSub'));
        } catch (err) {
          notifyToast('Error al hacer sonar el teléfono', 'er', err.message);
        }
        break;
      }
      case 'open-folder':
        await mikuLinkTransport.openReceivedFolder().catch(() => {});
        notifyToast('Abriendo carpeta Recibidos…', 'n');
        break;
      case 'lock-pc':
        try {
          await fetch(`${mikuLinkTransport.baseUrl}/api/desktop/lock`, { method: 'POST' });
        } catch (_) {}
        break;
      case 'dnd': {
        const nextDnd = btn.getAttribute('aria-checked') !== 'true';
        btn.setAttribute('aria-checked', nextDnd ? 'true' : 'false');
        ML_STATE.dnd = nextDnd;
        await mikuLinkTransport.setDoNotDisturb(nextDnd).catch(() => {});
        notifyToast(nextDnd ? 'No molestar activado' : 'No molestar desactivado', 'n');
        break;
      }
      case 'th': {
        ML_STATE.selectedThreadIdx = idx;
        const th = ML_STATE.threads[idx];
        if (th) {
          th.unread = 0;
          mikuLinkTransport.markThreadRead(th.id || th.name).catch(() => {});
        }
        renderActiveTabContent();
        break;
      }
      case 'send':
        await handleSendCurrentMessage();
        break;
      case 'send-new-thread': {
        const rec = document.getElementById('ml-new-recipient')?.value?.trim();
        const txt = document.getElementById('ml-new-msg-text')?.value?.trim();
        if (!rec || !txt) {
          notifyToast('Completa destinatario y mensaje', 'er');
          return;
        }
        try {
          await mikuLinkTransport.sendMessage({ threadId: rec, recipient: rec, text: txt });
          const msgRes = await mikuLinkTransport.getMessages();
          ML_STATE.threads = msgRes.threads || [];
          renderActiveTabContent();
        } catch (err) {
          notifyToast('Error al enviar mensaje', 'er', err.message);
        }
        break;
      }
      case 'k': {
        ML_STATE.dialNumber += btn.dataset.k || '';
        const numEl = document.getElementById('num');
        if (numEl) numEl.textContent = ML_STATE.dialNumber;
        break;
      }
      case 'del': {
        ML_STATE.dialNumber = ML_STATE.dialNumber.slice(0, -1);
        const numEl = document.getElementById('num');
        if (numEl) numEl.textContent = ML_STATE.dialNumber;
        break;
      }
      case 'dial': {
        if (!ML_STATE.dialNumber.trim()) {
          notifyToast(t('mikuLink.calls.emptyNumberError'), 'er');
          return;
        }
        try {
          const res = await mikuLinkTransport.dialCall(ML_STATE.dialNumber.trim());
          ML_STATE.activeCall = res.active_call;
          renderActiveTabContent();
        } catch (err) {
          notifyToast('No se pudo iniciar la llamada', 'er', err.message);
        }
        break;
      }
      case 'rc': {
        const item = ML_STATE.calls[idx];
        const number = item?.number || item?.name || item?.[0] || '';
        if (number) {
          const res = await mikuLinkTransport.dialCall(number);
          ML_STATE.activeCall = res.active_call;
          renderActiveTabContent();
        }
        break;
      }
      case 'mute':
      case 'spk': {
        const nextPressed = btn.getAttribute('aria-pressed') !== 'true';
        btn.setAttribute('aria-pressed', nextPressed ? 'true' : 'false');
        await mikuLinkTransport.callAction(action === 'mute' ? 'mute' : 'speaker', nextPressed).catch(() => {});
        break;
      }
      case 'hang': {
        await mikuLinkTransport.callAction('hangup').catch(() => {});
        ML_STATE.activeCall = null;
        ML_STATE.dialNumber = '';
        const callRes = await mikuLinkTransport.getCalls().catch(() => null);
        if (callRes?.recent) ML_STATE.calls = callRes.recent;
        notifyToast(t('mikuLink.calls.endedToast'), 'n');
        renderActiveTabContent();
        break;
      }
      case 'pho': {
        const photo = ML_STATE.photos[idx];
        if (!photo) return;
        ML_STATE.selectedPhoto = photo;
        const ov = document.getElementById('ml-photo-ov');
        const img = document.getElementById('ml-photo-img');
        const ttl = document.getElementById('ml-photo-title');
        if (ttl) ttl.textContent = photo.filename;
        if (img) img.src = photo.fullUrl;
        if (ov) ov.dataset.open = 'true';
        break;
      }
      case 'close-photo-modal': {
        const ov = document.getElementById('ml-photo-ov');
        if (ov) ov.dataset.open = 'false';
        break;
      }
      case 'save-photo': {
        if (!ML_STATE.selectedPhoto) return;
        try {
          const res = await mikuLinkTransport.savePhotoToPc(ML_STATE.selectedPhoto.filename);
          notifyToast('Foto guardada en Imágenes/Miku-Link', 'ok', res.saved_path || '');
          const ov = document.getElementById('ml-photo-ov');
          if (ov) ov.dataset.open = 'false';
        } catch (err) {
          notifyToast('No se pudo guardar la foto', 'er', err.message);
        }
        break;
      }
      case 'refresh-photos': {
        const phoRes = await mikuLinkTransport.getPhotos().catch(() => null);
        if (phoRes?.photos) ML_STATE.photos = phoRes.photos;
        renderActiveTabContent();
        notifyToast('Galería actualizada', 'n');
        break;
      }
      case 'refresh-notifs': {
        const notRes = await mikuLinkTransport.getNotifications().catch(() => null);
        if (notRes?.notifications) ML_STATE.notifications = notRes.notifications;
        renderActiveTabContent();
        break;
      }
      case 'rm-notif': {
        const id = btn.dataset.id;
        const rowEl = document.querySelector(`#nl [data-id="${CSS.escape(id)}"]`);
        if (rowEl) collapseOut(rowEl);
        ML_STATE.notifications = ML_STATE.notifications.filter((n) => String(n.id) !== String(id));
        await mikuLinkTransport.dismissNotification(id).catch(() => {});
        break;
      }
      case 'clr-notifs': {
        ML_STATE.notifications = [];
        await mikuLinkTransport.clearNotifications().catch(() => {});
        renderActiveTabContent();
        break;
      }
      case 'refresh-apps': {
        const appRes = await mikuLinkTransport.getApps().catch(() => null);
        if (appRes?.apps) ML_STATE.apps = appRes.apps;
        renderActiveTabContent();
        notifyToast(ML_STATE.apps.length ? 'Catálogo de apps actualizado' : 'Sin apps reportadas por el teléfono', 'n');
        break;
      }
      case 'app': {
        const appItem = ML_STATE.apps[idx];
        const name = typeof appItem === 'string' ? appItem : (appItem?.name || appItem?.id || 'App');
        const id = typeof appItem === 'string' ? appItem : (appItem?.id || name);
        const res = await mikuLinkTransport.openApp(id, name).catch(() => ({ active_app: { id, name } }));
        ML_STATE.activeApp = res.active_app || { id, name };
        renderActiveTabContent();
        break;
      }
      case 'mclose':
        await mikuLinkTransport.closeApp().catch(() => {});
        ML_STATE.activeApp = null;
        renderActiveTabContent();
        break;
      case 'shot':
        await mikuLinkTransport.captureAppScreenshot().catch(() => {});
        notifyToast(t('mikuLink.apps.screenshotSaved'), 'ok', t('mikuLink.apps.screenshotSub'));
        break;
    }
  });

  sectionEl.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && e.target.id === 'cin') {
      e.preventDefault();
      handleSendCurrentMessage();
    }
  });

  sectionEl.addEventListener('change', async (e) => {
    if (e.target.id === 'wpf' && e.target.files?.[0]) {
      const file = e.target.files[0];
      try {
        const res = await mikuLinkTransport.uploadWallpaper(file);
        ML_STATE.wallpaperUrl = res.wallpaper_url;
        document.querySelectorAll('.ph').forEach((p) => {
          p.dataset.w = '1';
          const wp = p.querySelector('.wp');
          if (wp) wp.style.backgroundImage = `url('${ML_STATE.wallpaperUrl}')`;
        });
        notifyToast(t('mikuLink.home.wallpaperUpdated'), 'ok');
      } catch (err) {
        notifyToast('Error al guardar el fondo de pantalla', 'er', err.message);
      }
      e.target.value = '';
    }
  });
}

if (typeof window !== 'undefined') {
  window.MikuLinkSection = {
    renderMikuLinkSectionHtml,
    mountMikuLinkSection,
    stopMikuLinkTimers,
    transitionMikuLinkView,
    ML_STATE
  };
}

