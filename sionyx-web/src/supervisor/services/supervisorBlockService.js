import { ref, get, set, remove, update } from 'firebase/database';
import { database, auth } from '../../config/firebase';
import { useSupervisorAuthStore } from '../store/supervisorAuthStore';

export const blockUser = async (phone, reason, userName) => {
  try {
    const user = auth.currentUser;
    if (!user) return { success: false, error: 'Not authenticated' };

    const normalizedPhone = phone.replace(/\D/g, '');
    if (!normalizedPhone) return { success: false, error: 'Invalid phone number' };

    const orgIds = useSupervisorAuthStore.getState().getOrgIds();
    if (orgIds.length === 0) return { success: false, error: 'No supervised organizations' };

    const blockedRef = ref(database, `supervisors/${user.uid}/blockedUsers/${normalizedPhone}`);
    await set(blockedRef, {
      name: userName || '',
      reason: reason || '',
      blockedAt: Date.now(),
      blockedBy: user.uid,
    });

    let blockedCount = 0;
    for (const orgId of orgIds) {
      const usersRef = ref(database, `organizations/${orgId}/users`);
      const usersSnap = await get(usersRef);
      if (!usersSnap.exists()) continue;

      const users = usersSnap.val();
      for (const [userId, userData] of Object.entries(users)) {
        const userPhone = (userData.phoneNumber || '').replace(/\D/g, '');
        if (userPhone === normalizedPhone) {
          const userRef = ref(database, `organizations/${orgId}/users/${userId}`);
          await update(userRef, {
            blocked: true,
            blockedAt: Date.now(),
            blockedReason: reason || '',
          });
          blockedCount++;
        }
      }
    }

    return { success: true, blockedCount, message: `User blocked in ${blockedCount} organization(s)` };
  } catch (error) {
    return { success: false, error: error.message };
  }
};

export const unblockUser = async phone => {
  try {
    const user = auth.currentUser;
    if (!user) return { success: false, error: 'Not authenticated' };

    const normalizedPhone = phone.replace(/\D/g, '');
    const orgIds = useSupervisorAuthStore.getState().getOrgIds();

    const blockedRef = ref(database, `supervisors/${user.uid}/blockedUsers/${normalizedPhone}`);
    await remove(blockedRef);

    let unblockedCount = 0;
    for (const orgId of orgIds) {
      const usersRef = ref(database, `organizations/${orgId}/users`);
      const usersSnap = await get(usersRef);
      if (!usersSnap.exists()) continue;

      const users = usersSnap.val();
      for (const [userId, userData] of Object.entries(users)) {
        const userPhone = (userData.phoneNumber || '').replace(/\D/g, '');
        if (userPhone === normalizedPhone) {
          const userRef = ref(database, `organizations/${orgId}/users/${userId}`);
          await update(userRef, {
            blocked: false,
            blockedAt: null,
            blockedReason: null,
          });
          unblockedCount++;
        }
      }
    }

    return { success: true, unblockedCount, message: `User unblocked in ${unblockedCount} organization(s)` };
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
