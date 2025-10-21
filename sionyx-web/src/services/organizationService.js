import { database } from '../config/firebase';
import { ref, set, get } from 'firebase/database';

// Simple base64 encoding for now (can be upgraded to proper encryption later)
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

export const registerOrganization = async (organizationData) => {
  try {
    const { organizationName, nedarimMosadId, nedarimApiValid } = organizationData;
    
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
    
    // Save to Firebase
    const orgRef = ref(database, `org/metadata/${orgId}`);
    await set(orgRef, metadata);
    
    return {
      success: true,
      orgId,
      message: 'Organization registered successfully'
    };
    
  } catch (error) {
    console.error('Error registering organization:', error);
    return {
      success: false,
      error: 'Failed to register organization'
    };
  }
};

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

export const getAllOrganizations = async () => {
  try {
    const orgsRef = ref(database, 'org/metadata');
    const snapshot = await get(orgsRef);
    
    if (snapshot.exists()) {
      const organizations = snapshot.val();
      return {
        success: true,
        organizations: Object.keys(organizations).map(orgId => ({
          orgId,
          name: organizations[orgId].name,
          created_at: organizations[orgId].created_at,
          status: organizations[orgId].status
        }))
      };
    } else {
      return {
        success: true,
        organizations: []
      };
    }
  } catch (error) {
    console.error('Error getting all organizations:', error);
    return {
      success: false,
      error: 'Failed to get organizations'
    };
  }
};