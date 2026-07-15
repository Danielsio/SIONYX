import { ref, get } from 'firebase/database';
import { database } from '../config/firebase';
import { logger } from '../utils/logger';

/**
 * Read the org's session logs (an audit trail the kiosk appends on every
 * session end). Stored at organizations/$orgId/sessionLogs/$userId/$ts; admin
 * read is enforced by the RTDB rules. Flattened to a list for the report.
 */
export const getSessionLogs = async orgId => {
  try {
    const snapshot = await get(ref(database, `organizations/${orgId}/sessionLogs`));
    if (!snapshot.exists()) return { success: true, logs: [] };

    const byUser = snapshot.val();
    const logs = [];
    for (const userId of Object.keys(byUser)) {
      const entries = byUser[userId] || {};
      for (const logId of Object.keys(entries)) {
        logs.push({ id: `${userId}/${logId}`, ...entries[logId] });
      }
    }
    // Newest first.
    logs.sort((a, b) => new Date(b.endTime || 0) - new Date(a.endTime || 0));
    return { success: true, logs };
  } catch (error) {
    logger.error('Error getting session logs:', error);
    return { success: false, error: error.message };
  }
};
