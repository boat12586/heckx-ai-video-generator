# video_generator/web_interface.py - Web interface for video generator
from flask import Flask, render_template_string, request, jsonify, redirect, url_for
from flask_cors import CORS
import os
import json
from datetime import datetime

from .main_service import VideoGeneratorService

# HTML Templates
MAIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Heckx AI Video Generator</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            text-align: center;
            color: white;
            margin-bottom: 40px;
        }
        
        .header h1 {
            font-size: 3rem;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .header p {
            font-size: 1.2rem;
            opacity: 0.9;
        }
        
        .card {
            background: white;
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }
        
        .card:hover {
            transform: translateY(-5px);
        }
        
        .card-title {
            font-size: 1.8rem;
            margin-bottom: 20px;
            color: #4a5568;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #2d3748;
        }
        
        .form-group input,
        .form-group select,
        .form-group textarea {
            width: 100%;
            padding: 12px;
            border: 2px solid #e2e8f0;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.3s ease;
        }
        
        .form-group input:focus,
        .form-group select:focus,
        .form-group textarea:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .form-group textarea {
            resize: vertical;
            min-height: 100px;
        }
        
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            text-decoration: none;
            display: inline-block;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }
        
        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        .btn-secondary {
            background: #718096;
        }
        
        .progress {
            width: 100%;
            height: 20px;
            background: #e2e8f0;
            border-radius: 10px;
            overflow: hidden;
            margin: 20px 0;
        }
        
        .progress-bar {
            height: 100%;
            background: linear-gradient(90deg, #48bb78, #38a169);
            transition: width 0.3s ease;
            border-radius: 10px;
        }
        
        .status {
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
        }
        
        .status.success {
            background: #f0fff4;
            border: 1px solid #68d391;
            color: #22543d;
        }
        
        .status.error {
            background: #fed7d7;
            border: 1px solid #fc8181;
            color: #742a2a;
        }
        
        .status.info {
            background: #ebf8ff;
            border: 1px solid #63b3ed;
            color: #2a4365;
        }
        
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 30px;
        }
        
        .project-item {
            background: #f7fafc;
            padding: 20px;
            border-radius: 10px;
            border-left: 4px solid #667eea;
        }
        
        .project-item h3 {
            margin-bottom: 10px;
            color: #2d3748;
        }
        
        .project-item p {
            margin: 5px 0;
            color: #4a5568;
        }
        
        .project-status {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
        }
        
        .status-completed {
            background: #c6f6d5;
            color: #22543d;
        }
        
        .status-failed {
            background: #fed7d7;
            color: #742a2a;
        }
        
        .status-running {
            background: #bee3f8;
            color: #2a4365;
        }
        
        .download-links {
            margin-top: 15px;
        }
        
        .download-links a {
            display: inline-block;
            padding: 8px 16px;
            background: #4299e1;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            margin-right: 10px;
            margin-top: 5px;
            font-size: 14px;
        }
        
        .download-links a:hover {
            background: #3182ce;
        }
        
        .nav-tabs {
            display: flex;
            margin-bottom: 30px;
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .nav-tab {
            flex: 1;
            padding: 15px 20px;
            background: #f7fafc;
            border: none;
            cursor: pointer;
            font-size: 16px;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        
        .nav-tab.active {
            background: #667eea;
            color: white;
        }
        
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
        }
        
        @media (max-width: 768px) {
            .container {
                padding: 10px;
            }
            
            .header h1 {
                font-size: 2rem;
            }
            
            .grid {
                grid-template-columns: 1fr;
            }
            
            .nav-tabs {
                flex-direction: column;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎬 Heckx AI Video Generator</h1>
            <p>สร้างวิดีโอ Motivation และ Lofi Music ด้วย AI</p>
        </div>
        
        <div class="nav-tabs">
            <button class="nav-tab active" onclick="showTab('motivation')">🔥 Motivation Videos</button>
            <button class="nav-tab" onclick="showTab('lofi')">🎵 Lofi Videos</button>
            <button class="nav-tab" onclick="showTab('projects')">📋 Projects</button>
            <button class="nav-tab" onclick="showTab('stats')">📊 Statistics</button>
        </div>
        
        <!-- Motivation Video Tab -->
        <div id="motivation" class="tab-content active">
            <div class="card">
                <h2 class="card-title">🔥 สร้าง Motivation Video</h2>
                <form id="motivationForm">
                    <div class="form-group">
                        <label for="theme">หัวข้อ Stoic Philosophy:</label>
                        <select id="theme" name="theme">
                            <option value="">สุ่มหัวข้อ</option>
                            <option value="inner_strength">ความแข็งแกร่งจากภายใน</option>
                            <option value="acceptance">การยอมรับในสิ่งที่ควบคุมไม่ได้</option>
                            <option value="purpose">การใช้ชีวิตอย่างมีจุดหมาย</option>
                            <option value="resilience">การเผชิญหน้ากับความทุกข์</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label for="duration">ความยาววิดีโอ (วินาที):</label>
                        <input type="number" id="duration" name="duration" value="60" min="30" max="300">
                    </div>
                    
                    <div class="form-group">
                        <label for="customScript">บทพูดกำหนดเอง (ถ้าต้องการ):</label>
                        <textarea id="customScript" name="customScript" placeholder="ใส่บทพูดที่ต้องการ หรือปล่อยว่างเพื่อให้ AI สร้างให้"></textarea>
                    </div>
                    
                    <button type="submit" class="btn">🚀 สร้างวิดีโอ</button>
                </form>
                
                <div id="motivationStatus"></div>
                <div id="motivationProgress"></div>
            </div>
        </div>
        
        <!-- Lofi Video Tab -->
        <div id="lofi" class="tab-content">
            <div class="card">
                <h2 class="card-title">🎵 สร้าง Lofi Video</h2>
                <form id="lofiForm">
                    <div class="form-group">
                        <label for="category">ประเภทเพลง:</label>
                        <select id="category" name="category">
                            <option value="">สุ่มประเภท</option>
                            <option value="เงียบสงบ">เงียบสงบ</option>
                            <option value="แจ๊สสมูท">แจ๊สสมูท</option>
                            <option value="อะคูสติก">อะคูสติก</option>
                            <option value="เปียโน">เปียโน</option>
                            <option value="กีต้าร์โปร่ง">กีต้าร์โปร่ง</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label for="lofiDuration">ความยาววิดีโอ (วินาที):</label>
                        <input type="number" id="lofiDuration" name="duration" value="120" min="60" max="600">
                    </div>
                    
                    <button type="submit" class="btn">🎶 สร้างวิดีโอ Lofi</button>
                </form>
                
                <div id="lofiStatus"></div>
                <div id="lofiProgress"></div>
            </div>
        </div>
        
        <!-- Projects Tab -->
        <div id="projects" class="tab-content">
            <div class="card">
                <h2 class="card-title">📋 โปรเจกต์ทั้งหมด</h2>
                <button onclick="loadProjects()" class="btn btn-secondary">🔄 โหลดใหม่</button>
                <div id="projectsList"></div>
            </div>
        </div>
        
        <!-- Statistics Tab -->
        <div id="stats" class="tab-content">
            <div class="card">
                <h2 class="card-title">📊 สถิติระบบ</h2>
                <button onclick="loadStats()" class="btn btn-secondary">🔄 โหลดสถิติ</button>
                <div id="statsContent"></div>
            </div>
        </div>
    </div>
    
    <script>
        // Tab switching
        function showTab(tabName) {
            // Hide all tabs
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // Remove active class from all nav tabs
            document.querySelectorAll('.nav-tab').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // Show selected tab
            document.getElementById(tabName).classList.add('active');
            
            // Add active class to clicked nav tab
            event.target.classList.add('active');
            
            // Load data for specific tabs
            if (tabName === 'projects') {
                loadProjects();
            } else if (tabName === 'stats') {
                loadStats();
            }
        }
        
        // Generate motivation video
        document.getElementById('motivationForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(e.target);
            const data = {
                theme: formData.get('theme') || null,
                duration: parseInt(formData.get('duration')),
                custom_script: formData.get('customScript') || null,
                async: true
            };
            
            const statusDiv = document.getElementById('motivationStatus');
            const progressDiv = document.getElementById('motivationProgress');
            
            try {
                statusDiv.innerHTML = '<div class="status info">⏳ กำลังเริ่มสร้างวิดีโอ...</div>';
                
                const response = await fetch('/api/generate/motivation', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    statusDiv.innerHTML = '<div class="status success">✅ เริ่มสร้างวิดีโอแล้ว</div>';
                    
                    // Monitor task progress
                    monitorTask(result.task_id, progressDiv, statusDiv);
                } else {
                    statusDiv.innerHTML = `<div class="status error">❌ เกิดข้อผิดพลาด: ${result.error}</div>`;
                }
            } catch (error) {
                statusDiv.innerHTML = `<div class="status error">❌ เกิดข้อผิดพลาด: ${error.message}</div>`;
            }
        });
        
        // Generate lofi video
        document.getElementById('lofiForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(e.target);
            const data = {
                category: formData.get('category') || null,
                duration: parseInt(formData.get('duration')),
                async: true
            };
            
            const statusDiv = document.getElementById('lofiStatus');
            const progressDiv = document.getElementById('lofiProgress');
            
            try {
                statusDiv.innerHTML = '<div class="status info">⏳ กำลังเริ่มสร้างวิดีโอ Lofi...</div>';
                
                const response = await fetch('/api/generate/lofi', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    statusDiv.innerHTML = '<div class="status success">✅ เริ่มสร้างวิดีโอ Lofi แล้ว</div>';
                    
                    // Monitor task progress
                    monitorTask(result.task_id, progressDiv, statusDiv);
                } else {
                    statusDiv.innerHTML = `<div class="status error">❌ เกิดข้อผิดพลาด: ${result.error}</div>`;
                }
            } catch (error) {
                statusDiv.innerHTML = `<div class="status error">❌ เกิดข้อผิดพลาด: ${error.message}</div>`;
            }
        });
        
        // Monitor task progress
        async function monitorTask(taskId, progressDiv, statusDiv) {
            const checkInterval = setInterval(async () => {
                try {
                    const response = await fetch(`/api/task/${taskId}`);
                    const task = await response.json();
                    
                    if (task.status === 'running') {
                        if (task.project_status) {
                            const progress = task.project_status.progress || 0;
                            progressDiv.innerHTML = `
                                <div class="progress">
                                    <div class="progress-bar" style="width: ${progress}%"></div>
                                </div>
                                <p>สถานะ: ${task.project_status.status} (${progress}%)</p>
                            `;
                        }
                    } else if (task.status === 'completed') {
                        clearInterval(checkInterval);
                        
                        const result = task.result;
                        progressDiv.innerHTML = `
                            <div class="progress">
                                <div class="progress-bar" style="width: 100%"></div>
                            </div>
                        `;
                        
                        statusDiv.innerHTML = `
                            <div class="status success">
                                ✅ สร้างวิดีโอเสร็จแล้ว!
                                <div class="download-links">
                                    <a href="/api/download/${result.project_id}/video" target="_blank">📥 ดาวน์โหลดวิดีโอ</a>
                                    ${result.voiceover_url ? `<a href="/api/download/${result.project_id}/voiceover" target="_blank">🎤 ดาวน์โหลดเสียงพากย์</a>` : ''}
                                </div>
                            </div>
                        `;
                    } else if (task.status === 'failed') {
                        clearInterval(checkInterval);
                        statusDiv.innerHTML = `<div class="status error">❌ สร้างวิดีโอไม่สำเร็จ: ${task.error}</div>`;
                        progressDiv.innerHTML = '';
                    }
                } catch (error) {
                    console.error('Error monitoring task:', error);
                }
            }, 2000); // Check every 2 seconds
        }
        
        // Load projects
        async function loadProjects() {
            const projectsList = document.getElementById('projectsList');
            
            try {
                projectsList.innerHTML = '<p>⏳ กำลังโหลดโปรเจกต์...</p>';
                
                const response = await fetch('/api/projects');
                const data = await response.json();
                
                if (data.projects.length === 0) {
                    projectsList.innerHTML = '<p>ยังไม่มีโปรเจกต์</p>';
                    return;
                }
                
                const projectsHtml = data.projects.map(project => `
                    <div class="project-item">
                        <h3>${project.type === 'motivation' ? '🔥 Motivation' : '🎵 Lofi'} - ${project.project_id.slice(0, 8)}</h3>
                        <p><strong>สถานะ:</strong> <span class="project-status status-${project.status}">${project.status}</span></p>
                        <p><strong>ความคืบหน้า:</strong> ${project.progress}%</p>
                        <p><strong>สร้างเมื่อ:</strong> ${new Date(project.created_at).toLocaleString('th-TH')}</p>
                        ${project.completed_at ? `<p><strong>เสร็จเมื่อ:</strong> ${new Date(project.completed_at).toLocaleString('th-TH')}</p>` : ''}
                        
                        ${project.status === 'completed' ? `
                            <div class="download-links">
                                <a href="/api/download/${project.project_id}/video" target="_blank">📥 ดาวน์โหลดวิดีโอ</a>
                                ${project.type === 'motivation' ? `<a href="/api/download/${project.project_id}/voiceover" target="_blank">🎤 เสียงพากย์</a>` : ''}
                            </div>
                        ` : ''}
                    </div>
                `).join('');
                
                projectsList.innerHTML = `<div class="grid">${projectsHtml}</div>`;
                
            } catch (error) {
                projectsList.innerHTML = `<p>❌ เกิดข้อผิดพลาดในการโหลดโปรเจกต์: ${error.message}</p>`;
            }
        }
        
        // Load statistics
        async function loadStats() {
            const statsContent = document.getElementById('statsContent');
            
            try {
                statsContent.innerHTML = '<p>⏳ กำลังโหลดสถิติ...</p>';
                
                const response = await fetch('/api/stats');
                const stats = await response.json();
                
                const statsHtml = `
                    <div class="grid">
                        <div class="project-item">
                            <h3>🎬 สถานะระบบ</h3>
                            <p><strong>Video Generator:</strong> ${stats.video_generator ? '✅ พร้อมใช้งาน' : '❌ ไม่พร้อม'}</p>
                            <p><strong>Stoic Content:</strong> ${stats.stoic_content ? '✅ พร้อมใช้งาน' : '❌ ไม่พร้อม'}</p>
                            <p><strong>Pixabay:</strong> ${stats.pixabay ? '✅ พร้อมใช้งาน' : '❌ ไม่พร้อม'}</p>
                            <p><strong>Storage:</strong> ${stats.storage ? '✅ พร้อมใช้งาน' : '❌ ไม่พร้อม'}</p>
                        </div>
                        
                        ${stats.statistics ? `
                            <div class="project-item">
                                <h3>📊 สถิติโปรเจกต์</h3>
                                <p><strong>โปรเจกต์ทั้งหมด:</strong> ${stats.statistics.total_projects || 0}</p>
                                <p><strong>Motivation Videos:</strong> ${stats.statistics.motivation_videos || 0}</p>
                                <p><strong>Lofi Videos:</strong> ${stats.statistics.lofi_videos || 0}</p>
                                <p><strong>สำเร็จแล้ว:</strong> ${stats.statistics.completed_projects || 0}</p>
                                <p><strong>ล้มเหลว:</strong> ${stats.statistics.failed_projects || 0}</p>
                            </div>
                        ` : ''}
                    </div>
                `;
                
                statsContent.innerHTML = statsHtml;
                
            } catch (error) {
                statsContent.innerHTML = `<p>❌ เกิดข้อผิดพลาดในการโหลดสถิติ: ${error.message}</p>`;
            }
        }
        
        // Load projects on page load
        document.addEventListener('DOMContentLoaded', function() {
            // Auto-load stats when page loads
            setTimeout(loadStats, 1000);
        });
    </script>
</body>
</html>
"""

# Initialize Flask app for web interface
web_app = Flask(__name__)
CORS(web_app)

# Initialize video generator service
video_service = VideoGeneratorService()

@web_app.route('/')
def index():
    """Main web interface"""
    return render_template_string(MAIN_TEMPLATE)

@web_app.route('/api/health', methods=['GET'])
def web_health_check():
    """Health check for web interface"""
    try:
        status = video_service.get_service_status()
        return jsonify({
            'status': 'healthy',
            'services': status,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

# Import API routes from api.py
from .api import (
    generate_motivation_video, generate_lofi_video, get_task_status,
    get_project_status, get_project_history, get_download_info,
    download_video_file, download_voiceover_file, get_stoic_themes,
    get_lofi_categories, get_service_stats, cleanup_old_projects
)

# Register API routes with web app
web_app.add_url_rule('/api/generate/motivation', 'generate_motivation_video', generate_motivation_video, methods=['POST'])
web_app.add_url_rule('/api/generate/lofi', 'generate_lofi_video', generate_lofi_video, methods=['POST'])
web_app.add_url_rule('/api/task/<task_id>', 'get_task_status', get_task_status, methods=['GET'])
web_app.add_url_rule('/api/project/<project_id>', 'get_project_status', get_project_status, methods=['GET'])
web_app.add_url_rule('/api/projects', 'get_project_history', get_project_history, methods=['GET'])
web_app.add_url_rule('/api/download/<project_id>', 'get_download_info', get_download_info, methods=['GET'])
web_app.add_url_rule('/api/download/<project_id>/video', 'download_video_file', download_video_file, methods=['GET'])
web_app.add_url_rule('/api/download/<project_id>/voiceover', 'download_voiceover_file', download_voiceover_file, methods=['GET'])
web_app.add_url_rule('/api/themes', 'get_stoic_themes', get_stoic_themes, methods=['GET'])
web_app.add_url_rule('/api/lofi/categories', 'get_lofi_categories', get_lofi_categories, methods=['GET'])
web_app.add_url_rule('/api/stats', 'get_service_stats', get_service_stats, methods=['GET'])
web_app.add_url_rule('/api/cleanup', 'cleanup_old_projects', cleanup_old_projects, methods=['POST'])

def run_web_interface(host='0.0.0.0', port=5002, debug=False):
    """Run the web interface server"""
    print(f"🌐 Starting Video Generator Web Interface on {host}:{port}")
    print(f"🔗 Open in browser: http://{host}:{port}")
    
    web_app.run(host=host, port=port, debug=debug, threaded=True)

if __name__ == "__main__":
    run_web_interface(debug=True)