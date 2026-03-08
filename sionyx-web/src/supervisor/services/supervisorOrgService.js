import { httpsCallable } from 'firebase/functions';
import { ref, get } from 'firebase/database';
import { database, functions } from '../../config/firebase';

export const getSupervisorOrgs = async () => {
  try {
    const fn = httpsCallable(functions, 'getSupervisorOrgs');
    const result = await fn({});
    return result.data;
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
