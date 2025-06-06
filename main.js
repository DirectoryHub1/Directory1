// Main JavaScript for Directory Hub

document.addEventListener('DOMContentLoaded', function() {
    // Initialize the application
    initApp();
    
    // Set up event listeners
    setupEventListeners();
    
    // Initialize charts
    initCharts();
});

// Initialize the application
function initApp() {
    // Check if user is logged in
    const isLoggedIn = localStorage.getItem('directoryHubLoggedIn');
    const userRole = localStorage.getItem('directoryHubUserRole') || 'admin';
    
    // Set the role on the body for CSS targeting
    document.body.setAttribute('data-role', userRole);
    
    // Set the role selector to match stored role
    const roleSelect = document.getElementById('role-select');
    if (roleSelect) {
        roleSelect.value = userRole;
    }
    
    // Show login page or dashboard based on login status
    if (!isLoggedIn) {
        showPage('login-page');
        document.querySelector('.sidebar').classList.add('d-none');
        document.querySelector('.navbar').classList.add('d-none');
        if (document.querySelector('.mobile-nav')) {
            document.querySelector('.mobile-nav').classList.add('d-none');
        }
    } else {
        showPage('dashboard-page');
        document.querySelector('.sidebar').classList.remove('d-none');
        document.querySelector('.navbar').classList.remove('d-none');
        if (document.querySelector('.mobile-nav')) {
            document.querySelector('.mobile-nav').classList.remove('d-none');
        }
        
        // Update user name and role in sidebar
        document.getElementById('user-name').textContent = localStorage.getItem('directoryHubUserName') || 'Admin User';
        document.getElementById('user-role').textContent = getUserRoleDisplay(userRole);
    }
}

// Set up event listeners
function setupEventListeners() {
    // Login form submission
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            e.preventDefault();
            handleLogin();
        });
    }
    
    // Logout button
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', function(e) {
            e.preventDefault();
            handleLogout();
        });
    }
    
    // Mobile logout button
    const mobileLogoutBtn = document.getElementById('mobile-logout');
    if (mobileLogoutBtn) {
        mobileLogoutBtn.addEventListener('click', function(e) {
            e.preventDefault();
            handleLogout();
        });
    }
    
    // Sidebar toggle
    const sidebarCollapse = document.getElementById('sidebarCollapse');
    if (sidebarCollapse) {
        sidebarCollapse.addEventListener('click', function() {
            document.querySelector('.sidebar').classList.toggle('active');
            document.getElementById('content').classList.toggle('sidebar-active');
        });
    }
    
    // Navigation links
    const navLinks = document.querySelectorAll('[data-page]');
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const page = this.getAttribute('data-page');
            showPage(page + '-page');
            
            // Update active state in sidebar
            document.querySelectorAll('.sidebar .list-unstyled li').forEach(item => {
                item.classList.remove('active');
            });
            
            // Find the parent li and add active class
            const parentLi = this.closest('li');
            if (parentLi) {
                parentLi.classList.add('active');
            }
            
            // Update page title
            document.getElementById('page-title').textContent = this.textContent.trim();
            
            // For mobile, close the more menu if open
            if (document.querySelector('.mobile-more-menu.active')) {
                document.querySelector('.mobile-more-menu').classList.remove('active');
            }
            
            // Update active state in mobile nav
            document.querySelectorAll('.mobile-nav-item').forEach(item => {
                item.classList.remove('active');
            });
            
            // Find the matching mobile nav item and add active class
            const mobileNavItem = document.querySelector(`.mobile-nav-item[data-page="${page}"]`);
            if (mobileNavItem) {
                mobileNavItem.classList.add('active');
            }
        });
    });
    
    // Mobile more menu
    const mobileMore = document.getElementById('mobile-more');
    if (mobileMore) {
        mobileMore.addEventListener('click', function(e) {
            e.preventDefault();
            document.querySelector('.mobile-more-menu').classList.toggle('active');
        });
    }
    
    // Close more menu
    const closeMoreMenu = document.querySelector('.close-more-menu');
    if (closeMoreMenu) {
        closeMoreMenu.addEventListener('click', function() {
            document.querySelector('.mobile-more-menu').classList.remove('active');
        });
    }
    
    // Role switcher
    const roleSelect = document.getElementById('role-select');
    if (roleSelect) {
        roleSelect.addEventListener('change', function() {
            const selectedRole = this.value;
            localStorage.setItem('directoryHubUserRole', selectedRole);
            document.body.setAttribute('data-role', selectedRole);
            document.getElementById('user-role').textContent = getUserRoleDisplay(selectedRole);
        });
    }
    
    // Chart type switcher
    const chartTypeLinks = document.querySelectorAll('.chart-type');
    chartTypeLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const chartType = this.getAttribute('data-type');
            updateChartType(chartType);
        });
    });
    
    // Business type filter
    const businessTypeFilter = document.getElementById('business-type-filter');
    if (businessTypeFilter) {
        businessTypeFilter.addEventListener('change', function() {
            filterBusinessData(this.value);
        });
    }
    
    // Download chart button
    const downloadChartBtn = document.getElementById('download-chart');
    if (downloadChartBtn) {
        downloadChartBtn.addEventListener('click', function(e) {
            e.preventDefault();
            downloadChart();
        });
    }
}

// Handle login
function handleLogin() {
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    
    // Simple validation
    if (!email || !password) {
        alert('Please enter both email and password.');
        return;
    }
    
    // Check credentials against predefined users
    // In a real app, this would be an API call to the Flask backend
    const users = [
        { email: 'admin@directoryhub.com', password: 'Admin123!', name: 'Admin User', role: 'admin' },
        { email: 'manager@directoryhub.com', password: 'Manager123!', name: 'Manager User', role: 'manager' },
        { email: 'staff@directoryhub.com', password: 'Staff123!', name: 'Staff User', role: 'staff' }
    ];
    
    const user = users.find(u => u.email === email && u.password === password);
    
    if (user) {
        // Store login state and user info
        localStorage.setItem('directoryHubLoggedIn', 'true');
        localStorage.setItem('directoryHubUserName', user.name);
        localStorage.setItem('directoryHubUserRole', user.role);
        localStorage.setItem('directoryHubUserEmail', user.email);
        
        // Set the role on the body for CSS targeting
        document.body.setAttribute('data-role', user.role);
        
        // Update user name and role in sidebar
        document.getElementById('user-name').textContent = user.name;
        document.getElementById('user-role').textContent = getUserRoleDisplay(user.role);
        
        // Set the role selector to match user role
        const roleSelect = document.getElementById('role-select');
        if (roleSelect) {
            roleSelect.value = user.role;
        }
        
        // Show dashboard
        showPage('dashboard-page');
        document.querySelector('.sidebar').classList.remove('d-none');
        document.querySelector('.navbar').classList.remove('d-none');
        if (document.querySelector('.mobile-nav')) {
            document.querySelector('.mobile-nav').classList.remove('d-none');
        }
        
        // Log activity
        logActivity(`${user.name} logged in`, 'user');
    } else {
        alert('Invalid email or password. Please try again.');
    }
}

// Handle logout
function handleLogout() {
    // Log activity before clearing user info
    const userName = localStorage.getItem('directoryHubUserName') || 'User';
    logActivity(`${userName} logged out`, 'user');
    
    // Clear login state and user info
    localStorage.removeItem('directoryHubLoggedIn');
    localStorage.removeItem('directoryHubUserName');
    localStorage.removeItem('directoryHubUserRole');
    localStorage.removeItem('directoryHubUserEmail');
    
    // Show login page
    showPage('login-page');
    document.querySelector('.sidebar').classList.add('d-none');
    document.querySelector('.navbar').classList.add('d-none');
    if (document.querySelector('.mobile-nav')) {
        document.querySelector('.mobile-nav').classList.add('d-none');
    }
    
    // Clear form fields
    document.getElementById('email').value = '';
    document.getElementById('password').value = '';
}

// Show a specific page
function showPage(pageId) {
    // Hide all pages
    document.querySelectorAll('.content-page').forEach(page => {
        page.classList.remove('active');
    });
    
    // Show the requested page
    const page = document.getElementById(pageId);
    if (page) {
        page.classList.add('active');
    }
}

// Get display text for user role
function getUserRoleDisplay(role) {
    switch (role) {
        case 'admin':
            return 'Administrator';
        case 'manager':
            return 'Manager';
        case 'staff':
            return 'Staff';
        default:
            return 'User';
    }
}

// Log activity
function logActivity(activity, type) {
    // In a real app, this would send data to the Flask API
    console.log(`Activity logged: ${activity} (${type})`);
    
    // For demo purposes, we'll just add it to the activity list if it exists
    const activityList = document.querySelector('.activity-list');
    if (activityList) {
        const now = new Date();
        const timeString = `Today, ${now.getHours()}:${now.getMinutes().toString().padStart(2, '0')} ${now.getHours() >= 12 ? 'PM' : 'AM'}`;
        
        let iconClass = 'fas fa-info-circle';
        let bgClass = 'bg-primary';
        
        switch (type) {
            case 'user':
                iconClass = 'fas fa-user';
                bgClass = 'bg-primary';
                break;
            case 'business':
                iconClass = 'fas fa-building';
                bgClass = 'bg-success';
                break;
            case 'document':
                iconClass = 'fas fa-file';
                bgClass = 'bg-info';
                break;
            case 'edit':
                iconClass = 'fas fa-user-edit';
                bgClass = 'bg-warning';
                break;
            case 'delete':
                iconClass = 'fas fa-trash';
                bgClass = 'bg-danger';
                break;
        }
        
        const activityItem = document.createElement('div');
        activityItem.className = 'activity-item';
        activityItem.innerHTML = `
            <div class="activity-icon ${bgClass}">
                <i class="${iconClass}"></i>
            </div>
            <div class="activity-content">
                <div class="activity-title">${activity}</div>
                <div class="activity-time">${timeString}</div>
            </div>
        `;
        
        // Insert at the top
        activityList.insertBefore(activityItem, activityList.firstChild);
        
        // Remove oldest if more than 5
        if (activityList.children.length > 5) {
            activityList.removeChild(activityList.lastChild);
        }
    }
}
