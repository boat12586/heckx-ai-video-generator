# video_generator/video_composer.py - Video composition engine with FFmpeg
import os
import tempfile
import subprocess
import json
import uuid
from typing import Tuple, Dict, Optional
from .models import VideoProject, MediaCollection, ProcessedVideo, VideoType
from .audio_processor import AudioProcessor

class VideoComposer:
    """Advanced video composition engine using FFmpeg"""
    
    def __init__(self):
        self.temp_dir = tempfile.gettempdir()
        self.ffmpeg_path = self._find_ffmpeg()
        self.audio_processor = AudioProcessor()
        print("✅ Video composer initialized")
    
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
    
    def compose_motivation_video(self, 
                                project: VideoProject,
                                media: MediaCollection,
                                target_duration: int = 60) -> ProcessedVideo:
        """Compose motivation video with background video, BGM, and voiceover"""
        
        output_filename = f"motivation_video_{project.id}.mp4"
        output_path = os.path.join(self.temp_dir, output_filename)
        
        # Download media files if needed
        video_path = self._ensure_local_video(media.video.url, "motivation_bg.mp4")
        bgm_path = self._ensure_local_audio(media.audio.url, "motivation_bgm.mp3")
        voiceover_path = media.voiceover.file_path if media.voiceover else None
        
        try:
            # Create complex FFmpeg filter for motivation video
            filter_complex = self._create_motivation_filter(
                target_duration, 
                has_voiceover=voiceover_path is not None
            )
            
            # Build FFmpeg command
            cmd = [
                self.ffmpeg_path,
                '-y',  # Overwrite output
                '-i', video_path,      # Input 0: Background video
                '-i', bgm_path,        # Input 1: Background music
            ]
            
            # Add voiceover input if available
            if voiceover_path:
                cmd.extend(['-i', voiceover_path])  # Input 2: Voiceover
            
            cmd.extend([
                '-filter_complex', filter_complex,
                '-map', '[video_out]',  # Map composed video
                '-map', '[audio_out]',  # Map mixed audio
                '-c:v', 'libx264',      # Video codec
                '-crf', '23',           # Video quality
                '-preset', 'medium',    # Encoding speed
                '-c:a', 'aac',          # Audio codec
                '-b:a', '192k',         # Audio bitrate
                '-ar', '44100',         # Audio sample rate
                '-ac', '2',             # Stereo audio
                '-pix_fmt', 'yuv420p',  # Pixel format for compatibility
                '-t', str(target_duration),  # Duration limit
                output_path
            ])
            
            # Execute FFmpeg command
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                raise Exception(f"Video composition failed: {result.stderr}")
            
            # Get video information
            video_info = self._get_video_info(output_path)
            
            processed_video = ProcessedVideo(
                project_id=project.id,
                video_path=output_path,
                voiceover_path=voiceover_path,
                duration=video_info.get('duration', target_duration),
                file_size=video_info.get('size', 0),
                resolution=f"{video_info.get('width', 1920)}x{video_info.get('height', 1080)}",
                format="mp4"
            )
            
            print(f"✅ Motivation video composed: {output_filename}")
            return processed_video
            
        except Exception as e:
            if os.path.exists(output_path):
                os.remove(output_path)
            raise Exception(f"Video composition failed: {e}")
    
    def compose_lofi_video(self,
                          project: VideoProject,
                          media: MediaCollection,
                          target_duration: int = 120) -> ProcessedVideo:
        """Compose lofi video with aesthetic footage and music"""
        
        output_filename = f"lofi_video_{project.id}.mp4"
        output_path = os.path.join(self.temp_dir, output_filename)
        
        # Download media files
        video_path = self._ensure_local_video(media.video.url, "lofi_bg.mp4")
        music_path = self._ensure_local_audio(media.audio.url, "lofi_music.mp3")
        
        try:
            # Create filter for lofi video
            filter_complex = self._create_lofi_filter(target_duration)
            
            cmd = [
                self.ffmpeg_path,
                '-y',
                '-i', video_path,      # Input 0: Background video
                '-i', music_path,      # Input 1: Lofi music
                '-filter_complex', filter_complex,
                '-map', '[video_out]',
                '-map', '[audio_out]',
                '-c:v', 'libx264',
                '-crf', '20',           # Higher quality for lofi aesthetic
                '-preset', 'slow',      # Better compression
                '-c:a', 'aac',
                '-b:a', '256k',         # Higher audio quality
                '-ar', '44100',
                '-ac', '2',
                '-pix_fmt', 'yuv420p',
                '-t', str(target_duration),
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=400)
            
            if result.returncode != 0:
                raise Exception(f"Lofi video composition failed: {result.stderr}")
            
            video_info = self._get_video_info(output_path)
            
            processed_video = ProcessedVideo(
                project_id=project.id,
                video_path=output_path,
                voiceover_path=None,  # No voiceover for lofi videos
                duration=video_info.get('duration', target_duration),
                file_size=video_info.get('size', 0),
                resolution=f"{video_info.get('width', 1920)}x{video_info.get('height', 1080)}",
                format="mp4"
            )
            
            print(f"✅ Lofi video composed: {output_filename}")
            return processed_video
            
        except Exception as e:
            if os.path.exists(output_path):
                os.remove(output_path)
            raise Exception(f"Lofi video composition failed: {e}")
    
    def _create_motivation_filter(self, duration: int, has_voiceover: bool = True) -> str:
        """Create FFmpeg filter for motivation video composition"""
        if has_voiceover:
            # Three inputs: video, bgm, voiceover
            return f"""
            [0:v]scale=1920:1080:force_original_aspect_ratio=increase,
            crop=1920:1080,
            loop=loop=-1:size=32767,
            setpts=PTS-STARTPTS,
            trim=duration={duration},
            fade=t=in:st=0:d=2,
            fade=t=out:st={duration-3}:d=3[video_out];
            
            [1:a]volume=0.20,
            aloop=loop=-1:size=2e+09,
            atrim=duration={duration}[bgm];
            
            [2:a]volume=0.80,
            adelay=3s[voice];
            
            [bgm][voice]amix=inputs=2:duration=longest:dropout_transition=2,
            compand=0.3|0.3:1|1:-90/-60|-60/-40|-40/-30|-20/-20:6:0:-90:0.2,
            highpass=f=80,
            lowpass=f=12000[audio_out]
            """.replace('\n', '').replace(' ', '')
        else:
            # Two inputs: video, bgm only
            return f"""
            [0:v]scale=1920:1080:force_original_aspect_ratio=increase,
            crop=1920:1080,
            loop=loop=-1:size=32767,
            setpts=PTS-STARTPTS,
            trim=duration={duration},
            fade=t=in:st=0:d=2,
            fade=t=out:st={duration-3}:d=3[video_out];
            
            [1:a]volume=0.60,
            aloop=loop=-1:size=2e+09,
            atrim=duration={duration},
            compand=0.2|0.2:1|1:-90/-60|-60/-40|-40/-30|-20/-20:6:0:-90:0.2[audio_out]
            """.replace('\n', '').replace(' ', '')
    
    def _create_lofi_filter(self, duration: int) -> str:
        """Create FFmpeg filter for lofi video composition"""
        return f"""
        [0:v]scale=1920:1080:force_original_aspect_ratio=increase,
        crop=1920:1080,
        loop=loop=-1:size=32767,
        setpts=PTS-STARTPTS,
        trim=duration={duration},
        eq=contrast=1.1:brightness=0.05:saturation=0.9,
        unsharp=5:5:0.3:3:3:0.1,
        fade=t=in:st=0:d=3,
        fade=t=out:st={duration-4}:d=4[video_out];
        
        [1:a]volume=0.85,
        aloop=loop=-1:size=2e+09,
        atrim=duration={duration},
        compand=0.1|0.1:1|1:-90/-60|-60/-40|-40/-30|-20/-20:6:0:-90:0.2,
        highpass=f=60,
        lowpass=f=15000,
        afade=t=in:ss=0:d=4,
        afade=t=out:st={duration-5}:d=5[audio_out]
        """.replace('\n', '').replace(' ', '')
    
    def _ensure_local_video(self, url: str, default_name: str) -> str:
        """Ensure video file is available locally"""
        if os.path.exists(url):
            return url
        else:
            local_path = os.path.join(self.temp_dir, default_name)
            
            try:
                cmd = [
                    self.ffmpeg_path,
                    '-y',
                    '-i', url,
                    '-c', 'copy',
                    local_path
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                
                if result.returncode != 0:
                    raise Exception(f"Video download failed: {result.stderr}")
                
                return local_path
                
            except Exception as e:
                raise Exception(f"Failed to download video {url}: {e}")
    
    def _ensure_local_audio(self, url: str, default_name: str) -> str:
        """Ensure audio file is available locally"""
        if os.path.exists(url):
            return url
        else:
            local_path = os.path.join(self.temp_dir, default_name)
            
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
                    raise Exception(f"Audio download failed: {result.stderr}")
                
                return local_path
                
            except Exception as e:
                raise Exception(f"Failed to download audio {url}: {e}")
    
    def _get_video_info(self, file_path: str) -> Dict:
        """Get video file information using FFprobe"""
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
            video_stream = next((s for s in streams if s['codec_type'] == 'video'), {})
            
            return {
                'duration': float(format_info.get('duration', 0)),
                'size': int(format_info.get('size', 0)),
                'bitrate': int(format_info.get('bit_rate', 0)),
                'width': int(video_stream.get('width', 0)),
                'height': int(video_stream.get('height', 0)),
                'fps': eval(video_stream.get('r_frame_rate', '30/1')),
                'codec': video_stream.get('codec_name', 'unknown')
            }
            
        except Exception as e:
            print(f"Failed to get video info: {e}")
            return {}
    
    def create_thumbnail(self, video_path: str, timestamp: float = 5.0) -> str:
        """Create thumbnail from video at specified timestamp"""
        thumbnail_filename = f"thumbnail_{uuid.uuid4().hex[:8]}.jpg"
        thumbnail_path = os.path.join(self.temp_dir, thumbnail_filename)
        
        try:
            cmd = [
                self.ffmpeg_path,
                '-y',
                '-i', video_path,
                '-ss', str(timestamp),
                '-vframes', '1',
                '-q:v', '2',  # High quality
                '-vf', 'scale=640:360',  # Thumbnail size
                thumbnail_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                raise Exception(f"Thumbnail creation failed: {result.stderr}")
            
            return thumbnail_path
            
        except Exception as e:
            raise Exception(f"Failed to create thumbnail: {e}")
    
    def add_subtitles(self, video_path: str, subtitle_text: str, output_path: str) -> str:
        """Add hardcoded subtitles to video"""
        try:
            # Create subtitle file
            srt_path = os.path.join(self.temp_dir, f"subtitle_{uuid.uuid4().hex[:8]}.srt")
            with open(srt_path, 'w', encoding='utf-8') as f:
                f.write("1\n00:00:05,000 --> 00:00:55,000\n")
                f.write(subtitle_text)
                f.write("\n")
            
            cmd = [
                self.ffmpeg_path,
                '-y',
                '-i', video_path,
                '-vf', f"subtitles={srt_path}:force_style='FontName=Arial,FontSize=24,PrimaryColour=&Hffffff,OutlineColour=&H000000,Outline=2'",
                '-c:a', 'copy',
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
            
            # Cleanup subtitle file
            if os.path.exists(srt_path):
                os.remove(srt_path)
            
            if result.returncode != 0:
                raise Exception(f"Subtitle addition failed: {result.stderr}")
            
            return output_path
            
        except Exception as e:
            raise Exception(f"Failed to add subtitles: {e}")
    
    def cleanup_temp_files(self, file_paths: list):
        """Clean up temporary video files"""
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"🗑️  Cleaned up: {os.path.basename(file_path)}")
            except Exception as e:
                print(f"Failed to cleanup {file_path}: {e}")

# Test function
def test_video_composer():
    """Test video composer capabilities"""
    print("🎬 Testing Video Composer...")
    
    try:
        composer = VideoComposer()
        
        print("✅ Video composer initialized")
        print(f"FFmpeg path: {composer.ffmpeg_path}")
        
        # Test filter creation
        motivation_filter = composer._create_motivation_filter(60, True)
        print(f"Motivation filter: {motivation_filter[:100]}...")
        
        lofi_filter = composer._create_lofi_filter(120)
        print(f"Lofi filter: {lofi_filter[:100]}...")
        
        print("✅ Video composer tests completed")
        
    except Exception as e:
        print(f"❌ Video composer test failed: {e}")

if __name__ == "__main__":
    test_video_composer()