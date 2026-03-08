import { httpsCallable } from 'firebase/functions';
import { ref, get } from 'firebase/database';
import { database, functions } from '../../config/firebase';
import { auth } from '../../config/firebase';

export const blockUser = async (phone, reason, userName) => {
  try {
    const fn = httpsCallable(functions, 'blockUser');
    const result = await fn({ phone, reason, userName });
    return result.data;
  } catch (error) {
    return { success: false, error: error.message };
  }
};

export const unblockUser = async phone => {
  try {
    const fn = httpsCallable(functions, 'unblockUser');
    const result = await fn({ phone });
    return result.data;
  } catch (error) {
    return { success: false, error: error.message };
  }
};

export const getBlockedUsers = async () => {
  try {
    const user = auth.currentUser;
    if (!user) return { success: false, error: 'Not authenticated', blockedUsers: [] };

    const blockedRef = ref(database, `supervisors/${user.uid}/blockedUsers`);
    const snapshot = await get(blockedRef);

    if (!snapshot.exists()) return { success: true, blockedUsers: [] };

    const data = snapshot.val();
    const blockedUsers = Object.keys(data).map(phone => ({
      phone,
      ...data[phone],
    }));

    blockedUsers.sort((a, b) => (b.blockedAt || 0) - (a.blockedAt || 0));
    return { success: true, blockedUsers };
  } catch (error) {
    return { success: false, error: error.message, blockedUsers: [] };
  }
};
