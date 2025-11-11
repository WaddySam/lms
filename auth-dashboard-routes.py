# Authentication and Dashboard Routes
# Add to railway-flask-app-enhanced.py

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

# API Routes for mobile/external access
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

# Templates (keeping them in the same file for simplicity)
login_template = '''
<!DOCTYPE html>
<html>
<head>
    <title>Login - Advanced LMS</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .login-container {
            background: white;
            padding: 40px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            width: 100%;
            max-width: 400px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: 500;
        }
        input {
            width: 100%;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 8px;
            font-size: 16px;
            box-sizing: border-box;
        }
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            width: 100%;
            font-size: 16px;
            cursor: pointer;
        }
        .error {
            color: #e74c3c;
            margin: 10px 0;
        }
        .link {
            text-align: center;
            margin-top: 20px;
        }
        .link a {
            color: #667eea;
            text-decoration: none;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <h2 style="text-align: center; margin-bottom: 30px;">Login to LMS</h2>
        
        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}
        
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
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .register-container {
            background: white;
            padding: 40px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            width: 100%;
            max-width: 500px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: 500;
        }
        input {
            width: 100%;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 8px;
            font-size: 16px;
            box-sizing: border-box;
        }
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            width: 100%;
            font-size: 16px;
            cursor: pointer;
        }
        .error {
            color: #e74c3c;
            margin: 10px 0;
        }
        .link {
            text-align: center;
            margin-top: 20px;
        }
        .link a {
            color: #667eea;
            text-decoration: none;
        }
        .form-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
        }
    </style>
</head>
<body>
    <div class="register-container">
        <h2 style="text-align: center; margin-bottom: 30px;">Create Account</h2>
        
        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}
        
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
            margin: 0;
            padding: 20px;
            background: #f8f9fa;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 30px;
        }
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }
        .card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .card h3 {
            margin-top: 0;
            color: #2c3e50;
        }
        .progress-bar {
            width: 100%;
            height: 8px;
            background: #eee;
            border-radius: 4px;
            margin: 10px 0;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 4px;
        }
        .course-list {
            list-style: none;
            padding: 0;
        }
        .course-item {
            padding: 15px;
            border: 1px solid #eee;
            border-radius: 8px;
            margin-bottom: 10px;
        }
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 8px 16px;
            border: none;
            border-radius: 6px;
            text-decoration: none;
            display: inline-block;
            margin: 5px 5px 5px 0;
        }
        .btn:hover { opacity: 0.9; }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .stat-card {
            background: rgba(255,255,255,0.2);
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }
        .stat-number {
            font-size: 2em;
            font-weight: bold;
        }
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
                <p>No courses yet. <a href="/create-course">Create your first course</a></p>
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
            margin: 0;
            padding: 20px;
            background: #f8f9fa;
        }
        .container {
            max-width: 1000px;
            margin: 0 auto;
        }
        .course-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            border-radius: 15px;
            margin-bottom: 30px;
        }
        .course-content {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 30px;
        }
        .lessons-section {
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        .course-info {
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        .lesson {
            border: 1px solid #eee;
            border-radius: 8px;
            margin-bottom: 15px;
            overflow: hidden;
        }
        .lesson-header {
            padding: 15px 20px;
            background: #f8f9fa;
            cursor: pointer;
            display: flex;
            justify-content: between;
            align-items: center;
        }
        .lesson-content {
            padding: 20px;
            display: none;
        }
        .lesson.completed .lesson-header {
            background: #e8f5e8;
            border-left: 4px solid #27ae60;
        }
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            text-decoration: none;
            display: inline-block;
            margin: 10px 0;
            cursor: pointer;
        }
        .btn:hover { opacity: 0.9; }
        .btn-success { background: #27ae60; }
        .progress-bar {
            width: 100%;
            height: 10px;
            background: #eee;
            border-radius: 5px;
            margin: 15px 0;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 5px;
            transition: width 0.3s ease;
        }
        .info-item {
            margin: 15px 0;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
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
                        {% if lesson[0] not in lesson_progress %}
                        <button class="btn" onclick="markComplete({{ lesson[0] }})">Mark as Complete</button>
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
    
    function markComplete(lessonId) {
        // This would typically make an AJAX call to mark the lesson as complete
        alert('Lesson marked as complete! (This would update the database in a real implementation)');
        location.reload();
    }
    </script>
</body>
</html>
'''