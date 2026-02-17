/**
 * Computer Management Service for Admin Dashboard
 * Handles computer/PC tracking and management
 */

import { ref, get, update, remove } from 'firebase/database';
import { database } from '../config/firebase';
import { getOrgId } from '../hooks/useOrgId';
import { useAuthStore } from '../store/authStore';
import { isSupervisorPendingActivation } from '../utils/roles';
import { logger } from '../utils/logger';

/**
 * Get all computers in the organization
 */
export const getAllComputers = async () => {
  // Supervisor activation gate: return empty data if not yet activated
  if (isSupervisorPendingActivation(useAuthStore.getState().user)) {
    return { success: true, data: [] };
  }

  try {
    // Get organization ID from localStorage or user data
    const orgId = getOrgId();
    const computersRef = ref(database, `organizations/${orgId}/computers`);
    const snapshot = await get(computersRef);

    if (snapshot.exists()) {
      const computers = snapshot.val();
      const computerList = Object.keys(computers).map(computerId => ({
        id: computerId,
        ...computers[computerId],
      }));

      return {
        success: true,
        data: computerList,
      };
    } else {
      return {
        success: true,
        data: [],
      };
    }
  } catch (error) {
    logger.error('Error fetching computers:', error);
    return {
      success: false,
      error: 'Failed to fetch computers',
    };
  }
};

/**
 * Get computer usage statistics
 */
export const getComputerUsageStats = async () => {
  try {
    // Get all computers
    const computersResult = await getAllComputers();
    if (!computersResult.success) {
      return computersResult;
    }

    const computers = computersResult.data;

    // Get all users
    const orgId = getOrgId();
    const usersRef = ref(database, `organizations/${orgId}/users`);
    const usersSnapshot = await get(usersRef);
    const users = usersSnapshot.exists() ? usersSnapshot.val() : {};

    // Process statistics
    const stats = {
      totalComputers: computers.length,
      activeComputers: 0,
      computersWithUsers: 0,
      computerDetails: [],
      userComputerUsage: {},
    };

    computers.forEach(computer => {
      const currentUserId = computer.currentUserId;
      const isActive = computer.isActive || !!currentUserId;

      if (isActive) {
        stats.activeComputers++;
      }

      if (currentUserId) {
        stats.computersWithUsers++;

        // Get user info
        const userData = users[currentUserId] || {};
        const userName = `${userData.firstName || ''} ${userData.lastName || ''}`.trim();

        stats.computerDetails.push({
          computerId: computer.id,
          computerName: computer.computerName || 'Unknown',
          location: computer.location || '',
          isActive: isActive,
          currentUserId: currentUserId,
          currentUserName: userName,
          lastSeen: computer.lastSeen || '',
          osInfo: computer.osInfo || {},
          macAddress: computer.macAddress || '',
          ipAddress: computer.networkInfo?.local_ip || '',
        });

        // Track user's computer usage
        if (!stats.userComputerUsage[currentUserId]) {
          stats.userComputerUsage[currentUserId] = {
            userId: currentUserId,
            userName: userName,
            computersUsed: [],
          };
        }

        stats.userComputerUsage[currentUserId].computersUsed.push({
          computerId: computer.id,
          computerName: computer.computerName || 'Unknown',
          loginTime: computer.lastUserLogin || '',
        });
      } else {
        // Computer without user
        stats.computerDetails.push({
          computerId: computer.id,
          computerName: computer.computerName || 'Unknown',
          location: computer.location || '',
          isActive: isActive,
          currentUserId: null,
          currentUserName: null,
          lastSeen: computer.lastSeen || '',
          osInfo: computer.osInfo || {},
          macAddress: computer.macAddress || '',
          ipAddress: computer.networkInfo?.local_ip || '',
        });
      }
    });

    return {
      success: true,
      data: stats,
    };
  } catch (error) {
    logger.error('Error getting computer usage stats:', error);
    return {
      success: false,
      error: 'Failed to get computer usage statistics',
    };
  }
};

/**
 * Get computer by ID
 */
export const getComputerById = async computerId => {
  try {
    const orgId = getOrgId();
    const computerRef = ref(database, `organizations/${orgId}/computers/${computerId}`);
    const snapshot = await get(computerRef);

    if (snapshot.exists()) {
      return {
        success: true,
        data: {
          id: computerId,
          ...snapshot.val(),
        },
      };
    } else {
      return {
        success: false,
        error: 'Computer not found',
      };
    }
  } catch (error) {
    logger.error('Error fetching computer:', error);
    return {
      success: false,
      error: 'Failed to fetch computer',
    };
  }
};

/**
 * Update computer information
 */
export const updateComputer = async (computerId, updates) => {
  try {
    const orgId = getOrgId();
    const computerRef = ref(database, `organizations/${orgId}/computers/${computerId}`);

    // Add updatedAt timestamp
    const updateData = {
      ...updates,
      updatedAt: new Date().toISOString(),
    };

    await update(computerRef, updateData);

    return {
      success: true,
    };
  } catch (error) {
    logger.error('Error updating computer:', error);
    return {
      success: false,
      error: 'Failed to update computer',
    };
  }
};

/**
 * Delete computer
 */
export const deleteComputer = async computerId => {
  try {
    const orgId = getOrgId();
    const computerRef = ref(database, `organizations/${orgId}/computers/${computerId}`);
    await remove(computerRef);

    return {
      success: true,
    };
  } catch (error) {
    logger.error('Error deleting computer:', error);
    return {
      success: false,
      error: 'Failed to delete computer',
    };
  }
};

/**
 * Get users currently using computers
 */
export const getActiveComputerUsers = async () => {
  try {
    const computersResult = await getAllComputers();
    if (!computersResult.success) {
      return computersResult;
    }

    const computers = computersResult.data;
    const activeUsers = [];

    for (const computer of computers) {
      if (computer.currentUserId) {
        // Get user details
        const orgId = getOrgId();
        const userRef = ref(database, `organizations/${orgId}/users/${computer.currentUserId}`);
        const userSnapshot = await get(userRef);

        if (userSnapshot.exists()) {
          const userData = userSnapshot.val();
          activeUsers.push({
            userId: computer.currentUserId,
            userName: `${userData.firstName || ''} ${userData.lastName || ''}`.trim(),
            userPhone: userData.phoneNumber || '',
            computerId: computer.id,
            computerName: computer.computerName || 'Unknown',
            computerLocation: computer.location || '',
            loginTime: computer.lastUserLogin || '',
            sessionStartTime: userData.sessionStartTime || null,
            sessionActive: userData.isSessionActive || false,
            remainingTime: userData.remainingTime || 0,
            printBalance: userData.printBalance || 0,
          });
        }
      }
    }

    return {
      success: true,
      data: activeUsers,
    };
  } catch (error) {
    logger.error('Error getting active computer users:', error);
    return {
      success: false,
      error: 'Failed to get active computer users',
    };
  }
};

/**
 * Force logout user from computer
 * This is a full logout - clears session, computer association, AND login status
 */
export const forceLogoutUser = async (userId, computerId) => {
  try {
    // Clear user's current computer and mark as logged out
    const orgId = getOrgId();
    const userRef = ref(database, `organizations/${orgId}/users/${userId}`);
    await update(userRef, {
      currentComputerId: null,
      currentComputerName: null,
      isSessionActive: false,
      isLoggedIn: false, // User is now logged out
      sessionStartTime: null,
      lastComputerLogout: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    });

    // Clear computer's current user and mark as inactive
    const computerRef = ref(database, `organizations/${orgId}/computers/${computerId}`);
    await update(computerRef, {
      currentUserId: null,
      lastUserLogout: new Date().toISOString(),
      isActive: false,
      updatedAt: new Date().toISOString(),
    });

    return {
      success: true,
    };
  } catch (error) {
    logger.error('Error forcing logout:', error);
    return {
      success: false,
      error: 'Failed to force logout user',
    };
  }
};
