from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
import os
from datetime import datetime

from .models.user import db, User, Tool, ActivityLog
from .models.content import Business

# Create blueprint for testing routes
test_bp = Blueprint('test', __name__, url_prefix='/test')

@test_bp.route('/user-roles')
@login_required
def test_user_roles():
    """Test page for validating user roles and permissions"""
    if not current_user.is_admin:
        flash('This test page is only accessible to administrators.', 'warning')
        return redirect(url_for('main.dashboard'))
    
    # Get all users
    users = User.query.all()
    
    # Get all tools
    tools = Tool.query.all()
    
    # Get permissions for each user
    user_permissions = {}
    for user in users:
        user_permissions[user.id] = {
            'role': user.role,
            'permissions': {tool.id: user.has_permission(tool.id) for tool in tools}
        }
    
    return render_template('test/user_roles.html', users=users, tools=tools, user_permissions=user_permissions)

@test_bp.route('/password-policy')
@login_required
def test_password_policy():
    """Test page for validating password policy implementation"""
    if not current_user.is_admin:
        flash('This test page is only accessible to administrators.', 'warning')
        return redirect(url_for('main.dashboard'))
    
    # Sample passwords to test
    test_passwords = [
        {'password': 'password', 'should_pass': False, 'reason': 'Too short, no uppercase, no number, no symbol'},
        {'password': 'Password123', 'should_pass': False, 'reason': 'No symbol'},
        {'password': 'password123!', 'should_pass': False, 'reason': 'No uppercase'},
        {'password': 'PASSWORD123!', 'should_pass': False, 'reason': 'No lowercase'},
        {'password': 'Password!', 'should_pass': False, 'reason': 'No number'},
        {'password': 'Pa1!', 'should_pass': False, 'reason': 'Too short'},
        {'password': 'Password123!', 'should_pass': True, 'reason': 'Valid password'},
        {'password': 'SecureP@ssw0rd', 'should_pass': True, 'reason': 'Valid password'},
        {'password': 'C0mpl3x!P@ssw0rd', 'should_pass': True, 'reason': 'Valid password'}
    ]
    
    # Import password validation function
    from .auth import is_password_valid
    
    # Test each password
    for test in test_passwords:
        test['result'] = is_password_valid(test['password'])
        test['passed'] = test['result'] == test['should_pass']
    
    return render_template('test/password_policy.html', test_passwords=test_passwords)

@test_bp.route('/chart-data')
@login_required
def test_chart_data():
    """Test page for validating chart data generation"""
    if not current_user.is_admin:
        flash('This test page is only accessible to administrators.', 'warning')
        return redirect(url_for('main.dashboard'))
    
    # Get business distribution by state
    state_counts = db.session.query(
        Business.state, 
        func.count(Business.id).label('count')
    ).group_by(Business.state).order_by(func.count(Business.id).desc()).all()
    
    # Get business distribution by type
    type_counts = db.session.query(
        Business.type, 
        func.count(Business.id).label('count')
    ).group_by(Business.type).order_by(func.count(Business.id).desc()).all()
    
    return render_template('test/chart_data.html', state_counts=state_counts, type_counts=type_counts)

@test_bp.route('/mobile-compatibility')
@login_required
def test_mobile_compatibility():
    """Test page for validating mobile compatibility"""
    if not current_user.is_admin:
        flash('This test page is only accessible to administrators.', 'warning')
        return redirect(url_for('main.dashboard'))
    
    return render_template('test/mobile_compatibility.html')

@test_bp.route('/activity-logging')
@login_required
def test_activity_logging():
    """Test page for validating activity logging"""
    if not current_user.is_admin:
        flash('This test page is only accessible to administrators.', 'warning')
        return redirect(url_for('main.dashboard'))
    
    # Generate test activity
    current_user.log_activity('test_activity', details='Testing activity logging system')
    db.session.commit()
    
    # Get recent activity logs
    logs = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).limit(20).all()
    
    return render_template('test/activity_logging.html', logs=logs)

@test_bp.route('/run-all-tests')
@login_required
def run_all_tests():
    """Run all tests and generate a comprehensive report"""
    if not current_user.is_admin:
        flash('This test page is only accessible to administrators.', 'warning')
        return redirect(url_for('main.dashboard'))
    
    test_results = {
        'user_roles': test_user_roles_function(),
        'password_policy': test_password_policy_function(),
        'chart_data': test_chart_data_function(),
        'activity_logging': test_activity_logging_function()
    }
    
    # Calculate overall test status
    all_passed = all(result['status'] == 'passed' for result in test_results.values())
    
    return render_template('test/all_tests.html', test_results=test_results, all_passed=all_passed)

# Helper functions for tests
def test_user_roles_function():
    """Test user roles and permissions"""
    try:
        # Check if all roles exist
        admin = User.query.filter_by(role='Admin').first()
        manager = User.query.filter_by(role='Manager').first()
        staff = User.query.filter_by(role='Staff').first()
        
        if not admin or not manager or not staff:
            return {
                'status': 'failed',
                'message': 'Not all required roles exist in the database'
            }
        
        # Check admin permissions
        tools = Tool.query.all()
        for tool in tools:
            if not admin.has_permission(tool.id):
                return {
                    'status': 'failed',
                    'message': f'Admin user does not have permission for tool {tool.name}'
                }
        
        return {
            'status': 'passed',
            'message': 'User roles and permissions are correctly configured'
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Error testing user roles: {str(e)}'
        }

def test_password_policy_function():
    """Test password policy implementation"""
    try:
        from .auth import is_password_valid
        
        # Test valid passwords
        valid_passwords = ['Password123!', 'SecureP@ssw0rd', 'C0mpl3x!P@ssw0rd']
        for password in valid_passwords:
            if not is_password_valid(password):
                return {
                    'status': 'failed',
                    'message': f'Valid password "{password}" was rejected'
                }
        
        # Test invalid passwords
        invalid_passwords = ['password', 'Password', 'password123', 'PASSWORD123!', 'Pass!']
        for password in invalid_passwords:
            if is_password_valid(password):
                return {
                    'status': 'failed',
                    'message': f'Invalid password "{password}" was accepted'
                }
        
        return {
            'status': 'passed',
            'message': 'Password policy is correctly implemented'
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Error testing password policy: {str(e)}'
        }

def test_chart_data_function():
    """Test chart data generation"""
    try:
        # Check if business data exists
        business_count = Business.query.count()
        if business_count == 0:
            return {
                'status': 'failed',
                'message': 'No business data found in the database'
            }
        
        # Check if state distribution data can be generated
        state_counts = db.session.query(
            Business.state, 
            func.count(Business.id).label('count')
        ).group_by(Business.state).all()
        
        if not state_counts:
            return {
                'status': 'failed',
                'message': 'Could not generate state distribution data'
            }
        
        return {
            'status': 'passed',
            'message': f'Chart data generation successful. Found {business_count} businesses across {len(state_counts)} states.'
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Error testing chart data: {str(e)}'
        }

def test_activity_logging_function():
    """Test activity logging system"""
    try:
        # Generate a test log
        test_user = User.query.first()
        test_user.log_activity('test_activity', details='Automated test of logging system')
        db.session.commit()
        
        # Check if the log was created
        log = ActivityLog.query.filter_by(action='test_activity').first()
        if not log:
            return {
                'status': 'failed',
                'message': 'Activity log was not created'
            }
        
        return {
            'status': 'passed',
            'message': 'Activity logging system is working correctly'
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Error testing activity logging: {str(e)}'
        }
