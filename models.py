"""
Database models for Room Radar.
Defines the structure for Users, Hostels, Reports, and Bookings.

SECURITY NOTE: Using SQLAlchemy ORM prevents SQL injection by default.
All database queries use parameterized queries.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import enum

db = SQLAlchemy()


class UserRole(enum.Enum):
    """Enum for user roles - used for role-based access control (RBAC)."""
    STUDENT = 'student'
    LANDLORD = 'landlord'
    ADMIN = 'admin'


class User(UserMixin, db.Model):
    """
    User model for authentication.
    
    SECURITY:
    - password_hash stores hashed passwords (never plain text)
    - use check_password() to verify login credentials
    - is_verified flag prevents fake accounts from listing hostels
    """
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    role = db.Column(db.Enum(UserRole), default=UserRole.STUDENT, nullable=False)
    
    # Account status flags
    is_verified = db.Column(db.Boolean, default=False)  # Email verified?
    is_active = db.Column(db.Boolean, default=True)  # Not banned?
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    hostels = db.relationship('Hostel', backref='owner', lazy=True, cascade='all, delete-orphan')
    reports = db.relationship('Report', backref='reporter', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def set_password(self, password):
        """
        Hash and store password.
        Uses Werkzeug's security module (PBKDF2 with SHA-256 by default).
        SECURITY: Never store plain text passwords!
        """
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
    
    def check_password(self, password):
        """
        Verify password against stored hash.
        SECURITY: Use this method in login routes only.
        """
        return check_password_hash(self.password_hash, password)
    
    def is_landlord(self):
        """Check if user is a landlord."""
        return self.role == UserRole.LANDLORD
    
    def is_student(self):
        """Check if user is a student."""
        return self.role == UserRole.STUDENT
    
    def is_admin(self):
        """Check if user is an admin."""
        return self.role == UserRole.ADMIN
    
    def can_list_hostels(self):
        """
        Check if user is allowed to list hostels.
        SECURITY: Only verified landlords can list.
        """
        return self.is_landlord() and self.is_verified


class Hostel(db.Model):
    """
    Hostel listing model.
    
    SECURITY:
    - owner_id is a foreign key (referential integrity)
    - is_approved flag prevents unverified listings from being shown
    - Reports can flag problematic listings for admin review
    - All user input is validated in forms.py before storing
    """
    __tablename__ = 'hostels'
    
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Listing information
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # Location and distance
    area = db.Column(db.String(100), nullable=False)  # e.g., "Mbarara Central", "Nyamityobora"
    distance_from_campus = db.Column(db.Float, nullable=False)  # in kilometers
    
    # Pricing
    price_min = db.Column(db.Integer, nullable=False)  # Minimum price (UGX)
    price_max = db.Column(db.Integer, nullable=False)  # Maximum price (UGX)
    
    # Hostel details
    gender_allowed = db.Column(db.String(50), nullable=False)  # 'male', 'female', 'both'
    room_type = db.Column(db.String(100), nullable=False)  # 'single', 'double', 'shared'
    total_rooms = db.Column(db.Integer, nullable=True)
    available_rooms = db.Column(db.Integer, nullable=True)
    
    # Amenities (stored as comma-separated string for simplicity)
    amenities = db.Column(db.String(500), nullable=True)  # e.g., "wifi,water,electricity,parking"
    
    # Contact information
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    
    # Photo URL (stored as path)
    photo_url = db.Column(db.String(255), nullable=True)
    
    # Status flags
    is_approved = db.Column(db.Boolean, default=False, index=True)  # Admin must approve
    is_active = db.Column(db.Boolean, default=True)  # Landlord can soft-delete
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    reports = db.relationship('Report', backref='hostel', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Hostel {self.name}>'
    
    def get_amenities_list(self):
        """Convert comma-separated amenities string to list."""
        if self.amenities:
            return [a.strip() for a in self.amenities.split(',')]
        return []
    
    def set_amenities_list(self, amenities_list):
        """Convert list of amenities to comma-separated string."""
        self.amenities = ','.join(amenities_list) if amenities_list else None
    
    def has_violation_reports(self):
        """Check if listing has multiple reports flagging it."""
        report_count = Report.query.filter_by(hostel_id=self.id, status='pending').count()
        return report_count >= 3  # Flag if 3+ pending reports


class Report(db.Model):
    """
    Report model for flagging problematic listings.
    
    SECURITY:
    - Admins review reports to remove fraudulent or inappropriate listings
    - Prevents abuse by tracking reporter_id
    - Reports are soft-deleted (status='resolved') for audit trail
    """
    __tablename__ = 'reports'
    
    id = db.Column(db.Integer, primary_key=True)
    hostel_id = db.Column(db.Integer, db.ForeignKey('hostels.id'), nullable=False, index=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Report details
    reason = db.Column(db.String(100), nullable=False)  # e.g., 'fraud', 'inappropriate', 'spam'
    description = db.Column(db.Text, nullable=False)
    
    # Status
    status = db.Column(db.String(20), default='pending')  # 'pending', 'resolved', 'dismissed'
    admin_notes = db.Column(db.Text, nullable=True)  # Notes from admin who reviewed
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Report {self.reason} on Hostel {self.hostel_id}>'


class AuditLog(db.Model):
    """
    Audit log for admin actions.
    
    SECURITY:
    - Tracks all admin actions for accountability
    - Helps detect abuse or unauthorized modifications
    """
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)  # e.g., 'approved_hostel', 'banned_user'
    target_type = db.Column(db.String(50), nullable=False)  # e.g., 'hostel', 'user'
    target_id = db.Column(db.Integer, nullable=False)
    details = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(50), nullable=True)  # For security tracking
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f'<AuditLog {self.action}>'


def init_db(app):
    """Initialize database tables."""
    with app.app_context():
        db.create_all()
        print("✓ Database initialized successfully!")
