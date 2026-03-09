import { ref, get } from 'firebase/database';
import { database, auth } from '../../config/firebase';
import { useSupervisorAuthStore } from '../store/supervisorAuthStore';

export const getSupervisorOrgs = async () => {
  try {
    const user = auth.currentUser;
    if (!user) return { success: false, error: 'Not authenticated', organizations: [] };

    const orgIds = useSupervisorAuthStore.getState().getOrgIds();

    const orgs = [];
    for (const orgId of orgIds) {
      const [metadataSnap, usersSnap, purchasesSnap] = await Promise.all([
        get(ref(database, `organizations/${orgId}/metadata`)),
        get(ref(database, `organizations/${orgId}/users`)),
        get(ref(database, `organizations/${orgId}/purchases`)),
      ]);

      const metadata = metadataSnap.exists() ? metadataSnap.val() : {};
      const users = usersSnap.exists() ? usersSnap.val() : {};
      const purchases = purchasesSnap.exists() ? purchasesSnap.val() : {};

      const userCount = Object.keys(users).length;
      const activeUsers = Object.values(users).filter(u => u.isSessionActive).length;

      let totalRevenue = 0;
      Object.values(purchases).forEach(p => {
        if (p.status === 'completed' && p.amount) {
          totalRevenue += parseFloat(p.amount) || 0;
        }
      });

      orgs.push({
        orgId,
        name: metadata.name || orgId,
        status: metadata.status || 'unknown',
        userCount,
        activeUsers,
        totalRevenue,
        createdAt: metadata.created_at || null,
      });
    }

    const blockedRef = ref(database, `supervisors/${user.uid}/blockedUsers`);
    const blockedSnap = await get(blockedRef);
    const blockedUsersCount = blockedSnap.exists() ? Object.keys(blockedSnap.val()).length : 0;

    return { success: true, organizations: orgs, blockedUsersCount };
  } catch (error) {
    return { success: false, error: error.message, organizations: [] };
  }
};

export const getOrgUsers = async orgId => {
  try {
    const usersRef = ref(database, `organizations/${orgId}/users`);
    const snapshot = await get(usersRef);
    if (!snapshot.exists()) return { success: true, users: [] };

    const usersData = snapshot.val();
    const users = Object.keys(usersData).map(uid => ({ uid, ...usersData[uid] }));
    users.sort((a, b) => new Date(b.createdAt || 0) - new Date(a.createdAt || 0));
    return { success: true, users };
  } catch (error) {
    return { success: false, error: error.message, users: [] };
  }
};

export const getOrgPackages = async orgId => {
  try {
    const packagesRef = ref(database, `organizations/${orgId}/packages`);
    const snapshot = await get(packagesRef);
    if (!snapshot.exists()) return { success: true, packages: [] };

    const data = snapshot.val();
    const packages = Object.keys(data).map(id => ({ id, ...data[id] }));
    return { success: true, packages };
  } catch (error) {
    return { success: false, error: error.message, packages: [] };
  }
};

export const getOrgComputers = async orgId => {
  try {
    const computersRef = ref(database, `organizations/${orgId}/computers`);
    const snapshot = await get(computersRef);
    if (!snapshot.exists()) return { success: true, computers: [] };

    const data = snapshot.val();
    const computers = Object.keys(data).map(id => ({ id, ...data[id] }));
    return { success: true, computers };
  } catch (error) {
    return { success: false, error: error.message, computers: [] };
  }
};
