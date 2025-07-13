#!/usr/bin/env python3
"""
Complete Deployment Execution Script for Heckx AI Video Generator
Automates the entire deployment process from setup to verification
"""

import os
import sys
import time
import json
import subprocess
import secrets
import string
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import requests


class DeploymentExecutor:
    """Execute complete deployment process"""
    
    def __init__(self):
        self.deployment_log = []
        self.config = {}
        self.start_time = datetime.now()
        
    def log_step(self, step: str, status: str, message: str = "", details: Dict = None):
        """Log deployment step"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "step": step,
            "status": status,
            "message": message,
            "details": details or {}
        }
        self.deployment_log.append(log_entry)
        
        status_symbols = {
            "START": "🚀",
            "SUCCESS": "✅",
            "WARNING": "⚠️",
            "ERROR": "❌",
            "INFO": "ℹ️"
        }
        
        symbol = status_symbols.get(status, "📋")
        print(f"{symbol} {step}: {message}")
        
        if details:
            for key, value in details.items():
                print(f"   {key}: {value}")
    
    def generate_secure_keys(self) -> Dict[str, str]:
        """Generate secure keys for production"""
        self.log_step("Key Generation", "START", "Generating secure keys...")
        
        def generate_secret_key(length: int = 32) -> str:
            alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
            return ''.join(secrets.choice(alphabet) for _ in range(length))
        
        keys = {
            "SECRET_KEY": generate_secret_key(32),
            "JWT_SECRET_KEY": generate_secret_key(32),
            "API_KEY": f"heckx_{secrets.token_urlsafe(32)}",
            "POSTGRES_PASSWORD": generate_secret_key(24),
            "REDIS_PASSWORD": generate_secret_key(24)
        }
        
        self.log_step("Key Generation", "SUCCESS", "Secure keys generated", {
            "keys_generated": len(keys),
            "api_key_preview": keys["API_KEY"][:20] + "..."
        })
        
        return keys
    
    def create_supabase_project_guide(self) -> Dict:
        """Provide Supabase project setup guide"""
        self.log_step("Supabase Setup", "START", "Preparing Supabase configuration...")
        
        supabase_config = {
            "instructions": [
                "1. Go to https://supabase.com/dashboard",
                "2. Click 'New Project'",
                "3. Choose organization",
                "4. Enter project details:",
                "   - Name: heckx-video-generator-prod",
                "   - Database Password: (generate secure password)",
                "   - Region: (choose closest to users)",
                "5. Wait for project creation (2-3 minutes)",
                "6. Get credentials from Settings > API:",
                "   - Project URL: https://your-project-id.supabase.co",
                "   - Anon Key: (public key)",
                "   - Service Role Key: (secret key)"
            ],
            "required_credentials": [
                "SUPABASE_URL",
                "SUPABASE_ANON_KEY", 
                "SUPABASE_SERVICE_ROLE_KEY"
            ],
            "database_setup_script": "scripts/setup-supabase.sql",
            "automated_setup_script": "scripts/supabase-setup.py"
        }
        
        self.log_step("Supabase Setup", "INFO", "Supabase setup guide prepared", {
            "project_name": "heckx-video-generator-prod",
            "setup_scripts": 2
        })
        
        return supabase_config
    
    def create_railway_deployment_config(self) -> Dict:
        """Create Railway deployment configuration"""
        self.log_step("Railway Config", "START", "Creating Railway deployment configuration...")
        
        railway_config = {
            "deployment_steps": [
                "1. Push code to GitHub repository",
                "2. Connect Railway to GitHub:",
                "   - Go to https://railway.app/dashboard",
                "   - Click 'New Project'",
                "   - Select 'Deploy from GitHub repo'",
                "   - Choose your repository",
                "3. Configure environment variables in Railway dashboard",
                "4. Add Redis service:",
                "   - Click 'New Service' > 'Database' > 'Redis'",
                "5. Add PostgreSQL service (optional):",
                "   - Click 'New Service' > 'Database' > 'PostgreSQL'",
                "6. Deploy automatically via railway.json configuration"
            ],
            "environment_variables": self.generate_production_env_vars(),
            "services_needed": ["Redis", "PostgreSQL (optional)"],
            "config_file": "railway.json"
        }
        
        self.log_step("Railway Config", "SUCCESS", "Railway configuration created", {
            "deployment_method": "GitHub integration",
            "services": len(railway_config["services_needed"]),
            "env_vars": len(railway_config["environment_variables"])
        })
        
        return railway_config
    
    def create_render_deployment_config(self) -> Dict:
        """Create Render deployment configuration"""
        self.log_step("Render Config", "START", "Creating Render deployment configuration...")
        
        render_config = {
            "deployment_steps": [
                "1. Connect Render to GitHub:",
                "   - Go to https://render.com/dashboard",
                "   - Click 'New' > 'Web Service'",
                "   - Connect your GitHub repository",
                "2. Configure service settings:",
                "   - Name: heckx-video-generator",
                "   - Environment: Docker",
                "   - Build Command: docker build --target production -t heckx .",
                "   - Start Command: python -m video_generator.main_service",
                "3. Set environment variables",
                "4. Add Redis service:",
                "   - Create new Redis service",
                "5. Deploy using render.yaml configuration"
            ],
            "environment_variables": self.generate_production_env_vars(),
            "services_needed": ["Redis", "PostgreSQL (optional)"],
            "config_file": "render.yaml"
        }
        
        self.log_step("Render Config", "SUCCESS", "Render configuration created", {
            "deployment_method": "Docker",
            "services": len(render_config["services_needed"]),
            "config_file": "render.yaml"
        })
        
        return render_config
    
    def generate_production_env_vars(self) -> Dict[str, str]:
        """Generate production environment variables"""
        secure_keys = self.generate_secure_keys()
        
        env_vars = {
            # Application Configuration
            "ENVIRONMENT": "production",
            "DEBUG": "false",
            "PORT": "5001",
            "HOST": "0.0.0.0",
            
            # Security Keys
            "SECRET_KEY": secure_keys["SECRET_KEY"],
            "JWT_SECRET_KEY": secure_keys["JWT_SECRET_KEY"],
            "API_KEY": secure_keys["API_KEY"],
            
            # External APIs (placeholder - user must provide)
            "PIXABAY_API_KEY": "your-pixabay-api-key-here",
            "OPENAI_API_KEY": "your-openai-api-key-here",
            
            # Supabase (placeholder - user must provide)
            "SUPABASE_URL": "https://your-project-id.supabase.co",
            "SUPABASE_ANON_KEY": "your-supabase-anon-key-here",
            "SUPABASE_SERVICE_ROLE_KEY": "your-supabase-service-role-key-here",
            
            # Database (will be provided by cloud platform)
            "DATABASE_URL": "postgresql://user:pass@host:port/db",
            "REDIS_URL": "redis://user:pass@host:port",
            
            # Features
            "ENABLE_API_AUTH": "true",
            "ENABLE_RATE_LIMITING": "true",
            "ENABLE_CORS": "true",
            "CORS_ORIGINS": "https://your-app.up.railway.app",
            
            # Performance
            "MAX_CONCURRENT_JOBS": "3",
            "WORKER_PROCESSES": "2",
            "REQUEST_TIMEOUT": "600",
            
            # Monitoring
            "LOG_LEVEL": "INFO",
            "PROMETHEUS_ENABLED": "true",
            
            # Storage
            "STORAGE_BACKEND": "supabase",
            "MAX_UPLOAD_SIZE": "200",
            "MAX_VIDEO_DURATION": "600"
        }
        
        return env_vars
    
    def create_deployment_checklist(self) -> Dict:
        """Create deployment checklist"""
        checklist = {
            "pre_deployment": [
                "☐ GitHub repository created and code pushed",
                "☐ Supabase project created and configured",
                "☐ Pixabay API key obtained",
                "☐ Cloud platform account (Railway/Render) created",
                "☐ Domain name configured (optional)",
                "☐ Slack webhook for notifications (optional)"
            ],
            "deployment_steps": [
                "☐ Connect cloud platform to GitHub repository",
                "☐ Configure environment variables",
                "☐ Add required services (Redis, PostgreSQL)",
                "☐ Deploy application",
                "☐ Verify health endpoint responding",
                "☐ Test API endpoints",
                "☐ Run deployment verification script"
            ],
            "post_deployment": [
                "☐ Set up monitoring and health checks",
                "☐ Configure custom domain (if applicable)",
                "☐ Set up backup procedures",
                "☐ Test video generation functionality",
                "☐ Configure auto-scaling (if available)",
                "☐ Document production URLs and credentials"
            ],
            "verification_commands": [
                "curl https://your-app-url.com/api/health",
                "python3 scripts/deploy-verify.py --url https://your-app-url.com",
                "python3 scripts/health-monitor.py --once --url https://your-app-url.com"
            ]
        }
        
        return checklist
    
    def setup_local_environment(self) -> bool:
        """Set up local development environment"""
        self.log_step("Local Setup", "START", "Setting up local environment...")
        
        try:
            # Create production environment file
            env_vars = self.generate_production_env_vars()
            env_content = "\n".join([f"{key}={value}" for key, value in env_vars.items()])
            
            with open(".env.production.template", "w") as f:
                f.write("# Production Environment Variables Template\n")
                f.write("# Copy this file to .env.production and fill in actual values\n\n")
                f.write(env_content)
            
            # Create deployment configuration
            deployment_config = {
                "timestamp": datetime.now().isoformat(),
                "deployment_mode": "production",
                "generated_keys": {
                    "api_key": env_vars["API_KEY"],
                    "secret_key_length": len(env_vars["SECRET_KEY"]),
                    "jwt_key_length": len(env_vars["JWT_SECRET_KEY"])
                },
                "next_steps": [
                    "1. Get Pixabay API key from https://pixabay.com/api/",
                    "2. Create Supabase project and get credentials", 
                    "3. Choose deployment platform (Railway or Render)",
                    "4. Configure environment variables in platform",
                    "5. Deploy and verify"
                ]
            }
            
            with open("deployment_config.json", "w") as f:
                json.dump(deployment_config, f, indent=2)
            
            self.log_step("Local Setup", "SUCCESS", "Local environment configured", {
                "env_template": ".env.production.template",
                "config_file": "deployment_config.json",
                "api_key": env_vars["API_KEY"][:20] + "..."
            })
            
            return True
            
        except Exception as e:
            self.log_step("Local Setup", "ERROR", f"Local setup failed: {str(e)}")
            return False
    
    def run_supabase_setup(self, supabase_url: str = None, service_key: str = None) -> bool:
        """Run Supabase setup if credentials provided"""
        if not supabase_url or not service_key:
            self.log_step("Supabase Setup", "WARNING", "Supabase credentials not provided, skipping automated setup")
            return False
        
        self.log_step("Supabase Setup", "START", "Running automated Supabase setup...")
        
        try:
            # Set environment variables for setup script
            os.environ["SUPABASE_URL"] = supabase_url
            os.environ["SUPABASE_SERVICE_ROLE_KEY"] = service_key
            
            # Run Supabase setup script
            result = subprocess.run([
                "python3", "scripts/supabase-setup.py"
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                self.log_step("Supabase Setup", "SUCCESS", "Supabase setup completed successfully")
                return True
            else:
                self.log_step("Supabase Setup", "ERROR", f"Supabase setup failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.log_step("Supabase Setup", "ERROR", f"Supabase setup error: {str(e)}")
            return False
    
    def verify_deployment(self, app_url: str) -> bool:
        """Verify deployment is working"""
        if not app_url:
            self.log_step("Deployment Verification", "WARNING", "App URL not provided, skipping verification")
            return False
        
        self.log_step("Deployment Verification", "START", f"Verifying deployment at {app_url}")
        
        try:
            # Run deployment verification script
            result = subprocess.run([
                "python3", "scripts/deploy-verify.py", 
                "--url", app_url,
                "--output", "verification_results.json"
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                self.log_step("Deployment Verification", "SUCCESS", "Deployment verification passed")
                
                # Load and display results
                if os.path.exists("verification_results.json"):
                    with open("verification_results.json", "r") as f:
                        results = json.load(f)
                    
                    summary = results.get("summary", {})
                    self.log_step("Verification Results", "INFO", "Detailed verification results", summary)
                
                return True
            else:
                self.log_step("Deployment Verification", "ERROR", f"Verification failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.log_step("Deployment Verification", "ERROR", f"Verification error: {str(e)}")
            return False
    
    def generate_deployment_report(self) -> Dict:
        """Generate comprehensive deployment report"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        report = {
            "deployment_summary": {
                "timestamp": end_time.isoformat(),
                "duration_seconds": duration,
                "total_steps": len(self.deployment_log),
                "successful_steps": len([log for log in self.deployment_log if log["status"] == "SUCCESS"]),
                "failed_steps": len([log for log in self.deployment_log if log["status"] == "ERROR"])
            },
            "generated_files": [
                ".env.production.template",
                "deployment_config.json",
                "verification_results.json"
            ],
            "deployment_log": self.deployment_log,
            "next_steps": [
                "1. Review .env.production.template and add actual API keys",
                "2. Follow platform-specific deployment guide",
                "3. Configure environment variables in cloud platform",
                "4. Deploy and monitor using provided scripts",
                "5. Set up monitoring and backup procedures"
            ],
            "important_files": {
                "deployment_guide": "PRODUCTION_DEPLOYMENT_GUIDE.md",
                "api_documentation": "docs/API.md",
                "health_monitor": "scripts/health-monitor.py",
                "auto_recovery": "scripts/auto-recovery.py"
            }
        }
        
        return report
    
    def execute_deployment_process(self, **kwargs) -> Dict:
        """Execute complete deployment process"""
        self.log_step("Deployment Process", "START", "Starting complete deployment execution")
        
        # Step 1: Setup local environment
        self.setup_local_environment()
        
        # Step 2: Supabase setup guide
        supabase_config = self.create_supabase_project_guide()
        
        # Step 3: Railway deployment config
        railway_config = self.create_railway_deployment_config()
        
        # Step 4: Render deployment config  
        render_config = self.create_render_deployment_config()
        
        # Step 5: Create deployment checklist
        checklist = self.create_deployment_checklist()
        
        # Step 6: Optional automated setup (if credentials provided)
        supabase_url = kwargs.get("supabase_url")
        supabase_key = kwargs.get("supabase_service_key")
        if supabase_url and supabase_key:
            self.run_supabase_setup(supabase_url, supabase_key)
        
        # Step 7: Optional deployment verification
        app_url = kwargs.get("app_url")
        if app_url:
            self.verify_deployment(app_url)
        
        # Generate final report
        report = self.generate_deployment_report()
        
        # Save deployment report
        with open("deployment_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        self.log_step("Deployment Process", "SUCCESS", "Deployment execution completed", {
            "report_file": "deployment_report.json",
            "duration": f"{report['deployment_summary']['duration_seconds']:.1f}s"
        })
        
        return report


def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Execute Heckx AI Video Generator Deployment")
    parser.add_argument("--supabase-url", help="Supabase project URL")
    parser.add_argument("--supabase-key", help="Supabase service role key")
    parser.add_argument("--app-url", help="Deployed application URL for verification")
    parser.add_argument("--platform", choices=["railway", "render"], help="Deployment platform")
    
    args = parser.parse_args()
    
    print("🚀 Heckx AI Video Generator - Deployment Executor")
    print("=" * 60)
    
    executor = DeploymentExecutor()
    
    # Execute deployment with provided parameters
    report = executor.execute_deployment_process(
        supabase_url=args.supabase_url,
        supabase_service_key=args.supabase_key,
        app_url=args.app_url,
        platform=args.platform
    )
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 DEPLOYMENT EXECUTION SUMMARY")
    print("=" * 60)
    
    summary = report["deployment_summary"]
    print(f"⏱️  Duration: {summary['duration_seconds']:.1f} seconds")
    print(f"📋 Total Steps: {summary['total_steps']}")
    print(f"✅ Successful: {summary['successful_steps']}")
    print(f"❌ Failed: {summary['failed_steps']}")
    
    print(f"\n📁 Generated Files:")
    for file in report["generated_files"]:
        if os.path.exists(file):
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ {file}")
    
    print(f"\n📖 Next Steps:")
    for step in report["next_steps"]:
        print(f"   {step}")
    
    print(f"\n📄 Full report saved to: deployment_report.json")
    print(f"📋 Follow PRODUCTION_DEPLOYMENT_GUIDE.md for detailed instructions")
    
    # Exit with appropriate code
    if summary["failed_steps"] == 0:
        print("\n🎉 Deployment preparation completed successfully!")
        sys.exit(0)
    else:
        print(f"\n⚠️  Deployment preparation completed with {summary['failed_steps']} issues")
        sys.exit(1)


if __name__ == "__main__":
    main()