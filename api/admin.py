from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
import secrets
from datetime import datetime, timedelta

from .models.user import db, User, Tool, Permission, ActivityLog
from .auth import is_password_valid

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Admin required decorator
def admin_required(f):
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# Manager or admin required decorator
def manager_required(f):
    @login_required
    def decorated_function(*args, **kwargs):
        if not (current_user.is_admin or current_user.is_manager):
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@admin_bp.route('/')
@admin_required
def index():
    return render_template('admin/index.html')

# User Management Routes
@admin_bp.route('/users')
@admin_required
def users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/users/new', methods=['GET', 'POST'])
@admin_required
def new_user():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        phone_number = request.form.get('phone_number')
        department = request.form.get('department')
        role = request.form.get('role')
        
        # Validate input
        if not username or not email or not password or not full_name or not role:
            flash('All required fields must be filled out.', 'danger')
            return render_template('admin/new_user.html')
        
        # Check if username or email already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'danger')
            return render_template('admin/new_user.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists.', 'danger')
            return render_template('admin/new_user.html')
        
        # Validate password
        if not is_password_valid(password):
            flash('Password must be at least 10 characters and include uppercase, lowercase, number, and symbol.', 'danger')
            return render_template('admin/new_user.html')
        
        # Create new user
        user = User(
            username=username,
            email=email,
            full_name=full_name,
            phone_number=phone_number,
            department=department,
            role=role
        )
        user.set_password(password)
        
        db.session.add(user)
        
        # Log activity
        current_user.log_activity(
            'user_created', 
            details=f'Created user {username} with role {role}',
            ip_address=request.remote_addr
        )
        
        db.session.commit()
        
        flash(f'User {username} has been created.', 'success')
        return redirect(url_for('admin.users'))
    
    return render_template('admin/new_user.html')

@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    
    # Prevent editing own user through this route
    if user.id == current_user.id:
        flash('You cannot edit your own user through this page. Use profile settings instead.', 'warning')
        return redirect(url_for('admin.users'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        full_name = request.form.get('full_name')
        phone_number = request.form.get('phone_number')
        department = request.form.get('department')
        role = request.form.get('role')
        is_active = 'is_active' in request.form
        
        # Validate input
        if not username or not email or not full_name or not role:
            flash('All required fields must be filled out.', 'danger')
            return render_template('admin/edit_user.html', user=user)
        
        # Check if username already exists (for another user)
        existing_user = User.query.filter_by(username=username).first()
        if existing_user and existing_user.id != user.id:
            flash('Username already exists.', 'danger')
            return render_template('admin/edit_user.html', user=user)
        
        # Check if email already exists (for another user)
        existing_user = User.query.filter_by(email=email).first()
        if existing_user and existing_user.id != user.id:
            flash('Email already exists.', 'danger')
            return render_template('admin/edit_user.html', user=user)
        
        # Update user
        user.username = username
        user.email = email
        user.full_name = full_name
        user.phone_number = phone_number
        user.department = department
        user.role = role
        user.is_active = is_active
        
        # Log activity
        current_user.log_activity(
            'user_updated', 
            details=f'Updated user {username}',
            ip_address=request.remote_addr
        )
        
        db.session.commit()
        
        flash(f'User {username} has been updated.', 'success')
        return redirect(url_for('admin.users'))
    
    return render_template('admin/edit_user.html', user=user)

@admin_bp.route('/users/<int:user_id>/reset-password', methods=['GET', 'POST'])
@admin_required
def reset_user_password(user_id):
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('admin/reset_user_password.html', user=user)
        
        if not is_password_valid(password):
            flash('Password must be at least 10 characters and include uppercase, lowercase, number, and symbol.', 'danger')
            return render_template('admin/reset_user_password.html', user=user)
        
        # Set new password
        user.set_password(password)
        
        # Log activity
        current_user.log_activity(
            'password_reset_by_admin', 
            details=f'Reset password for user {user.username}',
            ip_address=request.remote_addr
        )
        
        db.session.commit()
        
        flash(f'Password for {user.username} has been reset.', 'success')
        return redirect(url_for('admin.users'))
    
    return render_template('admin/reset_user_password.html', user=user)

@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    # Prevent deleting own user
    if user.id == current_user.id:
        flash('You cannot delete your own user.', 'danger')
        return redirect(url_for('admin.users'))
    
    username = user.username
    
    # Log activity before deletion
    current_user.log_activity(
        'user_deleted', 
        details=f'Deleted user {username}',
        ip_address=request.remote_addr
    )
    
    db.session.delete(user)
    db.session.commit()
    
    flash(f'User {username} has been deleted.', 'success')
    return redirect(url_for('admin.users'))

# Permission Management Routes
@admin_bp.route('/permissions')
@admin_required
def permissions():
    users = User.query.all()
    tools = Tool.query.all()
    return render_template('admin/permissions.html', users=users, tools=tools)

@admin_bp.route('/permissions/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def user_permissions(user_id):
    user = User.query.get_or_404(user_id)
    tools = Tool.query.all()
    
    if request.method == 'POST':
        # Clear existing permissions
        Permission.query.filter_by(user_id=user.id).delete()
        
        # Add new permissions
        for tool in tools:
            if f'tool_{tool.id}' in request.form:
                permission = Permission(user_id=user.id, tool_id=tool.id, can_access=True)
                db.session.add(permission)
        
        # Log activity
        current_user.log_activity(
            'permissions_updated', 
            details=f'Updated permissions for user {user.username}',
            ip_address=request.remote_addr
        )
        
        db.session.commit()
        
        flash(f'Permissions for {user.username} have been updated.', 'success')
        return redirect(url_for('admin.permissions'))
    
    # Get current permissions
    user_permissions = {p.tool_id: p.can_access for p in user.permissions}
    
    return render_template('admin/user_permissions.html', user=user, tools=tools, user_permissions=user_permissions)

# Activity Log Routes
@admin_bp.route('/activity-log')
@admin_required
def activity_log():
    logs = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).limit(100).all()
    return render_template('admin/activity_log.html', logs=logs)

@admin_bp.route('/activity-log/filter', methods=['GET', 'POST'])
@admin_required
def filter_activity_log():
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        action = request.form.get('action')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        
        query = ActivityLog.query
        
        if user_id and user_id != 'all':
            query = query.filter_by(user_id=user_id)
        
        if action and action != 'all':
            query = query.filter_by(action=action)
        
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(ActivityLog.timestamp >= start_date)
        
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
            end_date = end_date + timedelta(days=1)  # Include the entire day
            query = query.filter(ActivityLog.timestamp <= end_date)
        
        logs = query.order_by(ActivityLog.timestamp.desc()).all()
        
        return render_template('admin/activity_log.html', logs=logs, filters={
            'user_id': user_id,
            'action': action,
            'start_date': start_date,
            'end_date': end_date
        })
    
    users = User.query.all()
    actions = db.session.query(ActivityLog.action).distinct().all()
    actions = [a[0] for a in actions]
    
    return render_template('admin/filter_activity_log.html', users=users, actions=actions)

# System Settings Routes
@admin_bp.route('/settings')
@admin_required
def settings():
    return render_template('admin/settings.html')

# API Routes for AJAX
@admin_bp.route('/api/users')
@admin_required
def api_users():
    users = User.query.all()
    return jsonify([{
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'full_name': user.full_name,
        'role': user.role,
        'is_active': user.is_active
    } for user in users])

@admin_bp.route('/api/activity-log')
@admin_required
def api_activity_log():
    logs = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).limit(100).all()
    return jsonify([{
        'id': log.id,
        'user_id': log.user_id,
        'username': log.user.username,
        'action': log.action,
        'timestamp': log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        'details': log.details,
        'ip_address': log.ip_address
    } for log in logs])
