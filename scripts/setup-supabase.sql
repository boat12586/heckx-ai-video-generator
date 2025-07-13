-- Supabase Database Setup for Heckx AI Video Generator
-- Run this script in your Supabase SQL Editor

-- ================================================================
-- STORAGE BUCKETS SETUP
-- ================================================================

-- Create storage buckets for generated content
INSERT INTO storage.buckets (id, name, public, avif_autodetection, allowed_mime_types)
VALUES 
  ('generated-videos', 'generated-videos', true, true, ARRAY['video/mp4', 'video/webm', 'video/avi']),
  ('generated-audio', 'generated-audio', true, false, ARRAY['audio/mpeg', 'audio/wav', 'audio/mp3']),
  ('thumbnails', 'thumbnails', true, true, ARRAY['image/jpeg', 'image/png', 'image/webp']),
  ('temp-uploads', 'temp-uploads', false, false, ARRAY['video/*', 'audio/*', 'image/*'])
ON CONFLICT (id) DO NOTHING;

-- ================================================================
-- STORAGE POLICIES
-- ================================================================

-- Policy for public read access to generated videos
CREATE POLICY "Public read access for generated videos" ON storage.objects
  FOR SELECT USING (bucket_id = 'generated-videos');

-- Policy for public read access to generated audio
CREATE POLICY "Public read access for generated audio" ON storage.objects
  FOR SELECT USING (bucket_id = 'generated-audio');

-- Policy for public read access to thumbnails
CREATE POLICY "Public read access for thumbnails" ON storage.objects
  FOR SELECT USING (bucket_id = 'thumbnails');

-- Policy for authenticated uploads to temp bucket
CREATE POLICY "Authenticated uploads to temp bucket" ON storage.objects
  FOR INSERT WITH CHECK (bucket_id = 'temp-uploads' AND auth.role() = 'authenticated');

-- Policy for service role full access (for backend operations)
CREATE POLICY "Service role full access" ON storage.objects
  FOR ALL USING (auth.role() = 'service_role');

-- ================================================================
-- APPLICATION TABLES
-- ================================================================

-- Video projects table
CREATE TABLE IF NOT EXISTS video_projects (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  project_id VARCHAR(255) UNIQUE NOT NULL,
  type VARCHAR(50) NOT NULL, -- 'motivation', 'lofi'
  status VARCHAR(50) NOT NULL DEFAULT 'initializing',
  progress INTEGER DEFAULT 0,
  metadata JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  completed_at TIMESTAMP WITH TIME ZONE,
  error_message TEXT
);

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_video_projects_project_id ON video_projects(project_id);
CREATE INDEX IF NOT EXISTS idx_video_projects_status ON video_projects(status);
CREATE INDEX IF NOT EXISTS idx_video_projects_type ON video_projects(type);
CREATE INDEX IF NOT EXISTS idx_video_projects_created_at ON video_projects(created_at);

-- Video footage table for tracking used media
CREATE TABLE IF NOT EXISTS video_footage (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  pixabay_id BIGINT,
  title VARCHAR(500),
  tags TEXT,
  category VARCHAR(100),
  duration INTEGER,
  video_url TEXT,
  preview_url TEXT,
  thumbnail_url TEXT,
  width INTEGER,
  height INTEGER,
  file_size BIGINT,
  used_count INTEGER DEFAULT 0,
  last_used_at TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for video footage
CREATE INDEX IF NOT EXISTS idx_video_footage_pixabay_id ON video_footage(pixabay_id);
CREATE INDEX IF NOT EXISTS idx_video_footage_category ON video_footage(category);
CREATE INDEX IF NOT EXISTS idx_video_footage_tags ON video_footage USING gin(to_tsvector('english', tags));

-- Audio tracks table for background music
CREATE TABLE IF NOT EXISTS audio_tracks (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  category VARCHAR(100),
  duration INTEGER,
  file_path TEXT,
  file_size BIGINT,
  format VARCHAR(20),
  used_count INTEGER DEFAULT 0,
  last_used_at TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for audio tracks
CREATE INDEX IF NOT EXISTS idx_audio_tracks_category ON audio_tracks(category);
CREATE INDEX IF NOT EXISTS idx_audio_tracks_name ON audio_tracks(name);

-- Analytics events table
CREATE TABLE IF NOT EXISTS analytics_events (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  event_type VARCHAR(100) NOT NULL,
  event_data JSONB,
  user_agent TEXT,
  ip_address INET,
  timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for analytics
CREATE INDEX IF NOT EXISTS idx_analytics_events_type ON analytics_events(event_type);
CREATE INDEX IF NOT EXISTS idx_analytics_events_timestamp ON analytics_events(timestamp);

-- Performance logs table
CREATE TABLE IF NOT EXISTS performance_logs (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  operation VARCHAR(100) NOT NULL,
  duration_ms INTEGER,
  memory_usage_mb REAL,
  cpu_usage_percent REAL,
  project_id VARCHAR(255),
  metadata JSONB,
  timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance logs
CREATE INDEX IF NOT EXISTS idx_performance_logs_operation ON performance_logs(operation);
CREATE INDEX IF NOT EXISTS idx_performance_logs_timestamp ON performance_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_performance_logs_project_id ON performance_logs(project_id);

-- ================================================================
-- FUNCTIONS AND TRIGGERS
-- ================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for video_projects table
CREATE TRIGGER update_video_projects_updated_at
    BEFORE UPDATE ON video_projects
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Function to cleanup old temp files
CREATE OR REPLACE FUNCTION cleanup_old_temp_files()
RETURNS void AS $$
BEGIN
  -- Delete temp files older than 24 hours
  DELETE FROM storage.objects 
  WHERE bucket_id = 'temp-uploads' 
  AND created_at < NOW() - INTERVAL '24 hours';
END;
$$ LANGUAGE plpgsql;

-- ================================================================
-- VIEWS FOR ANALYTICS
-- ================================================================

-- View for project statistics
CREATE OR REPLACE VIEW project_statistics AS
SELECT 
  type,
  status,
  COUNT(*) as count,
  AVG(progress) as avg_progress,
  MIN(created_at) as first_created,
  MAX(created_at) as last_created
FROM video_projects
GROUP BY type, status;

-- View for daily project counts
CREATE OR REPLACE VIEW daily_project_counts AS
SELECT 
  DATE(created_at) as date,
  type,
  COUNT(*) as projects_created,
  COUNT(CASE WHEN status = 'completed' THEN 1 END) as projects_completed
FROM video_projects
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE(created_at), type
ORDER BY date DESC;

-- View for performance metrics
CREATE OR REPLACE VIEW performance_summary AS
SELECT 
  operation,
  COUNT(*) as execution_count,
  AVG(duration_ms) as avg_duration_ms,
  MIN(duration_ms) as min_duration_ms,
  MAX(duration_ms) as max_duration_ms,
  PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY duration_ms) as p95_duration_ms,
  AVG(memory_usage_mb) as avg_memory_mb,
  AVG(cpu_usage_percent) as avg_cpu_percent
FROM performance_logs
WHERE timestamp >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY operation;

-- ================================================================
-- ROW LEVEL SECURITY (RLS)
-- ================================================================

-- Enable RLS on tables
ALTER TABLE video_projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE analytics_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE performance_logs ENABLE ROW LEVEL SECURITY;

-- Policies for video_projects
CREATE POLICY "Allow public read access to video projects" ON video_projects
  FOR SELECT USING (true);

CREATE POLICY "Allow service role full access to video projects" ON video_projects
  FOR ALL USING (auth.role() = 'service_role');

-- Policies for analytics_events
CREATE POLICY "Allow service role full access to analytics" ON analytics_events
  FOR ALL USING (auth.role() = 'service_role');

-- Policies for performance_logs
CREATE POLICY "Allow service role full access to performance logs" ON performance_logs
  FOR ALL USING (auth.role() = 'service_role');

-- ================================================================
-- INITIAL DATA
-- ================================================================

-- Insert some default audio tracks
INSERT INTO audio_tracks (name, category, duration, file_path, format) VALUES
  ('Peaceful Rain', 'เงียบสงบ', 180, 'audio/peaceful_rain.mp3', 'mp3'),
  ('Gentle Piano', 'เปียโน', 200, 'audio/gentle_piano.mp3', 'mp3'),
  ('Smooth Jazz', 'แจ๊สสมูท', 220, 'audio/smooth_jazz.mp3', 'mp3'),
  ('Acoustic Guitar', 'กีต้าร์โปร่ง', 190, 'audio/acoustic_guitar.mp3', 'mp3'),
  ('Ambient Sounds', 'อะคูสติก', 240, 'audio/ambient_sounds.mp3', 'mp3')
ON CONFLICT DO NOTHING;

-- ================================================================
-- CLEANUP AND MAINTENANCE
-- ================================================================

-- Function to archive old projects (older than 30 days)
CREATE OR REPLACE FUNCTION archive_old_projects()
RETURNS INTEGER AS $$
DECLARE
  archived_count INTEGER;
BEGIN
  -- Move old completed projects to an archive table (if needed)
  -- For now, just count how many would be archived
  SELECT COUNT(*) INTO archived_count
  FROM video_projects
  WHERE status = 'completed' 
  AND completed_at < NOW() - INTERVAL '30 days';
  
  -- Could implement actual archiving logic here
  RETURN archived_count;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions
GRANT USAGE ON SCHEMA public TO postgres, anon, authenticated, service_role;
GRANT ALL ON ALL TABLES IN SCHEMA public TO postgres, service_role;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO anon, authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO postgres, service_role;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO anon, authenticated;

-- Grant storage permissions
GRANT ALL ON storage.objects TO service_role;
GRANT SELECT ON storage.objects TO anon, authenticated;

COMMIT;