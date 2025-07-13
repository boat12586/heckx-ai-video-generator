# main.py
import time
import threading
import numpy as np
import whisper
import sounddevice as sd
from queue import Queue
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from langchain.prompts import PromptTemplate
from langchain_community.llms import Ollama
from tts import TextToSpeechService
from config import Config
from real_web_search import RealWebSearchService
from conversation_logger import ConversationLogger
from audio_processor import EnhancedAudioProcessor
from enhanced_ai import EnhancedAIAssistant

console = Console()
stt = whisper.load_model(Config.WHISPER_MODEL)
tts = TextToSpeechService()
web_search = RealWebSearchService()
logger = ConversationLogger()
audio_processor = EnhancedAudioProcessor()
enhanced_ai = EnhancedAIAssistant(Config)

# Enhanced prompt template with personality - Thai language (Professional Version)
template = """
คุณคือ Heckx ผู้ช่วย AI ระดับโปรฟีเชื่อนัล สร้างโดย bobo คุณมีความสามารถพิเศษในการ:

🎯 ให้ข้อมูลที่แม่นยำและทันสมัย
🖼️ อธิบายได้เห็นภาพและละเอียดลึกซึ้ง
📚 วิเคราะห์และสรุปข้อมูลซับซ้อนให้เข้าใจง่าย
🎭 มีบุคลิกภาพที่เป็นมิตรและมีอารมณ์ขัน
🔍 ค้นหาข้อมูลจากแหล่งที่เชื่อถือได้

หลักการตอบ:
- ตอบภาษาไทยเสมอ
- อธิบายอย่างละเอียดและเห็นภาพ
- ใช้ตัวอย่างและเปรียบเทียบ
- ให้ข้อมูลเพิ่มเติมที่เป็นประโยชน์
- ความยาวการตอบ: 50-500 คำ (ขึ้นอยู่กับความซับซ้อนของคำถาม)
- สำหรับเรื่องประวัติศาสตร์/ข้อมูลข้อเท็จจริง: ให้รายละเอียดครบถ้วน

เมื่อได้รับข้อมูลเพิ่มเติมจากการค้นหาเว็บ ให้นำมาประกอบการตอบ

ประวัติการสนทนา:
{history}

ผู้ใช้พูดว่า: {input}

คำตอบของคุณ (อธิบายอย่างละเอียดและเห็นภาพ):
"""
PROMPT = PromptTemplate(input_variables=["history", "input"], template=template)
chain = ConversationChain(
    prompt=PROMPT,
    verbose=False,
    memory=ConversationBufferMemory(
        ai_prefix="Heckx:",
        human_prefix="You:",
        k=Config.CONVERSATION_HISTORY_LIMIT
    ),
    llm=Ollama(model=Config.OLLAMA_MODEL),
)

class VoiceAssistant:
    def __init__(self):
        self.console = console
        self.data_queue = Queue()
        self.stop_event = threading.Event()
        self.is_recording = False
        self.session_id = logger.start_session("Voice mode session")

    def record_audio(self):
        """Captures audio and puts it in the queue."""
        def callback(indata, frames, time, status):
            if status:
                self.console.print(f"[red]Audio Error: {status}")
            if self.is_recording:
                audio_level = np.abs(indata).mean()
                if audio_level > Config.AUDIO_THRESHOLD:
                    self.data_queue.put(bytes(indata))

        with sd.RawInputStream(
            samplerate=Config.SAMPLE_RATE,
            dtype=Config.DTYPE,
            channels=Config.CHANNELS,
            callback=callback
        ):
            while not self.stop_event.is_set():
                time.sleep(0.1)

    def transcribe(self, audio_np: np.ndarray) -> str:
        """Transcribes audio to text."""
        result = stt.transcribe(audio_np, fp16=False)
        text = result["text"].strip()
        return text

    def get_response(self, text: str) -> str:
        """Gets enhanced response with context awareness."""
        start_time = time.time()
        
        try:
            # ตรวจสอบว่าควรค้นหาเว็บหรือไม่
            web_info = ""
            if web_search.should_search_web(text):
                print("🔍 กำลังค้นหาข้อมูลล่าสุด...")
                search_results = web_search.search_real_time(text)
                web_info = web_search.format_search_results(search_results, text)
            
            # ใช้ Enhanced AI สำหรับการตอบ
            response = enhanced_ai.get_enhanced_response(text, web_info)
            
            # บันทึกการสนทนา
            response_time = time.time() - start_time
            logger.log_conversation(
                user_input=text,
                ai_response=response,
                response_time=response_time,
                mode="voice",
                metadata={
                    'web_search_used': bool(web_info),
                    'enhanced_ai_used': True,
                    'response_time': response_time
                }
            )
            
            return response
            
        except Exception as e:
            print(f"Error in get_response: {e}")
            return f"ขออภัย เกิดข้อผิดพลาด: {str(e)}"

    def play_audio(self, sample_rate: int, audio_array: np.ndarray):
        """Plays audio array."""
        sd.play(audio_array, sample_rate)
        sd.wait()

    def display_welcome(self):
        """Displays welcome message."""
        welcome_text = Text.assemble(
            ("ยินดีต้อนรับสู่ผู้ช่วย AI ด้วยเสียง!\n", "cyan bold"),
            ("กด Enter เพื่อพูด, กด Enter อีกครั้งเพื่อหยุด\n", "white"),
            ("กด Ctrl+C เพื่อออก มาคุยกันเถอะ!", "cyan")
        )
        self.console.print(Panel(welcome_text, title="Heckx", border_style="blue"))

    def run(self):
        """Main loop for the assistant with enhanced audio."""
        self.display_welcome()
        
        # ทดสอบระบบเสียงก่อน
        if not audio_processor.test_audio_system():
            self.console.print(Panel(
                "⚠️  ระบบเสียงมีปัญหา กรุณาตรวจสอบไมโครโฟน",
                title="คำเตือน",
                border_style="yellow"
            ))
        
        try:
            while True:
                self.console.input(
                    "[green]กด Enter เพื่อเริ่มพูด (ระบบจะฟังอัตโนมัติ)...[/green]"
                )
                
                # ใช้ระบบบันทึกเสียงแบบอัจฉริยะ
                with self.console.status("[blue]🎤 กำลังฟัง... (พูดได้เลย)", spinner="dots"):
                    audio_data = audio_processor.smart_recording(duration_limit=30.0)

                if audio_data.size > 0:
                    with self.console.status("[blue]🧠 กำลังแปลงเสียง...", spinner="dots"):
                        text = audio_processor.transcribe_with_whisper(audio_data, stt)
                    
                    if text.strip():
                        self.console.print(Panel(
                            f"คุณ: {text}",
                            title="✅ สิ่งที่คุณพูด",
                            border_style="yellow"
                        ))

                        with self.console.status("[blue]🤔 กำลังคิด...", spinner="moon"):
                            response = self.get_response(text)
                            sample_rate, audio_array = tts.long_form_synthesize(response)

                        self.console.print(Panel(
                            f"Heckx: {response}",
                            title="🤖 คำตอบของ Heckx",
                            border_style="cyan"
                        ))
                        
                        self.play_audio(sample_rate, audio_array)
                    else:
                        self.console.print(Panel(
                            "❌ ไม่สามารถแปลงเสียงเป็นข้อความได้ กรุณาลองใหม่",
                            title="ข้อผิดพลาด",
                            border_style="red"
                        ))
                else:
                    self.console.print(Panel(
                        "🔇 ไม่พบเสียงพูด กรุณาลองใหม่",
                        title="ไม่มีเสียง",
                        border_style="yellow"
                    ))

        except KeyboardInterrupt:
            self.console.print("\n[red]🛑 กำลังปิดระบบอย่างปลอดภัย...")
            logger.end_session()
            self.console.print(Panel(
                "ขอบคุณที่คุยด้วย! กลับมาคุยกันใหม่นะ! 👋",
                title="ลาก่อน",
                border_style="blue"
            ))

if __name__ == "__main__":
    assistant = VoiceAssistant()
    assistant.run()