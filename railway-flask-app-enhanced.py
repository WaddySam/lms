#!/usr/bin/env python3
"""
Enhanced Flask LMS with Advanced Features
- User Authentication
- Course Enrollment
- Progress Tracking
- Quizzes and Assignments
- Certificates
"""

import os
import json
import hashlib
from datetime import datetime, timedelta
from flask import Flask, render_template_string, jsonify, request, session, redirect, url_for
import psycopg2
from urllib.parse import urlparse

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-this')

# Database connection (same as before)
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

# Enhanced database schema
def init_db():
    """Initialize comprehensive LMS database schema"""
    try:
        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            
            # Users table
            cur.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    first_name VARCHAR(100),
                    last_name VARCHAR(100),
                    role VARCHAR(20) DEFAULT 'student',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Courses table (enhanced)
            cur.execute('''
                CREATE TABLE IF NOT EXISTS courses (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    description TEXT,
                    instructor_id INTEGER REFERENCES users(id),
                    duration_weeks INTEGER DEFAULT 4,
                    difficulty_level VARCHAR(20) DEFAULT 'beginner',
                    price DECIMAL(10,2) DEFAULT 0.00,
                    is_published BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Lessons table (enhanced)
            cur.execute('''
                CREATE TABLE IF NOT EXISTS lessons (
                    id SERIAL PRIMARY KEY,
                    course_id INTEGER REFERENCES courses(id),
                    title VARCHAR(255) NOT NULL,
                    content TEXT,
                    video_url VARCHAR(500),
                    lesson_order INTEGER DEFAULT 1,
                    duration_minutes INTEGER DEFAULT 30,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Enrollments table
            cur.execute('''
                CREATE TABLE IF NOT EXISTS enrollments (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id),
                    course_id INTEGER REFERENCES courses(id),
                    enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP NULL,
                    progress_percentage DECIMAL(5,2) DEFAULT 0.00,
                    UNIQUE(user_id, course_id)
                )
            ''')
            
            # Lesson progress table
            cur.execute('''
                CREATE TABLE IF NOT EXISTS lesson_progress (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id),
                    lesson_id INTEGER REFERENCES lessons(id),
                    completed_at TIMESTAMP NULL,
                    time_spent_minutes INTEGER DEFAULT 0,
                    UNIQUE(user_id, lesson_id)
                )
            ''')
            
            # Quizzes table
            cur.execute('''
                CREATE TABLE IF NOT EXISTS quizzes (
                    id SERIAL PRIMARY KEY,
                    lesson_id INTEGER REFERENCES lessons(id),
                    title VARCHAR(255) NOT NULL,
                    description TEXT,
                    passing_score INTEGER DEFAULT 70,
                    time_limit_minutes INTEGER DEFAULT 30,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Quiz questions table
            cur.execute('''
                CREATE TABLE IF NOT EXISTS quiz_questions (
                    id SERIAL PRIMARY KEY,
                    quiz_id INTEGER REFERENCES quizzes(id),
                    question_text TEXT NOT NULL,
                    question_type VARCHAR(20) DEFAULT 'multiple_choice',
                    options JSON,
                    correct_answer TEXT,
                    points INTEGER DEFAULT 1,
                    question_order INTEGER DEFAULT 1
                )
            ''')
            
            # Quiz attempts table
            cur.execute('''
                CREATE TABLE IF NOT EXISTS quiz_attempts (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id),
                    quiz_id INTEGER REFERENCES quizzes(id),
                    score INTEGER DEFAULT 0,
                    max_score INTEGER DEFAULT 0,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP NULL,
                    passed BOOLEAN DEFAULT FALSE
                )
            ''')
            
            # Certificates table
            cur.execute('''
                CREATE TABLE IF NOT EXISTS certificates (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id),
                    course_id INTEGER REFERENCES courses(id),
                    certificate_code VARCHAR(50) UNIQUE,
                    issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, course_id)
                )
            ''')
            
            conn.commit()
            cur.close()
            conn.close()
            
            # Create sample data
            create_sample_data()
            return True
    except Exception as e:
        print(f"Database initialization error: {e}")
    return False

def create_sample_data():
    """Create sample instructors, courses, and content"""
    try:
        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            
            # Check if sample data already exists
            cur.execute('SELECT COUNT(*) FROM users')
            if cur.fetchone()[0] > 0:
                return  # Sample data already exists
            
            # Create sample instructor
            password_hash = hashlib.sha256('instructor123'.encode()).hexdigest()
            cur.execute('''
                INSERT INTO users (username, email, password_hash, first_name, last_name, role)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            ''', ('instructor', 'instructor@example.com', password_hash, 'John', 'Doe', 'instructor'))
            instructor_id = cur.fetchone()[0]
            
            # Create sample student
            student_password = hashlib.sha256('student123'.encode()).hexdigest()
            cur.execute('''
                INSERT INTO users (username, email, password_hash, first_name, last_name, role)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            ''', ('student', 'student@example.com', student_password, 'Jane', 'Smith', 'student'))
            student_id = cur.fetchone()[0]
            
            # Create sample courses
            courses_data = [
                ('Python for Beginners', 'Learn Python programming from scratch', instructor_id, 6, 'beginner', 49.99),
                ('Web Development with Flask', 'Build web applications using Flask framework', instructor_id, 8, 'intermediate', 79.99),
                ('Data Science Fundamentals', 'Introduction to data analysis and visualization', instructor_id, 10, 'intermediate', 99.99),
            ]
            
            course_ids = []
            for course_data in courses_data:
                cur.execute('''
                    INSERT INTO courses (title, description, instructor_id, duration_weeks, difficulty_level, price, is_published)
                    VALUES (%s, %s, %s, %s, %s, %s, TRUE)
                    RETURNING id
                ''', course_data)
                course_ids.append(cur.fetchone()[0])
            
            # Create sample lessons for first course
            python_lessons = [
                ('Introduction to Python', 'What is Python and why use it?', 'https://example.com/video1', 1, 45),
                ('Variables and Data Types', 'Understanding basic data types in Python', 'https://example.com/video2', 2, 60),
                ('Control Structures', 'If statements, loops, and functions', 'https://example.com/video3', 3, 75),
                ('Working with Lists', 'Python lists and common operations', 'https://example.com/video4', 4, 50),
            ]
            
            lesson_ids = []
            for lesson_data in python_lessons:
                cur.execute('''
                    INSERT INTO lessons (course_id, title, content, video_url, lesson_order, duration_minutes)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                ''', (course_ids[0],) + lesson_data)
                lesson_ids.append(cur.fetchone()[0])
            
            # Create sample quiz for first lesson
            cur.execute('''
                INSERT INTO quizzes (lesson_id, title, description, passing_score, time_limit_minutes)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            ''', (lesson_ids[0], 'Python Basics Quiz', 'Test your understanding of Python basics', 70, 15))
            quiz_id = cur.fetchone()[0]
            
            # Add quiz questions
            quiz_questions = [
                ('What is Python?', 'multiple_choice', 
                 json.dumps(['A compiled language', 'An interpreted language', 'A markup language', 'A database']), 
                 'An interpreted language', 2, 1),
                ('Which keyword is used to define a function in Python?', 'multiple_choice',
                 json.dumps(['func', 'def', 'function', 'define']),
                 'def', 2, 2),
                ('What is the output of print(2 + 3)?', 'multiple_choice',
                 json.dumps(['23', '5', 'Error', 'None']),
                 '5', 2, 3),
            ]
            
            for question_data in quiz_questions:
                cur.execute('''
                    INSERT INTO quiz_questions (quiz_id, question_text, question_type, options, correct_answer, points, question_order)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                ''', (quiz_id,) + question_data)
            
            # Enroll sample student in first course
            cur.execute('''
                INSERT INTO enrollments (user_id, course_id, progress_percentage)
                VALUES (%s, %s, %s)
            ''', (student_id, course_ids[0], 25.0))
            
            conn.commit()
            cur.close()
            conn.close()
            print("Sample data created successfully!")
            
    except Exception as e:
        print(f"Error creating sample data: {e}")

# Authentication helpers
def hash_password(password):
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hash):
    """Verify password against hash"""
    return hashlib.sha256(password.encode()).hexdigest() == hash

# Enhanced Routes

@app.route('/')
def home():
    """Enhanced home page with user context"""
    user_info = ""
    if 'user_id' in session:
        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            cur.execute('SELECT first_name, last_name, role FROM users WHERE id = %s', (session['user_id'],))
            user = cur.fetchone()
            if user:
                user_info = f"Welcome back, {user[0]} {user[1]} ({user[2]})"
            cur.close()
            conn.close()
    
    template = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Advanced LMS - Railway Demo</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                margin: 0;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }
            .container {
                max-width: 1000px;
                margin: 0 auto;
                background: white;
                padding: 40px;
                border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            }
            .header {
                text-align: center;
                margin-bottom: 40px;
            }
            h1 {
                color: #2c3e50;
                font-size: 2.5em;
                margin-bottom: 10px;
            }
            .user-info {
                background: #e8f5e8;
                padding: 10px;
                border-radius: 8px;
                margin: 20px 0;
                border-left: 4px solid #27ae60;
            }
            .status {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin: 30px 0;
            }
            .status-card {
                background: #f8f9fa;
                padding: 20px;
                border-radius: 10px;
                border-left: 4px solid #3498db;
            }
            .btn {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 12px 24px;
                border: none;
                border-radius: 8px;
                text-decoration: none;
                display: inline-block;
                margin: 8px;
                transition: transform 0.2s;
            }
            .btn:hover { transform: translateY(-2px); }
            .btn-secondary {
                background: #6c757d;
            }
            .features {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin: 30px 0;
            }
            .feature-card {
                background: #f8f9fa;
                padding: 20px;
                border-radius: 10px;
                text-align: center;
            }
            .feature-icon {
                font-size: 3em;
                margin-bottom: 15px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎓 Advanced Learning Management System</h1>
                <p>Professional LMS with Full Feature Set</p>
                {% if user_info %}
                <div class="user-info">{{ user_info }}</div>
                {% endif %}
            </div>
            
            <div class="status">
                <div class="status-card">
                    <h3>🗄️ Database</h3>
                    <p>{{ db_status }}</p>
                </div>
                <div class="status-card">
                    <h3>🌐 Environment</h3>
                    <p>Railway Platform<br>Domain: {{ domain }}</p>
                </div>
                <div class="status-card">
                    <h3>👥 Sample Users</h3>
                    <p>Instructor: instructor/instructor123<br>Student: student/student123</p>
                </div>
            </div>
            
            <div class="features">
                <div class="feature-card">
                    <div class="feature-icon">📚</div>
                    <h3>Course Management</h3>
                    <p>Create and manage courses with lessons, quizzes, and multimedia content</p>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">👨‍🎓</div>
                    <h3>Student Progress</h3>
                    <p>Track learning progress, completion rates, and performance analytics</p>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">🏆</div>
                    <h3>Certificates</h3>
                    <p>Automated certificate generation upon course completion</p>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">📊</div>
                    <h3>Analytics</h3>
                    <p>Detailed reports on student performance and course effectiveness</p>
                </div>
            </div>
            
            <div style="text-align: center; margin: 40px 0;">
                {% if not user_info %}
                <a href="/login" class="btn">Login</a>
                <a href="/register" class="btn btn-secondary">Register</a>
                {% else %}
                <a href="/dashboard" class="btn">My Dashboard</a>
                <a href="/logout" class="btn btn-secondary">Logout</a>
                {% endif %}
                <a href="/lms" class="btn">Browse Courses</a>
                <a href="/api/courses" class="btn btn-secondary">API Documentation</a>
            </div>
        </div>
    </body>
    </html>
    '''
    
    db_status = "✅ Connected" if get_db_connection() else "❌ Not Connected"
    domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN', 'localhost')
    
    return render_template_string(template, 
                                db_status=db_status,
                                domain=domain,
                                user_info=user_info)

# Authentication Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login page"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            cur.execute('SELECT id, password_hash, first_name, last_name, role FROM users WHERE username = %s', (username,))
            user = cur.fetchone()
            cur.close()
            conn.close()
            
            if user and verify_password(password, user[1]):
                session['user_id'] = user[0]
                session['username'] = username
                session['role'] = user[4]
                return redirect(url_for('dashboard'))
            else:
                return render_template_string(login_template, error="Invalid username or password")
    
    return render_template_string(login_template)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration page"""
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        
        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            try:
                password_hash = hash_password(password)
                cur.execute('''
                    INSERT INTO users (username, email, password_hash, first_name, last_name)
                    VALUES (%s, %s, %s, %s, %s)
                ''', (username, email, password_hash, first_name, last_name))
                conn.commit()
                cur.close()
                conn.close()
                return redirect(url_for('login'))
            except psycopg2.IntegrityError:
                conn.rollback()
                cur.close()
                conn.close()
                return render_template_string(register_template, error="Username or email already exists")
    
    return render_template_string(register_template)

@app.route('/logout')
def logout():
    """User logout"""
    session.clear()
    return redirect(url_for('home'))

@app.route('/dashboard')
def dashboard():
    """User dashboard with personalized content"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    if not conn:
        return "Database connection error", 500
    
    cur = conn.cursor()
    user_id = session['user_id']
    role = session.get('role', 'student')
    
    # Get user info
    cur.execute('SELECT first_name, last_name, email FROM users WHERE id = %s', (user_id,))
    user_info = cur.fetchone()
    
    if role == 'instructor':
        # Get instructor's courses
        cur.execute('''
            SELECT c.id, c.title, c.description, COUNT(e.id) as enrollment_count
            FROM courses c
            LEFT JOIN enrollments e ON c.id = e.course_id
            WHERE c.instructor_id = %s
            GROUP BY c.id, c.title, c.description
            ORDER BY c.created_at DESC
        ''', (user_id,))
        courses = cur.fetchall()
        
        # Get recent enrollments
        cur.execute('''
            SELECT u.first_name, u.last_name, c.title, e.enrolled_at
            FROM enrollments e
            JOIN users u ON e.user_id = u.id
            JOIN courses c ON e.course_id = c.id
            WHERE c.instructor_id = %s
            ORDER BY e.enrolled_at DESC
            LIMIT 10
        ''', (user_id,))
        recent_enrollments = cur.fetchall()
        
        template_data = {
            'user_info': user_info,
            'role': role,
            'courses': courses,
            'recent_enrollments': recent_enrollments
        }
    else:
        # Get student's enrollments and progress
        cur.execute('''
            SELECT c.id, c.title, c.description, e.progress_percentage, e.enrolled_at, e.completed_at
            FROM enrollments e
            JOIN courses c ON e.course_id = c.id
            WHERE e.user_id = %s
            ORDER BY e.enrolled_at DESC
        ''', (user_id,))
        enrollments = cur.fetchall()
        
        # Get available courses (not enrolled)
        cur.execute('''
            SELECT c.id, c.title, c.description, c.price, u.first_name, u.last_name
            FROM courses c
            JOIN users u ON c.instructor_id = u.id
            WHERE c.is_published = TRUE
            AND c.id NOT IN (
                SELECT course_id FROM enrollments WHERE user_id = %s
            )
            ORDER BY c.created_at DESC
            LIMIT 6
        ''', (user_id,))
        available_courses = cur.fetchall()
        
        template_data = {
            'user_info': user_info,
            'role': role,
            'enrollments': enrollments,
            'available_courses': available_courses
        }
    
    cur.close()
    conn.close()
    
    return render_template_string(dashboard_template, **template_data)

@app.route('/course/<int:course_id>')
def course_detail(course_id):
    """Course detail page with lessons and progress"""
    conn = get_db_connection()
    if not conn:
        return "Database connection error", 500
    
    cur = conn.cursor()
    
    # Get course details
    cur.execute('''
        SELECT c.id, c.title, c.description, c.duration_weeks, c.difficulty_level, c.price,
               u.first_name, u.last_name
        FROM courses c
        JOIN users u ON c.instructor_id = u.id
        WHERE c.id = %s
    ''', (course_id,))
    course = cur.fetchone()
    
    if not course:
        return "Course not found", 404
    
    # Get lessons
    cur.execute('''
        SELECT id, title, content, video_url, lesson_order, duration_minutes
        FROM lessons
        WHERE course_id = %s
        ORDER BY lesson_order
    ''', (course_id,))
    lessons = cur.fetchall()
    
    # Check if user is enrolled (if logged in)
    enrollment = None
    lesson_progress = {}
    if 'user_id' in session:
        cur.execute('''
            SELECT progress_percentage, enrolled_at, completed_at
            FROM enrollments
            WHERE user_id = %s AND course_id = %s
        ''', (session['user_id'], course_id))
        enrollment = cur.fetchone()
        
        if enrollment:
            # Get lesson progress
            cur.execute('''
                SELECT lesson_id, completed_at
                FROM lesson_progress
                WHERE user_id = %s AND lesson_id IN (
                    SELECT id FROM lessons WHERE course_id = %s
                )
            ''', (session['user_id'], course_id))
            lesson_progress = dict(cur.fetchall())
    
    cur.close()
    conn.close()
    
    return render_template_string(course_detail_template, 
                                course=course, 
                                lessons=lessons, 
                                enrollment=enrollment,
                                lesson_progress=lesson_progress)

@app.route('/enroll/<int:course_id>', methods=['POST'])
def enroll_course(course_id):
    """Enroll user in a course"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    if conn:
        cur = conn.cursor()
        try:
            cur.execute('''
                INSERT INTO enrollments (user_id, course_id)
                VALUES (%s, %s)
            ''', (session['user_id'], course_id))
            conn.commit()
        except psycopg2.IntegrityError:
            # Already enrolled
            conn.rollback()
        cur.close()
        conn.close()
    
    return redirect(url_for('course_detail', course_id=course_id))

# Enhanced LMS route (existing courses page)
@app.route('/lms')
def lms():
    """Enhanced LMS course catalog"""
    conn = get_db_connection()
    if not conn:
        return "Database connection error", 500
    
    cur = conn.cursor()
    cur.execute('''
        SELECT c.id, c.title, c.description, c.difficulty_level, c.price, c.duration_weeks,
               u.first_name, u.last_name, COUNT(e.id) as enrollment_count
        FROM courses c
        JOIN users u ON c.instructor_id = u.id
        LEFT JOIN enrollments e ON c.id = e.course_id
        WHERE c.is_published = TRUE
        GROUP BY c.id, c.title, c.description, c.difficulty_level, c.price, c.duration_weeks, u.first_name, u.last_name
        ORDER BY c.created_at DESC
    ''')
    courses = cur.fetchall()
    
    # Get user's enrollments if logged in
    user_enrollments = set()
    if 'user_id' in session:
        cur.execute('SELECT course_id FROM enrollments WHERE user_id = %s', (session['user_id'],))
        user_enrollments = {row[0] for row in cur.fetchall()}
    
    cur.close()
    conn.close()
    
    return render_template_string(enhanced_lms_template, courses=courses, user_enrollments=user_enrollments)

# API Routes
@app.route('/api/user/progress')
def api_user_progress():
    """API endpoint for user progress data"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database error'}), 500
    
    cur = conn.cursor()
    cur.execute('''
        SELECT c.title, e.progress_percentage, e.enrolled_at, e.completed_at
        FROM enrollments e
        JOIN courses c ON e.course_id = c.id
        WHERE e.user_id = %s
    ''', (session['user_id'],))
    
    progress_data = []
    for row in cur.fetchall():
        progress_data.append({
            'course_title': row[0],
            'progress': float(row[1]) if row[1] else 0,
            'enrolled_at': row[2].isoformat() if row[2] else None,
            'completed_at': row[3].isoformat() if row[3] else None
        })
    
    cur.close()
    conn.close()
    
    return jsonify({'progress': progress_data})

# HTML Templates
login_template = '''
<!DOCTYPE html>
<html>
<head>
    <title>Login - Advanced LMS</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            margin: 0; padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh; display: flex;
            align-items: center; justify-content: center;
        }
        .login-container {
            background: white; padding: 40px; border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2); width: 100%; max-width: 400px;
        }
        .form-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 5px; font-weight: 500; }
        input {
            width: 100%; padding: 12px; border: 1px solid #ddd;
            border-radius: 8px; font-size: 16px; box-sizing: border-box;
        }
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; padding: 12px 24px; border: none;
            border-radius: 8px; width: 100%; font-size: 16px; cursor: pointer;
        }
        .error { color: #e74c3c; margin: 10px 0; }
        .link { text-align: center; margin-top: 20px; }
        .link a { color: #667eea; text-decoration: none; }
    </style>
</head>
<body>
    <div class="login-container">
        <h2 style="text-align: center; margin-bottom: 30px;">Login to LMS</h2>
        {% if error %}<div class="error">{{ error }}</div>{% endif %}
        <form method="POST">
            <div class="form-group">
                <label for="username">Username:</label>
                <input type="text" id="username" name="username" required>
            </div>
            <div class="form-group">
                <label for="password">Password:</label>
                <input type="password" id="password" name="password" required>
            </div>
            <button type="submit" class="btn">Login</button>
        </form>
        <div class="link">
            <p>Don't have an account? <a href="/register">Register here</a></p>
            <p><a href="/">Back to Home</a></p>
        </div>
        <div style="margin-top: 30px; padding: 15px; background: #f8f9fa; border-radius: 8px; font-size: 14px;">
            <strong>Demo Accounts:</strong><br>
            Instructor: username=instructor, password=instructor123<br>
            Student: username=student, password=student123
        </div>
    </div>
</body>
</html>
'''

register_template = '''
<!DOCTYPE html>
<html>
<head>
    <title>Register - Advanced LMS</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            margin: 0; padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh; display: flex; align-items: center; justify-content: center;
        }
        .register-container {
            background: white; padding: 40px; border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2); width: 100%; max-width: 500px;
        }
        .form-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 5px; font-weight: 500; }
        input {
            width: 100%; padding: 12px; border: 1px solid #ddd;
            border-radius: 8px; font-size: 16px; box-sizing: border-box;
        }
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; padding: 12px 24px; border: none;
            border-radius: 8px; width: 100%; font-size: 16px; cursor: pointer;
        }
        .error { color: #e74c3c; margin: 10px 0; }
        .link { text-align: center; margin-top: 20px; }
        .link a { color: #667eea; text-decoration: none; }
        .form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }
    </style>
</head>
<body>
    <div class="register-container">
        <h2 style="text-align: center; margin-bottom: 30px;">Create Account</h2>
        {% if error %}<div class="error">{{ error }}</div>{% endif %}
        <form method="POST">
            <div class="form-row">
                <div class="form-group">
                    <label for="first_name">First Name:</label>
                    <input type="text" id="first_name" name="first_name" required>
                </div>
                <div class="form-group">
                    <label for="last_name">Last Name:</label>
                    <input type="text" id="last_name" name="last_name" required>
                </div>
            </div>
            <div class="form-group">
                <label for="username">Username:</label>
                <input type="text" id="username" name="username" required>
            </div>
            <div class="form-group">
                <label for="email">Email:</label>
                <input type="email" id="email" name="email" required>
            </div>
            <div class="form-group">
                <label for="password">Password:</label>
                <input type="password" id="password" name="password" required>
            </div>
            <button type="submit" class="btn">Create Account</button>
        </form>
        <div class="link">
            <p>Already have an account? <a href="/login">Login here</a></p>
            <p><a href="/">Back to Home</a></p>
        </div>
    </div>
</body>
</html>
'''

dashboard_template = '''
<!DOCTYPE html>
<html>
<head>
    <title>Dashboard - Advanced LMS</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            margin: 0; padding: 20px; background: #f8f9fa;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; padding: 30px; border-radius: 15px; margin-bottom: 30px;
        }
        .dashboard-grid {
            display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px;
        }
        .card {
            background: white; padding: 20px; border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .card h3 { margin-top: 0; color: #2c3e50; }
        .progress-bar {
            width: 100%; height: 8px; background: #eee; border-radius: 4px; margin: 10px 0;
        }
        .progress-fill {
            height: 100%; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 4px;
        }
        .course-list { list-style: none; padding: 0; }
        .course-item {
            padding: 15px; border: 1px solid #eee; border-radius: 8px; margin-bottom: 10px;
        }
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; padding: 8px 16px; border: none;
            border-radius: 6px; text-decoration: none; display: inline-block; margin: 5px 5px 5px 0;
        }
        .btn:hover { opacity: 0.9; }
        .stats {
            display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px; margin: 20px 0;
        }
        .stat-card {
            background: rgba(255,255,255,0.2); padding: 20px;
            border-radius: 10px; text-align: center;
        }
        .stat-number { font-size: 2em; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Welcome, {{ user_info[0] }} {{ user_info[1] }}!</h1>
            <p>{{ role.title() }} Dashboard</p>
            {% if role == 'instructor' %}
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-number">{{ courses|length }}</div>
                    <div>Courses</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{{ recent_enrollments|length }}</div>
                    <div>Recent Enrollments</div>
                </div>
            </div>
            {% endif %}
            <div style="margin-top: 20px;">
                <a href="/lms" class="btn">Browse All Courses</a>
                <a href="/logout" class="btn">Logout</a>
            </div>
        </div>
        
        <div class="dashboard-grid">
            {% if role == 'instructor' %}
            <div class="card">
                <h3>📚 My Courses</h3>
                {% if courses %}
                <ul class="course-list">
                    {% for course in courses %}
                    <li class="course-item">
                        <strong>{{ course[1] }}</strong>
                        <p>{{ course[2][:100] }}...</p>
                        <p>👥 {{ course[3] }} students enrolled</p>
                        <a href="/course/{{ course[0] }}" class="btn">View Course</a>
                    </li>
                    {% endfor %}
                </ul>
                {% else %}
                <p>No courses yet.</p>
                {% endif %}
            </div>
            
            <div class="card">
                <h3>📈 Recent Enrollments</h3>
                {% if recent_enrollments %}
                <ul class="course-list">
                    {% for enrollment in recent_enrollments %}
                    <li class="course-item">
                        <strong>{{ enrollment[0] }} {{ enrollment[1] }}</strong><br>
                        enrolled in {{ enrollment[2] }}<br>
                        <small>{{ enrollment[3].strftime('%Y-%m-%d %H:%M') }}</small>
                    </li>
                    {% endfor %}
                </ul>
                {% else %}
                <p>No recent enrollments</p>
                {% endif %}
            </div>
            
            {% else %}
            <div class="card">
                <h3>📖 My Courses</h3>
                {% if enrollments %}
                <ul class="course-list">
                    {% for enrollment in enrollments %}
                    <li class="course-item">
                        <strong>{{ enrollment[1] }}</strong>
                        <p>{{ enrollment[2][:100] }}...</p>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: {{ enrollment[3] or 0 }}%"></div>
                        </div>
                        <small>Progress: {{ enrollment[3] or 0 }}%</small>
                        {% if enrollment[5] %}
                        <span style="color: green;"> ✅ Completed</span>
                        {% endif %}
                        <br>
                        <a href="/course/{{ enrollment[0] }}" class="btn">Continue Learning</a>
                    </li>
                    {% endfor %}
                </ul>
                {% else %}
                <p>No courses enrolled yet. Check out available courses below!</p>
                {% endif %}
            </div>
            
            <div class="card">
                <h3>🔍 Available Courses</h3>
                {% if available_courses %}
                <ul class="course-list">
                    {% for course in available_courses %}
                    <li class="course-item">
                        <strong>{{ course[1] }}</strong>
                        <p>{{ course[2][:100] }}...</p>
                        <p>👨‍🏫 {{ course[4] }} {{ course[5] }}</p>
                        {% if course[3] > 0 %}
                        <p>💰 ${{ course[3] }}</p>
                        {% else %}
                        <p style="color: green;">🆓 Free</p>
                        {% endif %}
                        <a href="/course/{{ course[0] }}" class="btn">View Details</a>
                    </li>
                    {% endfor %}
                </ul>
                {% else %}
                <p>No new courses available</p>
                {% endif %}
            </div>
            {% endif %}
        </div>
    </div>
</body>
</html>
'''

course_detail_template = '''
<!DOCTYPE html>
<html>
<head>
    <title>{{ course[1] }} - Advanced LMS</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            margin: 0; padding: 20px; background: #f8f9fa;
        }
        .container { max-width: 1000px; margin: 0 auto; }
        .course-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; padding: 40px; border-radius: 15px; margin-bottom: 30px;
        }
        .course-content { display: grid; grid-template-columns: 2fr 1fr; gap: 30px; }
        .lessons-section {
            background: white; padding: 30px; border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        .course-info {
            background: white; padding: 30px; border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        .lesson {
            border: 1px solid #eee; border-radius: 8px; margin-bottom: 15px; overflow: hidden;
        }
        .lesson-header {
            padding: 15px 20px; background: #f8f9fa; cursor: pointer;
            display: flex; justify-content: between; align-items: center;
        }
        .lesson-content { padding: 20px; display: none; }
        .lesson.completed .lesson-header { background: #e8f5e8; border-left: 4px solid #27ae60; }
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; padding: 12px 24px; border: none;
            border-radius: 8px; text-decoration: none; display: inline-block; margin: 10px 0;
        }
        .btn:hover { opacity: 0.9; }
        .btn-success { background: #27ae60; }
        .progress-bar {
            width: 100%; height: 10px; background: #eee; border-radius: 5px; margin: 15px 0;
        }
        .progress-fill {
            height: 100%; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 5px; transition: width 0.3s ease;
        }
        .info-item {
            margin: 15px 0; padding: 15px; background: #f8f9fa; border-radius: 8px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="course-header">
            <h1>{{ course[1] }}</h1>
            <p>{{ course[2] }}</p>
            <p>👨‍🏫 Instructor: {{ course[6] }} {{ course[7] }}</p>
            {% if enrollment %}
            <div class="progress-bar">
                <div class="progress-fill" style="width: {{ enrollment[0] or 0 }}%"></div>
            </div>
            <p>Progress: {{ enrollment[0] or 0 }}% completed</p>
            {% endif %}
        </div>
        
        <div class="course-content">
            <div class="lessons-section">
                <h2>📚 Course Lessons</h2>
                {% if lessons %}
                {% for lesson in lessons %}
                <div class="lesson {% if lesson[0] in lesson_progress %}completed{% endif %}">
                    <div class="lesson-header" onclick="toggleLesson({{ lesson[0] }})">
                        <div>
                            <strong>Lesson {{ lesson[4] }}: {{ lesson[1] }}</strong>
                            <br><small>⏱️ {{ lesson[5] }} minutes</small>
                        </div>
                        {% if lesson[0] in lesson_progress %}
                        <span style="color: #27ae60;">✅</span>
                        {% endif %}
                    </div>
                    <div id="lesson-{{ lesson[0] }}" class="lesson-content">
                        {% if enrollment %}
                        <p>{{ lesson[2] or 'No content available yet.' }}</p>
                        {% if lesson[3] %}
                        <p>🎥 <a href="{{ lesson[3] }}" target="_blank">Watch Video</a></p>
                        {% endif %}
                        {% else %}
                        <p><em>Enroll in this course to access lesson content</em></p>
                        {% endif %}
                    </div>
                </div>
                {% endfor %}
                {% else %}
                <p>No lessons available yet.</p>
                {% endif %}
            </div>
            
            <div class="course-info">
                <h3>📋 Course Information</h3>
                
                <div class="info-item">
                    <strong>Duration:</strong> {{ course[3] }} weeks
                </div>
                
                <div class="info-item">
                    <strong>Difficulty:</strong> {{ course[4].title() }}
                </div>
                
                <div class="info-item">
                    <strong>Price:</strong> 
                    {% if course[5] and course[5] > 0 %}
                    ${{ course[5] }}
                    {% else %}
                    Free
                    {% endif %}
                </div>
                
                {% if enrollment %}
                <div class="info-item">
                    <strong>Enrolled:</strong> {{ enrollment[1].strftime('%Y-%m-%d') }}
                    {% if enrollment[2] %}
                    <br><strong>Completed:</strong> {{ enrollment[2].strftime('%Y-%m-%d') }}
                    {% endif %}
                </div>
                
                <a href="/dashboard" class="btn">Back to Dashboard</a>
                {% else %}
                {% if 'user_id' in session %}
                <form action="/enroll/{{ course[0] }}" method="POST">
                    <button type="submit" class="btn btn-success">Enroll Now</button>
                </form>
                {% else %}
                <a href="/login" class="btn">Login to Enroll</a>
                {% endif %}
                {% endif %}
                
                <a href="/lms" class="btn">Browse All Courses</a>
            </div>
        </div>
    </div>
    
    <script>
    function toggleLesson(lessonId) {
        const content = document.getElementById('lesson-' + lessonId);
        content.style.display = content.style.display === 'none' ? 'block' : 
                                content.style.display === 'block' ? 'none' : 'block';
    }
    </script>
</body>
</html>
'''

enhanced_lms_template = '''
<!DOCTYPE html>
<html>
<head>
    <title>Course Catalog - Advanced LMS</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            margin: 0; padding: 20px; background: #f8f9fa;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; padding: 30px; border-radius: 15px; margin-bottom: 30px; text-align: center;
        }
        .course-grid {
            display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 25px;
        }
        .course-card {
            background: white; border-radius: 15px; overflow: hidden;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1); transition: transform 0.2s;
        }
        .course-card:hover { transform: translateY(-5px); }
        .course-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; padding: 20px;
        }
        .course-body { padding: 20px; }
        .course-meta {
            display: flex; justify-content: space-between; align-items: center;
            margin: 15px 0; font-size: 14px; color: #666;
        }
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; padding: 10px 20px; border: none;
            border-radius: 8px; text-decoration: none; display: inline-block; margin: 5px 0;
        }
        .btn:hover { opacity: 0.9; }
        .btn-enrolled { background: #27ae60; }
        .badge {
            background: rgba(255,255,255,0.2); color: white;
            padding: 5px 10px; border-radius: 15px; font-size: 12px; margin: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📚 Course Catalog</h1>
            <p>Explore our comprehensive selection of professional courses</p>
            <div style="margin-top: 20px;">
                {% if 'user_id' in session %}
                <a href="/dashboard" class="btn">My Dashboard</a>
                <a href="/logout" class="btn">Logout</a>
                {% else %}
                <a href="/login" class="btn">Login</a>
                <a href="/register" class="btn">Register</a>
                {% endif %}
                <a href="/" class="btn">Home</a>
            </div>
        </div>
        
        <div class="course-grid">
            {% for course in courses %}
            <div class="course-card">
                <div class="course-header">
                    <h3>{{ course[1] }}</h3>
                    <div>
                        <span class="badge">{{ course[3].title() }}</span>
                        <span class="badge">{{ course[5] }} weeks</span>
                    </div>
                </div>
                
                <div class="course-body">
                    <p>{{ course[2][:150] }}...</p>
                    
                    <div class="course-meta">
                        <span>👨‍🏫 {{ course[6] }} {{ course[7] }}</span>
                        <span>👥 {{ course[8] }} enrolled</span>
                    </div>
                    
                    <div class="course-meta">
                        <strong>
                            {% if course[4] and course[4] > 0 %}
                            💰 ${{ course[4] }}
                            {% else %}
                            🆓 Free
                            {% endif %}
                        </strong>
                    </div>
                    
                    {% if course[0] in user_enrollments %}
                    <a href="/course/{{ course[0] }}" class="btn btn-enrolled">Continue Learning</a>
                    {% else %}
                    <a href="/course/{{ course[0] }}" class="btn">View Details</a>
                    {% endif %}
                </div>
            </div>
            {% endfor %}
        </div>
    </div>
</body>
</html>
'''

# Initialize the database on startup
if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port, debug=False)