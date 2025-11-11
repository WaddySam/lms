# 🎓 Advanced Learning Management System (LMS)

A comprehensive, production-ready Learning Management System built with Flask and deployed on Railway.

## ✨ Features

### 👥 **User Management**
- User registration and authentication
- Role-based access (Student/Instructor)
- Session management with secure login

### 📚 **Course Management**
- Create and manage courses
- Lesson organization with multimedia support
- Progress tracking and completion certificates
- Course difficulty levels and pricing

### 🎯 **Learning Experience**
- Interactive course catalog
- Personal dashboard for students and instructors
- Lesson progress tracking
- Quiz and assessment system
- Certificate generation

### 📊 **Analytics & Reporting**
- Student progress analytics
- Course enrollment statistics
- Performance tracking
- API endpoints for data integration

## 🚀 **Live Demo**

The enhanced LMS is deployed on Railway with the following features:

- **Home Page**: Overview and navigation
- **Authentication**: Login/Register system
- **Dashboard**: Personalized user experience
- **Course Catalog**: Browse available courses
- **Course Details**: Detailed course information and enrollment
- **API**: RESTful endpoints for data access

### Demo Accounts

| Role | Username | Password |
|------|----------|----------|
| Instructor | `instructor` | `instructor123` |
| Student | `student` | `student123` |

## 🏗️ **Architecture**

### Database Schema

```sql
-- Users table for authentication
users (id, username, email, password_hash, first_name, last_name, role)

-- Courses table for course management
courses (id, title, description, instructor_id, duration_weeks, difficulty_level, price, is_published)

-- Lessons table for course content
lessons (id, course_id, title, content, video_url, lesson_order, duration_minutes)

-- Enrollments for student-course relationship
enrollments (id, user_id, course_id, enrolled_at, completed_at, progress_percentage)

-- Progress tracking
lesson_progress (id, user_id, lesson_id, completed_at, time_spent_minutes)

-- Quiz system
quizzes (id, lesson_id, title, description, passing_score, time_limit_minutes)
quiz_questions (id, quiz_id, question_text, question_type, options, correct_answer)
quiz_attempts (id, user_id, quiz_id, score, max_score, started_at, completed_at)

-- Certificates
certificates (id, user_id, course_id, certificate_code, issued_at)
```

### Technology Stack

- **Backend**: Python Flask
- **Database**: PostgreSQL (Railway managed)
- **Frontend**: HTML5, CSS3, JavaScript
- **Deployment**: Docker + Railway
- **Authentication**: Session-based with secure hashing

## 🔧 **Local Development**

### Prerequisites
- Python 3.11+
- PostgreSQL
- pip package manager

### Installation

1. **Clone the repository:**
```bash
git clone <repository-url>
cd lms
```

2. **Install dependencies:**
```bash
pip install -r requirements-enhanced.txt
```

3. **Set environment variables:**
```bash
export DATABASE_URL="postgresql://user:password@localhost:5432/lms_db"
export SECRET_KEY="your-secret-key"
```

4. **Run the application:**
```bash
python railway-flask-app-enhanced.py
```

The application will be available at `http://localhost:3000`

## 🌐 **Deployment on Railway**

### Automatic Deployment

This project is configured for automatic deployment on Railway:

1. **Connect Repository**: Link your GitHub repository to Railway
2. **Environment Setup**: Railway automatically detects the PostgreSQL requirement
3. **Build Process**: Uses `Dockerfile.enhanced` for containerized deployment
4. **Database**: Automatically provisions PostgreSQL database

### Manual Deployment

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Deploy
railway up
```

### Environment Variables

Railway automatically provides:
- `DATABASE_URL`: PostgreSQL connection string
- `PORT`: Application port
- `RAILWAY_PUBLIC_DOMAIN`: Public domain

Optional variables:
- `SECRET_KEY`: Flask session secret (auto-generated if not set)

## 📱 **API Endpoints**

### Course Management
- `GET /api/courses` - List all courses
- `GET /course/<id>` - Course details
- `POST /enroll/<course_id>` - Enroll in course

### User Management
- `POST /login` - User login
- `POST /register` - User registration
- `GET /api/user/progress` - User progress data

### Health & Monitoring
- `GET /health` - Application health check
- `GET /` - Application status

## 🎨 **UI/UX Features**

### Responsive Design
- Mobile-first responsive layout
- Modern gradient design
- Intuitive navigation

### User Experience
- Progress bars for course completion
- Interactive lesson navigation
- Real-time enrollment updates
- Certificate download functionality

### Accessibility
- Semantic HTML structure
- Keyboard navigation support
- Screen reader compatibility

## 🔐 **Security Features**

### Authentication
- Password hashing with SHA256
- Session-based authentication
- CSRF protection
- SQL injection prevention

### Data Protection
- Parameterized database queries
- Input validation and sanitization
- Secure session management

## 📈 **Performance Optimization**

### Database
- Indexed queries for fast lookups
- Optimized JOIN operations
- Connection pooling ready

### Application
- Efficient template rendering
- Minimal JavaScript dependencies
- Optimized static assets

## 🧪 **Testing**

### Manual Testing
1. User registration and login
2. Course enrollment workflow
3. Progress tracking functionality
4. API endpoint validation

### Automated Testing (Future Enhancement)
```bash
# Unit tests
python -m pytest tests/

# Integration tests
python -m pytest tests/integration/
```

## 🔄 **Future Enhancements**

### Phase 1: Core Features
- [ ] Advanced quiz system with multiple question types
- [ ] File upload for course materials
- [ ] Real-time notifications
- [ ] Discussion forums

### Phase 2: Advanced Features
- [ ] Video streaming integration
- [ ] Payment processing
- [ ] Mobile application
- [ ] Advanced analytics dashboard

### Phase 3: Enterprise Features
- [ ] Multi-tenant support
- [ ] SSO integration
- [ ] Advanced reporting
- [ ] White-label customization

## 🤝 **Contributing**

1. Fork the repository
2. Create feature branch: `git checkout -b feature/new-feature`
3. Commit changes: `git commit -am 'Add new feature'`
4. Push to branch: `git push origin feature/new-feature`
5. Create Pull Request

## 📝 **License**

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 **Support**

For support and questions:
- Create an issue on GitHub
- Email: support@lms-demo.com
- Documentation: [Project Wiki](link-to-wiki)

## 🙏 **Acknowledgments**

- Railway for hosting and deployment platform
- PostgreSQL for robust database management
- Flask community for excellent framework
- All contributors and testers

---

**Built with ❤️ using Flask and Railway**