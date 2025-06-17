import os
from flask import Flask, request, redirect, url_for
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient
from bson.objectid import ObjectId

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your_secret_key')

# MongoDB Connection
MONGO_URI = os.environ.get('MONGODB_URI')

if not MONGO_URI:
    print("Error: MONGODB_URI environment variable not set.")
    MONGO_URI = "mongodb://localhost:27017/test_db" 

try:
    client = MongoClient(MONGO_URI)
    db = client.get_database('directory_hub')
    users_collection = db.users
    businesses_collection = db.businesses
    print("MongoDB connection successful!")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    client = None
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
            return '<h1>Database not connected. Please check server configuration.</h1>'

        user_data = users_collection.find_one({'email': email})

        if user_data and check_password_hash(user_data['password'], password):
            user = User(user_data['_id'], user_data['email'], user_data['password'], user_data['role'])
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            return '''
            <h1>Invalid email or password</h1>
            <form method="post">
                <input type="email" name="email" placeholder="Email" required><br><br>
                <input type="password" name="password" placeholder="Password" required><br><br>
                <input type="submit" value="Login">
            </form>
            <p><a href="/login">Try again</a></p>
            '''
    
    return '''
    <h1>Directory Hub Login</h1>
    <form method="post">
        <input type="email" name="email" placeholder="Email" required><br><br>
        <input type="password" name="password" placeholder="Password" required><br><br>
        <input type="submit" value="Login">
    </form>
    '''

@app.route('/dashboard')
@login_required
def dashboard():
    total_businesses = 0
    if db and businesses_collection:
        total_businesses = businesses_collection.count_documents({})
    
    return f'''
    <h1>Welcome to Directory Hub Dashboard</h1>
    <p>Hello, {current_user.email}!</p>
    <p>Role: {current_user.role}</p>
    <p>Total Businesses: {total_businesses}</p>
    <p><a href="/logout">Logout</a></p>
    '''

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/api/test')
def api_test():
    return {"message": "API is working!"}

# Create admin user if none exists
@app.route('/setup')
def setup():
    if db and users_collection and users_collection.count_documents({}) == 0:
        hashed_password = generate_password_hash('Admin123!')
        users_collection.insert_one({
            'email': 'admin@directoryhub.com',
            'password': hashed_password,
            'role': 'Admin'
        })
        return "Default admin user created: admin@directoryhub.com / Admin123!"
    return "Admin user already exists or database not connected."
