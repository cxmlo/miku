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
        if sys.stdout is None:
            sys.stdout = open(os.devnull, "w", encoding="utf-8")
        elif hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if sys.stderr is None:
            sys.stderr = open(os.devnull, "w", encoding="utf-8")
        elif hasattr(sys.stderr, 'reconfigure'):
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
import miku_paths
miku_paths.ensure_all_server_folders()

from prompt_manager import get_system_prompt

# Carga diferida (Lazy Loading) de módulos pesados para arranque instantáneo (<500ms)
def get_llm_response(*args, **kwargs):
    from brain import get_llm_response as _impl
    return _impl(*args, **kwargs)

class _LazyAudioHandlerProxy:
    def __getattr__(self, name):
        import audio_handler
        return getattr(audio_handler, name)

audio_handler = _LazyAudioHandlerProxy()

def generate_full_audio_file(*args, **kwargs):
    return audio_handler.generate_full_audio_file(*args, **kwargs)

def speak(*args, **kwargs):
    return audio_handler.speak(*args, **kwargs)

def wait_for_wake_word(*args, **kwargs):
    return audio_handler.wait_for_wake_word(*args, **kwargs)

def listen_and_transcribe(*args, **kwargs):
    return audio_handler.listen_and_transcribe(*args, **kwargs)

def stop_speaking(*args, **kwargs):
    return audio_handler.stop_speaking(*args, **kwargs)

def set_barge_in_callback(*args, **kwargs):
    return audio_handler.set_barge_in_callback(*args, **kwargs)

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

def get_api_key(
    request: Request,
    api_key_header: str = Security(api_key_header),
    x_device_id: Optional[str] = Header(None),
):
    # Permitir peticiones desde localhost / loopback directamente (IPv4, IPv6 o IPv4-mapped IPv6)
    client_host = request.client.host if request.client else ""
    if client_host in ("127.0.0.1", "localhost", "::1", "testclient") or client_host.endswith("127.0.0.1") or client_host.startswith("127."):
        return API_KEY
    if x_device_id and miku_db.is_valid_device(x_device_id):
        return x_device_id
    if API_KEY and api_key_header == API_KEY:
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

LOW_COST_MODE: bool = False

@app.post("/api/settings/low_cost_toggle")
async def toggle_low_cost():
    global LOW_COST_MODE
    LOW_COST_MODE = not LOW_COST_MODE
    logger.info(f"Modo Bajo Costo cambiado a: {LOW_COST_MODE}")
    return {"status": "ok", "low_cost": LOW_COST_MODE}

@app.get("/api/settings/low_cost")
async def get_low_cost():
    return {"status": "ok", "low_cost": LOW_COST_MODE}

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

# Servir archivos compartidos (Descargas desde el Celular)
os.makedirs("shared_files", exist_ok=True)
app.mount("/shared", StaticFiles(directory="shared_files"), name="shared")

# Servir SVGs y assets locales
if os.path.exists("assets"):
    app.mount("/assets", StaticFiles(directory="assets"), name="assets")

# Servir la Isla Dinámica de Miku (interfaz web canónica)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ui_dir = os.path.join(BASE_DIR, "miku_ui", "src")
if not os.path.exists(ui_dir):
    ui_dir = os.path.join(BASE_DIR, "miku_island")
if os.path.exists(ui_dir):
    app.mount("/island", StaticFiles(directory=ui_dir, html=True), name="island")

@app.get("/settings")
@app.get("/config")
@app.get("/miku_settings.html")
@app.get("/island/miku_settings.html")
async def get_settings_page():
    """Sirve la página completa de configuración de Miku de forma directa."""
    settings_path = os.path.join(BASE_DIR, "miku_ui", "src", "miku_settings.html")
    if not os.path.exists(settings_path):
        settings_path = os.path.join(BASE_DIR, "miku_island", "miku_settings.html")
    return FileResponse(settings_path)


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
    attachment_name: Optional[str] = None
    attachment_path: Optional[str] = None
    attachment_analysis: Optional[str] = None
    attachment_data: Optional[str] = None
    attachment_content: Optional[str] = None

class ChatResponse(BaseModel):
    reply: str
    audio_url: Optional[str] = None
    agent_id: Optional[str] = "miku"
    agent_name: Optional[str] = "Miku"

from datetime import datetime
import json

from miku_paths import (
    WORKSPACE_DIR,
    get_chat_history_dir, get_daily_chat_history_file,
    get_env_path, get_models_config_path, get_mcp_config_path,
    get_agents_config_path, get_alerts_config_path, sync_env_to_workspace
)

# Memoria de Chat Global Diaria
CHAT_HISTORY_DIR = get_chat_history_dir()

def get_daily_history_file():
    return get_daily_chat_history_file()

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
        self.mobile_connections: dict[str, dict[str, Any]] = {}
        self.connection_devices: dict[WebSocket, str] = {}
        self._lock = asyncio.Lock()

    async def connect(
        self,
        websocket: WebSocket,
        device_id: Optional[str] = None,
        device_name: Optional[str] = None,
    ) -> bool:
        await websocket.accept()
        async with self._lock:
            if websocket not in self.active_connections:
                self.active_connections.append(websocket)
            if device_id:
                self.connection_devices[websocket] = device_id
                device = self.mobile_connections.get(device_id)
                is_new_device_connection = device is None
                if device is None:
                    self.mobile_connections[device_id] = {
                        "name": device_name or "Teléfono",
                        "connections": 1,
                    }
                else:
                    device["connections"] += 1
                return is_new_device_connection
        return False

    def disconnect(self, websocket: WebSocket) -> Optional[dict[str, str]]:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        device_id = self.connection_devices.pop(websocket, None)
        if not device_id:
            return None
        device = self.mobile_connections.get(device_id)
        if not device:
            return None
        device["connections"] -= 1
        if device["connections"] > 0:
            return None
        self.mobile_connections.pop(device_id, None)
        return {"type": "miku_link_disconnected"}

    def connected_mobile(self) -> Optional[dict[str, str]]:
        device = next(iter(self.mobile_connections.values()), None)
        if not device:
            return None
        return {"type": "miku_link_connected", "name": device["name"]}

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
        mobile_status_changed = False
        async with self._lock:
            for connection in self.active_connections:
                try:
                    await connection.send_json(message)
                except (WebSocketDisconnect, RuntimeError):
                    dead_connections.append(connection)
            
            for connection in dead_connections:
                mobile_status_changed = self.disconnect(connection) is not None or mobile_status_changed

        if mobile_status_changed:
            await self.broadcast_message(
                self.connected_mobile() or {"type": "miku_link_disconnected"}
            )

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

@app.post("/broadcast_command")
async def broadcast_command_endpoint(request: Request):
    """Reenvía comandos del backend a todos los clientes WebSocket (Isla dinámica, UI)."""
    try:
        body = await request.json()
        payload = body.get("payload", body)
        await manager.broadcast_message(payload)
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

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
    
    # Inyectar contexto del archivo adjunto si está presente
    if req.attachment_name:
        file_path = req.attachment_path
        analysis_info = req.attachment_analysis or ""
        file_content = req.attachment_content or ""
        
        # Limitar extracción a máximo 3,500 caracteres (o 1,500 en modo bajo costo) para no inflar tokens
        max_extract = 1500 if LOW_COST_MODE else 3500
        if file_content and not analysis_info:
            analysis_info = file_content[:max_extract]

        # Si no hay ruta explícita, buscar en la carpeta de descargas de Miku-Link
        if not file_path and req.attachment_name:
            miku_link_candidate = os.path.join(os.path.expanduser('~'), 'Downloads', 'miku-link', req.attachment_name)
            if os.path.exists(miku_link_candidate):
                file_path = miku_link_candidate

        # Si vino dataUrl y no está guardado aún en disco
        if not file_path and req.attachment_data:
            try:
                dest_dir = os.path.join(os.path.expanduser('~'), 'Downloads', 'miku-link')
                os.makedirs(dest_dir, exist_ok=True)
                file_path = os.path.join(dest_dir, req.attachment_name or f"archivo_{int(time.time())}.dat")
                b_data = base64.b64decode(req.attachment_data.split(",")[-1] if "," in req.attachment_data else req.attachment_data)
                with open(file_path, "wb") as f:
                    f.write(b_data)
                if not analysis_info:
                    from tools_miku import analizar_archivo_silencioso
                    analysis_info = analizar_archivo_silencioso(file_path)
            except Exception as e:
                logger.error(f"Error guardando attachment en /chat: {e}")
        
        if file_path and not analysis_info and os.path.exists(file_path):
            try:
                from tools_miku import analizar_archivo_silencioso
                analysis_info = analizar_archivo_silencioso(file_path)
            except Exception:
                pass
        
        if analysis_info and len(analysis_info) > max_extract:
            analysis_info = analysis_info[:max_extract] + "\n[... Contenido truncado para optimizar consumo de tokens]"

        file_context = f"\n\n[ARCHIVO ADJUNTADO: '{req.attachment_name}']\nRuta local: {file_path or 'No disponible'}"
        if analysis_info:
            file_context += f"\nContenido del archivo / Análisis:\n{analysis_info}"
        
        user_input = user_input + file_context
        logger.info(f"Contexto de archivo adjuntado inyectado: {req.attachment_name} -> {file_path or 'desconocido'} (Longitud info: {len(analysis_info)} chars)")
    
    clean_history_text = (req.message + f" [Adjunto: {req.attachment_name}]") if req.attachment_name else req.message
    user_msg = {
        "type": "user_message",
        "id": str(int(time.time() * 1000)),
        "text": clean_history_text,
        "sender": "user",
        "agent_id": req.agent_id,
        "agent_name": req.agent_name,
    }
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
        agent_mcp = req.agent_mcp
    else:
        aid = (req.agent_id or "").lower()
        if aid == "github":
            agent_mcp = req.agent_mcp or "github"
            sys_prompt = f"""Eres GitHub, el agente especializado en control de versiones, repositorios de código, ramas, commits, pull requests y herramientas de Git del ecosistema Miku.
Instrucciones de tu rol:
Eres un ingeniero DevOps y especialista en Git de élite. Si el usuario te pide abrir GitHub en el navegador, clona repositorios, o ejecuta acciones en la web, utiliza tus herramientas técnicas (ej. ejecutar_comando_sistema con 'start https://github.com', abrir_aplicacion, o herramientas mcp_github_*).
Si te piden revisar un repositorio o pull requests, consulta la API de GitHub o las herramientas de git.
NUNCA digas que eres solo un modelo de texto que no puede hacer nada; dispones de herramientas para interactuar con git y el sistema.
Responde de forma técnica, estructurada, precisa y concisa."""
        elif aid == "antigravity":
            agent_mcp = req.agent_mcp or "none"
            sys_prompt = f"""Eres Antigravity, el agente especializado en diseño UI/UX, desarrollo Frontend, CSS avanzado, animaciones fluidas, Canvas y arquitectura visual del ecosistema Miku.
Instrucciones de tu rol:
Eres un frontend architect y diseñador de software estético, limpio y preciso. Conoces a fondo HTML, CSS, JavaScript, Canvas, animaciones Web, componentes reactivos y diseño de sistemas modernos.
Dispones de herramientas técnicas para escribir y ejecutar código Python, buscar información técnica e inspeccionar archivos.
Responde de forma técnica, elegante y concisa."""
        else:
            agent_mcp = req.agent_mcp or "none"
            custom_instructions = req.agent_prompt.strip() if req.agent_prompt else ""
            sys_prompt = f"""Eres {req.agent_name}, un agente técnico autónomo y altamente capacitado del ecosistema Miku.
Instrucciones específicas de tu rol:
{custom_instructions if custom_instructions else 'Eres un asistente técnico proactivo. Ejecuta las órdenes técnicas que te asigne el usuario.'}

REGLAS DE OPERACIÓN:
1. Responde de forma técnica, estructurada, precisa y concisa.
2. NUNCA uses etiquetas de voz <voz> ni hables como mascota kawaii; eres un agente técnico.
3. Eres silencioso (no reproduces audio por altavoces). Tu salida es puramente texto y herramientas.
4. Si se te solicita una acción técnica, utiliza las herramientas disponibles a tu alcance y devuelve un resumen concreto y útil."""

    response_text = await asyncio.to_thread(
        get_llm_response,
        user_input,
        sys_prompt,
        status_callback,
        None,
        req.agent_id,
        agent_mcp
    )
    
    # Separar voz corta del texto completo (si usa <voz>)
    voice_text, chat_text = extract_voice_text(response_text)
    
    agent_msg = {"type": "agent_reply", "id": str(int(time.time()*1000) + 1), "text": chat_text, "sender": req.agent_id, "agent_id": req.agent_id, "agent_name": req.agent_name}
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
                def _speak_and_idle():
                    try:
                        speak(speech_text)
                    finally:
                        sync_miku_state("idle")
                        try:
                            asyncio.run_coroutine_threadsafe(
                                manager.broadcast_message({"type": "scene", "name": "prompt"}),
                                main_loop
                            )
                        except Exception:
                            pass
                threading.Thread(target=_speak_and_idle, daemon=True).start()
            else:
                sync_miku_state("idle")
                await manager.broadcast_message({"type": "scene", "name": "prompt"})
        else:
            # Tarea asíncrona para no bloquear la respuesta HTTP instantánea del celular
            async def send_audio_async():
                try:
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
                except Exception:
                    logger.exception("Error generando o enviando audio de respuesta móvil.")
                finally:
                    sync_miku_state("idle")
            
            asyncio.create_task(send_audio_async())
    else:
        sync_miku_state("idle")
    
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

@app.get("/api/agents")
async def get_agents():
    from agents import load_agents_config
    return {"agents": load_agents_config()}

class AgentsSaveRequest(BaseModel):
    agents: list

@app.post("/api/agents")
async def save_agents(req: AgentsSaveRequest, api_key: str = Security(get_api_key)):
    from agents import save_agents_config
    ok = save_agents_config(req.agents)
    if ok:
        await manager.broadcast_message({"type": "agents", "list": req.agents})
    return {"status": "ok" if ok else "error"}

class UploadFileRequest(BaseModel):
    filename: str
    content: str
    is_base64: bool = False

@app.post("/api/upload_file")
async def upload_file_endpoint(req: UploadFileRequest, api_key: str = Security(get_api_key)):

    from tools_miku import analizar_archivo_silencioso
    try:
        dest_dir = os.path.join(tempfile.gettempdir(), "miku_uploads")
        os.makedirs(dest_dir, exist_ok=True)
        file_path = os.path.join(dest_dir, req.filename)
        is_b64 = req.is_base64 or req.content.startswith("data:") or ";base64," in req.content
        if is_b64:
            b_data = base64.b64decode(req.content.split(",")[-1] if "," in req.content else req.content)
            with open(file_path, "wb") as f:
                f.write(b_data)
        else:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(req.content)
        analysis = analizar_archivo_silencioso(file_path)
        return {
            "status": "ok",
            "filename": req.filename,
            "file_path": file_path,
            "preview": analysis[:350] if analysis else "Archivo cargado",
            "analysis": analysis
        }
    except Exception as e:
        logger.error(f"Error procesando upload: {e}")
        return {"status": "error", "message": str(e)}

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
    
    server_pub = miku_db.get_server_public_key_b64()
    return {"status": "ok", "server_public_key": server_pub}

# ==========================================
# FUNCIONES DE DISPOSITIVO VINCULADO
# ==========================================

@app.post("/api/device/lock")
@app.post("/api/desktop/lock")
async def device_lock(request: Request, x_device_id: str = Header(None)):
    client_ip = request.client.host if request.client else "127.0.0.1"
    is_local = client_ip in ("127.0.0.1", "localhost", "::1", "testclient")
    if not is_local and not miku_db.is_valid_device(x_device_id):
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

class SendToPhoneRequest(BaseModel):
    path: str

@app.post("/api/desktop/send_file_to_phone")
async def send_file_to_phone_endpoint(req: SendToPhoneRequest):
    """Envía un archivo de la PC al celular vinculado (usado por el menú contextual de Windows y herramientas)."""
    file_path = req.path
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Archivo no encontrado: {file_path}")

    filename = os.path.basename(file_path)
    stage_dir = os.path.join(tempfile.gettempdir(), "miku_temp_media")
    os.makedirs(stage_dir, exist_ok=True)
    dest_path = os.path.join(stage_dir, filename)

    try:
        shutil.copy2(file_path, dest_path)
    except Exception as e:
        logger.error(f"Error copiando archivo para envío: {e}")

    # Avisar al teléfono conectado por WebSocket
    await manager.broadcast_message({
        "type": "ui_command",
        "action": "download_file",
        "filename": filename
    })

    # Mostrar notificación en la Isla
    await manager.broadcast_message({
        "type": "ui_command",
        "action": "show_info",
        "args": ["Miku-Link", f"Enviando '{filename}' a tu celular"]
    })

    return {"status": "ok", "filename": filename, "message": f"Archivo {filename} enviado al celular."}

@app.get("/api/temp_media/{filename}")
async def get_temp_media(filename: str):
    """Sirve archivos en tránsito hacia la app móvil."""
    stage_dir = os.path.join(tempfile.gettempdir(), "miku_temp_media")
    candidate1 = os.path.join(stage_dir, filename)
    downloads_dir = os.path.join(os.path.expanduser('~'), 'Downloads', 'miku-link')
    candidate2 = os.path.join(downloads_dir, filename)
    candidate3 = os.path.join(tempfile.gettempdir(), filename)

    for p in (candidate1, candidate2, candidate3):
        if os.path.exists(p) and os.path.isfile(p):
            return FileResponse(p, filename=filename)

    raise HTTPException(status_code=404, detail="Archivo temporal no encontrado")

# ==========================================
# GESTION MIKU-LINK Y MODO BAJO COSTO
# ==========================================
LOW_COST_MODE = False

@app.get("/api/link/status")
async def link_status_endpoint():
    devices = miku_db.get_all_devices()
    active_mobile = manager.connected_mobile()
    is_connected = bool(active_mobile and active_mobile.get("type") == "miku_link_connected")
    
    first_dev = devices[0] if devices else None
    dev_name = first_dev["name"] if first_dev else "Ningún dispositivo vinculado"
    
    import socket
    local_ip = "127.0.0.1"
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.255.255.255", 1))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        pass
        
    return {
        "status": "ok",
        "connected": is_connected,
        "device_name": dev_name,
        "devices": devices,
        "ip": local_ip
    }

@app.get("/api/link/qr_data")
async def get_link_qr_data():
    global PAIRING_SESSION
    import uuid, socket, io, base64
    session_id = uuid.uuid4().hex[:10]
    PAIRING_SESSION = session_id
    
    local_ip = "127.0.0.1"
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.255.255.255", 1))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        pass

    pair_url = f"miku://pair?s={session_id}&ip={local_ip}"
    
    qr_b64 = ""
    try:
        import qrcode
        img = qrcode.make(pair_url)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        qr_b64 = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")
    except Exception as e:
        logger.warning(f"Error generando código QR en backend: {e}")

    return {
        "status": "ok",
        "url": pair_url,
        "qr_base64": qr_b64,
        "ip": local_ip,
        "session_id": session_id
    }

@app.post("/api/link/unpair")
async def link_unpair_endpoint(req: Optional[Dict[str, Any]] = None):
    """Desvincula y elimina dispositivos registrados, avisando tanto al companion móvil como a la UI."""
    target_id = req.get("device_id") if req and isinstance(req, dict) else None
    
    if target_id:
        miku_db.remove_device(target_id)
    else:
        for d in miku_db.get_all_devices():
            miku_db.remove_device(d["device_id"])
            
    # Avisar a clientes WebSocket (Android Companion y Desktop)
    await manager.broadcast_message({
        "type": "miku_link_unpaired",
        "action": "unpair",
        "device_id": target_id
    })
    
    # Cerrar sockets móviles autorizados
    manager.mobile_connections.clear()
    await manager.broadcast_message({"type": "miku_link_disconnected"})
    
    return {"status": "ok", "message": "Dispositivo desvinculado y eliminado correctamente"}

@app.post("/api/link/open-folder")
async def link_open_folder():
    """Abre la carpeta de archivos recibidos en el Explorador de Windows."""
    downloads_path = os.path.join(os.path.expanduser('~'), 'Downloads', 'miku-link')
    os.makedirs(downloads_path, exist_ok=True)
    try:
        if sys.platform == "win32":
            os.startfile(downloads_path)
        else:
            import subprocess
            subprocess.Popen(["xdg-open", downloads_path])
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/devices")
async def get_registered_devices():
    return {"devices": miku_db.get_all_devices()}

@app.delete("/api/devices/{device_id}")
async def delete_registered_device(device_id: str):
    miku_db.remove_device(device_id)
    await manager.broadcast_message({
        "type": "miku_link_unpaired",
        "action": "unpair",
        "device_id": device_id
    })
    manager.mobile_connections.pop(device_id, None)
    await manager.broadcast_message({"type": "miku_link_disconnected"})
    return {"status": "ok", "deleted": device_id}

@app.post("/api/settings/low_cost_toggle")
async def toggle_low_cost_mode():
    global LOW_COST_MODE
    LOW_COST_MODE = not LOW_COST_MODE
    logger.info(f"Modo Bajo Costo cambiado a: {LOW_COST_MODE}")
    return {"status": "ok", "low_cost": LOW_COST_MODE}

@app.get("/api/settings/low_cost")
async def get_low_cost_mode():
    return {"low_cost": LOW_COST_MODE}



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
        env_path = get_env_path()
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

@app.post("/api/system/shutdown")
async def shutdown_system(api_key: str = Security(get_api_key)):
    """Permite que Tauri o la interfaz solicite el apagado limpio del servidor."""
    logger.info("Recibida solicitud de apagado del sistema (shutdown).")
    def _delayed_exit():
        time.sleep(0.5)
        os._exit(0)
    import threading
    threading.Thread(target=_delayed_exit, daemon=True).start()
    return {"status": "shutting_down"}

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
    "DEEPSEEK_API_KEY",
    "OPENROUTER_API_KEY",
    "NVIDIA_API_KEY",
    "GITHUB_TOKEN",
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
    env_path = get_env_path()
    
    existing_lines = []
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            existing_lines = f.readlines()
    
    try:
        updated_keys = set()
        new_lines = []
        for line in existing_lines:
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and "=" in stripped:
                key_name = stripped.split("=", 1)[0].strip()
                if key_name in req.keys:
                    new_value = str(req.keys[key_name]).strip()
                    if new_value and not new_value.startswith("*"):
                        new_lines.append(f"{key_name}={new_value}\n")
                        os.environ[key_name] = new_value
                        updated_keys.add(key_name)
                        continue
            new_lines.append(line)
        
        for key_name, new_value in req.keys.items():
            if key_name not in updated_keys:
                clean_val = str(new_value).strip()
                if clean_val and not clean_val.startswith("*"):
                    new_lines.append(f"{key_name}={clean_val}\n")
                    os.environ[key_name] = clean_val
        
        with open(env_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        sync_env_to_workspace(new_lines)
        
        try:
            import importlib
            import config
            importlib.reload(config)
        except Exception as e:
            logger.warning(f"Error recargando config: {e}")
        
        return {"status": "ok", "message": "Configuración de claves actualizada."}
    except Exception as e:
        logger.error(f"Error guardando claves en .env: {e}")
        raise HTTPException(status_code=500, detail=f"Error guardando claves: {str(e)}")

@app.delete("/api/config/keys/{key_name}")
async def delete_config_key(key_name: str, api_key: str = Security(get_api_key)):
    """Elimina una API key del archivo .env y del entorno de ejecución con confirmación."""
    try:
        env_path = get_env_path()
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
        sync_env_to_workspace(new_lines)
            
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
    except Exception as e:
        logger.error(f"Error eliminando clave {key_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Error eliminando clave: {str(e)}")

@app.get("/api/audio/devices")
async def get_audio_input_devices():
    """Devuelve los micrófonos y dispositivos de entrada reales del sistema formateados como Discord."""
    try:
        import sounddevice as sd
        import re
        devices = sd.query_devices()
        apis = sd.query_hostapis()
        
        # Priorizar DirectSound para nombres completos y compatibilidad nativa a 16kHz
        ds_api_idx = next((i for i, a in enumerate(apis) if 'directsound' in a['name'].lower()), None)
        selected = []
        if ds_api_idx is not None:
            selected = [(i, d) for i, d in enumerate(devices) if d.get("max_input_channels", 0) > 0 and d.get("hostapi") == ds_api_idx]
        if not selected:
            selected = [(i, d) for i, d in enumerate(devices) if d.get("max_input_channels", 0) > 0 and d.get("hostapi") in (0, 1, 2)]

        # Detectar el controlador de audio primario (ej. Realtek(R) Audio)
        primary_ctrl = "Realtek(R) Audio"
        for _, d in selected:
            m = re.match(r'^(.*?)\s*\((.*?)\)$', d.get("name", ""))
            if m and "controlador" not in m.group(1).lower() and "asignador" not in m.group(1).lower():
                primary_ctrl = m.group(2).strip()
                break

        inputs = [{
            "id": "default",
            "index": "default",
            "name": f"Windows Default ({primary_ctrl})",
            "is_default": True,
            "channels": 2
        }]

        seen_labels = set()
        for i, d in selected:
            raw = d.get("name", "").strip()
            if not raw or "controlador primario" in raw.lower() or "asignador de sonido" in raw.lower():
                continue
            m = re.match(r'^(.*?)\s*\((.*?)\)$', raw)
            if m:
                endpoint = m.group(1).strip()
                controller = m.group(2).strip()
                name = f"{controller} · {endpoint}"
            else:
                name = raw

            if name in seen_labels:
                continue
            seen_labels.add(name)

            inputs.append({
                "id": f"mic_{i}",
                "index": i,
                "name": name,
                "is_default": False,
                "channels": d.get("max_input_channels", 1)
            })

        return {"devices": inputs}
    except Exception as e:
        logger.warning(f"Error consultando dispositivos de audio: {e}")
        return {"devices": []}

@app.post("/api/audio/device")
async def set_audio_input_device(data: Optional[Dict[str, Any]] = None):
    """Establece el dispositivo de audio de entrada activo para transcripción y wake word."""
    if data is None:
        data = {}
    try:
        raw_val = data.get("index")
        if raw_val is None:
            raw_val = data.get("device_id")
        import audio_handler
        if raw_val is None or raw_val == "default" or str(raw_val) == "-1":
            audio_handler.set_active_device(None)
            logger.info("Micrófono establecido a predeterminado del sistema.")
            try:
                from prompt_manager import save_setting_key
                save_setting_key("mic", "default")
            except Exception:
                pass
            return {"status": "ok", "device": "default"}
        
        if isinstance(raw_val, str) and raw_val.startswith("mic_"):
            idx = int(raw_val.replace("mic_", ""))
        else:
            idx = int(raw_val)
        
        audio_handler.set_active_device(idx)
        logger.info(f"Micrófono cambiado activamente al índice {idx}")
        try:
            from prompt_manager import save_setting_key
            save_setting_key("mic", str(idx))
        except Exception:
            pass
        return {"status": "ok", "device_index": idx}
    except Exception as e:
        logger.warning(f"Error cambiando dispositivo de audio: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/api/system/browse_exe")
async def browse_executable_file():
    """Abre el diálogo nativo de Windows silenciosamente para seleccionar un archivo ejecutable."""
    def _open_dialog():
        try:
            import subprocess
            ps_script = (
                "[System.Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms') | Out-Null; "
                "$f = New-Object System.Windows.Forms.OpenFileDialog; "
                "$f.Filter = 'Ejecutables (*.exe)|*.exe|Todos los archivos (*.*)|*.*'; "
                "$f.Title = 'Seleccionar ejecutable para alerta proactiva'; "
                "if ($f.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) { "
                "  [Console]::Out.Write($f.FileName) "
                "}"
            )
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            res = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_script],
                capture_output=True,
                text=True,
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            return res.stdout.strip()
        except Exception as e:
            logger.error(f"Error abriendo selector de archivo: {e}")
            return ""

    loop = asyncio.get_event_loop()
    selected_path = await loop.run_in_executor(None, _open_dialog)
    return {"path": selected_path}

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
# CONFIGURACIÓN DE MODELOS (ROUTER DINÁMICO)
# ==========================================
MODELS_FILE = get_models_config_path()

def get_active_providers():
    from models_provider import get_active_providers as _gap
    return _gap()

@app.get("/api/config/models")
async def get_models_config():
    from models_provider import get_available_models, get_configured_models, get_active_providers as _gap
    current = get_configured_models()
    active_providers = _gap()
    available = get_available_models()

    # Si el modelo guardado no existe en los disponibles reales, sugerir el primero disponible sin borrarlo arbitrariamente
    for cat in ["chat", "pro", "computer_use", "stt"]:
        eligible = available.get(cat, [])
        if eligible:
            eligible_ids = [m["id"] for m in eligible]
            if not current.get(cat):
                current[cat] = eligible_ids[0]

    return {
        "current": current,
        "available": available,
        "active_providers": list(active_providers),
        "has_providers": len(active_providers) > 0
    }

class UpdateModelsRequest(BaseModel):
    chat: Optional[str] = None
    pro: Optional[str] = None
    computer_use: Optional[str] = None
    stt: Optional[str] = None

@app.post("/api/config/models")
async def update_models_config(req: UpdateModelsRequest):
    from models_provider import get_configured_models, reload_configured_models
    current = get_configured_models()
    if req.chat is not None and req.chat != "":
        current["chat"] = req.chat
    if req.pro is not None and req.pro != "":
        current["pro"] = req.pro
    if req.computer_use is not None and req.computer_use != "":
        current["computer_use"] = req.computer_use
    if req.stt is not None and req.stt != "":
        current["stt"] = req.stt
    with open(MODELS_FILE, "w", encoding="utf-8") as f:
        json.dump(current, f, indent=2, ensure_ascii=False)
    try:
        from miku_paths import WORKSPACE_DIR
        ws_file = os.path.join(WORKSPACE_DIR, "models_config.json")
        if ws_file != MODELS_FILE:
            with open(ws_file, "w", encoding="utf-8") as f_ws:
                json.dump(current, f_ws, indent=2, ensure_ascii=False)
    except Exception:
        pass
    try:
        reload_configured_models()
    except Exception:
        pass
    return {"status": "ok", "current": current}

# ==========================================
# MODOS DE EJECUCIÓN (ANTIGRAVITY SANDBOX)
# ==========================================
import security_manager

@app.get("/api/config/execution_mode")
async def get_execution_mode_endpoint():
    """Devuelve el modo de ejecución actual y las opciones disponibles (full, sandbox, restricted)."""
    return security_manager.get_modes_info()

class UpdateExecutionModeRequest(BaseModel):
    mode: str

@app.post("/api/config/execution_mode")
async def update_execution_mode_endpoint(req: UpdateExecutionModeRequest):
    """Actualiza el modo de ejecución de Miku (Toda la PC, Sandbox o Restringido)."""
    success = security_manager.set_execution_mode(req.mode)
    if not success:
        raise HTTPException(status_code=400, detail=f"Modo no válido. Opciones: {list(security_manager.VALID_MODES.keys())}")
    info = security_manager.get_modes_info()
    try:
        await manager.broadcast_message({
            "type": "execution_mode_updated",
            "mode": info["current_mode"],
            "details": info["current_details"]
        })
    except Exception:
        pass
    return {"status": "ok", **info}

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
    # 1. Intentar con Spotify API primero si está configurado
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

    # 2. Si Spotify API no tiene sesión activa, usar music_controller de Windows (GSMTC / apps de música activas)
    try:
        import music_controller
        ms = music_controller.media_state
        if ms.get("has_session") or ms.get("is_playing"):
            cov = ""
            if ms.get("thumbnail_bytes"):
                cov = f"data:image/jpeg;base64,{base64.b64encode(ms['thumbnail_bytes']).decode('ascii')}"
            
            pos_sec = ms.get("position_sec", 0)
            if ms.get("is_playing") and ms.get("last_update_time"):
                elapsed = time.time() - ms["last_update_time"]
                dur = ms.get("end_time_sec", 0)
                if dur > 0:
                    pos_sec = min(dur, pos_sec + elapsed)
                elif elapsed > 0:
                    pos_sec = pos_sec + elapsed

            state = {
                "title": ms.get("title") or "Sin música",
                "artist": ms.get("artist") or "Reproductor",
                "playing": bool(ms.get("is_playing")),
                "cover": cov,
                "pos": round(pos_sec, 1),
                "dur": round(ms.get("end_time_sec", 0), 1),
                "vol": ms.get("volume", 70)
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
    """Recibe eventos de agentes CLI (Claude Code, Cursor, Codex, Antigravity, GitHub)."""
    try:
        payload = await request.json()
    except Exception:
        payload = {}
    event_name = payload.get("hook_event_name", payload.get("event", "Notification"))
    agent_name = payload.get("miku_agent", payload.get("agent", payload.get("subagent", "antigravity")))
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
MCP_FILE = get_mcp_config_path()

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
            "enabled": srv.get("enabled", True),
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
    from mcp_client import mcp_manager
    msg = await mcp_manager.add_server(req.name, req.command, req.args)
    is_ok = not str(msg).lower().startswith("error")
    return {"status": "ok" if is_ok else "error", "message": msg}

class ToggleMcpRequest(BaseModel):
    enabled: bool

@app.patch("/api/config/mcp/{name}/toggle")
async def toggle_mcp_server(name: str, req: ToggleMcpRequest):
    from mcp_client import mcp_manager
    ok = await mcp_manager.toggle_server(name, req.enabled)
    return {"status": "ok" if ok else "error", "enabled": req.enabled}

@app.delete("/api/config/mcp/{name}")
async def delete_mcp_server(name: str):
    from mcp_client import mcp_manager
    ok = await mcp_manager.remove_server(name)
    if ok:
        return {"status": "ok", "message": f"Servidor MCP '{name}' eliminado y desconectado."}
    return {"status": "not_found", "message": f"Servidor MCP '{name}' no encontrado."}

class GenerateAgentPromptReq(BaseModel):
    name: str = "Agente"
    role: str = ""
    description: str = ""

@app.post("/api/agent/generate_prompt")
async def generate_agent_prompt(req: GenerateAgentPromptReq):
    def _gen():
        from brain import get_gemini_client, get_groq_client
        system_instruction = (
            "Eres un arquitecto de IA y Prompt Engineer de élite.\n"
            "Tu ÚNICA tarea es redactar el SYSTEM PROMPT (las instrucciones técnicas y directrices de comportamiento) "
            "para un agente de inteligencia artificial.\n\n"
            "REGLAS CRÍTICAS:\n"
            "1. PROHIBIDO responder como un chat (NUNCA digas '¡Entendido!', 'Hola', 'He registrado...', 'Claro').\n"
            "2. Redacta las instrucciones dirigiéndote al agente en segunda persona ('Eres...').\n"
            "3. Estructura el prompt en:\n"
            "   - Identidad y Especialidad: Quién es y sus conocimientos clave.\n"
            "   - Responsabilidades Principales: Tareas concretas que debe realizar.\n"
            "   - Pautas de Comportamiento: Tono técnico, precisión, brevedad y directrices de acción.\n"
            "4. Devuelve ÚNICAMENTE el texto del prompt del sistema, sin markdown quotes exteriores ni introducciones."
        )
        user_content = f"Nombre del agente: {req.name}\nRol: {req.role or 'Asistencia técnica'}\nDescripción de sus funciones:\n{req.description}"
        messages = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_content}
        ]
        
        client, model = get_gemini_client()
        if not client:
            client, model = get_groq_client()
            
        if client:
            try:
                resp = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=0.3,
                    max_tokens=600
                )
                text = (resp.choices[0].message.content or "").strip()
                if text.startswith("```") and text.endswith("```"):
                    lines = text.split("\n")
                    if len(lines) > 2:
                        text = "\n".join(lines[1:-1]).strip()
                return text
            except Exception as e:
                logger.error(f"Error llamando LLM para generar prompt: {e}")

        return (
            f"Eres {req.name}, un agente asistente especializado en {req.role or 'gestión técnica'}.\n\n"
            f"OBJETIVO:\n{req.description or 'Ejecutar las órdenes asignadas con máxima precisión y rapidez.'}\n\n"
            "REGLAS:\n"
            "1. Responde de manera técnica, estructurada y concisa.\n"
            "2. Ejecuta tareas de forma autónoma utilizando las herramientas disponibles a tu alcance.\n"
            "3. Sé directo y evita preámbulos innecesarios."
        )

    try:
        clean_text = await asyncio.to_thread(_gen)
        return {"prompt": clean_text}
    except Exception as e:
        logger.error(f"Error generando prompt con IA: {e}")
        return {"prompt": f"Eres {req.name}, un agente asistente especializado en {req.role or 'asistencia técnica'}.\nTu objetivo es: {req.description or 'cumplir las tareas encomendadas'}.\nResponde de forma clara, directa y concisa."}


# ==========================================
# CONFIGURACIÓN DE ALERTAS PROACTIVAS
# ==========================================
ALERTS_FILE = get_alerts_config_path()

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

@app.post("/api/alerts/test")
async def test_proactive_alert():
    """Dispara una alerta de prueba inmediata para validar notificaciones en la Isla y Windows."""
    test_msg = "Alerta de prueba: Llevas tiempo prolongado en tu equipo. Recuerda descansar la vista."
    await manager.broadcast_message({
        "type": "proactive_alert",
        "title": "Alerta de Enfoque (Prueba)",
        "message": test_msg,
        "badge": "Enfoque",
        "app": "Antigravity IDE",
        "minutes": 45
    })
    def _show_windows_toast(title, msg):
        try:
            import subprocess
            ps_cmd = f'[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null; $template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02); $textNodes = $template.GetElementsByTagName("text"); $textNodes.Item(0).AppendChild($template.CreateTextNode("{title}")) > $null; $textNodes.Item(1).AppendChild($template.CreateTextNode("{msg}")) > $null; $notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Miku Desktop"); $toast = [Windows.UI.Notifications.ToastNotification]::new($template); $notifier.Show($toast);'
            subprocess.Popen(["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_cmd], creationflags=subprocess.CREATE_NO_WINDOW)
        except Exception:
            pass

    asyncio.create_task(asyncio.to_thread(_show_windows_toast, "Miku: Alerta de Enfoque (Prueba)", test_msg))
    return {"status": "ok", "message": "Alerta de prueba emitida"}

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

KNOWN_APP_SVGS = {
    "spotify": '<svg viewBox="0 0 24 24" width="24" height="24" fill="#1DB954"><path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.495 17.306a.75.75 0 0 1-1.032.248c-2.825-1.727-6.38-2.118-10.57-1.16a.75.75 0 1 1-.334-1.462c4.586-1.047 8.528-.601 11.688 1.342a.75.75 0 0 1 .248 1.032zm1.465-3.259a.937.937 0 0 1-1.29.309c-3.233-1.987-8.163-2.562-11.988-1.4a.938.938 0 0 1-.55-1.791c4.37-1.326 9.805-.688 13.52 1.593a.937.937 0 0 1 .308 1.289zm.125-3.398c-3.877-2.302-10.272-2.514-13.985-1.387a1.125 1.125 0 1 1-.652-2.154c4.26-1.294 11.318-1.048 15.792 1.607a1.125 1.125 0 0 1-1.155 1.934z"/></svg>',
    "discord": '<svg viewBox="0 0 24 24" width="24" height="24" fill="#5865F2"><path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028c.462-.63.874-1.295 1.226-1.994.021-.041.001-.09-.041-.106a13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.929 1.793 8.18 1.793 12.061 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.894.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.028z"/></svg>',
    "code": '<svg viewBox="0 0 24 24" width="24" height="24" fill="#007ACC"><path d="M23.15 2.587L18.21.21a1.494 1.494 0 0 0-1.705.29l-9.46 8.63-4.12-3.128a.999.999 0 0 0-1.276.057L.327 7.261A1 1 0 0 0 .32 8.697L3.9 12 .32 15.303a1 1 0 0 0 .007 1.436l1.322 1.202a.999.999 0 0 0 1.276.057l4.12-3.128 9.46 8.63a1.492 1.492 0 0 0 1.704.29l4.942-2.377A1.5 1.5 0 0 0 24 20.06V3.939a1.5 1.5 0 0 0-.85-1.352z"/></svg>',
    "steam": '<svg viewBox="0 0 24 24" width="24" height="24" fill="#171a21"><path d="M12 0a12 12 0 0 0-12 12c0 5.43 3.6 9.99 8.57 11.45l2.67-3.9a4.8 4.8 0 0 1-.74-2.55 4.84 4.84 0 0 1 4.84-4.85h.06l3.37-4.88A11.96 11.96 0 0 0 12 0zm5.4 6.6a2.7 2.7 0 1 1 0 5.4 2.7 2.7 0 0 1 0-5.4z"/></svg>',
    "antigravity": '<svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="#a855f7" stroke-width="2.2"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>'
}

def get_app_icon_with_fallback(exe: str, name_lower: str) -> str:
    for key, svg in KNOWN_APP_SVGS.items():
        if key in name_lower:
            return svg
    for item in KNOWN_DETECTABLE_APPS:
        if item.get("process", "").lower() in name_lower or item.get("id", "").lower() in name_lower:
            return item.get("icon", "")
    icon_b64 = get_exe_icon_base64(exe)
    if icon_b64:
        return icon_b64
    return '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="#8e919a" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="3" width="20" height="14" rx="2"/><polygon points="6 21 18 21 12 17"/></svg>'

@app.get("/api/apps/running")
async def get_running_apps():
    """Devuelve las aplicaciones y juegos actualmente activos en la PC al instante (estilo Discord)."""
    import psutil
    apps = []
    seen_names = set()
    active_pids = set()

    # 1. Ventanas visibles en primer plano (juegos o apps abiertas en escritorio)
    try:
        import win32gui
        import win32process
        def _enum_win(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title and len(title.strip()) > 1 and title not in ("Program Manager", "Settings", "Miku Dynamic Island", "Miku"):
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    if pid > 4:
                        active_pids.add((pid, title.strip()))
            return True
        win32gui.EnumWindows(_enum_win, None)
    except Exception:
        pass

    for pid, win_title in active_pids:
        try:
            p = psutil.Process(pid)
            name = (p.name() or '').strip()
            exe = (p.exe() or '').strip()
            if not name or not exe:
                continue
            name_lower = name.lower()
            if name_lower in seen_names:
                continue
            if "windows\\system32" in exe.lower() or "windows\\syswow64" in exe.lower():
                continue
            
            clean_token = name_lower.replace(".exe", "")
            if any(bad in clean_token for bad in EXCLUDE_PROC_PATTERNS):
                continue

            seen_names.add(name_lower)
            matched_known = None
            for kname, kinfo in KNOWN_APP_INFO.items():
                if kname in name_lower:
                    matched_known = kinfo
                    break

            app_name = matched_known[0] if matched_known else (win_title if len(win_title) < 28 else os.path.splitext(name)[0].replace("_", " ").title())
            is_game = (matched_known and matched_known[1] == "juego") or any(g in name_lower or g in win_title.lower() for g in ("game", "play", "steam", "riot", "craft", "epic", "unity", "unreal", "valorant", "roblox"))
            category = "juego" if is_game else (matched_known[1] if matched_known else "aplicacion")
            icon_data = get_app_icon_with_fallback(exe, name_lower)

            apps.append({
                "id": name_lower.replace(".exe", ""),
                "name": app_name,
                "process": name,
                "exe": exe,
                "category": category,
                "is_active_window": True,
                "icon": icon_data
            })
        except Exception:
            continue

    # 2. Otros procesos conocidos que no tengan ventana visible activa
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

            matched_known = None
            for kname, kinfo in KNOWN_APP_INFO.items():
                if kname in name_lower:
                    matched_known = kinfo
                    break

            if matched_known:
                if any(a["name"] == matched_known[0] for a in apps):
                    continue
                seen_names.add(name_lower)
                icon_data = get_app_icon_with_fallback(exe, name_lower)
                apps.append({
                    "id": name_lower.replace(".exe", ""),
                    "name": matched_known[0],
                    "process": name,
                    "exe": exe,
                    "category": matched_known[1],
                    "is_active_window": False,
                    "icon": icon_data
                })
        except Exception:
            continue

    apps.sort(key=lambda a: (0 if a.get("is_active_window") else 1, 0 if a.get("category") == "juego" else 1, a["name"]))
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
async def send_to_phone_api(file: UploadFile = File(...), api_key: str = Security(get_api_key)):
    """Encola un archivo para el cliente móvil conectado."""
    if not manager.connected_mobile():
        raise HTTPException(status_code=409, detail="No hay un teléfono Miku conectado.")

    filename = os.path.basename((file.filename or "archivo").replace("\\", "/"))
    if not filename:
        raise HTTPException(status_code=400, detail="El archivo no tiene un nombre válido.")
    temp_dir = tempfile.gettempdir()
    file_path = os.path.join(temp_dir, filename)
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except OSError as exc:
        logger.exception("Error preparando archivo para el teléfono")
        raise HTTPException(status_code=500, detail="No se pudo preparar el archivo para el teléfono.") from exc

    await manager.broadcast_message({
        "type": "ui_command",
        "action": "download_file",
        "filename": filename
    })
    return {"status": "ok", "message": f"El archivo {filename} está listo para guardarse en el celular."}

@app.post("/api/device/send_to_phone")
async def send_text_to_phone(req: ClipboardRequest, api_key: str = Security(get_api_key)):
    if not manager.connected_mobile():
        raise HTTPException(status_code=409, detail="No hay un teléfono Miku conectado.")

    await manager.broadcast_message({
        "type": "ui_command",
        "action": "sync_clipboard",
        "text": req.text
    })
    return {"status": "ok"}

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
    device_id = websocket.headers.get("x-device-id") or websocket.query_params.get("device_id")
    authorized_device = bool(device_id and miku_db.is_valid_device(device_id))
    if token != API_KEY and not authorized_device:
        logger.warning("Conexión WS rechazada: faltan credenciales válidas o el dispositivo no está vinculado.")
        await websocket.close(code=1008)
        return
    logger.info("[WS] Cliente conectado exitosamente.")
    
    # 1. Accept the connection first
    device = miku_db.get_device(device_id) if authorized_device else None
    is_new_mobile_connection = await manager.connect(
        websocket,
        device_id=device_id if authorized_device else None,
        device_name=device["name"] if device else None,
    )
    if authorized_device and is_new_mobile_connection:
        await manager.broadcast_message({
            "type": "miku_link_connected",
            "name": device["name"] if device else "Teléfono",
        })
    elif not authorized_device:
        connected_mobile = manager.connected_mobile()
        if connected_mobile:
            await websocket.send_json(connected_mobile)
    
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
        disconnected_event = manager.disconnect(websocket)
        if disconnected_event:
            await manager.broadcast_message(disconnected_event)
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
        await asyncio.sleep(6.0 if LOW_COST_MODE else 2.5)

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

async def dev_activity_watcher_loop():
    """Monitorea cambios en el repositorio Git y actividad de Antigravity para mantener informada a la Dynamic Island."""
    repo_dir = os.path.dirname(os.path.abspath(__file__))
    last_git_status = None
    last_antigravity_mtime = 0
    antigravity_brain_dir = os.path.expanduser(r"~\.gemini\antigravity-ide\brain")
    
    await asyncio.sleep(5)
    while True:
        try:
            # 1. Monitoreo de cambios Git locales (Agente GitHub)
            def check_git():
                try:
                    res = subprocess.run(
                        ["git", "status", "--porcelain"],
                        cwd=repo_dir,
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    return res.stdout.strip()
                except Exception:
                    return None

            git_out = await asyncio.to_thread(check_git)
            if git_out is not None and git_out != last_git_status:
                if last_git_status is not None and git_out:
                    lines = [l for l in git_out.splitlines() if l.strip()]
                    await manager.broadcast_message({
                        "type": "agent_hook",
                        "agent": "github",
                        "event": "Git Changes",
                        "prompt": f"{len(lines)} archivo(s) con cambios en el proyecto",
                        "tool": "git"
                    })
                last_git_status = git_out

            # 2. Monitoreo de actividad de Antigravity IDE (Agente Antigravity)
            if os.path.exists(antigravity_brain_dir):
                def check_antigravity():
                    max_mtime = 0
                    try:
                        for entry in os.scandir(antigravity_brain_dir):
                            if entry.is_dir():
                                log_path = os.path.join(entry.path, ".system_generated", "logs", "transcript.jsonl")
                                if os.path.exists(log_path):
                                    mt = os.path.getmtime(log_path)
                                    if mt > max_mtime:
                                        max_mtime = mt
                    except Exception:
                        pass
                    return max_mtime

                latest_mt = await asyncio.to_thread(check_antigravity)
                last_antigravity_mtime = latest_mt

        except Exception:
            pass
        await asyncio.sleep(6)

_last_alert_triggered = {}

async def activity_alert_watcher_loop():
    """Vigila el tiempo continuo en aplicaciones/juegos y dispara alertas proactivas tanto en la Isla como en Windows."""
    while True:
        try:
            await asyncio.sleep(25)
            if not os.path.exists(ALERTS_FILE):
                continue
            try:
                with open(ALERTS_FILE, "r", encoding="utf-8") as f:
                    alerts_cfg = json.load(f)
            except Exception:
                continue

            if not alerts_cfg:
                continue

            from activity_monitor import get_activity_summary
            summary = get_activity_summary()
            
            app_times = {}
            for item in summary:
                proc = item.get("process", "").lower()
                mins = item.get("minutes", 0)
                app_times[proc] = (item.get("app", proc), mins)

            now_ts = time.time()
            for key, alert_data in alerts_cfg.items():
                if not alert_data or not alert_data.get("enabled", True):
                    continue
                threshold_mins = alert_data.get("threshold", 120)
                key_lower = key.lower()

                matched_proc = None
                matched_name = alert_data.get("label", key)
                matched_mins = 0
                for proc, (name, mins) in app_times.items():
                    if key_lower in proc or key_lower in name.lower() or proc in key_lower:
                        matched_proc = proc
                        matched_name = name
                        matched_mins = mins
                        break

                if matched_proc and matched_mins >= threshold_mins:
                    last_time = _last_alert_triggered.get(matched_proc, 0)
                    if (now_ts - last_time) > 1800:  # Máximo 1 alerta cada 30 min por app
                        _last_alert_triggered[matched_proc] = now_ts
                        alert_msg = f"Llevas más de {int(matched_mins)} minutos en {matched_name}. ¿Es momento de tomar un descanso?"
                        logger.info(f"[Alerta de Enfoque]: {alert_msg}")

                        # 1. Notificar al WebSocket de la Isla dinámica
                        await manager.broadcast_message({
                            "type": "proactive_alert",
                            "title": f"Alerta: {matched_name}",
                            "message": alert_msg,
                            "badge": "Enfoque",
                            "app": matched_name,
                            "minutes": matched_mins
                        })

                        # 2. Notificación nativa de Windows (Toast)
                        def _show_windows_toast(title, msg):
                            try:
                                import winsdk.windows.ui.notifications as win_notif
                                import winsdk.windows.data.xml.dom as win_xml
                                xml_content = f"<toast><visual><binding template='ToastGeneric'><text>{title}</text><text>{msg}</text></binding></visual></toast>"
                                doc = win_xml.XmlDocument()
                                doc.load_xml(xml_content)
                                notification = win_notif.ToastNotification(doc)
                                notifier = win_notif.ToastNotificationManager.create_toast_notifier("Miku Desktop")
                                notifier.show(notification)
                            except Exception:
                                try:
                                    import subprocess
                                    ps_cmd = f'[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null; $template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02); $textNodes = $template.GetElementsByTagName("text"); $textNodes.Item(0).AppendChild($template.CreateTextNode("{title}")) > $null; $textNodes.Item(1).AppendChild($template.CreateTextNode("{msg}")) > $null; $notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Miku Desktop"); $toast = [Windows.UI.Notifications.ToastNotification]::new($template); $notifier.Show($toast);'
                                    subprocess.Popen(["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_cmd], creationflags=subprocess.CREATE_NO_WINDOW)
                                except Exception:
                                    pass

                        await asyncio.to_thread(_show_windows_toast, f"Miku: Límite en {matched_name}", alert_msg)

        except Exception as e:
            logger.debug(f"Error en loop de alertas: {e}")

@app.on_event("startup")
async def startup_event():
    loop = asyncio.get_running_loop()
    sys.stdout = StdoutHook(sys.stdout)
    sys.stdout.loop = loop
    
    try:
        from activity_monitor import start_monitoring
        start_monitoring(interval=15)
        logger.info("[Startup] Monitor de actividad iniciado para alertas proactivas.")
    except Exception as e:
        logger.warning(f"No se pudo iniciar activity_monitor: {e}")

    asyncio.create_task(clipboard_monitor())
    asyncio.create_task(ui_context_loop())
    asyncio.create_task(spotify_media_loop())
    asyncio.create_task(dev_activity_watcher_loop())
    asyncio.create_task(activity_alert_watcher_loop())

    # Precalentar módulos pesados en segundo plano sin retrasar el puerto 8000
    import threading
    def _warmup_background():
        try:
            import brain
            import audio_handler
            logger.info("Precalentamiento en segundo plano completado (Cerebro y Audio listos).")
        except Exception as e:
            logger.debug(f"Aviso precalentamiento: {e}")
    threading.Thread(target=_warmup_background, daemon=True).start()

    try:
        import music_controller
        music_controller.start_media_listener()
    except Exception as e:
        logger.warning(f"Music controller no iniciado: {e}")
    
    # Iniciar monitor de actividad del usuario (qué apps usa en el PC)
    try:
        from activity_monitor import start_monitoring
        start_monitoring(interval=30)
        logger.info("Monitor de actividad del usuario iniciado.")
    except Exception as e:
        logger.warning(f"Activity monitor no disponible: {e}")

    # Iniciar túnel de Cloudflare automáticamente si existe el ejecutable
    try:
        cf_local = os.path.join(WORKSPACE_DIR, "cloudflared.exe")
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
    import multiprocessing
    multiprocessing.freeze_support()
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
            
            # Avisar inmediatamente a la UI para que se abra el chat de Miku (blanca)
            try:
                requests.post(
                    "http://127.0.0.1:8000/broadcast_command",
                    json={"payload": {"type": "wake", "who": "miku"}},
                    headers={"x-api-key": API_KEY},
                    timeout=1.0
                )
                requests.post(
                    "http://127.0.0.1:8000/broadcast_command",
                    json={"payload": {"type": "scene", "name": "prompt"}},
                    headers={"x-api-key": API_KEY},
                    timeout=1.0
                )
            except Exception:
                pass
            
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
