# Directory Hub User Management System - Design Document

## Overview
This document outlines the design for converting the static Directory Hub into a Flask application with a comprehensive user management system as requested by the client.

## User Roles and Permissions

### 1. Admin Role
- Full access to all features and functionality
- User management (add/edit/delete users)
- Access to all directory data
- Access to all tools
- System configuration

### 2. Manager Role
- View all directory data
- Limited editing capabilities
- Access to all tools
- Cannot manage users (except password reset for staff)
- Cannot modify system configuration

### 3. Staff Role
- View directory data
- Access to tools only (no editing of directory data)
- No user management capabilities
- No system configuration access

## Database Schema

### Users Table
```
id: Integer (Primary Key)
username: String (Unique)
email: String (Unique)
password_hash: String
full_name: String
phone_number: String
department: String
role: String (Admin, Manager, Staff)
last_password_change: DateTime
account_created: DateTime
last_login: DateTime
is_active: Boolean
```

### Permissions Table
```
id: Integer (Primary Key)
user_id: Integer (Foreign Key)
tool_id: Integer (Foreign Key)
can_access: Boolean
```

### Tools Table
```
id: Integer (Primary Key)
name: String
description: String
url: String
icon: String
```

### Password Reset Table
```
id: Integer (Primary Key)
user_id: Integer (Foreign Key)
reset_token: String
expiry: DateTime
```

### Activity Log Table
```
id: Integer (Primary Key)
user_id: Integer (Foreign Key)
action: String
timestamp: DateTime
details: String
ip_address: String
```

## Password Policy Implementation
- Minimum 10 characters
- Must include uppercase, lowercase, numbers, and symbols
- Expires every 3 months
- Cannot reuse previous 5 passwords
- Lockout after 5 failed attempts
- Password strength indicator during creation/change

## Admin Panel Features
1. User Management
   - List all users with filtering and sorting
   - Create new users
   - Edit user details
   - Reset user passwords
   - Deactivate/reactivate users
   - Delete users (with confirmation)

2. Permission Management
   - Assign tools to users
   - Set role-based permissions
   - Override permissions for specific users

3. Activity Monitoring
   - View login history
   - Track user actions
   - Filter by user, action type, date range

4. System Settings
   - Password policy configuration
   - Email notification settings
   - System backup and restore

## User Interface Design
- Maintain the professional blue gradient design
- Responsive layout for all devices
- Consistent navigation and sidebar
- Role-specific dashboard views
- Clear visual indicators for permission levels

## Security Considerations
- HTTPS for all connections
- Password hashing using bcrypt
- CSRF protection
- Rate limiting for login attempts
- Session timeout after inactivity
- Input validation and sanitization
- SQL injection protection

## Implementation Technologies
- Backend: Flask with SQLAlchemy
- Database: SQLite for development, PostgreSQL for production
- Authentication: Flask-Login
- Form handling: Flask-WTF
- Password hashing: Werkzeug security
- Frontend: HTML, CSS, JavaScript (maintaining current design)
