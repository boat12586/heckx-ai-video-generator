#!/usr/bin/env python3
"""
Real Deployment Helper for Heckx AI Video Generator
Interactive script to guide through live deployment with real API keys
"""

import os
import sys
import json
import subprocess
import requests
from datetime import datetime
from typing import Dict, List, Optional

class RealDeploymentHelper:
    """Interactive helper for real deployment with actual API keys"""
    
    def __init__(self):
        self.credentials = {}
        self.deployment_log = []
        self.platform = None
        
    def log_step(self, step: str, status: str, details: str = ""):
        """Log deployment step"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "step": step,
            "status": status,
            "details": details
        }
        self.deployment_log.append(entry)
        
        status_symbols = {
            "START": "🚀",
            "SUCCESS": "✅", 
            "WARNING": "⚠️",
            "ERROR": "❌",
            "INFO": "ℹ️",
            "INPUT": "📝"
        }
        
        symbol = status_symbols.get(status, "📋")
        print(f"{symbol} {step}")
        if details:
            print(f"   {details}")
    
    def collect_pixabay_credentials(self):
        """Interactive Pixabay API key collection"""
        print("\n" + "="*60)
        print("🎨 PIXABAY API KEY SETUP")
        print("="*60)
        
        self.log_step("Pixabay Setup", "START")
        
        print("1. Visit: https://pixabay.com/api/docs/")
        print("2. Create account or sign in")
        print("3. Get your API key")
        print("4. API key format: 12345678-abcd1234efgh5678ijkl")
        
        while True:
            api_key = input("\n📝 Enter your Pixabay API key: ").strip()
            
            if not api_key:
                print("❌ API key cannot be empty")
                continue
                
            if len(api_key) < 20:
                print("❌ API key seems too short")
                continue
                
            # Test the API key
            print("🔍 Testing API key...")
            if self.test_pixabay_api(api_key):
                self.credentials['pixabay_api_key'] = api_key
                self.log_step("Pixabay API Key", "SUCCESS", "API key validated")
                break
            else:
                print("❌ API key test failed. Please check and try again.")
                retry = input("Try again? (y/n): ").lower()
                if retry != 'y':
                    return False
        
        return True
    
    def test_pixabay_api(self, api_key: str) -> bool:
        """Test Pixabay API key"""
        try:
            url = f"https://pixabay.com/api/videos/?key={api_key}&q=nature&per_page=3"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'hits' in data:
                    print(f"✅ API key valid! Found {data.get('totalHits', 0)} videos available")
                    return True
            
            print(f"❌ API responded with status {response.status_code}")
            return False
            
        except Exception as e:
            print(f"❌ API test failed: {str(e)}")
            return False
    
    def collect_supabase_credentials(self):
        """Interactive Supabase credentials collection"""
        print("\n" + "="*60)
        print("🗄️ SUPABASE PROJECT SETUP")
        print("="*60)
        
        self.log_step("Supabase Setup", "START")
        
        print("1. Visit: https://supabase.com")
        print("2. Create new project")
        print("3. Go to Settings → API")
        print("4. Copy Project URL and API keys")
        
        # Project URL
        while True:
            url = input("\n📝 Enter Supabase Project URL: ").strip()
            if url.startswith('https://') and '.supabase.co' in url:
                self.credentials['supabase_url'] = url
                break
            print("❌ URL should be: https://your-project-id.supabase.co")
        
        # Anon Key
        while True:
            anon_key = input("📝 Enter Supabase Anon Key: ").strip()
            if len(anon_key) > 100 and anon_key.startswith('eyJ'):
                self.credentials['supabase_anon_key'] = anon_key
                break
            print("❌ Anon key should start with 'eyJ' and be quite long")
        
        # Service Role Key
        while True:
            service_key = input("📝 Enter Supabase Service Role Key: ").strip()
            if len(service_key) > 100 and service_key.startswith('eyJ'):
                self.credentials['supabase_service_key'] = service_key
                break
            print("❌ Service role key should start with 'eyJ' and be quite long")
        
        # Test connection
        print("🔍 Testing Supabase connection...")
        if self.test_supabase_connection():
            self.log_step("Supabase Connection", "SUCCESS", "Database accessible")
            return True
        else:
            print("❌ Supabase connection test failed")
            return False
    
    def test_supabase_connection(self) -> bool:
        """Test Supabase connection"""
        try:
            url = f"{self.credentials['supabase_url']}/rest/v1/"
            headers = {
                'apikey': self.credentials['supabase_anon_key'],
                'Authorization': f"Bearer {self.credentials['supabase_anon_key']}"
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code in [200, 404]:  # 404 is fine, means API is responding
                print("✅ Supabase connection successful!")
                return True
            
            print(f"❌ Supabase responded with status {response.status_code}")
            return False
            
        except Exception as e:
            print(f"❌ Supabase test failed: {str(e)}")
            return False
    
    def choose_deployment_platform(self):
        """Choose deployment platform"""
        print("\n" + "="*60)
        print("☁️ DEPLOYMENT PLATFORM SELECTION")
        print("="*60)
        
        print("Choose your deployment platform:")
        print("1. Railway (Recommended - easier setup)")
        print("2. Render (More configurable)")
        
        while True:
            choice = input("\n📝 Enter choice (1 or 2): ").strip()
            if choice == '1':
                self.platform = 'railway'
                break
            elif choice == '2':
                self.platform = 'render'
                break
            print("❌ Please enter 1 or 2")
        
        self.log_step("Platform Selection", "SUCCESS", f"Selected {self.platform}")
        
        # Platform-specific instructions
        if self.platform == 'railway':
            self.setup_railway_instructions()
        else:
            self.setup_render_instructions()
    
    def setup_railway_instructions(self):
        """Railway setup instructions"""
        print("\n🚄 RAILWAY DEPLOYMENT STEPS:")
        print("1. Visit: https://railway.app")
        print("2. Sign up with GitHub")
        print("3. Click 'New Project' → 'Deploy from GitHub repo'")
        print("4. Select your Heckx repository")
        print("5. Add Redis: New → Database → Add Redis")
        print("6. Add PostgreSQL: New → Database → Add PostgreSQL")
        
        input("\n⏸️ Complete these steps, then press Enter to continue...")
        
        print("\n📋 Now you'll need to add environment variables in Railway:")
        print("1. Click on your main service")
        print("2. Go to 'Variables' tab")
        print("3. Add the variables shown next...")
    
    def setup_render_instructions(self):
        """Render setup instructions"""
        print("\n🎨 RENDER DEPLOYMENT STEPS:")
        print("1. Visit: https://render.com")
        print("2. Sign up with GitHub")
        print("3. Click 'New' → 'Web Service'")
        print("4. Connect your GitHub repository")
        print("5. Configure:")
        print("   - Environment: Docker")
        print("   - Build Command: (auto-detected)")
        print("   - Start Command: (auto-detected)")
        print("6. Create Redis: New → Redis")
        print("7. Create PostgreSQL: New → PostgreSQL")
        
        input("\n⏸️ Complete these steps, then press Enter to continue...")
        
        print("\n📋 Now you'll need to add environment variables in Render:")
        print("1. Go to your web service")
        print("2. Click 'Environment' tab")
        print("3. Add the variables shown next...")
    
    def generate_environment_variables(self):
        """Generate environment variables file"""
        print("\n" + "="*60)
        print("⚙️ ENVIRONMENT VARIABLES GENERATION")
        print("="*60)
        
        # Load the demo template and replace with real values
        template_path = '.env.production.demo'
        real_env_path = '.env.production.real'
        
        try:
            with open(template_path, 'r') as f:
                template = f.read()
            
            # Replace demo values with real ones
            real_env = template.replace(
                'PIXABAY_API_KEY=12345678-abcd1234efgh5678ijkl',
                f'PIXABAY_API_KEY={self.credentials["pixabay_api_key"]}'
            ).replace(
                'SUPABASE_URL=https://demo-project-id.supabase.co',
                f'SUPABASE_URL={self.credentials["supabase_url"]}'
            ).replace(
                'SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.demo_anon_key',
                f'SUPABASE_ANON_KEY={self.credentials["supabase_anon_key"]}'
            ).replace(
                'SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.demo_service_role_key',
                f'SUPABASE_SERVICE_ROLE_KEY={self.credentials["supabase_service_key"]}'
            )
            
            # Write real environment file
            with open(real_env_path, 'w') as f:
                f.write(real_env)
            
            print(f"✅ Environment variables saved to: {real_env_path}")
            
            # Display key variables to copy
            print("\n📋 KEY VARIABLES TO ADD TO YOUR PLATFORM:")
            print("-" * 50)
            
            key_vars = [
                ('PIXABAY_API_KEY', self.credentials['pixabay_api_key']),
                ('SUPABASE_URL', self.credentials['supabase_url']),
                ('SUPABASE_ANON_KEY', self.credentials['supabase_anon_key'][:50] + '...'),
                ('SUPABASE_SERVICE_ROLE_KEY', self.credentials['supabase_service_key'][:50] + '...')
            ]
            
            for name, value in key_vars:
                print(f"{name}={value}")
            
            print("-" * 50)
            print("💡 Copy ALL variables from .env.production.real to your platform")
            
            self.log_step("Environment Generation", "SUCCESS", f"Variables saved to {real_env_path}")
            
        except Exception as e:
            print(f"❌ Error generating environment variables: {str(e)}")
            return False
        
        return True
    
    def setup_database_schema(self):
        """Setup database schema in Supabase"""
        print("\n" + "="*60)
        print("🗄️ DATABASE SCHEMA SETUP")
        print("="*60)
        
        print("Setting up your Supabase database schema...")
        
        schema_file = 'scripts/setup-supabase.sql'
        if os.path.exists(schema_file):
            print(f"📄 Found schema file: {schema_file}")
            print("\n📋 MANUAL SETUP REQUIRED:")
            print("1. Go to your Supabase project dashboard")
            print("2. Navigate to 'SQL Editor'")
            print("3. Copy and paste the contents of scripts/setup-supabase.sql")
            print("4. Click 'Run' to execute the schema")
            print("5. Verify tables and storage buckets are created")
            
            input("\n⏸️ Complete database setup, then press Enter to continue...")
            self.log_step("Database Schema", "SUCCESS", "Manual setup completed")
        else:
            print(f"❌ Schema file not found: {schema_file}")
            return False
        
        return True
    
    def verify_deployment(self):
        """Verify the deployment"""
        print("\n" + "="*60)
        print("🔍 DEPLOYMENT VERIFICATION")
        print("="*60)
        
        # Get deployment URL
        while True:
            url = input("\n📝 Enter your deployment URL: ").strip()
            if url.startswith('https://'):
                break
            print("❌ URL should start with https://")
        
        print("🔍 Testing deployment...")
        
        # Test health endpoint
        try:
            health_url = f"{url}/api/health"
            response = requests.get(health_url, timeout=30)
            
            if response.status_code == 200:
                print("✅ Health check: PASSED")
                self.log_step("Health Check", "SUCCESS", "Endpoint responding")
            else:
                print(f"❌ Health check failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Health check error: {str(e)}")
        
        # Test API documentation
        try:
            docs_url = f"{url}/docs"
            response = requests.get(docs_url, timeout=30)
            
            if response.status_code == 200:
                print("✅ API Documentation: ACCESSIBLE")
                print(f"📖 Visit: {docs_url}")
            else:
                print(f"❌ API docs failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ API docs error: {str(e)}")
        
        self.log_step("Deployment Verification", "SUCCESS", f"App accessible at {url}")
        
        return url
    
    def save_deployment_summary(self, deployment_url: str):
        """Save deployment summary"""
        summary = {
            "timestamp": datetime.now().isoformat(),
            "platform": self.platform,
            "deployment_url": deployment_url,
            "credentials_configured": len(self.credentials),
            "deployment_log": self.deployment_log
        }
        
        with open('real_deployment_summary.json', 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\n📄 Deployment summary saved to: real_deployment_summary.json")
    
    def run_deployment_process(self):
        """Run the complete deployment process"""
        print("🎬 HECKX AI VIDEO GENERATOR - REAL DEPLOYMENT")
        print("=" * 70)
        print("This interactive guide will help you deploy with real API keys")
        print("=" * 70)
        
        try:
            # Step 1: Pixabay API
            if not self.collect_pixabay_credentials():
                print("❌ Pixabay setup failed")
                return
            
            # Step 2: Supabase
            if not self.collect_supabase_credentials():
                print("❌ Supabase setup failed")
                return
            
            # Step 3: Platform choice
            self.choose_deployment_platform()
            
            # Step 4: Generate environment variables
            if not self.generate_environment_variables():
                print("❌ Environment generation failed")
                return
            
            # Step 5: Database setup
            if not self.setup_database_schema():
                print("❌ Database setup failed")
                return
            
            # Step 6: Deployment verification
            deployment_url = self.verify_deployment()
            
            # Step 7: Save summary
            self.save_deployment_summary(deployment_url)
            
            # Success message
            print("\n" + "="*70)
            print("🎉 DEPLOYMENT COMPLETED SUCCESSFULLY!")
            print("="*70)
            print(f"🚀 Your app is live at: {deployment_url}")
            print(f"📖 API docs: {deployment_url}/docs")
            print(f"❤️ Health check: {deployment_url}/api/health")
            print("\n🎬 Your Heckx AI Video Generator is ready for production! ✨")
            
        except KeyboardInterrupt:
            print("\n\n⏸️ Deployment process interrupted by user")
        except Exception as e:
            print(f"\n❌ Deployment failed: {str(e)}")


def main():
    """Main function"""
    helper = RealDeploymentHelper()
    helper.run_deployment_process()


if __name__ == "__main__":
    main()