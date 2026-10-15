# Audio y Voz 🎙️🔊

Todo lo relacionado con las cuerdas vocales y oídos de Miku reside en `audio_handler.py`.

## `audio_handler.py`
Este es un script complejo que unifica STT (Speech-to-Text) y TTS (Text-to-Speech) de forma asíncrona.

- **Wake Word (Escucha Pasiva)**:
  - `wait_for_wake_word()` / `get_oww_model()`: Utiliza el motor `openwakeword` local para escuchar pasivamente la palabra "Miku". No envía datos a internet hasta que reconoce su nombre.

- **Síntesis de Voz (TTS)**:
  - `speak(texto)`: Función de alto nivel.
  - `synth_worker()` y `_run_synth()`: Hilos trabajadores que procesan bloques de oraciones (`_split_into_sentences`). Permite que Miku comience a hablar la primera oración mientras el LLM sigue generando el resto de la respuesta (Streaming).

- **Interrupciones (Barge-In)**:
  - `_barge_in_monitor()`: Monitorea activamente la entrada del micrófono *mientras* Miku está hablando. Si el usuario interrumpe a Miku, ejecuta `stop_speaking()` para detener la reproducción de audio abruptamente y poner atención a la nueva instrucción.

- **Reconocimiento de Voz (STT)**:
  - `record_audio()`, `transcribe_audio()`, `listen_and_transcribe()`: Utiliza APIs como Whisper para convertir el comando de voz del usuario a texto.

## Enlaces Relacionados
- 👉 Volver a [[Home]]
