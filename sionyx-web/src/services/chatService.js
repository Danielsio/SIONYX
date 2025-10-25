import {
  ref,
  get,
  set,
  push,
  update,
  query,
  orderByChild,
  equalTo,
  onValue,
} from 'firebase/database';
import { database } from '../config/firebase';

/**
 * Send a message from admin to user
 */
export const sendMessage = async (orgId, toUserId, message, fromAdminId) => {
  try {
    const messagesRef = ref(database, `organizations/${orgId}/messages`);
    const newMessageRef = push(messagesRef);

    const messageData = {
      id: newMessageRef.key,
      fromAdminId,
      toUserId,
      message: message.trim(),
      timestamp: new Date().toISOString(),
      read: false,
      orgId,
    };

    await set(newMessageRef, messageData);

    return {
      success: true,
      messageId: newMessageRef.key,
      message: messageData,
    };
  } catch (error) {
    console.error('Error sending message:', error);
    return {
      success: false,
      error: error.message,
    };
  }
};

/**
 * Get all messages for an organization (admin view)
 */
export const getAllMessages = async orgId => {
  try {
    const messagesRef = ref(database, `organizations/${orgId}/messages`);
    const snapshot = await get(messagesRef);

    if (!snapshot.exists()) {
      return {
        success: true,
        messages: [],
      };
    }

    const messagesData = snapshot.val();
    const messages = Object.keys(messagesData).map(key => ({
      id: key,
      ...messagesData[key],
    }));

    // Sort by timestamp (newest first)
    messages.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));

    return {
      success: true,
      messages,
    };
  } catch (error) {
    console.error('Error getting messages:', error);
    return {
      success: false,
      error: error.message,
      messages: [],
    };
  }
};

/**
 * Get messages for a specific user (admin view)
 */
export const getMessagesForUser = async (orgId, userId) => {
  try {
    const messagesRef = ref(database, `organizations/${orgId}/messages`);
    const userMessagesQuery = query(messagesRef, orderByChild('toUserId'), equalTo(userId));

    const snapshot = await get(userMessagesQuery);

    if (!snapshot.exists()) {
      return {
        success: true,
        messages: [],
      };
    }

    const messagesData = snapshot.val();
    const messages = Object.keys(messagesData).map(key => ({
      id: key,
      ...messagesData[key],
    }));

    // Sort by timestamp (newest first)
    messages.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));

    return {
      success: true,
      messages,
    };
  } catch (error) {
    console.error('Error getting user messages:', error);
    return {
      success: false,
      error: error.message,
      messages: [],
    };
  }
};

/**
 * Get unread messages for a user (client view)
 */
export const getUnreadMessages = async (orgId, userId) => {
  try {
    const messagesRef = ref(database, `organizations/${orgId}/messages`);
    const userMessagesQuery = query(messagesRef, orderByChild('toUserId'), equalTo(userId));

    const snapshot = await get(userMessagesQuery);

    if (!snapshot.exists()) {
      return {
        success: true,
        messages: [],
      };
    }

    const messagesData = snapshot.val();
    const messages = Object.keys(messagesData)
      .map(key => ({
        id: key,
        ...messagesData[key],
      }))
      .filter(msg => !msg.read);

    // Sort by timestamp (oldest first for display)
    messages.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));

    return {
      success: true,
      messages,
    };
  } catch (error) {
    console.error('Error getting unread messages:', error);
    return {
      success: false,
      error: error.message,
      messages: [],
    };
  }
};

/**
 * Mark message as read
 */
export const markMessageAsRead = async (orgId, messageId) => {
  try {
    const messageRef = ref(database, `organizations/${orgId}/messages/${messageId}`);

    await update(messageRef, {
      read: true,
      readAt: new Date().toISOString(),
    });

    return {
      success: true,
    };
  } catch (error) {
    console.error('Error marking message as read:', error);
    return {
      success: false,
      error: error.message,
    };
  }
};

/**
 * Listen to real-time messages for a user (client)
 */
export const listenToUserMessages = (orgId, userId, callback) => {
  const messagesRef = ref(database, `organizations/${orgId}/messages`);
  const userMessagesQuery = query(messagesRef, orderByChild('toUserId'), equalTo(userId));

  const unsubscribe = onValue(
    userMessagesQuery,
    snapshot => {
      if (snapshot.exists()) {
        const messagesData = snapshot.val();
        const messages = Object.keys(messagesData).map(key => ({
          id: key,
          ...messagesData[key],
        }));

        // Sort by timestamp (oldest first for display)
        messages.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));

        callback({
          success: true,
          messages,
        });
      } else {
        callback({
          success: true,
          messages: [],
        });
      }
    },
    error => {
      console.error('Error listening to messages:', error);
      callback({
        success: false,
        error: error.message,
        messages: [],
      });
    }
  );

  return unsubscribe;
};

/**
 * Update user's last seen timestamp
 */
export const updateUserLastSeen = async (orgId, userId) => {
  try {
    const userRef = ref(database, `organizations/${orgId}/users/${userId}`);

    await update(userRef, {
      lastSeen: new Date().toISOString(),
    });

    return {
      success: true,
    };
  } catch (error) {
    console.error('Error updating last seen:', error);
    return {
      success: false,
      error: error.message,
    };
  }
};

/**
 * Get user's online status (active if last seen within 5 minutes)
 */
export const isUserActive = lastSeen => {
  if (!lastSeen) return false;

  const lastSeenTime = new Date(lastSeen);
  const now = new Date();
  const diffMinutes = (now - lastSeenTime) / (1000 * 60);

  return diffMinutes <= 5; // Active if last seen within 5 minutes
};
