#!/usr/bin/env python3
"""
Simple Flask app for Frappe LMS on Railway
This is a minimal implementation to get started quickly
"""

import os
import json
from flask import Flask, render_template_string, jsonify, request
import psycopg2
from urllib.parse import urlparse

app = Flask(__name__)

# Database connection
def get_db_connection():
    """Get PostgreSQL database connection"""
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        url = urlparse(database_url)
        return psycopg2.connect(
            database=url.path[1:],
            user=url.username,
            password=url.password,
            host=url.hostname,
            port=url.port,
        )
    return None

# Initialize database
def init_db():
    """Initialize basic database schema"""
    try:
        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            cur.execute('''
                CREATE TABLE IF NOT EXISTS courses (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS lessons (
                    id SERIAL PRIMARY KEY,
                    course_id INTEGER REFERENCES courses(id),
                    title VARCHAR(255) NOT NULL,
                    content TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
            cur.close()
            conn.close()
            return True
    except Exception as e:
        print(f"Database initialization error: {e}")
    return False

# Routes
@app.route('/')
def home():
    """Home page"""
    template = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Frappe LMS - Railway Demo</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                margin: 0;
                padding: 20px;
                background: #f8f9fa;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
                background: white;
                padding: 40px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            h1 {
                color: #2c3e50;
                text-align: center;
                margin-bottom: 30px;
            }
            .status {
                padding: 15px;
                border-radius: 5px;
                margin: 20px 0;
            }
            .success { background: #d4edda; border: 1px solid #c3e6cb; color: #155724; }
            .error { background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; }
            .info { background: #d1ecf1; border: 1px solid #bee5eb; color: #0c5460; }
            .btn {
                background: #007bff;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                text-decoration: none;
                display: inline-block;
                margin: 5px;
            }
            .feature {
                background: #f8f9fa;
                padding: 15px;
                margin: 10px 0;
                border-radius: 5px;
                border-left: 4px solid #007bff;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎓 Frappe LMS</h1>
            <h2>Railway Deployment - Demo Version</h2>
            
            <div class="status success">
                <strong>✅ Application is running successfully!</strong><br>
                Your Frappe LMS is deployed and accessible on Railway.
            </div>
            
            <div class="info">
                <strong>ℹ️ Demo Version:</strong><br>
                This is a simplified demo version of Frappe LMS running on Railway. 
                The full Frappe framework with all features will be available in the next update.
            </div>
            
            <h3>🚀 Features Available:</h3>
            <div class="feature">
                <strong>Database Connection:</strong> {{ db_status }}
            </div>
            <div class="feature">
                <strong>Environment:</strong> Railway Platform
            </div>
            <div class="feature">
                <strong>Domain:</strong> {{ domain }}
            </div>
            <div class="feature">
                <strong>Port:</strong> {{ port }}
            </div>
            
            <h3>🛠️ API Endpoints:</h3>
            <p>
                <a href="/health" class="btn">Health Check</a>
                <a href="/api/courses" class="btn">Courses API</a>
                <a href="/lms" class="btn">LMS Interface</a>
            </p>
            
            <div class="info">
                <strong>📝 Next Steps:</strong><br>
                1. The database is ready for course content<br>
                2. You can extend this app with more Frappe LMS features<br>
                3. Add authentication, course management, and student enrollment
            </div>
        </div>
    </body>
    </html>
    '''
    
    # Get status information
    db_status = "✅ Connected" if get_db_connection() else "❌ Not Connected"
    domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN', 'localhost')
    port = os.environ.get('PORT', '3000')
    
    return render_template_string(template, 
                                db_status=db_status,
                                domain=domain,
                                port=port)

@app.route('/lms')
def lms_interface():
    """LMS main interface"""
    template = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>LMS - Learning Management System</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .header { background: #2c3e50; color: white; padding: 20px; border-radius: 5px; }
            .course { background: #ecf0f1; padding: 15px; margin: 10px 0; border-radius: 5px; }
            .btn { background: #3498db; color: white; padding: 8px 16px; border: none; border-radius: 3px; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🎓 Learning Management System</h1>
            <p>Welcome to your LMS platform</p>
        </div>
        
        <h2>Available Courses</h2>
        <div class="course">
            <h3>📚 Demo Course: Introduction to Railway</h3>
            <p>Learn how to deploy applications on Railway platform</p>
            <button class="btn">Enroll Now</button>
        </div>
        
        <div class="course">
            <h3>🚀 Demo Course: Frappe Framework</h3>
            <p>Master the Frappe framework for rapid application development</p>
            <button class="btn">Enroll Now</button>
        </div>
        
        <p><a href="/">← Back to Home</a></p>
    </body>
    </html>
    '''
    return render_template_string(template)

@app.route('/health')
def health_check():
    """Health check endpoint for Railway"""
    db_status = get_db_connection() is not None
    return jsonify({
        'status': 'healthy',
        'database': 'connected' if db_status else 'disconnected',
        'port': os.environ.get('PORT', '3000'),
        'domain': os.environ.get('RAILWAY_PUBLIC_DOMAIN', 'localhost')
    })

@app.route('/api/courses')
def api_courses():
    """API endpoint for courses"""
    try:
        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            cur.execute('SELECT id, title, description FROM courses ORDER BY created_at DESC')
            courses = []
            for row in cur.fetchall():
                courses.append({
                    'id': row[0],
                    'title': row[1],
                    'description': row[2]
                })
            cur.close()
            conn.close()
            return jsonify({'courses': courses})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    return jsonify({'courses': []})

@app.route('/api/courses', methods=['POST'])
def create_course():
    """Create a new course"""
    try:
        data = request.json
        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            cur.execute(
                'INSERT INTO courses (title, description) VALUES (%s, %s) RETURNING id',
                (data.get('title'), data.get('description'))
            )
            course_id = cur.fetchone()[0]
            conn.commit()
            cur.close()
            conn.close()
            return jsonify({'id': course_id, 'status': 'created'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'Failed to create course'}), 500

# Initialize the database on startup
if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port, debug=False)