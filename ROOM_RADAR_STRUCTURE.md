# Room Radar - Complete Project Structure

```
room-radar/
│
├── app.py                          # Main Flask application entry point
├── config.py                       # Configuration settings (development/production)
├── models.py                       # Database models (User, Hostel, Report, etc.)
├── forms.py                        # WTForms validation classes
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment variables template
├── .gitignore                      # Git ignore rules
│
├── routes/
│   ├── __init__.py
│   ├── auth.py                     # Authentication: login, register, logout
│   ├── hostels.py                  # Hostel browsing and search
│   ├── admin.py                    # Admin dashboard and moderation
│   └── api.py                      # API endpoints for AJAX calls
│
├── templates/
│   ├── base.html                   # Base template with navbar/footer
│   ├── index.html                  # Login page with blurred background
│   ├── register.html               # Registration page
│   ├── dashboard.html              # Student dashboard (hostel listings)
│   ├── hostel_detail.html          # Individual hostel detail page
│   ├── landlord_dashboard.html     # Landlord dashboard
│   ├── admin_dashboard.html        # Admin moderation panel
│   ├── 404.html                    # Error page
│   └── 500.html                    # Server error page
│
├── static/
│   ├── css/
│   │   └── style.css               # Main responsive stylesheet
│   ├── js/
│   │   └── script.js               # Vanilla JavaScript (no jQuery)
│   ├── images/
│   │   └── hostel-bg.jpg           # Background image for login
│   └── uploads/                    # User-uploaded images (hostel photos)
│
├── database/
│   └── init_db.py                  # Script to initialize database
│
└── docs/
    ├── SETUP.md                    # Setup instructions for Windows 11
    ├── API_DOCUMENTATION.md        # API endpoints documentation
    └── SECURITY.md                 # Security implementation details
```

## Key Features Overview:
1. **Authentication**: Role-based (Student, Landlord, Admin)
2. **Hostel Listings**: CRUD with admin approval workflow
3. **Search & Filters**: Fast, indexed queries
4. **Admin Dashboard**: Moderate content, manage users
5. **Security**: CSRF protection, SQL injection prevention, password hashing
6. **Responsive**: Mobile-first design

## Security Layers Implemented:
- ✅ Passwords hashed with Werkzeug (not stored in plain text)
- ✅ CSRF tokens on all forms
- ✅ Input validation and sanitization
- ✅ SQL injection prevention (parameterized queries)
- ✅ SQL Alchemy ORM (no raw SQL)
- ✅ Rate limiting on login attempts
- ✅ Secure session management
- ✅ File upload validation
- ✅ Role-based access control (RBAC)
- ✅ Logging of admin actions

## Tech Stack:
- **Backend**: Flask 2.0+, SQLAlchemy ORM
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Security**: Werkzeug, Flask-WTF, Flask-Login
- **Hosting Ready**: PythonAnywhere, Render

---

Files will be created in order of dependencies:
1. models.py → Database schema
2. forms.py → Input validation
3. app.py → Main app
4. routes/ → All route handlers
5. templates/ → HTML files
6. static/ → CSS and JS
