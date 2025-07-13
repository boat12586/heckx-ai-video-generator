# video_generator/preview_service.py - Video preview generation service
import os
import tempfile
import subprocess
import uuid
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from .models import VideoProject, VideoFootage, AudioTrack, StoicContent
from .pixabay_service import PixabayService, LofiMusicLibrary
from .stoic_content import StoicContentGenerator
from .audio_processor import AudioProcessor

class VideoPreviewService:
    """Service for generating video previews before full generation"""
    
    def __init__(self):
        self.temp_dir = tempfile.gettempdir()
        self.preview_dir = os.path.join(self.temp_dir, "heckx_previews")
        self.ffmpeg_path = self._find_ffmpeg()
        self.audio_processor = AudioProcessor()
        
        # Create preview directory
        os.makedirs(self.preview_dir, exist_ok=True)
        
        print("✅ Video Preview Service initialized")
    
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
    
    def generate_motivation_preview(self,
                                   video_options: List[VideoFootage],
                                   audio_options: List[AudioTrack],
                                   stoic_content: StoicContent,
                                   preview_duration: int = 15) -> Dict:
        """Generate motivation video preview with multiple options"""
        
        preview_id = str(uuid.uuid4())[:8]
        preview_results = []
        
        try:
            print(f"🎬 Generating motivation previews: {preview_id}")
            
            # Limit to top 3 video options for preview
            video_samples = video_options[:3]
            audio_samples = audio_options[:2]
            
            preview_count = 0
            for i, video in enumerate(video_samples):
                for j, audio in enumerate(audio_samples):
                    if preview_count >= 4:  # Limit total previews
                        break
                    
                    try:
                        preview_path = self._create_motivation_preview(
                            video, audio, stoic_content, 
                            preview_duration, f"{preview_id}_{i}_{j}"
                        )
                        
                        if preview_path:
                            # Generate thumbnail
                            thumbnail_path = self._generate_thumbnail(
                                preview_path, f"{preview_id}_{i}_{j}_thumb.jpg"
                            )
                            
                            preview_info = {
                                'preview_id': f"{preview_id}_{i}_{j}",
                                'video_path': preview_path,
                                'thumbnail_path': thumbnail_path,
                                'video_source': {
                                    'id': video.id,
                                    'tags': video.tags[:5],
                                    'category': video.category,
                                    'duration': video.duration
                                },
                                'audio_source': {
                                    'id': audio.id,
                                    'title': audio.title,
                                    'category': audio.category
                                },
                                'content_theme': stoic_content.theme,
                                'file_size': os.path.getsize(preview_path) if os.path.exists(preview_path) else 0
                            }
                            
                            preview_results.append(preview_info)
                            preview_count += 1
                            
                    except Exception as e:
                        print(f"Failed to create preview {i}_{j}: {e}")
                        continue
            
            return {
                'preview_id': preview_id,
                'type': 'motivation',
                'previews': preview_results,
                'total_previews': len(preview_results),
                'stoic_content': {
                    'theme': stoic_content.theme,
                    'quote': stoic_content.quote,
                    'emotional_tone': stoic_content.emotional_tone,
                    'keywords': stoic_content.keywords
                },
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            raise Exception(f"Failed to generate motivation previews: {e}")
    
    def generate_lofi_preview(self,
                             video_options: List[VideoFootage],
                             audio_options: List[AudioTrack],
                             preview_duration: int = 20) -> Dict:
        """Generate lofi video preview with multiple combinations"""
        
        preview_id = str(uuid.uuid4())[:8]
        preview_results = []
        
        try:
            print(f"🎵 Generating lofi previews: {preview_id}")
            
            # Sample options for preview
            video_samples = video_options[:3]
            audio_samples = audio_options[:3]
            
            preview_count = 0
            for i, video in enumerate(video_samples):
                for j, audio in enumerate(audio_samples):
                    if preview_count >= 6:  # More previews for lofi
                        break
                    
                    try:
                        preview_path = self._create_lofi_preview(
                            video, audio, preview_duration, f"{preview_id}_{i}_{j}"
                        )
                        
                        if preview_path:
                            # Generate thumbnail
                            thumbnail_path = self._generate_thumbnail(
                                preview_path, f"{preview_id}_{i}_{j}_thumb.jpg"
                            )
                            
                            preview_info = {
                                'preview_id': f"{preview_id}_{i}_{j}",
                                'video_path': preview_path,
                                'thumbnail_path': thumbnail_path,
                                'video_source': {
                                    'id': video.id,
                                    'tags': video.tags[:5],
                                    'category': video.category,
                                    'duration': video.duration
                                },
                                'audio_source': {
                                    'id': audio.id,
                                    'title': audio.title,
                                    'category': audio.category,
                                    'genre': audio.metadata.get('genre', 'unknown'),
                                    'mood': audio.metadata.get('mood', 'unknown')
                                },
                                'file_size': os.path.getsize(preview_path) if os.path.exists(preview_path) else 0
                            }
                            
                            preview_results.append(preview_info)
                            preview_count += 1
                            
                    except Exception as e:
                        print(f"Failed to create lofi preview {i}_{j}: {e}")
                        continue
            
            return {
                'preview_id': preview_id,
                'type': 'lofi',
                'previews': preview_results,
                'total_previews': len(preview_results),
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            raise Exception(f"Failed to generate lofi previews: {e}")
    
    def _create_motivation_preview(self,
                                  video: VideoFootage,
                                  audio: AudioTrack,
                                  stoic_content: StoicContent,
                                  duration: int,
                                  preview_id: str) -> str:
        """Create a single motivation preview"""
        
        output_filename = f"motivation_preview_{preview_id}.mp4"
        output_path = os.path.join(self.preview_dir, output_filename)
        
        try:
            # Download video and audio
            video_path = self._download_media(video.url, f"prev_video_{preview_id}.mp4")
            audio_path = self._download_media(audio.url, f"prev_audio_{preview_id}.mp3")
            
            # Create simplified preview filter (no voiceover for speed)
            filter_complex = f"""
            [0:v]scale=1280:720:force_original_aspect_ratio=increase,
            crop=1280:720,
            setpts=PTS-STARTPTS,
            trim=duration={duration},
            fade=t=in:st=0:d=1,
            fade=t=out:st={duration-2}:d=2,
            drawtext=text='Preview - {stoic_content.theme}':fontsize=32:fontcolor=white:x=(w-tw)/2:y=h-th-20:enable='between(t,2,{duration-2})'[video_out];
            
            [1:a]volume=0.7,
            atrim=duration={duration},
            afade=t=in:ss=0:d=1,
            afade=t=out:st={duration-2}:d=2[audio_out]
            """.replace('\n', '').replace(' ', '')
            
            cmd = [
                self.ffmpeg_path,
                '-y',
                '-i', video_path,
                '-i', audio_path,
                '-filter_complex', filter_complex,
                '-map', '[video_out]',
                '-map', '[audio_out]',
                '-c:v', 'libx264',
                '-crf', '28',  # Lower quality for preview
                '-preset', 'fast',
                '-c:a', 'aac',
                '-b:a', '128k',
                '-ar', '44100',
                '-ac', '2',
                '-pix_fmt', 'yuv420p',
                '-t', str(duration),
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode != 0:
                raise Exception(f"Preview generation failed: {result.stderr}")
            
            # Cleanup temp files
            for temp_file in [video_path, audio_path]:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            
            return output_path
            
        except Exception as e:
            if os.path.exists(output_path):
                os.remove(output_path)
            raise Exception(f"Motivation preview creation failed: {e}")
    
    def _create_lofi_preview(self,
                            video: VideoFootage,
                            audio: AudioTrack,
                            duration: int,
                            preview_id: str) -> str:
        """Create a single lofi preview"""
        
        output_filename = f"lofi_preview_{preview_id}.mp4"
        output_path = os.path.join(self.preview_dir, output_filename)
        
        try:
            # Download video and audio
            video_path = self._download_media(video.url, f"prev_video_{preview_id}.mp4")
            audio_path = self._download_media(audio.url, f"prev_audio_{preview_id}.mp3")
            
            # Create lofi preview filter with aesthetic effects
            filter_complex = f"""
            [0:v]scale=1280:720:force_original_aspect_ratio=increase,
            crop=1280:720,
            setpts=PTS-STARTPTS,
            trim=duration={duration},
            eq=contrast=1.1:brightness=0.1:saturation=0.8,
            fade=t=in:st=0:d=2,
            fade=t=out:st={duration-3}:d=3,
            drawtext=text='Lofi Preview - {audio.category}':fontsize=28:fontcolor=white@0.8:x=(w-tw)/2:y=h-th-20:enable='between(t,2,{duration-3})'[video_out];
            
            [1:a]volume=0.8,
            atrim=duration={duration},
            highpass=f=60,
            lowpass=f=15000,
            afade=t=in:ss=0:d=2,
            afade=t=out:st={duration-3}:d=3[audio_out]
            """.replace('\n', '').replace(' ', '')
            
            cmd = [
                self.ffmpeg_path,
                '-y',
                '-i', video_path,
                '-i', audio_path,
                '-filter_complex', filter_complex,
                '-map', '[video_out]',
                '-map', '[audio_out]',
                '-c:v', 'libx264',
                '-crf', '26',  # Better quality for lofi aesthetic
                '-preset', 'fast',
                '-c:a', 'aac',
                '-b:a', '192k',
                '-ar', '44100',
                '-ac', '2',
                '-pix_fmt', 'yuv420p',
                '-t', str(duration),
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode != 0:
                raise Exception(f"Lofi preview generation failed: {result.stderr}")
            
            # Cleanup temp files
            for temp_file in [video_path, audio_path]:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            
            return output_path
            
        except Exception as e:
            if os.path.exists(output_path):
                os.remove(output_path)
            raise Exception(f"Lofi preview creation failed: {e}")
    
    def _generate_thumbnail(self, video_path: str, thumbnail_name: str) -> str:
        """Generate thumbnail from video"""
        thumbnail_path = os.path.join(self.preview_dir, thumbnail_name)
        
        try:
            cmd = [
                self.ffmpeg_path,
                '-y',
                '-i', video_path,
                '-ss', '3',  # Take frame at 3 seconds
                '-vframes', '1',
                '-q:v', '2',
                '-vf', 'scale=320:180',
                thumbnail_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return thumbnail_path
            else:
                print(f"Thumbnail generation failed: {result.stderr}")
                return None
                
        except Exception as e:
            print(f"Failed to generate thumbnail: {e}")
            return None
    
    def _download_media(self, url: str, filename: str) -> str:
        """Download media file for preview"""
        local_path = os.path.join(self.preview_dir, filename)
        
        try:
            if url.startswith('http'):
                # Download from URL
                cmd = [
                    self.ffmpeg_path,
                    '-y',
                    '-i', url,
                    '-t', '30',  # Only download first 30 seconds for preview
                    '-c', 'copy',
                    local_path
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                
                if result.returncode != 0:
                    raise Exception(f"Download failed: {result.stderr}")
            else:
                # Local file, just copy
                import shutil
                shutil.copy2(url, local_path)
            
            return local_path
            
        except Exception as e:
            raise Exception(f"Failed to download {url}: {e}")
    
    def get_preview_info(self, preview_id: str) -> Optional[Dict]:
        """Get information about a specific preview"""
        try:
            preview_files = [f for f in os.listdir(self.preview_dir) if f.startswith(f"motivation_preview_{preview_id}") or f.startswith(f"lofi_preview_{preview_id}")]
            
            if not preview_files:
                return None
            
            previews = []
            for file in preview_files:
                file_path = os.path.join(self.preview_dir, file)
                if os.path.exists(file_path):
                    previews.append({
                        'filename': file,
                        'path': file_path,
                        'size': os.path.getsize(file_path),
                        'created': datetime.fromtimestamp(os.path.getctime(file_path)).isoformat()
                    })
            
            return {
                'preview_id': preview_id,
                'files': previews,
                'total_files': len(previews)
            }
            
        except Exception as e:
            print(f"Failed to get preview info: {e}")
            return None
    
    def cleanup_old_previews(self, hours_old: int = 24) -> int:
        """Clean up old preview files"""
        try:
            import time
            cutoff_time = time.time() - (hours_old * 3600)
            cleaned_count = 0
            
            for file in os.listdir(self.preview_dir):
                file_path = os.path.join(self.preview_dir, file)
                
                try:
                    if os.path.getmtime(file_path) < cutoff_time:
                        os.remove(file_path)
                        cleaned_count += 1
                except Exception as e:
                    print(f"Failed to cleanup {file_path}: {e}")
            
            print(f"✅ Cleaned up {cleaned_count} old preview files")
            return cleaned_count
            
        except Exception as e:
            print(f"Preview cleanup failed: {e}")
            return 0
    
    def get_preview_stats(self) -> Dict:
        """Get preview service statistics"""
        try:
            stats = {
                'preview_dir': self.preview_dir,
                'total_files': 0,
                'total_size': 0,
                'video_previews': 0,
                'thumbnails': 0
            }
            
            if os.path.exists(self.preview_dir):
                for file in os.listdir(self.preview_dir):
                    file_path = os.path.join(self.preview_dir, file)
                    if os.path.isfile(file_path):
                        stats['total_files'] += 1
                        stats['total_size'] += os.path.getsize(file_path)
                        
                        if file.endswith('.mp4'):
                            stats['video_previews'] += 1
                        elif file.endswith('.jpg'):
                            stats['thumbnails'] += 1
            
            # Convert size to MB
            stats['total_size_mb'] = round(stats['total_size'] / (1024 * 1024), 2)
            
            return stats
            
        except Exception as e:
            print(f"Failed to get preview stats: {e}")
            return {}

# Test function
def test_preview_service():
    """Test preview service capabilities"""
    print("🎬 Testing Video Preview Service...")
    
    try:
        service = VideoPreviewService()
        
        print("✅ Preview service initialized")
        print(f"Preview directory: {service.preview_dir}")
        
        # Test stats
        stats = service.get_preview_stats()
        print(f"Preview stats: {stats}")
        
        print("✅ Preview service tests completed")
        
    except Exception as e:
        print(f"❌ Preview service test failed: {e}")

if __name__ == "__main__":
    test_preview_service()