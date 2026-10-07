# Room Radar - Setup Guide for Windows 11 Pro

Complete step-by-step instructions to set up and run Room Radar locally on Windows 11 Pro.

---

## Prerequisites

Before you start, ensure you have:
- Windows 11 Pro
- Administrator access
- Internet connection
- At least 2GB free disk space

---

## Step 1: Install Python 3.10+

### Download Python:
1. Go to https://www.python.org/downloads/
2. Click "Download Python 3.11" (or latest version)
3. Run the installer

### During Installation:
- ✅ **Check "Add Python to PATH"** - This is CRITICAL
- ✅ Check "Install pip"
- Click "Install Now"

### Verify Installation:
Open Command Prompt and run:
```cmd
python --version
pip --version
```

Both should show version numbers. If not, Python wasn't added to PATH.

---

## Step 2: Set Up Project Folder

1. Choose a location (e.g., `C:\Users\YourName\Documents`)
2. Create a new folder: `room-radar`
3. Open Command Prompt in that folder:
   - Open File Explorer
   - Navigate to the folder
   - Click the address bar, type `cmd`, press Enter

---

## Step 3: Create Python Virtual Environment

Virtual environments isolate project dependencies.

Run in Command Prompt (in your `room-radar` folder):

```cmd
python -m venv venv
```

This creates a `venv` folder. Now activate it:

```cmd
venv\Scripts\activate
```

You should see `(venv)` at the start of your Command Prompt line.

---

## Step 4: Copy Project Files

Copy all the files we've created into your `room-radar` folder:

```
room-radar/
├── app.py
├── config.py
├── models.py
├── forms.py
├── requirements.txt
├── .env.example
├── routes/
│   ├── __init__.py
│   ├── auth.py
│   ├── hostels.py
│   ├── admin.py
│   └── api.py
├── templates/
│   └── (HTML files)
└── static/
    ├── css/
    │   └── style.css
    ├── js/
    │   └── script.js
    └── uploads/
```

---

## Step 5: Install Dependencies

With virtual environment activated, run:

```cmd
pip install -r requirements.txt
```

This installs Flask, SQLAlchemy, and all other packages.

**Installation time**: 2-3 minutes

---

## Step 6: Configure Environment

1. Copy `.env.example` to `.env`:
   ```cmd
   copy .env.example .env
   ```

2. Open `.env` in Notepad and update:
   ```
   FLASK_ENV=development
   SECRET_KEY=your-random-secret-key-12345
   ```

   For SECRET_KEY, generate a random string:
   ```cmd
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

---

## Step 7: Initialize Database

Create the SQLite database:

```cmd
python
```

Then in Python shell:
```python
from app import app, db
with app.app_context():
    db.create_all()
print("✓ Database created!")
exit()
```

This creates `room_radar_dev.db` in your folder.

---

## Step 8: Create Admin User (Optional)

Create an admin account for testing:

```python
python
```

```python
from app import app, db
from models import User, UserRole
from datetime import datetime

with app.app_context():
    # Create admin user
    admin = User(
        username='admin',
        email='admin@roomradar.local',
        full_name='Admin User',
        phone='+256701234567',
        role=UserRole.ADMIN,
        is_verified=True,
        is_active=True
    )
    admin.set_password('Admin@1234')  # Change this!
    
    db.session.add(admin)
    db.session.commit()
    print("✓ Admin user created!")
    print(f"  Email: admin@roomradar.local")
    print(f"  Password: Admin@1234")
exit()
```

---

## Step 9: Run the Application

```cmd
python app.py
```

You should see:

```
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
 * Press CTRL+C to quit
```

Open your browser and go to: **http://localhost:5000**

---

## Step 10: Test the Application

### Login:
- Email: `admin@roomradar.local`
- Password: `Admin@1234`

### Create Test Users:

**Student account:**
- Register at `/auth/register`
- Select "Student"
- Use any email

**Landlord account:**
- Register at `/auth/register`
- Select "Landlord"
- List will be pending admin approval

### Test Features:
1. ✅ Login/Logout
2. ✅ View hostels (admin can create some for testing)
3. ✅ Search and filter
4. ✅ Admin dashboard (as admin user)
5. ✅ Approve listings (as admin)

---

## Troubleshooting

### "Python is not recognized"
**Solution**: Python wasn't added to PATH.
1. Uninstall Python
2. Reinstall, checking "Add Python to PATH"
3. Restart Command Prompt

### "No module named 'flask'"
**Solution**: Virtual environment not activated.
Run: `venv\Scripts\activate`

### "Port 5000 already in use"
**Solution**: Another app is using port 5000.
Change in `app.py`:
```python
app.run(debug=True, port=5001)  # Use 5001 instead
```

### Database errors
**Solution**: Delete `room_radar_dev.db` and re-run Step 7

### CSRF errors on forms
**Solution**: Make sure `.env` has a valid `SECRET_KEY`

---

## Development Tips

### Enable SQL Query Logging:
In `config.py`, change:
```python
SQLALCHEMY_ECHO = True  # See all SQL queries in console
```

### Hot Reload Code:
Flask automatically reloads code when you save files (in development mode).

### View Database:
SQLite databases can be viewed with tools like:
- DB Browser for SQLite (free): https://sqlitebrowser.org/
- Visual Studio Code SQLite extension

### Stop the Server:
Press `CTRL+C` in Command Prompt

---

## Security Checklist Before Production

Before deploying to hosting:

- [ ] Change `SECRET_KEY` to a strong random value
- [ ] Set `FLASK_ENV=production`
- [ ] Change `DEBUG=False`
- [ ] Use PostgreSQL instead of SQLite
- [ ] Set strong admin password
- [ ] Add HTTPS certificate
- [ ] Set secure session cookies
- [ ] Review all user inputs for validation
- [ ] Set up database backups
- [ ] Configure error logging

---

## Next Steps: Deployment

### Option 1: PythonAnywhere (Easiest for beginners)
1. Go to https://www.pythonanywhere.com
2. Create free account
3. Upload your files
4. Configure web app
5. Done! Your app is live

### Option 2: Render (Also free tier)
1. Go to https://render.com
2. Connect GitHub repository
3. Deploy with one click

### Option 3: Traditional VPS (Heroku, AWS, DigitalOcean)
- More control but requires more setup
- Use Gunicorn + Nginx

---

## File Structure Summary

```
room-radar/
├── app.py                          # Main app entry point
├── config.py                       # Configuration
├── models.py                       # Database models
├── forms.py                        # Form validation
├── requirements.txt                # Python dependencies
├── .env                            # Environment config (CREATE THIS)
│
├── routes/                         # URL handlers
│   ├── auth.py                     # Login/register
│   ├── hostels.py                  # Hostel listings
│   ├── admin.py                    # Admin dashboard
│   └── api.py                      # API endpoints
│
├── templates/                      # HTML templates
│   ├── base.html                   # Base layout
│   ├── index.html                  # Login page
│   ├── dashboard.html              # Hostel browse
│   └── ... (other pages)
│
├── static/                         # Static files
│   ├── css/style.css               # Stylesheet
│   ├── js/script.js                # JavaScript
│   ├── images/hostel-bg.jpg        # Background
│   └── uploads/                    # User uploads
│
├── venv/                           # Virtual environment (auto-created)
└── room_radar_dev.db               # SQLite database (auto-created)
```

---

## Common Commands Cheat Sheet

```cmd
# Activate virtual environment
venv\Scripts\activate

# Deactivate virtual environment
deactivate

# Install dependencies
pip install -r requirements.txt

# Run Flask app
python app.py

# Access Python shell
python

# Create database
python -c "from app import app, db; app.app_context().push(); db.create_all()"

# List installed packages
pip list

# Update pip
python -m pip install --upgrade pip
```

---

## Support

If you encounter issues:
1. Check the error message carefully
2. Google the error message
3. Check Flask documentation: https://flask.palletsprojects.com
4. Check SQLAlchemy docs: https://docs.sqlalchemy.org

---

**Happy Coding! 🚀**

Your Room Radar app is now ready for development!
