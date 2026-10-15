from fastapi import FastAPI, Request, HTTPException, Security, WebSocket, WebSocketDisconnect, UploadFile, File, Header
from fastapi.security.api_key import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Dict, Any
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uuid
import miku_db
import ctypes
from pydantic import BaseModel
import uvicorn
import os
import shutil
import tempfile
import json
import time
import asyncio
import subprocess
import pyperclip
import sys
# Configure UTF-8 encoding for Windows standard output to avoid UnicodeEncodeError
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import io
import base64
import win32clipboard
from PIL import Image
from fastapi.responses import FileResponse
from fastapi import Request
from dotenv import load_dotenv
from brain import get_llm_response
from prompt_manager import get_system_prompt
import audio_handler
from audio_handler import generate_full_audio_file, speak, wait_for_wake_word, listen_and_transcribe, stop_speaking, set_barge_in_callback
import logging

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

load_dotenv()

# ==========================================
# SEGURIDAD: API KEY
# ==========================================
API_KEY = os.getenv("MIKU_API_KEY", "miku_secure_key_2026")

def sync_miku_state(state: str):
    import requests
    # ui.py call removed: set_miku_state(state)
    text_map = {"idle": "IDLE", "thinking": "pensando...", "talking": "hablando..."}
    
    def _send():
        try:
            requests.post("http://127.0.0.1:8000/broadcast_command", 
                          json={"payload": {"type": "ui_command", "action": "status_update", "text": text_map.get(state, state)}}, 
                          headers={"x-api-key": API_KEY}, timeout=0.5)
        except: pass
        
    import threading
    threading.Thread(target=_send, daemon=True).start()

API_KEY_NAME = "x-api-key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

def get_api_key(request: Request, api_key_header: str = Security(api_key_header)):
    # Permitir peticiones desde localhost / loopback directamente
    client_host = request.client.host if request.client else ""
    if client_host in ("127.0.0.1", "localhost", "::1", "testclient"):
        return API_KEY
    if api_key_header == API_KEY:
        return api_key_header
    raise HTTPException(status_code=403, detail="Acceso denegado: API Key inválida.")

# ==========================================
# INICIALIZACIÓN DE FASTAPI
# ==========================================
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Miku Backend (OpenClaw Gateway)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# CURSOR TRACKING GLOBAL (Para los ojos de Miku)
# ==========================================
import ctypes
class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

@app.get("/mouse")
def get_mouse():
    pt = POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
    return {"x": pt.x, "y": pt.y}

from pydantic import BaseModel
class FileRequest(BaseModel):
    ruta: str

@app.post("/analyze_file")
async def analyze_file(req: FileRequest):
    import tools_miku
    import threading
    # Ejecutar en segundo plano para no bloquear
    def _run():
        res = tools_miku.analizar_archivo(req.ruta)
        # Mostrar resultado en UI:
        sync_miku_state("idle")
        tools_miku.mostrar_widget_info("Análisis completado", res, "📋", 20)
    
    sync_miku_state("thinking")
    threading.Thread(target=_run, daemon=True).start()
    return {"status": "ok"}

logger = logging.getLogger("MikuGateway")

# Habilitar CORS para peticiones desde el móvil
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir archivos compartidos (Descargas desde el Celular)
os.makedirs("shared_files", exist_ok=True)
app.mount("/shared", StaticFiles(directory="shared_files"), name="shared")

# Servir SVGs y assets locales
if os.path.exists("assets"):
    app.mount("/assets", StaticFiles(directory="assets"), name="assets")

# Servir la Isla Dinámica de Miku (interfaz web)
if os.path.exists("miku_island"):
    app.mount("/island", StaticFiles(directory="miku_island", html=True), name="island")

# Sesión de emparejamiento temporal
PAIRING_SESSION = None

class _POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

@app.get("/mouse")
def get_mouse_position():
    pt = _POINT()
    try:
        ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
        return {"x": pt.x, "y": pt.y}
    except Exception:
        return {"x": 0, "y": 0}

class ChatRequest(BaseModel):
    message: str
    source: str = "mobile"  # 'mobile' o 'pc'
    agent_id: str = "miku"
    agent_name: str = "Miku"
    agent_prompt: str = ""
    agent_mcp: Optional[str] = None
    silent: bool = False

class ChatResponse(BaseModel):
    reply: str
    audio_url: Optional[str] = None
    agent_id: Optional[str] = "miku"
    agent_name: Optional[str] = "Miku"

from datetime import datetime
import json

# Memoria de Chat Global Diaria
CHAT_HISTORY_DIR = "chat_history"
os.makedirs(CHAT_HISTORY_DIR, exist_ok=True)

def get_daily_history_file():
    today = datetime.now().strftime("%Y-%m-%d")
    return os.path.join(CHAT_HISTORY_DIR, f"history_{today}.json")

def get_chat_history():
    file_path = get_daily_history_file()
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def append_to_chat_history(msg):
    history = get_chat_history()
    history.append(msg)
    with open(get_daily_history_file(), "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

chat_history = get_chat_history()

# Manejo de WebSockets para estado en tiempo real (Always On Mic & Status)
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        async with self._lock:
            if websocket not in self.active_connections:
                self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast_status(self, status_msg: str):
        async with self._lock:
            for connection in self.active_connections:
                try:
                    await connection.send_text(status_msg)
                except Exception as e:
                    logger.error(f"Error enviando WebSocket: {e}")

    async def broadcast_message(self, message: dict):
        if message.get("type") == "ui_command":
            action = message.get("action")
            args = message.get("args", [])
            if action and args:
                try:
                    from ui import ui_comm
                    if action == "show_weather":
                        ui_comm.show_weather_signal.emit(*args)
                    elif action == "show_clock":
                        ui_comm.show_clock_signal.emit(*args)
                    elif action == "show_info":
                        ui_comm.show_info_signal.emit(*args)
                    elif action == "show_card":
                        ui_comm.show_card_signal.emit(*args)
                    elif action == "show_quicklook":
                        ui_comm.show_quicklook_signal.emit(*args)
                    elif action == "modify_widget":
                        ui_comm.modify_widget_state_signal.emit(*args)
                except Exception:
                    pass

        dead_connections = []
        async with self._lock:
            for connection in self.active_connections:
                try:
                    await connection.send_json(message)
                except (WebSocketDisconnect, RuntimeError):
                    dead_connections.append(connection)
            
            for connection in dead_connections:
                self.disconnect(connection)

manager = ConnectionManager()

# ==========================================
# ENDPOINTS REST
# ==========================================
@app.get("/")
def read_root():
    return {"status": "Miku OpenClaw Gateway Online", "auth_required": True}

@app.post("/api/stop")
async def stop_endpoint(api_key: str = Security(get_api_key)):
    from audio_handler import stop_speaking
    stop_speaking()
    
    from agents import agent_manager
    agent_manager.cancel_all()
    
    await manager.broadcast_message({"type": "ui_command", "action": "status_update", "text": "Idle"})
    return {"status": "stopped"}

@app.post("/api/speech/stop")
async def stop_speech_endpoint():
    """Detiene inmediatamente cualquier audio o sintetizador de voz en ejecución."""
    from audio_handler import stop_speaking
    stop_speaking()
    return {"status": "speech_stopped"}

@app.get("/history")
def get_history(api_key: str = Security(get_api_key)):
    return {"messages": get_chat_history()}

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest, api_key: str = Security(get_api_key)):
    user_input = req.message
    source = req.source
    is_miku = (req.agent_id == "miku")
    is_silent = req.silent or not is_miku
    logger.info(f"Petición de Texto recibida de {source} [Agente: {req.agent_name} ({req.agent_id})]: {user_input}")
    
    user_msg = {"id": str(int(time.time()*1000)), "text": user_input, "sender": "user", "agent_id": req.agent_id}
    append_to_chat_history(user_msg)
    await manager.broadcast_message(user_msg)
    
    stop_keywords = ["miku detente", "miku para", "detente", "cancela", "para miku", "silencio", "cállate"]
    if any(k in user_input.lower() for k in stop_keywords) and len(user_input) < 40:
        from audio_handler import stop_speaking
        stop_speaking()
        from agents import agent_manager
        agent_manager.cancel_all()
        await manager.broadcast_message({"type": "ui_command", "action": "status_update", "text": "Idle"})
        return ChatResponse(reply="[IGNORAR]", agent_id=req.agent_id, agent_name=req.agent_name)
    
    main_loop = asyncio.get_running_loop()
    def status_callback(status: str):
        try:
            asyncio.run_coroutine_threadsafe(
                manager.broadcast_message({"type": "ui_command", "action": "status_update", "text": status, "agent_id": req.agent_id}),
                main_loop
            )
        except Exception:
            pass

    os.environ["MIKU_CURRENT_SOURCE"] = source
    if is_miku:
        sys_prompt = get_system_prompt(user_input, source=source)
    else:
        custom_instructions = req.agent_prompt.strip() if req.agent_prompt else ""
        mcp_note = f"\nTienes conectado el servidor MCP '{req.agent_mcp}'. Utiliza sus herramientas mcp_{req.agent_mcp}_* prioritariamente para ejecutar tareas de forma autónoma (ej. Pull Requests, inspección de archivos, base de datos)." if req.agent_mcp else ""
        sys_prompt = f"""Eres {req.agent_name}, un agente técnico autónomo y altamente capacitado del ecosistema Miku.
Instrucciones específicas de tu rol:
{custom_instructions if custom_instructions else 'Eres un asistente técnico proactivo. Ejecuta las órdenes técnicas que te asigne el usuario.'}{mcp_note}

REGLAS DE OPERACIÓN:
1. Responde de forma técnica, estructurada, precisa y concisa.
2. NUNCA uses etiquetas de voz <voz> ni hables como mascota kawaii; eres un agente técnico.
3. Eres silencioso (no reproduces audio por altavoces). Tu salida es puramente texto y herramientas.
4. Si se te solicita una acción técnica (como una pull request, ejecutar un comando, revisar código), utiliza las herramientas disponibles a tu alcance y devuelve un resumen concreto y útil de lo ejecutado."""

    response_text = await asyncio.to_thread(
        get_llm_response,
        user_input,
        sys_prompt,
        status_callback,
        None,
        req.agent_id
    )
    
    # Separar voz corta del texto completo (si usa <voz>)
    voice_text, chat_text = extract_voice_text(response_text)
    
    agent_msg = {"id": str(int(time.time()*1000) + 1), "text": chat_text, "sender": req.agent_id, "agent_id": req.agent_id, "agent_name": req.agent_name}
    append_to_chat_history(agent_msg)
    await manager.broadcast_message(agent_msg)
    
    # Imprimir en la terminal para el usuario
    logger.info(f"[{req.agent_name}]: {chat_text}")
    
    if is_miku and not is_silent:
        if source in ("pc", "desktop"):
            if len(manager.active_connections) > 0:
                import threading
                sync_miku_state("talking")
                speech_text = clean_text_for_speech(voice_text)
                threading.Thread(target=speak, args=(speech_text,), daemon=True).start()
        else:
            # Tarea asíncrona para no bloquear la respuesta HTTP instantánea del celular
            async def send_audio_async():
                speech_text = clean_text_for_speech(voice_text)
                audio_path = await generate_full_audio_file(speech_text)
                if audio_path:
                    filename = f"miku_response_{int(time.time())}.mp3"
                    dest_path = os.path.join(tempfile.gettempdir(), filename)
                    shutil.copy2(audio_path, dest_path)
                    audio_url = f"/api/audio_temp/{filename}"
                    await manager.broadcast_message({
                        "type": "ui_command", 
                        "action": "play_audio", 
                        "url": audio_url
                    })
            
            asyncio.create_task(send_audio_async())
    
    return ChatResponse(reply=chat_text, agent_id=req.agent_id, agent_name=req.agent_name)

@app.post("/audio", response_model=ChatResponse)
async def audio_endpoint(file: UploadFile = File(...), api_key: str = Security(get_api_key)):
    logger.info("Petición de Audio (Voz) recibida desde la App.")
    
    # 1. Guardar el archivo temporalmente
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
        shutil.copyfileobj(file.file, temp_audio)
        temp_file_path = temp_audio.name
        
    try:
        # 2. Convertir el audio a texto usando Groq/Whisper
        user_text = audio_handler.transcribe_audio(temp_file_path)
        logger.info(f"Transcripción exitosa: {user_text}")
        
        if not user_text:
            return ChatResponse(reply="[IGNORAR]") # No se detectó voz clara
            
        user_msg = {"id": str(int(time.time()*1000)), "text": user_text, "sender": "user"}
        append_to_chat_history(user_msg)
        await manager.broadcast_message(user_msg)
            
        stop_keywords = ["miku detente", "miku para", "detente", "cancela", "para miku", "silencio", "cállate"]
        if any(k in user_text.lower() for k in stop_keywords) and len(user_text) < 40:
            from audio_handler import stop_speaking
            stop_speaking()
            from agents import agent_manager
            agent_manager.cancel_all()
            await manager.broadcast_message({"type": "ui_command", "action": "status_update", "text": "Idle"})
            return ChatResponse(reply="[IGNORAR]")
            
        # 3. Pasar el texto al cerebro
        main_loop = asyncio.get_running_loop()
        def status_callback(status: str):
            try:
                asyncio.run_coroutine_threadsafe(
                    manager.broadcast_message({"type": "ui_command", "action": "status_update", "text": status}),
                    main_loop
                )
            except Exception:
                pass

        os.environ["MIKU_CURRENT_SOURCE"] = "mobile"
        sys_prompt = get_system_prompt(user_text, source="mobile")
        response_text = await asyncio.to_thread(
            get_llm_response,
            user_text,
            sys_prompt,
            status_callback
        )
        
        miku_msg = {"id": str(int(time.time()*1000) + 1), "text": response_text, "sender": "miku"}
        append_to_chat_history(miku_msg)
        await manager.broadcast_message(miku_msg)
        
        # Imprimir en la terminal para el usuario
        logger.info(f"[Miku]: {response_text}")
        
        # Generar audio y enviarlo a la app
        async def send_audio_async():
            speech_text = clean_text_for_speech(response_text)
            audio_path = await generate_full_audio_file(speech_text)
            if audio_path:
                filename = f"miku_response_{int(time.time())}.mp3"
                dest_path = os.path.join(tempfile.gettempdir(), filename)
                shutil.copy2(audio_path, dest_path)
                audio_url = f"/api/audio_temp/{filename}"
                await manager.broadcast_message({
                    "type": "ui_command", 
                    "action": "play_audio", 
                    "url": audio_url
                })
                
        asyncio.create_task(send_audio_async())
        
        return ChatResponse(reply=response_text)
        
    finally:
        # Limpiez
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

@app.get("/api/audio_temp/{filename}")
async def get_audio_temp(filename: str):
    file_path = os.path.join(tempfile.gettempdir(), filename)
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="audio/mpeg")
    raise HTTPException(status_code=404, detail="Audio file not found")

class BroadcastRequest(BaseModel):
    payload: dict

@app.post("/broadcast_command")
async def broadcast_command(req: BroadcastRequest, api_key: str = Security(get_api_key)):
    await manager.broadcast_message(req.payload)
    return {"status": "ok"}

class IslandNotifyRequest(BaseModel):
    mood: str = "soft"
    bot_state: str = "idle"
    duration: int = 6000
    layout: dict = {}

@app.post("/island_notify")
async def island_notify(req: IslandNotifyRequest, api_key: str = Security(get_api_key)):
    """Push a procedural notification to the Miku Island frontend."""
    payload = {
        "event": "island_notify",
        "mood": req.mood,
        "bot_state": req.bot_state,
        "duration": req.duration,
        "layout": req.layout,
    }
    await manager.broadcast_message(payload)
    return {"status": "ok"}

# ==========================================
# EMPAREJAMIENTO DE DISPOSITIVOS Y MCP AUTH
# ==========================================

MCP_AUTH_REQUESTS = {}

@app.get("/api/mcp/auth_status/{task_id}")
async def get_mcp_auth_status(task_id: str):
    if task_id in MCP_AUTH_REQUESTS:
        return {"status": "ok", "decision": MCP_AUTH_REQUESTS[task_id]}
    return {"status": "pending"}

class MCPAuthResponseRequest(BaseModel):
    action: str

@app.post("/api/mcp/auth_response/{task_id}")
async def post_mcp_auth_response(task_id: str, req: MCPAuthResponseRequest):
    MCP_AUTH_REQUESTS[task_id] = req.action
    await manager.broadcast_message({
        "type": "ui_command",
        "action": "mobile_widget",
        "args": ["none"]
    })
    return {"status": "ok"}

class PairInitRequest(BaseModel):
    session_id: str

@app.post("/api/pair/init")
async def pair_init(req: PairInitRequest):
    global PAIRING_SESSION
    # En producción este endpoint debería estar protegido, pero por simplicidad de UI local
    PAIRING_SESSION = req.session_id
    return {"status": "ok"}

class PairConfirmRequest(BaseModel):
    session_id: str
    device_id: str
    name: str
    public_key: str

@app.post("/api/pair/confirm")
async def pair_confirm(req: PairConfirmRequest):
    global PAIRING_SESSION
    if PAIRING_SESSION is None or req.session_id != PAIRING_SESSION:
        raise HTTPException(status_code=403, detail="Sesión inválida o expirada")
        
    miku_db.add_device(req.device_id, req.name, req.public_key)
    PAIRING_SESSION = None # Consumir
    
    # Avisar a la interfaz web
    if manager:
        asyncio.create_task(manager.broadcast_message({"type": "ui_command", "action": "miku_link_connected", "text": req.name}))
        
    server_pub = miku_db.get_server_public_key_b64()
    return {"status": "ok", "server_public_key": server_pub}

# ==========================================
# FUNCIONES DE DISPOSITIVO VINCULADO
# ==========================================

@app.post("/api/device/lock")
async def device_lock(x_device_id: str = Header(None)):
    if not miku_db.is_valid_device(x_device_id):
        raise HTTPException(status_code=403, detail="Dispositivo no autorizado")
    
    # Bloquear PC
    try:
        import ctypes
        ctypes.windll.user32.LockWorkStation()
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Error bloqueando PC: {e}")
        raise HTTPException(status_code=500, detail="Error interno")

@app.post("/api/device/upload")
async def device_upload(file: UploadFile = File(...), x_device_id: str = Header(None)):
    if not miku_db.is_valid_device(x_device_id):
        raise HTTPException(status_code=403, detail="Dispositivo no autorizado")
        
    downloads_path = os.path.join(os.path.expanduser('~'), 'Downloads', 'miku-link')
    os.makedirs(downloads_path, exist_ok=True)
    file_path = os.path.join(downloads_path, file.filename)
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())
        
    # Avisar a Miku (broadcast WS) para que muestre el QuickLook y la notificación
    abs_path = os.path.abspath(file_path)
    
    await manager.broadcast_message({
        "type": "ui_command",
        "action": "show_info",
        "args": ["Archivo Recibido", f"Se recibió {file.filename} desde tu celular."]
    })
    
    await manager.broadcast_message({
        "type": "ui_command",
        "action": "show_quicklook",
        "args": [abs_path]
    })
    
    return {"status": "ok", "filename": file.filename}


class ClipboardRequest(BaseModel):
    text: str

class PhoneDownloadRequest(BaseModel):
    filename: str

class SecretRequest(BaseModel):
    secrets: dict[str, str]

@app.post("/api/secrets")
async def save_secret(req: SecretRequest, api_key: str = Security(get_api_key)):
    try:
        from dotenv import set_key
        env_path = os.path.join(os.path.dirname(__file__), ".env")
        if not os.path.exists(env_path):
            with open(env_path, "w") as f: pass
        
        for k, v in req.secrets.items():
            set_key(env_path, k, v)
            os.environ[k] = v
            
        return {"status": "ok", "message": f"{len(req.secrets)} secretos guardados."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/desktop/info")
async def get_desktop_info():
    import socket
    local_ip = "127.0.0.1"
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        try:
            local_ip = socket.gethostbyname(socket.gethostname())
        except Exception:
            pass
    return {"hostname": socket.gethostname(), "ip": local_ip}

# ==========================================
# CONFIGURACIÓN DE API KEYS Y MODELOS
# ==========================================
MANAGED_KEYS = [
    "GROQ_API_KEY",
    "GEMINI_API_KEY",
    "GOOGLE_CLOUD_PROJECT",
    "GOOGLE_CLOUD_LOCATION",
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "NVIDIA_API_KEY",
    "ELEVENLABS_API_KEY",
    "SPOTIFY_CLIENT_ID",
    "SPOTIFY_CLIENT_SECRET",
    "SPOTIFY_REDIRECT_URI",
    "MIKU_API_KEY",
]

def mask_key(value: str) -> str:
    """Enmascara una API key para mostrar solo los últimos 4 caracteres."""
    if not value or len(value) <= 4:
        return "****"
    return "*" * (len(value) - 4) + value[-4:]

@app.get("/api/config/keys")
async def get_config_keys(api_key: str = Security(get_api_key)):
    """Devuelve las API keys configuradas (enmascaradas por seguridad)."""
    keys = {}
    for key_name in MANAGED_KEYS:
        value = os.getenv(key_name, "")
        keys[key_name] = {
            "value_masked": mask_key(value) if value else "",
            "is_set": bool(value),
        }
    return {"keys": keys}

class UpdateKeysRequest(BaseModel):
    keys: dict  # {"GROQ_API_KEY": "new_value", ...}

@app.post("/api/config/keys")
async def update_config_keys(req: UpdateKeysRequest, api_key: str = Security(get_api_key)):
    """Actualiza las API keys en el archivo .env y recarga las variables de entorno."""
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    
    existing_lines = []
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            existing_lines = f.readlines()
    
    updated_keys = set()
    new_lines = []
    for line in existing_lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            key_name = stripped.split("=", 1)[0].strip()
            if key_name in req.keys and key_name in MANAGED_KEYS:
                new_value = req.keys[key_name]
                if new_value and not new_value.startswith("*"):
                    new_lines.append(f"{key_name}={new_value}\n")
                    os.environ[key_name] = new_value
                    updated_keys.add(key_name)
                    continue
        new_lines.append(line)
    
    for key_name, new_value in req.keys.items():
        if key_name in MANAGED_KEYS and key_name not in updated_keys:
            if new_value and not new_value.startswith("*"):
                new_lines.append(f"{key_name}={new_value}\n")
                os.environ[key_name] = new_value
    
    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    
    try:
        import importlib
        import config
        importlib.reload(config)
    except Exception:
        pass
    
    return {"status": "ok", "message": "Configuración de claves actualizada."}

@app.delete("/api/config/keys/{key_name}")
async def delete_config_key(key_name: str, api_key: str = Security(get_api_key)):
    """Elimina una API key del archivo .env y del entorno de ejecución con confirmación."""
    if key_name not in MANAGED_KEYS:
        raise HTTPException(status_code=400, detail="Clave no gestionada")
    
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    existing_lines = []
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            existing_lines = f.readlines()
            
    new_lines = []
    for line in existing_lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            k = stripped.split("=", 1)[0].strip()
            if k == key_name:
                continue
        new_lines.append(line)
        
    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
        
    if key_name in os.environ:
        del os.environ[key_name]
        
    try:
        import importlib
        import config
        importlib.reload(config)
    except Exception:
        pass
        
    logger.info(f"API key eliminada: {key_name}")
    return {"status": "ok", "deleted": key_name, "message": f"Clave {key_name} eliminada con éxito."}

@app.get("/api/elevenlabs/voices")
async def get_elevenlabs_voices():
    """Obtiene la lista de voces disponibles en ElevenLabs si hay API Key."""
    key = os.getenv("ELEVENLABS_API_KEY", "")
    if not key:
        return {"status": "error", "message": "No hay ELEVENLABS_API_KEY configurada", "voices": []}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://api.elevenlabs.io/v1/voices",
                headers={"xi-api-key": key}
            )
            if resp.status_code == 200:
                data = resp.json()
                voices = []
                for v in data.get("voices", []):
                    voices.append({
                        "id": v.get("voice_id"),
                        "name": v.get("name"),
                        "category": v.get("category", ""),
                        "preview_url": v.get("preview_url", "")
                    })
                return {"status": "ok", "voices": voices}
            return {"status": "error", "message": f"Error ElevenLabs: {resp.status_code}", "voices": []}
    except Exception as e:
        return {"status": "error", "message": str(e), "voices": []}

# ==========================================
# CONFIGURACIÓN DE MODELOS (ROUTER)
# ==========================================
MODELS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models_config.json")

AVAILABLE_MODELS = {
    "chat": [
        {"id": "gemini-flash-lite-latest", "name": "Gemini Flash Lite (Recomendado - Rápido)", "provider": "google"},
        {"id": "gemini-3.8-flash", "name": "Gemini 3.8 Flash (Google AI Studio)", "provider": "google"},
        {"id": "gemini-3.5-flash", "name": "Gemini 3.5 Flash (Google AI Studio)", "provider": "google"},
        {"id": "gemini-2.5-pro", "name": "Gemini 2.5 Pro (Razonamiento Complejo)", "provider": "google"},
        {"id": "gemini-2.5-flash", "name": "Gemini 2.5 Flash (Vertex AI)", "provider": "google"},
        {"id": "llama-3.3-70b-versatile", "name": "Llama 3.3 70B (Groq - Ultra Veloz)", "provider": "groq"},
        {"id": "openai/gpt-oss-120b", "name": "GPT-OSS 120B (Groq)", "provider": "groq"},
        {"id": "claude-3-5-sonnet-20241022", "name": "Claude 3.5 Sonnet (Recomendado Código)", "provider": "anthropic"},
        {"id": "gpt-4o", "name": "GPT-4o (OpenAI)", "provider": "openai"},
        {"id": "gpt-4o-mini", "name": "GPT-4o Mini (OpenAI)", "provider": "openai"},
    ],
    "computer_use": [
        {"id": "gemini-3.5-flash", "name": "Gemini 3.5 Flash (Visión y Pantalla - Recomendado)", "provider": "google"},
        {"id": "gemini-2.5-computer-use-preview-10-2025", "name": "Gemini 2.5 Computer Use (Vertex AI)", "provider": "google"},
        {"id": "gemini-2.5-pro", "name": "Gemini 2.5 Pro (Vertex AI)", "provider": "google"},
        {"id": "claude-3-5-sonnet-20241022", "name": "Claude 3.5 Sonnet (Computer Use)", "provider": "anthropic"},
        {"id": "gpt-4o", "name": "GPT-4o (OpenAI)", "provider": "openai"},
    ],
    "stt": [
        {"id": "whisper-large-v3", "name": "Whisper Large v3 (Groq - Recomendado)", "provider": "groq"},
        {"id": "whisper-large-v3-turbo", "name": "Whisper Large v3 Turbo (Groq)", "provider": "groq"},
        {"id": "whisper-1", "name": "Whisper v1 (OpenAI)", "provider": "openai"},
    ]
}

def get_active_providers():
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    env_keys = {}
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if stripped and not stripped.startswith("#") and "=" in stripped:
                    k, v = stripped.split("=", 1)
                    env_keys[k.strip()] = v.strip().strip('"').strip("'")
    active = set()
    if env_keys.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY"):
        active.add("groq")
    if env_keys.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY") or env_keys.get("GOOGLE_CLOUD_PROJECT") or os.getenv("GOOGLE_CLOUD_PROJECT"):
        active.add("google")
    if env_keys.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY"):
        active.add("openai")
    if env_keys.get("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_API_KEY"):
        active.add("anthropic")
    if env_keys.get("NVIDIA_API_KEY") or os.getenv("NVIDIA_API_KEY"):
        active.add("nvidia")
    return active

@app.get("/api/config/models")
async def get_models_config():
    current = {"chat": "gemini-2.5-pro", "computer_use": "gemini-3.5-flash", "stt": "whisper-large-v3"}
    if os.path.exists(MODELS_FILE):
        try:
            with open(MODELS_FILE, "r", encoding="utf-8") as f:
                current.update(json.load(f))
        except Exception as e:
            logger.error(f"Error reading models_config.json: {e}")
            
    active_providers = get_active_providers()
    filtered_available = {}
    for cat, models in AVAILABLE_MODELS.items():
        eligible = [m for m in models if m.get("provider") in active_providers]
        filtered_available[cat] = eligible
        if eligible:
            eligible_ids = [m["id"] for m in eligible]
            if current.get(cat) not in eligible_ids:
                current[cat] = eligible_ids[0]
        else:
            current[cat] = ""

    return {
        "current": current,
        "available": filtered_available,
        "active_providers": list(active_providers),
        "has_providers": len(active_providers) > 0
    }

class UpdateModelsRequest(BaseModel):
    chat: Optional[str] = None
    computer_use: Optional[str] = None
    stt: Optional[str] = None

@app.post("/api/config/models")
async def update_models_config(req: UpdateModelsRequest):
    current = {"chat": "gemini-2.5-pro", "computer_use": "gemini-3.5-flash", "stt": "whisper-large-v3"}
    if os.path.exists(MODELS_FILE):
        try:
            with open(MODELS_FILE, "r", encoding="utf-8") as f:
                current.update(json.load(f))
        except Exception:
            pass
    if req.chat:
        current["chat"] = req.chat
    if req.computer_use:
        current["computer_use"] = req.computer_use
    if req.stt:
        current["stt"] = req.stt
    with open(MODELS_FILE, "w", encoding="utf-8") as f:
        json.dump(current, f, indent=2, ensure_ascii=False)
    return {"status": "ok", "current": current}

# ==========================================
# GESTIÓN Y MONITOREO DE MÚSICA / SPOTIFY
# ==========================================
LAST_MUSIC_STATE = {
    "title": "Sin reproducción",
    "artist": "—",
    "playing": False,
    "cover": "",
    "pos": 0,
    "dur": 0,
    "vol": 50
}

def get_current_spotify_status_sync() -> dict:
    global LAST_MUSIC_STATE
    try:
        import tools_spotify
        if not tools_spotify.sp:
            tools_spotify.init_spotify()
        if tools_spotify.sp:
            playback = tools_spotify.sp.current_playback()
            if playback and playback.get("item"):
                item = playback["item"]
                is_playing = bool(playback.get("is_playing", False))
                title = item.get("name", "Desconocido")
                artists = ", ".join([a["name"] for a in item.get("artists", [])]) or "Artista"
                images = item.get("album", {}).get("images", [])
                cover = images[0]["url"] if images else ""
                progress_ms = playback.get("progress_ms") or 0
                duration_ms = item.get("duration_ms") or 0
                device_vol = playback.get("device", {}).get("volume_percent", 50)
                
                state = {
                    "title": title,
                    "artist": artists,
                    "playing": is_playing,
                    "cover": cover,
                    "pos": round(progress_ms / 1000, 1),
                    "dur": round(duration_ms / 1000, 1),
                    "vol": device_vol
                }
                LAST_MUSIC_STATE = state
                return state
    except Exception:
        pass
    return LAST_MUSIC_STATE

async def spotify_media_loop():
    """Monitorea Spotify periódicamente y notifica a la interfaz dinámica si la canción o estado cambia."""
    last_sig = ""
    while True:
        try:
            status = await asyncio.to_thread(get_current_spotify_status_sync)
            current_sig = f"{status.get('title')}|{status.get('artist')}|{status.get('playing')}"
            if current_sig != last_sig:
                last_sig = current_sig
                await manager.broadcast_message({
                    "type": "ui_command",
                    "action": "music",
                    "args": status
                })
        except Exception:
            pass
        await asyncio.sleep(2.5)

@app.get("/api/media/status")
async def get_media_status():
    status = await asyncio.to_thread(get_current_spotify_status_sync)
    return status

class MediaControlRequest(BaseModel):
    action: str
    param: Optional[Any] = None

@app.post("/api/media/control")
async def control_media_endpoint(req: MediaControlRequest):
    action = req.action.lower().strip()
    
    def _do_control():
        success = False
        try:
            import tools_spotify
            if not tools_spotify.sp:
                tools_spotify.init_spotify()
            
            res = None
            if action in ["play", "start"]:
                res = tools_spotify.controlar_spotify("play")
            elif action in ["pause", "stop"]:
                res = tools_spotify.controlar_spotify("pause")
            elif action == "toggle":
                cur = tools_spotify.sp.current_playback() if tools_spotify.sp else None
                if cur and cur.get("is_playing"):
                    res = tools_spotify.controlar_spotify("pause")
                else:
                    res = tools_spotify.controlar_spotify("play")
            elif action in ["next", "fwd"]:
                res = tools_spotify.controlar_spotify("next")
            elif action in ["previous", "prev", "back"]:
                res = tools_spotify.controlar_spotify("previous")
            elif action in ["vol", "volume"] and req.param is not None:
                res = tools_spotify.cambiar_volumen_spotify(int(req.param))
            else:
                res = tools_spotify.controlar_spotify(action)
            
            if res and not str(res).lower().startswith("error"):
                success = True
        except Exception as e:
            logger.warning(f"Spotify API control failed: {e}")
            success = False

        if not success:
            VK_MEDIA_NEXT_TRACK = 0xB0
            VK_MEDIA_PREV_TRACK = 0xB1
            VK_MEDIA_PLAY_PAUSE = 0xB3
            key = None
            if action in ["toggle", "play", "pause"]:
                key = VK_MEDIA_PLAY_PAUSE
            elif action in ["next", "fwd"]:
                key = VK_MEDIA_NEXT_TRACK
            elif action in ["previous", "prev", "back"]:
                key = VK_MEDIA_PREV_TRACK
            if action in ["vol", "volume"] and req.param is not None:
                try:
                    vol_val = max(0, min(100, int(req.param)))
                    from pycaw.pycaw import AudioUtilities, ISimpleAudioVolume, IAudioEndpointVolume
                    from ctypes import cast, POINTER
                    from comtypes import CLSCTX_ALL
                    sessions = AudioUtilities.GetAllSessions()
                    found = False
                    for s in sessions:
                        if s.Process and "spotify" in s.Process.name().lower():
                            v = s._ctl.QueryInterface(ISimpleAudioVolume)
                            v.SetMasterVolume(vol_val / 100.0, None)
                            found = True
                    if not found:
                        devices = AudioUtilities.GetSpeakers()
                        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                        master_vol = cast(interface, POINTER(IAudioEndpointVolume))
                        master_vol.SetMasterVolumeLevelScalar(vol_val / 100.0, None)
                    logger.info(f"[Media] Volumen ajustado a {vol_val}% vía pycaw")
                except Exception as ex:
                    logger.warning(f"[Media] Falló ajuste de volumen pycaw: {ex}")
            elif key:
                ctypes.windll.user32.keybd_event(key, 0, 0, 0)
                ctypes.windll.user32.keybd_event(key, 0, 2, 0)
                logger.info(f"[Media] Simulado atajo multimedia Windows para acción '{action}'")

    await asyncio.to_thread(_do_control)
    await asyncio.sleep(0.3)
    new_status = await asyncio.to_thread(get_current_spotify_status_sync)
    await manager.broadcast_message({
        "type": "ui_command",
        "action": "music",
        "args": new_status
    })
    return {"status": "ok", "current": new_status}

class SettingUpdateRequest(BaseModel):
    key: str
    value: Any

@app.post("/api/setting")
async def update_setting(req: SettingUpdateRequest):
    """Sincroniza ajustes en vivo entre la UI y el backend."""
    import prompt_manager
    if req.key == "voice_volume":
        try:
            audio_handler.set_voice_volume(int(req.value))
        except Exception as e:
            logger.warning(f"Error fijando volumen de voz: {e}")
    elif req.key == "personality":
        try:
            prompt_manager.set_personality_preset(str(req.value))
            logger.info(f"Personalidad actualizada a: {req.value}")
        except Exception as e:
            logger.warning(f"Error actualizando personalidad: {e}")
    elif req.key == "lang":
        try:
            prompt_manager.set_language(str(req.value))
            logger.info(f"Idioma del sistema actualizado a: {req.value}")
        except Exception as e:
            logger.warning(f"Error actualizando idioma: {e}")
    else:
        try:
            prompt_manager.save_setting_key(req.key, req.value)
        except Exception as e:
            logger.warning(f"Error guardando ajuste {req.key}: {e}")
    return {"status": "ok", "key": req.key, "value": req.value}

@app.post("/api/hook")
async def receive_agent_hook(request: Request):
    """Recibe eventos de agentes CLI (Claude Code, Cursor, Codex, Antigravity) estilo Coucou."""
    try:
        payload = await request.json()
    except Exception:
        payload = {}
    event_name = payload.get("hook_event_name", payload.get("event", "Notification"))
    agent_name = payload.get("coucou_agent", payload.get("agent", "claude"))
    prompt = payload.get("prompt", payload.get("message", ""))
    tool_name = payload.get("tool_name", payload.get("tool", ""))
    
    logger.info(f"[Hook] Agente '{agent_name}' -> Evento: {event_name}")
    
    # Notificar a la Isla vía WebSocket
    await manager.broadcast_message({
        "type": "agent_hook",
        "agent": agent_name,
        "event": event_name,
        "prompt": prompt,
        "tool": tool_name,
        "payload": payload
    })
    return {"status": "ok", "received": event_name}

class FileDropRequest(BaseModel):
    path: Optional[str] = None
    filename: Optional[str] = None

@app.post("/api/desktop/file_drop")
async def desktop_file_drop(req: FileDropRequest):
    """Maneja un archivo soltado en la interfaz dinámica."""
    try:
        if req.path and os.path.exists(req.path):
            filename = os.path.basename(req.path)
            content_preview = ""
            try:
                if os.path.getsize(req.path) < 50000:
                    with open(req.path, "r", encoding="utf-8", errors="ignore") as f:
                        content_preview = f.read(2000)
            except Exception:
                pass
            if not content_preview:
                content_preview = f"Archivo: {filename}\nRuta: {req.path}\nTamaño: {os.path.getsize(req.path)} bytes"
                
            await manager.broadcast_message({
                "type": "ui_command",
                "action": "show_quicklook",
                "args": [req.path, content_preview]
            })
            return {"status": "ok", "filename": filename, "path": req.path}
        return {"status": "error", "message": "Ruta no encontrada"}
    except Exception as e:
        logger.error(f"Error en desktop_file_drop: {e}")
        return {"status": "error", "message": str(e)}

# ==========================================
# CONFIGURACIÓN DE SERVIDORES MCP
# ==========================================
MCP_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mcp_config.json")

@app.get("/api/config/mcp")
async def get_mcp_config():
    from mcp_client import mcp_manager
    servers = {}
    if os.path.exists(MCP_FILE):
        try:
            with open(MCP_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                servers = data.get("servidores", {})
        except Exception as e:
            logger.error(f"Error reading mcp_config.json: {e}")
            
    result = []
    for name, srv in servers.items():
        is_connected = name in mcp_manager.sessions
        tools = [t for t in mcp_manager.tools_schema_extension if t["function"]["name"].startswith(f"mcp_{name}_")]
        result.append({
            "name": name,
            "command": srv.get("command", ""),
            "args": srv.get("args", []),
            "connected": is_connected,
            "tools_count": len(tools)
        })
    return {"servers": result}

class AddMcpRequest(BaseModel):
    name: str
    command: str
    args: list[str] = []

@app.post("/api/config/mcp")
async def add_mcp_server(req: AddMcpRequest):
    servers = {}
    if os.path.exists(MCP_FILE):
        try:
            with open(MCP_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                servers = data.get("servidores", {})
        except Exception:
            pass
    servers[req.name] = {"command": req.command, "args": req.args}
    with open(MCP_FILE, "w", encoding="utf-8") as f:
        json.dump({"servidores": servers}, f, indent=2, ensure_ascii=False)
    return {"status": "ok", "message": f"Servidor MCP '{req.name}' guardado."}

@app.delete("/api/config/mcp/{name}")
async def delete_mcp_server(name: str):
    servers = {}
    if os.path.exists(MCP_FILE):
        try:
            with open(MCP_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                servers = data.get("servidores", {})
        except Exception:
            pass
    if name in servers:
        del servers[name]
        with open(MCP_FILE, "w", encoding="utf-8") as f:
            json.dump({"servidores": servers}, f, indent=2, ensure_ascii=False)
        return {"status": "ok", "message": f"Servidor MCP '{name}' eliminado."}
    return {"status": "not_found", "message": f"Servidor MCP '{name}' no encontrado."}

# ==========================================
# CONFIGURACIÓN DE ALERTAS PROACTIVAS
# ==========================================
ALERTS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "alerts_config.json")

DEFAULT_ALERTS = {}

@app.get("/api/config/alerts")
async def get_alerts_config():
    if os.path.exists(ALERTS_FILE):
        try:
            with open(ALERTS_FILE, "r", encoding="utf-8") as f:
                return {"alerts": json.load(f)}
        except Exception as e:
            logger.error(f"Error reading alerts_config.json: {e}")
    return {"alerts": {}}

class UpdateAlertsRequest(BaseModel):
    alerts: dict

@app.post("/api/config/alerts")
async def update_alerts_config(req: UpdateAlertsRequest):
    os.makedirs(os.path.dirname(ALERTS_FILE), exist_ok=True)
    with open(ALERTS_FILE, "w", encoding="utf-8") as f:
        json.dump(req.alerts, f, indent=2, ensure_ascii=False)
    return {"status": "ok", "alerts": req.alerts}

KNOWN_DETECTABLE_APPS = [
    {
        "id": "vscode",
        "name": "Visual Studio Code",
        "process": "code.exe",
        "category": "trabajo",
        "icon": '<svg viewBox="0 0 24 24" fill="#007ACC"><path d="M23.15 2.587L18.21.21a1.494 1.494 0 0 0-1.705.29l-9.46 8.63-4.12-3.128a.999.999 0 0 0-1.276.057L.327 7.261A1 1 0 0 0 .32 8.697L3.9 12 .32 15.303a1 1 0 0 0 .007 1.436l1.322 1.202a.999.999 0 0 0 1.276.057l4.12-3.128 9.46 8.63a1.492 1.492 0 0 0 1.704.29l4.942-2.377A1.5 1.5 0 0 0 24 20.06V3.939a1.5 1.5 0 0 0-.85-1.352z"/></svg>'
    },
    {
        "id": "discord",
        "name": "Discord",
        "process": "discord.exe",
        "category": "ocio",
        "icon": '<svg viewBox="0 0 24 24" fill="#5865F2"><path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028c.462-.63.874-1.295 1.226-1.994.021-.041.001-.09-.041-.106a13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.929 1.793 8.18 1.793 12.061 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.894.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.028zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.955-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.946 2.418-2.157 2.418z"/></svg>'
    },
    {
        "id": "chrome",
        "name": "Google Chrome",
        "process": "chrome.exe",
        "category": "navegador",
        "icon": '<svg viewBox="0 0 24 24"><path fill="#EA4335" d="M12 2C6.48 2 2 6.48 2 12c0 2.85 1.2 5.42 3.12 7.24L8.7 13.5A5.5 5.5 0 0 1 12 6.5h9.72A9.97 9.97 0 0 0 12 2z"/><path fill="#4285F4" d="M12 6.5A5.5 5.5 0 0 1 17.5 12c0 .88-.21 1.71-.58 2.45l5.22 3.01C23.28 15.74 24 13.96 24 12c0-5.52-4.48-10-10-10H12v4.5z"/><path fill="#FBBC05" d="M12 17.5a5.5 5.5 0 0 1-4.76-2.75L1.86 17.9A9.97 9.97 0 0 0 12 22c4.05 0 7.57-2.41 9.14-5.88L15.92 13.1A5.48 5.48 0 0 1 12 17.5z"/><circle fill="#FFF" cx="12" cy="12" r="3.8"/><circle fill="#1A73E8" cx="12" cy="12" r="3"/></svg>'
    },
    {
        "id": "spotify",
        "name": "Spotify",
        "process": "spotify.exe",
        "category": "ocio",
        "icon": '<svg viewBox="0 0 24 24" fill="#1DB954"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.65 14.65c-.2.32-.6.41-.92.21-2.52-1.54-5.7-1.89-9.44-1.04-.37.08-.73-.15-.81-.52-.08-.37.15-.73.52-.81 4.1-.94 7.62-.53 10.44 1.19.32.2.41.6.21.97zm1.23-2.74c-.25.4-.77.53-1.17.28-2.88-1.77-7.28-2.28-10.69-1.25-.45.14-.93-.12-1.07-.57-.14-.45.12-.93.57-1.07 3.9-1.18 8.76-.61 12.08 1.44.4.25.53.77.28 1.17zm.11-2.86c-3.46-2.05-9.17-2.24-12.49-1.23-.53.16-1.09-.14-1.25-.67-.16-.53.14-1.09.67-1.25 3.82-1.16 10.12-.94 14.11 1.43.48.28.63.89.35 1.37-.29.48-.9.63-1.39.35z"/></svg>'
    },
    {
        "id": "steam",
        "name": "Steam / Juegos",
        "process": "steam.exe",
        "category": "juego",
        "icon": '<svg viewBox="0 0 24 24" fill="#171A21"><path d="M12 2a10 10 0 0 0-10 10c0 4.74 3.31 8.7 7.74 9.71l2.58-3.73a3.54 3.54 0 0 1-.32-.22l-3.32-1.37a2.5 2.5 0 1 1 2.3-4.22l3.35 1.38c.45-.16.94-.25 1.45-.25a3.75 3.75 0 1 1 0 7.5c-.32 0-.63-.04-.93-.11l-2.6 3.76A10 10 0 1 0 12 2z"/></svg>'
    },
    {
        "id": "telegram",
        "name": "Telegram",
        "process": "telegram.exe",
        "category": "ocio",
        "icon": '<svg viewBox="0 0 24 24" fill="#24A1DE"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.64 6.8c-.15 1.58-.8 5.42-1.13 7.19-.14.75-.42 1-.68 1.03-.58.05-1.02-.38-1.58-.75-.88-.58-1.38-.94-2.23-1.5-.99-.65-.35-1.01.22-1.59.15-.15 2.71-2.48 2.76-2.69a.2.2 0 0 0-.05-.18c-.06-.05-.14-.03-.21-.02-.09.02-1.49.95-4.22 2.79-.4.27-.76.41-1.08.4-.36-.01-1.04-.2-1.55-.37-.63-.2-1.12-.31-1.08-.66.02-.18.27-.36.75-.55 2.92-1.27 4.86-2.11 5.83-2.51 2.78-1.16 3.35-1.36 3.73-1.36.08 0 .27.02.39.12.1.08.13.19.14.27-.01.06.01.24 0 .37z"/></svg>'
    },
    {
        "id": "edge",
        "name": "Microsoft Edge",
        "process": "msedge.exe",
        "category": "navegador",
        "icon": '<svg viewBox="0 0 24 24" fill="#0078D7"><path d="M21.95 12.87c-.17-.79-.53-1.53-1.05-2.17-.78-.96-1.89-1.58-3.13-1.74-.75-.1-1.5.02-2.18.35-.45.22-.85.52-1.18.89l-.27.31c.32-1.37.15-2.82-.48-4.08-.66-1.31-1.74-2.35-3.04-2.93-1.34-.6-2.84-.67-4.22-.21C5.07 3.76 3.86 4.7 3.01 5.95 2.16 7.2 1.7 8.68 1.7 10.18c0 .88.16 1.75.48 2.58.46 1.21 1.28 2.25 2.36 2.99 1.13.78 2.48 1.2 3.86 1.2h.85c.34 0 .68-.03 1.01-.1.49-.1.97-.27 1.41-.5l.39-.22c-.64.44-1.38.74-2.16.88-1.07.19-2.18.06-3.18-.38-.63-.28-1.19-.69-1.63-1.21-.43-.5-.73-1.1-.88-1.73l-.06-.31c.42.59.97 1.07 1.61 1.4.74.38 1.57.57 2.4.55h.35c.81-.03 1.6-.24 2.32-.61.7-.36 1.3-.87 1.77-1.49.5-.66.83-1.43.96-2.25.13-.81.04-1.64-.26-2.4-.23-.59-.59-1.12-1.04-1.54l-.4-.34c.59.04 1.16.23 1.67.55.51.32.93.76 1.24 1.28.32.54.5 1.15.53 1.77.03.62-.09 1.24-.35 1.81-.22.48-.54.91-.94 1.25l-.39.29c.47-.2.89-.48 1.25-.83.47-.46.82-1.03 1.02-1.66.2-.62.24-1.28.12-1.92z"/></svg>'
    },
    {
        "id": "valorant",
        "name": "Valorant / Riot Games",
        "process": "valorant.exe",
        "category": "juego",
        "icon": '<svg viewBox="0 0 24 24" fill="#FF4655"><path d="M4.092 12.012L0 15.932 6.552 24h6.059L4.092 12.012zm15.816-12L10.37 9.544l2.585 3.176L24 0h-4.092z"/></svg>'
    },
    {
        "id": "minecraft",
        "name": "Minecraft",
        "process": "javaw.exe",
        "category": "juego",
        "icon": '<svg viewBox="0 0 24 24" fill="#5E8C31"><path d="M4 2h16a2 2 0 0 1 2 2v16a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2zm2 4v4h4V6H6zm8 0v4h4V6h-4zm-4 6v4h4v-4h-4zm-4 4v2h4v-2H6zm8 0v2h4v-2h-4z"/></svg>'
    }
]

@app.get("/api/apps/detectable")
async def get_detectable_apps():
    """Devuelve las aplicaciones populares e instaladas con sus iconos y categorías."""
    return {"apps": KNOWN_DETECTABLE_APPS}

_EXE_ICON_CACHE = {}

def get_exe_icon_base64(exe_path: str) -> str:
    if not exe_path or not os.path.exists(exe_path):
        return ""
    if exe_path in _EXE_ICON_CACHE:
        return _EXE_ICON_CACHE[exe_path]
    try:
        import ctypes
        import win32ui
        import win32gui
        from PIL import Image
        import io
        import base64

        shell32 = ctypes.windll.shell32
        user32 = ctypes.windll.user32
        hicon = shell32.ExtractIconW(0, exe_path, 0)
        if hicon and hicon > 1:
            hdc = win32ui.CreateDCFromHandle(win32gui.GetDC(0))
            hbmp = win32ui.CreateBitmap()
            hbmp.CreateCompatibleBitmap(hdc, 32, 32)
            hdc_mem = hdc.CreateCompatibleDC()
            hdc_mem.SelectObject(hbmp)
            win32gui.DrawIconEx(hdc_mem.GetHandleOutput(), 0, 0, hicon, 32, 32, 0, 0, 3)
            bmpinfo = hbmp.GetInfo()
            bmpstr = hbmp.GetBitmapBits(True)
            img = Image.frombuffer('RGBA', (bmpinfo['bmWidth'], bmpinfo['bmHeight']), bmpstr, 'raw', 'BGRA', 0, 1)
            buf = io.BytesIO()
            img.save(buf, format='PNG')
            b64 = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
            user32.DestroyIcon(hicon)
            _EXE_ICON_CACHE[exe_path] = b64
            return b64
    except Exception:
        pass
    return ""

KNOWN_APP_INFO = {
    "spotify.exe": ("Spotify", "musica"),
    "zen.exe": ("Zen Browser", "navegador"),
    "chrome.exe": ("Google Chrome", "navegador"),
    "msedge.exe": ("Microsoft Edge", "navegador"),
    "firefox.exe": ("Mozilla Firefox", "navegador"),
    "brave.exe": ("Brave Browser", "navegador"),
    "antigravity ide.exe": ("Antigravity IDE", "desarrollo"),
    "code.exe": ("Visual Studio Code", "desarrollo"),
    "cursor.exe": ("Cursor AI", "desarrollo"),
    "discord.exe": ("Discord", "comunicacion"),
    "steam.exe": ("Steam", "juego"),
    "steamwebhelper.exe": ("Steam", "juego"),
    "valorant.exe": ("Valorant", "juego"),
    "league of legends.exe": ("League of Legends", "juego"),
    "javaw.exe": ("Minecraft", "juego"),
    "robloxplayerbeta.exe": ("Roblox", "juego"),
    "obs64.exe": ("OBS Studio", "multimedia"),
    "vlc.exe": ("VLC Media Player", "multimedia"),
    "figma.exe": ("Figma", "diseño"),
    "notion.exe": ("Notion", "productividad"),
    "telegram.exe": ("Telegram", "comunicacion"),
    "slack.exe": ("Slack", "comunicacion"),
    "ghelper.exe": ("G-Helper", "sistema"),
    "wallpaper64.exe": ("Wallpaper Engine", "personalizacion"),
    "photoshop.exe": ("Adobe Photoshop", "diseño"),
    "illustrator.exe": ("Adobe Illustrator", "diseño"),
    "premiere.exe": ("Adobe Premiere", "diseño"),
    "blender.exe": ("Blender", "diseño")
}

EXCLUDE_PROC_PATTERNS = [
    "service", "helper", "updater", "agent", "tray", "host", "broker", "container",
    "daemon", "server", "sync", "crash", "overlay", "install", "node", "python",
    "cargo", "rustup", "bash", "git", "pyrefly", "smartscreen", "compression",
    "vctip", "presentmon", "psiservice", "search", "runtime", "miku", "session",
    "package", "manager", "crossdevice", "appaction", "appvsh", "registry",
    "shellexperience", "cortana", "ctfmon", "sihost", "conhost", "cmd", "powershell",
    "msmpeng", "nissrv", "monotification", "microsoftedgeupdate", "explorer",
    "msedgewebview", "officeclicktorun"
]

@app.get("/api/apps/running")
async def get_running_apps():
    """Devuelve las aplicaciones de usuario actualmente en ejecución en la PC (filtrando servicios y demonios del sistema)."""
    import psutil
    apps = []
    seen_names = set()

    for p in psutil.process_iter(['name', 'exe']):
        try:
            name = (p.info['name'] or '').strip()
            exe = (p.info['exe'] or '').strip()
            if not name or not exe:
                continue
            name_lower = name.lower()
            if name_lower in seen_names:
                continue
            if "windows\\system32" in exe.lower() or "windows\\syswow64" in exe.lower():
                continue
            
            # 1. Comprobar si es una aplicación conocida
            matched_known = None
            for kname, kinfo in KNOWN_APP_INFO.items():
                if kname in name_lower:
                    matched_known = kinfo
                    break

            if matched_known:
                # Evitar duplicados (ej: Steam vs steamwebhelper)
                if any(a["name"] == matched_known[0] for a in apps):
                    continue
                seen_names.add(name_lower)
                icon_b64 = get_exe_icon_base64(exe)
                apps.append({
                    "id": name_lower.replace(".exe", ""),
                    "name": matched_known[0],
                    "process": name,
                    "exe": exe,
                    "category": matched_known[1],
                    "icon": icon_b64
                })
                continue

            # 2. Si no es conocida, excluir demonios, servicios y herramientas CLI
            clean_token = name_lower.replace(".exe", "")
            if any(bad in clean_token for bad in EXCLUDE_PROC_PATTERNS):
                continue

            seen_names.add(name_lower)
            friendly_name = os.path.splitext(name)[0].replace("_", " ").replace("-", " ").title()
            icon_b64 = get_exe_icon_base64(exe)
            
            apps.append({
                "id": name_lower.replace(".exe", ""),
                "name": friendly_name,
                "process": name,
                "exe": exe,
                "category": "aplicacion",
                "icon": icon_b64
            })
        except Exception:
            continue

    apps.sort(key=lambda a: (0 if a["icon"] else 1, a["name"]))
    return {"apps": apps}


import re

def extract_voice_text(response_text: str) -> tuple[str, str]:
    """Separa el texto para voz del texto para chat.
    Si el LLM usa <voz>mensaje corto</voz>, extrae ese mensaje para TTS
    y limpia las etiquetas del texto que se muestra en el chat.
    Returns: (texto_para_voz, texto_para_chat)
    """
    voz_match = re.search(r"<voz>(.*?)</voz>", response_text, re.DOTALL)
    if voz_match:
        texto_voz = voz_match.group(1).strip()
        texto_chat = re.sub(r"<voz>.*?</voz>", "", response_text, flags=re.DOTALL).strip()
        return texto_voz, texto_chat
    return response_text, response_text

def clean_text_for_speech(text: str) -> str:
    """Elimina markdown, acciones entre asteriscos, y emojis para la síntesis de voz."""
    # Eliminar acciones estilo *sonríe* o *pensando*
    text = re.sub(r'\*[^*]+\*', '', text)
    # Eliminar emojis (rango básico)
    text = re.sub(r'[^\w\s.,!?¿¡\'"áéíóúÁÉÍÓÚñÑ-]', '', text)
    # Limpiar espacios extra
    text = re.sub(r'\s+', ' ', text).strip()
    return text

@app.get("/api/desktop/status")
async def get_desktop_status():
    """Devuelve el estado de salud de todos los servidores MCP y del sistema."""
    from mcp_client import mcp_manager
    import socket, platform, subprocess
    
    mcp_status = []
    for name, config in mcp_manager.servers_config.items():
        is_connected = name in mcp_manager.sessions
        tools_count = len([t for t in mcp_manager.tools_schema_extension if t["function"]["name"].startswith(f"mcp_{name}_")])
        mcp_status.append({
            "name": name,
            "command": config.get("command", ""),
            "connected": is_connected,
            "tools_count": tools_count
        })
    
    # Check if cloudflared is running using tasklist (no external dependencies needed)
    cloudflared_running = False
    try:
        output = subprocess.check_output('tasklist', shell=True, text=True)
        if "cloudflared.exe" in output.lower():
            cloudflared_running = True
    except Exception as e:
        print(f"Error checking cloudflared: {e}")
        cloudflared_running = False
    
    return {
        "hostname": socket.gethostname(),
        "platform": platform.system(),
        "python_version": platform.python_version(),
        "mcp_servers": mcp_status,
        "cloudflared_running": cloudflared_running,
        "websocket_clients": len(manager.active_connections)
    }

@app.get("/api/desktop/wallpaper")
async def get_wallpaper():
    try:
        import ctypes
        SPI_GETDESKWALLPAPER = 0x0073
        buffer = ctypes.create_unicode_buffer(512)
        ctypes.windll.user32.SystemParametersInfoW(SPI_GETDESKWALLPAPER, 512, buffer, 0)
        wallpaper_path = buffer.value
        if os.path.exists(wallpaper_path):
            return FileResponse(wallpaper_path)
    except Exception as e:
        logger.error(f"Error obteniendo wallpaper: {e}")
    return {"status": "error"}

@app.get("/api/desktop/miku_gif/{state}")
async def get_miku_gif(state: str):
    base = os.path.dirname(os.path.abspath(__file__))
    gif_map = {
        "idle": "idle.gif",
        "thinking": "thinking-part1.gif",
        "talking": "TALKING.gif"
    }
    gif_file = gif_map.get(state, "idle.gif")
    path = os.path.join(base, "assets", "animations", gif_file)
    if os.path.exists(path):
        return FileResponse(path)
    return {"status": "error"}

@app.post("/api/desktop/trigger_phone_download")
async def trigger_phone_download(req: PhoneDownloadRequest):
    await manager.broadcast_message({
        "type": "ui_command",
        "action": "download_file",
        "filename": req.filename
    })
    return {"status": "ok"}

@app.post("/api/send_to_phone")
async def send_to_phone_api(file: UploadFile = File(...)):
    """API Endpoint público para enviar cualquier archivo directamente al celular."""
    temp_dir = tempfile.gettempdir()
    file_path = os.path.join(temp_dir, file.filename)
    
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())
        
    await manager.broadcast_message({
        "type": "ui_command",
        "action": "download_file",
        "filename": file.filename
    })
    return {"status": "ok", "message": f"El archivo {file.filename} se está descargando en el celular"}

@app.post("/api/device/clipboard")
async def device_clipboard(req: ClipboardRequest):
    global LAST_CLIPBOARD
    LAST_CLIPBOARD = req.text
    pyperclip.copy(req.text)
    
    return {"status": "ok"}

@app.post("/api/device/clipboard_image")
async def device_clipboard_image(request: Request):
    # Recibir body JSON
    data = await request.json()
    b64_img = data.get("image", "")
    
    try:
        if b64_img.startswith("data:image"):
            b64_img = b64_img.split(",")[1]
            
        img_bytes = base64.b64decode(b64_img)
        img = Image.open(io.BytesIO(img_bytes))
        
        # Para Windows CF_DIB
        output = io.BytesIO()
        img.convert("RGB").save(output, "BMP")
        data_bmp = output.getvalue()[14:]  # Skip 14 bytes bitmap header
        
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data_bmp)
        win32clipboard.CloseClipboard()
        
        # También guardar como archivo por si acaso
        downloads_path = os.path.join(os.path.expanduser('~'), 'Downloads', 'miku-link')
        os.makedirs(downloads_path, exist_ok=True)
        img_path = os.path.join(downloads_path, f"clipboard_{int(time.time())}.png")
        img.save(img_path)
        
        # Lanzar la notificación de QuickLook
        await manager.broadcast_message({
            "type": "ui_command",
            "action": "show_quicklook",
            "args": [os.path.abspath(img_path)]
        })
        
        return {"status": "ok", "path": img_path}
    except Exception as e:
        logger.error(f"Error parseando imagen de portapapeles: {e}")
        return {"status": "error", "detail": str(e)}

@app.get("/api/device/download/{filename}")
async def device_download(filename: str):
    downloads_path = os.path.join(os.path.expanduser('~'), 'Downloads', 'miku-link')
    file_path = os.path.join(downloads_path, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
        
    return FileResponse(file_path, filename=filename)

@app.get("/api/temp_media/{filename}")
async def temp_media_download(filename: str):
    temp_dir = tempfile.gettempdir()
    file_path = os.path.join(temp_dir, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Archivo temporal no encontrado o expirado")
        
    return FileResponse(file_path, filename=filename)

# ==========================================
# ENDPOINTS WEBSOCKET
# ==========================================
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    token = websocket.query_params.get("token")
    logger.info(f"Intento de conexión WS con token: {token}")
    if token != API_KEY:
        logger.warning(f"Conexión WS rechazada. Token esperado: {API_KEY}, recibido: {token}")
        await websocket.close(code=1008)
        return
    logger.info("[WS] Cliente conectado exitosamente.")
    
    # 1. Accept the connection first
    await manager.connect(websocket)
    
    # 2. Send the current clipboard state if available
    if LAST_CLIPBOARD:
        try:
            async with manager._lock:
                await websocket.send_text(json.dumps({
                    "type": "clipboard_update",
                    "text": LAST_CLIPBOARD
                }))
        except Exception as e:
            print(f"Failed to send initial clipboard: {e}")

    # 3. Send current music status if available
    try:
        cur_music = get_current_spotify_status_sync()
        async with manager._lock:
            await websocket.send_text(json.dumps({
                "type": "ui_command",
                "action": "music",
                "args": cur_music
            }))
    except Exception as e:
        pass
    try:
        while True:
            # We don't expect messages from mobile yet, but if they send text (e.g. ping), handle it gracefully
            message = await websocket.receive()
            if message["type"] == "websocket.disconnect":
                break
            elif message["type"] == "websocket.receive":
                text_data = message.get("text")
                if text_data:
                    try:
                        parsed = json.loads(text_data)
                        if parsed.get("type") == "ui_event" and parsed.get("action") == "button_clicked":
                            from ui_events import set_ui_event
                            set_ui_event(parsed.get("data"))
                    except Exception as parse_e:
                        logger.error(f"Error parsing WS message: {parse_e}")
    except (WebSocketDisconnect, RuntimeError, Exception) as e:
        pass
    finally:
        manager.disconnect(websocket)
        logger.info("Cliente Móvil desconectado")

@app.post("/api/ui_event")
async def handle_ui_event(request: Request):
    try:
        data = await request.json()
        if data.get("type") == "ui_event" and data.get("action") == "button_clicked":
            from ui_events import set_ui_event
            val = data.get("data")
            logger.info(f"Received UI event via HTTP: {val}")
            set_ui_event(val)
            return {"status": "ok", "received": val}
    except Exception as e:
        logger.error(f"Error handling /api/ui_event: {e}")
        return {"status": "error", "error": str(e)}
    return {"status": "ignored"}

LAST_CLIPBOARD = ""

def read_clipboard_text():
    try:
        return pyperclip.paste()
    except:
        return None

async def clipboard_monitor():
    global LAST_CLIPBOARD
    while True:
        try:
            # Leer el texto del portapapeles en un hilo separado para NO bloquear el servidor
            current_clipboard = await asyncio.to_thread(read_clipboard_text)
            
            if current_clipboard and current_clipboard != LAST_CLIPBOARD:
                LAST_CLIPBOARD = current_clipboard
                if len(current_clipboard) < 10000:
                    await manager.broadcast_message({
                        "type": "ui_command",
                        "action": "sync_clipboard",
                        "text": current_clipboard
                    })
        except Exception as e:
            pass
        await asyncio.sleep(2.5)

class StdoutHook:
    def __init__(self, original_stdout):
        self.original_stdout = original_stdout
        self.loop = None
        
    def write(self, text):
        try:
            self.original_stdout.write(text)
            self.original_stdout.flush()
        except Exception:
            try:
                self.original_stdout.write(text.encode("ascii", errors="replace").decode("ascii"))
                self.original_stdout.flush()
            except Exception:
                pass
        
        # Interceptar logs del Agente
        if "[Sistema]" in text or "Seleccionando" in text or "Buscando" in text or "Miku ha solicitado" in text:
            clean_text = text.replace("[Sistema]", "").replace("\n", "").strip()
            if clean_text and self.loop and not self.loop.is_closed():
                asyncio.run_coroutine_threadsafe(
                    manager.broadcast_message({
                        "type": "ui_command",
                        "action": "status_update",
                        "text": clean_text
                    }),
                    self.loop
                )
                
    def flush(self):
        try:
            self.original_stdout.flush()
        except Exception:
            pass

async def ui_context_loop():
    last_state = None
    while True:
        try:
            from activity_monitor import get_current_activity
            activity = get_current_activity()
            app = activity.get("app", "")
            process = activity.get("process", "")
            title = activity.get("window_title", "")
            
            ctx = app if app else "Entorno Local"
            
            mode = "compact"
            if process.lower() in ["valorant.exe", "vlc.exe", "netflix.exe", "steamwebhelper.exe", "obs64.exe", "riotclientservices.exe"]:
                mode = "hidden"
            elif "youtube" in title.lower() or "twitch" in title.lower():
                mode = "hidden"
            
            if (ctx, mode) != last_state:
                await manager.broadcast_message({"type": "ui_command", "action": "update_context", "text": ctx})
                await manager.broadcast_message({"type": "ui_command", "action": "set_mode", "text": mode})
                last_state = (ctx, mode)
                
        except Exception:
            pass
        await asyncio.sleep(2)

@app.on_event("startup")
async def startup_event():
    loop = asyncio.get_running_loop()
    sys.stdout = StdoutHook(sys.stdout)
    sys.stdout.loop = loop
    asyncio.create_task(clipboard_monitor())
    asyncio.create_task(ui_context_loop())
    asyncio.create_task(spotify_media_loop())
    
    # Iniciar monitor de actividad del usuario (qué apps usa en el PC)
    try:
        from activity_monitor import start_monitoring
        start_monitoring(interval=30)
        logger.info("Monitor de actividad del usuario iniciado.")
    except Exception as e:
        logger.warning(f"Activity monitor no disponible: {e}")

    # Iniciar túnel de Cloudflare automáticamente si existe el ejecutable
    try:
        cf_local = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cloudflared.exe")
        cf_system = r"C:\Program Files (x86)\cloudflared\cloudflared.exe"
        cf_path = cf_local if os.path.exists(cf_local) else (cf_system if os.path.exists(cf_system) else None)
        
        if cf_path:
            subprocess.Popen(
                [cf_path, "tunnel", "run", "miku"],
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            logger.info("Túnel de Cloudflare iniciado en segundo plano.")
        else:
            logger.info("cloudflared.exe no encontrado (operando en red local).")
    except Exception as e:
        logger.warning(f"Aviso túnel Cloudflare: {e}")
    
    # Inicializar MCP
    try:
        from mcp_client import mcp_manager
        mcp_manager.main_loop = loop
        await mcp_manager.connect_all()
    except Exception as e:
        logger.error(f"Error inicializando MCP: {e}")
        
    from agents import agent_manager
    
    def on_agent_finished(report_text: str):
        async def _handle_agent_finish():
            try:
                # 1. Enviar el reporte del agente al chat para contexto visual
                miku_internal_msg = {"id": str(int(time.time()*1000)), "text": f"[Reporte Interno del Agente]:\n{report_text}", "sender": "miku"}
                append_to_chat_history(miku_internal_msg)
                await manager.broadcast_message(miku_internal_msg)

                # 2. Obtener la respuesta de Miku
                def status_callback(status: str):
                    try:
                        asyncio.run_coroutine_threadsafe(
                            manager.broadcast_message({"type": "ui_command", "action": "status_update", "text": status}),
                            loop
                        )
                    except Exception:
                        pass
                
                # Simulamos que el sistema le pide a Miku que avise al usuario
                simulated_input = f"[INSTRUCCIÓN DEL SISTEMA]: Tu agente de fondo acaba de terminar su tarea. Este es su reporte: '{report_text}'. Escribe un resumen breve y directo para el usuario. IMPORTANTE: NO uses la herramienta 'hablar_al_usuario' para esto, simplemente responde con el texto y el sistema lo hablará automáticamente."
                
                os.environ["MIKU_CURRENT_SOURCE"] = "pc" 
                sys_prompt = get_system_prompt(simulated_input, source="pc")
                
                response_text = await asyncio.to_thread(
                    get_llm_response,
                    simulated_input,
                    sys_prompt,
                    status_callback
                )
                
                if not response_text or "Mensaje bloqueado o nulo" in response_text:
                    logger.warning("El LLM no devolvió una respuesta válida para el callback del agente.")
                    return
                
                # 3. Miku responde (Audio y Texto)
                # Separar voz corta del texto completo (si usa <voz>)
                voice_text, chat_text = extract_voice_text(response_text)
                
                miku_msg = {"id": str(int(time.time()*1000) + 1), "text": chat_text, "sender": "miku"}
                append_to_chat_history(miku_msg)
                await manager.broadcast_message(miku_msg)
                
                logger.info(f"[Miku (Proactiva)]: {chat_text}")
                
                # Reproducir localmente (PC)
                import threading
                try:
                    sync_miku_state("talking")
                except:
                    pass
                speech_text = clean_text_for_speech(voice_text)
                threading.Thread(target=speak, args=(speech_text,), daemon=True).start()

                # Enviar audio a la app móvil
                audio_path = await generate_full_audio_file(clean_text_for_speech(voice_text))
                if audio_path:
                    filename = f"miku_response_{int(time.time())}.mp3"
                    dest_path = os.path.join(tempfile.gettempdir(), filename)
                    import shutil
                    shutil.copy2(audio_path, dest_path)
                    audio_url = f"/api/audio_temp/{filename}"
                    await manager.broadcast_message({
                        "type": "ui_command", 
                        "action": "play_audio", 
                        "url": audio_url
                    })

            except Exception as e:
                logger.error(f"Error en callback proactivo de agente: {e}")
        
        asyncio.run_coroutine_threadsafe(_handle_agent_finish(), loop)
        
    agent_manager.callback = on_agent_finished

def start_fastapi():
    logger.info("Iniciando Miku Gateway API (0.0.0.0:8000)...")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info", access_log=False)

if __name__ == "__main__":
    import threading
    import requests
    
    def pc_mic_worker():
        """Bucle para escuchar la palabra clave y grabar audio en PC."""
        is_asleep_event = threading.Event()
        is_asleep_event.set()
        interrupt_event = threading.Event()
        
        def on_wake():
            logger.info("Palabra clave detectada en PC.")
            stop_speaking()
            interrupt_event.set()
            is_asleep_event.clear()
            
            def handle_wake_conversation():
                try:
                    sync_miku_state("escuchando...")
                    # Grabar audio del usuario con el micrófono y transcribir con Groq Whisper
                    user_text = listen_and_transcribe()
                    if user_text and user_text.strip() not in [".", "", " ", "[IGNORAR]"]:
                        logger.info(f"Usuario dijo: {user_text}")
                        sync_miku_state("thinking")
                        try:
                            requests.post(
                                "http://127.0.0.1:8000/chat",
                                json={"message": user_text, "source": "pc"},
                                headers={"x-api-key": API_KEY},
                                timeout=60
                            )
                        except Exception as chat_err:
                            logger.error(f"Error enviando chat desde PC mic: {chat_err}")
                            sync_miku_state("idle")
                    else:
                        logger.info("No se detectó audio del usuario tras la palabra clave.")
                        sync_miku_state("idle")
                except Exception as e:
                    logger.error(f"Error procesando voz en on_wake: {e}")
                    sync_miku_state("idle")
                finally:
                    time.sleep(1.0)
                    is_asleep_event.set()

            threading.Thread(target=handle_wake_conversation, daemon=True).start()
                
        while True:
            wait_for_wake_word(on_wake, is_asleep_event)
            time.sleep(1)

    def on_barge_in():
        logger.info("Barge-in: interrumpiendo voz de Miku.")

    def on_text_input(text):
        if not text or text.strip() in [".", "", " "]: return
        stop_speaking()
        sync_miku_state("thinking")
        
        def send_req():
            try:
                requests.post("http://127.0.0.1:8000/chat", json={"message": text, "source": "pc"}, headers={"x-api-key": API_KEY})
            except Exception as e:
                logger.error(f"Error chat text: {e}")
        threading.Thread(target=send_req, daemon=True).start()

    set_barge_in_callback(on_barge_in)

    # 1. Iniciar Servidor FastAPI
    t_server = threading.Thread(target=start_fastapi, daemon=True)
    t_server.start()

    # 2. Iniciar Oyente de Micrófono
    t_mic = threading.Thread(target=pc_mic_worker, daemon=True)
    t_mic.start()

    # 3. Mantener el proceso principal vivo (La UI antigua de PyQt se ha desactivado)
    logger.info("Miku Desktop (Headless) iniciado correctamente.")
    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            break
