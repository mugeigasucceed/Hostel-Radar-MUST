# Room Radar - Security Implementation Guide

Comprehensive documentation of security features and best practices implemented in Room Radar.

---

## 🔒 Security Features Overview

### 1. Authentication & Authorization

#### Password Security
**Implementation**: Werkzeug Password Hashing
```python
# In models.py
def set_password(self, password):
    """Hash password using PBKDF2 with SHA-256"""
    self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

def check_password(self, password):
    """Verify password against stored hash"""
    return check_password_hash(self.password_hash, password)
```

**Why it's secure**:
- ✅ PBKDF2 with SHA-256: Industry standard
- ✅ Passwords hashed with salt automatically
- ✅ Never stores plain text passwords
- ✅ Each password is unique even if identical

**Attack Prevention**:
- Blocks password dictionary attacks
- Resistant to rainbow tables
- Slow by design (intentional computation delay)

---

#### Session Management
**Implementation**: Flask-Login + Secure Cookies

```python
# In config.py
SESSION_COOKIE_SECURE = True         # HTTPS only
SESSION_COOKIE_HTTPONLY = True       # No JavaScript access
SESSION_COOKIE_SAMESITE = 'Lax'      # CSRF protection
PERMANENT_SESSION_LIFETIME = timedelta(days=7)
```

**Benefits**:
- ✅ `HTTPONLY`: Prevents XSS attacks from stealing session cookies
- ✅ `SECURE`: Cookie only sent over HTTPS
- ✅ `SAMESITE`: Blocks CSRF attacks
- ✅ Automatic session expiration after 7 days

**Attack Prevention**:
- Blocks cookie-stealing JavaScript
- Forces secure encrypted transport
- Prevents cross-site request forgery

---

#### Role-Based Access Control (RBAC)
**Implementation**: User roles with authorization checks

```python
# In models.py
class UserRole(enum.Enum):
    STUDENT = 'student'
    LANDLORD = 'landlord'
    ADMIN = 'admin'

# Usage in routes
@admin_required  # Only admins access
def admin_dashboard():
    return render_template('admin_dashboard.html')

# In hostels.py
if not current_user.is_landlord():
    abort(403)  # Deny access
```

**Protection**:
- ✅ Students can't access landlord features
- ✅ Landlords can't access admin features
- ✅ Each route validates user role
- ✅ Unauthorized access logs security warning

---

### 2. CSRF (Cross-Site Request Forgery) Protection

**Implementation**: Flask-WTF CSRF Tokens

```python
# In forms.py
from flask_wtf import FlaskForm
class LoginForm(FlaskForm):
    # Automatically includes CSRF token
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])

# In templates/login.html
<form method="POST">
    {{ form.csrf_token }}
    {{ form.email }}
    {{ form.password }}
    <button>Login</button>
</form>
```

**How it works**:
1. Each form gets unique CSRF token
2. Token embedded in form HTML
3. Server validates token on submission
4. Attackers can't forge valid tokens
5. Token expires with session

**Attack Prevention**:
- Blocks unauthorized form submissions
- Prevents malicious sites from stealing data
- Even if attacker steals token, it's session-specific

---

### 3. SQL Injection Prevention

**Implementation**: SQLAlchemy ORM (Object-Relational Mapping)

```python
# SAFE - Using ORM
hostels = Hostel.query.filter(
    Hostel.area.ilike(f'%{search_term}%')
).all()

# DANGEROUS - Raw SQL (NEVER DO THIS)
# db.session.execute(f"SELECT * FROM hostels WHERE area LIKE '%{search_term}%'")
```

**Why ORM is secure**:
- ✅ Automatic parameterization
- ✅ Escapes special characters
- ✅ No string concatenation
- ✅ Database driver handles syntax

**Example Attack Blocked**:
```python
# Attacker enters search term:
search_term = "'; DROP TABLE hostels; --"

# ORM treats it as literal string, not SQL command
# Query becomes: SELECT * FROM hostels WHERE area LIKE '%...;DROP TABLE...; --%'
# Database sees it as data, not executable code
```

---

### 4. Input Validation & Sanitization

**Implementation**: WTForms Validators

```python
# In forms.py
class RegistrationForm(FlaskForm):
    username = StringField(
        'Username',
        validators=[
            DataRequired(),
            Length(min=3, max=20),
            Regexp('^[a-zA-Z0-9_-]*$', message='Only letters, numbers allowed')
        ]
    )
    
    email = StringField(
        'Email',
        validators=[DataRequired(), Email()]
    )
    
    password = PasswordField(
        'Password',
        validators=[
            DataRequired(),
            Length(min=8, message='Min 8 characters')
        ]
    )
```

**Validations performed**:
- ✅ Required fields aren't empty
- ✅ Email format is valid
- ✅ Usernames follow regex pattern (no SQL injection)
- ✅ Passwords meet length requirement
- ✅ Phone numbers are valid format
- ✅ Prices are numeric and positive

**Attack Prevention**:
- Blocks invalid data at form submission
- Prevents injection through form fields
- Ensures data consistency in database

---

### 5. Rate Limiting (Login Attacks)

**Implementation**: IP-based rate limiting

```python
# In routes/auth.py
def rate_limit_login(max_attempts=5, window_seconds=300):
    """Block IP after 5 failed attempts in 5 minutes"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            ip = request.remote_addr
            
            # Clean old attempts
            login_attempts[ip] = [
                timestamp for timestamp in login_attempts[ip]
                if (now - timestamp).total_seconds() < window_seconds
            ]
            
            # Block if too many attempts
            if len(login_attempts[ip]) >= max_attempts:
                flash('Too many login attempts. Try again in 5 minutes.')
                return redirect(url_for('auth.login'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Applied to login route:
@auth_bp.route('/login', methods=['GET', 'POST'])
@rate_limit_login(max_attempts=5, window_seconds=300)
def login():
    # ... login logic
```

**Attack Prevention**:
- ✅ Blocks brute force password attacks
- ✅ Slows down automated attempts
- ✅ Tracks per IP address
- ✅ Temporary lockout (5 minutes)
- ✅ Logs suspicious activity

---

### 6. File Upload Security (Future Feature)

**Config for Safe Uploads**:

```python
# In config.py
MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB max
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}

# In upload handler
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_upload(file):
    # Validate file
    if not allowed_file(file.filename):
        raise ValueError('File type not allowed')
    
    # Generate random name (prevents directory traversal)
    random_name = secrets.token_hex(16) + '.jpg'
    
    # Save to safe location
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], random_name)
    file.save(filepath)
    
    return random_name  # Store in DB, not user-provided name
```

**Attack Prevention**:
- ✅ Size limits prevent disk DoS
- ✅ Extension validation blocks executables
- ✅ Random filenames prevent overwriting
- ✅ Separate upload folder (outside web root ideally)

---

### 7. Error Handling & Information Disclosure

**Implementation**: Custom error pages

```python
# In app.py
@app.errorhandler(404)
def not_found(error):
    app.logger.warning(f'404 error: {request.path}')
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(error):
    app.logger.error(f'500 error: {error}')
    return render_template('500.html'), 500  # Generic message
```

**Security Benefits**:
- ✅ Doesn't show full error stack to users
- ✅ Attackers don't learn system info
- ✅ Errors still logged for debugging
- ✅ Professional error pages

**Example**:
```
❌ BAD (reveals info):
"Error in file /home/user/room-radar/models.py line 42: Column 'email' not found"

✅ GOOD:
"An error occurred. Our team has been notified."
```

---

### 8. Authorization Checks on Data Access

**Implementation**: Query-level access control

```python
# Only show approved hostels to students
hostels = Hostel.query.filter(
    Hostel.is_approved == True,
    Hostel.is_active == True
).all()

# Only owner/admin can edit hostel
if current_user.id != hostel.owner_id and not current_user.is_admin():
    abort(403)  # Forbidden

# Only admin can approve listings
@admin_required
def approve_hostel(hostel_id):
    # ...
```

**Attack Prevention**:
- ✅ Data filtering at database query level
- ✅ Users can't access data they shouldn't
- ✅ Ownership validation prevents tampering
- ✅ Permission checks before every operation

---

### 9. Audit Logging

**Implementation**: Track all admin actions

```python
# In models.py
class AuditLog(db.Model):
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(100))  # 'approved_hostel', 'banned_user'
    target_type = db.Column(db.String(50))  # 'hostel', 'user', 'report'
    target_id = db.Column(db.Integer)
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# In routes/admin.py
def log_admin_action(action, target_type, target_id, details=None):
    audit_log = AuditLog(
        admin_id=current_user.id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details,
        ip_address=request.remote_addr
    )
    db.session.add(audit_log)
    db.session.commit()
```

**Benefits**:
- ✅ Tracks who made changes
- ✅ Knows what was changed
- ✅ Records when changes happened
- ✅ Logs IP address for investigations
- ✅ Detects unauthorized admin activity

---

### 10. Secure Dependencies

**Implementation**: Regular updates

```bash
# Check for security vulnerabilities
pip install safety
safety check

# Update packages
pip install --upgrade -r requirements.txt
```

**Best Practice**:
- ✅ Keep all packages updated
- ✅ Use `safety` to check for known vulns
- ✅ Review security advisories
- ✅ Update immediately for critical fixes

---

## 🛡️ Defense Layers Summary

| Attack Type | Prevention Method | Code Location |
|------------|------------------|----------------|
| Password Guessing | Hashing + Salt | models.py |
| Brute Force | Rate Limiting | routes/auth.py |
| CSRF | CSRF Tokens | forms.py |
| SQL Injection | SQLAlchemy ORM | All routes |
| XSS | Secure Cookies | config.py |
| Privilege Escalation | RBAC + Checks | routes/*.py |
| Unauthorized Access | Query Filtering | routes/hostels.py |
| Data Tampering | Ownership Validation | routes/hostels.py |
| Untracked Changes | Audit Logging | routes/admin.py |
| Invalid Data | Input Validation | forms.py |

---

## 🚀 Production Security Checklist

Before deploying to production:

- [ ] **Environment Variables**
  - [ ] Change `SECRET_KEY` to random 32-character string
  - [ ] Set `FLASK_ENV=production`
  - [ ] Set `DEBUG=False`
  - [ ] Set `SESSION_COOKIE_SECURE=True`

- [ ] **Database**
  - [ ] Switch from SQLite to PostgreSQL
  - [ ] Use strong database password
  - [ ] Regular backups (daily minimum)
  - [ ] Restrict database access by IP

- [ ] **HTTPS/SSL**
  - [ ] Install SSL certificate
  - [ ] Redirect HTTP to HTTPS
  - [ ] Set `SESSION_COOKIE_SECURE=True`

- [ ] **Server Configuration**
  - [ ] Use Gunicorn or uWSGI (not Flask dev server)
  - [ ] Run behind reverse proxy (Nginx)
  - [ ] Restrict file permissions (chmod 755)
  - [ ] Disable directory listing

- [ ] **Monitoring**
  - [ ] Setup error logging (Sentry, CloudWatch)
  - [ ] Monitor CPU/Memory/Disk
  - [ ] Track login attempts
  - [ ] Alert on suspicious activity

- [ ] **Users**
  - [ ] Change default admin password
  - [ ] Require strong passwords (8+ chars, mixed case, numbers)
  - [ ] Enable two-factor authentication (future)
  - [ ] Regular account audits

- [ ] **Regular Updates**
  - [ ] Security patches within 24 hours
  - [ ] Test updates in staging first
  - [ ] Keep logs for 90+ days
  - [ ] Annual security audit

---

## 📋 Reporting Security Issues

If you discover a security vulnerability:

1. **Do NOT** post it publicly
2. **Do NOT** open a GitHub issue
3. Contact admin privately
4. Include:
   - Description of vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if you have one)

We'll acknowledge within 48 hours and fix promptly.

---

## 📚 Security Resources

- OWASP Top 10: https://owasp.org/www-project-top-ten/
- Flask Security: https://flask.palletsprojects.com/security/
- SQLAlchemy Security: https://docs.sqlalchemy.org/security/
- Werkzeug Security: https://werkzeug.palletsprojects.com/security/

---

**Remember**: Security is not a feature, it's a foundation. Regular updates and vigilance are essential.
