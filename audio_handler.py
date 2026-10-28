import json
import wave
import time
import re
import os
import tempfile
import asyncio
import threading
import queue
import logging
import sounddevice as sd
import numpy as np
import pygame
import edge_tts
from groq import Groq
from config import (
    GROQ_API_KEY, WAKE_WORD,
    VOICE_NAME, VOICE_RATE, VOICE_PITCH,
    ENABLE_BARGE_IN, BARGE_IN_MODE, ELEVENLABS_API_KEY
)

logger = logging.getLogger("AudioHandler")

try:
    import torch
    from silero_vad import load_silero_vad
    vad_model = load_silero_vad()
    VAD_ENABLED = True
except Exception as e:
    logger.warning(f"Silero VAD / Torch no disponible: {e}")
    VAD_ENABLED = False

groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# active_device_index se resuelve con resolve_best_device() más abajo

_is_speaking = False
_interrupt_speaking = threading.Event()
_barge_in_callback = None
_oww_model = None
_pygame_lock = threading.Lock()
_speak_lock = threading.Lock()
_voice_volume = 0.8
_wake_paused = False

try:
    from miku_paths import WORKSPACE_DIR as _WDIR
    _cfg_path = os.path.join(_WDIR, "settings_config.json")
    if os.path.exists(_cfg_path):
        with open(_cfg_path, "r", encoding="utf-8") as _f:
            _wake_paused = bool(json.load(_f).get("wake_paused", 0))
except Exception:
    pass

def is_wake_paused() -> bool:
    return _wake_paused

def set_wake_paused(paused: bool):
    global _wake_paused
    _wake_paused = bool(paused)
    logger.info(f"[Audio] Detección de wake word 'Miku': {'PAUSADA' if _wake_paused else 'ACTIVA'}")

def set_voice_volume(vol: int):
    """Ajusta el volumen de la voz de Miku (0 - 100)."""
    global _voice_volume
    try:
        _voice_volume = max(0.0, min(1.0, float(vol) / 100.0))
        if pygame.mixer.get_init():
            pygame.mixer.music.set_volume(_voice_volume)
    except Exception as e:
        logger.warning(f"Error ajustando volumen: {e}")

def get_voice_volume() -> int:
    return int(_voice_volume * 100)

def get_oww_model():
    """Carga y reutiliza el modelo de openWakeWord para evitar cargarlo múltiples veces."""
    global _oww_model
    if _oww_model is None:
        try:
            from openwakeword.model import Model
            from miku_paths import WORKSPACE_DIR
            model_candidate = os.path.join(WORKSPACE_DIR, "Miku_20260622_080146.onnx")
            target_model = model_candidate if os.path.exists(model_candidate) else "Miku_20260622_080146.onnx"
            _oww_model = Model(wakeword_models=[target_model], inference_framework="onnx")
        except Exception as e:
            logger.error(f"Error cargando openWakeWord: {e}")
    return _oww_model

def get_input_devices():
    """Devuelve una lista de tuplas (índice, nombre) de los micrófonos disponibles."""
    try:
        devices = sd.query_devices()
        input_devices = [(i, dev['name']) for i, dev in enumerate(devices) if dev['max_input_channels'] > 0]
        return input_devices
    except Exception as e:
        logger.error(f"Error al obtener micrófonos: {e}")
        return []

def resolve_best_device(preferred_index=None):
    """Resuelve el mejor dispositivo de entrada disponible para captura de voz y wake word."""
    try:
        if preferred_index is not None and str(preferred_index).isdigit():
            return int(preferred_index)
        
        cfg_file = "settings_config.json"
        if os.path.exists(cfg_file):
            with open(cfg_file, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                saved_mic = cfg.get("mic")
                if saved_mic and saved_mic != "default" and str(saved_mic).lstrip("-").isdigit():
                    idx = int(saved_mic)
                    if idx >= 0:
                        return idx
        
        devices = sd.query_devices()
        candidates = []
        for i, d in enumerate(devices):
            if d.get('max_input_channels', 0) > 0:
                name = d.get('name', '').lower()
                api = d.get('hostapi', -1)
                # Priorizar MME (0) o DirectSound (1) para compatibilidad nativa a 16kHz en Windows
                if api in (0, 1):
                    prio = 1
                    if 'varios micr' in name or 'array' in name:
                        prio = 10
                    elif 'micr' in name and 'stereo' not in name and 'mezcla' not in name and 'altavoz' not in name:
                        prio = 5
                    candidates.append((prio, i, d['name']))
        if candidates:
            candidates.sort(key=lambda x: -x[0])
            chosen = candidates[0][1]
            logger.info(f"Micrófono auto-detectado óptimo: [{chosen}] {candidates[0][2]}")
            return chosen
    except Exception as e:
        logger.warning(f"Error resolviendo mejor micrófono: {e}")
    return None

active_device_index = resolve_best_device()

def set_active_device(index):
    """Establece el micrófono activo."""
    global active_device_index
    if index is None or index == "default" or str(index) == "-1":
        active_device_index = resolve_best_device()
    else:
        try:
            active_device_index = int(index)
        except Exception:
            active_device_index = resolve_best_device()
    logger.info(f"Micrófono activo cambiado al índice {active_device_index}")

def set_barge_in_callback(callback):
    """Registra el callback a ejecutar cuando se detecta una interrupción por voz mientras Miku habla."""
    global _barge_in_callback
    _barge_in_callback = callback

def stop_speaking():
    """Detiene inmediatamente la reproducción de voz actual de Miku."""
    global _is_speaking
    _interrupt_speaking.set()
    try:
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()
    except Exception as e:
        logger.error(f"Error al detener reproducción: {e}")

def is_speaking() -> bool:
    """Indica si Miku está actualmente reproduciendo voz."""
    return _is_speaking

def _clean_text_for_speech(text: str) -> str:
    """Limpia markdown, etiquetas internas y caracteres especiales para síntesis de voz natural."""
    # Eliminar bloques de código
    cleaned = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    # Eliminar etiquetas internas [SISTEMA...], [IGNORAR], etc.
    cleaned = re.sub(r'\[.*?\]', '', cleaned)
    # Eliminar formato markdown
    cleaned = re.sub(r'[*_`#~]', '', cleaned)
    # Limpiar espacios excesivos
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

def _split_into_sentences(text: str) -> list[str]:
    """Divide el texto en oraciones naturales para habilitar streaming de audio con latencia mínima."""
    cleaned = _clean_text_for_speech(text)
    if not cleaned:
        return []
    
    # Dividir por signos de puntuación de fin de oración
    raw_sentences = re.split(r'(?<=[.!?:;\n])\s+', cleaned)
    sentences = []
    current = ""
    
    for s in raw_sentences:
        s = s.strip()
        if not s:
            continue
        # Si la frase actual acumulada es muy corta (< 18 caracteres), combinarla para fluidez
        if len(current) > 0 and len(current) + len(s) < 30:
            current += " " + s
        else:
            if current:
                sentences.append(current)
            current = s
            
    if current:
        sentences.append(current)
        
    return sentences if sentences else [cleaned]

def _barge_in_monitor():
    """Monitorea el micrófono en segundo plano mientras Miku habla para detectar interrupciones del usuario."""
    global _is_speaking, active_device_index
    if not ENABLE_BARGE_IN:
        return

    fs = 16000
    chunk_size = 1280
    consecutive_speech_frames = 0
    oww = get_oww_model()

    try:
        stream = sd.InputStream(samplerate=fs, channels=1, dtype='int16', device=active_device_index, blocksize=chunk_size)
        stream.start()
    except Exception as e:
        logger.warning(f"Barge-in monitor no pudo abrir micrófono ({e}). Modo streaming continuará sin barge-in.")
        return

    try:
        # Pequeña pausa inicial de 200ms para evitar falsos positivos al arrancar
        time.sleep(0.2)
        while _is_speaking and not _interrupt_speaking.is_set():
            if stream.read_available < chunk_size:
                time.sleep(0.02)
                continue

            chunk, _ = stream.read(chunk_size)
            audio_data = np.frombuffer(chunk, dtype=np.int16)

            # 1. Detección por Wake Word (inmune a altavoces y eco)
            if oww:
                prediction = oww.predict(audio_data)
                for model_name, score in prediction.items():
                    if score > 0.45:
                        logger.info(f"[Barge-in] Palabra clave '{model_name}' detectada (conf: {score:.2f}) mientras Miku hablaba. Interrumpiendo.")
                        stop_speaking()
                        oww.reset()
                        if _barge_in_callback:
                            _barge_in_callback()
                        return

            # 2. Detección por VAD de voz sostenida (especialmente útil con auriculares o voz clara)
            if BARGE_IN_MODE in ("hybrid", "vad") and VAD_ENABLED:
                audio_float32 = audio_data.astype(np.float32) / 32768.0
                chunks_512 = [audio_float32[:512], audio_float32[512:1024]]
                speech_detected_in_chunk = False
                for c_512 in chunks_512:
                    if len(c_512) == 512:
                        prob = vad_model(torch.from_numpy(c_512), 16000).item()
                        # Usamos un umbral estricto (0.75) para no confundir eco de altavoces
                        if prob > 0.75:
                            speech_detected_in_chunk = True
                            break

                if speech_detected_in_chunk:
                    consecutive_speech_frames += 1
                    # Requiere 4 frames consecutivos (~320ms de habla humana deliberada)
                    if consecutive_speech_frames >= 4:
                        logger.info("[Barge-in] Voz del usuario detectada mientras Miku hablaba. Interrumpiendo.")
                        stop_speaking()
                        if _barge_in_callback:
                            _barge_in_callback()
                        return
                else:
                    consecutive_speech_frames = max(0, consecutive_speech_frames - 1)

    except Exception as e:
        logger.debug(f"Excepción en barge-in monitor: {e}")
    finally:
        try:
            stream.stop()
            stream.close()
        except Exception:
            pass

async def generate_full_audio_file(text: str) -> str:
    """Generates a complete TTS audio file for the mobile app and returns its path."""
    if not text or text.strip() in [".", "", " ", "[IGNORAR]", "[INTERRUPTED]"]:
        return None
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
        temp_path = fp.name
        
    try:
        communicate = edge_tts.Communicate(text, VOICE_NAME, rate=VOICE_RATE, pitch=VOICE_PITCH)
        await communicate.save(temp_path)
        return temp_path
    except Exception as e:
        logger.error(f"Error generando archivo de audio completo: {e}")
        return None

def speak(text: str, interrupt_event: threading.Event = None):
    """
    Sintetiza y reproduce la respuesta de Miku con streaming de audio por oraciones,
    modulación de tono (pitch/rate) y soporte para interrupción en tiempo real (Barge-in).
    """
    global _is_speaking
    if not text or text.strip() in [".", "", " ", "[IGNORAR]", "[INTERRUPTED]"]:
        return

    # Detener cualquier otra voz en curso inmediatamente fuera del lock
    stop_speaking()
    
    with _speak_lock:
        # Espera activa y robusta a que el bucle de reproducción anterior termine y limpie _is_speaking.
        # Al estar dentro del lock, evitamos que dos hilos entren a reproducir al mismo tiempo.
        wait_attempts = 0
        while _is_speaking and wait_attempts < 100:
            time.sleep(0.02)
            wait_attempts += 1
            
        _interrupt_speaking.clear()
        print(f"[Miku]: {text}")

    with _pygame_lock:
        if not pygame.mixer.get_init():
            pygame.mixer.init()

    sentences = _split_into_sentences(text)
    if not sentences:
        return

    _is_speaking = True
    _interrupt_speaking.clear()

    # Iniciar monitor de interrupción por voz solo para respuestas sustanciales (> 15 caracteres)
    # Evita falsos positivos con el wake word durante saludos cortos de inicio como 'Dime'
    if len(text.strip()) > 15:
        barge_in_thread = threading.Thread(target=_barge_in_monitor, daemon=True)
        barge_in_thread.start()

    audio_queue = queue.Queue(maxsize=5)

    synthesis_done = threading.Event()
    temp_files = []

    # Trabajador de síntesis asíncrona en streaming
    def synth_worker():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def _run_synth():
            for sentence in sentences:
                if _interrupt_speaking.is_set() or (interrupt_event and interrupt_event.is_set()):
                    break

                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
                    temp_path = fp.name
                temp_files.append(temp_path)

                try:
                    communicate = edge_tts.Communicate(
                        sentence,
                        voice=VOICE_NAME,
                        rate=VOICE_RATE,
                        pitch=VOICE_PITCH
                    )
                    await communicate.save(temp_path)
                    audio_queue.put(temp_path)
                except Exception as err:
                    logger.error(f"Error sintetizando fragmento: {err}")

            synthesis_done.set()

        try:
            loop.run_until_complete(_run_synth())
        finally:
            loop.close()
            synthesis_done.set()

    synth_thread = threading.Thread(target=synth_worker, daemon=True)
    synth_thread.start()

    # Bucle de reproducción en streaming
    try:
        while True:
            if _interrupt_speaking.is_set() or (interrupt_event and interrupt_event.is_set()):
                break

            try:
                temp_path = audio_queue.get(timeout=0.15)
            except queue.Empty:
                if synthesis_done.is_set() and audio_queue.empty():
                    break
                continue

            if _interrupt_speaking.is_set() or (interrupt_event and interrupt_event.is_set()):
                break

            try:
                pygame.mixer.music.load(temp_path)
                pygame.mixer.music.set_volume(_voice_volume)
                pygame.mixer.music.play()

                # Esperar reproducción chequeando interrupción cada 30ms
                while pygame.mixer.music.get_busy():
                    if _interrupt_speaking.is_set() or (interrupt_event and interrupt_event.is_set()):
                        pygame.mixer.music.stop()
                        pygame.mixer.music.unload()
                        break
                    pygame.time.Clock().tick(30)

                pygame.mixer.music.unload()
            except Exception as play_err:
                logger.error(f"Error reproduciendo fragmento TTS: {play_err}")

    finally:
        _is_speaking = False
        _interrupt_speaking.set()
        # Limpieza de archivos temporales
        for f in temp_files:
            try:
                if os.path.exists(f):
                    os.remove(f)
            except Exception:
                pass

def record_audio(filename="temp.wav", duration=600, fs=16000, silent=False):
    global active_device_index
    if not silent:
        print(f"[Miku] Escuchando...")
        
    recording = []
    chunk_size = 2048 # Aumentado a 2048 para dar estabilidad a micrófonos por WiFi como WO Mic
    
    try:
        stream = sd.InputStream(samplerate=fs, channels=1, dtype='int16', device=active_device_index, blocksize=chunk_size)
    except Exception as e:
        logger.error(f"Error abriendo micrófono {active_device_index} a {fs}Hz: {e}")
        logger.info("El micrófono seleccionado probablemente no soporta la tasa de muestreo de 16000Hz o está desconectado. Volviendo al predeterminado.")
        active_device_index = None
        return "temp.wav"

    try:
        with stream:
            # 1. Calibración dinámica del ruido de fondo (WO Mic suele tener estática)
            ambient_chunks = []
            for _ in range(int(0.3 * (fs / chunk_size))):
                c, _ = stream.read(chunk_size)
                ambient_chunks.append(c)
            
            if ambient_chunks:
                ambient_data = np.concatenate(ambient_chunks, axis=0)
                base_rms = np.sqrt(np.mean(ambient_data.astype(np.float32)**2))
            else:
                base_rms = 40
                
            # El umbral de silencio será un poco más alto que la estática constante, o mínimo 60
            silence_threshold = max(base_rms * 1.5, 60)
            
            speech_started = False
            silence_after_speech_frames = 0
            frames_waited_for_speech = 0
            
            # Guardamos el audio de calibración para no perder la primera sílaba
            recording.extend(ambient_chunks)
            
            for _ in range(int(duration * (fs / chunk_size))):
                chunk, overflow = stream.read(chunk_size)
                recording.append(chunk)
                
                volume = np.sqrt(np.mean(chunk.astype(np.float32)**2))
                is_speech_record = False
                if VAD_ENABLED:
                    audio_float32 = chunk.flatten().astype(np.float32) / 32768.0
                    chunks_512 = np.split(audio_float32, 4)
                    for c_512 in chunks_512:
                        if vad_model(torch.from_numpy(c_512), 16000).item() > 0.4:
                            is_speech_record = True
                            break
                else:
                    is_speech_record = volume >= silence_threshold
                    
                if is_speech_record:
                    speech_started = True
                    silence_after_speech_frames = 0
                else:
                    if speech_started:
                        silence_after_speech_frames += 1
                    else:
                        frames_waited_for_speech += 1
                        
                # Si empezó a hablar y hay 0.8 segundos de silencio, terminamos de grabar la frase rápidamente
                if speech_started and silence_after_speech_frames > int(0.8 * (fs / chunk_size)):
                    break
                    
                # Timeout de 5 segundos si el usuario fue despertado pero no dijo nada
                if not speech_started and frames_waited_for_speech > int(5.0 * (fs / chunk_size)):
                    return None
    except Exception as e:
        logger.error(f"Error reading from audio stream: {e}")
        return None
                
    audio_data = np.concatenate(recording, axis=0)
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2) # 16-bit
        wf.setframerate(fs)
        wf.writeframes(audio_data.tobytes())
    return filename

def transcribe_audio(filename="temp.wav") -> str:
    if not groq_client:
        return ""
    try:
        with open(filename, "rb") as file:
            transcription = groq_client.audio.transcriptions.create(
                file=(filename, file.read()),
                model="whisper-large-v3",
                prompt="El usuario está hablando en español.",
                language="es",
                response_format="json",
                temperature=0.0
            )
            text = transcription.text.strip()
            ignore_phrases = [
                ".", "", " ", "Thank you.", "Gracias.",
                "Gracias por ver el video.", "Gracias por ver el vídeo.",
                "Gracias por ver el video", "¡Suscríbete!",
                "Subtítulos realizados por la comunidad de Amara.org"
            ]
            if text not in ignore_phrases:
                print(f"[Usuario]: {text}")
            return text
    except Exception as e:
        logger.error(f"Error de STT (Groq Whisper): {e}")
        return ""

def listen_and_transcribe() -> str:
    filename = record_audio(duration=30)
    if not filename:
        return ""
    return transcribe_audio(filename)

def wait_for_wake_word(callback, is_asleep_event):
    global active_device_index
    
    logger.info("Cargando modelo de wake word Miku ONNX...")
    oww_model = get_oww_model()
    if not oww_model:
        logger.error("No se pudo iniciar openWakeWord.")
        time.sleep(5)
        return

    fs = 16000
    chunk_size = 1280

    logger.info("Esperando palabra clave Miku Nativo Offline...")
    
    current_device = active_device_index
    try:
        stream = sd.InputStream(samplerate=fs, channels=1, dtype='int16', device=active_device_index, blocksize=chunk_size)
        stream.start()
    except Exception as e:
        logger.warning(f"Error iniciando micrófono {active_device_index} para wake word: {e}. Resolviendo mejor alternativa.")
        active_device_index = resolve_best_device()
        current_device = active_device_index
        stream = sd.InputStream(samplerate=fs, channels=1, dtype='int16', device=active_device_index, blocksize=chunk_size)
        stream.start()

    while True:
        try:
            if active_device_index != current_device:
                current_device = active_device_index
                stream.stop()
                stream.close()
                try:
                    stream = sd.InputStream(samplerate=fs, channels=1, dtype='int16', device=active_device_index, blocksize=chunk_size)
                    stream.start()
                except Exception as e:
                    logger.warning(f"Error cambiando micrófono en wake word: {e}")
                    active_device_index = resolve_best_device()
                    current_device = active_device_index
                    stream = sd.InputStream(samplerate=fs, channels=1, dtype='int16', device=active_device_index, blocksize=chunk_size)
                    stream.start()
                    
            if _wake_paused or not is_asleep_event.is_set():
                time.sleep(0.15)
                if stream.read_available > 0:
                    stream.read(stream.read_available)
                continue

            chunk, _ = stream.read(chunk_size)
            audio_data = np.frombuffer(chunk, dtype=np.int16)
            
            prediction = oww_model.predict(audio_data)
            
            for model_name, score in prediction.items():
                if score > 0.5:
                    logger.info(f"Wake word detectada con confidencia {score:.2f}!")
                    callback()
                    logger.info("Volviendo a esperar palabra clave Miku...")
                    
                    if stream.read_available > 0:
                        stream.read(stream.read_available)
                    oww_model.reset()
                    
        except Exception as e:
            time.sleep(1)
