from flask import Flask, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime

# Import modules
from .models.user import db, User, Tool, Permission
from .auth import auth_bp, init_app as init_auth
from .admin import admin_bp
from .main import main_bp
from .data import data_bp

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-for-testing')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///directory_hub.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions
    db.init_app(app)
    init_auth(app)
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(data_bp)
    
    # Create database tables
    with app.app_context():
        db.create_all()
        
        # Create default tools if they don't exist
        create_default_tools()
        
        # Create admin user if no users exist
        create_admin_user()
        
        # Create sample business data if none exists
        create_sample_businesses()
    
    # Main routes
    @app.route('/')
    def index():
        return redirect(url_for('auth.login'))
    
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('500.html'), 500
    
    return app

def create_default_tools():
    """Create default tools if they don't exist"""
    default_tools = [
        {
            'name': 'Email Marketing',
            'description': 'Use our directory data for targeted email marketing campaigns.',
            'url': 'https://ymlp.com',
            'icon': '✉️'
        },
        {
            'name': 'Postal Mail',
            'description': 'Send physical mail to businesses in our directory.',
            'url': 'https://postalmethods.com',
            'icon': '📬'
        },
        {
            'name': 'Label Making',
            'description': 'Create mailing labels from our directory data.',
            'url': 'https://avery.com/templates',
            'icon': '🏷️'
        },
        {
            'name': 'Mass Calls & Texting',
            'description': 'Send mass calls and text messages to businesses in our directory.',
            'url': 'https://dialmycalls.com',
            'icon': '📱'
        },
        {
            'name': 'Promotional Texts',
            'description': 'Access promotional text templates for NoteStacker.com.',
            'url': '#promotional-texts',
            'icon': '💬'
        }
    ]
    
    for tool_data in default_tools:
        tool = Tool.query.filter_by(name=tool_data['name']).first()
        if not tool:
            tool = Tool(**tool_data)
            db.session.add(tool)
    
    db.session.commit()

def create_admin_user():
    """Create admin user if no users exist"""
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
        
        db.session.commit()

def create_sample_businesses():
    """Create sample business data if none exists"""
    from .models.content import Business
    
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
