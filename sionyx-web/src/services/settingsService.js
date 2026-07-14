import { ref, get, update } from 'firebase/database';
import { auth, database, SERVER_URL } from '../config/firebase';
import { logger } from '../utils/logger';

/**
 * Settings Service for Admin Dashboard
 * Handles organization settings management
 *
 * Settings are stored in: organizations/{orgId}/metadata/settings/
 */

export const DAYS_OF_WEEK = [
  { key: 'sunday', label: 'ראשון', short: "א'" },
  { key: 'monday', label: 'שני', short: "ב'" },
  { key: 'tuesday', label: 'שלישי', short: "ג'" },
  { key: 'wednesday', label: 'רביעי', short: "ד'" },
  { key: 'thursday', label: 'חמישי', short: "ה'" },
  { key: 'friday', label: 'שישי', short: "ו'" },
  { key: 'saturday', label: 'שבת', short: 'שבת' },
];

const DEFAULT_DAY = { open: true, startTime: '08:00', endTime: '22:00' };
const DEFAULT_FRIDAY = { open: true, startTime: '08:00', endTime: '14:00' };
const DEFAULT_SATURDAY = { open: false, startTime: '00:00', endTime: '00:00' };

export const DEFAULT_OPERATING_HOURS = {
  enabled: false,
  startTime: '06:00',
  endTime: '00:00',
  gracePeriodMinutes: 5,
  graceBehavior: 'graceful',
  schedule: {
    sunday: { ...DEFAULT_DAY },
    monday: { ...DEFAULT_DAY },
    tuesday: { ...DEFAULT_DAY },
    wednesday: { ...DEFAULT_DAY },
    thursday: { ...DEFAULT_DAY },
    friday: { ...DEFAULT_FRIDAY },
    saturday: { ...DEFAULT_SATURDAY },
  },
};

/**
 * Build a complete schedule with defaults for any missing days.
 */
const buildSchedule = (schedule) => {
  const result = {};
  for (const day of DAYS_OF_WEEK) {
    const defaults = day.key === 'friday' ? DEFAULT_FRIDAY
      : day.key === 'saturday' ? DEFAULT_SATURDAY
      : DEFAULT_DAY;
    result[day.key] = { ...defaults, ...(schedule?.[day.key] || {}) };
  }
  return result;
};

/**
 * Get operating hours settings for an organization
 */
export const getOperatingHours = async orgId => {
  try {
    const settingsRef = ref(database, `organizations/${orgId}/metadata/settings/operatingHours`);
    const snapshot = await get(settingsRef);

    if (!snapshot.exists()) {
      return { success: true, operatingHours: { ...DEFAULT_OPERATING_HOURS } };
    }

    const data = snapshot.val();
    const operatingHours = {
      ...DEFAULT_OPERATING_HOURS,
      ...data,
      schedule: buildSchedule(data.schedule),
    };

    return { success: true, operatingHours };
  } catch (error) {
    logger.error('Error getting operating hours:', error);
    return { success: false, error: 'Failed to get operating hours settings' };
  }
};

/**
 * Update operating hours settings for an organization
 */
export const updateOperatingHours = async (orgId, operatingHoursData) => {
  try {
    logger.info('Updating operating hours for org:', orgId);

    const settingsRef = ref(database, `organizations/${orgId}/metadata/settings/operatingHours`);

    const { enabled, gracePeriodMinutes, graceBehavior, schedule } = operatingHoursData;

    if (typeof enabled !== 'boolean') {
      return { success: false, error: 'enabled must be a boolean' };
    }

    if (typeof gracePeriodMinutes !== 'number' || gracePeriodMinutes < 0) {
      return { success: false, error: 'Grace period must be a non-negative number' };
    }

    if (!['graceful', 'force'].includes(graceBehavior)) {
      return { success: false, error: 'Grace behavior must be "graceful" or "force"' };
    }

    const cleanSchedule = {};
    for (const day of DAYS_OF_WEEK) {
      const d = schedule?.[day.key];
      if (!d) continue;
      cleanSchedule[day.key] = {
        open: !!d.open,
        startTime: d.startTime || '08:00',
        endTime: d.endTime || '22:00',
      };
    }

    const updateData = {
      enabled,
      startTime: cleanSchedule.sunday?.startTime || '08:00',
      endTime: cleanSchedule.sunday?.endTime || '22:00',
      gracePeriodMinutes: parseInt(gracePeriodMinutes, 10),
      graceBehavior,
      schedule: cleanSchedule,
    };

    await update(settingsRef, updateData);

    logger.info('Operating hours updated successfully');
    return { success: true, message: 'Operating hours updated successfully' };
  } catch (error) {
    logger.error('Error updating operating hours:', error);
    return { success: false, error: `Failed to update operating hours: ${error.message}` };
  }
};

/**
 * Get all settings for an organization
 */
/**
 * Store display name — the name the kiosk shows as the message sender, so users
 * see "הודעה מ<שם החנות>" instead of a generic "מנהל".
 */
export const getDisplayName = async orgId => {
  try {
    const snapshot = await get(
      ref(database, `organizations/${orgId}/metadata/settings/displayName`)
    );
    return { success: true, displayName: snapshot.exists() ? snapshot.val() : '' };
  } catch (error) {
    logger.error('Error getting display name:', error);
    return { success: false, error: error.message };
  }
};

export const updateDisplayName = async (orgId, displayName) => {
  try {
    const clean = (displayName || '').trim();
    if (clean.length > 40) {
      return { success: false, error: 'השם ארוך מדי (מקסימום 40 תווים)' };
    }
    await update(ref(database, `organizations/${orgId}/metadata/settings`), {
      displayName: clean,
    });
    logger.info('Display name updated');
    return { success: true };
  } catch (error) {
    logger.error('Error updating display name:', error);
    return { success: false, error: error.message };
  }
};

/**
 * Payment settings. `saveCardEnabled` lets an org turn the saved-card ("keva")
 * one-click flow off; the kiosk hides it when disabled. The gateway password
 * itself never lives here — it stays server-side only (see the Worker).
 */
export const getPaymentSettings = async orgId => {
  try {
    const snapshot = await get(
      ref(database, `organizations/${orgId}/metadata/settings/payment`)
    );
    if (!snapshot.exists()) {
      return { success: true, payment: { saveCardEnabled: false } };
    }
    const value = snapshot.val() || {};
    return { success: true, payment: { saveCardEnabled: value.saveCardEnabled === true } };
  } catch (error) {
    logger.error('Error getting payment settings:', error);
    return { success: false, error: error.message };
  }
};

export const updatePaymentSettings = async (orgId, payment) => {
  try {
    await update(ref(database, `organizations/${orgId}/metadata/settings`), {
      payment: { saveCardEnabled: !!payment.saveCardEnabled },
    });
    logger.info('Payment settings updated');
    return { success: true };
  } catch (error) {
    logger.error('Error updating payment settings:', error);
    return { success: false, error: error.message };
  }
};

/**
 * Kiosk admin-exit password. It NEVER travels through the database from here:
 * the Worker stores it encrypted in the server-only `secrets/` path (clients are
 * denied that path by the RTDB rules) and only ever answers "configured: yes/no".
 * A blank password removes the remote override — kiosks then fall back to the
 * password the installer provisioned.
 */
export const getExitPasswordStatus = async orgId => {
  try {
    const token = await auth.currentUser.getIdToken();
    const res = await fetch(
      `${SERVER_URL}/admin/exit-password-status?orgId=${encodeURIComponent(orgId)}`,
      { headers: { Authorization: `Bearer ${token}` } }
    );
    const data = await res.json().catch(() => ({}));
    if (!res.ok || !data.success) {
      return { success: false, error: data.error || 'Failed to read status' };
    }
    return { success: true, configured: !!data.configured };
  } catch (error) {
    logger.error('Error getting exit password status:', error);
    return { success: false, error: error.message };
  }
};

export const setExitPassword = async (orgId, password) => {
  try {
    const token = await auth.currentUser.getIdToken();
    const res = await fetch(`${SERVER_URL}/admin/set-exit-password`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify({ orgId, password }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || !data.success) {
      const map = {
        password_too_short: 'הסיסמה חייבת להכיל לפחות 4 תווים',
        not_admin: 'נדרשות הרשאות מנהל',
      };
      return { success: false, error: map[data.error] || data.error || 'שמירה נכשלה' };
    }
    return { success: true, cleared: !!data.cleared };
  } catch (error) {
    logger.error('Error setting exit password:', error);
    return { success: false, error: error.message };
  }
};

export const getAllSettings = async orgId => {
  try {
    const metadataRef = ref(database, `organizations/${orgId}/metadata`);
    const snapshot = await get(metadataRef);

    if (!snapshot.exists()) {
      return { success: false, error: 'Organization metadata not found' };
    }

    const metadata = snapshot.val();
    const rawOH = metadata.settings?.operatingHours || {};

    return {
      success: true,
      settings: {
        pricing: {
          blackAndWhitePrice: metadata.blackAndWhitePrice || 1.0,
          colorPrice: metadata.colorPrice || 3.0,
        },
        operatingHours: {
          ...DEFAULT_OPERATING_HOURS,
          ...rawOH,
          schedule: buildSchedule(rawOH.schedule),
        },
      },
    };
  } catch (error) {
    logger.error('Error getting all settings:', error);
    return { success: false, error: 'Failed to get settings' };
  }
};
