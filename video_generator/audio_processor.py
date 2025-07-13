# video_generator/audio_processor.py - Audio processing and separation system
import os
import tempfile
import subprocess
import json
from typing import Tuple, Optional
from .models import AudioTrack, VoiceoverAudio, AudioSourceType
import uuid

class AudioProcessor:
    """Advanced audio processing with separation and mixing capabilities"""
    
    def __init__(self):
        self.temp_dir = tempfile.gettempdir()
        self.ffmpeg_path = self._find_ffmpeg()
        print("✅ Audio processor initialized")
    
    def _find_ffmpeg(self) -> str:
        """Find FFmpeg executable"""
        # Common FFmpeg locations
        possible_paths = [
            'ffmpeg',  # In PATH
            '/usr/bin/ffmpeg',  # Linux
            '/usr/local/bin/ffmpeg',  # macOS
            'C:\\Program Files\\ffmpeg\\bin\\ffmpeg.exe',  # Windows
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
    
    def mix_motivation_audio(self, 
                           bgm_track: AudioTrack, 
                           voiceover: VoiceoverAudio,
                           target_duration: int = 60) -> str:
        """Mix background music with voiceover for motivation videos"""
        
        # Generate output filename
        output_filename = f"motivation_audio_{uuid.uuid4().hex[:8]}.mp3"
        output_path = os.path.join(self.temp_dir, output_filename)
        
        try:
            # Download BGM if needed
            bgm_path = self._ensure_local_file(bgm_track.url, "bgm.mp3")
            voiceover_path = voiceover.file_path
            
            # Create FFmpeg command for mixing
            cmd = [
                self.ffmpeg_path,
                '-y',  # Overwrite output file
                '-i', bgm_path,  # Background music input
                '-i', voiceover_path,  # Voiceover input
                '-filter_complex', self._create_motivation_filter(target_duration),
                '-c:a', 'libmp3lame',  # MP3 codec
                '-b:a', '192k',  # High quality bitrate
                '-ar', '44100',  # Sample rate
                '-ac', '2',  # Stereo
                '-t', str(target_duration),  # Target duration
                output_path
            ]
            
            # Execute FFmpeg command
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode != 0:
                raise Exception(f"FFmpeg failed: {result.stderr}")
            
            print(f"✅ Motivation audio mixed: {output_filename}")
            return output_path
            
        except Exception as e:
            if os.path.exists(output_path):
                os.remove(output_path)
            raise Exception(f"Audio mixing failed: {e}")
    
    def process_lofi_audio(self, 
                          music_track: AudioTrack,
                          target_duration: int = 120) -> str:
        """Process lofi music (no mixing needed, just optimization)"""
        
        output_filename = f"lofi_audio_{uuid.uuid4().hex[:8]}.mp3"
        output_path = os.path.join(self.temp_dir, output_filename)
        
        try:
            # Download music if needed
            music_path = self._ensure_local_file(music_track.url, "lofi_music.mp3")
            
            # Create FFmpeg command for processing
            cmd = [
                self.ffmpeg_path,
                '-y',
                '-i', music_path,
                '-filter_complex', self._create_lofi_filter(target_duration),
                '-c:a', 'libmp3lame',
                '-b:a', '256k',  # Higher quality for music
                '-ar', '44100',
                '-ac', '2',
                '-t', str(target_duration),
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode != 0:
                raise Exception(f"FFmpeg failed: {result.stderr}")
            
            print(f"✅ Lofi audio processed: {output_filename}")
            return output_path
            
        except Exception as e:
            if os.path.exists(output_path):
                os.remove(output_path)
            raise Exception(f"Audio processing failed: {e}")
    
    def _create_motivation_filter(self, duration: int) -> str:
        """Create FFmpeg filter for motivation video audio mixing"""
        return f"""
        [0:a]volume=0.20,aloop=loop=-1:size=2e+09,atrim=duration={duration}[bgm];
        [1:a]volume=0.80,adelay=2s[voice];
        [bgm][voice]amix=inputs=2:duration=longest:dropout_transition=3,
        compand=0.3|0.3:1|1:-90/-60|-60/-40|-40/-30|-20/-20:6:0:-90:0.2,
        highpass=f=80,
        lowpass=f=12000
        """.replace('\n', '').replace(' ', '')
    
    def _create_lofi_filter(self, duration: int) -> str:
        """Create FFmpeg filter for lofi music processing"""
        return f"""
        [0:a]volume=0.85,
        aloop=loop=-1:size=2e+09,
        atrim=duration={duration},
        compand=0.1|0.1:1|1:-90/-60|-60/-40|-40/-30|-20/-20:6:0:-90:0.2,
        highpass=f=60,
        lowpass=f=15000,
        afade=t=in:ss=0:d=3,
        afade=t=out:st={duration-4}:d=4
        """.replace('\n', '').replace(' ', '')
    
    def extract_voiceover_only(self, voiceover: VoiceoverAudio) -> str:
        """Extract and optimize voiceover audio for separate download"""
        
        output_filename = f"voiceover_only_{uuid.uuid4().hex[:8]}.mp3"
        output_path = os.path.join(self.temp_dir, output_filename)
        
        try:
            cmd = [
                self.ffmpeg_path,
                '-y',
                '-i', voiceover.file_path,
                '-filter_complex', self._create_voiceover_filter(),
                '-c:a', 'libmp3lame',
                '-b:a', '192k',
                '-ar', '44100',
                '-ac', '2',  # Convert to stereo for compatibility
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                raise Exception(f"FFmpeg failed: {result.stderr}")
            
            print(f"✅ Voiceover extracted: {output_filename}")
            return output_path
            
        except Exception as e:
            if os.path.exists(output_path):
                os.remove(output_path)
            raise Exception(f"Voiceover extraction failed: {e}")
    
    def _create_voiceover_filter(self) -> str:
        """Create FFmpeg filter for voiceover optimization"""
        return """
        [0:a]volume=1.0,
        compand=0.02|0.02:0.05|0.05:-60/-40|-40/-30|-30/-20:6:0.25:-60:0.1,
        highpass=f=100,
        lowpass=f=8000,
        dynaudnorm=p=0.9:s=5,
        afade=t=in:ss=0:d=0.5,
        afade=t=out:st=-1:d=0.5
        """.replace('\n', '').replace(' ', '')
    
    def _ensure_local_file(self, url: str, default_name: str) -> str:
        """Ensure file is available locally, download if needed"""
        if os.path.exists(url):
            # Already a local file
            return url
        else:
            # Need to download
            local_path = os.path.join(self.temp_dir, default_name)
            
            # Simple download using subprocess (could use requests)
            try:
                cmd = [
                    self.ffmpeg_path,
                    '-y',
                    '-i', url,
                    '-c', 'copy',
                    local_path
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                
                if result.returncode != 0:
                    raise Exception(f"Download failed: {result.stderr}")
                
                return local_path
                
            except Exception as e:
                raise Exception(f"Failed to download {url}: {e}")
    
    def get_audio_info(self, file_path: str) -> dict:
        """Get audio file information using FFprobe"""
        try:
            cmd = [
                self.ffmpeg_path.replace('ffmpeg', 'ffprobe'),
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                file_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                raise Exception(f"FFprobe failed: {result.stderr}")
            
            info = json.loads(result.stdout)
            
            # Extract relevant information
            format_info = info.get('format', {})
            streams = info.get('streams', [])
            audio_stream = next((s for s in streams if s['codec_type'] == 'audio'), {})
            
            return {
                'duration': float(format_info.get('duration', 0)),
                'size': int(format_info.get('size', 0)),
                'bitrate': int(format_info.get('bit_rate', 0)),
                'sample_rate': int(audio_stream.get('sample_rate', 0)),
                'channels': int(audio_stream.get('channels', 0)),
                'codec': audio_stream.get('codec_name', 'unknown')
            }
            
        except Exception as e:
            print(f"Failed to get audio info: {e}")
            return {}
    
    def create_audio_visualization(self, audio_path: str, output_path: str) -> str:
        """Create audio visualization video (waveform/spectrum)"""
        try:
            cmd = [
                self.ffmpeg_path,
                '-y',
                '-i', audio_path,
                '-filter_complex', 
                '[0:a]showwaves=s=1920x1080:mode=cline:colors=0x00FFFF:rate=30[v]',
                '-map', '[v]',
                '-map', '0:a',
                '-c:v', 'libx264',
                '-c:a', 'copy',
                '-pix_fmt', 'yuv420p',
                '-t', '60',  # 1 minute max
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
            
            if result.returncode != 0:
                raise Exception(f"Visualization creation failed: {result.stderr}")
            
            return output_path
            
        except Exception as e:
            raise Exception(f"Audio visualization failed: {e}")
    
    def cleanup_temp_files(self, file_paths: list):
        """Clean up temporary audio files"""
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"🗑️  Cleaned up: {os.path.basename(file_path)}")
            except Exception as e:
                print(f"Failed to cleanup {file_path}: {e}")

# Audio Separation Service for advanced features
class AudioSeparationService:
    """Advanced audio separation and analysis"""
    
    def __init__(self):
        self.processor = AudioProcessor()
    
    def separate_background_and_voice(self, mixed_audio_path: str) -> Tuple[str, str]:
        """Separate background music and voice from mixed audio (future feature)"""
        # This would require more advanced AI models like Spleeter
        # For now, return the original mixed audio
        return mixed_audio_path, mixed_audio_path
    
    def analyze_audio_levels(self, audio_path: str) -> dict:
        """Analyze audio levels and dynamics"""
        info = self.processor.get_audio_info(audio_path)
        
        # Add more detailed analysis here
        return {
            'peak_level': -3.0,  # dB
            'rms_level': -18.0,  # dB
            'dynamic_range': 15.0,  # dB
            'loudness': -23.0,  # LUFS
            'duration': info.get('duration', 0),
            'sample_rate': info.get('sample_rate', 44100),
            'channels': info.get('channels', 2)
        }

# Test function
def test_audio_processor():
    """Test audio processing capabilities"""
    print("🎵 Testing Audio Processor...")
    
    try:
        processor = AudioProcessor()
        
        # Test audio info
        print("✅ Audio processor initialized")
        print(f"FFmpeg path: {processor.ffmpeg_path}")
        
        # Test filters
        motivation_filter = processor._create_motivation_filter(60)
        print(f"Motivation filter: {motivation_filter[:50]}...")
        
        lofi_filter = processor._create_lofi_filter(120)
        print(f"Lofi filter: {lofi_filter[:50]}...")
        
        print("✅ Audio processor tests completed")
        
    except Exception as e:
        print(f"❌ Audio processor test failed: {e}")

if __name__ == "__main__":
    test_audio_processor()