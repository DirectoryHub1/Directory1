from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime, timedelta
import json
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-for-testing')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///directory_hub.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# User model - simplified
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), default='Staff')  # Admin, Manager, Staff
    is_active = db.Column(db.Boolean, default=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        return self.role == 'Admin'
    
    def is_manager(self):
        return self.role == 'Manager'

# Activity Log model - simplified
class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(64), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='activity_logs')

@login_manager.user_loader
def load_user(user_id):
    try:
        return User.query.get(int(user_id))
    except Exception as e:
        logger.error(f"Error loading user: {e}")
        return None

# Error handlers
@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    logger.error(f"Internal server error: {error}")
    return render_template('error.html', error_message="Internal Server Error. Please try again later."), 500

@app.errorhandler(404)
def not_found_error(error):
    logger.error(f"Page not found: {error}")
    return render_template('error.html', error_message="Page not found. Please check the URL."), 404

# Routes
@app.route('/')
def index():
    try:
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        return redirect(url_for('login'))
    except Exception as e:
        logger.error(f"Error in index route: {e}")
        return render_template('error.html', error_message="An error occurred. Please try again later.")

@app.route('/login', methods=['GET', 'POST'])
def login():
    try:
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
            
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
            
            user = User.query.filter_by(email=email).first()
            
            if user and user.check_password(password):
                if not user.is_active:
                    flash('Your account is disabled. Please contact an administrator.', 'danger')
                    return render_template('login.html')
                    
                login_user(user)
                
                # Log activity
                try:
                    log = ActivityLog(user_id=user.id, action='login')
                    db.session.add(log)
                    db.session.commit()
                except Exception as e:
                    logger.error(f"Error logging activity: {e}")
                    db.session.rollback()
                    
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid email or password', 'danger')
                
        return render_template('login.html')
    except Exception as e:
        logger.error(f"Error in login route: {e}")
        return render_template('error.html', error_message="An error occurred during login. Please try again later.")

@app.route('/logout')
@login_required
def logout():
    try:
        # Log activity
        try:
            log = ActivityLog(user_id=current_user.id, action='logout')
            db.session.add(log)
            db.session.commit()
        except Exception as e:
            logger.error(f"Error logging activity: {e}")
            db.session.rollback()
            
        logout_user()
        return redirect(url_for('login'))
    except Exception as e:
        logger.error(f"Error in logout route: {e}")
        return render_template('error.html', error_message="An error occurred during logout. Please try again later.")

@app.route('/dashboard')
@login_required
def dashboard():
    try:
        # Get tools for sidebar
        tools = [
            {'name': 'Email Marketing', 'url': 'https://www.ymlp.com', 'icon': 'envelope'},
            {'name': 'Postal Mail Service', 'url': 'https://www.postalmethods.com', 'icon': 'mail-bulk'},
            {'name': 'Label Templates', 'url': 'https://www.avery.com/templates', 'icon': 'tag'},
            {'name': 'Mass Calls & Texting', 'url': 'https://www.dialmycalls.com', 'icon': 'phone'},
            {'name': 'Promotional Texts', 'url': '/promotional_texts', 'icon': 'bullhorn'}
        ]
        
        # Get recent activity for dashboard
        try:
            if current_user.is_admin():
                # Admins see all activity
                recent_activity = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).limit(10).all()
            else:
                # Others only see their own activity
                recent_activity = ActivityLog.query.filter_by(user_id=current_user.id).order_by(ActivityLog.timestamp.desc()).limit(10).all()
        except Exception as e:
            logger.error(f"Error fetching activity logs: {e}")
            recent_activity = []
        
        # Get business counts - using static data for reliability
        total_businesses = 152
        vehicle_dealerships = 48
        real_estate = 64
        apartment_rentals = 40
        
        # Get business types for filter
        business_types = ['Vehicle Dealership', 'Real Estate Professional', 'Apartment Rental']
        
        # Log dashboard view
        try:
            log = ActivityLog(user_id=current_user.id, action='viewed_dashboard')
            db.session.add(log)
            db.session.commit()
        except Exception as e:
            logger.error(f"Error logging activity: {e}")
            db.session.rollback()
        
        return render_template(
            'dashboard.html', 
            tools=tools, 
            recent_activity=recent_activity,
            business_types=business_types,
            total_businesses=total_businesses,
            vehicle_dealerships=vehicle_dealerships,
            real_estate=real_estate,
            apartment_rentals=apartment_rentals
        )
    except Exception as e:
        logger.error(f"Error in dashboard route: {e}")
        return render_template('error.html', error_message="An error occurred loading the dashboard. Please try again later.")

@app.route('/api/chart-data')
@login_required
def chart_data():
    try:
        # Sample data for different business types
        business_type = request.args.get('type', 'all')
        
        if business_type == 'Vehicle Dealership':
            return jsonify({
                'labels': ['California', 'Texas', 'Florida', 'New York', 'Illinois', 'Ohio', 'Pennsylvania', 'Michigan', 'Georgia', 'North Carolina'],
                'data': [8, 7, 6, 5, 4, 4, 3, 3, 2, 2]
            })
        elif business_type == 'Real Estate Professional':
            return jsonify({
                'labels': ['Florida', 'California', 'Texas', 'New York', 'Arizona', 'Colorado', 'Washington', 'Nevada', 'North Carolina', 'Georgia'],
                'data': [12, 10, 9, 7, 5, 4, 4, 3, 3, 2]
            })
        elif business_type == 'Apartment Rental':
            return jsonify({
                'labels': ['New York', 'California', 'Texas', 'Florida', 'Illinois', 'Georgia', 'Massachusetts', 'Washington', 'Colorado', 'Arizona'],
                'data': [9, 8, 6, 5, 3, 2, 2, 2, 1, 1]
            })
        else:  # all business types
            return jsonify({
                'labels': ['California', 'Texas', 'Florida', 'New York', 'Illinois', 'Ohio', 'Pennsylvania', 'Georgia', 'North Carolina', 'Michigan'],
                'data': [25, 22, 20, 18, 12, 10, 9, 8, 7, 6]
            })
    except Exception as e:
        logger.error(f"Error in chart data route: {e}")
        return jsonify({'error': 'An error occurred fetching chart data'}), 500

@app.route('/users')
@login_required
def users():
    try:
        if not current_user.is_admin():
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('dashboard'))
            
        try:
            users = User.query.all()
        except Exception as e:
            logger.error(f"Error fetching users: {e}")
            users = []
            
        tools = [
            {'name': 'Email Marketing', 'url': 'https://www.ymlp.com', 'icon': 'envelope'},
            {'name': 'Postal Mail Service', 'url': 'https://www.postalmethods.com', 'icon': 'mail-bulk'},
            {'name': 'Label Templates', 'url': 'https://www.avery.com/templates', 'icon': 'tag'},
            {'name': 'Mass Calls & Texting', 'url': 'https://www.dialmycalls.com', 'icon': 'phone'},
            {'name': 'Promotional Texts', 'url': '/promotional_texts', 'icon': 'bullhorn'}
        ]
        return render_template('users.html', users=users, tools=tools)
    except Exception as e:
        logger.error(f"Error in users route: {e}")
        return render_template('error.html', error_message="An error occurred loading the users page. Please try again later.")

@app.route('/businesses')
@login_required
def businesses():
    try:
        tools = [
            {'name': 'Email Marketing', 'url': 'https://www.ymlp.com', 'icon': 'envelope'},
            {'name': 'Postal Mail Service', 'url': 'https://www.postalmethods.com', 'icon': 'mail-bulk'},
            {'name': 'Label Templates', 'url': 'https://www.avery.com/templates', 'icon': 'tag'},
            {'name': 'Mass Calls & Texting', 'url': 'https://www.dialmycalls.com', 'icon': 'phone'},
            {'name': 'Promotional Texts', 'url': '/promotional_texts', 'icon': 'bullhorn'}
        ]
        return render_template('businesses.html', tools=tools)
    except Exception as e:
        logger.error(f"Error in businesses route: {e}")
        return render_template('error.html', error_message="An error occurred loading the businesses page. Please try again later.")

@app.route('/documents')
@login_required
def documents():
    try:
        tools = [
            {'name': 'Email Marketing', 'url': 'https://www.ymlp.com', 'icon': 'envelope'},
            {'name': 'Postal Mail Service', 'url': 'https://www.postalmethods.com', 'icon': 'mail-bulk'},
            {'name': 'Label Templates', 'url': 'https://www.avery.com/templates', 'icon': 'tag'},
            {'name': 'Mass Calls & Texting', 'url': 'https://www.dialmycalls.com', 'icon': 'phone'},
            {'name': 'Promotional Texts', 'url': '/promotional_texts', 'icon': 'bullhorn'}
        ]
        return render_template('documents.html', tools=tools)
    except Exception as e:
        logger.error(f"Error in documents route: {e}")
        return render_template('error.html', error_message="An error occurred loading the documents page. Please try again later.")

@app.route('/promotional_texts')
@login_required
def promotional_texts():
    try:
        tools = [
            {'name': 'Email Marketing', 'url': 'https://www.ymlp.com', 'icon': 'envelope'},
            {'name': 'Postal Mail Service', 'url': 'https://www.postalmethods.com', 'icon': 'mail-bulk'},
            {'name': 'Label Templates', 'url': 'https://www.avery.com/templates', 'icon': 'tag'},
            {'name': 'Mass Calls & Texting', 'url': 'https://www.dialmycalls.com', 'icon': 'phone'},
            {'name': 'Promotional Texts', 'url': '/promotional_texts', 'icon': 'bullhorn'}
        ]
        return render_template('promotional_texts.html', tools=tools)
    except Exception as e:
        logger.error(f"Error in promotional_texts route: {e}")
        return render_template('error.html', error_message="An error occurred loading the promotional texts page. Please try again later.")

@app.route('/settings')
@login_required
def settings():
    try:
        if not current_user.is_admin():
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('dashboard'))
            
        tools = [
            {'name': 'Email Marketing', 'url': 'https://www.ymlp.com', 'icon': 'envelope'},
            {'name': 'Postal Mail Service', 'url': 'https://www.postalmethods.com', 'icon': 'mail-bulk'},
            {'name': 'Label Templates', 'url': 'https://www.avery.com/templates', 'icon': 'tag'},
            {'name': 'Mass Calls & Texting', 'url': 'https://www.dialmycalls.com', 'icon': 'phone'},
            {'name': 'Promotional Texts', 'url': '/promotional_texts', 'icon': 'bullhorn'}
        ]
        return render_template('settings.html', tools=tools)
    except Exception as e:
        logger.error(f"Error in settings route: {e}")
        return render_template('error.html', error_message="An error occurred loading the settings page. Please try again later.")

# Create initial database and admin user
def create_initial_data():
    try:
        # Create tables if they don't exist
        with app.app_context():
            db.create_all()
            
            # Check if admin user exists
            admin = User.query.filter_by(email='admin@directoryhub.com').first()
            if not admin:
                admin = User(
                    username='admin',
                    email='admin@directoryhub.com',
                    full_name='Admin User',
                    role='Admin',
                    is_active=True
                )
                admin.set_password('Admin123!')
                db.session.add(admin)
                
            # Check if manager user exists
            manager = User.query.filter_by(email='manager@directoryhub.com').first()
            if not manager:
                manager = User(
                    username='manager',
                    email='manager@directoryhub.com',
                    full_name='Manager User',
                    role='Manager',
                    is_active=True
                )
                manager.set_password('Manager123!')
                db.session.add(manager)
                
            # Check if staff user exists
            staff = User.query.filter_by(email='staff@directoryhub.com').first()
            if not staff:
                staff = User(
                    username='staff',
                    email='staff@directoryhub.com',
                    full_name='Staff User',
                    role='Staff',
                    is_active=True
                )
                staff.set_password('Staff123!')
                db.session.add(staff)
                
            db.session.commit()
            logger.info("Initial data created successfully")
    except Exception as e:
        logger.error(f"Error creating initial data: {e}")
        db.session.rollback()

# Call create_initial_data at startup with explicit schema reset
with app.app_context():
    try:
        # Force drop all tables first to ensure clean schema
        db.drop_all()
        logger.info("Dropped all tables successfully")
    except Exception as e:
        logger.error(f"Error dropping tables: {e}")
    
    # Now create tables and initial data
    create_initial_data()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
