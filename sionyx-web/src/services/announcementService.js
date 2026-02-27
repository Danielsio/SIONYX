import { ref, get, set, update, remove, push } from 'firebase/database';
import { database } from '../config/firebase';
import { logger } from '../utils/logger';

/**
 * Get all announcements for an organization
 */
export const getAllAnnouncements = async orgId => {
  try {
    const announcementsRef = ref(database, `organizations/${orgId}/announcements`);
    const snapshot = await get(announcementsRef);

    if (!snapshot.exists()) {
      return { success: true, announcements: [] };
    }

    const data = snapshot.val();
    const announcements = Object.keys(data).map(id => ({
      id,
      ...data[id],
    }));

    announcements.sort((a, b) => {
      const dateA = new Date(a.createdAt || 0);
      const dateB = new Date(b.createdAt || 0);
      return dateB - dateA;
    });

    return { success: true, announcements };
  } catch (error) {
    logger.error('Error getting announcements:', error);
    return { success: false, error: error.message, announcements: [] };
  }
};

/**
 * Create a new announcement
 */
export const createAnnouncement = async (orgId, data) => {
  try {
    const announcementsRef = ref(database, `organizations/${orgId}/announcements`);
    const newRef = push(announcementsRef);

    const announcement = {
      title: data.title,
      body: data.body || '',
      type: data.type || 'info',
      active: data.active !== false,
      startDate: data.startDate || null,
      endDate: data.endDate || null,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    await set(newRef, announcement);
    return { success: true, id: newRef.key };
  } catch (error) {
    logger.error('Error creating announcement:', error);
    return { success: false, error: error.message };
  }
};

/**
 * Update an existing announcement
 */
export const updateAnnouncement = async (orgId, id, updates) => {
  try {
    const announcementRef = ref(database, `organizations/${orgId}/announcements/${id}`);
    await update(announcementRef, {
      ...updates,
      updatedAt: new Date().toISOString(),
    });
    return { success: true };
  } catch (error) {
    logger.error('Error updating announcement:', error);
    return { success: false, error: error.message };
  }
};

/**
 * Delete an announcement
 */
export const deleteAnnouncement = async (orgId, id) => {
  try {
    const announcementRef = ref(database, `organizations/${orgId}/announcements/${id}`);
    await remove(announcementRef);
    return { success: true };
  } catch (error) {
    logger.error('Error deleting announcement:', error);
    return { success: false, error: error.message };
  }
};

/**
 * Toggle an announcement's active status
 */
export const toggleAnnouncementActive = async (orgId, id, active) => {
  return updateAnnouncement(orgId, id, { active });
};
