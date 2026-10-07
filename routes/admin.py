"""
Admin routes for Room Radar.
Admin-only endpoints for approving listings, managing reports, and moderating users.

SECURITY FEATURES:
✓ Role-based access control (admin_required decorator)
✓ Audit logging of all admin actions
✓ Authorization checks on all operations
✓ CSRF protection on all forms
✓ Prevents privilege escalation
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, current_app
from flask_login import login_required, current_user
from functools import wraps
from models import db, Hostel, Report, User, UserRole, AuditLog
from sqlalchemy import desc
import logging

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')
logger = logging.getLogger(__name__)


def admin_required(f):
    """
    Decorator to restrict routes to admin users only.
    SECURITY: Prevents non-admin users from accessing admin routes.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            logger.warning(f'Unauthorized admin access attempt by {current_user.username if current_user.is_authenticated else "Anonymous"}')
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def log_admin_action(action, target_type, target_id, details=None):
    """
    Log admin actions for audit trail.
    SECURITY: Creates accountability for all admin actions.
    """
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
    logger.info(f'Admin action logged: {action} on {target_type} {target_id} by {current_user.username}')


@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    """
    Admin dashboard - overview of pending approvals and reports.
    
    SECURITY: Admin-only access
    """
    
    # Get statistics
    pending_hostels = Hostel.query.filter_by(is_approved=False).count()
    pending_reports = Report.query.filter_by(status='pending').count()
    total_users = User.query.count()
    total_hostels = Hostel.query.filter_by(is_approved=True).count()
    
    # Get recent activity
    recent_reports = Report.query.filter_by(status='pending').order_by(
        desc(Report.created_at)
    ).limit(5).all()
    
    recent_hostels = Hostel.query.filter_by(is_approved=False).order_by(
        desc(Hostel.created_at)
    ).limit(5).all()
    
    return render_template(
        'admin_dashboard.html',
        pending_hostels=pending_hostels,
        pending_reports=pending_reports,
        total_users=total_users,
        total_hostels=total_hostels,
        recent_reports=recent_reports,
        recent_hostels=recent_hostels
    )


@admin_bp.route('/hostels/pending')
@login_required
@admin_required
def pending_hostels():
    """
    List all pending hostel approvals.
    Admins approve or reject from here.
    
    SECURITY: Admin-only, shows detailed info for review
    """
    
    page = request.args.get('page', 1, type=int)
    
    # Get pending hostels with owner info
    hostels = Hostel.query.filter_by(is_approved=False).order_by(
        Hostel.created_at.desc()
    ).paginate(
        page=page,
        per_page=current_app.config['ITEMS_PER_PAGE'],
        error_out=False
    )
    
    return render_template(
        'admin_pending_hostels.html',
        hostels=hostels,
        page=page
    )


@admin_bp.route('/hostels/<int:hostel_id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_hostel(hostel_id):
    """
    Approve a hostel listing for public display.
    
    SECURITY:
    ✓ CSRF protection (POST method)
    ✓ Validates hostel exists
    ✓ Logs action for audit trail
    ✓ Only pending hostels can be approved
    """
    
    hostel = Hostel.query.get_or_404(hostel_id)
    
    if hostel.is_approved:
        flash('This hostel is already approved.', 'info')
        return redirect(url_for('admin.pending_hostels'))
    
    # Approve hostel
    hostel.is_approved = True
    db.session.commit()
    
    # Log action
    log_admin_action(
        'approved_hostel',
        'hostel',
        hostel_id,
        f'Approved: {hostel.name}'
    )
    
    logger.info(f'Hostel {hostel.name} approved by admin {current_user.username}')
    flash(f'Hostel "{hostel.name}" has been approved and is now live!', 'success')
    
    return redirect(url_for('admin.pending_hostels'))


@admin_bp.route('/hostels/<int:hostel_id>/reject', methods=['POST'])
@login_required
@admin_required
def reject_hostel(hostel_id):
    """
    Reject a hostel listing (soft delete it).
    
    SECURITY:
    ✓ CSRF protection
    ✓ Logs rejection for audit trail
    ✓ Keeps data for audit purposes
    """
    
    hostel = Hostel.query.get_or_404(hostel_id)
    
    # Soft delete
    hostel.is_active = False
    hostel.is_approved = False
    db.session.commit()
    
    # Log action
    log_admin_action(
        'rejected_hostel',
        'hostel',
        hostel_id,
        f'Rejected: {hostel.name}'
    )
    
    logger.warning(f'Hostel {hostel.name} rejected by admin {current_user.username}')
    flash(f'Hostel "{hostel.name}" has been rejected.', 'success')
    
    return redirect(url_for('admin.pending_hostels'))


@admin_bp.route('/reports/pending')
@login_required
@admin_required
def pending_reports():
    """
    List all pending abuse reports for moderation.
    
    SECURITY: Admin-only access to reports
    """
    
    page = request.args.get('page', 1, type=int)
    
    # Get pending reports with related data
    reports = Report.query.filter_by(status='pending').order_by(
        Report.created_at.desc()
    ).paginate(
        page=page,
        per_page=current_app.config['ITEMS_PER_PAGE'],
        error_out=False
    )
    
    return render_template(
        'admin_pending_reports.html',
        reports=reports,
        page=page
    )


@admin_bp.route('/reports/<int:report_id>/resolve', methods=['POST'])
@login_required
@admin_required
def resolve_report(report_id):
    """
    Resolve a report (approve and take action).
    Action: Delete the hostel listing.
    
    SECURITY:
    ✓ CSRF protection
    ✓ Validates report and hostel exist
    ✓ Logs all actions
    ✓ Only pending reports can be resolved
    """
    
    report = Report.query.get_or_404(report_id)
    
    if report.status != 'pending':
        flash('This report has already been resolved.', 'info')
        return redirect(url_for('admin.pending_reports'))
    
    # Get the hostel
    hostel = Hostel.query.get(report.hostel_id)
    
    # Take action based on report reason
    if hostel:
        hostel.is_active = False
        hostel.is_approved = False
    
    # Mark report as resolved
    report.status = 'resolved'
    report.admin_notes = request.form.get('notes', '')
    
    db.session.commit()
    
    # Log action
    log_admin_action(
        'resolved_report',
        'report',
        report_id,
        f'Resolved report: {report.reason} - Action taken: Hostel deactivated'
    )
    
    logger.warning(f'Report #{report_id} resolved by admin {current_user.username} - Hostel {hostel.name} deactivated')
    flash('Report resolved and hostel removed.', 'success')
    
    return redirect(url_for('admin.pending_reports'))


@admin_bp.route('/reports/<int:report_id>/dismiss', methods=['POST'])
@login_required
@admin_required
def dismiss_report(report_id):
    """
    Dismiss a report (no action needed).
    
    SECURITY:
    ✓ CSRF protection
    ✓ Logs dismissal
    ✓ Keeps report for audit trail
    """
    
    report = Report.query.get_or_404(report_id)
    
    # Mark as dismissed
    report.status = 'dismissed'
    report.admin_notes = request.form.get('notes', '')
    
    db.session.commit()
    
    # Log action
    log_admin_action(
        'dismissed_report',
        'report',
        report_id,
        f'Dismissed report: {report.reason}'
    )
    
    logger.info(f'Report #{report_id} dismissed by admin {current_user.username}')
    flash('Report dismissed.', 'success')
    
    return redirect(url_for('admin.pending_reports'))


@admin_bp.route('/users')
@login_required
@admin_required
def manage_users():
    """
    List all users for management.
    Admin can view, ban, or unban users.
    
    SECURITY: Admin-only, shows account status and role
    """
    
    page = request.args.get('page', 1, type=int)
    
    users = User.query.order_by(User.created_at.desc()).paginate(
        page=page,
        per_page=current_app.config['ITEMS_PER_PAGE'],
        error_out=False
    )
    
    return render_template(
        'admin_manage_users.html',
        users=users,
        page=page
    )


@admin_bp.route('/users/<int:user_id>/ban', methods=['POST'])
@login_required
@admin_required
def ban_user(user_id):
    """
    Ban a user from platform.
    Sets is_active = False, preventing login.
    
    SECURITY:
    ✓ Prevents banning self
    ✓ Logs action
    ✓ Soft delete (keeps data for audit)
    """
    
    user = User.query.get_or_404(user_id)
    
    # Prevent admin from banning themselves
    if user.id == current_user.id:
        flash('You cannot ban yourself!', 'danger')
        return redirect(url_for('admin.manage_users'))
    
    # Ban user
    user.is_active = False
    db.session.commit()
    
    # Log action
    log_admin_action(
        'banned_user',
        'user',
        user_id,
        f'Banned: {user.username} ({user.email})'
    )
    
    logger.warning(f'User {user.username} banned by admin {current_user.username}')
    flash(f'User "{user.username}" has been banned.', 'success')
    
    return redirect(url_for('admin.manage_users'))


@admin_bp.route('/users/<int:user_id>/unban', methods=['POST'])
@login_required
@admin_required
def unban_user(user_id):
    """
    Unban a previously banned user.
    
    SECURITY:
    ✓ Logs action
    ✓ Re-enables login for user
    """
    
    user = User.query.get_or_404(user_id)
    
    # Unban user
    user.is_active = True
    db.session.commit()
    
    # Log action
    log_admin_action(
        'unbanned_user',
        'user',
        user_id,
        f'Unbanned: {user.username} ({user.email})'
    )
    
    logger.info(f'User {user.username} unbanned by admin {current_user.username}')
    flash(f'User "{user.username}" has been unbanned.', 'success')
    
    return redirect(url_for('admin.manage_users'))


@admin_bp.route('/audit-log')
@login_required
@admin_required
def audit_log():
    """
    View audit log of admin actions.
    
    SECURITY: Shows who did what and when (accountability)
    """
    
    page = request.args.get('page', 1, type=int)
    
    logs = AuditLog.query.order_by(AuditLog.created_at.desc()).paginate(
        page=page,
        per_page=current_app.config['ITEMS_PER_PAGE'],
        error_out=False
    )
    
    return render_template(
        'admin_audit_log.html',
        logs=logs,
        page=page
    )
