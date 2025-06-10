from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import re
from datetime import datetime, timedelta
import secrets

from .models.user import db, User, PasswordReset, ActivityLog

auth_bp = Blueprint('auth', __name__)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def init_app(app):
    login_manager.init_app(app)

# Password validation function
def is_password_valid(password):
    """
    Check if password meets security requirements:
    - At least 10 characters
    - Contains uppercase, lowercase, number, and symbol
    """
    if len(password) < 10:
        return False
    
    if not re.search(r'[A-Z]', password):  # Uppercase
        return False
    
    if not re.search(r'[a-z]', password):  # Lowercase
        return False
    
    if not re.search(r'[0-9]', password):  # Number
        return False
    
    if not re.search(r'[^A-Za-z0-9]', password):  # Symbol
        return False
    
    return True

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = 'remember' in request.form
        
        user = User.query.filter_by(username=username).first()
        
        # Check if user exists and password is correct
        if not user or not user.check_password(password):
            flash('Invalid username or password', 'danger')
            return render_template('login.html')
        
        # Check if user is active
        if not user.is_active:
            flash('Your account has been deactivated. Please contact an administrator.', 'danger')
            return render_template('login.html')
        
        # Check if password is expired
        if user.is_password_expired():
            # Generate password reset token
            token = secrets.token_urlsafe(32)
            expiry = datetime.utcnow() + timedelta(hours=24)
            
            reset = PasswordReset(user_id=user.id, reset_token=token, expiry=expiry)
            db.session.add(reset)
            db.session.commit()
            
            flash('Your password has expired. Please reset your password.', 'warning')
            return redirect(url_for('auth.reset_password', token=token))
        
        # Log the user in
        login_user(user, remember=remember)
        
        # Update last login time
        user.last_login = datetime.utcnow()
        
        # Log activity
        user.log_activity('login', ip_address=request.remote_addr)
        
        db.session.commit()
        
        # Redirect to requested page or dashboard
        next_page = request.args.get('next')
        if next_page and next_page.startswith('/'):
            return redirect(next_page)
        return redirect(url_for('main.dashboard'))
    
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    # Log activity before logout
    current_user.log_activity('logout', ip_address=request.remote_addr)
    
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        
        if user:
            # Generate token
            token = secrets.token_urlsafe(32)
            expiry = datetime.utcnow() + timedelta(hours=24)
            
            reset = PasswordReset(user_id=user.id, reset_token=token, expiry=expiry)
            db.session.add(reset)
            db.session.commit()
            
            # In a real app, send email with reset link
            # For now, just redirect to reset page with token
            flash('Password reset link has been sent to your email.', 'info')
            
            # For demo purposes, redirect directly to reset page
            return redirect(url_for('auth.reset_password', token=token))
        
        flash('If that email exists in our system, a password reset link has been sent.', 'info')
        return redirect(url_for('auth.login'))
    
    return render_template('reset_password_request.html')

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    # Find the reset token
    reset = PasswordReset.query.filter_by(reset_token=token, used=False).first()
    
    if not reset or reset.is_expired():
        flash('Invalid or expired password reset link.', 'danger')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('reset_password.html', token=token)
        
        if not is_password_valid(password):
            flash('Password must be at least 10 characters and include uppercase, lowercase, number, and symbol.', 'danger')
            return render_template('reset_password.html', token=token)
        
        user = User.query.get(reset.user_id)
        
        # Check if password is in history
        if user.is_password_in_history(password):
            flash('You cannot reuse one of your last 5 passwords.', 'danger')
            return render_template('reset_password.html', token=token)
        
        # Set new password
        user.set_password(password)
        
        # Mark token as used
        reset.used = True
        
        # Log activity
        user.log_activity('password_reset', ip_address=request.remote_addr)
        
        db.session.commit()
        
        flash('Your password has been reset. You can now log in with your new password.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('reset_password.html', token=token)

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not current_user.check_password(current_password):
            flash('Current password is incorrect.', 'danger')
            return render_template('change_password.html')
        
        if new_password != confirm_password:
            flash('New passwords do not match.', 'danger')
            return render_template('change_password.html')
        
        if not is_password_valid(new_password):
            flash('Password must be at least 10 characters and include uppercase, lowercase, number, and symbol.', 'danger')
            return render_template('change_password.html')
        
        # Check if password is in history
        if current_user.is_password_in_history(new_password):
            flash('You cannot reuse one of your last 5 passwords.', 'danger')
            return render_template('change_password.html')
        
        # Set new password
        current_user.set_password(new_password)
        
        # Log activity
        current_user.log_activity('password_change', ip_address=request.remote_addr)
        
        db.session.commit()
        
        flash('Your password has been changed.', 'success')
        return redirect(url_for('main.dashboard'))
    
    return render_template('change_password.html')
