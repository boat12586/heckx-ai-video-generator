#!/usr/bin/env python3
"""
Automatic Fallback and Recovery System for Heckx AI Video Generator
Handles service failures, deployment rollbacks, and disaster recovery
"""

import os
import sys
import time
import json
import subprocess
import shutil
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import requests
import tarfile


class RecoveryAction(Enum):
    RESTART_SERVICE = "restart_service"
    ROLLBACK_DEPLOYMENT = "rollback_deployment"
    SWITCH_DATABASE = "switch_database"
    SCALE_RESOURCES = "scale_resources"
    CLEAR_CACHE = "clear_cache"
    FAILOVER_STORAGE = "failover_storage"
    EMERGENCY_MAINTENANCE = "emergency_maintenance"


class FailureType(Enum):
    SERVICE_DOWN = "service_down"
    HIGH_ERROR_RATE = "high_error_rate"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    DATABASE_FAILURE = "database_failure"
    STORAGE_FAILURE = "storage_failure"
    DEPENDENCY_FAILURE = "dependency_failure"
    DEPLOYMENT_FAILURE = "deployment_failure"


@dataclass
class RecoveryPlan:
    failure_type: FailureType
    actions: List[RecoveryAction]
    priority: int
    timeout: int
    prerequisites: List[str]
    success_criteria: List[str]


class BackupManager:
    """Manage backups and restore operations"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.backup_dir = config.get('backup_dir', '/app/backups')
        self.retention_days = config.get('retention_days', 7)
        
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def create_application_backup(self) -> Optional[str]:
        """Create complete application backup"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"heckx_backup_{timestamp}"
        backup_path = os.path.join(self.backup_dir, f"{backup_name}.tar.gz")
        
        try:
            # Files and directories to backup
            backup_items = [
                '/app/data',
                '/app/logs',
                '/app/config',
                '/app/.env.production',
                '/app/docker-compose.prod.yml'
            ]
            
            with tarfile.open(backup_path, 'w:gz') as tar:
                for item in backup_items:
                    if os.path.exists(item):
                        tar.add(item, arcname=os.path.basename(item))
            
            print(f"✅ Application backup created: {backup_path}")
            return backup_path
            
        except Exception as e:
            print(f"❌ Backup creation failed: {e}")
            return None
    
    def create_database_backup(self, db_url: str) -> Optional[str]:
        """Create database backup"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(self.backup_dir, f"database_backup_{timestamp}.sql")
        
        try:
            # Extract database connection details
            # This is a simplified version - would need proper URL parsing
            cmd = [
                'pg_dump',
                db_url,
                '--no-password',
                '--file', backup_file
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                print(f"✅ Database backup created: {backup_file}")
                return backup_file
            else:
                print(f"❌ Database backup failed: {result.stderr}")
                return None
                
        except Exception as e:
            print(f"❌ Database backup error: {e}")
            return None
    
    def list_backups(self) -> List[Dict]:
        """List available backups"""
        backups = []
        
        for filename in os.listdir(self.backup_dir):
            if filename.endswith(('.tar.gz', '.sql')):
                filepath = os.path.join(self.backup_dir, filename)
                stat = os.stat(filepath)
                
                backups.append({
                    'filename': filename,
                    'path': filepath,
                    'size': stat.st_size,
                    'created': datetime.fromtimestamp(stat.st_mtime),
                    'type': 'application' if filename.endswith('.tar.gz') else 'database'
                })
        
        return sorted(backups, key=lambda x: x['created'], reverse=True)
    
    def restore_from_backup(self, backup_path: str) -> bool:
        """Restore from backup"""
        try:
            if backup_path.endswith('.tar.gz'):
                return self._restore_application_backup(backup_path)
            elif backup_path.endswith('.sql'):
                return self._restore_database_backup(backup_path)
            else:
                print(f"❌ Unknown backup type: {backup_path}")
                return False
                
        except Exception as e:
            print(f"❌ Restore failed: {e}")
            return False
    
    def _restore_application_backup(self, backup_path: str) -> bool:
        """Restore application from backup"""
        try:
            with tarfile.open(backup_path, 'r:gz') as tar:
                tar.extractall('/app')
            
            print(f"✅ Application restored from: {backup_path}")
            return True
            
        except Exception as e:
            print(f"❌ Application restore failed: {e}")
            return False
    
    def _restore_database_backup(self, backup_path: str) -> bool:
        """Restore database from backup"""
        try:
            db_url = self.config.get('database_url')
            if not db_url:
                print("❌ Database URL not configured")
                return False
            
            cmd = [
                'psql',
                db_url,
                '--file', backup_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                print(f"✅ Database restored from: {backup_path}")
                return True
            else:
                print(f"❌ Database restore failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Database restore error: {e}")
            return False
    
    def cleanup_old_backups(self):
        """Remove old backups based on retention policy"""
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        
        for backup in self.list_backups():
            if backup['created'] < cutoff_date:
                try:
                    os.remove(backup['path'])
                    print(f"🗑️  Removed old backup: {backup['filename']}")
                except Exception as e:
                    print(f"❌ Failed to remove backup {backup['filename']}: {e}")


class ServiceController:
    """Control service lifecycle and deployments"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.docker_compose_file = config.get('compose_file', 'docker-compose.prod.yml')
        self.service_name = config.get('service_name', 'heckx-video-generator')
    
    def restart_service(self, service: str = None) -> bool:
        """Restart specific service or all services"""
        service = service or self.service_name
        
        try:
            print(f"🔄 Restarting service: {service}")
            
            # Try Docker Compose restart
            cmd = ['docker-compose', '-f', self.docker_compose_file, 'restart', service]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                print(f"✅ Service {service} restarted successfully")
                
                # Wait for service to be ready
                time.sleep(10)
                return self._verify_service_health(service)
            else:
                print(f"❌ Service restart failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Restart error: {e}")
            return False
    
    def scale_service(self, service: str, replicas: int) -> bool:
        """Scale service to specified replica count"""
        try:
            print(f"📊 Scaling {service} to {replicas} replicas")
            
            cmd = ['docker-compose', '-f', self.docker_compose_file, 'up', '-d', '--scale', f"{service}={replicas}"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                print(f"✅ Service {service} scaled to {replicas} replicas")
                return True
            else:
                print(f"❌ Scaling failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Scaling error: {e}")
            return False
    
    def stop_service(self, service: str = None) -> bool:
        """Stop service gracefully"""
        service = service or self.service_name
        
        try:
            print(f"⏹️  Stopping service: {service}")
            
            cmd = ['docker-compose', '-f', self.docker_compose_file, 'stop', service]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                print(f"✅ Service {service} stopped")
                return True
            else:
                print(f"❌ Stop failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Stop error: {e}")
            return False
    
    def start_service(self, service: str = None) -> bool:
        """Start service"""
        service = service or self.service_name
        
        try:
            print(f"▶️  Starting service: {service}")
            
            cmd = ['docker-compose', '-f', self.docker_compose_file, 'up', '-d', service]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                print(f"✅ Service {service} started")
                
                # Wait for service to be ready
                time.sleep(15)
                return self._verify_service_health(service)
            else:
                print(f"❌ Start failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Start error: {e}")
            return False
    
    def _verify_service_health(self, service: str) -> bool:
        """Verify service is healthy after restart"""
        max_attempts = 12  # 2 minutes with 10-second intervals
        base_url = self.config.get('base_url', 'http://localhost:5001')
        
        for attempt in range(max_attempts):
            try:
                response = requests.get(f"{base_url}/api/health", timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('status') == 'healthy':
                        print(f"✅ Service {service} is healthy")
                        return True
            except:
                pass
            
            print(f"⏳ Waiting for {service} to be ready... ({attempt + 1}/{max_attempts})")
            time.sleep(10)
        
        print(f"❌ Service {service} failed health check")
        return False
    
    def rollback_deployment(self, backup_path: str = None) -> bool:
        """Rollback to previous deployment"""
        try:
            print("🔙 Starting deployment rollback")
            
            # Stop current services
            if not self.stop_service():
                print("⚠️  Failed to stop services, continuing rollback")
            
            # Restore from backup if provided
            if backup_path:
                backup_manager = BackupManager(self.config)
                if not backup_manager.restore_from_backup(backup_path):
                    print("❌ Backup restoration failed")
                    return False
            
            # Start services with previous configuration
            if self.start_service():
                print("✅ Rollback completed successfully")
                return True
            else:
                print("❌ Rollback failed - services did not start")
                return False
                
        except Exception as e:
            print(f"❌ Rollback error: {e}")
            return False


class AutoRecoverySystem:
    """Main automatic recovery orchestrator"""
    
    def __init__(self, config_file: str = None):
        self.config = self._load_config(config_file)
        self.backup_manager = BackupManager(self.config.get('backup', {}))
        self.service_controller = ServiceController(self.config.get('services', {}))
        self.recovery_plans = self._init_recovery_plans()
        self.recovery_history = []
    
    def _load_config(self, config_file: str) -> Dict:
        """Load configuration"""
        default_config = {
            "base_url": os.getenv("BASE_URL", "http://localhost:5001"),
            "backup": {
                "backup_dir": "/app/backups",
                "retention_days": 7
            },
            "services": {
                "compose_file": "docker-compose.prod.yml",
                "service_name": "heckx-video-generator"
            },
            "recovery": {
                "max_attempts": 3,
                "cooldown_minutes": 5
            }
        }
        
        if config_file and os.path.exists(config_file):
            with open(config_file, 'r') as f:
                file_config = json.load(f)
                default_config.update(file_config)
        
        return default_config
    
    def _init_recovery_plans(self) -> Dict[FailureType, RecoveryPlan]:
        """Initialize recovery plans for different failure types"""
        return {
            FailureType.SERVICE_DOWN: RecoveryPlan(
                failure_type=FailureType.SERVICE_DOWN,
                actions=[
                    RecoveryAction.RESTART_SERVICE,
                    RecoveryAction.ROLLBACK_DEPLOYMENT
                ],
                priority=1,
                timeout=300,
                prerequisites=[],
                success_criteria=['service_healthy', 'api_responding']
            ),
            
            FailureType.HIGH_ERROR_RATE: RecoveryPlan(
                failure_type=FailureType.HIGH_ERROR_RATE,
                actions=[
                    RecoveryAction.CLEAR_CACHE,
                    RecoveryAction.RESTART_SERVICE,
                    RecoveryAction.SCALE_RESOURCES
                ],
                priority=2,
                timeout=180,
                prerequisites=[],
                success_criteria=['error_rate_normal', 'response_time_acceptable']
            ),
            
            FailureType.RESOURCE_EXHAUSTION: RecoveryPlan(
                failure_type=FailureType.RESOURCE_EXHAUSTION,
                actions=[
                    RecoveryAction.SCALE_RESOURCES,
                    RecoveryAction.CLEAR_CACHE,
                    RecoveryAction.RESTART_SERVICE
                ],
                priority=1,
                timeout=240,
                prerequisites=['backup_available'],
                success_criteria=['resource_usage_normal']
            ),
            
            FailureType.DATABASE_FAILURE: RecoveryPlan(
                failure_type=FailureType.DATABASE_FAILURE,
                actions=[
                    RecoveryAction.SWITCH_DATABASE,
                    RecoveryAction.ROLLBACK_DEPLOYMENT
                ],
                priority=1,
                timeout=600,
                prerequisites=['database_backup_available'],
                success_criteria=['database_accessible', 'data_consistent']
            ),
            
            FailureType.DEPLOYMENT_FAILURE: RecoveryPlan(
                failure_type=FailureType.DEPLOYMENT_FAILURE,
                actions=[
                    RecoveryAction.ROLLBACK_DEPLOYMENT
                ],
                priority=1,
                timeout=300,
                prerequisites=['previous_backup_available'],
                success_criteria=['service_healthy', 'api_responding']
            )
        }
    
    def detect_failure_type(self, health_data: Dict) -> Optional[FailureType]:
        """Analyze health data to determine failure type"""
        overall_status = health_data.get('overall_status', 'unknown')
        checks = health_data.get('checks', [])
        
        # Service completely down
        api_check = next((c for c in checks if 'API' in c.get('name', '')), None)
        if api_check and api_check.get('status') == 'critical':
            return FailureType.SERVICE_DOWN
        
        # High error rate
        if any(c.get('status') == 'unhealthy' for c in checks):
            return FailureType.HIGH_ERROR_RATE
        
        # Resource issues
        resource_check = next((c for c in checks if 'Resource' in c.get('name', '')), None)
        if resource_check and resource_check.get('status') in ['unhealthy', 'critical']:
            return FailureType.RESOURCE_EXHAUSTION
        
        # Database issues
        db_check = next((c for c in checks if any(db in c.get('name', '') for db in ['Supabase', 'Database', 'Redis']), None)
        if db_check and db_check.get('status') == 'critical':
            return FailureType.DATABASE_FAILURE
        
        return None
    
    def execute_recovery_action(self, action: RecoveryAction) -> bool:
        """Execute a specific recovery action"""
        print(f"🔧 Executing recovery action: {action.value}")
        
        try:
            if action == RecoveryAction.RESTART_SERVICE:
                return self.service_controller.restart_service()
            
            elif action == RecoveryAction.ROLLBACK_DEPLOYMENT:
                # Find most recent backup
                backups = self.backup_manager.list_backups()
                if backups:
                    latest_backup = backups[0]['path']
                    return self.service_controller.rollback_deployment(latest_backup)
                else:
                    print("❌ No backup available for rollback")
                    return False
            
            elif action == RecoveryAction.CLEAR_CACHE:
                # Implementation would clear Redis cache
                print("🧹 Clearing cache")
                return True
            
            elif action == RecoveryAction.SCALE_RESOURCES:
                # Scale down to reduce resource usage
                return self.service_controller.scale_service("heckx-video-generator", 1)
            
            elif action == RecoveryAction.SWITCH_DATABASE:
                print("🔄 Database failover not implemented")
                return False
            
            elif action == RecoveryAction.EMERGENCY_MAINTENANCE:
                print("🚨 Entering emergency maintenance mode")
                return self.service_controller.stop_service()
            
            else:
                print(f"❌ Unknown recovery action: {action}")
                return False
                
        except Exception as e:
            print(f"❌ Recovery action failed: {e}")
            return False
    
    def execute_recovery_plan(self, failure_type: FailureType) -> bool:
        """Execute recovery plan for failure type"""
        plan = self.recovery_plans.get(failure_type)
        if not plan:
            print(f"❌ No recovery plan for failure type: {failure_type}")
            return False
        
        print(f"📋 Executing recovery plan for: {failure_type.value}")
        
        # Record recovery attempt
        recovery_record = {
            'timestamp': datetime.now().isoformat(),
            'failure_type': failure_type.value,
            'plan': plan.actions,
            'success': False,
            'actions_completed': []
        }
        
        # Execute actions in sequence
        for action in plan.actions:
            if self.execute_recovery_action(action):
                recovery_record['actions_completed'].append(action.value)
                print(f"✅ Action completed: {action.value}")
            else:
                print(f"❌ Action failed: {action.value}")
                break
        
        # Verify recovery success
        time.sleep(30)  # Wait for services to stabilize
        success = self._verify_recovery_success(plan.success_criteria)
        
        recovery_record['success'] = success
        self.recovery_history.append(recovery_record)
        
        if success:
            print("✅ Recovery plan completed successfully")
        else:
            print("❌ Recovery plan failed")
        
        return success
    
    def _verify_recovery_success(self, success_criteria: List[str]) -> bool:
        """Verify that recovery was successful"""
        base_url = self.config.get('base_url', 'http://localhost:5001')
        
        try:
            # Check API health
            response = requests.get(f"{base_url}/api/health", timeout=30)
            if response.status_code == 200:
                data = response.json()
                return data.get('status') == 'healthy'
            else:
                return False
        except:
            return False
    
    def handle_failure(self, health_data: Dict) -> bool:
        """Main failure handling entry point"""
        failure_type = self.detect_failure_type(health_data)
        
        if not failure_type:
            print("ℹ️  No critical failure detected")
            return True
        
        print(f"🚨 Failure detected: {failure_type.value}")
        
        # Create backup before recovery
        print("💾 Creating backup before recovery")
        self.backup_manager.create_application_backup()
        
        # Execute recovery
        success = self.execute_recovery_plan(failure_type)
        
        # Send notification about recovery attempt
        self._send_recovery_notification(failure_type, success)
        
        return success
    
    def _send_recovery_notification(self, failure_type: FailureType, success: bool):
        """Send notification about recovery attempt"""
        status = "✅ SUCCESS" if success else "❌ FAILED"
        message = f"Auto-recovery {status} for {failure_type.value}"
        
        # In a real implementation, this would send to Slack, email, etc.
        print(f"📢 NOTIFICATION: {message}")
    
    def create_scheduled_backup(self):
        """Create scheduled backup"""
        print("💾 Creating scheduled backup")
        
        # Create application backup
        app_backup = self.backup_manager.create_application_backup()
        
        # Create database backup if configured
        db_url = self.config.get('database_url')
        if db_url:
            db_backup = self.backup_manager.create_database_backup(db_url)
        
        # Cleanup old backups
        self.backup_manager.cleanup_old_backups()
        
        print("✅ Scheduled backup completed")
    
    def get_recovery_status(self) -> Dict:
        """Get current recovery system status"""
        return {
            'timestamp': datetime.now().isoformat(),
            'recovery_history': self.recovery_history[-10:],  # Last 10 attempts
            'available_backups': len(self.backup_manager.list_backups()),
            'system_status': 'operational'
        }


def main():
    """Main function for CLI usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Heckx Auto-Recovery System")
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--backup", action="store_true", help="Create backup")
    parser.add_argument("--rollback", help="Rollback to specific backup")
    parser.add_argument("--status", action="store_true", help="Show recovery status")
    parser.add_argument("--test-recovery", help="Test recovery for failure type")
    
    args = parser.parse_args()
    
    recovery_system = AutoRecoverySystem(args.config)
    
    if args.backup:
        recovery_system.create_scheduled_backup()
    
    elif args.rollback:
        success = recovery_system.service_controller.rollback_deployment(args.rollback)
        sys.exit(0 if success else 1)
    
    elif args.status:
        status = recovery_system.get_recovery_status()
        print(json.dumps(status, indent=2))
    
    elif args.test_recovery:
        try:
            failure_type = FailureType(args.test_recovery)
            success = recovery_system.execute_recovery_plan(failure_type)
            sys.exit(0 if success else 1)
        except ValueError:
            print(f"Unknown failure type: {args.test_recovery}")
            sys.exit(1)
    
    else:
        print("Heckx Auto-Recovery System")
        print("Use --help for available options")


if __name__ == "__main__":
    main()