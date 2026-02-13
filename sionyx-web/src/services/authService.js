import {
  signInWithEmailAndPassword,
  signOut as firebaseSignOut,
  onAuthStateChanged,
} from 'firebase/auth';
import { ref, get, set } from 'firebase/database';
import { auth, database } from '../config/firebase';
import { isAdminOrAbove, getUserRole, ROLES } from '../utils/roles';

/**
 * Convert phone number to email format for Firebase Auth
 * Example: '1234567890' -> '1234567890@sionyx.app'
 * This matches the desktop app's authentication system
 */
const phoneToEmail = phone => {
  // Remove all non-digit characters
  const cleanPhone = phone.replace(/\D/g, '');
  return `${cleanPhone}@sionyx.app`;
};

/**
 * Sign in admin user with phone number and organization ID
 * Admin provides their organization ID during login
 */
export const signInAdmin = async (phone, password, orgId) => {
  try {
    // Validate orgId format
    if (!orgId || orgId.trim() === '') {
      return {
        success: false,
        error: 'Organization ID is required',
      };
    }

    // Clean and validate orgId (lowercase, alphanumeric, hyphens)
    const cleanOrgId = orgId.trim().toLowerCase();
    if (!/^[a-z0-9-]+$/.test(cleanOrgId)) {
      return {
        success: false,
        error: 'Invalid Organization ID format. Use only lowercase letters, numbers, and hyphens.',
      };
    }

    // Convert phone to email format (same as desktop app)
    const email = phoneToEmail(phone);

    console.log('Signing in:', { phone, email, orgId: cleanOrgId });

    // Sign in with Firebase Auth
    const userCredential = await signInWithEmailAndPassword(auth, email, password);
    const userId = userCredential.user.uid;

    // Fetch user data from the specified organization
    // Path: organizations/{orgId}/users/{userId}
    const userRef = ref(database, `organizations/${cleanOrgId}/users/${userId}`);
    const userSnapshot = await get(userRef);

    if (!userSnapshot.exists()) {
      // User doesn't exist in this organization - sign out
      await firebaseSignOut(auth);
      return {
        success: false,
        error: `No account found in organization "${cleanOrgId}". Please verify your organization ID.`,
      };
    }

    const userData = userSnapshot.val();

    // Check if user is an admin or above (supports both role field and legacy isAdmin)
    if (!isAdminOrAbove(userData)) {
      // Not an admin - sign out
      await firebaseSignOut(auth);
      return {
        success: false,
        error: 'You do not have administrator privileges. Only admins can access this dashboard.',
      };
    }

    // Store orgId in localStorage for future use
    localStorage.setItem('adminOrgId', cleanOrgId);

    // Ensure role is set (for backwards compatibility)
    const effectiveRole = getUserRole(userData);

    // For supervisors, fetch the activation status from org settings
    let supervisorActive = undefined;
    if (effectiveRole === ROLES.SUPERVISOR) {
      try {
        const settingsRef = ref(database, `organizations/${cleanOrgId}/metadata/settings/supervisorActive`);
        const settingsSnapshot = await get(settingsRef);
        supervisorActive = settingsSnapshot.exists() ? settingsSnapshot.val() === true : false;
      } catch (e) {
        console.warn('Could not fetch supervisor activation status:', e);
        supervisorActive = false;
      }
    }

    return {
      success: true,
      user: {
        uid: userId,
        phone: phone,
        orgId: cleanOrgId,
        ...userData,
        role: effectiveRole,
        ...(supervisorActive !== undefined && { supervisorActive }),
      },
    };
  } catch (error) {
    console.error('Sign in error:', error);

    // User-friendly error messages
    let errorMessage = 'An error occurred during sign in';
    if (error.code === 'auth/invalid-credential' || error.code === 'auth/wrong-password') {
      errorMessage = 'Invalid phone number or password';
    } else if (error.code === 'auth/user-not-found') {
      errorMessage = 'No account found with this phone number';
    } else if (error.code === 'auth/too-many-requests') {
      errorMessage = 'Too many failed attempts. Please try again later';
    } else if (error.code === 'auth/network-request-failed') {
      errorMessage = 'Network error. Please check your internet connection';
    }

    return {
      success: false,
      error: errorMessage,
    };
  }
};

/**
 * Sign out admin user
 */
export const signOut = async () => {
  try {
    await firebaseSignOut(auth);
    localStorage.removeItem('adminOrgId');
    return { success: true };
  } catch (error) {
    console.error('Sign out error:', error);
    return {
      success: false,
      error: error.message,
    };
  }
};

/**
 * Get current admin data from database
 */
export const getCurrentAdminData = async () => {
  try {
    const user = auth.currentUser;
    if (!user) {
      return { success: false, error: 'Not authenticated' };
    }

    const orgId = localStorage.getItem('adminOrgId');
    if (!orgId) {
      return {
        success: false,
        error: 'Organization ID not found. Please log in again.',
      };
    }

    // Fetch user data from organization
    const userRef = ref(database, `organizations/${orgId}/users/${user.uid}`);
    const snapshot = await get(userRef);

    if (!snapshot.exists()) {
      return {
        success: false,
        error: 'User data not found',
      };
    }

    const userData = snapshot.val();

    // Verify still an admin or above (supports both role field and legacy isAdmin)
    if (!isAdminOrAbove(userData)) {
      return {
        success: false,
        error: 'Admin privileges revoked. Please contact your administrator.',
      };
    }

    // Ensure role is set (for backwards compatibility)
    const effectiveRole = getUserRole(userData);

    // For supervisors, fetch the activation status from org settings
    let supervisorActive = undefined;
    if (effectiveRole === ROLES.SUPERVISOR) {
      try {
        const settingsRef = ref(database, `organizations/${orgId}/metadata/settings/supervisorActive`);
        const settingsSnapshot = await get(settingsRef);
        supervisorActive = settingsSnapshot.exists() ? settingsSnapshot.val() === true : false;
      } catch (e) {
        console.warn('Could not fetch supervisor activation status:', e);
        supervisorActive = false;
      }
    }

    return {
      success: true,
      admin: {
        uid: user.uid,
        orgId: orgId,
        ...userData,
        role: effectiveRole,
        ...(supervisorActive !== undefined && { supervisorActive }),
      },
    };
  } catch (error) {
    console.error('Error getting admin data:', error);
    return {
      success: false,
      error: error.message,
    };
  }
};

/**
 * Listen to auth state changes
 */
export const onAuthChange = callback => {
  return onAuthStateChanged(auth, callback);
};
