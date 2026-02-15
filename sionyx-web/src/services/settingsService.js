import { ref, get, update } from 'firebase/database';
import { database } from '../config/firebase';
import { logger } from '../utils/logger';

/**
 * Settings Service for Admin Dashboard
 * Handles organization settings management
 *
 * Settings are stored in: organizations/{orgId}/metadata/settings/
 */

// Default values for settings
export const DEFAULT_OPERATING_HOURS = {
  enabled: false,
  startTime: '06:00',
  endTime: '00:00',
  gracePeriodMinutes: 5,
  graceBehavior: 'graceful', // 'graceful' | 'force'
};

/**
 * Get operating hours settings for an organization
 */
export const getOperatingHours = async orgId => {
  try {
    const settingsRef = ref(database, `organizations/${orgId}/metadata/settings/operatingHours`);
    const snapshot = await get(settingsRef);

    if (!snapshot.exists()) {
      // Return defaults if not set
      return {
        success: true,
        operatingHours: { ...DEFAULT_OPERATING_HOURS },
      };
    }

    const data = snapshot.val();
    // Merge with defaults to ensure all fields exist
    const operatingHours = {
      ...DEFAULT_OPERATING_HOURS,
      ...data,
    };

    return {
      success: true,
      operatingHours,
    };
  } catch (error) {
    logger.error('Error getting operating hours:', error);
    return {
      success: false,
      error: 'Failed to get operating hours settings',
    };
  }
};

/**
 * Update operating hours settings for an organization
 */
export const updateOperatingHours = async (orgId, operatingHoursData) => {
  try {
    logger.info('Updating operating hours for org:', orgId, 'with data:', operatingHoursData);

    const settingsRef = ref(database, `organizations/${orgId}/metadata/settings/operatingHours`);

    // Validate data
    const { enabled, startTime, endTime, gracePeriodMinutes, graceBehavior } = operatingHoursData;

    if (typeof enabled !== 'boolean') {
      return {
        success: false,
        error: 'enabled must be a boolean',
      };
    }

    if (!/^\d{2}:\d{2}$/.test(startTime) || !/^\d{2}:\d{2}$/.test(endTime)) {
      return {
        success: false,
        error: 'Times must be in HH:mm format',
      };
    }

    if (typeof gracePeriodMinutes !== 'number' || gracePeriodMinutes < 0) {
      return {
        success: false,
        error: 'Grace period must be a non-negative number',
      };
    }

    if (!['graceful', 'force'].includes(graceBehavior)) {
      return {
        success: false,
        error: 'Grace behavior must be "graceful" or "force"',
      };
    }

    const updateData = {
      enabled,
      startTime,
      endTime,
      gracePeriodMinutes: parseInt(gracePeriodMinutes, 10),
      graceBehavior,
    };

    await update(settingsRef, updateData);

    logger.info('Operating hours updated successfully');
    return {
      success: true,
      message: 'Operating hours updated successfully',
    };
  } catch (error) {
    logger.error('Error updating operating hours:', error);
    return {
      success: false,
      error: `Failed to update operating hours: ${error.message}`,
    };
  }
};

/**
 * Get all settings for an organization (for future use)
 */
export const getAllSettings = async orgId => {
  try {
    const metadataRef = ref(database, `organizations/${orgId}/metadata`);
    const snapshot = await get(metadataRef);

    if (!snapshot.exists()) {
      return {
        success: false,
        error: 'Organization metadata not found',
      };
    }

    const metadata = snapshot.val();

    return {
      success: true,
      settings: {
        pricing: {
          blackAndWhitePrice: metadata.blackAndWhitePrice || 1.0,
          colorPrice: metadata.colorPrice || 3.0,
        },
        operatingHours: {
          ...DEFAULT_OPERATING_HOURS,
          ...(metadata.settings?.operatingHours || {}),
        },
      },
    };
  } catch (error) {
    logger.error('Error getting all settings:', error);
    return {
      success: false,
      error: 'Failed to get settings',
    };
  }
};
