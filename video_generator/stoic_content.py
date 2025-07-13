# video_generator/stoic_content.py - Stoic content generation with Thai TTS
import random
import os
import tempfile
from typing import List, Dict
from datetime import datetime
from .models import StoicContent, VoiceoverAudio
import pyttsx3
import uuid

class StoicContentGenerator:
    def __init__(self):
        self.stoic_themes = {
            "inner_strength": {
                "theme": "ความแข็งแกร่งจากภายใน",
                "keywords": ["แข็งแกร่ง", "จิตใจ", "อุปสรรค", "เอาชนะ"],
                "quotes": [
                    "ความแข็งแกร่งแท้จริงมาจากการเอาชนะตัวเองในวันที่ไม่อยากทำ",
                    "อุปสรรคในเส้นทาง คือ เส้นทาง ไม่ใช่สิ่งขวางทาง",
                    "ทุกวันที่คุณไม่ยอมแพ้ คือวันที่คุณชนะแล้ว",
                    "จิตใจที่แข็งแกร่งไม่ได้เกิดจากการไม่มีปัญหา แต่เกิดจากการเผชิญหน้ากับปัญหา"
                ],
                "narratives": [
                    """
                    ในชีวิตเรามีสองประเภทของความแข็งแกร่ง
                    ความแข็งแกร่งของร่างกาย และความแข็งแกร่งของจิตใจ
                    
                    ร่างกายที่แข็งแรงช่วยให้เราทำงานได้ดี
                    แต่จิตใจที่แข็งแกร่งช่วยให้เราอยู่รอดได้
                    
                    ทุกวันที่คุณเลือกลุกขึ้นเมื่อไม่อยากลุก
                    ทุกครั้งที่คุณเลือกทำเมื่อไม่อยากทำ
                    คุณกำลังสร้างความแข็งแกร่งที่ไม่มีใครพรากไปได้
                    
                    อุปสรรคไม่ได้มาขวางทาง อุปสรรคคือทาง
                    ทุกความยากลำบากคือโอกาสในการเติบโต
                    """
                ]
            },
            
            "acceptance": {
                "theme": "การยอมรับในสิ่งที่ควบคุมไม่ได้",
                "keywords": ["ยอมรับ", "ควบคุม", "ปล่อยวาง", "ความสงบ"],
                "quotes": [
                    "สิ่งที่อยู่ในอำนาจเราคือความคิด การกระทำ และการตัดสินใจ",
                    "อย่าเสียเวลากับสิ่งที่เปลี่ยนแปลงไม่ได้ จงมุ่งมั่นกับสิ่งที่อยู่ในมือเรา",
                    "ความสงบใจเกิดขึ้นเมื่อเรารู้จักแยกแยะสิ่งที่ควบคุมได้และควบคุมไม่ได้",
                    "การยอมรับไม่ใช่การยอมแพ้ แต่เป็นการเลือกสู้ในสนามรบที่ชนะได้"
                ],
                "narratives": [
                    """
                    ปรัชญา Stoic สอนเราเรื่องการแบ่งแยก
                    สิ่งที่เราควบคุมได้ และสิ่งที่เราควบคุมไม่ได้
                    
                    สิ่งที่เราควบคุมได้คือ ความคิด การกระทำ และการตอบสนองของเรา
                    สิ่งที่เราควบคุมไม่ได้คือ ผู้คน เหตุการณ์ และผลลัพธ์
                    
                    ความสงบใจเกิดขึ้นเมื่อเรารู้จักแยกแยะสองสิ่งนี้
                    และมุ่งมั่นกับสิ่งที่อยู่ในอำนาจของเราเท่านั้น
                    
                    การยอมรับไม่ใช่การยอมแพ้
                    แต่เป็นการเลือกใช้พลังงานอย่างชาญฉลาด
                    """
                ]
            },
            
            "purpose": {
                "theme": "การใช้ชีวิตอย่างมีจุดหมาย",
                "keywords": ["จุดหมาย", "ชีวิต", "คุณค่า", "ความหมาย"],
                "quotes": [
                    "ชีวิตที่มีความหมายไม่ได้วัดจากความยาว แต่วัดจากความลึก",
                    "คุณคือสิ่งที่คุณทำซ้ำๆ ความเป็นเลิศจึงไม่ใช่การกระทำ แต่เป็นนิสัย",
                    "ทุกการกระทำเล็กๆ ที่สอดคล้องกับค่านิยมของเรา คือการก้าวสู่ชีวิตที่มีความหมาย",
                    "จุดหมายของชีวิตไม่ใช่การมีความสุข แต่เป็นการมีคุณค่า"
                ],
                "narratives": [
                    """
                    ชีวิตที่ยิ่งใหญ่ไม่ได้เกิดจากโชคชาตา
                    แต่เกิดจากการเลือกที่จะทำสิ่งที่มีความหมาย
                    
                    ทุกการกระทำเล็กๆ ที่สอดคล้องกับค่านิยมของเรา
                    ทุกการตัดสินใจที่ยึดหลักการมากกว่าความสะดวก
                    ก็คือการก้าวเข้าสู่ชีวิตที่มีจุดหมาย
                    
                    ความสำเร็จไม่ได้วัดจากสิ่งที่เราได้รับ
                    แต่วัดจากสิ่งที่เราให้
                    
                    คุณคือสิ่งที่คุณทำซ้ำๆ เลือกอย่างชาญฉลาด
                    """
                ]
            },
            
            "resilience": {
                "theme": "การเผชิญหน้ากับความทุกข์",
                "keywords": ["ความทุกข์", "เผชิญหน้า", "แก้ไข", "เติบโต"],
                "quotes": [
                    "ความทุกข์คือครูที่ดีที่สุด มันสอนเราในสิ่งที่ความสุขทำไม่ได้",
                    "เมื่อคุณไม่สามารถเปลี่ยนสถานการณ์ได้ คุณต้องเปลี่ยนตัวเอง",
                    "ในความยากลำบาก เราค้นพบความแข็งแกร่งที่ไม่เคยรู้ว่ามี",
                    "ความทุกข์ไม่ใช่ศัตรู แต่เป็นครูที่มาสอนเราเติบโต"
                ],
                "narratives": [
                    """
                    ความทุกข์ไม่ใช่ศัตรู แต่เป็นครู
                    มันมาเพื่อสอนเราในสิ่งที่ความสุขสอนไม่ได้
                    
                    ในความยากลำบาก เราค้นพบความแข็งแกร่งที่ไม่เคยรู้ว่ามี
                    ในความล้มเหลว เราเรียนรู้บทเรียนที่ประเมินค่าไม่ได้
                    ในความเจ็บปวด เราพัฒนาความเข้าใจที่ลึกซึ้ง
                    
                    อย่ากลัวความทุกข์ จงเผชิญหน้ากับมัน
                    เพราะมันคือประตูสู่การเติบโตที่แท้จริง
                    
                    ทุกวิกฤตคือโอกาส ทุกปัญหาคือบทเรียน
                    """
                ]
            }
        }
        
        self.tts_engine = None
        self.setup_tts()
    
    def setup_tts(self):
        """Setup Thai TTS engine"""
        try:
            self.tts_engine = pyttsx3.init()
            
            # Get available voices
            voices = self.tts_engine.getProperty('voices')
            
            # Try to find Thai voice or use default
            thai_voice = None
            for voice in voices:
                if 'th' in voice.id.lower() or 'thai' in voice.id.lower():
                    thai_voice = voice.id
                    break
            
            if thai_voice:
                self.tts_engine.setProperty('voice', thai_voice)
            
            # Set speech properties for powerful delivery
            self.tts_engine.setProperty('rate', 140)  # Slightly slower for impact
            self.tts_engine.setProperty('volume', 1.0)  # Maximum volume
            
            print("✅ Thai TTS engine initialized successfully")
            
        except Exception as e:
            print(f"❌ TTS initialization failed: {e}")
            self.tts_engine = None
    
    def generate_content(self, theme: str = None) -> StoicContent:
        """Generate Stoic content for motivation video"""
        # Select theme
        if theme and theme in self.stoic_themes:
            selected_theme = self.stoic_themes[theme]
        else:
            selected_theme = random.choice(list(self.stoic_themes.values()))
        
        # Select quote and narrative
        quote = random.choice(selected_theme["quotes"])
        narrative = random.choice(selected_theme["narratives"])
        
        # Create voiceover script
        voiceover_script = self.create_voiceover_script(narrative, quote)
        
        return StoicContent(
            theme=selected_theme["theme"],
            quote=quote,
            narrative=narrative.strip(),
            voiceover_script=voiceover_script,
            keywords=selected_theme["keywords"],
            emotional_tone="powerful"
        )
    
    def create_voiceover_script(self, narrative: str, quote: str) -> str:
        """Create structured voiceover script with directions"""
        return f"""
[เสียงลึก มีพลัง เริ่มช้าๆ แล้วเร็วขึ้น]

{narrative.strip()}

[หยุดชั่วครู่ เสียงแน่วแน่]

จำไว้เสมอ...

[เสียงดังขึ้น เน้นทุกคำ]

"{quote}"

[เงียบครู่หนึ่ง แล้วปิดท้ายด้วยเสียงเบา]

เวลาที่จะเปลี่ยนแปลงคือตอนนี้
เริ่มต้นกันเถอะ
        """.strip()
    
    def generate_voiceover_audio(self, content: StoicContent) -> VoiceoverAudio:
        """Generate Thai voiceover audio from content"""
        if not self.tts_engine:
            raise Exception("TTS engine not available")
        
        # Clean script for TTS (remove directions)
        clean_script = self.clean_script_for_tts(content.voiceover_script)
        
        # Generate unique filename
        filename = f"voiceover_{uuid.uuid4().hex[:8]}.mp3"
        temp_dir = tempfile.gettempdir()
        file_path = os.path.join(temp_dir, filename)
        
        try:
            # Configure TTS for powerful delivery
            self.tts_engine.setProperty('rate', 130)  # Slower for emphasis
            self.tts_engine.setProperty('volume', 1.0)
            
            # Generate audio
            self.tts_engine.save_to_file(clean_script, file_path)
            self.tts_engine.runAndWait()
            
            # Read audio data
            with open(file_path, 'rb') as f:
                audio_data = f.read()
            
            # Estimate duration (rough calculation)
            word_count = len(clean_script.split())
            estimated_duration = word_count * 0.6  # ~0.6 seconds per word in Thai
            
            return VoiceoverAudio(
                script=clean_script,
                voice_style="powerful_thai_male",
                audio_data=audio_data,
                duration=estimated_duration,
                file_path=file_path,
                metadata={
                    "theme": content.theme,
                    "generated_at": datetime.now().isoformat(),
                    "voice_settings": {
                        "rate": 130,
                        "volume": 1.0,
                        "language": "th-TH"
                    }
                }
            )
            
        except Exception as e:
            if os.path.exists(file_path):
                os.remove(file_path)
            raise Exception(f"Voiceover generation failed: {e}")
    
    def clean_script_for_tts(self, script: str) -> str:
        """Remove direction markers and clean script for TTS"""
        lines = script.split('\n')
        clean_lines = []
        
        for line in lines:
            line = line.strip()
            # Skip direction lines (contain brackets)
            if line and not (line.startswith('[') and line.endswith(']')):
                # Remove quotes around the main quote
                if line.startswith('"') and line.endswith('"'):
                    line = line[1:-1]
                clean_lines.append(line)
        
        # Join with proper pauses
        clean_script = ' ... '.join(clean_lines)
        
        # Add natural pauses
        clean_script = clean_script.replace('จำไว้เสมอ', 'จำไว้เสมอ ... ')
        clean_script = clean_script.replace('เริ่มต้นกันเถอะ', ' ... เริ่มต้นกันเถอะ')
        
        return clean_script
    
    def get_available_themes(self) -> List[str]:
        """Get list of available Stoic themes"""
        return list(self.stoic_themes.keys())
    
    def get_theme_info(self, theme: str) -> Dict:
        """Get information about a specific theme"""
        return self.stoic_themes.get(theme, {})

# Test function
def test_stoic_content_generator():
    """Test the Stoic content generator"""
    generator = StoicContentGenerator()
    
    print("🧠 Testing Stoic Content Generator...")
    
    # Test content generation
    content = generator.generate_content("inner_strength")
    
    print(f"📋 Theme: {content.theme}")
    print(f"💬 Quote: {content.quote}")
    print(f"📝 Narrative: {content.narrative[:100]}...")
    print(f"🎤 Script: {content.voiceover_script[:100]}...")
    
    # Test voiceover generation
    try:
        voiceover = generator.generate_voiceover_audio(content)
        print(f"🔊 Voiceover generated: {len(voiceover.audio_data)} bytes")
        print(f"⏱️  Duration: {voiceover.duration:.1f} seconds")
        print(f"💾 File: {voiceover.file_path}")
    except Exception as e:
        print(f"❌ Voiceover generation failed: {e}")

if __name__ == "__main__":
    test_stoic_content_generator()