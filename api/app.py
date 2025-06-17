import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient
from bson.objectid import ObjectId

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your_secret_key') # Use environment variable for secret key

# MongoDB Connection
# Get MongoDB URI from environment variable
MONGO_URI = os.environ.get('MONGODB_URI')

if not MONGO_URI:
    # Fallback for local development if MONGO_URI is not set
    # In production on Vercel, MONGO_URI MUST be set as an environment variable
    print("Error: MONGODB_URI environment variable not set.")
    # You might want to raise an exception or handle this more gracefully
    # For now, we'll use a placeholder to allow the app to start, but it won't connect
    # In a real scenario, this should prevent the app from running without a DB
    MONGO_URI = "mongodb://localhost:27017/test_db" 

try:
    client = MongoClient(MONGO_URI)
    db = client.get_database('directory_hub') # Specify your database name here
    users_collection = db.users
    businesses_collection = db.businesses
    print("MongoDB connection successful!")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    # In a production environment, you might want to exit or log this more severely
    client = None # Ensure client is None if connection fails
    db = None

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User:
    def __init__(self, user_id, email, password, role):
        self.id = str(user_id)
        self.email = email
        self.password = password
        self.role = role

    def is_active(self):
        return True

    def is_authenticated(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id

@login_manager.user_loader
def load_user(user_id):
    if db and users_collection:
        user_data = users_collection.find_one({"_id": ObjectId(user_id)})
        if user_data:
            return User(user_data["_id"], user_data["email"], user_data["password"], user_data["role"])
    return None

# Routes
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not db or not users_collection:
            flash('Database not connected. Please check server configuration.', 'danger')
            return render_template('login.html')

        user_data = users_collection.find_one({'email': email})

        if user_data and check_password_hash(user_data['password'], password):
            user = User(user_data['_id'], user_data['email'], user_data['password'], user_data['role'])
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password', 'danger')
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    # Example data for dashboard - replace with actual data from MongoDB
    total_businesses = 0
    if db and businesses_collection:
        total_businesses = businesses_collection.count_documents({})
    return render_template('dashboard.html', total_businesses=total_businesses)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Admin routes (example - you'll have more)
@app.route('/admin/users')
@login_required
def admin_users():
    if current_user.role != 'Admin':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    users = []
    if db and users_collection:
        users = list(users_collection.find({}))
    return render_template('admin_users.html', users=users)

# Add other routes as needed for businesses, documents, etc.

# Initial user setup (run once, e.g., on first deploy or via a script)
# This part should ideally be handled outside the main app run for production
# For testing, you can uncomment and run once, then comment out
# with app.app_context():
#     if db and users_collection and users_collection.count_documents({}) == 0:
#         hashed_password = generate_password_hash('Admin123!', method='sha256')
#         users_collection.insert_one({
#             'email': 'admin@directoryhub.com',
#             'password': hashed_password,
#             'role': 'Admin'
#         })
#         print("Default admin user created.")

# if __name__ == '__main__':
#     app.run(debug=True)

