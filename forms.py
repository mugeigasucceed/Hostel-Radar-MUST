"""
Form validation for Room Radar.
Uses WTForms for server-side validation and CSRF protection.

SECURITY NOTE:
- All forms include CSRF tokens (WTF_CSRF_ENABLED = True in config)
- Input is validated before storing in database
- Regex patterns prevent injection attacks
- Email validation prevents typos and spam
"""

from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, SelectField, TextAreaField,
    IntegerField, BooleanField, DecimalField, SubmitField
)
from wtforms.validators import (
    DataRequired, Email, Length, EqualTo, NumberRange,
    Optional, Regexp, ValidationError
)
from models import User
import re


class RegistrationForm(FlaskForm):
    """
    Registration form for new users.
    Validates all inputs before account creation.
    """
    username = StringField(
        'Username',
        validators=[
            DataRequired(),
            Length(min=3, max=20),
            Regexp('^[a-zA-Z0-9_-]*$', message='Only letters, numbers, underscore and dash allowed')
        ]
    )
    
    email = StringField(
    'Email',
    validators=[
        DataRequired(),
        Email(message='Invalid email address', check_deliverability=False)
    ]
)
    
    full_name = StringField(
        'Full Name',
        validators=[
            DataRequired(),
            Length(min=2, max=120)
        ]
    )
    
    phone = StringField(
        'Phone Number',
        validators=[
            DataRequired(),
            Regexp(r'^\+?1?\d{9,15}$', message='Invalid phone number. Use format: +256701234567')
        ]
    )
    
    role = SelectField(
        'Account Type',
        choices=[
            ('student', 'Student'),
            ('landlord', 'Landlord')
        ],
        validators=[DataRequired()]
    )
    
    password = PasswordField(
        'Password',
        validators=[
            DataRequired(),
            Length(min=8, message='Password must be at least 8 characters'),
        ]
    )
    
    password_confirm = PasswordField(
        'Confirm Password',
        validators=[
            DataRequired(),
            EqualTo('password', message='Passwords do not match')
        ]
    )
    
    agree_terms = BooleanField(
        'I agree to the Terms & Conditions',
        validators=[DataRequired()]
    )
    
    submit = SubmitField('Create Account')
    
    def validate_username(self, username):
        """Check if username is already taken."""
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already taken. Choose another.')
    
    def validate_email(self, email):
        """Check if email is already registered."""
        user = User.query.filter_by(email=email.data.lower()).first()
        if user:
            raise ValidationError('Email already registered. Login instead.')


class LoginForm(FlaskForm):
    """
    Login form with rate limiting consideration.
    See auth.py for rate limiting implementation.
    """
    email = StringField(
        'Email',
        validators=[
            DataRequired(),
            Email(message='Invalid email address', check_deliverability=False)
        ]
    )
    
    password = PasswordField(
        'Password',
        validators=[DataRequired()]
    )
    
    remember_me = BooleanField('Remember me for 7 days')
    
    submit = SubmitField('Login')


class HostelForm(FlaskForm):
    """
    Form for creating/editing hostel listings.
    Landlords use this to add accommodation to Room Radar.
    """
    name = StringField(
        'Hostel Name',
        validators=[
            DataRequired(),
            Length(min=3, max=120)
        ]
    )
    
    description = TextAreaField(
        'Description',
        validators=[
            Optional(),
            Length(max=1000)
        ]
    )
    
    area = StringField(
        'Area/Location',
        validators=[
            DataRequired(),
            Length(min=2, max=100)
        ]
    )
    
    distance_from_campus = DecimalField(
        'Distance from Campus (km)',
        validators=[
            DataRequired(),
            NumberRange(min=0, max=100, message='Must be between 0 and 100 km')
        ]
    )
    
    price_min = IntegerField(
        'Minimum Price (UGX)',
        validators=[
            DataRequired(),
            NumberRange(min=10000, message='Price must be at least 10,000 UGX')
        ]
    )
    
    price_max = IntegerField(
        'Maximum Price (UGX)',
        validators=[
            DataRequired(),
            NumberRange(min=10000, message='Price must be at least 10,000 UGX')
        ]
    )
    
    gender_allowed = SelectField(
        'Gender Allowed',
        choices=[
            ('male', 'Male only'),
            ('female', 'Female only'),
            ('both', 'Both male and female')
        ],
        validators=[DataRequired()]
    )
    
    room_type = SelectField(
        'Room Type',
        choices=[
            ('single', 'Single room'),
            ('double', 'Double room'),
            ('shared', 'Shared room')
        ],
        validators=[DataRequired()]
    )
    
    total_rooms = IntegerField(
        'Total Rooms',
        validators=[
            Optional(),
            NumberRange(min=1, message='Must be at least 1 room')
        ]
    )
    
    available_rooms = IntegerField(
        'Available Rooms',
        validators=[
            Optional(),
            NumberRange(min=0, message='Cannot be negative')
        ]
    )
    
    phone = StringField(
        'Contact Phone',
        validators=[
            DataRequired(),
            Regexp(r'^\+?1?\d{9,15}$', message='Invalid phone number')
        ]
    )
    
    email = StringField(
        'Contact Email',
        validators=[
            Optional(),
            Email(message='Invalid email address')
        ]
    )
    
    submit = SubmitField('Save Hostel Listing')
    
    def validate_price_max(self, price_max):
        """Ensure max price is not less than min price."""
        if price_max.data and self.price_min.data:
            if price_max.data < self.price_min.data:
                raise ValidationError('Max price cannot be less than minimum price.')


class ReportForm(FlaskForm):
    """
    Form for users to report problematic listings.
    Admin uses reports to moderate content.
    """
    reason = SelectField(
        'Report Reason',
        choices=[
            ('fraud', 'Fraud or fake listing'),
            ('inappropriate', 'Inappropriate content'),
            ('spam', 'Spam or scam'),
            ('harassment', 'Harassment'),
            ('other', 'Other reason')
        ],
        validators=[DataRequired()]
    )
    
    description = TextAreaField(
        'Additional Details',
        validators=[
            DataRequired(),
            Length(min=10, max=500, message='Please provide at least 10 characters')
        ]
    )
    
    submit = SubmitField('Submit Report')


class SearchForm(FlaskForm):
    """
    Search/filter form for browsing hostels.
    Uses GET method (no CSRF token needed for GET requests).
    """
    location = StringField(
        'Location',
        validators=[Optional(), Length(max=100)]
    )
    
    price_min = IntegerField(
        'Min Price (UGX)',
        validators=[Optional(), NumberRange(min=0)]
    )
    
    price_max = IntegerField(
        'Max Price (UGX)',
        validators=[Optional(), NumberRange(min=0)]
    )
    
    gender = SelectField(
        'Gender',
        choices=[
            ('', 'Any'),
            ('male', 'Male'),
            ('female', 'Female'),
            ('both', 'Both')
        ],
        validators=[Optional()]
    )
    
    room_type = SelectField(
        'Room Type',
        choices=[
            ('', 'Any'),
            ('single', 'Single'),
            ('double', 'Double'),
            ('shared', 'Shared')
        ],
        validators=[Optional()]
    )
    
    amenities = StringField(
        'Amenities (comma-separated)',
        validators=[Optional(), Length(max=200)]
    )
    
    submit = SubmitField('Search')


class ChangePasswordForm(FlaskForm):
    """
    Form for users to change their password.
    Requires old password for verification.
    """
    old_password = PasswordField(
        'Current Password',
        validators=[DataRequired()]
    )
    
    new_password = PasswordField(
        'New Password',
        validators=[
            DataRequired(),
            Length(min=8, message='Password must be at least 8 characters'),
            Regexp(
                r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)',
                message='Password must contain uppercase, lowercase, and number'
            )
        ]
    )
    
    new_password_confirm = PasswordField(
        'Confirm New Password',
        validators=[
            DataRequired(),
            EqualTo('new_password', message='Passwords do not match')
        ]
    )
    
    submit = SubmitField('Change Password')


class EditProfileForm(FlaskForm):
    """Form for users to update their profile information."""
    
    full_name = StringField(
        'Full Name',
        validators=[
            DataRequired(),
            Length(min=2, max=120)
        ]
    )
    
    phone = StringField(
        'Phone Number',
        validators=[
            DataRequired(),
            Regexp(r'^\+?1?\d{9,15}$', message='Invalid phone number')
        ]
    )
    
    submit = SubmitField('Save Profile')
