import { database, functions } from '../config/firebase';
import { ref, get } from 'firebase/database';
import { httpsCallable } from 'firebase/functions';
import { useAuthStore } from '../store/authStore';
import { isSupervisorPendingActivation } from '../utils/roles';

/**
 * Organization Service
 *
 * This service handles organization-related operations including:
 * - Registration of new organizations
 * - Retrieving organization metadata (including NEDARIM credentials)
 * - Getting organization statistics for the admin dashboard
 */

// Simple base64 encoding for sensitive data (can be upgraded to proper encryption later)
const encodeData = data => {
  return btoa(JSON.stringify(data));
};

const decodeData = encodedData => {
  try {
    return JSON.parse(atob(encodedData));
  } catch (error) {
    console.error('Error decoding data:', error);
    return null;
  }
};

// New encryption format used by Cloud Function (base64 encoded JSON)
const decodeCloudFunctionData = encodedData => {
  try {
    // The Cloud Function uses Buffer.from(JSON.stringify(data)).toString('base64')
    // So we need to decode it back
    const jsonString = atob(encodedData);
    return JSON.parse(jsonString);
  } catch (error) {
    console.error('Error decoding Cloud Function data:', error);
    return null;
  }
};

/**
 * Register a new organization via Cloud Function
 *
 * WHY NEEDED: Landing page needs this to register new organizations
 * with their NEDARIM credentials for payment processing
 *
 * @param {Object} organizationData - Organization details including NEDARIM credentials
 * @returns {Object} Success status and organization ID
 */
export const registerOrganization = async organizationData => {
  try {
    console.log('Calling Cloud Function for organization registration:', {
      hasData: !!organizationData,
    });

    // Initialize Firebase Functions
    const registerOrg = httpsCallable(functions, 'registerOrganization');

    // Call the Cloud Function
    const result = await registerOrg(organizationData);

    console.log('Organization registered successfully:', result.data);
    return result.data;
  } catch (error) {
    console.error('Error calling Cloud Function:', error);

    // Handle Firebase Functions errors
    if (error.code) {
      return {
        success: false,
        error: error.message || 'Registration failed',
      };
    }

    return {
      success: false,
      error: 'Failed to register organization. Please try again.',
    };
  }
};

/**
 * Get organization metadata including NEDARIM credentials
 *
 * WHY NEEDED: Python client needs this to fetch NEDARIM credentials
 * from database instead of environment variables for payment processing
 *
 * @param {string} orgId - Organization ID
 * @returns {Object} Success status and decoded metadata
 */
export const getOrganizationMetadata = async orgId => {
  try {
    const orgRef = ref(database, `organizations/${orgId}/metadata`);
    const snapshot = await get(orgRef);

    if (snapshot.exists()) {
      const data = snapshot.val();

      // Try both decoding methods for backward compatibility
      let decodedMosadId, decodedApiValid;

      try {
        // Try new Cloud Function format first
        decodedMosadId = decodeCloudFunctionData(data.nedarim_mosad_id);
        decodedApiValid = decodeCloudFunctionData(data.nedarim_api_valid);
      } catch (error) {
        // Fall back to old format
        decodedMosadId = decodeData(data.nedarim_mosad_id);
        decodedApiValid = decodeData(data.nedarim_api_valid);
      }

      return {
        success: true,
        metadata: {
          ...data,
          nedarim_mosad_id: decodedMosadId,
          nedarim_api_valid: decodedApiValid,
        },
      };
    } else {
      return {
        success: false,
        error: 'Organization not found',
      };
    }
  } catch (error) {
    console.error('Error getting organization metadata:', error);
    return {
      success: false,
      error: 'Failed to get organization metadata',
    };
  }
};

/**
 * Get organization statistics for admin dashboard
 *
 * WHY NEEDED: OverviewPage needs this to display dashboard statistics
 * including user count, package count, purchases, revenue, and time metrics
 *
 * @param {string} orgId - Organization ID
 * @returns {Object} Success status and statistics data
 */
export const getOrganizationStats = async orgId => {
  // Supervisor activation gate: return zero stats if not yet activated
  if (isSupervisorPendingActivation(useAuthStore.getState().user)) {
    return {
      success: true,
      stats: {
        usersCount: 0,
        packagesCount: 0,
        purchasesCount: 0,
        totalRevenue: 0,
        totalTimeMinutes: 0,
      },
    };
  }

  try {
    // Get users count
    const usersRef = ref(database, `organizations/${orgId}/users`);
    const usersSnapshot = await get(usersRef);
    const usersCount = usersSnapshot.exists() ? Object.keys(usersSnapshot.val()).length : 0;

    // Get packages count
    const packagesRef = ref(database, `organizations/${orgId}/packages`);
    const packagesSnapshot = await get(packagesRef);
    const packagesCount = packagesSnapshot.exists()
      ? Object.keys(packagesSnapshot.val()).length
      : 0;

    // Get purchases count and total revenue
    const purchasesRef = ref(database, `organizations/${orgId}/purchases`);
    const purchasesSnapshot = await get(purchasesRef);

    let purchasesCount = 0;
    let totalRevenue = 0;
    let totalTimeMinutes = 0;

    if (purchasesSnapshot.exists()) {
      const purchases = purchasesSnapshot.val();
      purchasesCount = Object.keys(purchases).length;

      // Calculate totals
      Object.values(purchases).forEach(purchase => {
        if (purchase.status === 'completed' && purchase.amount) {
          totalRevenue += parseFloat(purchase.amount) || 0;
        }
        if (purchase.minutes) {
          totalTimeMinutes += parseInt(purchase.minutes) || 0;
        }
      });
    }

    return {
      success: true,
      stats: {
        usersCount,
        packagesCount,
        purchasesCount,
        totalRevenue,
        totalTimeMinutes,
      },
    };
  } catch (error) {
    console.error('Error getting organization stats:', error);
    return {
      success: false,
      error: 'Failed to get organization statistics',
    };
  }
};
