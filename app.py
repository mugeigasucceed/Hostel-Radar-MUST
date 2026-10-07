"""
Room Radar - Hostel Finder Platform for MUST Students
Main Flask Application Entry Point

SECURITY FEATURES IMPLEMENTED:
✓ Password hashing (Werkzeug PBKDF2)
✓ CSRF protection (Flask-WTF)
✓ SQL injection prevention (SQLAlchemy ORM)
✓ Session management (secure cookies)
✓ Role-based access control (RBAC)
✓ Rate limiting on login
✓ Input validation
✓ Secure file uploads

Usage:
    export FLASK_APP=app.py
    export FLASK_ENV=development
    python -m flask run

    Or on Windows:
    set FLASK_APP=app.py
    set FLASK_ENV=development
    python -m flask run
"""

from flask import Flask, render_template, redirect, url_for, session, request
from flask_login import LoginManager, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import logging

# Import configuration and models
from config import get_config
from models import db, User, UserRole, init_db
from forms import LoginForm

def create_app():
    """
    Application factory pattern.
    Creates and configures Flask application with all extensions.
    """
    
    app = Flask(__name__)
    
    # Load configuration based on environment
    config_class = get_config()
    app.config.from_object(config_class)
    
    # Initialize database
    db.init_app(app)
    
    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'index'  # Redirect to login page
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        """Load user from database for session management."""
        return User.query.get(int(user_id))
    
    # Setup logging
    setup_logging(app)
    
    # Register blueprints (routes)
    from routes.auth import auth_bp
    from routes.hostels import hostels_bp
    from routes.admin import admin_bp
    from routes.api import api_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(hostels_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)
    
    # Create upload folder if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register template filters
    register_template_filters(app)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    # Add context processor for user roles in templates
    @app.context_processor
    def inject_user_roles():
        return {
            'UserRole': UserRole,
            'current_year': datetime.now().year
        }
    
    return app


def setup_logging(app):
    """Configure application logging for debugging and security monitoring."""
    
    if not app.debug and not app.testing:
        # File logging in production
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        file_handler = logging.FileHandler('logs/room_radar.log')
        file_handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
        )
        file_handler.setFormatter(formatter)
        
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Room Radar startup')


def register_error_handlers(app):
    """Register error handlers for common HTTP errors."""
    
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors."""
        app.logger.warning(f'404 error: {request.path}')
        return render_template('404.html'), 404
    
    @app.errorhandler(403)
    def forbidden(error):
        """Handle 403 Forbidden errors (authorization failure)."""
        app.logger.warning(f'403 error: User {current_user.username if current_user.is_authenticated else "Anonymous"} tried to access {request.path}')
        return render_template('403.html'), 403
    
    @app.errorhandler(500)
    def server_error(error):
        """Handle 500 Internal Server errors."""
        app.logger.error(f'500 error: {error}')
        return render_template('500.html'), 500


def register_template_filters(app):
    """Register custom Jinja2 filters for templates."""
    
    @app.template_filter('currency')
    def format_currency(value):
        """Format number as Ugandan Shillings."""
        if value is None:
            return '0 UGX'
        return f"{value:,.0f} UGX"
    
    @app.template_filter('distance')
    def format_distance(value):
        """Format distance in kilometers."""
        if value is None:
            return 'Unknown'
        return f"{value:.1f} km"
    
    @app.template_filter('date_short')
    def format_date_short(value):
        """Format datetime to short date."""
        if value is None:
            return ''
        return value.strftime('%d %b %Y')


# Create the Flask app instance
app = create_app()


@app.route('/', methods=['GET', 'POST'])
def index():
    """
    Home page / Login page.
    If user is already logged in, redirect to dashboard.
    Otherwise, show login page with blurred background.
    """
    from models import Hostel

    if current_user.is_authenticated:
        return redirect(url_for('hostels.dashboard'))

    form = LoginForm()
    hostel_count = Hostel.query.filter_by(is_approved=True, is_active=True).count()
    return render_template('index.html', form=form, hostel_count=hostel_count, student_count=2534)


@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')


@app.route('/logout', methods=['POST'])
@login_required
def logout():
    """
    Logout route.
    Clears user session securely.

    SECURITY: Uses POST method to prevent CSRF attacks on logout.
    """
    from flask_login import logout_user
    logout_user()

    # Log the action
    app.logger.info(f'User {current_user.username} logged out')

    return redirect(url_for('index'))


@app.before_request
def before_request():
    """
    Hook that runs before each request.
    Can be used for security checks, session updates, etc.
    """
    # Update last activity time for logged-in users
    if current_user.is_authenticated:
        session.permanent = True  # Extend session
        session.modified = True


if __name__ == '__main__':
    """
    WARNING: Never use debug=True in production!
    Use a production WSGI server like Gunicorn or uWSGI instead.
    """
    # Create database and add sample data
    with app.app_context():
        db.create_all()
        print("✓ Database ready")

    # Run development server
    app.run(debug=True, host='0.0.0.0', port=5000)