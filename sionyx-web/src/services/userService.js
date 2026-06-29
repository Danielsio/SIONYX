import { ref, get, update } from 'firebase/database';
import { auth, database, SERVER_URL } from '../config/firebase';
import { logger } from '../utils/logger';

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
    logger.error('Error getting users:', error);
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
    logger.error('Error getting user purchases:', error);
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
    // Server-authoritative: the Worker adjusts the balance (clients are/will be
    // denied direct writes to remainingTime/printBalance by RTDB rules).
    const token = await auth.currentUser.getIdToken();
    const res = await fetch(`${SERVER_URL}/admin/adjust-balance`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify({
        orgId,
        userId,
        addSeconds: adjustments.timeSeconds,
        addPrints: adjustments.prints,
      }),
    });
    const data = await res.json().catch(() => ({}));

    if (!res.ok || !data.success) {
      return { success: false, error: data.error || 'Failed to adjust user balance' };
    }

    return {
      success: true,
      message: 'User balance adjusted successfully',
      newBalance: {
        remainingTime: data.remainingTime,
        printBalance: data.printBalance,
      },
    };
  } catch (error) {
    logger.error('Error adjusting user balance:', error);
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
    logger.error('Error granting admin permission:', error);
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
    logger.error('Error revoking admin permission:', error);
    return {
      success: false,
      error: error.message,
    };
  }
};

/**
 * Reset user password (admin only)
 * Calls Firebase Cloud Function to update user's password
 */
export const resetUserPassword = async (orgId, userId, newPassword) => {
  try {
    const token = await auth.currentUser.getIdToken();
    const res = await fetch(`${SERVER_URL}/auth/reset-password`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify({ orgId, userId, newPassword }),
    });
    const data = await res.json().catch(() => ({}));

    if (!res.ok || !data.success) {
      return { success: false, error: data.error || 'שגיאה באיפוס הסיסמה' };
    }

    return {
      success: true,
      message: 'הסיסמה אופסה בהצלחה',
    };
  } catch (error) {
    logger.error('Error resetting user password:', error);
    return {
      success: false,
      error: error.message || 'שגיאה באיפוס הסיסמה',
    };
  }
};

/**
 * Delete a user (admin only).
 * Calls Cloud Function which handles auth deletion, messages, and computer cleanup.
 */
export const deleteUser = async (orgId, userId) => {
  try {
    const token = await auth.currentUser.getIdToken();
    const res = await fetch(`${SERVER_URL}/admin/delete-user`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify({ orgId, userId }),
    });
    const data = await res.json().catch(() => ({}));

    if (!res.ok || !data.success) {
      return { success: false, error: data.error || 'שגיאה במחיקת המשתמש' };
    }

    return {
      success: true,
      message: 'המשתמש נמחק בהצלחה',
    };
  } catch (error) {
    logger.error('Error deleting user:', error);
    return { success: false, error: error.message || 'שגיאה במחיקת המשתמש' };
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

    // Also disassociate user from computer if they have a current computer
    if (currentUser.currentComputerId) {
      const computerRef = ref(
        database,
        `organizations/${orgId}/computers/${currentUser.currentComputerId}`
      );
      await update(computerRef, {
        currentUserId: null,
        lastUserLogout: new Date().toISOString(),
        isActive: false,
        updatedAt: new Date().toISOString(),
      });

      // Clear user's computer association
      await update(userRef, {
        currentComputerId: null,
        currentComputerName: null,
        lastComputerLogout: new Date().toISOString(),
        isSessionActive: false,
      });
    }

    return {
      success: true,
      message: 'User has been kicked successfully',
    };
  } catch (error) {
    logger.error('Error kicking user:', error);
    return {
      success: false,
      error: error.message,
    };
  }
};
