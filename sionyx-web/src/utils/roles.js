/**
 * Role utilities for RBAC (Role-Based Access Control)
 * 
 * Role hierarchy: user < admin < supervisor
 */

export const ROLES = {
  USER: 'user',
  ADMIN: 'admin',
  SUPERVISOR: 'supervisor',
};

export const ROLE_HIERARCHY = {
  [ROLES.USER]: 0,
  [ROLES.ADMIN]: 1,
  [ROLES.SUPERVISOR]: 2,
};

/**
 * Get user's effective role from user object
 * Handles backwards compatibility with isAdmin field
 */
export const getUserRole = user => {
  if (!user) return ROLES.USER;
  
  // New role field takes precedence
  if (user.role) {
    return user.role;
  }
  
  // Fallback to isAdmin for backwards compatibility
  if (user.isAdmin === true) {
    return ROLES.ADMIN;
  }
  
  return ROLES.USER;
};

/**
 * Check if user has at least the required role
 */
export const hasRole = (user, requiredRole) => {
  const userRole = getUserRole(user);
  const userLevel = ROLE_HIERARCHY[userRole] ?? 0;
  const requiredLevel = ROLE_HIERARCHY[requiredRole] ?? 0;
  return userLevel >= requiredLevel;
};

/**
 * Check if user is admin or above
 */
export const isAdminOrAbove = user => hasRole(user, ROLES.ADMIN);

/**
 * Check if user is supervisor
 */
export const isSupervisor = user => hasRole(user, ROLES.SUPERVISOR);

/**
 * Get display name for role in Hebrew
 */
export const getRoleDisplayName = role => {
  switch (role) {
    case ROLES.SUPERVISOR:
      return 'מפקח';
    case ROLES.ADMIN:
      return 'מנהל';
    case ROLES.USER:
    default:
      return 'משתמש';
  }
};
