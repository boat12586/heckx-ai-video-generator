# video_generator/api.py - REST API endpoints for video generator
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import threading
from typing import Dict, Any

from .main_service import VideoGeneratorService

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for web interface

# Initialize video generator service
video_service = VideoGeneratorService()

# Store background tasks
background_tasks = {}

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        status = video_service.get_service_status()
        return jsonify({
            'status': 'healthy',
            'services': status,
            'timestamp': '2024-01-01T00:00:00Z'
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': '2024-01-01T00:00:00Z'
        }), 500

@app.route('/api/generate/motivation', methods=['POST'])
def generate_motivation_video():
    """Generate motivation video endpoint"""
    try:
        data = request.get_json() or {}
        
        # Extract parameters
        theme = data.get('theme')
        duration = data.get('duration', 60)
        custom_script = data.get('custom_script')
        async_mode = data.get('async', True)
        
        # Validate duration
        if not 30 <= duration <= 300:
            return jsonify({
                'error': 'Duration must be between 30 and 300 seconds'
            }), 400
        
        if async_mode:
            # Start background task
            task_id = f"motivation_{len(background_tasks) + 1}"
            
            def generate_async():
                try:
                    result = video_service.generate_motivation_video(
                        theme=theme,
                        duration=duration,
                        custom_script=custom_script
                    )
                    background_tasks[task_id] = {
                        'status': 'completed',
                        'result': result
                    }
                except Exception as e:
                    background_tasks[task_id] = {
                        'status': 'failed',
                        'error': str(e)
                    }
            
            # Store initial task status
            background_tasks[task_id] = {
                'status': 'running',
                'project_id': None
            }
            
            # Start background thread
            thread = threading.Thread(target=generate_async)
            thread.start()
            
            return jsonify({
                'task_id': task_id,
                'status': 'started',
                'message': 'Video generation started in background'
            })
        else:
            # Synchronous generation
            result = video_service.generate_motivation_video(
                theme=theme,
                duration=duration,
                custom_script=custom_script
            )
            
            return jsonify({
                'success': True,
                'result': result
            })
            
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

@app.route('/api/generate/lofi', methods=['POST'])
def generate_lofi_video():
    """Generate lofi video endpoint"""
    try:
        data = request.get_json() or {}
        
        # Extract parameters
        category = data.get('category')
        duration = data.get('duration', 120)
        async_mode = data.get('async', True)
        
        # Validate duration
        if not 60 <= duration <= 600:
            return jsonify({
                'error': 'Duration must be between 60 and 600 seconds'
            }), 400
        
        if async_mode:
            # Start background task
            task_id = f"lofi_{len(background_tasks) + 1}"
            
            def generate_async():
                try:
                    result = video_service.generate_lofi_video(
                        category=category,
                        duration=duration
                    )
                    background_tasks[task_id] = {
                        'status': 'completed',
                        'result': result
                    }
                except Exception as e:
                    background_tasks[task_id] = {
                        'status': 'failed',
                        'error': str(e)
                    }
            
            # Store initial task status
            background_tasks[task_id] = {
                'status': 'running',
                'project_id': None
            }
            
            # Start background thread
            thread = threading.Thread(target=generate_async)
            thread.start()
            
            return jsonify({
                'task_id': task_id,
                'status': 'started',
                'message': 'Lofi video generation started in background'
            })
        else:
            # Synchronous generation
            result = video_service.generate_lofi_video(
                category=category,
                duration=duration
            )
            
            return jsonify({
                'success': True,
                'result': result
            })
            
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

@app.route('/api/task/<task_id>', methods=['GET'])
def get_task_status(task_id: str):
    """Get background task status"""
    task = background_tasks.get(task_id)
    
    if not task:
        return jsonify({
            'error': 'Task not found'
        }), 404
    
    # If task has project_id, get current status from database
    if task.get('project_id') and task['status'] == 'running':
        project_status = video_service.get_project_status(task['project_id'])
        if project_status:
            task['project_status'] = project_status
    
    return jsonify(task)

@app.route('/api/project/<project_id>', methods=['GET'])
def get_project_status(project_id: str):
    """Get project status"""
    status = video_service.get_project_status(project_id)
    
    if not status:
        return jsonify({
            'error': 'Project not found'
        }), 404
    
    return jsonify(status)

@app.route('/api/projects', methods=['GET'])
def get_project_history():
    """Get project history"""
    limit = request.args.get('limit', 20, type=int)
    projects = video_service.get_project_history(limit)
    
    return jsonify({
        'projects': projects,
        'total': len(projects)
    })

@app.route('/api/download/<project_id>', methods=['GET'])
def get_download_info(project_id: str):
    """Get download information for a project"""
    download_package = video_service.get_download_package(project_id)
    
    if not download_package:
        return jsonify({
            'error': 'Download not available'
        }), 404
    
    return jsonify(download_package)

@app.route('/api/download/<project_id>/video', methods=['GET'])
def download_video_file(project_id: str):
    """Download video file directly"""
    try:
        if not video_service.storage_service:
            return jsonify({
                'error': 'Storage service not available'
            }), 503
        
        project = video_service.storage_service.get_project(project_id)
        if not project:
            return jsonify({
                'error': 'Project not found'
            }), 404
        
        video_url = project.metadata.get('video_url')
        if not video_url:
            return jsonify({
                'error': 'Video file not available'
            }), 404
        
        # For direct download, redirect to the storage URL
        from flask import redirect
        return redirect(video_url)
        
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

@app.route('/api/download/<project_id>/voiceover', methods=['GET'])
def download_voiceover_file(project_id: str):
    """Download voiceover file directly"""
    try:
        if not video_service.storage_service:
            return jsonify({
                'error': 'Storage service not available'
            }), 503
        
        project = video_service.storage_service.get_project(project_id)
        if not project:
            return jsonify({
                'error': 'Project not found'
            }), 404
        
        voiceover_url = project.metadata.get('voiceover_url')
        if not voiceover_url:
            return jsonify({
                'error': 'Voiceover file not available'
            }), 404
        
        # For direct download, redirect to the storage URL
        from flask import redirect
        return redirect(voiceover_url)
        
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

@app.route('/api/themes', methods=['GET'])
def get_stoic_themes():
    """Get available Stoic themes"""
    themes = video_service.stoic_generator.get_available_themes()
    
    theme_info = {}
    for theme in themes:
        theme_info[theme] = video_service.stoic_generator.get_theme_info(theme)
    
    return jsonify({
        'themes': themes,
        'theme_info': theme_info
    })

@app.route('/api/lofi/categories', methods=['GET'])
def get_lofi_categories():
    """Get available lofi music categories"""
    # Extract categories from lofi library
    categories = []
    for track_data in video_service.lofi_library.lofi_tracks:
        category = track_data['category']
        if category not in categories:
            categories.append(category)
    
    return jsonify({
        'categories': categories
    })

@app.route('/api/stats', methods=['GET'])
def get_service_stats():
    """Get service statistics"""
    stats = video_service.get_service_status()
    return jsonify(stats)

@app.route('/api/cleanup', methods=['POST'])
def cleanup_old_projects():
    """Clean up old projects and files"""
    try:
        data = request.get_json() or {}
        days_old = data.get('days_old', 30)
        
        if days_old < 1:
            return jsonify({
                'error': 'days_old must be at least 1'
            }), 400
        
        results = video_service.cleanup_old_projects(days_old)
        
        return jsonify({
            'success': True,
            'cleanup_results': results
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'error': 'Endpoint not found',
        'available_endpoints': [
            '/api/health',
            '/api/generate/motivation',
            '/api/generate/lofi',
            '/api/task/<task_id>',
            '/api/project/<project_id>',
            '/api/projects',
            '/api/download/<project_id>',
            '/api/themes',
            '/api/lofi/categories',
            '/api/stats'
        ]
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({
        'error': 'Internal server error',
        'message': 'An unexpected error occurred'
    }), 500

def run_api_server(host='0.0.0.0', port=5001, debug=False):
    """Run the API server"""
    print(f"🚀 Starting Video Generator API server on {host}:{port}")
    print(f"🔗 API Documentation: http://{host}:{port}/api/health")
    
    # Print available endpoints
    print("\n📋 Available API Endpoints:")
    print("  GET  /api/health - Service health check")
    print("  POST /api/generate/motivation - Generate motivation video")
    print("  POST /api/generate/lofi - Generate lofi video")
    print("  GET  /api/task/<task_id> - Get background task status")
    print("  GET  /api/project/<project_id> - Get project status")
    print("  GET  /api/projects - Get project history")
    print("  GET  /api/download/<project_id> - Get download info")
    print("  GET  /api/download/<project_id>/video - Download video file")
    print("  GET  /api/download/<project_id>/voiceover - Download voiceover")
    print("  GET  /api/themes - Get Stoic themes")
    print("  GET  /api/lofi/categories - Get lofi categories")
    print("  GET  /api/stats - Get service statistics")
    print("  POST /api/cleanup - Clean up old projects")
    print()
    
    app.run(host=host, port=port, debug=debug, threaded=True)

if __name__ == "__main__":
    run_api_server(debug=True)