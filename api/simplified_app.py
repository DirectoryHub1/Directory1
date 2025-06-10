from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime, timedelta
import json

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-for-testing')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///directory_hub.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# User model
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20))
    department = db.Column(db.String(50))
    role = db.Column(db.String(20), default='Staff')  # Admin, Manager, Staff
    is_active = db.Column(db.Boolean, default=True)
    password_changed_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        self.password_changed_at = datetime.utcnow()
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_password_expired(self):
        # Check if password is older than 3 months
        if not self.password_changed_at:
            return True
        expiry_date = self.password_changed_at + timedelta(days=90)
        return datetime.utcnow() > expiry_date
    
    def is_admin(self):
        return self.role == 'Admin'
    
    def is_manager(self):
        return self.role == 'Manager'
    
    def log_activity(self, action, details=None):
        log = ActivityLog(user_id=self.id, action=action, details=details)
        db.session.add(log)
        
    def has_permission(self, tool_id):
        # Admin has all permissions
        if self.is_admin():
            return True
        
        # Check specific permissions
        permission = Permission.query.filter_by(user_id=self.id, tool_id=tool_id).first()
        if permission:
            return permission.has_access
        
        # Default permissions based on role
        tool = Tool.query.get(tool_id)
        if not tool:
            return False
            
        # Managers have access to most tools
        if self.is_manager():
            return True
            
        # Staff have access to basic tools
        return tool.staff_default_access

# Tool model
class Tool(db.Model):
    __tablename__ = 'tools'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.String(256))
    url = db.Column(db.String(256))
    icon = db.Column(db.String(20))
    staff_default_access = db.Column(db.Boolean, default=True)
    
# Permission model
class Permission(db.Model):
    __tablename__ = 'permissions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    tool_id = db.Column(db.Integer, db.ForeignKey('tools.id'), nullable=False)
    has_access = db.Column(db.Boolean, default=True)
    
# Activity Log model
class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(64), nullable=False)
    details = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))
    
    user = db.relationship('User', backref='activity_logs')

# Business model
class Business(db.Model):
    __tablename__ = 'businesses'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # Vehicle Dealership, Real Estate Professional, Apartment Rental
    state = db.Column(db.String(50), nullable=False)
    city = db.Column(db.String(50), nullable=False)
    address = db.Column(db.String(200))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    website = db.Column(db.String(200))
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
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
            user.last_login = datetime.utcnow()
            user.log_activity('login')
            db.session.commit()
            
            if user.is_password_expired():
                flash('Your password has expired. Please change it now.', 'warning')
                return redirect(url_for('change_password'))
                
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password', 'danger')
            
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    current_user.log_activity('logout')
    db.session.commit()
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Get tools for sidebar
    tools = Tool.query.all()
    
    # Get recent activity for dashboard
    if current_user.is_admin():
        # Admins see all activity
        recent_activity = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).limit(10).all()
    elif current_user.is_manager():
        # Managers see activity from staff and themselves
        staff_ids = [user.id for user in User.query.filter_by(role='Staff').all()]
        staff_ids.append(current_user.id)
        recent_activity = ActivityLog.query.filter(ActivityLog.user_id.in_(staff_ids)).order_by(ActivityLog.timestamp.desc()).limit(10).all()
    else:
        # Staff only see their own activity
        recent_activity = ActivityLog.query.filter_by(user_id=current_user.id).order_by(ActivityLog.timestamp.desc()).limit(10).all()
    
    # Get business counts
    total_businesses = Business.query.count()
    vehicle_dealerships = Business.query.filter_by(type='Vehicle Dealership').count()
    real_estate = Business.query.filter_by(type='Real Estate Professional').count()
    apartment_rentals = Business.query.filter_by(type='Apartment Rental').count()
    
    # Get business types for filter
    business_types = db.session.query(Business.type).distinct().all()
    business_types = [t[0] for t in business_types]
    
    # Log dashboard view
    current_user.log_activity('viewed_dashboard')
    db.session.commit()
    
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

@app.route('/api/chart-data')
@login_required
def chart_data():
    # Get business distribution by state
    state_data = db.session.query(
        Business.state, 
        db.func.count(Business.id).label('count')
    ).group_by(Business.state).order_by(db.func.count(Business.id).desc()).all()
    
    # Filter by business type if specified
    business_type = request.args.get('type')
    if business_type and business_type != 'all':
        state_data = db.session.query(
            Business.state, 
            db.func.count(Business.id).label('count')
        ).filter(Business.type == business_type).group_by(Business.state).order_by(db.func.count(Business.id).desc()).all()
    
    # Convert to dictionary
    data = {
        'labels': [s[0] for s in state_data],
        'data': [s[1] for s in state_data]
    }
    
    return json.dumps(data)

@app.route('/users')
@login_required
def users():
    if not current_user.is_admin():
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('dashboard'))
        
    users = User.query.all()
    return render_template('users.html', users=users)

@app.route('/users/new', methods=['GET', 'POST'])
@login_required
def new_user():
    if not current_user.is_admin():
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('dashboard'))
        
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
            flash('All required fields must be filled.', 'danger')
            return render_template('new_user.html')
            
        # Check if username or email already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'danger')
            return render_template('new_user.html')
            
        if User.query.filter_by(email=email).first():
            flash('Email already exists.', 'danger')
            return render_template('new_user.html')
            
        # Validate password
        if len(password) < 10:
            flash('Password must be at least 10 characters long.', 'danger')
            return render_template('new_user.html')
            
        if not any(c.isupper() for c in password):
            flash('Password must contain at least one uppercase letter.', 'danger')
            return render_template('new_user.html')
            
        if not any(c.islower() for c in password):
            flash('Password must contain at least one lowercase letter.', 'danger')
            return render_template('new_user.html')
            
        if not any(c.isdigit() for c in password):
            flash('Password must contain at least one number.', 'danger')
            return render_template('new_user.html')
            
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?/~`' for c in password):
            flash('Password must contain at least one special character.', 'danger')
            return render_template('new_user.html')
            
        # Create new user
        user = User(
            username=username,
            email=email,
            full_name=full_name,
            phone_number=phone_number,
            department=department,
            role=role,
            is_active=True
        )
        user.set_password(password)
        
        db.session.add(user)
        current_user.log_activity('created_user', details=f'Created user: {username}')
        db.session.commit()
        
        flash('User created successfully.', 'success')
        return redirect(url_for('users'))
        
    return render_template('new_user.html')

@app.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    if not current_user.is_admin():
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('dashboard'))
        
    user = User.query.get_or_404(user_id)
    
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
            flash('All required fields must be filled.', 'danger')
            return render_template('edit_user.html', user=user)
            
        # Check if username or email already exists (for another user)
        existing_user = User.query.filter_by(username=username).first()
        if existing_user and existing_user.id != user.id:
            flash('Username already exists.', 'danger')
            return render_template('edit_user.html', user=user)
            
        existing_user = User.query.filter_by(email=email).first()
        if existing_user and existing_user.id != user.id:
            flash('Email already exists.', 'danger')
            return render_template('edit_user.html', user=user)
            
        # Update user
        user.username = username
        user.email = email
        user.full_name = full_name
        user.phone_number = phone_number
        user.department = department
        user.role = role
        user.is_active = is_active
        
        current_user.log_activity('updated_user', details=f'Updated user: {username}')
        db.session.commit()
        
        flash('User updated successfully.', 'success')
        return redirect(url_for('users'))
        
    return render_template('edit_user.html', user=user)

@app.route('/users/<int:user_id>/reset-password', methods=['GET', 'POST'])
@login_required
def reset_password(user_id):
    if not current_user.is_admin():
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('dashboard'))
        
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        password = request.form.get('password')
        
        # Validate password
        if len(password) < 10:
            flash('Password must be at least 10 characters long.', 'danger')
            return render_template('reset_password.html', user=user)
            
        if not any(c.isupper() for c in password):
            flash('Password must contain at least one uppercase letter.', 'danger')
            return render_template('reset_password.html', user=user)
            
        if not any(c.islower() for c in password):
            flash('Password must contain at least one lowercase letter.', 'danger')
            return render_template('reset_password.html', user=user)
            
        if not any(c.isdigit() for c in password):
            flash('Password must contain at least one number.', 'danger')
            return render_template('reset_password.html', user=user)
            
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?/~`' for c in password):
            flash('Password must contain at least one special character.', 'danger')
            return render_template('reset_password.html', user=user)
            
        # Update password
        user.set_password(password)
        
        current_user.log_activity('reset_password', details=f'Reset password for user: {user.username}')
        db.session.commit()
        
        flash('Password reset successfully.', 'success')
        return redirect(url_for('users'))
        
    return render_template('reset_password.html', user=user)

@app.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate input
        if not current_user.check_password(current_password):
            flash('Current password is incorrect.', 'danger')
            return render_template('change_password.html')
            
        if new_password != confirm_password:
            flash('New passwords do not match.', 'danger')
            return render_template('change_password.html')
            
        # Validate password
        if len(new_password) < 10:
            flash('Password must be at least 10 characters long.', 'danger')
            return render_template('change_password.html')
            
        if not any(c.isupper() for c in new_password):
            flash('Password must contain at least one uppercase letter.', 'danger')
            return render_template('change_password.html')
            
        if not any(c.islower() for c in new_password):
            flash('Password must contain at least one lowercase letter.', 'danger')
            return render_template('change_password.html')
            
        if not any(c.isdigit() for c in new_password):
            flash('Password must contain at least one number.', 'danger')
            return render_template('change_password.html')
            
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?/~`' for c in new_password):
            flash('Password must contain at least one special character.', 'danger')
            return render_template('change_password.html')
            
        # Update password
        current_user.set_password(new_password)
        
        current_user.log_activity('changed_password')
        db.session.commit()
        
        flash('Password changed successfully.', 'success')
        return redirect(url_for('dashboard'))
        
    return render_template('change_password.html')

@app.route('/activity-log')
@login_required
def activity_log():
    if not current_user.is_admin() and not current_user.is_manager():
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('dashboard'))
        
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    if current_user.is_admin():
        # Admins see all activity
        logs = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).paginate(page=page, per_page=per_page)
    else:
        # Managers see activity from staff and themselves
        staff_ids = [user.id for user in User.query.filter_by(role='Staff').all()]
        staff_ids.append(current_user.id)
        logs = ActivityLog.query.filter(ActivityLog.user_id.in_(staff_ids)).order_by(ActivityLog.timestamp.desc()).paginate(page=page, per_page=per_page)
    
    current_user.log_activity('viewed_activity_log')
    db.session.commit()
    
    return render_template('activity_log.html', logs=logs)

@app.route('/businesses')
@login_required
def businesses():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    businesses = Business.query.paginate(page=page, per_page=per_page)
    
    current_user.log_activity('viewed_businesses')
    db.session.commit()
    
    return render_template('businesses.html', businesses=businesses)

@app.route('/businesses/<int:business_id>')
@login_required
def business_detail(business_id):
    business = Business.query.get_or_404(business_id)
    
    current_user.log_activity('viewed_business_detail', details=f'Business ID: {business_id}')
    db.session.commit()
    
    return render_template('business_detail.html', business=business)

# Create default data
def create_default_data():
    # Create default tools if they don't exist
    default_tools = [
        {
            'name': 'Email Marketing',
            'description': 'Use our directory data for targeted email marketing campaigns.',
            'url': 'https://ymlp.com',
            'icon': '✉️',
            'staff_default_access': True
        },
        {
            'name': 'Postal Mail',
            'description': 'Send physical mail to businesses in our directory.',
            'url': 'https://postalmethods.com',
            'icon': '📬',
            'staff_default_access': True
        },
        {
            'name': 'Label Making',
            'description': 'Create mailing labels from our directory data.',
            'url': 'https://avery.com/templates',
            'icon': '🏷️',
            'staff_default_access': True
        },
        {
            'name': 'Mass Calls & Texting',
            'description': 'Send mass calls and text messages to businesses in our directory.',
            'url': 'https://dialmycalls.com',
            'icon': '📱',
            'staff_default_access': True
        },
        {
            'name': 'Promotional Texts',
            'description': 'Access promotional text templates for NoteStacker.com.',
            'url': '#promotional-texts',
            'icon': '💬',
            'staff_default_access': True
        }
    ]
    
    for tool_data in default_tools:
        tool = Tool.query.filter_by(name=tool_data['name']).first()
        if not tool:
            tool = Tool(**tool_data)
            db.session.add(tool)
    
    # Create admin user if no users exist
    if User.query.count() == 0:
        admin = User(
            username='admin',
            email='admin@directoryhub.com',
            full_name='Administrator',
            role='Admin',
            is_active=True
        )
        admin.set_password('Admin123!')
        db.session.add(admin)
        
        # Also create a manager and staff user for testing
        manager = User(
            username='manager',
            email='manager@directoryhub.com',
            full_name='Manager User',
            role='Manager',
            is_active=True
        )
        manager.set_password('Manager123!')
        db.session.add(manager)
        
        staff = User(
            username='staff',
            email='staff@directoryhub.com',
            full_name='Staff User',
            role='Staff',
            is_active=True
        )
        staff.set_password('Staff123!')
        db.session.add(staff)
    
    # Create sample business data if none exists
    if Business.query.count() == 0:
        # Sample data for businesses across different states
        sample_businesses = [
            # Vehicle Dealerships
            {'name': 'ABC Auto Sales', 'type': 'Vehicle Dealership', 'state': 'California', 'city': 'Los Angeles'},
            {'name': 'XYZ Motors', 'type': 'Vehicle Dealership', 'state': 'Texas', 'city': 'Houston'},
            {'name': 'Sunshine Cars', 'type': 'Vehicle Dealership', 'state': 'Florida', 'city': 'Miami'},
            {'name': 'Empire Auto', 'type': 'Vehicle Dealership', 'state': 'New York', 'city': 'Buffalo'},
            {'name': 'Windy City Motors', 'type': 'Vehicle Dealership', 'state': 'Illinois', 'city': 'Chicago'},
            {'name': 'Keystone Cars', 'type': 'Vehicle Dealership', 'state': 'Pennsylvania', 'city': 'Philadelphia'},
            {'name': 'Buckeye Auto', 'type': 'Vehicle Dealership', 'state': 'Ohio', 'city': 'Columbus'},
            {'name': 'Peach State Motors', 'type': 'Vehicle Dealership', 'state': 'Georgia', 'city': 'Atlanta'},
            {'name': 'Tar Heel Autos', 'type': 'Vehicle Dealership', 'state': 'North Carolina', 'city': 'Charlotte'},
            {'name': 'Great Lakes Cars', 'type': 'Vehicle Dealership', 'state': 'Michigan', 'city': 'Detroit'},
            
            # Real Estate Professionals
            {'name': 'Golden State Realty', 'type': 'Real Estate Professional', 'state': 'California', 'city': 'San Francisco'},
            {'name': 'Lone Star Properties', 'type': 'Real Estate Professional', 'state': 'Texas', 'city': 'Dallas'},
            {'name': 'Sunshine Homes', 'type': 'Real Estate Professional', 'state': 'Florida', 'city': 'Orlando'},
            {'name': 'Empire State Realty', 'type': 'Real Estate Professional', 'state': 'New York', 'city': 'New York City'},
            {'name': 'Windy City Homes', 'type': 'Real Estate Professional', 'state': 'Illinois', 'city': 'Chicago'},
            {'name': 'Keystone Properties', 'type': 'Real Estate Professional', 'state': 'Pennsylvania', 'city': 'Pittsburgh'},
            {'name': 'Buckeye Realty', 'type': 'Real Estate Professional', 'state': 'Ohio', 'city': 'Cleveland'},
            {'name': 'Peach State Properties', 'type': 'Real Estate Professional', 'state': 'Georgia', 'city': 'Savannah'},
            {'name': 'Carolina Homes', 'type': 'Real Estate Professional', 'state': 'North Carolina', 'city': 'Raleigh'},
            {'name': 'Great Lakes Realty', 'type': 'Real Estate Professional', 'state': 'Michigan', 'city': 'Ann Arbor'},
            
            # Apartment Rentals
            {'name': 'Pacific View Apartments', 'type': 'Apartment Rental', 'state': 'California', 'city': 'San Diego'},
            {'name': 'Texas Towers', 'type': 'Apartment Rental', 'state': 'Texas', 'city': 'Austin'},
            {'name': 'Palm Beach Residences', 'type': 'Apartment Rental', 'state': 'Florida', 'city': 'Tampa'},
            {'name': 'Manhattan Lofts', 'type': 'Apartment Rental', 'state': 'New York', 'city': 'New York City'},
            {'name': 'Lakefront Apartments', 'type': 'Apartment Rental', 'state': 'Illinois', 'city': 'Chicago'},
            {'name': 'Liberty Bell Residences', 'type': 'Apartment Rental', 'state': 'Pennsylvania', 'city': 'Philadelphia'},
            {'name': 'Riverside Apartments', 'type': 'Apartment Rental', 'state': 'Ohio', 'city': 'Cincinnati'},
            {'name': 'Magnolia Apartments', 'type': 'Apartment Rental', 'state': 'Georgia', 'city': 'Atlanta'},
            {'name': 'Blue Ridge Residences', 'type': 'Apartment Rental', 'state': 'North Carolina', 'city': 'Asheville'},
            {'name': 'Great Lakes Apartments', 'type': 'Apartment Rental', 'state': 'Michigan', 'city': 'Grand Rapids'}
        ]
        
        # Add more businesses to reach the total counts mentioned in the dashboard
        # (152 total: 48 vehicle dealerships, 64 real estate professionals, 40 apartment rentals)
        
        # Add more Vehicle Dealerships to reach 48
        states = ['California', 'Texas', 'Florida', 'New York', 'Illinois', 'Pennsylvania', 'Ohio', 'Georgia', 'North Carolina', 'Michigan']
        for i in range(38):  # Already have 10, need 38 more
            state = states[i % len(states)]
            sample_businesses.append({
                'name': f'Auto Dealer {i+1}',
                'type': 'Vehicle Dealership',
                'state': state,
                'city': f'City {i+1}'
            })
        
        # Add more Real Estate Professionals to reach 64
        for i in range(54):  # Already have 10, need 54 more
            state = states[i % len(states)]
            sample_businesses.append({
                'name': f'Realty Group {i+1}',
                'type': 'Real Estate Professional',
                'state': state,
                'city': f'City {i+1}'
            })
        
        # Add more Apartment Rentals to reach 40
        for i in range(30):  # Already have 10, need 30 more
            state = states[i % len(states)]
            sample_businesses.append({
                'name': f'Apartment Complex {i+1}',
                'type': 'Apartment Rental',
                'state': state,
                'city': f'City {i+1}'
            })
        
        # Add all businesses to database
        for business_data in sample_businesses:
            business = Business(**business_data)
            db.session.add(business)
    
    db.session.commit()

# Initialize database and create default data
with app.app_context():
    db.create_all()
    create_default_data()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
