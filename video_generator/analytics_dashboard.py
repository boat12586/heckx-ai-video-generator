# video_generator/analytics_dashboard.py - Analytics and reporting dashboard
import os
import json
import sqlite3
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import tempfile

class AnalyticsMetric(Enum):
    VIDEO_GENERATION_COUNT = "video_generation_count"
    PROCESSING_TIME = "processing_time"
    SUCCESS_RATE = "success_rate"
    USER_ENGAGEMENT = "user_engagement"
    CONTENT_POPULARITY = "content_popularity"
    RESOURCE_USAGE = "resource_usage"
    ERROR_FREQUENCY = "error_frequency"
    PEAK_USAGE_TIMES = "peak_usage_times"

class TimeRange(Enum):
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"

@dataclass
class AnalyticsEvent:
    timestamp: datetime
    event_type: str
    user_id: Optional[str]
    project_id: Optional[str]
    video_type: Optional[str]
    duration: Optional[float]
    success: bool
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data

@dataclass
class MetricData:
    metric: AnalyticsMetric
    value: float
    timestamp: datetime
    time_range: TimeRange
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class AnalyticsReport:
    title: str
    description: str
    generated_at: datetime
    time_range: TimeRange
    metrics: List[MetricData]
    insights: List[str]
    recommendations: List[str]

class AnalyticsDashboard:
    """Comprehensive analytics and reporting system"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or os.path.join(tempfile.gettempdir(), "heckx_analytics.db")
        self.init_database()
        
        # Performance tracking
        self.session_start = datetime.now()
        self.session_metrics = {
            'videos_generated': 0,
            'total_processing_time': 0,
            'errors_encountered': 0,
            'peak_memory_usage': 0
        }
        
        print("✅ Analytics Dashboard initialized")
    
    def init_database(self):
        """Initialize analytics database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Events table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS analytics_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        event_type TEXT NOT NULL,
                        user_id TEXT,
                        project_id TEXT,
                        video_type TEXT,
                        duration REAL,
                        success BOOLEAN NOT NULL,
                        metadata TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Metrics table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        metric_type TEXT NOT NULL,
                        value REAL NOT NULL,
                        timestamp TEXT NOT NULL,
                        time_range TEXT NOT NULL,
                        metadata TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Performance logs
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS performance_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        operation TEXT NOT NULL,
                        duration REAL NOT NULL,
                        memory_usage REAL,
                        cpu_usage REAL,
                        success BOOLEAN NOT NULL,
                        error_message TEXT,
                        metadata TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # User sessions
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT UNIQUE NOT NULL,
                        user_id TEXT,
                        start_time TEXT NOT NULL,
                        end_time TEXT,
                        videos_generated INTEGER DEFAULT 0,
                        total_time_spent REAL DEFAULT 0,
                        actions_performed TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create indexes for better performance
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_timestamp ON analytics_events(timestamp)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_type ON analytics_events(event_type)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_metrics_type ON metrics(metric_type)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_performance_operation ON performance_logs(operation)')
                
                conn.commit()
                print("✅ Analytics database initialized")
                
        except Exception as e:
            print(f"❌ Failed to initialize analytics database: {e}")
    
    def log_event(self, event: AnalyticsEvent):
        """Log analytics event"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO analytics_events 
                    (timestamp, event_type, user_id, project_id, video_type, duration, success, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    event.timestamp.isoformat(),
                    event.event_type,
                    event.user_id,
                    event.project_id,
                    event.video_type,
                    event.duration,
                    event.success,
                    json.dumps(event.metadata)
                ))
                
                conn.commit()
                
        except Exception as e:
            print(f"Failed to log analytics event: {e}")
    
    def log_performance(self, operation: str, duration: float, 
                       memory_usage: float = None, cpu_usage: float = None,
                       success: bool = True, error_message: str = None,
                       metadata: Dict = None):
        """Log performance metrics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO performance_logs 
                    (timestamp, operation, duration, memory_usage, cpu_usage, success, error_message, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    datetime.now().isoformat(),
                    operation,
                    duration,
                    memory_usage,
                    cpu_usage,
                    success,
                    error_message,
                    json.dumps(metadata or {})
                ))
                
                conn.commit()
                
        except Exception as e:
            print(f"Failed to log performance: {e}")
    
    def track_video_generation(self, project_id: str, video_type: str, 
                              duration: float, success: bool,
                              processing_time: float, user_id: str = None):
        """Track video generation event"""
        
        # Log main event
        event = AnalyticsEvent(
            timestamp=datetime.now(),
            event_type="video_generation",
            user_id=user_id,
            project_id=project_id,
            video_type=video_type,
            duration=duration,
            success=success,
            metadata={
                'processing_time': processing_time,
                'video_duration': duration
            }
        )
        
        self.log_event(event)
        
        # Log performance
        self.log_performance(
            operation=f"generate_{video_type}_video",
            duration=processing_time,
            success=success,
            metadata={
                'project_id': project_id,
                'video_duration': duration
            }
        )
        
        # Update session metrics
        self.session_metrics['videos_generated'] += 1
        self.session_metrics['total_processing_time'] += processing_time
        if not success:
            self.session_metrics['errors_encountered'] += 1
    
    def get_generation_statistics(self, time_range: TimeRange = TimeRange.DAY,
                                 days_back: int = 30) -> Dict:
        """Get video generation statistics"""
        try:
            end_time = datetime.now()
            if time_range == TimeRange.HOUR:
                start_time = end_time - timedelta(hours=days_back)
            elif time_range == TimeRange.DAY:
                start_time = end_time - timedelta(days=days_back)
            elif time_range == TimeRange.WEEK:
                start_time = end_time - timedelta(weeks=days_back)
            elif time_range == TimeRange.MONTH:
                start_time = end_time - timedelta(days=days_back * 30)
            else:
                start_time = end_time - timedelta(days=days_back)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Total videos generated
                cursor.execute('''
                    SELECT COUNT(*) FROM analytics_events 
                    WHERE event_type = 'video_generation' 
                    AND timestamp >= ? AND timestamp <= ?
                ''', (start_time.isoformat(), end_time.isoformat()))
                
                total_videos = cursor.fetchone()[0]
                
                # Success rate
                cursor.execute('''
                    SELECT COUNT(*) FROM analytics_events 
                    WHERE event_type = 'video_generation' 
                    AND success = 1
                    AND timestamp >= ? AND timestamp <= ?
                ''', (start_time.isoformat(), end_time.isoformat()))
                
                successful_videos = cursor.fetchone()[0]
                
                success_rate = (successful_videos / max(total_videos, 1)) * 100
                
                # Average processing time
                cursor.execute('''
                    SELECT AVG(CAST(json_extract(metadata, '$.processing_time') AS REAL))
                    FROM analytics_events 
                    WHERE event_type = 'video_generation' 
                    AND success = 1
                    AND timestamp >= ? AND timestamp <= ?
                ''', (start_time.isoformat(), end_time.isoformat()))
                
                avg_processing_time = cursor.fetchone()[0] or 0
                
                # Videos by type
                cursor.execute('''
                    SELECT video_type, COUNT(*) 
                    FROM analytics_events 
                    WHERE event_type = 'video_generation'
                    AND timestamp >= ? AND timestamp <= ?
                    GROUP BY video_type
                ''', (start_time.isoformat(), end_time.isoformat()))
                
                videos_by_type = dict(cursor.fetchall())
                
                # Daily breakdown
                cursor.execute('''
                    SELECT DATE(timestamp) as date, COUNT(*) as count
                    FROM analytics_events 
                    WHERE event_type = 'video_generation'
                    AND timestamp >= ? AND timestamp <= ?
                    GROUP BY DATE(timestamp)
                    ORDER BY date
                ''', (start_time.isoformat(), end_time.isoformat()))
                
                daily_breakdown = dict(cursor.fetchall())
                
                return {
                    'total_videos': total_videos,
                    'successful_videos': successful_videos,
                    'failed_videos': total_videos - successful_videos,
                    'success_rate': round(success_rate, 2),
                    'average_processing_time': round(avg_processing_time, 2),
                    'videos_by_type': videos_by_type,
                    'daily_breakdown': daily_breakdown,
                    'time_range': time_range.value,
                    'period': f"{start_time.date()} to {end_time.date()}"
                }
                
        except Exception as e:
            print(f"Failed to get generation statistics: {e}")
            return {}
    
    def get_performance_metrics(self, operation: str = None, 
                               time_range: TimeRange = TimeRange.DAY,
                               days_back: int = 7) -> Dict:
        """Get performance metrics"""
        try:
            end_time = datetime.now()
            if time_range == TimeRange.HOUR:
                start_time = end_time - timedelta(hours=days_back)
            elif time_range == TimeRange.DAY:
                start_time = end_time - timedelta(days=days_back)
            else:
                start_time = end_time - timedelta(days=days_back)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Build query conditions
                where_conditions = [
                    "timestamp >= ?", 
                    "timestamp <= ?"
                ]
                params = [start_time.isoformat(), end_time.isoformat()]
                
                if operation:
                    where_conditions.append("operation = ?")
                    params.append(operation)
                
                where_clause = " AND ".join(where_conditions)
                
                # Average duration
                cursor.execute(f'''
                    SELECT AVG(duration) FROM performance_logs 
                    WHERE {where_clause} AND success = 1
                ''', params)
                
                avg_duration = cursor.fetchone()[0] or 0
                
                # Success rate
                cursor.execute(f'''
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful
                    FROM performance_logs 
                    WHERE {where_clause}
                ''', params)
                
                total, successful = cursor.fetchone()
                success_rate = (successful / max(total, 1)) * 100
                
                # Performance by operation
                cursor.execute(f'''
                    SELECT operation, AVG(duration), COUNT(*)
                    FROM performance_logs 
                    WHERE {where_clause}
                    GROUP BY operation
                    ORDER BY AVG(duration) DESC
                ''', params)
                
                operations_performance = [
                    {
                        'operation': op,
                        'avg_duration': round(avg_dur, 2),
                        'count': count
                    }
                    for op, avg_dur, count in cursor.fetchall()
                ]
                
                # Error analysis
                cursor.execute(f'''
                    SELECT error_message, COUNT(*) 
                    FROM performance_logs 
                    WHERE {where_clause} AND success = 0 AND error_message IS NOT NULL
                    GROUP BY error_message
                    ORDER BY COUNT(*) DESC
                    LIMIT 10
                ''', params)
                
                common_errors = [
                    {
                        'error': error,
                        'count': count
                    }
                    for error, count in cursor.fetchall()
                ]
                
                return {
                    'average_duration': round(avg_duration, 2),
                    'success_rate': round(success_rate, 2),
                    'total_operations': total,
                    'successful_operations': successful,
                    'failed_operations': total - successful,
                    'operations_performance': operations_performance,
                    'common_errors': common_errors,
                    'time_range': time_range.value,
                    'operation_filter': operation
                }
                
        except Exception as e:
            print(f"Failed to get performance metrics: {e}")
            return {}
    
    def get_usage_patterns(self, time_range: TimeRange = TimeRange.DAY,
                          days_back: int = 30) -> Dict:
        """Analyze usage patterns"""
        try:
            end_time = datetime.now()
            if time_range == TimeRange.HOUR:
                start_time = end_time - timedelta(hours=days_back)
                group_format = "%H"
                group_label = "hour"
            elif time_range == TimeRange.DAY:
                start_time = end_time - timedelta(days=days_back)
                group_format = "%w"  # Day of week
                group_label = "day_of_week"
            else:
                start_time = end_time - timedelta(days=days_back)
                group_format = "%Y-%m-%d"
                group_label = "date"
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Peak usage times
                cursor.execute(f'''
                    SELECT strftime('{group_format}', timestamp) as time_group, COUNT(*) as count
                    FROM analytics_events 
                    WHERE timestamp >= ? AND timestamp <= ?
                    GROUP BY time_group
                    ORDER BY count DESC
                ''', (start_time.isoformat(), end_time.isoformat()))
                
                usage_by_time = dict(cursor.fetchall())
                
                # Content type preferences
                cursor.execute('''
                    SELECT video_type, COUNT(*) as count
                    FROM analytics_events 
                    WHERE event_type = 'video_generation'
                    AND timestamp >= ? AND timestamp <= ?
                    GROUP BY video_type
                    ORDER BY count DESC
                ''', (start_time.isoformat(), end_time.isoformat()))
                
                content_preferences = dict(cursor.fetchall())
                
                # User engagement (if user_id is tracked)
                cursor.execute('''
                    SELECT 
                        COUNT(DISTINCT user_id) as unique_users,
                        COUNT(*) as total_interactions,
                        AVG(CASE WHEN video_type IS NOT NULL THEN duration ELSE NULL END) as avg_video_duration
                    FROM analytics_events 
                    WHERE timestamp >= ? AND timestamp <= ?
                    AND user_id IS NOT NULL
                ''', (start_time.isoformat(), end_time.isoformat()))
                
                engagement_data = cursor.fetchone()
                unique_users, total_interactions, avg_video_duration = engagement_data
                
                return {
                    'usage_by_time': usage_by_time,
                    'content_preferences': content_preferences,
                    'unique_users': unique_users or 0,
                    'total_interactions': total_interactions,
                    'average_video_duration': round(avg_video_duration or 0, 2),
                    'interactions_per_user': round(total_interactions / max(unique_users or 1, 1), 2),
                    'time_grouping': group_label,
                    'analysis_period': f"{start_time.date()} to {end_time.date()}"
                }
                
        except Exception as e:
            print(f"Failed to analyze usage patterns: {e}")
            return {}
    
    def generate_insights(self, stats: Dict) -> List[str]:
        """Generate insights from analytics data"""
        insights = []
        
        try:
            # Generation insights
            if 'success_rate' in stats:
                success_rate = stats['success_rate']
                if success_rate >= 95:
                    insights.append("✅ Excellent success rate - system is performing very well")
                elif success_rate >= 85:
                    insights.append("🟡 Good success rate - minor optimizations may help")
                else:
                    insights.append("🔴 Low success rate - investigation needed")
            
            # Performance insights
            if 'average_processing_time' in stats:
                avg_time = stats['average_processing_time']
                if avg_time <= 60:
                    insights.append("⚡ Fast processing times - users likely satisfied")
                elif avg_time <= 120:
                    insights.append("🕐 Moderate processing times - acceptable performance")
                else:
                    insights.append("🐌 Slow processing times - optimization recommended")
            
            # Usage pattern insights
            if 'content_preferences' in stats:
                prefs = stats['content_preferences']
                if prefs:
                    most_popular = max(prefs.items(), key=lambda x: x[1])
                    insights.append(f"📊 Most popular content type: {most_popular[0]} ({most_popular[1]} videos)")
            
            # User engagement insights
            if 'interactions_per_user' in stats:
                ipu = stats['interactions_per_user']
                if ipu >= 10:
                    insights.append("💪 High user engagement - users are actively using the system")
                elif ipu >= 5:
                    insights.append("👍 Moderate user engagement - room for improvement")
                else:
                    insights.append("📈 Low user engagement - consider UX improvements")
            
        except Exception as e:
            insights.append(f"⚠️  Error generating insights: {e}")
        
        return insights
    
    def generate_recommendations(self, stats: Dict, insights: List[str]) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        try:
            # Performance recommendations
            if 'average_processing_time' in stats:
                avg_time = stats['average_processing_time']
                if avg_time > 120:
                    recommendations.append("🔧 Consider optimizing video processing pipeline")
                    recommendations.append("💾 Review resource allocation and scaling options")
            
            # Quality recommendations
            if 'success_rate' in stats:
                success_rate = stats['success_rate']
                if success_rate < 90:
                    recommendations.append("🛠️  Investigate and fix common failure points")
                    recommendations.append("📋 Implement better error handling and retry logic")
            
            # Usage recommendations
            if 'content_preferences' in stats:
                prefs = stats['content_preferences']
                if len(prefs) > 1:
                    least_popular = min(prefs.items(), key=lambda x: x[1])
                    recommendations.append(f"🎯 Consider improving {least_popular[0]} content features")
            
            # Infrastructure recommendations
            if 'operations_performance' in stats:
                ops = stats['operations_performance']
                if ops:
                    slowest_op = ops[0]  # First item is slowest
                    if slowest_op['avg_duration'] > 60:
                        recommendations.append(f"⚡ Optimize '{slowest_op['operation']}' operation performance")
            
            # General recommendations
            recommendations.append("📊 Continue monitoring metrics for trends")
            recommendations.append("🔄 Regular performance reviews and optimizations")
            
        except Exception as e:
            recommendations.append(f"⚠️  Error generating recommendations: {e}")
        
        return recommendations
    
    def generate_comprehensive_report(self, time_range: TimeRange = TimeRange.WEEK,
                                    days_back: int = 7) -> AnalyticsReport:
        """Generate comprehensive analytics report"""
        
        # Gather all statistics
        generation_stats = self.get_generation_statistics(time_range, days_back)
        performance_stats = self.get_performance_metrics(None, time_range, days_back)
        usage_patterns = self.get_usage_patterns(time_range, days_back)
        
        # Combine stats
        combined_stats = {**generation_stats, **performance_stats, **usage_patterns}
        
        # Generate insights and recommendations
        insights = self.generate_insights(combined_stats)
        recommendations = self.generate_recommendations(combined_stats, insights)
        
        # Create metrics
        metrics = []
        
        if 'total_videos' in combined_stats:
            metrics.append(MetricData(
                metric=AnalyticsMetric.VIDEO_GENERATION_COUNT,
                value=combined_stats['total_videos'],
                timestamp=datetime.now(),
                time_range=time_range
            ))
        
        if 'success_rate' in combined_stats:
            metrics.append(MetricData(
                metric=AnalyticsMetric.SUCCESS_RATE,
                value=combined_stats['success_rate'],
                timestamp=datetime.now(),
                time_range=time_range
            ))
        
        if 'average_processing_time' in combined_stats:
            metrics.append(MetricData(
                metric=AnalyticsMetric.PROCESSING_TIME,
                value=combined_stats['average_processing_time'],
                timestamp=datetime.now(),
                time_range=time_range
            ))
        
        # Create report
        report = AnalyticsReport(
            title=f"Video Generator Analytics Report - {time_range.value.title()}",
            description=f"Comprehensive analytics for the past {days_back} {time_range.value}(s)",
            generated_at=datetime.now(),
            time_range=time_range,
            metrics=metrics,
            insights=insights,
            recommendations=recommendations
        )
        
        return report
    
    def export_report_to_json(self, report: AnalyticsReport, file_path: str = None) -> str:
        """Export analytics report to JSON file"""
        if not file_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = os.path.join(tempfile.gettempdir(), f"analytics_report_{timestamp}.json")
        
        try:
            report_data = {
                'title': report.title,
                'description': report.description,
                'generated_at': report.generated_at.isoformat(),
                'time_range': report.time_range.value,
                'metrics': [
                    {
                        'metric': metric.metric.value,
                        'value': metric.value,
                        'timestamp': metric.timestamp.isoformat(),
                        'time_range': metric.time_range.value,
                        'metadata': metric.metadata
                    }
                    for metric in report.metrics
                ],
                'insights': report.insights,
                'recommendations': report.recommendations
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Analytics report exported to: {file_path}")
            return file_path
            
        except Exception as e:
            print(f"Failed to export report: {e}")
            return None
    
    def get_real_time_metrics(self) -> Dict:
        """Get real-time system metrics"""
        current_time = datetime.now()
        uptime = (current_time - self.session_start).total_seconds()
        
        return {
            'session_uptime_hours': round(uptime / 3600, 2),
            'videos_generated_this_session': self.session_metrics['videos_generated'],
            'total_processing_time_this_session': round(self.session_metrics['total_processing_time'], 2),
            'errors_this_session': self.session_metrics['errors_encountered'],
            'average_time_per_video': round(
                self.session_metrics['total_processing_time'] / max(self.session_metrics['videos_generated'], 1), 2
            ),
            'videos_per_hour': round(
                self.session_metrics['videos_generated'] / max(uptime / 3600, 0.01), 2
            ),
            'current_timestamp': current_time.isoformat()
        }
    
    def cleanup_old_data(self, days_to_keep: int = 90) -> Dict:
        """Clean up old analytics data"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Clean old events
                cursor.execute('''
                    DELETE FROM analytics_events 
                    WHERE timestamp < ?
                ''', (cutoff_date.isoformat(),))
                events_deleted = cursor.rowcount
                
                # Clean old metrics
                cursor.execute('''
                    DELETE FROM metrics 
                    WHERE timestamp < ?
                ''', (cutoff_date.isoformat(),))
                metrics_deleted = cursor.rowcount
                
                # Clean old performance logs
                cursor.execute('''
                    DELETE FROM performance_logs 
                    WHERE timestamp < ?
                ''', (cutoff_date.isoformat(),))
                logs_deleted = cursor.rowcount
                
                conn.commit()
                
                return {
                    'events_deleted': events_deleted,
                    'metrics_deleted': metrics_deleted,
                    'logs_deleted': logs_deleted,
                    'cutoff_date': cutoff_date.isoformat()
                }
                
        except Exception as e:
            print(f"Failed to cleanup old data: {e}")
            return {}

# Test function
def test_analytics_dashboard():
    """Test analytics dashboard capabilities"""
    print("📊 Testing Analytics Dashboard...")
    
    try:
        dashboard = AnalyticsDashboard()
        
        print("✅ Analytics Dashboard initialized")
        
        # Test event logging
        event = AnalyticsEvent(
            timestamp=datetime.now(),
            event_type="test_event",
            user_id="test_user",
            project_id="test_project",
            video_type="motivation",
            duration=60.0,
            success=True,
            metadata={'test': True}
        )
        
        dashboard.log_event(event)
        print("✅ Event logging test completed")
        
        # Test statistics
        stats = dashboard.get_generation_statistics()
        print(f"Generation statistics: {len(stats)} metrics")
        
        # Test real-time metrics
        real_time = dashboard.get_real_time_metrics()
        print(f"Real-time metrics: {real_time}")
        
        print("✅ Analytics Dashboard tests completed")
        
    except Exception as e:
        print(f"❌ Analytics Dashboard test failed: {e}")

if __name__ == "__main__":
    test_analytics_dashboard()