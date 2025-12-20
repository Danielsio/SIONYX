/**
 * User Status Constants
 * =====================
 * Unified status states for users combining connection and activity states.
 */

// User status enum
export const USER_STATUS = {
  ACTIVE: 'active',           // User is logged in AND using a computer
  CONNECTED: 'connected',     // User is logged in but NOT actively using
  OFFLINE: 'offline',         // User is not logged in
};

// Status display configuration
export const USER_STATUS_CONFIG = {
  [USER_STATUS.ACTIVE]: {
    label: 'פעיל',
    color: 'success',
    description: 'המשתמש מחובר ומשתמש במחשב',
  },
  [USER_STATUS.CONNECTED]: {
    label: 'מחובר',
    color: 'processing',
    description: 'המשתמש מחובר אך לא בשימוש',
  },
  [USER_STATUS.OFFLINE]: {
    label: 'לא מחובר',
    color: 'default',
    description: 'המשתמש לא מחובר',
  },
};

/**
 * Get user status based on session and computer data
 * @param {Object} user - User object with isSessionActive and currentComputerId
 * @returns {string} User status key
 */
export const getUserStatus = (user) => {
  if (!user) return USER_STATUS.OFFLINE;
  
  const isLoggedIn = user.isSessionActive === true;
  const isUsingComputer = isLoggedIn && user.currentComputerId;
  
  if (isUsingComputer) return USER_STATUS.ACTIVE;
  if (isLoggedIn) return USER_STATUS.CONNECTED;
  return USER_STATUS.OFFLINE;
};

/**
 * Get status label for display
 * @param {string} status - Status key
 * @returns {string} Hebrew label
 */
export const getStatusLabel = (status) => {
  return USER_STATUS_CONFIG[status]?.label || 'לא ידוע';
};

/**
 * Get status color for Ant Design Tag
 * @param {string} status - Status key
 * @returns {string} Color name
 */
export const getStatusColor = (status) => {
  return USER_STATUS_CONFIG[status]?.color || 'default';
};



