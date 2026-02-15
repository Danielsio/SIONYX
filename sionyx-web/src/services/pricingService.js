import { ref, get, update } from 'firebase/database';
import { database } from '../config/firebase';
import { logger } from '../utils/logger';

/**
 * Print Pricing Service for Admin Dashboard
 * Handles print pricing management (black & white and color prints)
 */

/**
 * Get current print pricing for an organization
 */
export const getPrintPricing = async orgId => {
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
    const pricing = {
      blackAndWhitePrice: metadata.blackAndWhitePrice || 1.0,
      colorPrice: metadata.colorPrice || 3.0,
    };

    return {
      success: true,
      pricing,
    };
  } catch (error) {
    logger.error('Error getting print pricing:', error);
    return {
      success: false,
      error: 'Failed to get print pricing',
    };
  }
};

/**
 * Update print pricing for an organization
 */
export const updatePrintPricing = async (orgId, pricingData) => {
  try {
    logger.info('Updating print pricing for org:', orgId, 'with data:', pricingData);
    
    const metadataRef = ref(database, `organizations/${orgId}/metadata`);
    
    // Validate pricing data
    const { blackAndWhitePrice, colorPrice } = pricingData;
    
    if (typeof blackAndWhitePrice !== 'number' && typeof blackAndWhitePrice !== 'string' ||
        typeof colorPrice !== 'number' && typeof colorPrice !== 'string' ||
        Number(blackAndWhitePrice) <= 0 || Number(colorPrice) <= 0) {
      return {
        success: false,
        error: 'Prices must be greater than 0',
      };
    }

    const updateData = {
      blackAndWhitePrice: parseFloat(blackAndWhitePrice),
      colorPrice: parseFloat(colorPrice),
    };

    logger.info('Update data:', updateData);
    logger.info('Database path:', `organizations/${orgId}/metadata`);

    await update(metadataRef, updateData);

    logger.info('Print pricing updated successfully');
    return {
      success: true,
      message: 'Print pricing updated successfully',
    };
  } catch (error) {
    logger.error('Error updating print pricing:', error);
    return {
      success: false,
      error: `Failed to update print pricing: ${error.message}`,
    };
  }
};
