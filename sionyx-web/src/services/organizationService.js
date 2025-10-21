import { database } from '../config/firebase';
import { ref, set, get } from 'firebase/database';

/**
 * Organization Service
 * 
 * This service handles organization-related operations including:
 * - Registration of new organizations
 * - Retrieving organization metadata (including NEDARIM credentials)
 * - Getting organization statistics for the admin dashboard
 */

// Simple base64 encoding for sensitive data (can be upgraded to proper encryption later)
const encodeData = (data) => {
  return btoa(JSON.stringify(data));
};

const decodeData = (encodedData) => {
  try {
    return JSON.parse(atob(encodedData));
  } catch (error) {
    console.error('Error decoding data:', error);
    return null;
  }
};

/**
 * Register a new organization
 * 
 * WHY NEEDED: Landing page needs this to register new organizations
 * with their NEDARIM credentials for payment processing
 * 
 * @param {Object} organizationData - Organization details including NEDARIM credentials
 * @returns {Object} Success status and organization ID
 */
export const registerOrganization = async (organizationData) => {
  try {
    const { organizationName, nedarimMosadId, nedarimApiValid } = organizationData;
    
    // Check if organization name already exists
    const orgsRef = ref(database, 'org/metadata');
    const snapshot = await get(orgsRef);
    
    if (snapshot.exists()) {
      const organizations = snapshot.val();
      const existingOrg = Object.values(organizations).find(org => 
        org.name && org.name.toLowerCase() === organizationName.toLowerCase()
      );
      
      if (existingOrg) {
        return {
          success: false,
          error: 'Organization name already exists'
        };
      }
    }
    
    // Generate organization ID (simple timestamp-based for now)
    const orgId = `org_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    // Prepare metadata with encrypted sensitive data
    const metadata = {
      name: organizationName,
      nedarim_mosad_id: encodeData(nedarimMosadId),
      nedarim_api_valid: encodeData(nedarimApiValid),
      created_at: new Date().toISOString(),
      status: 'active'
    };
    
    // Save to Firebase (will be validated by database rules)
    const orgRef = ref(database, `org/metadata/${orgId}`);
    await set(orgRef, metadata);
    
    return {
      success: true,
      orgId,
      message: 'Organization registered successfully'
    };
    
  } catch (error) {
    console.error('Error registering organization:', error);
    
    // Handle specific Firebase errors
    if (error.message && error.message.includes('permission')) {
      return {
        success: false,
        error: 'Permission denied. Please contact support.'
      };
    }
    
    return {
      success: false,
      error: 'Failed to register organization'
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
export const getOrganizationMetadata = async (orgId) => {
  try {
    const orgRef = ref(database, `org/metadata/${orgId}`);
    const snapshot = await get(orgRef);
    
    if (snapshot.exists()) {
      const data = snapshot.val();
      return {
        success: true,
        metadata: {
          ...data,
          nedarim_mosad_id: decodeData(data.nedarim_mosad_id),
          nedarim_api_valid: decodeData(data.nedarim_api_valid)
        }
      };
    } else {
      return {
        success: false,
        error: 'Organization not found'
      };
    }
  } catch (error) {
    console.error('Error getting organization metadata:', error);
    return {
      success: false,
      error: 'Failed to get organization metadata'
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
export const getOrganizationStats = async (orgId) => {
  try {
    // Get users count
    const usersRef = ref(database, `organizations/${orgId}/users`);
    const usersSnapshot = await get(usersRef);
    const usersCount = usersSnapshot.exists() ? Object.keys(usersSnapshot.val()).length : 0;

    // Get packages count
    const packagesRef = ref(database, `organizations/${orgId}/packages`);
    const packagesSnapshot = await get(packagesRef);
    const packagesCount = packagesSnapshot.exists() ? Object.keys(packagesSnapshot.val()).length : 0;

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
        totalTimeMinutes
      }
    };

  } catch (error) {
    console.error('Error getting organization stats:', error);
    return {
      success: false,
      error: 'Failed to get organization statistics'
    };
  }
};