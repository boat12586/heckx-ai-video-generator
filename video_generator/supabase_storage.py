# video_generator/supabase_storage.py - Supabase storage integration
import os
import json
from datetime import datetime
from typing import Optional, Dict, List
from supabase import create_client, Client
from .models import VideoProject, StorageResult, ProcessedVideo, StoicContent

class SupabaseStorageService:
    """Supabase integration for video generator storage and database"""
    
    def __init__(self, url: str = None, key: str = None):
        self.url = url or os.getenv('SUPABASE_URL')
        self.key = key or os.getenv('SUPABASE_ANON_KEY')
        
        if not self.url or not self.key:
            raise ValueError("Supabase URL and key are required")
        
        try:
            self.supabase: Client = create_client(self.url, self.key)
            print("✅ Supabase client initialized")
        except Exception as e:
            raise Exception(f"Failed to initialize Supabase client: {e}")
    
    def create_project_record(self, project: VideoProject) -> VideoProject:
        """Create project record in database"""
        try:
            data = {
                'id': project.id,
                'type': project.type.value,
                'status': project.status.value,
                'progress': project.progress,
                'metadata': project.metadata or {},
                'created_at': project.created_at.isoformat(),
                'error_message': project.error_message
            }
            
            result = self.supabase.table('video_projects').insert(data).execute()
            
            if result.data:
                print(f"✅ Project record created: {project.id}")
                return project
            else:
                raise Exception("Failed to create project record")
                
        except Exception as e:
            raise Exception(f"Database error creating project: {e}")
    
    def update_project_status(self, 
                             project_id: str, 
                             status: str, 
                             progress: int = None,
                             error_message: str = None) -> bool:
        """Update project status and progress"""
        try:
            update_data = {
                'status': status,
                'updated_at': datetime.now().isoformat()
            }
            
            if progress is not None:
                update_data['progress'] = progress
            
            if error_message:
                update_data['error_message'] = error_message
            
            if status == 'completed':
                update_data['completed_at'] = datetime.now().isoformat()
            
            result = self.supabase.table('video_projects').update(update_data).eq('id', project_id).execute()
            
            if result.data:
                print(f"✅ Project status updated: {project_id} -> {status}")
                return True
            return False
            
        except Exception as e:
            print(f"❌ Failed to update project status: {e}")
            return False
    
    def store_stoic_content(self, project_id: str, content: StoicContent) -> bool:
        """Store Stoic content data"""
        try:
            data = {
                'project_id': project_id,
                'theme': content.theme,
                'quote': content.quote,
                'narrative': content.narrative,
                'voiceover_script': content.voiceover_script,
                'keywords': content.keywords,
                'emotional_tone': content.emotional_tone,
                'created_at': datetime.now().isoformat()
            }
            
            result = self.supabase.table('stoic_content').insert(data).execute()
            
            if result.data:
                print(f"✅ Stoic content stored for project: {project_id}")
                return True
            return False
            
        except Exception as e:
            print(f"❌ Failed to store Stoic content: {e}")
            return False
    
    def upload_video_file(self, project_id: str, video_path: str) -> Optional[str]:
        """Upload video file to Supabase storage"""
        try:
            bucket_name = 'generated-videos'
            file_name = f"{project_id}/video.mp4"
            
            # Read video file
            with open(video_path, 'rb') as f:
                video_data = f.read()
            
            # Upload to storage
            result = self.supabase.storage.from_(bucket_name).upload(
                file_name, 
                video_data,
                file_options={
                    "content-type": "video/mp4",
                    "cache-control": "3600"
                }
            )
            
            if result.data:
                # Get public URL
                public_url = self.supabase.storage.from_(bucket_name).get_public_url(file_name)
                print(f"✅ Video uploaded: {file_name}")
                return public_url
            else:
                print(f"❌ Video upload failed: {result}")
                return None
                
        except Exception as e:
            print(f"❌ Video upload error: {e}")
            return None
    
    def upload_voiceover_file(self, project_id: str, voiceover_path: str) -> Optional[str]:
        """Upload voiceover MP3 file to Supabase storage"""
        try:
            bucket_name = 'generated-audio'
            file_name = f"{project_id}/voiceover.mp3"
            
            # Read audio file
            with open(voiceover_path, 'rb') as f:
                audio_data = f.read()
            
            # Upload to storage
            result = self.supabase.storage.from_(bucket_name).upload(
                file_name,
                audio_data,
                file_options={
                    "content-type": "audio/mpeg",
                    "cache-control": "3600"
                }
            )
            
            if result.data:
                # Get public URL
                public_url = self.supabase.storage.from_(bucket_name).get_public_url(file_name)
                print(f"✅ Voiceover uploaded: {file_name}")
                return public_url
            else:
                print(f"❌ Voiceover upload failed: {result}")
                return None
                
        except Exception as e:
            print(f"❌ Voiceover upload error: {e}")
            return None
    
    def store_complete_project(self, 
                              project: VideoProject,
                              video_url: str,
                              voiceover_url: str = None,
                              file_sizes: Dict[str, int] = None) -> StorageResult:
        """Store complete project with all URLs"""
        try:
            # Update project with URLs
            update_data = {
                'status': 'completed',
                'progress': 100,
                'video_url': video_url,
                'voiceover_url': voiceover_url,
                'completed_at': datetime.now().isoformat(),
                'file_sizes': file_sizes or {}
            }
            
            result = self.supabase.table('video_projects').update(update_data).eq('id', project.id).execute()
            
            if result.data:
                storage_result = StorageResult(
                    project_id=project.id,
                    video_url=video_url,
                    voiceover_url=voiceover_url,
                    storage_size=sum(file_sizes.values()) if file_sizes else 0,
                    uploaded_at=datetime.now()
                )
                
                print(f"✅ Project completed and stored: {project.id}")
                return storage_result
            else:
                raise Exception("Failed to update project with URLs")
                
        except Exception as e:
            raise Exception(f"Failed to store complete project: {e}")
    
    def get_project(self, project_id: str) -> Optional[VideoProject]:
        """Retrieve project by ID"""
        try:
            result = self.supabase.table('video_projects').select('*').eq('id', project_id).execute()
            
            if result.data and len(result.data) > 0:
                data = result.data[0]
                
                from .models import VideoType, ProjectStatus
                
                project = VideoProject(
                    id=data['id'],
                    type=VideoType(data['type']),
                    status=ProjectStatus(data['status']),
                    progress=data['progress'],
                    created_at=datetime.fromisoformat(data['created_at']),
                    completed_at=datetime.fromisoformat(data['completed_at']) if data['completed_at'] else None,
                    error_message=data.get('error_message'),
                    metadata=data.get('metadata', {})
                )
                
                return project
            return None
            
        except Exception as e:
            print(f"❌ Failed to get project: {e}")
            return None
    
    def get_project_history(self, limit: int = 50) -> List[VideoProject]:
        """Get project history"""
        try:
            result = self.supabase.table('video_projects').select('*').order('created_at', desc=True).limit(limit).execute()
            
            projects = []
            if result.data:
                from .models import VideoType, ProjectStatus
                
                for data in result.data:
                    project = VideoProject(
                        id=data['id'],
                        type=VideoType(data['type']),
                        status=ProjectStatus(data['status']),
                        progress=data['progress'],
                        created_at=datetime.fromisoformat(data['created_at']),
                        completed_at=datetime.fromisoformat(data['completed_at']) if data['completed_at'] else None,
                        error_message=data.get('error_message'),
                        metadata=data.get('metadata', {})
                    )
                    projects.append(project)
            
            return projects
            
        except Exception as e:
            print(f"❌ Failed to get project history: {e}")
            return []
    
    def get_stoic_content(self, project_id: str) -> Optional[StoicContent]:
        """Get Stoic content for project"""
        try:
            result = self.supabase.table('stoic_content').select('*').eq('project_id', project_id).execute()
            
            if result.data and len(result.data) > 0:
                data = result.data[0]
                
                content = StoicContent(
                    theme=data['theme'],
                    quote=data['quote'],
                    narrative=data['narrative'],
                    voiceover_script=data['voiceover_script'],
                    keywords=data['keywords'],
                    emotional_tone=data['emotional_tone']
                )
                
                return content
            return None
            
        except Exception as e:
            print(f"❌ Failed to get Stoic content: {e}")
            return None
    
    def delete_project_files(self, project_id: str) -> bool:
        """Delete project files from storage"""
        try:
            success = True
            
            # Delete video file
            try:
                self.supabase.storage.from_('generated-videos').remove([f"{project_id}/video.mp4"])
                print(f"✅ Deleted video file for project: {project_id}")
            except Exception as e:
                print(f"⚠️  Failed to delete video file: {e}")
                success = False
            
            # Delete voiceover file
            try:
                self.supabase.storage.from_('generated-audio').remove([f"{project_id}/voiceover.mp3"])
                print(f"✅ Deleted voiceover file for project: {project_id}")
            except Exception as e:
                print(f"⚠️  Failed to delete voiceover file: {e}")
                success = False
            
            return success
            
        except Exception as e:
            print(f"❌ Failed to delete project files: {e}")
            return False
    
    def get_storage_stats(self) -> Dict[str, any]:
        """Get storage usage statistics"""
        try:
            # Get project count by type
            result = self.supabase.table('video_projects').select('type, status').execute()
            
            stats = {
                'total_projects': len(result.data) if result.data else 0,
                'motivation_videos': 0,
                'lofi_videos': 0,
                'completed_projects': 0,
                'failed_projects': 0,
                'storage_usage': 0  # Would need additional queries to calculate
            }
            
            if result.data:
                for project in result.data:
                    if project['type'] == 'motivation':
                        stats['motivation_videos'] += 1
                    elif project['type'] == 'lofi':
                        stats['lofi_videos'] += 1
                    
                    if project['status'] == 'completed':
                        stats['completed_projects'] += 1
                    elif project['status'] == 'failed':
                        stats['failed_projects'] += 1
            
            return stats
            
        except Exception as e:
            print(f"❌ Failed to get storage stats: {e}")
            return {}
    
    def cleanup_old_projects(self, days_old: int = 30) -> int:
        """Clean up projects older than specified days"""
        try:
            from datetime import timedelta
            
            cutoff_date = (datetime.now() - timedelta(days=days_old)).isoformat()
            
            # Get old projects
            result = self.supabase.table('video_projects').select('id').lt('created_at', cutoff_date).execute()
            
            cleaned_count = 0
            if result.data:
                for project in result.data:
                    project_id = project['id']
                    
                    # Delete files
                    if self.delete_project_files(project_id):
                        # Delete database records
                        self.supabase.table('stoic_content').delete().eq('project_id', project_id).execute()
                        self.supabase.table('video_projects').delete().eq('id', project_id).execute()
                        cleaned_count += 1
            
            print(f"✅ Cleaned up {cleaned_count} old projects")
            return cleaned_count
            
        except Exception as e:
            print(f"❌ Cleanup failed: {e}")
            return 0

# Database schema initialization
def initialize_supabase_schema():
    """SQL commands to initialize Supabase schema"""
    return """
    -- Video Projects Table
    CREATE TABLE IF NOT EXISTS video_projects (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        type VARCHAR(20) NOT NULL CHECK (type IN ('motivation', 'lofi')),
        status VARCHAR(20) NOT NULL DEFAULT 'initializing',
        progress INTEGER DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
        metadata JSONB DEFAULT '{}',
        video_url TEXT,
        voiceover_url TEXT,
        file_sizes JSONB DEFAULT '{}',
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        completed_at TIMESTAMP WITH TIME ZONE,
        error_message TEXT
    );

    -- Stoic Content Table
    CREATE TABLE IF NOT EXISTS stoic_content (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        project_id UUID REFERENCES video_projects(id) ON DELETE CASCADE,
        theme VARCHAR(200) NOT NULL,
        quote TEXT NOT NULL,
        narrative TEXT NOT NULL,
        voiceover_script TEXT NOT NULL,
        keywords TEXT[] DEFAULT '{}',
        emotional_tone VARCHAR(50) DEFAULT 'powerful',
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );

    -- Media Assets Table
    CREATE TABLE IF NOT EXISTS media_assets (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        project_id UUID REFERENCES video_projects(id) ON DELETE CASCADE,
        type VARCHAR(20) NOT NULL CHECK (type IN ('video', 'audio', 'voiceover')),
        source VARCHAR(50) NOT NULL,
        original_url TEXT,
        local_url TEXT,
        metadata JSONB DEFAULT '{}',
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );

    -- Indexes for performance
    CREATE INDEX IF NOT EXISTS idx_video_projects_type ON video_projects(type);
    CREATE INDEX IF NOT EXISTS idx_video_projects_status ON video_projects(status);
    CREATE INDEX IF NOT EXISTS idx_video_projects_created_at ON video_projects(created_at);
    CREATE INDEX IF NOT EXISTS idx_stoic_content_project_id ON stoic_content(project_id);
    CREATE INDEX IF NOT EXISTS idx_media_assets_project_id ON media_assets(project_id);

    -- Row Level Security (RLS) - Enable if needed
    -- ALTER TABLE video_projects ENABLE ROW LEVEL SECURITY;
    -- ALTER TABLE stoic_content ENABLE ROW LEVEL SECURITY;
    -- ALTER TABLE media_assets ENABLE ROW LEVEL SECURITY;

    -- Storage buckets (run these in Supabase dashboard)
    -- INSERT INTO storage.buckets (id, name, public) VALUES ('generated-videos', 'generated-videos', true);
    -- INSERT INTO storage.buckets (id, name, public) VALUES ('generated-audio', 'generated-audio', true);
    """

# Test function
def test_supabase_storage():
    """Test Supabase storage service"""
    print("🗄️  Testing Supabase Storage...")
    
    try:
        # Mock credentials for testing
        storage = SupabaseStorageService("https://example.supabase.co", "mock-key")
        print("✅ Supabase storage service initialized")
        
        # Print schema
        schema = initialize_supabase_schema()
        print(f"📋 Database schema ready ({len(schema)} characters)")
        
    except Exception as e:
        print(f"❌ Supabase test failed: {e}")

if __name__ == "__main__":
    test_supabase_storage()