#!/usr/bin/env python3
"""
Supabase Setup and Integration Script for Heckx AI Video Generator
Automatically configures Supabase storage buckets, database tables, and policies
"""

import os
import sys
import json
import time
from typing import Dict, List, Optional
from supabase import create_client, Client
from dotenv import load_dotenv

class SupabaseSetup:
    def __init__(self, url: str = None, service_role_key: str = None):
        """Initialize Supabase setup with credentials"""
        load_dotenv()
        
        self.url = url or os.getenv('SUPABASE_URL')
        self.service_role_key = service_role_key or os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        
        if not self.url or not self.service_role_key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be provided")
        
        self.client: Client = create_client(self.url, self.service_role_key)
        self.setup_results = []
    
    def log_result(self, step: str, success: bool, message: str = ""):
        """Log setup step result"""
        result = {
            "step": step,
            "success": success,
            "message": message,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self.setup_results.append(result)
        
        status = "✅" if success else "❌"
        print(f"{status} {step}: {'SUCCESS' if success else 'FAILED'}")
        if message:
            print(f"   {message}")
    
    def create_storage_buckets(self) -> bool:
        """Create required storage buckets"""
        print("\n📁 Creating Supabase Storage Buckets...")
        
        buckets = [
            {
                "id": "generated-videos",
                "name": "generated-videos",
                "public": True,
                "allowed_mime_types": ["video/mp4", "video/webm", "video/avi"]
            },
            {
                "id": "generated-audio",
                "name": "generated-audio", 
                "public": True,
                "allowed_mime_types": ["audio/mpeg", "audio/wav", "audio/mp3"]
            },
            {
                "id": "thumbnails",
                "name": "thumbnails",
                "public": True,
                "allowed_mime_types": ["image/jpeg", "image/png", "image/webp"]
            },
            {
                "id": "temp-uploads",
                "name": "temp-uploads",
                "public": False,
                "allowed_mime_types": ["video/*", "audio/*", "image/*"]
            }
        ]
        
        success_count = 0
        for bucket in buckets:
            try:
                response = self.client.storage.create_bucket(
                    bucket["id"],
                    options={
                        "public": bucket["public"],
                        "allowed_mime_types": bucket["allowed_mime_types"]
                    }
                )
                self.log_result(f"Create bucket '{bucket['id']}'", True, f"Bucket created successfully")
                success_count += 1
                
            except Exception as e:
                error_msg = str(e)
                if "already exists" in error_msg.lower():
                    self.log_result(f"Create bucket '{bucket['id']}'", True, "Bucket already exists")
                    success_count += 1
                else:
                    self.log_result(f"Create bucket '{bucket['id']}'", False, f"Error: {error_msg}")
        
        return success_count == len(buckets)
    
    def setup_storage_policies(self) -> bool:
        """Setup storage bucket policies"""
        print("\n🔒 Setting up Storage Policies...")
        
        policies = [
            {
                "bucket": "generated-videos",
                "policy": "Public read access for generated videos",
                "sql": """
                CREATE POLICY "Public read access for generated videos" ON storage.objects
                FOR SELECT USING (bucket_id = 'generated-videos');
                """
            },
            {
                "bucket": "generated-audio",
                "policy": "Public read access for generated audio",
                "sql": """
                CREATE POLICY "Public read access for generated audio" ON storage.objects
                FOR SELECT USING (bucket_id = 'generated-audio');
                """
            },
            {
                "bucket": "thumbnails", 
                "policy": "Public read access for thumbnails",
                "sql": """
                CREATE POLICY "Public read access for thumbnails" ON storage.objects
                FOR SELECT USING (bucket_id = 'thumbnails');
                """
            },
            {
                "bucket": "temp-uploads",
                "policy": "Authenticated uploads to temp bucket",
                "sql": """
                CREATE POLICY "Authenticated uploads to temp bucket" ON storage.objects
                FOR INSERT WITH CHECK (bucket_id = 'temp-uploads' AND auth.role() = 'authenticated');
                """
            }
        ]
        
        success_count = 0
        for policy in policies:
            try:
                # Execute policy creation SQL
                response = self.client.rpc('exec_sql', {'sql': policy['sql']})
                self.log_result(f"Create policy '{policy['policy']}'", True)
                success_count += 1
                
            except Exception as e:
                error_msg = str(e)
                if "already exists" in error_msg.lower():
                    self.log_result(f"Create policy '{policy['policy']}'", True, "Policy already exists")
                    success_count += 1
                else:
                    self.log_result(f"Create policy '{policy['policy']}'", False, f"Error: {error_msg}")
        
        return success_count == len(policies)
    
    def create_database_tables(self) -> bool:
        """Create required database tables"""
        print("\n🗄️  Creating Database Tables...")
        
        # Read SQL script
        sql_file_path = os.path.join(os.path.dirname(__file__), 'setup-supabase.sql')
        
        try:
            with open(sql_file_path, 'r', encoding='utf-8') as f:
                sql_script = f.read()
            
            # Execute the SQL script
            response = self.client.rpc('exec_sql', {'sql': sql_script})
            self.log_result("Execute database setup script", True, "All tables and functions created")
            return True
            
        except FileNotFoundError:
            self.log_result("Execute database setup script", False, f"SQL file not found: {sql_file_path}")
            return False
        except Exception as e:
            self.log_result("Execute database setup script", False, f"Error: {str(e)}")
            return False
    
    def test_database_connection(self) -> bool:
        """Test database connection and basic operations"""
        print("\n🔍 Testing Database Connection...")
        
        try:
            # Test basic query
            response = self.client.table('video_projects').select('*').limit(1).execute()
            self.log_result("Database connection test", True, "Can query video_projects table")
            
            # Test storage access
            buckets = self.client.storage.list_buckets()
            bucket_names = [bucket.name for bucket in buckets]
            
            required_buckets = ['generated-videos', 'generated-audio', 'thumbnails', 'temp-uploads']
            missing_buckets = [b for b in required_buckets if b not in bucket_names]
            
            if not missing_buckets:
                self.log_result("Storage buckets test", True, f"All {len(required_buckets)} buckets accessible")
            else:
                self.log_result("Storage buckets test", False, f"Missing buckets: {missing_buckets}")
            
            return len(missing_buckets) == 0
            
        except Exception as e:
            self.log_result("Database connection test", False, f"Error: {str(e)}")
            return False
    
    def create_sample_data(self) -> bool:
        """Create sample data for testing"""
        print("\n📊 Creating Sample Data...")
        
        try:
            # Create a sample video project
            sample_project = {
                "project_id": "sample_project_001",
                "type": "motivation",
                "status": "completed",
                "progress": 100,
                "metadata": {
                    "theme": "inner_strength",
                    "duration": 60,
                    "video_url": "https://example.com/sample.mp4",
                    "created_for": "testing"
                }
            }
            
            response = self.client.table('video_projects').insert(sample_project).execute()
            self.log_result("Create sample project", True, "Sample video project created")
            
            # Create sample analytics event
            sample_event = {
                "event_type": "video_generation_completed",
                "event_data": {
                    "project_id": "sample_project_001",
                    "duration_seconds": 45,
                    "theme": "inner_strength"
                }
            }
            
            response = self.client.table('analytics_events').insert(sample_event).execute()
            self.log_result("Create sample analytics event", True, "Sample analytics event created")
            
            return True
            
        except Exception as e:
            self.log_result("Create sample data", False, f"Error: {str(e)}")
            return False
    
    def setup_environment_validation(self) -> bool:
        """Validate environment configuration"""
        print("\n⚙️  Validating Environment Configuration...")
        
        required_env_vars = [
            'SUPABASE_URL',
            'SUPABASE_ANON_KEY', 
            'SUPABASE_SERVICE_ROLE_KEY'
        ]
        
        missing_vars = []
        for var in required_env_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            self.log_result("Environment validation", False, f"Missing variables: {missing_vars}")
            return False
        else:
            self.log_result("Environment validation", True, "All required environment variables present")
            return True
    
    def generate_config_file(self) -> bool:
        """Generate Supabase configuration file"""
        print("\n📝 Generating Configuration File...")
        
        try:
            config = {
                "supabase": {
                    "url": self.url,
                    "anon_key": os.getenv('SUPABASE_ANON_KEY'),
                    "buckets": {
                        "videos": "generated-videos",
                        "audio": "generated-audio", 
                        "thumbnails": "thumbnails",
                        "temp": "temp-uploads"
                    },
                    "tables": {
                        "projects": "video_projects",
                        "footage": "video_footage",
                        "audio_tracks": "audio_tracks",
                        "analytics": "analytics_events",
                        "performance": "performance_logs"
                    }
                },
                "setup_completed": True,
                "setup_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "setup_results": self.setup_results
            }
            
            config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'supabase.json')
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            self.log_result("Generate config file", True, f"Configuration saved to {config_path}")
            return True
            
        except Exception as e:
            self.log_result("Generate config file", False, f"Error: {str(e)}")
            return False
    
    def run_full_setup(self) -> Dict:
        """Run complete Supabase setup process"""
        print("🚀 Starting Supabase Setup for Heckx AI Video Generator")
        print("=" * 60)
        
        # Run all setup steps
        steps = [
            ("Environment Validation", self.setup_environment_validation),
            ("Storage Buckets", self.create_storage_buckets),
            ("Storage Policies", self.setup_storage_policies),
            ("Database Tables", self.create_database_tables),
            ("Connection Test", self.test_database_connection),
            ("Sample Data", self.create_sample_data),
            ("Config File", self.generate_config_file)
        ]
        
        success_count = 0
        total_steps = len(steps)
        
        for step_name, step_function in steps:
            try:
                if step_function():
                    success_count += 1
            except Exception as e:
                self.log_result(f"Step '{step_name}'", False, f"Unexpected error: {str(e)}")
        
        # Generate summary
        print("\n" + "=" * 60)
        print("📊 SUPABASE SETUP SUMMARY")
        print("=" * 60)
        
        success_rate = (success_count / total_steps) * 100
        print(f"Total Steps: {total_steps}")
        print(f"Successful: {success_count} ✅")
        print(f"Failed: {total_steps - success_count} ❌")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print("\n🎉 Supabase setup completed successfully!")
            print("Your Heckx AI Video Generator is ready for production deployment.")
        else:
            print("\n⚠️  Supabase setup completed with issues.")
            print("Please review the failed steps and retry setup.")
        
        return {
            "success": success_rate >= 80,
            "total_steps": total_steps,
            "successful_steps": success_count,
            "failed_steps": total_steps - success_count,
            "success_rate": success_rate,
            "results": self.setup_results
        }

def main():
    """Main setup function"""
    print("Heckx AI Video Generator - Supabase Setup Tool")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    # Check for required environment variables
    url = os.getenv('SUPABASE_URL')
    service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not url or not service_key:
        print("❌ Missing required environment variables:")
        print("   - SUPABASE_URL")
        print("   - SUPABASE_SERVICE_ROLE_KEY")
        print("\nPlease set these in your .env file and try again.")
        sys.exit(1)
    
    try:
        # Run setup
        setup = SupabaseSetup(url, service_key)
        result = setup.run_full_setup()
        
        # Exit with appropriate code
        sys.exit(0 if result["success"] else 1)
        
    except Exception as e:
        print(f"\n❌ Setup failed with error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()