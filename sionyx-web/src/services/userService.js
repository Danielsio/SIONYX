import { ref, get, update } from 'firebase/database';
import { database } from '../config/firebase';

/**
 * Get all users in an organization
 */
export const getAllUsers = async orgId => {
  try {
    const usersRef = ref(database, `organizations/${orgId}/users`);
    const snapshot = await get(usersRef);

    if (!snapshot.exists()) {
      return {
        success: true,
        users: [],
      };
    }

    const usersData = snapshot.val();
    const users = Object.keys(usersData).map(uid => ({
      uid,
      ...usersData[uid],
    }));

    // Sort by creation date (newest first)
    users.sort((a, b) => {
      const dateA = new Date(a.createdAt || 0);
      const dateB = new Date(b.createdAt || 0);
      return dateB - dateA;
    });

    return {
      success: true,
      users,
    };
  } catch (error) {
    console.error('Error getting users:', error);
    return {
      success: false,
      error: error.message,
      users: [],
    };
  }
};

/**
 * Get user's purchase history
 */
export const getUserPurchaseHistory = async (orgId, userId) => {
  try {
    const purchasesRef = ref(database, `organizations/${orgId}/purchases`);
    const snapshot = await get(purchasesRef);

    if (!snapshot.exists()) {
      return {
        success: true,
        purchases: [],
      };
    }

    const allPurchases = snapshot.val();
    const userPurchases = Object.keys(allPurchases)
      .filter(key => allPurchases[key].userId === userId)
      .map(key => ({
        id: key,
        ...allPurchases[key],
      }));

    // Sort by date (newest first)
    userPurchases.sort((a, b) => {
      const dateA = new Date(a.createdAt || 0);
      const dateB = new Date(b.createdAt || 0);
      return dateB - dateA;
    });

    return {
      success: true,
      purchases: userPurchases,
    };
  } catch (error) {
    console.error('Error getting user purchases:', error);
    return {
      success: false,
      error: error.message,
      purchases: [],
    };
  }
};

/**
 * Adjust user's balance (time and prints)
 */
export const adjustUserBalance = async (orgId, userId, adjustments) => {
  try {
    // First get the current user data
    const userRef = ref(database, `organizations/${orgId}/users/${userId}`);
    const snapshot = await get(userRef);

    if (!snapshot.exists()) {
      return {
        success: false,
        error: 'User not found',
      };
    }

    const currentUser = snapshot.val();

    // Calculate new values
    const updates = {
      updatedAt: new Date().toISOString(),
    };

    if (adjustments.timeSeconds !== undefined) {
      updates.remainingTime = (currentUser.remainingTime || 0) + adjustments.timeSeconds;
      // Ensure it doesn't go negative
      if (updates.remainingTime < 0) updates.remainingTime = 0;
    }

    if (adjustments.prints !== undefined) {
      updates.remainingPrints = (currentUser.remainingPrints || 0) + adjustments.prints;
      // Ensure it doesn't go negative
      if (updates.remainingPrints < 0) updates.remainingPrints = 0;
    }

    await update(userRef, updates);

    return {
      success: true,
      message: 'User balance adjusted successfully',
      newBalance: {
        remainingTime: updates.remainingTime,
        remainingPrints: updates.remainingPrints,
      },
    };
  } catch (error) {
    console.error('Error adjusting user balance:', error);
    return {
      success: false,
      error: error.message,
    };
  }
};

/**
 * Grant admin permission to a user
 */
export const grantAdminPermission = async (orgId, userId) => {
  try {
    const userRef = ref(database, `organizations/${orgId}/users/${userId}`);
    const snapshot = await get(userRef);

    if (!snapshot.exists()) {
      return {
        success: false,
        error: 'User not found',
      };
    }

    const updates = {
      isAdmin: true,
      updatedAt: new Date().toISOString(),
    };

    await update(userRef, updates);

    return {
      success: true,
      message: 'Admin permission granted successfully',
    };
  } catch (error) {
    console.error('Error granting admin permission:', error);
    return {
      success: false,
      error: error.message,
    };
  }
};

/**
 * Revoke admin permission from a user
 */
export const revokeAdminPermission = async (orgId, userId) => {
  try {
    const userRef = ref(database, `organizations/${orgId}/users/${userId}`);
    const snapshot = await get(userRef);

    if (!snapshot.exists()) {
      return {
        success: false,
        error: 'User not found',
      };
    }

    const updates = {
      isAdmin: false,
      updatedAt: new Date().toISOString(),
    };

    await update(userRef, updates);

    return {
      success: true,
      message: 'Admin permission revoked successfully',
    };
  } catch (error) {
    console.error('Error revoking admin permission:', error);
    return {
      success: false,
      error: error.message,
    };
  }
};

/**
 * Kick a user (force logout)
 */
export const kickUser = async (orgId, userId) => {
  try {
    const userRef = ref(database, `organizations/${orgId}/users/${userId}`);
    const snapshot = await get(userRef);

    if (!snapshot.exists()) {
      return {
        success: false,
        error: 'User not found',
      };
    }

    const currentUser = snapshot.val();

    // Check if user is already kicked (prevent spam clicking)
    if (currentUser.forceLogout === true) {
      return {
        success: false,
        error: 'User has already been kicked',
      };
    }

    const updates = {
      forceLogout: true,
      forceLogoutTimestamp: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    await update(userRef, updates);

    return {
      success: true,
      message: 'User has been kicked successfully',
    };
  } catch (error) {
    console.error('Error kicking user:', error);
    return {
      success: false,
      error: error.message,
    };
  }
};
