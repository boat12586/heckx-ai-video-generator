#!/usr/bin/env python3
"""
Deployment Verification Script for Heckx AI Video Generator
Comprehensive testing of all deployment components and production readiness
"""

import os
import sys
import time
import json
import requests
import subprocess
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import yaml


@dataclass
class VerificationResult:
    test_name: str
    success: bool
    message: str
    details: Dict = None
    duration: float = 0


class DeploymentVerifier:
    """Comprehensive deployment verification"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.base_url = config.get('base_url', 'http://localhost:5001')
        self.results = []
        self.start_time = datetime.now()
    
    def log_result(self, test_name: str, success: bool, message: str, details: Dict = None, duration: float = 0):
        """Log verification result"""
        result = VerificationResult(test_name, success, message, details, duration)
        self.results.append(result)
        
        status = "✅" if success else "❌"
        print(f"{status} {test_name}: {message}")
        if details and isinstance(details, dict):
            for key, value in details.items():
                print(f"   {key}: {value}")
    
    def verify_environment_variables(self) -> bool:
        """Verify all required environment variables are set"""
        print("\n🔍 Verifying Environment Variables...")
        
        required_vars = [
            'ENVIRONMENT',
            'SECRET_KEY',
            'PIXABAY_API_KEY',
            'SUPABASE_URL',
            'SUPABASE_ANON_KEY',
            'SUPABASE_SERVICE_ROLE_KEY'
        ]
        
        production_vars = [
            'DATABASE_URL',
            'REDIS_URL',
            'JWT_SECRET_KEY',
            'API_KEY'
        ]
        
        missing_vars = []
        weak_vars = []
        
        # Check required variables
        for var in required_vars:
            value = os.getenv(var)
            if not value:
                missing_vars.append(var)
            elif value in ['your-key-here', 'changeme', 'default']:
                weak_vars.append(var)
        
        # Check production-specific variables
        environment = os.getenv('ENVIRONMENT', 'development')
        if environment == 'production':
            for var in production_vars:
                value = os.getenv(var)
                if not value:
                    missing_vars.append(var)
        
        success = len(missing_vars) == 0
        details = {
            'environment': environment,
            'missing_variables': missing_vars,
            'weak_variables': weak_vars,
            'total_checked': len(required_vars) + len(production_vars)
        }
        
        if success:
            message = f"All required environment variables present for {environment}"
        else:
            message = f"Missing {len(missing_vars)} required variables"
        
        self.log_result("Environment Variables", success, message, details)
        return success
    
    def verify_docker_setup(self) -> bool:
        """Verify Docker and containers are running"""
        print("\n🐳 Verifying Docker Setup...")
        
        try:
            # Check if Docker is installed
            result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
            if result.returncode != 0:
                self.log_result("Docker Installation", False, "Docker not installed")
                return False
            
            docker_version = result.stdout.strip()
            
            # Check if containers are running
            result = subprocess.run(['docker', 'ps', '--format', 'json'], capture_output=True, text=True)
            if result.returncode != 0:
                self.log_result("Docker Status", False, "Cannot list Docker containers")
                return False
            
            # Parse container information
            containers = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    try:
                        container = json.loads(line)
                        containers.append({
                            'name': container.get('Names', ''),
                            'status': container.get('Status', ''),
                            'image': container.get('Image', '')
                        })
                    except json.JSONDecodeError:
                        pass
            
            success = len(containers) > 0
            details = {
                'docker_version': docker_version,
                'running_containers': len(containers),
                'containers': containers
            }
            
            message = f"Docker operational with {len(containers)} containers"
            self.log_result("Docker Setup", success, message, details)
            return success
            
        except FileNotFoundError:
            self.log_result("Docker Setup", False, "Docker command not found")
            return False
        except Exception as e:
            self.log_result("Docker Setup", False, f"Docker check failed: {str(e)}")
            return False
    
    def verify_api_endpoints(self) -> bool:
        """Verify all API endpoints are responding"""
        print("\n🌐 Verifying API Endpoints...")
        
        endpoints = [
            ('/api/health', 'GET', 200),
            ('/api/themes', 'GET', 200),
            ('/api/lofi/categories', 'GET', 200),
            ('/api/stats', 'GET', 200),
            ('/api/projects', 'GET', 200)
        ]
        
        results = []
        total_success = 0
        
        for endpoint, method, expected_status in endpoints:
            start_time = time.time()
            try:
                if method == 'GET':
                    response = requests.get(f"{self.base_url}{endpoint}", timeout=30)
                else:
                    response = requests.request(method, f"{self.base_url}{endpoint}", timeout=30)
                
                duration = (time.time() - start_time) * 1000
                success = response.status_code == expected_status
                
                if success:
                    total_success += 1
                
                results.append({
                    'endpoint': endpoint,
                    'method': method,
                    'status_code': response.status_code,
                    'expected': expected_status,
                    'response_time_ms': round(duration, 2),
                    'success': success
                })
                
            except Exception as e:
                results.append({
                    'endpoint': endpoint,
                    'method': method,
                    'error': str(e),
                    'success': False
                })
        
        success = total_success == len(endpoints)
        details = {
            'endpoints_tested': len(endpoints),
            'successful': total_success,
            'failed': len(endpoints) - total_success,
            'results': results
        }
        
        message = f"{total_success}/{len(endpoints)} endpoints responding correctly"
        self.log_result("API Endpoints", success, message, details)
        return success
    
    def verify_video_generation(self) -> bool:
        """Test video generation functionality"""
        print("\n🎬 Verifying Video Generation...")
        
        try:
            # Test motivation video generation
            payload = {
                'theme': 'inner_strength',
                'duration': 10,  # Short test
                'async': True
            }
            
            start_time = time.time()
            response = requests.post(
                f"{self.base_url}/api/generate/motivation",
                json=payload,
                timeout=60
            )
            duration = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                task_id = data.get('task_id')
                
                details = {
                    'response_time_ms': round(duration, 2),
                    'task_id': task_id,
                    'status_code': response.status_code
                }
                
                self.log_result("Video Generation", True, "Generation API functional", details)
                return True
            else:
                details = {
                    'status_code': response.status_code,
                    'response': response.text[:200]
                }
                self.log_result("Video Generation", False, f"API returned {response.status_code}", details)
                return False
                
        except Exception as e:
            self.log_result("Video Generation", False, f"Generation test failed: {str(e)}")
            return False
    
    def verify_database_connections(self) -> bool:
        """Verify database connections"""
        print("\n🗄️  Verifying Database Connections...")
        
        success_count = 0
        total_checks = 0
        
        # Test Supabase connection through API
        try:
            response = requests.get(f"{self.base_url}/api/stats", timeout=30)
            if response.status_code == 200:
                data = response.json()
                if 'statistics' in data:
                    success_count += 1
                    self.log_result("Supabase Database", True, "Connection successful via API")
                else:
                    self.log_result("Supabase Database", False, "API response missing statistics")
            else:
                self.log_result("Supabase Database", False, f"Stats API returned {response.status_code}")
            total_checks += 1
        except Exception as e:
            self.log_result("Supabase Database", False, f"Connection test failed: {str(e)}")
            total_checks += 1
        
        # Test Redis connection (if health endpoint reports it)
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=30)
            if response.status_code == 200:
                data = response.json()
                services = data.get('services', {})
                
                if 'redis' in services or 'cache' in services:
                    redis_status = services.get('redis', services.get('cache', False))
                    if redis_status:
                        success_count += 1
                        self.log_result("Redis Cache", True, "Connection successful")
                    else:
                        self.log_result("Redis Cache", False, "Not accessible")
                    total_checks += 1
        except Exception as e:
            self.log_result("Redis Cache", False, f"Check failed: {str(e)}")
            total_checks += 1
        
        overall_success = success_count == total_checks and total_checks > 0
        return overall_success
    
    def verify_security_configuration(self) -> bool:
        """Verify security settings"""
        print("\n🔒 Verifying Security Configuration...")
        
        checks = []
        
        # Check HTTPS configuration (in production)
        environment = os.getenv('ENVIRONMENT', 'development')
        if environment == 'production':
            if self.base_url.startswith('https://'):
                checks.append(('HTTPS', True, 'HTTPS configured'))
            else:
                checks.append(('HTTPS', False, 'HTTPS not configured for production'))
        else:
            checks.append(('HTTPS', True, 'HTTPS not required for development'))
        
        # Check API authentication
        auth_enabled = os.getenv('ENABLE_API_AUTH', 'false').lower() == 'true'
        if auth_enabled:
            api_key = os.getenv('API_KEY')
            if api_key and api_key not in ['your-api-key', 'changeme']:
                checks.append(('API Authentication', True, 'API key configured'))
            else:
                checks.append(('API Authentication', False, 'Weak or missing API key'))
        else:
            checks.append(('API Authentication', False, 'API authentication disabled'))
        
        # Check secret keys
        secret_key = os.getenv('SECRET_KEY')
        if secret_key and len(secret_key) >= 32 and secret_key not in ['your-secret-key', 'changeme']:
            checks.append(('Secret Key', True, 'Strong secret key configured'))
        else:
            checks.append(('Secret Key', False, 'Weak or missing secret key'))
        
        # Check CORS configuration
        cors_enabled = os.getenv('ENABLE_CORS', 'false').lower() == 'true'
        if cors_enabled:
            cors_origins = os.getenv('CORS_ORIGINS', '*')
            if cors_origins != '*':
                checks.append(('CORS', True, 'CORS origins restricted'))
            else:
                checks.append(('CORS', False, 'CORS allows all origins'))
        else:
            checks.append(('CORS', True, 'CORS disabled'))
        
        # Log all security checks
        successful_checks = 0
        for check_name, success, message in checks:
            if success:
                successful_checks += 1
            self.log_result(f"Security: {check_name}", success, message)
        
        overall_success = successful_checks == len(checks)
        return overall_success
    
    def verify_monitoring_setup(self) -> bool:
        """Verify monitoring and health check setup"""
        print("\n📊 Verifying Monitoring Setup...")
        
        checks = []
        
        # Check health endpoint
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=30)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'healthy':
                    checks.append(('Health Endpoint', True, 'Health endpoint functional'))
                else:
                    checks.append(('Health Endpoint', False, f"Health status: {data.get('status')}"))
            else:
                checks.append(('Health Endpoint', False, f"HTTP {response.status_code}"))
        except Exception as e:
            checks.append(('Health Endpoint', False, f"Health check failed: {str(e)}"))
        
        # Check if monitoring scripts exist
        monitoring_scripts = [
            'scripts/health-monitor.py',
            'scripts/auto-recovery.py'
        ]
        
        for script in monitoring_scripts:
            if os.path.exists(script):
                checks.append((f'Script: {os.path.basename(script)}', True, 'Monitoring script available'))
            else:
                checks.append((f'Script: {os.path.basename(script)}', False, 'Monitoring script missing'))
        
        # Log all monitoring checks
        successful_checks = 0
        for check_name, success, message in checks:
            if success:
                successful_checks += 1
            self.log_result(f"Monitoring: {check_name}", success, message)
        
        overall_success = successful_checks >= len(checks) * 0.8  # 80% success rate
        return overall_success
    
    def verify_deployment_files(self) -> bool:
        """Verify deployment configuration files"""
        print("\n📁 Verifying Deployment Files...")
        
        required_files = [
            'Dockerfile',
            'docker-compose.prod.yml',
            'railway.json',
            'render.yaml',
            '.env.production',
            'requirements.txt'
        ]
        
        optional_files = [
            '.env.staging',
            'scripts/deploy.sh',
            'scripts/setup-supabase.sql'
        ]
        
        missing_required = []
        missing_optional = []
        
        for file in required_files:
            if not os.path.exists(file):
                missing_required.append(file)
        
        for file in optional_files:
            if not os.path.exists(file):
                missing_optional.append(file)
        
        success = len(missing_required) == 0
        details = {
            'required_files': len(required_files),
            'optional_files': len(optional_files),
            'missing_required': missing_required,
            'missing_optional': missing_optional
        }
        
        if success:
            message = f"All {len(required_files)} required deployment files present"
        else:
            message = f"Missing {len(missing_required)} required files"
        
        self.log_result("Deployment Files", success, message, details)
        return success
    
    def run_comprehensive_verification(self) -> Dict:
        """Run all verification tests"""
        print("🚀 Starting Comprehensive Deployment Verification")
        print("=" * 60)
        
        # Run all verification tests
        verification_tests = [
            ("Environment Variables", self.verify_environment_variables),
            ("Deployment Files", self.verify_deployment_files),
            ("Docker Setup", self.verify_docker_setup),
            ("API Endpoints", self.verify_api_endpoints),
            ("Database Connections", self.verify_database_connections),
            ("Video Generation", self.verify_video_generation),
            ("Security Configuration", self.verify_security_configuration),
            ("Monitoring Setup", self.verify_monitoring_setup)
        ]
        
        passed_tests = 0
        total_tests = len(verification_tests)
        
        for test_name, test_function in verification_tests:
            try:
                if test_function():
                    passed_tests += 1
            except Exception as e:
                self.log_result(test_name, False, f"Test failed with exception: {str(e)}")
        
        # Calculate overall success
        success_rate = (passed_tests / total_tests) * 100
        deployment_ready = success_rate >= 80  # 80% success rate required
        
        # Generate summary
        end_time = datetime.now()
        total_duration = (end_time - self.start_time).total_seconds()
        
        summary = {
            'deployment_ready': deployment_ready,
            'success_rate': round(success_rate, 1),
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': total_tests - passed_tests,
            'verification_duration': round(total_duration, 2),
            'timestamp': end_time.isoformat(),
            'environment': os.getenv('ENVIRONMENT', 'unknown'),
            'base_url': self.base_url
        }
        
        self._print_verification_summary(summary)
        
        return {
            'summary': summary,
            'detailed_results': [
                {
                    'test_name': r.test_name,
                    'success': r.success,
                    'message': r.message,
                    'details': r.details,
                    'duration': r.duration
                }
                for r in self.results
            ]
        }
    
    def _print_verification_summary(self, summary: Dict):
        """Print verification summary"""
        print("\n" + "=" * 60)
        print("📊 DEPLOYMENT VERIFICATION SUMMARY")
        print("=" * 60)
        
        status_emoji = "✅" if summary['deployment_ready'] else "❌"
        print(f"{status_emoji} Deployment Ready: {summary['deployment_ready']}")
        print(f"📈 Success Rate: {summary['success_rate']}%")
        print(f"📊 Tests: {summary['passed_tests']}/{summary['total_tests']} passed")
        print(f"⏱️  Duration: {summary['verification_duration']}s")
        print(f"🌍 Environment: {summary['environment']}")
        print(f"🔗 Base URL: {summary['base_url']}")
        
        if summary['deployment_ready']:
            print("\n🎉 DEPLOYMENT VERIFICATION SUCCESSFUL!")
            print("Your Heckx AI Video Generator is ready for production.")
        else:
            print("\n⚠️  DEPLOYMENT VERIFICATION FAILED!")
            print("Please review failed tests and fix issues before deployment.")
        
        print("\n📋 Failed Tests:")
        for result in self.results:
            if not result.success:
                print(f"   ❌ {result.test_name}: {result.message}")
        
        print("\n📄 Detailed verification report available in verification_report.json")


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Heckx Deployment Verification")
    parser.add_argument("--url", default="http://localhost:5001", help="Base URL to test")
    parser.add_argument("--output", default="verification_report.json", help="Output file for results")
    parser.add_argument("--env-file", help="Environment file to load")
    
    args = parser.parse_args()
    
    # Load environment file if specified
    if args.env_file and os.path.exists(args.env_file):
        from dotenv import load_dotenv
        load_dotenv(args.env_file)
    
    # Configure verifier
    config = {
        'base_url': args.url
    }
    
    # Run verification
    verifier = DeploymentVerifier(config)
    results = verifier.run_comprehensive_verification()
    
    # Save results
    try:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n📄 Results saved to: {args.output}")
    except Exception as e:
        print(f"\n⚠️  Could not save results: {e}")
    
    # Exit with appropriate code
    if results['summary']['deployment_ready']:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()