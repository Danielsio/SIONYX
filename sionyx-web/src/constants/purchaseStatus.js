/**
 * Purchase Status Constants
 * Unified constants for purchase status values across the application
 * Database stores English values, UI displays Hebrew labels
 */

// Database values (English) - used in Firebase and all services
export const PURCHASE_STATUS = {
  PENDING: 'pending',
  COMPLETED: 'completed',
  FAILED: 'failed',
};

// Display labels (Hebrew) - used in UI
export const PURCHASE_STATUS_LABELS = {
  [PURCHASE_STATUS.PENDING]: 'ממתין',
  [PURCHASE_STATUS.COMPLETED]: 'הושלם',
  [PURCHASE_STATUS.FAILED]: 'נכשל',
};

// Status colors for UI components
export const PURCHASE_STATUS_COLORS = {
  [PURCHASE_STATUS.PENDING]: 'processing',
  [PURCHASE_STATUS.COMPLETED]: 'success',
  [PURCHASE_STATUS.FAILED]: 'error',
};

// Helper function to get Hebrew label for status
export const getStatusLabel = status => {
  return PURCHASE_STATUS_LABELS[status] || status;
};

// Helper function to get color for status
export const getStatusColor = status => {
  return PURCHASE_STATUS_COLORS[status] || 'default';
};

// Helper function to check if status is final (completed or failed)
export const isFinalStatus = status => {
  return status === PURCHASE_STATUS.COMPLETED || status === PURCHASE_STATUS.FAILED;
};
