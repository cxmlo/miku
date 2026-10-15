export const getBaseUrl = (ip: string | null | undefined): string => {
  if (!ip) return 'http://127.0.0.1:8000';
  
  // Si es un dominio (Cloudflare), usamos HTTPS sin puerto 8000
  if (ip.includes('.com') || ip.includes('.org') || ip.includes('.net') || ip.includes('.trycloudflare.com') || ip.includes('.xyz')) {
    return `https://${ip}`;
  }
  
  // Si es IP local, usamos HTTP con puerto 8000
  return `http://${ip}:8000`;
};

export const getWsUrl = (ip: string | null | undefined): string => {
  if (!ip) return 'ws://127.0.0.1:8000';
  
  // Si es un dominio, usamos WSS (WebSocket Secure)
  if (ip.includes('.com') || ip.includes('.org') || ip.includes('.net') || ip.includes('.trycloudflare.com') || ip.includes('.xyz')) {
    return `wss://${ip}`;
  }
  
  // Si es IP local, usamos WS con puerto 8000
  return `ws://${ip}:8000`;
};
