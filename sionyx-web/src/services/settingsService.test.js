import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ref, get, update } from 'firebase/database';
import {
  getOperatingHours,
  updateOperatingHours,
  getAllSettings,
  DEFAULT_OPERATING_HOURS,
} from './settingsService';

vi.mock('firebase/database', () => ({
  ref: vi.fn(),
  get: vi.fn(),
  update: vi.fn(),
}));

vi.mock('../config/firebase', () => ({
  database: {},
}));

describe('settingsService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('DEFAULT_OPERATING_HOURS', () => {
    it('has correct default values', () => {
      expect(DEFAULT_OPERATING_HOURS).toEqual({
        enabled: false,
        startTime: '06:00',
        endTime: '00:00',
        gracePeriodMinutes: 5,
        graceBehavior: 'graceful',
      });
    });
  });

  describe('getOperatingHours', () => {
    it('returns defaults when settings do not exist', async () => {
      get.mockResolvedValue({ exists: () => false });

      const result = await getOperatingHours('my-org');

      expect(result.success).toBe(true);
      expect(result.operatingHours).toEqual(DEFAULT_OPERATING_HOURS);
    });

    it('returns stored settings when they exist', async () => {
      const storedSettings = {
        enabled: true,
        startTime: '08:00',
        endTime: '22:00',
        gracePeriodMinutes: 10,
        graceBehavior: 'force',
      };

      get.mockResolvedValue({
        exists: () => true,
        val: () => storedSettings,
      });

      const result = await getOperatingHours('my-org');

      expect(result.success).toBe(true);
      expect(result.operatingHours).toEqual(storedSettings);
    });

    it('merges partial settings with defaults', async () => {
      get.mockResolvedValue({
        exists: () => true,
        val: () => ({ enabled: true, startTime: '09:00' }),
      });

      const result = await getOperatingHours('my-org');

      expect(result.success).toBe(true);
      expect(result.operatingHours.enabled).toBe(true);
      expect(result.operatingHours.startTime).toBe('09:00');
      expect(result.operatingHours.endTime).toBe('00:00'); // default
      expect(result.operatingHours.gracePeriodMinutes).toBe(5); // default
    });

    it('handles errors', async () => {
      get.mockRejectedValue(new Error('Network error'));

      const result = await getOperatingHours('my-org');

      expect(result.success).toBe(false);
      expect(result.error).toBe('Failed to get operating hours settings');
    });
  });

  describe('updateOperatingHours', () => {
    const validData = {
      enabled: true,
      startTime: '06:00',
      endTime: '00:00',
      gracePeriodMinutes: 5,
      graceBehavior: 'graceful',
    };

    it('updates settings successfully', async () => {
      update.mockResolvedValue();

      const result = await updateOperatingHours('my-org', validData);

      expect(result.success).toBe(true);
      expect(update).toHaveBeenCalled();
    });

    it('validates enabled must be boolean', async () => {
      const result = await updateOperatingHours('my-org', {
        ...validData,
        enabled: 'true',
      });

      expect(result.success).toBe(false);
      expect(result.error).toBe('enabled must be a boolean');
    });

    it('validates time format', async () => {
      const result = await updateOperatingHours('my-org', {
        ...validData,
        startTime: '6:00',
      });

      expect(result.success).toBe(false);
      expect(result.error).toBe('Times must be in HH:mm format');
    });

    it('validates grace period is non-negative', async () => {
      const result = await updateOperatingHours('my-org', {
        ...validData,
        gracePeriodMinutes: -1,
      });

      expect(result.success).toBe(false);
      expect(result.error).toBe('Grace period must be a non-negative number');
    });

    it('validates grace behavior values', async () => {
      const result = await updateOperatingHours('my-org', {
        ...validData,
        graceBehavior: 'invalid',
      });

      expect(result.success).toBe(false);
      expect(result.error).toBe('Grace behavior must be "graceful" or "force"');
    });

    it('handles update errors', async () => {
      update.mockRejectedValue(new Error('Permission denied'));

      const result = await updateOperatingHours('my-org', validData);

      expect(result.success).toBe(false);
      expect(result.error).toContain('Failed to update operating hours');
    });
  });

  describe('getAllSettings', () => {
    it('returns combined settings', async () => {
      get.mockResolvedValue({
        exists: () => true,
        val: () => ({
          blackAndWhitePrice: 2.0,
          colorPrice: 5.0,
          settings: {
            operatingHours: {
              enabled: true,
              startTime: '07:00',
            },
          },
        }),
      });

      const result = await getAllSettings('my-org');

      expect(result.success).toBe(true);
      expect(result.settings.pricing.blackAndWhitePrice).toBe(2.0);
      expect(result.settings.pricing.colorPrice).toBe(5.0);
      expect(result.settings.operatingHours.enabled).toBe(true);
      expect(result.settings.operatingHours.startTime).toBe('07:00');
    });

    it('returns defaults when metadata not found', async () => {
      get.mockResolvedValue({ exists: () => false });

      const result = await getAllSettings('my-org');

      expect(result.success).toBe(false);
      expect(result.error).toBe('Organization metadata not found');
    });

    it('handles errors', async () => {
      get.mockRejectedValue(new Error('Network error'));

      const result = await getAllSettings('my-org');

      expect(result.success).toBe(false);
      expect(result.error).toBe('Failed to get settings');
    });
  });
});
