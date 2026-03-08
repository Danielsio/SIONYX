import { httpsCallable } from 'firebase/functions';
import { ref, get } from 'firebase/database';
import { database, functions } from '../../config/firebase';

export const getOrgOperatingHours = async orgId => {
  try {
    const settingsRef = ref(database, `organizations/${orgId}/metadata/settings/operatingHours`);
    const snapshot = await get(settingsRef);

    if (!snapshot.exists()) {
      return {
        success: true,
        operatingHours: {
          enabled: false,
          startTime: '06:00',
          endTime: '00:00',
          gracePeriodMinutes: 5,
          graceBehavior: 'graceful',
        },
      };
    }

    return { success: true, operatingHours: snapshot.val() };
  } catch (error) {
    return { success: false, error: error.message };
  }
};

export const updateOrgOperatingHours = async (orgId, operatingHours) => {
  try {
    const fn = httpsCallable(functions, 'setSupervisorOrgSettings');
    const result = await fn({ orgId, settings: { operatingHours } });
    return result.data;
  } catch (error) {
    return { success: false, error: error.message };
  }
};
