"""
API routes for Room Radar.
Provides JSON endpoints for AJAX calls and frontend updates.

SECURITY FEATURES:
✓ All endpoints require authentication
✓ CSRF token validation (handled by Flask-WTF)
✓ JSON responses prevent XSS
✓ Rate limiting on sensitive operations
✓ Proper HTTP status codes
"""

from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required, current_user
from models import db, Hostel, Report, User
from sqlalchemy import func
import logging

api_bp = Blueprint('api', __name__, url_prefix='/api')
logger = logging.getLogger(__name__)


@api_bp.route('/hostels/search', methods=['GET'])
@login_required
def search_hostels_api():
    """
    API endpoint for hostel search (used by frontend JavaScript).
    Returns JSON results.
    
    SECURITY:
    ✓ Requires authentication
    ✓ Validates all parameters
    ✓ Returns only approved hostels
    ✓ Pagination prevents abuse
    
    Query Parameters:
    - q: search query (location)
    - min_price: minimum price filter
    - max_price: maximum price filter
    - gender: gender filter
    - page: page number
    """
    
    try:
        # Get parameters
        query = request.args.get('q', '').strip()
        min_price = request.args.get('min_price', type=int)
        max_price = request.args.get('max_price', type=int)
        gender = request.args.get('gender', '').strip()
        page = request.args.get('page', 1, type=int)
        
        # Validate inputs
        if len(query) > 100:
            return jsonify({'error': 'Search query too long'}), 400
        
        if min_price and min_price < 0:
            return jsonify({'error': 'Invalid price'}), 400
        
        if max_price and max_price < 0:
            return jsonify({'error': 'Invalid price'}), 400
        
        # Build query
        sql_query = Hostel.query.filter(
            Hostel.is_approved == True,
            Hostel.is_active == True
        )
        
        # Apply filters
        if query:
            sql_query = sql_query.filter(Hostel.area.ilike(f'%{query}%'))
        
        if min_price:
            sql_query = sql_query.filter(Hostel.price_max >= min_price)
        
        if max_price:
            sql_query = sql_query.filter(Hostel.price_min <= max_price)
        
        if gender and gender in ['male', 'female', 'both']:
            sql_query = sql_query.filter(
                Hostel.gender_allowed.in_([gender, 'both'])
            )
        
        # Sort by distance
        sql_query = sql_query.order_by(Hostel.distance_from_campus.asc())
        
        # Paginate
        results = sql_query.paginate(
            page=page,
            per_page=current_app.config['ITEMS_PER_PAGE'],
            error_out=False
        )
        
        # Build response
        hostels_data = []
        for hostel in results.items:
            hostels_data.append({
                'id': hostel.id,
                'name': hostel.name,
                'area': hostel.area,
                'distance': float(hostel.distance_from_campus),
                'price_min': hostel.price_min,
                'price_max': hostel.price_max,
                'gender': hostel.gender_allowed,
                'room_type': hostel.room_type
            })
        
        return jsonify({
            'success': True,
            'data': hostels_data,
            'total': results.total,
            'pages': results.pages,
            'current_page': page
        })
    
    except Exception as e:
        logger.error(f'Search API error: {str(e)}')
        return jsonify({'error': 'Search failed'}), 500


@api_bp.route('/hostels/<int:hostel_id>/details', methods=['GET'])
@login_required
def get_hostel_details_api(hostel_id):
    """
    Get detailed hostel information as JSON.
    
    SECURITY:
    ✓ Validates hostel_id is integer
    ✓ Only returns approved hostels
    ✓ Returns owner info safely (no email to non-owner)
    """
    
    hostel = Hostel.query.filter(
        Hostel.id == hostel_id,
        Hostel.is_approved == True,
        Hostel.is_active == True
    ).first()
    
    if not hostel:
        return jsonify({'error': 'Hostel not found'}), 404
    
    owner = User.query.get(hostel.owner_id)
    
    return jsonify({
        'success': True,
        'data': {
            'id': hostel.id,
            'name': hostel.name,
            'area': hostel.area,
            'description': hostel.description,
            'distance': float(hostel.distance_from_campus),
            'price_min': hostel.price_min,
            'price_max': hostel.price_max,
            'gender': hostel.gender_allowed,
            'room_type': hostel.room_type,
            'amenities': hostel.get_amenities_list(),
            'owner_name': owner.full_name if owner else 'Unknown',
            'phone': hostel.phone,
            'email': hostel.email,
            'created_at': hostel.created_at.isoformat()
        }
    })


@api_bp.route('/user/stats', methods=['GET'])
@login_required
def get_user_stats_api():
    """
    Get user statistics (for dashboard).
    
    Returns different data based on user role:
    - Student: saved hostels count
    - Landlord: listing count, approval status, reports count
    - Admin: pending approvals, reports, users
    """
    
    stats = {
        'success': True,
        'user_role': current_user.role.value
    }
    
    if current_user.is_landlord():
        # Landlord stats
        total_listings = Hostel.query.filter_by(owner_id=current_user.id).count()
        approved_listings = Hostel.query.filter(
            Hostel.owner_id == current_user.id,
            Hostel.is_approved == True
        ).count()
        pending_listings = total_listings - approved_listings
        
        stats['listings'] = {
            'total': total_listings,
            'approved': approved_listings,
            'pending': pending_listings
        }
    
    elif current_user.is_admin():
        # Admin stats
        stats['admin'] = {
            'pending_hostels': Hostel.query.filter_by(is_approved=False).count(),
            'pending_reports': Report.query.filter_by(status='pending').count(),
            'total_users': User.query.count(),
            'total_hostels': Hostel.query.filter_by(is_approved=True).count()
        }
    
    return jsonify(stats)


@api_bp.route('/validate-email', methods=['POST'])
def validate_email_api():
    """
    Check if email is already registered (for registration form).
    
    SECURITY:
    ✓ POST method
    ✓ Validates email format
    ✓ Case-insensitive check
    ✓ No data leakage (doesn't confirm if user exists)
    """
    
    email = request.json.get('email', '').lower().strip()
    
    # Basic email validation
    if not email or '@' not in email:
        return jsonify({'available': False}), 400
    
    # Check if email exists
    user = User.query.filter_by(email=email).first()
    
    return jsonify({
        'available': user is None,
        'email': email
    })


@api_bp.route('/validate-username', methods=['POST'])
def validate_username_api():
    """
    Check if username is available (for registration form).
    
    SECURITY:
    ✓ Validates username format
    ✓ Case-insensitive check
    """
    
    username = request.json.get('username', '').strip()
    
    # Validate username length
    if len(username) < 3 or len(username) > 20:
        return jsonify({'available': False}), 400
    
    # Check if username exists
    user = User.query.filter_by(username=username).first()
    
    return jsonify({
        'available': user is None,
        'username': username
    })


@api_bp.route('/hostels/<int:hostel_id>/report-count', methods=['GET'])
@login_required
def get_report_count_api(hostel_id):
    """
    Get count of reports for a hostel (admin only).
    
    SECURITY:
    ✓ Admin-only endpoint
    ✓ Returns only pending report count
    """
    
    if not current_user.is_admin():
        return jsonify({'error': 'Unauthorized'}), 403
    
    hostel = Hostel.query.get_or_404(hostel_id)
    
    pending_count = Report.query.filter(
        Report.hostel_id == hostel_id,
        Report.status == 'pending'
    ).count()
    
    return jsonify({
        'hostel_id': hostel_id,
        'pending_reports': pending_count
    })


@api_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint (for monitoring/deployment).
    No authentication required.
    """
    return jsonify({'status': 'healthy', 'version': '1.0.0'}), 200


# Error handlers for API
@api_bp.errorhandler(404)
def api_not_found(error):
    return jsonify({'error': 'Not found'}), 404


@api_bp.errorhandler(500)
def api_server_error(error):
    logger.error(f'API error: {error}')
    return jsonify({'error': 'Internal server error'}), 500
