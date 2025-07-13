# video_generator/models.py - Data models for video generation system
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
import uuid

class VideoType(Enum):
    MOTIVATION = "motivation"
    LOFI = "lofi"

class ProjectStatus(Enum):
    INITIALIZING = "initializing"
    ACQUIRING_MEDIA = "acquiring_media"
    GENERATING_CONTENT = "generating_content"
    PROCESSING_AUDIO = "processing_audio"
    COMPOSING_VIDEO = "composing_video"
    UPLOADING = "uploading"
    COMPLETED = "completed"
    FAILED = "failed"

class AudioSourceType(Enum):
    PIXABAY_BGM = "pixabay_bgm"
    MUSIC_LIBRARY = "music_library"
    GENERATED_VOICEOVER = "generated_voiceover"

@dataclass
class VideoProject:
    id: str
    type: VideoType
    status: ProjectStatus
    progress: int = 0
    created_at: datetime = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.id is None:
            self.id = str(uuid.uuid4())
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.metadata is None:
            self.metadata = {}

@dataclass
class StoicContent:
    theme: str
    quote: str
    narrative: str
    voiceover_script: str
    keywords: List[str]
    emotional_tone: str = "powerful"

@dataclass
class VideoFootage:
    id: str
    source: str
    url: str
    preview_url: str
    tags: List[str]
    duration: int
    width: int
    height: int
    size: int
    category: str
    local_path: Optional[str] = None

@dataclass
class AudioTrack:
    id: str
    title: str
    source: AudioSourceType
    url: str
    preview_url: str
    duration: int
    size: int
    category: str
    volume_level: float
    local_path: Optional[str] = None
    metadata: Dict[str, Any] = None

@dataclass
class VoiceoverAudio:
    script: str
    voice_style: str
    audio_data: bytes
    duration: float
    file_path: str
    metadata: Dict[str, Any] = None

@dataclass
class MediaCollection:
    video: VideoFootage
    audio: AudioTrack
    voiceover: Optional[VoiceoverAudio] = None

@dataclass
class ProcessedVideo:
    project_id: str
    video_path: str
    voiceover_path: Optional[str]
    duration: float
    file_size: int
    resolution: str
    format: str = "mp4"

@dataclass
class StorageResult:
    project_id: str
    video_url: str
    voiceover_url: Optional[str]
    storage_size: int
    uploaded_at: datetime