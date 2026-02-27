import { ref, onValue } from 'firebase/database';
import { database } from '../config/firebase';
import { logger } from '../utils/logger';
import { useNotificationStore } from '../store/notificationStore';

// Track previous message counts per org for new-message notifications
const prevMessageCountByOrg = new Map();

/**
 * Subscribe to real-time updates for users
 * @param {string} orgId - Organization ID
 * @param {Function} callback - Callback receiving user list
 * @returns {Function} Unsubscribe function
 */
export const subscribeToUsers = (orgId, callback) => {
  if (!orgId) return () => {};
  const usersRef = ref(database, `organizations/${orgId}/users`);
  return onValue(
    usersRef,
    snapshot => {
      if (snapshot.exists()) {
        const users = snapshot.val();
        const userList = Object.keys(users).map(uid => ({ uid, ...users[uid] }));
        callback(userList);
      } else {
        callback([]);
      }
    },
    error => {
      logger.error('Users listener error:', error);
    }
  );
};

/**
 * Subscribe to real-time updates for messages
 * Fires in-app notification when new messages arrive (count increases)
 * @param {string} orgId - Organization ID
 * @param {Function} callback - Callback receiving message list
 * @returns {Function} Unsubscribe function
 */
export const subscribeToMessages = (orgId, callback) => {
  if (!orgId) return () => {};
  const messagesRef = ref(database, `organizations/${orgId}/messages`);
  return onValue(
    messagesRef,
    snapshot => {
      if (snapshot.exists()) {
        const messages = snapshot.val();
        const messageList = Object.keys(messages).map(id => ({ id, ...messages[id] }));
        const prevCount = prevMessageCountByOrg.get(orgId) ?? 0;
        if (prevCount > 0 && messageList.length > prevCount) {
          useNotificationStore.getState().addNotification({
            type: 'message',
            message: 'הודעה חדשה התקבלה',
          });
        }
        prevMessageCountByOrg.set(orgId, messageList.length);
        callback(messageList);
      } else {
        prevMessageCountByOrg.set(orgId, 0);
        callback([]);
      }
    },
    error => {
      logger.error('Messages listener error:', error);
    }
  );
};

/**
 * Subscribe to real-time updates for computers
 * @param {string} orgId - Organization ID
 * @param {Function} callback - Callback receiving computer list
 * @returns {Function} Unsubscribe function
 */
export const subscribeToComputers = (orgId, callback) => {
  if (!orgId) return () => {};
  const computersRef = ref(database, `organizations/${orgId}/computers`);
  return onValue(
    computersRef,
    snapshot => {
      if (snapshot.exists()) {
        const computers = snapshot.val();
        const computerList = Object.keys(computers).map(id => ({ id, ...computers[id] }));
        callback(computerList);
      } else {
        callback([]);
      }
    },
    error => {
      logger.error('Computers listener error:', error);
    }
  );
};

/**
 * Subscribe to real-time updates for announcements
 * @param {string} orgId - Organization ID
 * @param {Function} callback - Callback receiving announcement list
 * @returns {Function} Unsubscribe function
 */
export const subscribeToAnnouncements = (orgId, callback) => {
  if (!orgId) return () => {};
  const announcementsRef = ref(database, `organizations/${orgId}/announcements`);
  return onValue(
    announcementsRef,
    snapshot => {
      if (snapshot.exists()) {
        const announcements = snapshot.val();
        const list = Object.keys(announcements).map(id => ({ id, ...announcements[id] }));
        callback(list);
      } else {
        callback([]);
      }
    },
    error => {
      logger.error('Announcements listener error:', error);
    }
  );
};
