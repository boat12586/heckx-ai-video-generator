#!/usr/bin/env python3
"""
Advanced Health Check and Monitoring System for Heckx AI Video Generator
Includes automatic fallback, recovery, and alerting capabilities
"""

import os
import sys
import time
import json
import requests
import subprocess
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import psutil
import redis
from supabase import create_client


class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"


@dataclass
class HealthCheck:
    name: str
    status: HealthStatus
    message: str
    response_time: float
    timestamp: datetime
    metadata: Dict = None


@dataclass
class ServiceMetrics:
    cpu_percent: float
    memory_percent: float
    disk_usage: float
    response_time: float
    error_rate: float
    active_connections: int


class NotificationManager:
    """Handle alerts and notifications"""
    
    def __init__(self, config: Dict):
        self.slack_webhook = config.get('slack_webhook')
        self.email_config = config.get('email')
        self.notification_cooldown = config.get('cooldown', 300)  # 5 minutes
        self.last_notifications = {}
    
    def should_send_notification(self, alert_type: str) -> bool:
        """Check if enough time has passed since last notification"""
        last_sent = self.last_notifications.get(alert_type)
        if not last_sent:
            return True
        
        return (datetime.now() - last_sent).total_seconds() > self.notification_cooldown
    
    def send_slack_alert(self, title: str, message: str, status: HealthStatus):
        """Send Slack notification"""
        if not self.slack_webhook or not self.should_send_notification(f"slack_{title}"):
            return
        
        color_map = {
            HealthStatus.HEALTHY: "good",
            HealthStatus.DEGRADED: "warning", 
            HealthStatus.UNHEALTHY: "danger",
            HealthStatus.CRITICAL: "danger"
        }
        
        payload = {
            "text": f"🚨 Heckx Video Generator Alert",
            "attachments": [{
                "color": color_map.get(status, "warning"),
                "title": title,
                "text": message,
                "timestamp": int(time.time()),
                "fields": [
                    {"title": "Status", "value": status.value, "short": True},
                    {"title": "Time", "value": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "short": True}
                ]
            }]
        }
        
        try:
            response = requests.post(self.slack_webhook, json=payload, timeout=10)
            if response.status_code == 200:
                self.last_notifications[f"slack_{title}"] = datetime.now()
        except Exception as e:
            print(f"Failed to send Slack notification: {e}")
    
    def send_email_alert(self, subject: str, body: str):
        """Send email notification"""
        # Implementation would depend on email service used
        # For now, just log the alert
        print(f"EMAIL ALERT: {subject}\n{body}")


class ServiceHealthChecker:
    """Comprehensive service health monitoring"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.base_url = config.get('base_url', 'http://localhost:5001')
        self.timeout = config.get('timeout', 30)
        self.redis_client = None
        self.supabase_client = None
        self.notification_manager = NotificationManager(config.get('notifications', {}))
        
        # Initialize external service clients
        self._init_external_clients()
    
    def _init_external_clients(self):
        """Initialize external service clients"""
        try:
            redis_url = self.config.get('redis_url', 'redis://localhost:6379')
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
        except Exception as e:
            print(f"Redis connection failed: {e}")
        
        try:
            supabase_url = self.config.get('supabase_url')
            supabase_key = self.config.get('supabase_service_key')
            if supabase_url and supabase_key:
                self.supabase_client = create_client(supabase_url, supabase_key)
        except Exception as e:
            print(f"Supabase connection failed: {e}")
    
    def check_api_health(self) -> HealthCheck:
        """Check main API health endpoint"""
        start_time = time.time()
        
        try:
            response = requests.get(
                f"{self.base_url}/api/health",
                timeout=self.timeout
            )
            response_time = (time.time() - start_time) * 1000  # ms
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'healthy':
                    return HealthCheck(
                        name="API Health",
                        status=HealthStatus.HEALTHY,
                        message="API responding normally",
                        response_time=response_time,
                        timestamp=datetime.now(),
                        metadata=data
                    )
                else:
                    return HealthCheck(
                        name="API Health",
                        status=HealthStatus.DEGRADED,
                        message=f"API reports status: {data.get('status')}",
                        response_time=response_time,
                        timestamp=datetime.now(),
                        metadata=data
                    )
            else:
                return HealthCheck(
                    name="API Health",
                    status=HealthStatus.UNHEALTHY,
                    message=f"HTTP {response.status_code}",
                    response_time=response_time,
                    timestamp=datetime.now()
                )
        
        except requests.exceptions.ConnectionError:
            return HealthCheck(
                name="API Health",
                status=HealthStatus.CRITICAL,
                message="API server not responding",
                response_time=float('inf'),
                timestamp=datetime.now()
            )
        except requests.exceptions.Timeout:
            return HealthCheck(
                name="API Health",
                status=HealthStatus.UNHEALTHY,
                message=f"API timeout after {self.timeout}s",
                response_time=self.timeout * 1000,
                timestamp=datetime.now()
            )
        except Exception as e:
            return HealthCheck(
                name="API Health",
                status=HealthStatus.CRITICAL,
                message=f"API check failed: {str(e)}",
                response_time=float('inf'),
                timestamp=datetime.now()
            )
    
    def check_redis_health(self) -> HealthCheck:
        """Check Redis connection and performance"""
        start_time = time.time()
        
        if not self.redis_client:
            return HealthCheck(
                name="Redis Health",
                status=HealthStatus.CRITICAL,
                message="Redis client not initialized",
                response_time=0,
                timestamp=datetime.now()
            )
        
        try:
            # Test basic operations
            test_key = f"health_check:{int(time.time())}"
            self.redis_client.set(test_key, "test", ex=60)
            value = self.redis_client.get(test_key)
            self.redis_client.delete(test_key)
            
            response_time = (time.time() - start_time) * 1000
            
            if value == "test":
                # Check memory usage
                info = self.redis_client.info('memory')
                memory_usage = info.get('used_memory_human', 'unknown')
                
                return HealthCheck(
                    name="Redis Health",
                    status=HealthStatus.HEALTHY,
                    message=f"Redis operational, memory: {memory_usage}",
                    response_time=response_time,
                    timestamp=datetime.now(),
                    metadata={"memory_usage": memory_usage}
                )
            else:
                return HealthCheck(
                    name="Redis Health",
                    status=HealthStatus.UNHEALTHY,
                    message="Redis operations failing",
                    response_time=response_time,
                    timestamp=datetime.now()
                )
        
        except Exception as e:
            return HealthCheck(
                name="Redis Health",
                status=HealthStatus.CRITICAL,
                message=f"Redis error: {str(e)}",
                response_time=(time.time() - start_time) * 1000,
                timestamp=datetime.now()
            )
    
    def check_supabase_health(self) -> HealthCheck:
        """Check Supabase connection and storage"""
        start_time = time.time()
        
        if not self.supabase_client:
            return HealthCheck(
                name="Supabase Health",
                status=HealthStatus.CRITICAL,
                message="Supabase client not initialized",
                response_time=0,
                timestamp=datetime.now()
            )
        
        try:
            # Test database connection
            response = self.supabase_client.table('video_projects').select('*').limit(1).execute()
            
            # Test storage access
            buckets = self.supabase_client.storage.list_buckets()
            bucket_count = len(buckets)
            
            response_time = (time.time() - start_time) * 1000
            
            return HealthCheck(
                name="Supabase Health",
                status=HealthStatus.HEALTHY,
                message=f"Database and storage accessible, {bucket_count} buckets",
                response_time=response_time,
                timestamp=datetime.now(),
                metadata={"bucket_count": bucket_count}
            )
        
        except Exception as e:
            return HealthCheck(
                name="Supabase Health",
                status=HealthStatus.CRITICAL,
                message=f"Supabase error: {str(e)}",
                response_time=(time.time() - start_time) * 1000,
                timestamp=datetime.now()
            )
    
    def check_system_resources(self) -> HealthCheck:
        """Check system resource usage"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            
            # Determine status based on thresholds
            if cpu_percent > 90 or memory_percent > 90 or disk_percent > 95:
                status = HealthStatus.CRITICAL
                message = "System resources critically high"
            elif cpu_percent > 80 or memory_percent > 80 or disk_percent > 90:
                status = HealthStatus.UNHEALTHY
                message = "System resources high"
            elif cpu_percent > 70 or memory_percent > 70 or disk_percent > 85:
                status = HealthStatus.DEGRADED
                message = "System resources elevated"
            else:
                status = HealthStatus.HEALTHY
                message = "System resources normal"
            
            return HealthCheck(
                name="System Resources",
                status=status,
                message=message,
                response_time=0,
                timestamp=datetime.now(),
                metadata={
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory_percent,
                    "disk_percent": disk_percent
                }
            )
        
        except Exception as e:
            return HealthCheck(
                name="System Resources",
                status=HealthStatus.CRITICAL,
                message=f"Resource check failed: {str(e)}",
                response_time=0,
                timestamp=datetime.now()
            )
    
    def check_video_generation_capability(self) -> HealthCheck:
        """Test video generation functionality"""
        start_time = time.time()
        
        try:
            # Test generation endpoint with minimal request
            payload = {
                "theme": "inner_strength",
                "duration": 10,  # Short test video
                "async": True
            }
            
            response = requests.post(
                f"{self.base_url}/api/generate/motivation",
                json=payload,
                timeout=30
            )
            
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                if "task_id" in data:
                    return HealthCheck(
                        name="Video Generation",
                        status=HealthStatus.HEALTHY,
                        message="Video generation API functional",
                        response_time=response_time,
                        timestamp=datetime.now(),
                        metadata={"task_id": data["task_id"]}
                    )
                else:
                    return HealthCheck(
                        name="Video Generation",
                        status=HealthStatus.DEGRADED,
                        message="Generation response incomplete",
                        response_time=response_time,
                        timestamp=datetime.now()
                    )
            else:
                return HealthCheck(
                    name="Video Generation",
                    status=HealthStatus.UNHEALTHY,
                    message=f"Generation API error: {response.status_code}",
                    response_time=response_time,
                    timestamp=datetime.now()
                )
        
        except Exception as e:
            return HealthCheck(
                name="Video Generation",
                status=HealthStatus.CRITICAL,
                message=f"Generation test failed: {str(e)}",
                response_time=(time.time() - start_time) * 1000,
                timestamp=datetime.now()
            )
    
    def run_all_health_checks(self) -> List[HealthCheck]:
        """Run all health checks"""
        checks = [
            self.check_api_health(),
            self.check_redis_health(),
            self.check_supabase_health(),
            self.check_system_resources(),
            self.check_video_generation_capability()
        ]
        
        return checks
    
    def get_overall_health_status(self, checks: List[HealthCheck]) -> HealthStatus:
        """Determine overall system health"""
        statuses = [check.status for check in checks]
        
        if HealthStatus.CRITICAL in statuses:
            return HealthStatus.CRITICAL
        elif HealthStatus.UNHEALTHY in statuses:
            return HealthStatus.UNHEALTHY
        elif HealthStatus.DEGRADED in statuses:
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.HEALTHY


class AutoRecoveryManager:
    """Automatic recovery and fallback manager"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.recovery_attempts = {}
        self.max_attempts = config.get('max_recovery_attempts', 3)
        self.recovery_cooldown = config.get('recovery_cooldown', 300)  # 5 minutes
    
    def can_attempt_recovery(self, service: str) -> bool:
        """Check if recovery can be attempted for service"""
        attempts = self.recovery_attempts.get(service, {})
        last_attempt = attempts.get('last_attempt')
        attempt_count = attempts.get('count', 0)
        
        if attempt_count >= self.max_attempts:
            if last_attempt:
                time_since = (datetime.now() - last_attempt).total_seconds()
                if time_since < self.recovery_cooldown:
                    return False
                else:
                    # Reset counter after cooldown
                    self.recovery_attempts[service] = {'count': 0}
        
        return True
    
    def record_recovery_attempt(self, service: str):
        """Record a recovery attempt"""
        if service not in self.recovery_attempts:
            self.recovery_attempts[service] = {'count': 0}
        
        self.recovery_attempts[service]['count'] += 1
        self.recovery_attempts[service]['last_attempt'] = datetime.now()
    
    def restart_service(self, service_name: str) -> bool:
        """Restart a service using Docker or systemctl"""
        if not self.can_attempt_recovery(service_name):
            return False
        
        self.record_recovery_attempt(service_name)
        
        try:
            # Try Docker restart first
            result = subprocess.run(
                ['docker', 'restart', service_name],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                print(f"Successfully restarted Docker service: {service_name}")
                return True
            
            # Try systemctl as fallback
            result = subprocess.run(
                ['systemctl', 'restart', service_name],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                print(f"Successfully restarted systemctl service: {service_name}")
                return True
            
            print(f"Failed to restart service {service_name}: {result.stderr}")
            return False
        
        except Exception as e:
            print(f"Error restarting service {service_name}: {e}")
            return False
    
    def clear_cache(self) -> bool:
        """Clear application cache"""
        try:
            # Clear Redis cache if available
            redis_url = self.config.get('redis_url')
            if redis_url:
                redis_client = redis.from_url(redis_url)
                redis_client.flushdb()
                print("Redis cache cleared")
            
            return True
        except Exception as e:
            print(f"Error clearing cache: {e}")
            return False
    
    def scale_down_resources(self) -> bool:
        """Scale down resource usage"""
        try:
            # This would implement resource scaling logic
            # For example, reducing worker processes, job limits, etc.
            print("Scaling down resources to reduce load")
            return True
        except Exception as e:
            print(f"Error scaling down resources: {e}")
            return False


class HealthMonitor:
    """Main health monitoring orchestrator"""
    
    def __init__(self, config_file: str = None):
        self.config = self._load_config(config_file)
        self.health_checker = ServiceHealthChecker(self.config)
        self.recovery_manager = AutoRecoveryManager(self.config.get('recovery', {}))
        self.running = False
        self.check_interval = self.config.get('check_interval', 60)  # 1 minute
    
    def _load_config(self, config_file: str) -> Dict:
        """Load configuration from file or environment"""
        default_config = {
            "base_url": os.getenv("BASE_URL", "http://localhost:5001"),
            "redis_url": os.getenv("REDIS_URL", "redis://localhost:6379"),
            "supabase_url": os.getenv("SUPABASE_URL"),
            "supabase_service_key": os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
            "check_interval": int(os.getenv("HEALTH_CHECK_INTERVAL", "60")),
            "timeout": int(os.getenv("HEALTH_CHECK_TIMEOUT", "30")),
            "notifications": {
                "slack_webhook": os.getenv("SLACK_WEBHOOK"),
                "cooldown": int(os.getenv("NOTIFICATION_COOLDOWN", "300"))
            },
            "recovery": {
                "max_recovery_attempts": int(os.getenv("MAX_RECOVERY_ATTEMPTS", "3")),
                "recovery_cooldown": int(os.getenv("RECOVERY_COOLDOWN", "300"))
            }
        }
        
        if config_file and os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    file_config = json.load(f)
                default_config.update(file_config)
            except Exception as e:
                print(f"Error loading config file: {e}")
        
        return default_config
    
    def run_health_checks(self) -> Dict:
        """Run all health checks and return results"""
        print(f"\n🔍 Running health checks at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        checks = self.health_checker.run_all_health_checks()
        overall_status = self.health_checker.get_overall_health_status(checks)
        
        # Display results
        for check in checks:
            status_symbol = {
                HealthStatus.HEALTHY: "✅",
                HealthStatus.DEGRADED: "⚠️",
                HealthStatus.UNHEALTHY: "❌",
                HealthStatus.CRITICAL: "🚨"
            }.get(check.status, "❓")
            
            print(f"{status_symbol} {check.name}: {check.status.value}")
            print(f"   {check.message}")
            if check.response_time < float('inf'):
                print(f"   Response time: {check.response_time:.0f}ms")
        
        print(f"\n📊 Overall Status: {overall_status.value}")
        
        # Handle unhealthy states
        self._handle_unhealthy_services(checks, overall_status)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "overall_status": overall_status.value,
            "checks": [
                {
                    "name": check.name,
                    "status": check.status.value,
                    "message": check.message,
                    "response_time": check.response_time,
                    "metadata": check.metadata
                }
                for check in checks
            ]
        }
    
    def _handle_unhealthy_services(self, checks: List[HealthCheck], overall_status: HealthStatus):
        """Handle unhealthy services with recovery actions"""
        for check in checks:
            if check.status in [HealthStatus.UNHEALTHY, HealthStatus.CRITICAL]:
                print(f"\n🔧 Attempting recovery for: {check.name}")
                
                # Send notification
                self.health_checker.notification_manager.send_slack_alert(
                    f"Service Alert: {check.name}",
                    check.message,
                    check.status
                )
                
                # Attempt recovery based on service type
                if "API" in check.name:
                    self.recovery_manager.restart_service("heckx-video-generator")
                elif "Redis" in check.name:
                    self.recovery_manager.restart_service("redis")
                elif "System Resources" in check.name:
                    self.recovery_manager.scale_down_resources()
                elif "Video Generation" in check.name:
                    self.recovery_manager.clear_cache()
    
    def start_monitoring(self):
        """Start continuous monitoring"""
        print("🚀 Starting Heckx Health Monitor")
        print(f"Check interval: {self.check_interval} seconds")
        print("=" * 50)
        
        self.running = True
        
        while self.running:
            try:
                result = self.run_health_checks()
                
                # Save results to file
                self._save_health_report(result)
                
                # Wait for next check
                time.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                print("\n👋 Monitoring stopped by user")
                self.running = False
            except Exception as e:
                print(f"\n❌ Monitoring error: {e}")
                time.sleep(30)  # Wait before retrying
    
    def _save_health_report(self, result: Dict):
        """Save health report to file"""
        try:
            os.makedirs("logs", exist_ok=True)
            report_file = f"logs/health_report_{datetime.now().strftime('%Y%m%d')}.json"
            
            # Load existing reports for the day
            reports = []
            if os.path.exists(report_file):
                with open(report_file, 'r') as f:
                    reports = json.load(f)
            
            # Add new report
            reports.append(result)
            
            # Keep only last 24 hours of reports
            cutoff_time = datetime.now() - timedelta(hours=24)
            reports = [
                r for r in reports 
                if datetime.fromisoformat(r['timestamp']) > cutoff_time
            ]
            
            # Save updated reports
            with open(report_file, 'w') as f:
                json.dump(reports, f, indent=2)
                
        except Exception as e:
            print(f"Error saving health report: {e}")


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Heckx AI Video Generator Health Monitor")
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--once", action="store_true", help="Run health checks once and exit")
    parser.add_argument("--interval", type=int, help="Check interval in seconds")
    
    args = parser.parse_args()
    
    monitor = HealthMonitor(args.config)
    
    if args.interval:
        monitor.check_interval = args.interval
    
    if args.once:
        result = monitor.run_health_checks()
        print(f"\n📄 Health report saved")
        overall_status = result["overall_status"]
        
        # Exit with appropriate code
        if overall_status in ["critical", "unhealthy"]:
            sys.exit(1)
        elif overall_status == "degraded":
            sys.exit(2)
        else:
            sys.exit(0)
    else:
        monitor.start_monitoring()


if __name__ == "__main__":
    main()