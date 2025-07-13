# video_generator/main_service.py - Main orchestration service for video generation
import os
import uuid
from typing import Dict, Optional, List
from datetime import datetime

from .models import VideoProject, VideoType, ProjectStatus, MediaCollection
from .stoic_content import StoicContentGenerator
from .pixabay_service import PixabayService, LofiMusicLibrary
from .audio_processor import AudioProcessor
from .video_composer import VideoComposer
from .supabase_storage import SupabaseStorageService
from .download_service import DownloadService

class VideoGeneratorService:
    """Main orchestration service for video generation system"""
    
    def __init__(self):
        # Initialize all service components
        self.stoic_generator = StoicContentGenerator()
        self.pixabay_service = None
        self.lofi_library = LofiMusicLibrary()
        self.audio_processor = AudioProcessor()
        self.video_composer = VideoComposer()
        self.storage_service = None
        self.download_service = None
        
        # Initialize Pixabay service if API key is available
        try:
            self.pixabay_service = PixabayService()
        except Exception as e:
            print(f"⚠️  Pixabay service not available: {e}")
        
        # Initialize Supabase services if credentials are available
        try:
            self.storage_service = SupabaseStorageService()
            self.download_service = DownloadService(self.storage_service)
        except Exception as e:
            print(f"⚠️  Supabase services not available: {e}")
        
        print("✅ Video Generator Service initialized")
    
    def generate_motivation_video(self, 
                                 theme: str = None,
                                 duration: int = 60,
                                 custom_script: str = None) -> Dict:
        """Generate complete motivation video with Stoic content"""
        
        # Create new project
        project = VideoProject(
            id=str(uuid.uuid4()),
            type=VideoType.MOTIVATION,
            status=ProjectStatus.INITIALIZING,
            metadata={
                'theme': theme,
                'duration': duration,
                'custom_script': custom_script,
                'started_at': datetime.now().isoformat()
            }
        )
        
        try:
            # Store project in database
            if self.storage_service:
                self.storage_service.create_project_record(project)
            
            print(f"🎬 Starting motivation video generation: {project.id}")
            
            # Step 1: Generate Stoic content
            self._update_progress(project, ProjectStatus.GENERATING_CONTENT, 20)
            
            if custom_script:
                # Use custom script
                stoic_content = self.stoic_generator.generate_content(theme)
                stoic_content.voiceover_script = custom_script
                stoic_content.narrative = custom_script
            else:
                # Generate Stoic content
                stoic_content = self.stoic_generator.generate_content(theme)
            
            # Store Stoic content
            if self.storage_service:
                self.storage_service.store_stoic_content(project.id, stoic_content)
            
            # Step 2: Acquire media assets
            self._update_progress(project, ProjectStatus.ACQUIRING_MEDIA, 40)
            media = self._acquire_motivation_media()
            
            # Step 3: Process audio
            self._update_progress(project, ProjectStatus.PROCESSING_AUDIO, 60)
            
            # Generate voiceover
            voiceover = self.stoic_generator.generate_voiceover_audio(stoic_content)
            
            # Create media collection
            media_collection = MediaCollection(
                video=media['video'],
                audio=media['audio'],
                voiceover=voiceover
            )
            
            # Step 4: Compose video
            self._update_progress(project, ProjectStatus.COMPOSING_VIDEO, 80)
            processed_video = self.video_composer.compose_motivation_video(
                project, media_collection, duration
            )
            
            # Step 5: Upload and finalize
            self._update_progress(project, ProjectStatus.UPLOADING, 90)
            
            result = self._finalize_project(project, processed_video, voiceover.file_path)
            
            self._update_progress(project, ProjectStatus.COMPLETED, 100)
            
            print(f"✅ Motivation video completed: {project.id}")
            return result
            
        except Exception as e:
            error_msg = f"Motivation video generation failed: {e}"
            print(f"❌ {error_msg}")
            
            if self.storage_service:
                self.storage_service.update_project_status(
                    project.id, ProjectStatus.FAILED.value, error_message=error_msg
                )
            
            raise Exception(error_msg)
    
    def generate_lofi_video(self, 
                           category: str = None,
                           duration: int = 120) -> Dict:
        """Generate lofi video with aesthetic footage and music"""
        
        # Create new project
        project = VideoProject(
            id=str(uuid.uuid4()),
            type=VideoType.LOFI,
            status=ProjectStatus.INITIALIZING,
            metadata={
                'category': category,
                'duration': duration,
                'started_at': datetime.now().isoformat()
            }
        )
        
        try:
            # Store project in database
            if self.storage_service:
                self.storage_service.create_project_record(project)
            
            print(f"🎵 Starting lofi video generation: {project.id}")
            
            # Step 1: Acquire media assets
            self._update_progress(project, ProjectStatus.ACQUIRING_MEDIA, 30)
            media = self._acquire_lofi_media(category)
            
            # Step 2: Process audio
            self._update_progress(project, ProjectStatus.PROCESSING_AUDIO, 50)
            
            # Create media collection (no voiceover for lofi)
            media_collection = MediaCollection(
                video=media['video'],
                audio=media['audio'],
                voiceover=None
            )
            
            # Step 3: Compose video
            self._update_progress(project, ProjectStatus.COMPOSING_VIDEO, 80)
            processed_video = self.video_composer.compose_lofi_video(
                project, media_collection, duration
            )
            
            # Step 4: Upload and finalize
            self._update_progress(project, ProjectStatus.UPLOADING, 90)
            
            result = self._finalize_project(project, processed_video, None)
            
            self._update_progress(project, ProjectStatus.COMPLETED, 100)
            
            print(f"✅ Lofi video completed: {project.id}")
            return result
            
        except Exception as e:
            error_msg = f"Lofi video generation failed: {e}"
            print(f"❌ {error_msg}")
            
            if self.storage_service:
                self.storage_service.update_project_status(
                    project.id, ProjectStatus.FAILED.value, error_message=error_msg
                )
            
            raise Exception(error_msg)
    
    def _acquire_motivation_media(self) -> Dict:
        """Acquire video and audio assets for motivation video"""
        media = {}
        
        # Get video footage
        if self.pixabay_service:
            video = self.pixabay_service.get_random_video('motivation')
            if not video:
                raise Exception("Failed to acquire motivation video footage")
            media['video'] = video
        else:
            raise Exception("Pixabay service not available")
        
        # Get background music
        bgm = self.pixabay_service.get_random_background_music()
        if not bgm:
            raise Exception("Failed to acquire background music")
        media['audio'] = bgm
        
        return media
    
    def _acquire_lofi_media(self, category: str = None) -> Dict:
        """Acquire video and audio assets for lofi video"""
        media = {}
        
        # Get lofi video footage
        if self.pixabay_service:
            video = self.pixabay_service.get_random_video('lofi')
            if not video:
                raise Exception("Failed to acquire lofi video footage")
            media['video'] = video
        else:
            raise Exception("Pixabay service not available")
        
        # Get lofi music
        if category:
            tracks = self.lofi_library.search_tracks([category])
            if tracks:
                media['audio'] = tracks[0]
            else:
                media['audio'] = self.lofi_library.get_random_track()
        else:
            media['audio'] = self.lofi_library.get_random_track()
        
        return media
    
    def _finalize_project(self, project: VideoProject, processed_video, voiceover_path: str = None) -> Dict:
        """Finalize project by uploading files and updating database"""
        
        if not self.storage_service:
            # Return local file paths if no storage
            return {
                'project_id': project.id,
                'video_path': processed_video.video_path,
                'voiceover_path': voiceover_path,
                'storage': 'local'
            }
        
        # Upload video file
        video_url = self.storage_service.upload_video_file(project.id, processed_video.video_path)
        if not video_url:
            raise Exception("Failed to upload video file")
        
        # Upload voiceover file (motivation videos only)
        voiceover_url = None
        if voiceover_path:
            voiceover_url = self.storage_service.upload_voiceover_file(project.id, voiceover_path)
        
        # Calculate file sizes
        file_sizes = {
            'video': os.path.getsize(processed_video.video_path) if os.path.exists(processed_video.video_path) else 0
        }
        
        if voiceover_path and os.path.exists(voiceover_path):
            file_sizes['voiceover'] = os.path.getsize(voiceover_path)
        
        # Store complete project
        storage_result = self.storage_service.store_complete_project(
            project, video_url, voiceover_url, file_sizes
        )
        
        # Cleanup temporary files
        temp_files = [processed_video.video_path]
        if voiceover_path:
            temp_files.append(voiceover_path)
        
        self.video_composer.cleanup_temp_files(temp_files)
        
        return {
            'project_id': project.id,
            'video_url': video_url,
            'voiceover_url': voiceover_url,
            'storage_result': storage_result,
            'storage': 'supabase'
        }
    
    def _update_progress(self, project: VideoProject, status: ProjectStatus, progress: int):
        """Update project progress"""
        project.status = status
        project.progress = progress
        
        if self.storage_service:
            self.storage_service.update_project_status(
                project.id, status.value, progress
            )
        
        print(f"📊 {project.id}: {status.value} ({progress}%)")
    
    def get_project_status(self, project_id: str) -> Optional[Dict]:
        """Get current status of a project"""
        if not self.storage_service:
            return None
        
        project = self.storage_service.get_project(project_id)
        if not project:
            return None
        
        return {
            'project_id': project.id,
            'type': project.type.value,
            'status': project.status.value,
            'progress': project.progress,
            'created_at': project.created_at.isoformat(),
            'completed_at': project.completed_at.isoformat() if project.completed_at else None,
            'error_message': project.error_message,
            'metadata': project.metadata
        }
    
    def get_project_history(self, limit: int = 20) -> List[Dict]:
        """Get project history"""
        if not self.storage_service:
            return []
        
        projects = self.storage_service.get_project_history(limit)
        
        return [
            {
                'project_id': p.id,
                'type': p.type.value,
                'status': p.status.value,
                'progress': p.progress,
                'created_at': p.created_at.isoformat(),
                'completed_at': p.completed_at.isoformat() if p.completed_at else None,
                'metadata': p.metadata
            }
            for p in projects
        ]
    
    def get_download_package(self, project_id: str) -> Optional[Dict]:
        """Get download package for a project"""
        if not self.download_service:
            return None
        
        project = self.storage_service.get_project(project_id)
        if not project:
            return None
        
        try:
            download_urls = self.download_service.prepare_download_package(project)
            return {
                'project_id': project_id,
                'download_urls': download_urls,
                'available': True
            }
        except Exception as e:
            return {
                'project_id': project_id,
                'error': str(e),
                'available': False
            }
    
    def get_service_status(self) -> Dict:
        """Get overall service status"""
        status = {
            'video_generator': True,
            'stoic_content': self.stoic_generator.tts_engine is not None,
            'pixabay': self.pixabay_service is not None,
            'lofi_library': True,
            'audio_processor': True,
            'video_composer': True,
            'storage': self.storage_service is not None,
            'downloads': self.download_service is not None
        }
        
        # Get statistics if storage is available
        if self.storage_service:
            storage_stats = self.storage_service.get_storage_stats()
            status['statistics'] = storage_stats
        
        if self.download_service:
            download_stats = self.download_service.get_download_stats()
            status['download_stats'] = download_stats
        
        return status
    
    def cleanup_old_projects(self, days_old: int = 30) -> Dict:
        """Clean up old projects and files"""
        results = {
            'storage_cleanup': 0,
            'download_cleanup': 0
        }
        
        if self.storage_service:
            results['storage_cleanup'] = self.storage_service.cleanup_old_projects(days_old)
        
        if self.download_service:
            results['download_cleanup'] = self.download_service.cleanup_old_downloads(days_old // 4)  # Clean downloads more frequently
        
        return results

# Test function
def test_video_generator_service():
    """Test the main video generator service"""
    print("🎬 Testing Video Generator Service...")
    
    try:
        service = VideoGeneratorService()
        
        # Test service status
        status = service.get_service_status()
        print(f"Service status: {status}")
        
        # Test Stoic themes
        themes = service.stoic_generator.get_available_themes()
        print(f"Available themes: {themes}")
        
        # Test lofi categories
        lofi_tracks = service.lofi_library.search_tracks(['เงียบสงบ'])
        print(f"Lofi tracks found: {len(lofi_tracks)}")
        
        print("✅ Video Generator Service tests completed")
        
    except Exception as e:
        print(f"❌ Service test failed: {e}")

if __name__ == "__main__":
    test_video_generator_service()