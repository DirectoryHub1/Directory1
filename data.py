from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func
import json

from .models.user import db, User, Tool, ActivityLog
from .models.content import Business

# Create blueprint for data visualization routes
data_bp = Blueprint('data', __name__, url_prefix='/data')

@data_bp.route('/state-distribution')
@login_required
def state_distribution():
    """Get business distribution by state"""
    # Query the database for businesses grouped by state
    state_counts = db.session.query(
        Business.state, 
        func.count(Business.id).label('count')
    ).group_by(Business.state).order_by(func.count(Business.id).desc()).all()
    
    # Format data for Chart.js
    labels = [state[0] for state in state_counts]
    data = [state[1] for state in state_counts]
    
    # Generate color gradient based on number of states
    colors = generate_blue_gradient(len(labels))
    
    # Log this activity
    current_user.log_activity('viewed_state_distribution')
    
    return jsonify({
        'labels': labels,
        'datasets': [{
            'label': 'Businesses by State',
            'data': data,
            'backgroundColor': [f'rgba({r}, {g}, {b}, 0.8)' for r, g, b in colors],
            'borderColor': [f'rgba({r}, {g}, {b}, 1)' for r, g, b in colors],
            'borderWidth': 1
        }]
    })

@data_bp.route('/state-distribution/<business_type>')
@login_required
def state_distribution_by_type(business_type):
    """Get business distribution by state for a specific business type"""
    # Query the database for businesses of a specific type grouped by state
    state_counts = db.session.query(
        Business.state, 
        func.count(Business.id).label('count')
    ).filter(Business.type == business_type).group_by(Business.state).order_by(func.count(Business.id).desc()).all()
    
    # Format data for Chart.js
    labels = [state[0] for state in state_counts]
    data = [state[1] for state in state_counts]
    
    # Generate color gradient based on number of states
    colors = generate_blue_gradient(len(labels))
    
    # Log this activity
    current_user.log_activity('viewed_state_distribution_by_type', details=f'Business type: {business_type}')
    
    return jsonify({
        'labels': labels,
        'datasets': [{
            'label': f'{business_type} by State',
            'data': data,
            'backgroundColor': [f'rgba({r}, {g}, {b}, 0.8)' for r, g, b in colors],
            'borderColor': [f'rgba({r}, {g}, {b}, 1)' for r, g, b in colors],
            'borderWidth': 1
        }]
    })

@data_bp.route('/business-types')
@login_required
def business_types():
    """Get distribution of business types"""
    # Query the database for businesses grouped by type
    type_counts = db.session.query(
        Business.type, 
        func.count(Business.id).label('count')
    ).group_by(Business.type).order_by(func.count(Business.id).desc()).all()
    
    # Format data for Chart.js
    labels = [type_[0] for type_ in type_counts]
    data = [type_[1] for type_ in type_counts]
    
    # Generate color gradient based on number of types
    colors = generate_blue_gradient(len(labels))
    
    # Log this activity
    current_user.log_activity('viewed_business_types_distribution')
    
    return jsonify({
        'labels': labels,
        'datasets': [{
            'label': 'Business Types',
            'data': data,
            'backgroundColor': [f'rgba({r}, {g}, {b}, 0.8)' for r, g, b in colors],
            'borderColor': [f'rgba({r}, {g}, {b}, 1)' for r, g, b in colors],
            'borderWidth': 1
        }]
    })

@data_bp.route('/recent-activity')
@login_required
def recent_activity():
    """Get recent activity data"""
    # Query for recent activity logs
    if current_user.is_admin:
        # Admins see all activity
        logs = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).limit(10).all()
    elif current_user.is_manager:
        # Managers see activity from staff and themselves
        staff_ids = [user.id for user in User.query.filter_by(role='Staff').all()]
        staff_ids.append(current_user.id)
        logs = ActivityLog.query.filter(ActivityLog.user_id.in_(staff_ids)).order_by(ActivityLog.timestamp.desc()).limit(10).all()
    else:
        # Staff only see their own activity
        logs = ActivityLog.query.filter_by(user_id=current_user.id).order_by(ActivityLog.timestamp.desc()).limit(10).all()
    
    # Format data for frontend
    activity_data = [{
        'id': log.id,
        'user': log.user.username,
        'action': log.action,
        'timestamp': log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        'details': log.details
    } for log in logs]
    
    return jsonify(activity_data)

def generate_blue_gradient(count):
    """Generate a blue gradient color palette with the specified number of colors"""
    # Start with a deep blue and gradually lighten it
    start_color = (30, 87, 153)  # RGB for a deep blue
    end_color = (125, 185, 235)  # RGB for a light blue
    
    colors = []
    for i in range(count):
        # Calculate the interpolation factor
        factor = i / (count - 1) if count > 1 else 0
        
        # Interpolate between start and end colors
        r = int(start_color[0] + factor * (end_color[0] - start_color[0]))
        g = int(start_color[1] + factor * (end_color[1] - start_color[1]))
        b = int(start_color[2] + factor * (end_color[2] - start_color[2]))
        
        colors.append((r, g, b))
    
    return colors

# For testing/development when no real data is available
@data_bp.route('/sample-state-distribution')
@login_required
def sample_state_distribution():
    """Get sample business distribution by state for development/testing"""
    # Sample data representing business distribution across states
    sample_data = {
        'labels': ['California', 'Texas', 'Florida', 'New York', 'Illinois', 
                  'Pennsylvania', 'Ohio', 'Georgia', 'North Carolina', 'Michigan'],
        'datasets': [{
            'label': 'Businesses by State',
            'data': [24, 18, 16, 14, 12, 10, 9, 8, 7, 6],
            'backgroundColor': [
                'rgba(41, 137, 216, 0.8)',
                'rgba(35, 123, 202, 0.8)',
                'rgba(30, 110, 188, 0.8)',
                'rgba(26, 96, 173, 0.8)',
                'rgba(22, 83, 159, 0.8)',
                'rgba(18, 70, 145, 0.8)',
                'rgba(14, 57, 130, 0.8)',
                'rgba(11, 44, 116, 0.8)',
                'rgba(8, 31, 102, 0.8)',
                'rgba(5, 18, 87, 0.8)'
            ],
            'borderColor': [
                'rgba(41, 137, 216, 1)',
                'rgba(35, 123, 202, 1)',
                'rgba(30, 110, 188, 1)',
                'rgba(26, 96, 173, 1)',
                'rgba(22, 83, 159, 1)',
                'rgba(18, 70, 145, 1)',
                'rgba(14, 57, 130, 1)',
                'rgba(11, 44, 116, 1)',
                'rgba(8, 31, 102, 1)',
                'rgba(5, 18, 87, 1)'
            ],
            'borderWidth': 1
        }]
    }
    
    # Log this activity
    current_user.log_activity('viewed_sample_state_distribution')
    
    return jsonify(sample_data)
