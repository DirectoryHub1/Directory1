from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):
    """User model for authentication and profile information"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20))
    department = db.Column(db.String(50))
    role = db.Column(db.String(20), default='Staff')  # Admin, Manager, Staff
    last_password_change = db.Column(db.DateTime, default=datetime.utcnow)
    account_created = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    permissions = db.relationship('Permission', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    password_history = db.relationship('PasswordHistory', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    activity_logs = db.relationship('ActivityLog', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Set the user's password with hashing"""
        self.password_hash = generate_password_hash(password)
        self.last_password_change = datetime.utcnow()
        
        # Store password in history
        history = PasswordHistory(user_id=self.id, password_hash=self.password_hash)
        db.session.add(history)
    
    def check_password(self, password):
        """Check if the provided password matches the stored hash"""
        return check_password_hash(self.password_hash, password)
    
    def is_password_expired(self):
        """Check if the password has expired (3 months)"""
        expiry_date = self.last_password_change + timedelta(days=90)
        return datetime.utcnow() > expiry_date
    
    def is_password_in_history(self, password):
        """Check if the password has been used before (last 5 passwords)"""
        recent_passwords = self.password_history.order_by(PasswordHistory.created_at.desc()).limit(5).all()
        return any(check_password_hash(history.password_hash, password) for history in recent_passwords)
    
    def has_permission(self, tool_id):
        """Check if the user has permission to access a specific tool"""
        # Admins have access to everything
        if self.role == 'Admin':
            return True
            
        # Check specific permission
        permission = self.permissions.filter_by(tool_id=tool_id).first()
        return permission and permission.can_access
    
    def log_activity(self, action, details=None, ip_address=None):
        """Log user activity"""
        log = ActivityLog(
            user_id=self.id,
            action=action,
            details=details,
            ip_address=ip_address
        )
        db.session.add(log)
        db.session.commit()
    
    @property
    def is_admin(self):
        return self.role == 'Admin'
    
    @property
    def is_manager(self):
        return self.role == 'Manager'
    
    @property
    def is_staff(self):
        return self.role == 'Staff'
    
    def __repr__(self):
        return f'<User {self.username}>'


class Tool(db.Model):
    """Tool model for the directory hub tools"""
    __tablename__ = 'tools'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200))
    url = db.Column(db.String(200))
    icon = db.Column(db.String(50))
    
    # Relationships
    permissions = db.relationship('Permission', backref='tool', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Tool {self.name}>'


class Permission(db.Model):
    """Permission model for user-tool access control"""
    __tablename__ = 'permissions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    tool_id = db.Column(db.Integer, db.ForeignKey('tools.id'), nullable=False)
    can_access = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<Permission user_id={self.user_id} tool_id={self.tool_id} can_access={self.can_access}>'


class PasswordHistory(db.Model):
    """Password history for preventing password reuse"""
    __tablename__ = 'password_history'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<PasswordHistory user_id={self.user_id} created_at={self.created_at}>'


class PasswordReset(db.Model):
    """Password reset tokens"""
    __tablename__ = 'password_resets'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    reset_token = db.Column(db.String(100), nullable=False, unique=True)
    expiry = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)
    
    def is_expired(self):
        return datetime.utcnow() > self.expiry
    
    def __repr__(self):
        return f'<PasswordReset user_id={self.user_id} expiry={self.expiry}>'


class ActivityLog(db.Model):
    """Activity logging for user actions"""
    __tablename__ = 'activity_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(50))
    
    def __repr__(self):
        return f'<ActivityLog user_id={self.user_id} action={self.action} timestamp={self.timestamp}>'
