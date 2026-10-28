import http from 'http';
import fs from 'fs';
import path from 'path';
import crypto from 'crypto';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const PORT = parseInt(process.env.PORT || '3000', 10);
const HOST = '0.0.0.0';

const MIME_TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.gif': 'image/gif',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon',
  '.webp': 'image/webp',
  '.wav': 'audio/wav',
  '.mp3': 'audio/mpeg',
  '.woff': 'font/woff',
  '.woff2': 'font/woff2',
  '.ttf': 'font/ttf'
};

const MOCK_STATE = {
  status: 'ok',
  version: '0.1.7-beta',
  execMode: 'sandbox',
  tunnel_url: 'https://miku-gateway.trycloudflare.com',
  local_ip: '192.168.1.100',
  device: {
    id: '2510ERA8BG',
    name: 'Xiaomi 14 / Android 14',
    battery: 88,
    charging: true,
    paired: true,
    last_sync: new Date().toISOString(),
    tunnel_active: true
  },
  agents: [
    { id: 'github', name: 'GitHub', c: '#39D353', role: 'Control de versiones, commits y repos', model: 'google/gemini-2.5-flash', isl: 1 },
    { id: 'antigravity', name: 'Antigravity', c: '#00D2FF', role: 'Desarrollo frontend e interfaz reactiva', model: 'google/gemini-2.5-pro', isl: 2 }
  ],
  media: {
    track: 'World is Mine',
    artist: 'Hatsune Miku · ryo',
    album: 'Supercell',
    is_playing: true,
    volume: 75
  }
};

const wsClients = new Set();

function handleUpgrade(req, socket, head) {
  const key = req.headers['sec-websocket-key'];
  if (!key) {
    socket.destroy();
    return;
  }

  const acceptKey = crypto
    .createHash('sha1')
    .update(key + '258EAFA5-E914-47DA-95CA-C5AB0DC85B11')
    .digest('base64');

  const responseHeaders = [
    'HTTP/1.1 101 Switching Protocols',
    'Upgrade: websocket',
    'Connection: Upgrade',
    `Sec-WebSocket-Accept: ${acceptKey}`
  ];

  socket.write(responseHeaders.join('\r\n') + '\r\n\r\n');
  wsClients.add(socket);

  socket.on('close', () => wsClients.delete(socket));
  socket.on('error', () => wsClients.delete(socket));

  // Send initial welcome state frame
  const welcomePayload = JSON.stringify({
    type: 'init_state',
    status: 'online',
    version: '0.1.7',
    device: MOCK_STATE.device,
    tunnel_url: MOCK_STATE.tunnel_url
  });
  sendWsText(socket, welcomePayload);
}

function sendWsText(socket, text) {
  try {
    const payload = Buffer.from(text);
    const length = payload.length;
    let header;
    if (length <= 125) {
      header = Buffer.from([0x81, length]);
    } else if (length <= 65535) {
      header = Buffer.alloc(4);
      header[0] = 0x81;
      header[1] = 126;
      header.writeUInt16BE(length, 2);
    } else {
      header = Buffer.alloc(10);
      header[0] = 0x81;
      header[1] = 127;
      header.writeBigUInt64BE(BigInt(length), 2);
    }
    socket.write(Buffer.concat([header, payload]));
  } catch (_) {}
}

const server = http.createServer((req, res) => {
  const urlObj = new URL(req.url, `http://${req.headers.host || 'localhost'}`);
  let pathname = decodeURIComponent(urlObj.pathname);

  // Enable CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, PUT, DELETE');
  res.setHeader('Access-Control-Allow-Headers', '*');

  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    res.end();
    return;
  }

  // REST API Routes
  if (pathname === '/status' || pathname === '/api/status') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      status: 'ok',
      version: '0.1.7',
      mode: MOCK_STATE.execMode,
      local_ip: MOCK_STATE.local_ip,
      cloudflared_tunnel: MOCK_STATE.tunnel_url,
      device_paired: true
    }));
    return;
  }

  if (pathname === '/api/agents') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify(MOCK_STATE.agents));
    return;
  }

  if (pathname === '/api/media/status') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify(MOCK_STATE.media));
    return;
  }

  if (pathname === '/api/miku_link/device' || pathname === '/api/device') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify(MOCK_STATE.device));
    return;
  }

  if (pathname === '/api/link/open-folder' || pathname === '/api/open_shared_folder') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ status: 'ok', message: 'Carpeta de archivos recibidos abierta en el explorador' }));
    return;
  }

  if (pathname === '/api/link/photos') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      status: 'ok',
      photos: [
        {
          filename: 'IMG-20261017-WA0003.jpeg',
          size_kb: 480,
          modified_at: Date.now() - 3600000,
          url: '/public/assets/aistudio/image_0bb9c7ca.png'
        }
      ]
    }));
    return;
  }

  if (pathname === '/api/config/keys' || pathname === '/api/keys') {
    if (req.method === 'POST') {
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ status: 'ok', message: 'Clave guardada correctamente' }));
      return;
    }
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      keys: {
        GEMINI_API_KEY: { is_set: true, value_masked: '••••rjFA' },
        GROQ_API_KEY: { is_set: true, value_masked: '••••boeT' },
        DEEPSEEK_API_KEY: { is_set: true, value_masked: '••••eba6' },
        OPENAI_API_KEY: { is_set: false, value_masked: '' },
        ANTHROPIC_API_KEY: { is_set: false, value_masked: '' },
        OPENROUTER_API_KEY: { is_set: false, value_masked: '' }
      }
    }));
    return;
  }

  if (pathname.startsWith('/api/')) {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ status: 'ok', message: 'Operación completada' }));
    return;
  }

  // Page Routing
  if (pathname === '/' || pathname === '/config' || pathname === '/settings') {
    pathname = '/miku_ui/src/miku_settings.html';
  } else if (pathname === '/island') {
    pathname = '/miku_ui/src/index.html';
  } else if (pathname === '/catalogo') {
    pathname = '/miku-catalogo.html';
  }

  // Resolve file path
  let filePath = path.join(__dirname, pathname);

  // If pointing inside /src/ directly from miku_settings.html
  if (!fs.existsSync(filePath)) {
    const alternativePaths = [
      path.join(__dirname, 'miku_ui', 'src', pathname),
      path.join(__dirname, 'miku_ui', pathname),
      path.join(__dirname, 'public', pathname)
    ];
    for (const alt of alternativePaths) {
      if (fs.existsSync(alt) && fs.statSync(alt).isFile()) {
        filePath = alt;
        break;
      }
    }
  }

  if (fs.existsSync(filePath) && fs.statSync(filePath).isDirectory()) {
    filePath = path.join(filePath, 'index.html');
  }

  if (!fs.existsSync(filePath)) {
    res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' });
    res.end(`404 Not Found: ${pathname}`);
    return;
  }

  const ext = path.extname(filePath).toLowerCase();
  const contentType = MIME_TYPES[ext] || 'application/octet-stream';

  try {
    const data = fs.readFileSync(filePath);
    res.writeHead(200, {
      'Content-Type': contentType,
      'Cache-Control': 'no-cache, no-store, must-revalidate'
    });
    res.end(data);
  } catch (err) {
    res.writeHead(500, { 'Content-Type': 'text/plain; charset=utf-8' });
    res.end(`500 Server Error: ${err.message}`);
  }
});

server.on('upgrade', handleUpgrade);

server.listen(PORT, HOST, () => {
  console.log(`[DevServer] 🚀 Miku Desktop Web Gateway active on http://${HOST}:${PORT}`);
  console.log(`[DevServer] ⚙️  Settings: http://${HOST}:${PORT}/settings`);
  console.log(`[DevServer] 🏝️  Island:   http://${HOST}:${PORT}/island`);
});
