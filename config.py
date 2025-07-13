# config.py
class Config:
    WHISPER_MODEL = "base"  # รองรับหลายภาษารวมทั้งภาษาไทย
    SAMPLE_RATE = 16000
    CHANNELS = 1
    DTYPE = "int16"
    OLLAMA_MODEL = "llama3.2:1b"  # ใช้ model ที่เพิ่งดาวน์โหลด
    AUDIO_THRESHOLD = 0.01  # Minimum audio level to consider as speech
    MAX_SILENCE_SECONDS = 2  # Seconds of silence before stopping recording
    CONVERSATION_HISTORY_LIMIT = 5  # Number of previous exchanges to keep