import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
WAKE_WORD = os.getenv("WAKE_WORD", "miku").lower()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
GOOGLE_CLOUD_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

# Configuraciones de Voz y Conversación
VOICE_NAME = os.getenv("VOICE_NAME", "es-ES-ElviraNeural")
VOICE_RATE = os.getenv("VOICE_RATE", "+5%")
VOICE_PITCH = os.getenv("VOICE_PITCH", "+6Hz") # Modulación dulce y natural

# Interrupción en Tiempo Real (Barge-in / Duplex)
# Opciones: "hybrid" (wake word + voz fuerte, ideal para altavoces y auriculares), "wakeword", "vad"
ENABLE_BARGE_IN = os.getenv("ENABLE_BARGE_IN", "True").lower() in ("true", "1", "yes")
BARGE_IN_MODE = os.getenv("BARGE_IN_MODE", "hybrid")

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")





