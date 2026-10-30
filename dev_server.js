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
  version: '0.2.0-beta',
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
    { id: 'korus', name: 'Korus', role: 'Claude Code', category: 'code', c: '#7C3AED', model: 'claude-3-7-sonnet', isl: 1, active: true, phases: ['Read', 'Edit', 'Bash', 'Done'] },
    { id: 'antigravity', name: 'Antigravity', role: 'Project Architect', category: 'code', c: '#00D2FF', model: 'gemini-2.5-pro', isl: 2, active: true, phases: ['Read', 'Edit', 'Bash', 'Done'] },
    { id: 'codex', name: 'Codex', role: 'Autonomous Code Generator', category: 'code', c: '#10B981', model: 'deepseek-coder', isl: 3, active: true, phases: ['Read', 'Edit', 'Bash', 'Done'] },
    { id: 'scholar', name: 'Scholar', role: 'Research Analyst', category: 'research', c: '#3B82F6', model: 'gemini-2.5-flash', isl: 4, active: true, phases: ['Search', 'Extract', 'Synthesize', 'Done'] },
    { id: 'indexer', name: 'Indexer', role: 'Data & SQL Engineer', category: 'data', c: '#F59E0B', model: 'groq-llama-3.3-70b', isl: 5, active: true, phases: ['Scan', 'Process', 'Write', 'Done'] },
    { id: 'sentinel', name: 'Sentinel', role: 'Operations & Watchdog', category: 'general', c: '#EF4444', model: 'gemini-2.5-flash', isl: 6, active: true, phases: ['Listen', 'Think', 'Action', 'Done'] }
  ],
  integrations: {
    github: { id: 'github', name: 'GitHub', connected: true, account: 'miku-dev', status: 'Conectado · Webhook activo', icon: 'github', repo_count: 12 },
    vercel: { id: 'vercel', name: 'Vercel', connected: true, account: 'miku-team', status: 'Conectado · 4 proyectos sincronizados', icon: 'vercel', deploys_today: 9 },
    spotify: { id: 'spotify', name: 'Spotify', connected: true, account: 'Premium', status: 'Conectado · Audio Ducking activo', icon: 'spotify', track: 'World is Mine' },
    discord: { id: 'discord', name: 'Discord', connected: true, account: 'MikuBot#0039', status: 'En línea · Canal #dev', icon: 'discord' },
    notion: { id: 'notion', name: 'Notion', connected: true, account: 'Workspace Personal', status: 'Sincronizado · Base de datos activa', icon: 'notion' },
    telegram: { id: 'telegram', name: 'Telegram', connected: true, account: '@MikuCompanionBot', status: 'Conectado · Notificaciones push', icon: 'telegram' },
    google_workspace: { id: 'google_workspace', name: 'Google Workspace', connected: true, account: 'miku.companion@gmail.com', status: 'OAuth activo (Gmail, Calendar, Drive)', icon: 'google' },
    docker: { id: 'docker', name: 'Docker Local', connected: true, account: 'docker.sock', status: '3 contenedores activos', icon: 'docker' }
  },
  mcpCatalog: [
    { id: 'github-mcp', name: 'GitHub MCP Server', desc: 'Control de repositorios, issues, commits y pull requests en vivo.', author: 'modelcontextprotocol', repo_url: 'https://github.com/modelcontextprotocol/servers/tree/main/src/github', stars: 1840, installed: true, enabled: true },
    { id: 'filesystem-mcp', name: 'Filesystem Safe MCP', desc: 'Inspección, lectura y parcheo granular de archivos en directorios autorizados.', author: 'modelcontextprotocol', repo_url: 'https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem', stars: 2210, installed: true, enabled: true },
    { id: 'sqlite-mcp', name: 'SQLite Explorer MCP', desc: 'Ejecución de queries SQL locales, migraciones e inspección de esquemas.', author: 'modelcontextprotocol', repo_url: 'https://github.com/modelcontextprotocol/servers/tree/main/src/sqlite', stars: 950, installed: true, enabled: true },
    { id: 'postgres-mcp', name: 'PostgreSQL & Cloud SQL MCP', desc: 'Conector para bases de datos relacionales Postgres con pooling.', author: 'modelcontextprotocol', repo_url: 'https://github.com/modelcontextprotocol/servers/tree/main/src/postgres', stars: 1420, installed: false, enabled: false },
    { id: 'brave-search-mcp', name: 'Brave Web Search MCP', desc: 'Búsqueda web estructurada y extracción de fuentes oficiales.', author: 'modelcontextprotocol', repo_url: 'https://github.com/modelcontextprotocol/servers/tree/main/src/brave-search', stars: 1680, installed: false, enabled: false },
    { id: 'playwright-mcp', name: 'Playwright Browser MCP', desc: 'Automatización de navegación web, capturas y comprobación de interfaces.', author: 'modelcontextprotocol', repo_url: 'https://github.com/modelcontextprotocol/servers/tree/main/src/puppeteer', stars: 2950, installed: false, enabled: false },
    { id: 'docker-mcp', name: 'Docker Engine MCP', desc: 'Supervisión y control de contenedores y servicios en segundo plano.', author: 'modelcontextprotocol', repo_url: 'https://github.com/modelcontextprotocol/servers/tree/main/src/docker', stars: 820, installed: false, enabled: false },
    { id: 'fetch-mcp', name: 'HTTP Fetch & Webhook MCP', desc: 'Peticiones REST seguras con filtrado de cabeceras y sanitización.', author: 'modelcontextprotocol', repo_url: 'https://github.com/modelcontextprotocol/servers/tree/main/src/fetch', stars: 740, installed: false, enabled: false }
  ],
  skills: [
    { id: 'git-code-reviewer', name: 'Revisor de Git y Código', category: 'Desarrollo', description: 'Analiza diffs, prepara commits atómicos y detecta fallos de sintaxis.', triggers: ['git diff', 'commit', 'revisar codigo'], enabled: true, is_builtin: true },
    { id: 'web-researcher', name: 'Investigador Web y Grounding', category: 'Investigación', description: 'Búsquedas web estructuradas, extracción de fuentes verificadas y síntesis.', triggers: ['busca en internet', 'investiga', 'grounding'], enabled: true, is_builtin: true },
    { id: 'desktop-automation', name: 'Automatización de Escritorio y CLI', category: 'Sistema', description: 'Ejecución segura de comandos, manipulación de archivos y scripts.', triggers: ['ejecuta en terminal', 'corre comando', 'instala dependencia'], enabled: true, is_builtin: true },
    { id: 'phone-link-assistant', name: 'Asistente de Enlace Móvil Miku-Link', category: 'Móvil', description: 'Sincronización de notificaciones, fotos y portapapeles con Android.', triggers: ['celular', 'telefono', 'miku link', 'android'], enabled: true, is_builtin: true },
    { id: 'study-pomodoro', name: 'Asistente de Enfoque y Pomodoro', category: 'Productividad', description: 'Bloques de trabajo concentrado y pausas activas.', triggers: ['pomodoro', 'modo estudio', 'concentracion'], enabled: true, is_builtin: true }
  ],
  autostart: {
    enabled: true,
    platform: 'windows',
    path: 'shell:startup'
  },
  update: {
    available: true,
    current_version: '0.5.3',
    latest_version: '0.5.6',
    title: 'Ya salió Miku 0.5.6',
    sub: 'Tienes la 0.5.3',
    notes: [
      'Pantalla de trabajo en vivo para agentes de código y asistentes generales',
      'Desacople de Agentes e Integraciones nativas',
      'Catálogo online de MCP con enlaces directos a GitHub y botón de descarga compacto',
      'Sistema de Skills Nativas de Miku con auto-activación inteligente',
      'Dashboard local de uso de API con circuit-breaker anti-429',
      'Atenuación dinámica de audio (Audio Ducking) al 20%'
    ]
  },
  activeTasks: [
    {
      task_id: 'task_korus_invoice',
      agent_id: 'korus',
      agent_name: 'Korus',
      agent_role: 'Claude Code',
      category: 'code',
      task: 'Ajuste de cálculo de impuestos en invoice.ts',
      phase: 'Edit',
      phase_index: 1,
      phases: ['Read', 'Edit', 'Bash', 'Done'],
      progress: 55,
      file: 'src/invoice.ts',
      diff: {
        file: 'src/invoice.ts',
        path: 'src/invoice.ts',
        language: 'TS',
        deleted_lines: [{ line: 12, text: 'const TVA = 0.196' }],
        added_lines: [{ line: 12, text: 'const TVA = 0.20' }],
        full_lines: [
          { num: 10, type: 'ctx', text: "import { Item } from './types'" },
          { num: 11, type: 'ctx', text: "" },
          { num: 12, type: 'del', text: "- const TVA = 0.196" },
          { num: 12, type: 'add', text: "+ const TVA |" },
          { num: 13, type: 'ctx', text: "" },
          { num: 14, type: 'ctx', text: "export function total(items: Item[]) {" },
          { num: 15, type: 'ctx', text: "  const sum = items.reduce((s, i) => s + i.price, 0)" },
          { num: 16, type: 'ctx', text: "  return sum * (1 + TVA)" },
          { num: 17, type: 'ctx', text: "}" }
        ]
      }
    }
  ],
  media: {
    track: 'World is Mine',
    artist: 'Hatsune Miku · ryo',
    album: 'Supercell',
    is_playing: true,
    volume: 75,
    is_ducked: false
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
    version: '0.2.0',
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
      version: '0.2.0',
      mode: MOCK_STATE.execMode,
      local_ip: MOCK_STATE.local_ip,
      cloudflared_tunnel: MOCK_STATE.tunnel_url,
      device_paired: true
    }));
    return;
  }

  // Agents endpoint (built-in and custom)
  if (pathname === '/api/agents') {
    if (req.method === 'POST') {
      let body = '';
      req.on('data', chunk => { body += chunk; });
      req.on('end', () => {
        let data = {};
        try { data = JSON.parse(body || '{}'); } catch (_) {}
        const name = (data.name || 'Nuevo Agente').trim();
        const id = (data.id || name.toLowerCase().replace(/[^a-z0-9]+/g, '-')).replace(/^-+|-+$/g, '');
        const vaultVar = `MIKU_AGENT_${id.toUpperCase().replace(/-/g, '_')}_KEY`;
        const category = data.category || 'general';
        const defaultPhases = category === 'code' ? ['Read', 'Edit', 'Bash', 'Done'] :
                              category === 'research' ? ['Search', 'Extract', 'Synthesize', 'Done'] :
                              category === 'data' ? ['Scan', 'Process', 'Write', 'Done'] :
                              ['Listen', 'Think', 'Action', 'Done'];

        const newAgent = {
          id,
          name,
          role: data.role || 'Asistente Especializado',
          category,
          c: data.c || data.avatar_color || '#8B5CF6',
          model: data.model || 'gemini-2.5-flash',
          api_key_env_var: vaultVar,
          requires_api_key: Boolean(data.requires_api_key),
          temperature: parseFloat(data.temperature || 0.3),
          autonomy_level: data.autonomy_level || 'supervised',
          cli_permissions: Boolean(data.cli_permissions),
          assigned_skills: data.assigned_skills || [],
          assigned_mcp_servers: data.assigned_mcp_servers || [],
          isolated_memory: data.isolated_memory !== false,
          trigger_keywords: data.trigger_keywords || [name.toLowerCase()],
          phases: data.phases || defaultPhases,
          isl: MOCK_STATE.agents.length + 1,
          active: true,
          is_custom: true
        };

        const existingIdx = MOCK_STATE.agents.findIndex(a => a.id === id);
        if (existingIdx >= 0) {
          MOCK_STATE.agents[existingIdx] = { ...MOCK_STATE.agents[existingIdx], ...newAgent };
        } else {
          MOCK_STATE.agents.push(newAgent);
        }

        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ status: 'ok', agent: newAgent, vault_env_var: vaultVar }));
      });
      return;
    }

    if (req.method === 'DELETE') {
      const agentId = urlObj.searchParams.get('id');
      if (agentId) {
        MOCK_STATE.agents = MOCK_STATE.agents.filter(a => a.id !== agentId);
      }
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ status: 'ok', deleted: agentId }));
      return;
    }

    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify(MOCK_STATE.agents));
    return;
  }

  // Active tasks for live work view
  if (pathname === '/api/agents/active_tasks') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      status: 'ok',
      tasks: MOCK_STATE.activeTasks || []
    }));
    return;
  }

  // Delegate task to agent
  if (pathname === '/api/agents/delegate' && req.method === 'POST') {
    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', () => {
      let data = {};
      try { data = JSON.parse(body || '{}'); } catch (_) {}
      const agentId = data.agent_id || 'korus';
      const taskText = data.task || 'Refactorización y optimización de código';
      const targetAgent = MOCK_STATE.agents.find(a => a.id === agentId) || MOCK_STATE.agents[0];

      const phases = targetAgent.phases || ['Read', 'Edit', 'Bash', 'Done'];
      const taskId = `task_${Date.now()}`;

      const activeTask = {
        task_id: taskId,
        agent_id: agentId,
        agent_name: targetAgent.name,
        agent_role: targetAgent.role,
        category: targetAgent.category || 'code',
        task: taskText,
        phase: phases[1] || 'Edit',
        phase_index: 1,
        phases: phases,
        progress: 45,
        start_time: Date.now(),
        file: 'src/invoice.ts',
        diff: {
          file: 'src/invoice.ts',
          path: 'src/invoice.ts',
          language: 'TS',
          deleted_lines: [{ line: 12, text: 'const TVA = 0.196' }],
          added_lines: [{ line: 12, text: 'const TVA = 0.20' }],
          full_lines: [
            { num: 10, type: 'ctx', text: "import { Item } from './types'" },
            { num: 11, type: 'ctx', text: "" },
            { num: 12, type: 'del', text: "- const TVA = 0.196" },
            { num: 12, type: 'add', text: "+ const TVA = 0.20 |" },
            { num: 13, type: 'ctx', text: "" },
            { num: 14, type: 'ctx', text: "export function total(items: Item[]) {" },
            { num: 15, type: 'ctx', text: "  const sum = items.reduce((s, i) => s + i.price, 0)" },
            { num: 16, type: 'ctx', text: "  return sum * (1 + TVA)" },
            { num: 17, type: 'ctx', text: "}" }
          ]
        }
      };

      MOCK_STATE.activeTasks = [activeTask];

      // Broadcast via WebSocket to Island
      const wsMsg = JSON.stringify({
        type: 'agent_task_update',
        task: activeTask
      });
      wsClients.forEach(s => sendWsText(s, wsMsg));

      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ status: 'ok', task: activeTask }));
    });
    return;
  }

  // Skills Nativas API
  if (pathname === '/api/skills') {
    if (req.method === 'POST') {
      let body = '';
      req.on('data', chunk => { body += chunk; });
      req.on('end', () => {
        let data = {};
        try { data = JSON.parse(body || '{}'); } catch (_) {}
        const id = data.id || `custom-skill-${Date.now()}`;
        const newSkill = {
          id,
          name: data.name || 'Nueva Skill Especializada',
          category: data.category || 'General',
          description: data.description || 'Instrucciones y herramientas ampliadas',
          triggers: data.triggers || [],
          tools_required: data.tools_required || [],
          max_concurrent: 1,
          system_prompt_addon: data.system_prompt_addon || '',
          enabled: data.enabled !== false,
          is_custom: true
        };
        const idx = MOCK_STATE.skills.findIndex(s => s.id === id);
        if (idx >= 0) MOCK_STATE.skills[idx] = newSkill;
        else MOCK_STATE.skills.push(newSkill);

        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ status: 'ok', skill: newSkill }));
      });
      return;
    }

    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ status: 'ok', skills: MOCK_STATE.skills }));
    return;
  }

  // Integraciones Nativas
  if (pathname === '/api/integrations') {
    if (req.method === 'POST') {
      let body = '';
      req.on('data', chunk => { body += chunk; });
      req.on('end', () => {
        let data = {};
        try { data = JSON.parse(body || '{}'); } catch (_) {}
        const id = data.id;
        if (id && MOCK_STATE.integrations[id]) {
          MOCK_STATE.integrations[id].connected = Boolean(data.connected);
          if (data.status) MOCK_STATE.integrations[id].status = data.status;
        }
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ status: 'ok', integrations: MOCK_STATE.integrations }));
      });
      return;
    }
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ status: 'ok', integrations: MOCK_STATE.integrations }));
    return;
  }

  // Telemetria y Dashboard de uso de API
  if (pathname === '/api/telemetry/usage') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      status: 'ok',
      total_requests: 48,
      successful_requests: 48,
      failed_requests: 0,
      total_tokens: 68420,
      prompt_tokens: 42150,
      completion_tokens: 26270,
      total_cost_usd: 0.0184,
      avg_latency_ms: 194.2,
      circuit_breakers: [
        { provider: 'gemini', state: 'CLOSED', fallback: 'groq', latency_ms: 118, health: '100%' },
        { provider: 'groq', state: 'CLOSED', fallback: 'deepseek', latency_ms: 82, health: '100%' },
        { provider: 'anthropic', state: 'CLOSED', fallback: 'gemini', latency_ms: 240, health: '100%' },
        { provider: 'deepseek', state: 'CLOSED', fallback: 'groq', latency_ms: 165, health: '100%' }
      ],
      by_model: {
        'gemini-2.5-flash': { requests: 28, tokens: 36200, cost_usd: 0.0058, avg_latency: 120.4 },
        'gemini-2.5-pro': { requests: 8, tokens: 18400, cost_usd: 0.0089, avg_latency: 310.2 },
        'claude-3-7-sonnet': { requests: 6, tokens: 8200, cost_usd: 0.0028, avg_latency: 245.0 },
        'deepseek-coder': { requests: 6, tokens: 5620, cost_usd: 0.0009, avg_latency: 160.1 }
      },
      by_agent: {
        'korus': { requests: 12, tokens: 18400, cost_usd: 0.0052 },
        'antigravity': { requests: 16, tokens: 24600, cost_usd: 0.0078 },
        'codex': { requests: 10, tokens: 12200, cost_usd: 0.0024 },
        'miku': { requests: 10, tokens: 13220, cost_usd: 0.0030 }
      }
    }));
    return;
  }

  // Audio ducking media control
  if (pathname === '/api/media/duck' && req.method === 'POST') {
    MOCK_STATE.media.is_ducked = true;
    MOCK_STATE.media.volume = 20;
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ status: 'ok', ducked: true, volume: 20 }));
    return;
  }

  if (pathname === '/api/media/restore' && req.method === 'POST') {
    MOCK_STATE.media.is_ducked = false;
    MOCK_STATE.media.volume = 75;
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ status: 'ok', ducked: false, volume: 75 }));
    return;
  }

  // List available custom sounds in assets/sounds
  if (pathname === '/api/sounds/list') {
    let files = [];
    try {
      const soundsDir = path.join(__dirname, 'assets', 'sounds');
      if (fs.existsSync(soundsDir)) {
        files = fs.readdirSync(soundsDir).filter(f => /\.(mp3|wav)$/i.test(f));
      }
    } catch (_) {}
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ status: 'ok', files }));
    return;
  }

  // System Update status
  if (pathname === '/api/system/update') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify(MOCK_STATE.update));
    return;
  }

  // Autostart toggle
  if (pathname === '/api/system/autostart') {
    if (req.method === 'POST') {
      let body = '';
      req.on('data', chunk => { body += chunk; });
      req.on('end', () => {
        let data = {};
        try { data = JSON.parse(body || '{}'); } catch (_) {}
        MOCK_STATE.autostart.enabled = Boolean(data.enabled);
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ status: 'ok', autostart: MOCK_STATE.autostart }));
      });
      return;
    }
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ status: 'ok', autostart: MOCK_STATE.autostart }));
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
      res.end(JSON.stringify({ status: 'ok', vault_backend: 'os_keyring_dpapi', message: 'Clave guardada en bóveda cifrada' }));
      return;
    }
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      vault_backend: 'os_keyring_dpapi',
      keys: {
        GEMINI_API_KEY: { is_set: true, value_masked: '••••rjFA', source: 'vault' },
        GROQ_API_KEY: { is_set: true, value_masked: '••••boeT', source: 'vault' },
        DEEPSEEK_API_KEY: { is_set: true, value_masked: '••••eba6', source: 'vault' },
        OPENAI_API_KEY: { is_set: false, value_masked: '', source: 'none' },
        ANTHROPIC_API_KEY: { is_set: false, value_masked: '', source: 'none' },
        OPENROUTER_API_KEY: { is_set: false, value_masked: '', source: 'none' }
      }
    }));
    return;
  }

  if (pathname === '/api/config/models/test' && req.method === 'POST') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      status: 'ok',
      provider: 'verified',
      latency_ms: 118,
      message: 'Conexión verificada con el proveedor'
    }));
    return;
  }

  if (pathname === '/api/hooks/event' && req.method === 'POST') {
    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', () => {
      let data = {};
      try { data = JSON.parse(body || '{}'); } catch (_) {}
      const payload = JSON.stringify({
        type: 'miku_state',
        state: data.event_type === 'error' ? 'error' : (data.event_type === 'tool_start' ? 'working' : 'thinking'),
        thought: data.thought || data.detail || 'Hook recibido',
        source: data.source || 'ide-hook'
      });
      wsClients.forEach(s => sendWsText(s, payload));
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ status: 'ok', miku_state: 'working', thought: data.thought || '' }));
    });
    return;
  }

  if (pathname === '/api/ui/choice' && req.method === 'POST') {
    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', () => {
      let data = {};
      try { data = JSON.parse(body || '{}'); } catch (_) {}
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ status: 'ok', resolved: true, choice: data.choice || 'allow' }));
    });
    return;
  }

  // Online MCP Catalog with repo URLs & direct install toggle
  if (pathname === '/api/mcp/catalog') {
    if (req.method === 'POST') {
      let body = '';
      req.on('data', chunk => { body += chunk; });
      req.on('end', () => {
        let data = {};
        try { data = JSON.parse(body || '{}'); } catch (_) {}
        const id = data.id;
        const target = MOCK_STATE.mcpCatalog.find(m => m.id === id);
        if (target) {
          if (typeof data.installed === 'boolean') target.installed = data.installed;
          if (typeof data.enabled === 'boolean') target.enabled = data.enabled;
        }
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ status: 'ok', item: target, catalog: MOCK_STATE.mcpCatalog }));
      });
      return;
    }

    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      status: 'ok',
      catalog: MOCK_STATE.mcpCatalog
    }));
    return;
  }

  if (pathname === '/api/google/oauth/status') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      status: 'ok',
      oauth_configured: true,
      grounding_ready: true,
      auth_url: ''
    }));
    return;
  }

  if (pathname === '/api/startup/metrics') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      status: 'ok',
      metrics: { boot_duration_ms: 340, target_under_1500ms: true },
      plugins_loaded: ['ui', 'desktop', 'media', 'vision', 'browser', 'google', 'hooks', 'mcp']
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
  console.log(`[DevServer] Miku Desktop Web Gateway active on http://${HOST}:${PORT}`);
  console.log(`[DevServer] Settings: http://${HOST}:${PORT}/settings`);
  console.log(`[DevServer] Island:   http://${HOST}:${PORT}/island`);
});
