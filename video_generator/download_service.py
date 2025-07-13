# video_generator/download_service.py - Download service for video generator
import os
import tempfile
import zipfile
import shutil
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from .models import VideoProject, ProcessedVideo, StorageResult
from .supabase_storage import SupabaseStorageService

class DownloadService:
    """Service for handling video and audio downloads"""
    
    def __init__(self, storage_service: SupabaseStorageService):
        self.storage = storage_service
        self.temp_dir = tempfile.gettempdir()
        self.download_dir = os.path.join(self.temp_dir, "heckx_downloads")
        
        # Create download directory if it doesn't exist
        os.makedirs(self.download_dir, exist_ok=True)
        print("✅ Download service initialized")
    
    def prepare_download_package(self, project: VideoProject) -> Dict[str, str]:
        """Prepare download package for a completed project"""
        try:
            # Get project from storage
            stored_project = self.storage.get_project(project.id)
            if not stored_project:
                raise Exception(f"Project {project.id} not found in storage")
            
            if stored_project.status.value != 'completed':
                raise Exception(f"Project {project.id} is not completed")
            
            # Create project download folder
            project_folder = os.path.join(self.download_dir, f"project_{project.id}")
            os.makedirs(project_folder, exist_ok=True)
            
            download_urls = {}
            
            # Download main video file
            video_url = stored_project.metadata.get('video_url')
            if video_url:
                video_filename = f"{project.type.value}_video_{project.id}.mp4"
                video_path = os.path.join(project_folder, video_filename)
                if self._download_file(video_url, video_path):
                    download_urls['video'] = video_path
            
            # Download voiceover file (motivation videos only)
            if project.type.value == 'motivation':
                voiceover_url = stored_project.metadata.get('voiceover_url')
                if voiceover_url:
                    voiceover_filename = f"voiceover_{project.id}.mp3"
                    voiceover_path = os.path.join(project_folder, voiceover_filename)
                    if self._download_file(voiceover_url, voiceover_path):
                        download_urls['voiceover'] = voiceover_path
            
            # Create project info file
            info_path = self._create_project_info_file(project, project_folder)
            download_urls['info'] = info_path
            
            # Create ZIP package
            zip_path = self._create_zip_package(project, project_folder)
            download_urls['zip'] = zip_path
            
            print(f"✅ Download package prepared for project: {project.id}")
            return download_urls
            
        except Exception as e:
            raise Exception(f"Failed to prepare download package: {e}")
    
    def create_bulk_download(self, project_ids: List[str]) -> str:
        """Create bulk download package for multiple projects"""
        try:
            bulk_folder = os.path.join(self.download_dir, f"bulk_download_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            os.makedirs(bulk_folder, exist_ok=True)
            
            successful_downloads = 0
            failed_projects = []
            
            for project_id in project_ids:
                try:
                    project = self.storage.get_project(project_id)
                    if project and project.status.value == 'completed':
                        download_urls = self.prepare_download_package(project)
                        
                        # Copy files to bulk folder
                        project_subfolder = os.path.join(bulk_folder, f"project_{project_id}")
                        os.makedirs(project_subfolder, exist_ok=True)
                        
                        for file_type, file_path in download_urls.items():
                            if file_type != 'zip' and os.path.exists(file_path):
                                dest_path = os.path.join(project_subfolder, os.path.basename(file_path))
                                shutil.copy2(file_path, dest_path)
                        
                        successful_downloads += 1
                    else:
                        failed_projects.append(project_id)
                        
                except Exception as e:
                    failed_projects.append(project_id)
                    print(f"Failed to download project {project_id}: {e}")
            
            # Create bulk summary
            summary_path = os.path.join(bulk_folder, "download_summary.txt")
            with open(summary_path, 'w', encoding='utf-8') as f:
                f.write(f"Bulk Download Summary\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write(f"Total Projects Requested: {len(project_ids)}\n")
                f.write(f"Successfully Downloaded: {successful_downloads}\n")
                f.write(f"Failed Downloads: {len(failed_projects)}\n\n")
                
                if failed_projects:
                    f.write("Failed Project IDs:\n")
                    for project_id in failed_projects:
                        f.write(f"- {project_id}\n")
            
            # Create bulk ZIP
            bulk_zip_path = f"{bulk_folder}.zip"
            with zipfile.ZipFile(bulk_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(bulk_folder):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, bulk_folder)
                        zipf.write(file_path, arcname)
            
            print(f"✅ Bulk download created: {successful_downloads}/{len(project_ids)} projects")
            return bulk_zip_path
            
        except Exception as e:
            raise Exception(f"Failed to create bulk download: {e}")
    
    def get_download_link(self, project_id: str, file_type: str = 'video') -> Optional[str]:
        """Get direct download link for a specific file"""
        try:
            project = self.storage.get_project(project_id)
            if not project:
                return None
            
            if file_type == 'video':
                return project.metadata.get('video_url')
            elif file_type == 'voiceover':
                return project.metadata.get('voiceover_url')
            else:
                return None
                
        except Exception as e:
            print(f"Failed to get download link: {e}")
            return None
    
    def _download_file(self, url: str, local_path: str) -> bool:
        """Download file from URL to local path"""
        try:
            import requests
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return True
            
        except Exception as e:
            print(f"Failed to download {url}: {e}")
            return False
    
    def _create_project_info_file(self, project: VideoProject, project_folder: str) -> str:
        """Create project information file"""
        info_path = os.path.join(project_folder, "project_info.txt")
        
        # Get Stoic content if available
        stoic_content = self.storage.get_stoic_content(project.id)
        
        with open(info_path, 'w', encoding='utf-8') as f:
            f.write(f"Project Information\n")
            f.write(f"==================\n\n")
            f.write(f"Project ID: {project.id}\n")
            f.write(f"Type: {project.type.value.title()}\n")
            f.write(f"Status: {project.status.value.title()}\n")
            f.write(f"Created: {project.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n")
            
            if project.completed_at:
                f.write(f"Completed: {project.completed_at.strftime('%Y-%m-%d %H:%M:%S')}\n")
            
            f.write(f"\nFiles Included:\n")
            f.write(f"- Main video file ({project.type.value}_video_{project.id}.mp4)\n")
            
            if project.type.value == 'motivation':
                f.write(f"- Voiceover audio (voiceover_{project.id}.mp3)\n")
                
                if stoic_content:
                    f.write(f"\nContent Details:\n")
                    f.write(f"Theme: {stoic_content.theme}\n")
                    f.write(f"Quote: {stoic_content.quote}\n")
                    f.write(f"Emotional Tone: {stoic_content.emotional_tone}\n")
                    f.write(f"Keywords: {', '.join(stoic_content.keywords)}\n")
            
            f.write(f"\nGenerated by Heckx AI Video Generator\n")
            f.write(f"https://github.com/heckx/ai-assistant\n")
        
        return info_path
    
    def _create_zip_package(self, project: VideoProject, project_folder: str) -> str:
        """Create ZIP package for project"""
        zip_filename = f"{project.type.value}_project_{project.id}.zip"
        zip_path = os.path.join(self.download_dir, zip_filename)
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(project_folder):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, project_folder)
                    zipf.write(file_path, arcname)
        
        return zip_path
    
    def get_project_history_downloads(self, limit: int = 20) -> List[Dict]:
        """Get download information for recent projects"""
        try:
            projects = self.storage.get_project_history(limit)
            download_info = []
            
            for project in projects:
                if project.status.value == 'completed':
                    info = {
                        'project_id': project.id,
                        'type': project.type.value,
                        'created_at': project.created_at.isoformat(),
                        'completed_at': project.completed_at.isoformat() if project.completed_at else None,
                        'video_url': project.metadata.get('video_url'),
                        'voiceover_url': project.metadata.get('voiceover_url'),
                        'file_sizes': project.metadata.get('file_sizes', {}),
                        'downloadable': True
                    }
                    download_info.append(info)
            
            return download_info
            
        except Exception as e:
            print(f"Failed to get project history: {e}")
            return []
    
    def cleanup_old_downloads(self, days_old: int = 7) -> int:
        """Clean up old download files"""
        try:
            from datetime import timedelta
            import time
            
            cutoff_time = time.time() - (days_old * 24 * 60 * 60)
            cleaned_count = 0
            
            for item in os.listdir(self.download_dir):
                item_path = os.path.join(self.download_dir, item)
                
                try:
                    if os.path.getmtime(item_path) < cutoff_time:
                        if os.path.isfile(item_path):
                            os.remove(item_path)
                            cleaned_count += 1
                        elif os.path.isdir(item_path):
                            shutil.rmtree(item_path)
                            cleaned_count += 1
                except Exception as e:
                    print(f"Failed to cleanup {item_path}: {e}")
            
            print(f"✅ Cleaned up {cleaned_count} old download files")
            return cleaned_count
            
        except Exception as e:
            print(f"Download cleanup failed: {e}")
            return 0
    
    def get_download_stats(self) -> Dict:
        """Get download service statistics"""
        try:
            stats = {
                'download_dir': self.download_dir,
                'total_files': 0,
                'total_size': 0,
                'available_projects': 0
            }
            
            # Count files in download directory
            if os.path.exists(self.download_dir):
                for root, dirs, files in os.walk(self.download_dir):
                    stats['total_files'] += len(files)
                    for file in files:
                        file_path = os.path.join(root, file)
                        try:
                            stats['total_size'] += os.path.getsize(file_path)
                        except:
                            pass
            
            # Count available projects
            storage_stats = self.storage.get_storage_stats()
            stats['available_projects'] = storage_stats.get('completed_projects', 0)
            
            return stats
            
        except Exception as e:
            print(f"Failed to get download stats: {e}")
            return {}

# Test function
def test_download_service():
    """Test download service capabilities"""
    print("💾 Testing Download Service...")
    
    try:
        # Mock storage service for testing
        from unittest.mock import Mock
        mock_storage = Mock()
        
        service = DownloadService(mock_storage)
        
        print("✅ Download service initialized")
        print(f"Download directory: {service.download_dir}")
        
        # Test stats
        stats = service.get_download_stats()
        print(f"Download stats: {stats}")
        
        print("✅ Download service tests completed")
        
    except Exception as e:
        print(f"❌ Download service test failed: {e}")

if __name__ == "__main__":
    test_download_service()