/**
 * Role-based permission management for Directory Hub
 * 
 * This script handles the visibility and access control for different user roles:
 * - Admin: Full access to all features
 * - Manager: Access to most features except user management and permissions
 * - Staff: Access to basic directory features and tools only
 */

document.addEventListener('DOMContentLoaded', function() {
    // Simulate current user role (would come from backend in real app)
    // Options: 'Admin', 'Manager', 'Staff'
    const currentRole = localStorage.getItem('currentRole') || 'Admin';
    
    // Update role display in UI
    document.getElementById('current-role-display').textContent = currentRole;
    
    // Apply role-based visibility
    applyRoleBasedVisibility(currentRole);
    
    // Set up role switcher for demo purposes
    setupRoleSwitcher();
});

/**
 * Apply visibility rules based on user role
 */
function applyRoleBasedVisibility(role) {
    // Hide elements based on role
    const adminOnlyElements = document.querySelectorAll('.admin-only');
    const adminManagerElements = document.querySelectorAll('.admin-manager-only');
    
    // Reset all elements first
    adminOnlyElements.forEach(el => el.style.display = 'none');
    adminManagerElements.forEach(el => el.style.display = 'none');
    
    // Apply role-specific visibility
    if (role === 'Admin') {
        // Admin sees everything
        adminOnlyElements.forEach(el => el.style.display = '');
        adminManagerElements.forEach(el => el.style.display = '');
    } else if (role === 'Manager') {
        // Manager sees admin-manager elements but not admin-only
        adminManagerElements.forEach(el => el.style.display = '');
    }
    // Staff sees neither admin-only nor admin-manager elements
    
    // Update main content visibility
    updateMainContentVisibility(role);
}

/**
 * Update main content sections based on role
 */
function updateMainContentVisibility(role) {
    // Hide/show main content sections based on role
    const userManagementSection = document.getElementById('user-management-section');
    const permissionsSection = document.getElementById('permissions-section');
    const activityLogSection = document.getElementById('activity-log-section');
    const settingsSection = document.getElementById('settings-section');
    
    if (userManagementSection) {
        userManagementSection.style.display = (role === 'Admin') ? 'block' : 'none';
    }
    
    if (permissionsSection) {
        permissionsSection.style.display = (role === 'Admin') ? 'block' : 'none';
    }
    
    if (activityLogSection) {
        activityLogSection.style.display = (role === 'Admin' || role === 'Manager') ? 'block' : 'none';
    }
    
    if (settingsSection) {
        settingsSection.style.display = (role === 'Admin' || role === 'Manager') ? 'block' : 'none';
    }
}

/**
 * Set up role switcher for demo purposes
 */
function setupRoleSwitcher() {
    const roleSwitcher = document.getElementById('role-switcher');
    if (!roleSwitcher) return;
    
    roleSwitcher.addEventListener('change', function() {
        const selectedRole = this.value;
        localStorage.setItem('currentRole', selectedRole);
        applyRoleBasedVisibility(selectedRole);
    });
}
