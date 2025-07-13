# video_generator/thai_voice_engine.py - Advanced Thai voice selection and customization
import os
import tempfile
import subprocess
import uuid
import json
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from dataclasses import dataclass
import pyttsx3

class ThaiVoiceGender(Enum):
    MALE = "male"
    FEMALE = "female"
    NEUTRAL = "neutral"

class ThaiVoiceStyle(Enum):
    POWERFUL = "powerful"           # ทรงพลัง, เหมาะสำหรับ motivation
    GENTLE = "gentle"               # อ่อนโยน, เหมาะสำหรับ lofi
    PROFESSIONAL = "professional"   # เป็นทางการ
    FRIENDLY = "friendly"           # เป็นกันเอง
    DRAMATIC = "dramatic"           # ดราม่า, เน้นอารมณ์
    STORYTELLER = "storyteller"     # เล่าเรื่อง
    MEDITATION = "meditation"       # สำหรับสมาธิ
    ENERGETIC = "energetic"         # กระปรี้กระเปร่า

class ThaiVoiceSpeed(Enum):
    VERY_SLOW = 0.6
    SLOW = 0.8
    NORMAL = 1.0
    FAST = 1.2
    VERY_FAST = 1.4

class ThaiVoicePitch(Enum):
    VERY_LOW = 0.7
    LOW = 0.85
    NORMAL = 1.0
    HIGH = 1.15
    VERY_HIGH = 1.3

@dataclass
class ThaiVoiceProfile:
    id: str
    name: str
    display_name: str
    gender: ThaiVoiceGender
    style: ThaiVoiceStyle
    description: str
    sample_text: str
    recommended_for: List[str]
    voice_settings: Dict[str, Any]
    is_available: bool = True

@dataclass
class VoiceCustomization:
    speed: ThaiVoiceSpeed = ThaiVoiceSpeed.NORMAL
    pitch: ThaiVoicePitch = ThaiVoicePitch.NORMAL
    volume: float = 1.0  # 0.0 to 1.0
    emphasis_words: List[str] = None
    pause_duration: float = 1.0  # seconds between sentences
    emotion_intensity: float = 0.7  # 0.0 to 1.0
    breathing_sounds: bool = False
    
    def __post_init__(self):
        if self.emphasis_words is None:
            self.emphasis_words = []

class ThaiVoiceEngine:
    """Advanced Thai voice selection and customization engine"""
    
    def __init__(self):
        self.temp_dir = tempfile.gettempdir()
        self.voice_profiles = self._initialize_voice_profiles()
        self.tts_engines = {}
        self.ffmpeg_path = self._find_ffmpeg()
        
        # Initialize available TTS engines
        self._initialize_tts_engines()
        
        print("✅ Thai Voice Engine initialized")
    
    def _find_ffmpeg(self) -> str:
        """Find FFmpeg executable"""
        possible_paths = [
            'ffmpeg',
            '/usr/bin/ffmpeg',
            '/usr/local/bin/ffmpeg',
            'C:\\Program Files\\ffmpeg\\bin\\ffmpeg.exe',
        ]
        
        for path in possible_paths:
            try:
                result = subprocess.run([path, '-version'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    return path
            except:
                continue
        
        raise Exception("FFmpeg not found. Please install FFmpeg.")
    
    def _initialize_voice_profiles(self) -> Dict[str, ThaiVoiceProfile]:
        """Initialize Thai voice profiles"""
        profiles = {}
        
        # Male Voices
        profiles['male_powerful'] = ThaiVoiceProfile(
            id="male_powerful",
            name="powerful_male",
            display_name="ชายเสียงทรงพลัง",
            gender=ThaiVoiceGender.MALE,
            style=ThaiVoiceStyle.POWERFUL,
            description="เสียงชายที่ทรงพลัง มั่นใจ เหมาะสำหรับเนื้อหา Motivation",
            sample_text="ความแข็งแกร่งแท้จริงมาจากการเอาชนะตัวเองในวันที่ไม่อยากทำ",
            recommended_for=["motivation", "stoic", "leadership"],
            voice_settings={
                'rate': 130,
                'volume': 1.0,
                'voice_id': 'com.apple.speech.synthesis.voice.Kanya',
                'pitch_shift': -2
            }
        )
        
        profiles['male_gentle'] = ThaiVoiceProfile(
            id="male_gentle",
            name="gentle_male",
            display_name="ชายเสียงอ่อนโยน",
            gender=ThaiVoiceGender.MALE,
            style=ThaiVoiceStyle.GENTLE,
            description="เสียงชายที่อ่อนโยน สงบ เหมาะสำหรับเนื้อหา Lofi",
            sample_text="จิตใจที่สงบนิ่งคือแหล่งที่มาของความสุขที่แท้จริง",
            recommended_for=["lofi", "meditation", "relaxation"],
            voice_settings={
                'rate': 120,
                'volume': 0.8,
                'voice_id': 'com.apple.speech.synthesis.voice.Kanya',
                'pitch_shift': 0
            }
        )
        
        profiles['male_storyteller'] = ThaiVoiceProfile(
            id="male_storyteller",
            name="storyteller_male",
            display_name="ชายเล่าเรื่อง",
            gender=ThaiVoiceGender.MALE,
            style=ThaiVoiceStyle.STORYTELLER,
            description="เสียงชายที่เล่าเรื่องได้น่าฟัง มีจังหวะที่ดี",
            sample_text="ในอดีตมีนักปรัชญาท่านหนึ่งที่สอนเราเรื่องความแข็งแกร่งของจิตใจ",
            recommended_for=["storytelling", "philosophy", "education"],
            voice_settings={
                'rate': 140,
                'volume': 0.9,
                'voice_id': 'com.apple.speech.synthesis.voice.Kanya',
                'pitch_shift': -1
            }
        )
        
        # Female Voices
        profiles['female_professional'] = ThaiVoiceProfile(
            id="female_professional",
            name="professional_female",
            display_name="หญิงเสียงเป็นทางการ",
            gender=ThaiVoiceGender.FEMALE,
            style=ThaiVoiceStyle.PROFESSIONAL,
            description="เสียงหญิงที่เป็นทางการ มีความน่าเชื่อถือ",
            sample_text="การพัฒนาตนเองเป็นกระบวนการที่ต้องใช้เวลาและความอดทน",
            recommended_for=["education", "business", "formal"],
            voice_settings={
                'rate': 135,
                'volume': 0.9,
                'voice_id': 'com.apple.speech.synthesis.voice.Kanya',
                'pitch_shift': 2
            }
        )
        
        profiles['female_gentle'] = ThaiVoiceProfile(
            id="female_gentle",
            name="gentle_female",
            display_name="หญิงเสียงอ่อนโยน",
            gender=ThaiVoiceGender.FEMALE,
            style=ThaiVoiceStyle.GENTLE,
            description="เสียงหญิงที่อ่อนโยน เบา เหมาะสำหรับเนื้อหาผ่อนคลาย",
            sample_text="ให้จิตใจของเราสงบนิ่งเหมือนผืนน้ำที่ไร้คลื่น",
            recommended_for=["meditation", "relaxation", "wellness"],
            voice_settings={
                'rate': 115,
                'volume': 0.7,
                'voice_id': 'com.apple.speech.synthesis.voice.Kanya',
                'pitch_shift': 3
            }
        )
        
        profiles['female_energetic'] = ThaiVoiceProfile(
            id="female_energetic",
            name="energetic_female",
            display_name="หญิงเสียงกระปรี้กระเปร่า",
            gender=ThaiVoiceGender.FEMALE,
            style=ThaiVoiceStyle.ENERGETIC,
            description="เสียงหญิงที่มีพลัง กระปรี้กระเปร่า สร้างแรงบันดาลใจ",
            sample_text="วันนี้เป็นโอกาสใหม่ที่จะทำสิ่งดีๆ ให้กับตัวเราและคนรอบข้าง",
            recommended_for=["motivation", "energy", "inspiration"],
            voice_settings={
                'rate': 145,
                'volume': 1.0,
                'voice_id': 'com.apple.speech.synthesis.voice.Kanya',
                'pitch_shift': 4
            }
        )
        
        # Check voice availability
        for profile in profiles.values():
            profile.is_available = self._check_voice_availability(profile)
        
        return profiles
    
    def _initialize_tts_engines(self):
        """Initialize TTS engines for different voice profiles"""
        try:
            # Initialize pyttsx3 engine
            self.tts_engines['pyttsx3'] = pyttsx3.init()
            
            # Get available voices
            voices = self.tts_engines['pyttsx3'].getProperty('voices')
            
            print(f"✅ Found {len(voices)} system voices")
            
            # Log available voices for debugging
            for i, voice in enumerate(voices[:5]):  # Show first 5 voices
                print(f"  Voice {i}: {voice.id}")
                
        except Exception as e:
            print(f"⚠️  TTS engine initialization warning: {e}")
    
    def _check_voice_availability(self, profile: ThaiVoiceProfile) -> bool:
        """Check if voice profile is available on the system"""
        try:
            if 'pyttsx3' in self.tts_engines:
                engine = self.tts_engines['pyttsx3']
                voices = engine.getProperty('voices')
                
                # Check if specific voice ID exists
                voice_id = profile.voice_settings.get('voice_id')
                if voice_id:
                    for voice in voices:
                        if voice_id in voice.id:
                            return True
                
                # If specific voice not found, use any available voice
                return len(voices) > 0
            
            return False
            
        except Exception as e:
            print(f"Voice availability check failed for {profile.id}: {e}")
            return False
    
    def get_available_voices(self, filter_style: ThaiVoiceStyle = None, 
                           filter_gender: ThaiVoiceGender = None) -> List[Dict]:
        """Get list of available voice profiles"""
        voices = []
        
        for profile in self.voice_profiles.values():
            if not profile.is_available:
                continue
            
            if filter_style and profile.style != filter_style:
                continue
            
            if filter_gender and profile.gender != filter_gender:
                continue
            
            voice_info = {
                'id': profile.id,
                'display_name': profile.display_name,
                'gender': profile.gender.value,
                'style': profile.style.value,
                'description': profile.description,
                'sample_text': profile.sample_text,
                'recommended_for': profile.recommended_for
            }
            voices.append(voice_info)
        
        return voices
    
    def generate_voice_sample(self, voice_id: str, text: str = None) -> str:
        """Generate voice sample for preview"""
        if voice_id not in self.voice_profiles:
            raise ValueError(f"Voice profile '{voice_id}' not found")
        
        profile = self.voice_profiles[voice_id]
        
        if not profile.is_available:
            raise Exception(f"Voice profile '{voice_id}' is not available")
        
        # Use profile's sample text if no text provided
        if not text:
            text = profile.sample_text
        
        # Generate audio file
        output_filename = f"voice_sample_{voice_id}_{uuid.uuid4().hex[:8]}.mp3"
        output_path = os.path.join(self.temp_dir, output_filename)
        
        try:
            # Generate with basic settings
            self._generate_voice_audio(text, profile, output_path)
            
            print(f"✅ Voice sample generated: {voice_id}")
            return output_path
            
        except Exception as e:
            if os.path.exists(output_path):
                os.remove(output_path)
            raise Exception(f"Failed to generate voice sample: {e}")
    
    def generate_custom_voice(self, 
                            text: str, 
                            voice_id: str,
                            customization: VoiceCustomization = None) -> str:
        """Generate voice audio with custom settings"""
        
        if voice_id not in self.voice_profiles:
            raise ValueError(f"Voice profile '{voice_id}' not found")
        
        profile = self.voice_profiles[voice_id]
        
        if not profile.is_available:
            raise Exception(f"Voice profile '{voice_id}' is not available")
        
        if customization is None:
            customization = VoiceCustomization()
        
        # Generate audio file
        output_filename = f"custom_voice_{voice_id}_{uuid.uuid4().hex[:8]}.mp3"
        output_path = os.path.join(self.temp_dir, output_filename)
        
        try:
            # Process text with customizations
            processed_text = self._process_text_for_voice(text, customization)
            
            # Generate base audio
            temp_path = self._generate_voice_audio(processed_text, profile, None)
            
            # Apply voice customizations
            final_path = self._apply_voice_customizations(
                temp_path, customization, profile, output_path
            )
            
            # Cleanup temp file
            if os.path.exists(temp_path) and temp_path != final_path:
                os.remove(temp_path)
            
            print(f"✅ Custom voice generated: {voice_id}")
            return final_path
            
        except Exception as e:
            if os.path.exists(output_path):
                os.remove(output_path)
            raise Exception(f"Failed to generate custom voice: {e}")
    
    def _generate_voice_audio(self, text: str, profile: ThaiVoiceProfile, output_path: str = None) -> str:
        """Generate basic voice audio using TTS engine"""
        
        if not output_path:
            output_filename = f"voice_audio_{uuid.uuid4().hex[:8]}.wav"
            output_path = os.path.join(self.temp_dir, output_filename)
        
        try:
            engine = self.tts_engines.get('pyttsx3')
            if not engine:
                raise Exception("TTS engine not available")
            
            # Configure voice settings
            voices = engine.getProperty('voices')
            
            # Try to set specific voice or use first available
            voice_id = profile.voice_settings.get('voice_id')
            selected_voice = None
            
            if voice_id:
                for voice in voices:
                    if voice_id in voice.id:
                        selected_voice = voice.id
                        break
            
            if not selected_voice and voices:
                selected_voice = voices[0].id
            
            if selected_voice:
                engine.setProperty('voice', selected_voice)
            
            # Set voice properties
            rate = profile.voice_settings.get('rate', 140)
            volume = profile.voice_settings.get('volume', 1.0)
            
            engine.setProperty('rate', rate)
            engine.setProperty('volume', volume)
            
            # Generate audio
            engine.save_to_file(text, output_path)
            engine.runAndWait()
            
            return output_path
            
        except Exception as e:
            if os.path.exists(output_path):
                os.remove(output_path)
            raise Exception(f"TTS generation failed: {e}")
    
    def _process_text_for_voice(self, text: str, customization: VoiceCustomization) -> str:
        """Process text with voice customizations"""
        processed_text = text
        
        # Add emphasis to specific words
        for word in customization.emphasis_words:
            processed_text = processed_text.replace(
                word, f"<emphasis level='strong'>{word}</emphasis>"
            )
        
        # Add pauses between sentences
        if customization.pause_duration != 1.0:
            pause_ms = int(customization.pause_duration * 1000)
            processed_text = processed_text.replace(
                '. ', f'. <break time="{pause_ms}ms"/> '
            )
            processed_text = processed_text.replace(
                '! ', f'! <break time="{pause_ms}ms"/> '
            )
            processed_text = processed_text.replace(
                '? ', f'? <break time="{pause_ms}ms"/> '
            )
        
        # Add breathing sounds if requested
        if customization.breathing_sounds:
            sentences = processed_text.split('. ')
            if len(sentences) > 1:
                processed_text = '. <break time="300ms"/> '.join(sentences)
        
        return processed_text
    
    def _apply_voice_customizations(self, input_path: str, 
                                  customization: VoiceCustomization,
                                  profile: ThaiVoiceProfile,
                                  output_path: str) -> str:
        """Apply voice customizations using FFmpeg"""
        
        try:
            # Build FFmpeg filter chain for voice customizations
            filters = []
            
            # Speed adjustment
            if customization.speed != ThaiVoiceSpeed.NORMAL:
                speed_factor = customization.speed.value
                filters.append(f"atempo={speed_factor}")
            
            # Pitch adjustment
            if customization.pitch != ThaiVoicePitch.NORMAL:
                pitch_factor = customization.pitch.value
                # Add pitch shift from profile settings
                profile_pitch = profile.voice_settings.get('pitch_shift', 0)
                total_pitch = pitch_factor + (profile_pitch * 0.1)
                
                if abs(total_pitch - 1.0) > 0.05:
                    semitones = 12 * (total_pitch - 1.0)
                    filters.append(f"asetrate=44100*2^({semitones}/12),aresample=44100")
            
            # Volume adjustment
            if customization.volume != 1.0:
                filters.append(f"volume={customization.volume}")
            
            # Emotion intensity (subtle EQ adjustments)
            if customization.emotion_intensity != 0.7:
                intensity = customization.emotion_intensity
                
                if profile.style == ThaiVoiceStyle.POWERFUL:
                    # Boost mid frequencies for power
                    mid_boost = intensity * 2
                    filters.append(f"equalizer=f=2000:g={mid_boost}:w=2")
                elif profile.style == ThaiVoiceStyle.GENTLE:
                    # Reduce harsh frequencies for gentleness
                    high_cut = -intensity * 2
                    filters.append(f"treble=g={high_cut}:f=6000")
            
            # Apply filters if any
            if filters:
                filter_chain = ",".join(filters)
                
                cmd = [
                    self.ffmpeg_path,
                    '-y',
                    '-i', input_path,
                    '-af', filter_chain,
                    '-c:a', 'libmp3lame',
                    '-b:a', '192k',
                    '-ar', '44100',
                    '-ac', '2',
                    output_path
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                
                if result.returncode != 0:
                    raise Exception(f"Voice customization failed: {result.stderr}")
                
                return output_path
            else:
                # No customizations needed, convert to MP3
                cmd = [
                    self.ffmpeg_path,
                    '-y',
                    '-i', input_path,
                    '-c:a', 'libmp3lame',
                    '-b:a', '192k',
                    output_path
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                
                if result.returncode != 0:
                    raise Exception(f"Audio conversion failed: {result.stderr}")
                
                return output_path
                
        except Exception as e:
            if os.path.exists(output_path):
                os.remove(output_path)
            raise Exception(f"Failed to apply voice customizations: {e}")
    
    def get_voice_recommendations(self, content_type: str, mood: str = None) -> List[str]:
        """Get voice recommendations based on content type and mood"""
        recommendations = []
        
        # Content type mapping
        content_mapping = {
            'motivation': [ThaiVoiceStyle.POWERFUL, ThaiVoiceStyle.ENERGETIC, ThaiVoiceStyle.DRAMATIC],
            'lofi': [ThaiVoiceStyle.GENTLE, ThaiVoiceStyle.MEDITATION],
            'storytelling': [ThaiVoiceStyle.STORYTELLER, ThaiVoiceStyle.FRIENDLY],
            'education': [ThaiVoiceStyle.PROFESSIONAL, ThaiVoiceStyle.FRIENDLY],
            'meditation': [ThaiVoiceStyle.MEDITATION, ThaiVoiceStyle.GENTLE]
        }
        
        # Get recommended styles
        recommended_styles = content_mapping.get(content_type.lower(), [])
        
        # Find matching voice profiles
        for profile in self.voice_profiles.values():
            if not profile.is_available:
                continue
            
            if profile.style in recommended_styles:
                recommendations.append(profile.id)
            elif content_type.lower() in profile.recommended_for:
                recommendations.append(profile.id)
        
        # Mood-based filtering
        if mood:
            mood_filtered = []
            for voice_id in recommendations:
                profile = self.voice_profiles[voice_id]
                
                if mood.lower() in ['calm', 'peaceful', 'relaxed']:
                    if profile.style in [ThaiVoiceStyle.GENTLE, ThaiVoiceStyle.MEDITATION]:
                        mood_filtered.append(voice_id)
                elif mood.lower() in ['energetic', 'powerful', 'dynamic']:
                    if profile.style in [ThaiVoiceStyle.POWERFUL, ThaiVoiceStyle.ENERGETIC]:
                        mood_filtered.append(voice_id)
                elif mood.lower() in ['professional', 'formal']:
                    if profile.style == ThaiVoiceStyle.PROFESSIONAL:
                        mood_filtered.append(voice_id)
            
            if mood_filtered:
                recommendations = mood_filtered
        
        return recommendations[:5]  # Return top 5 recommendations
    
    def get_voice_statistics(self) -> Dict:
        """Get voice engine statistics"""
        stats = {
            'total_voices': len(self.voice_profiles),
            'available_voices': sum(1 for p in self.voice_profiles.values() if p.is_available),
            'voices_by_gender': {},
            'voices_by_style': {},
            'tts_engines': list(self.tts_engines.keys())
        }
        
        # Count by gender
        for gender in ThaiVoiceGender:
            count = sum(1 for p in self.voice_profiles.values() 
                       if p.gender == gender and p.is_available)
            stats['voices_by_gender'][gender.value] = count
        
        # Count by style
        for style in ThaiVoiceStyle:
            count = sum(1 for p in self.voice_profiles.values() 
                       if p.style == style and p.is_available)
            stats['voices_by_style'][style.value] = count
        
        return stats

# Test function
def test_thai_voice_engine():
    """Test Thai voice engine capabilities"""
    print("🎤 Testing Thai Voice Engine...")
    
    try:
        engine = ThaiVoiceEngine()
        
        print("✅ Thai Voice Engine initialized")
        
        # Test available voices
        voices = engine.get_available_voices()
        print(f"Available voices: {len(voices)}")
        
        for voice in voices[:3]:  # Show first 3
            print(f"  - {voice['display_name']}: {voice['description']}")
        
        # Test voice statistics
        stats = engine.get_voice_statistics()
        print(f"Voice statistics: {stats}")
        
        # Test recommendations
        recommendations = engine.get_voice_recommendations('motivation', 'powerful')
        print(f"Motivation recommendations: {recommendations}")
        
        print("✅ Thai Voice Engine tests completed")
        
    except Exception as e:
        print(f"❌ Thai Voice Engine test failed: {e}")

if __name__ == "__main__":
    test_thai_voice_engine()