import { ref, get, push, set } from 'firebase/database';
import { database } from '../../config/firebase';

export const getOrgMessages = async orgId => {
  try {
    const snap = await get(ref(database, `organizations/${orgId}/messages`));
    if (!snap.exists()) return { success: true, messages: [] };

    const data = snap.val();
    const messages = Object.entries(data).map(([id, msg]) => ({ id, ...msg }));
    messages.sort((a, b) => b.timestamp - a.timestamp);
    return { success: true, messages };
  } catch (error) {
    return { success: false, error: error.message, messages: [] };
  }
};

export const sendSupervisorMessage = async (orgId, toUserId, messageText, supervisorId) => {
  try {
    const messagesRef = ref(database, `organizations/${orgId}/messages`);
    const newRef = push(messagesRef);

    await set(newRef, {
      fromAdminId: supervisorId,
      fromSupervisor: true,
      toUserId,
      message: messageText.trim(),
      timestamp: Date.now(),
      read: false,
    });

    return { success: true, messageId: newRef.key };
  } catch (error) {
    return { success: false, error: error.message };
  }
};
