import { describe, it, expect } from 'vitest';
import {
  USER_STATUS,
  USER_STATUS_CONFIG,
  getUserStatus,
  getStatusLabel,
  getStatusColor,
} from './userStatus';

describe('userStatus constants', () => {
  describe('USER_STATUS enum', () => {
    it('has correct status values', () => {
      expect(USER_STATUS.ACTIVE).toBe('active');
      expect(USER_STATUS.CONNECTED).toBe('connected');
      expect(USER_STATUS.OFFLINE).toBe('offline');
    });

    it('has exactly 3 status types', () => {
      expect(Object.keys(USER_STATUS)).toHaveLength(3);
    });
  });

  describe('USER_STATUS_CONFIG', () => {
    it('has configuration for all status types', () => {
      expect(USER_STATUS_CONFIG[USER_STATUS.ACTIVE]).toBeDefined();
      expect(USER_STATUS_CONFIG[USER_STATUS.CONNECTED]).toBeDefined();
      expect(USER_STATUS_CONFIG[USER_STATUS.OFFLINE]).toBeDefined();
    });

    it('has Hebrew labels for all statuses', () => {
      expect(USER_STATUS_CONFIG[USER_STATUS.ACTIVE].label).toBe('פעיל');
      expect(USER_STATUS_CONFIG[USER_STATUS.CONNECTED].label).toBe('מחובר');
      expect(USER_STATUS_CONFIG[USER_STATUS.OFFLINE].label).toBe('לא מחובר');
    });

    it('has colors for all statuses', () => {
      expect(USER_STATUS_CONFIG[USER_STATUS.ACTIVE].color).toBe('success');
      expect(USER_STATUS_CONFIG[USER_STATUS.CONNECTED].color).toBe('processing');
      expect(USER_STATUS_CONFIG[USER_STATUS.OFFLINE].color).toBe('default');
    });

    it('has descriptions for all statuses', () => {
      expect(USER_STATUS_CONFIG[USER_STATUS.ACTIVE].description).toBeDefined();
      expect(USER_STATUS_CONFIG[USER_STATUS.CONNECTED].description).toBeDefined();
      expect(USER_STATUS_CONFIG[USER_STATUS.OFFLINE].description).toBeDefined();
    });
  });

  describe('getUserStatus', () => {
    it('returns OFFLINE for null user', () => {
      expect(getUserStatus(null)).toBe(USER_STATUS.OFFLINE);
    });

    it('returns OFFLINE for undefined user', () => {
      expect(getUserStatus(undefined)).toBe(USER_STATUS.OFFLINE);
    });

    it('returns OFFLINE for user not logged in', () => {
      const user = { isSessionActive: false };
      expect(getUserStatus(user)).toBe(USER_STATUS.OFFLINE);
    });

    it('returns CONNECTED for logged in user without computer', () => {
      const user = { isSessionActive: true, currentComputerId: null };
      expect(getUserStatus(user)).toBe(USER_STATUS.CONNECTED);
    });

    it('returns CONNECTED for logged in user with undefined computer', () => {
      const user = { isSessionActive: true };
      expect(getUserStatus(user)).toBe(USER_STATUS.CONNECTED);
    });

    it('returns ACTIVE for logged in user with computer', () => {
      const user = { isSessionActive: true, currentComputerId: 'computer-123' };
      expect(getUserStatus(user)).toBe(USER_STATUS.ACTIVE);
    });

    it('returns OFFLINE for user with computer but not logged in', () => {
      const user = { isSessionActive: false, currentComputerId: 'computer-123' };
      expect(getUserStatus(user)).toBe(USER_STATUS.OFFLINE);
    });

    it('handles empty object as OFFLINE', () => {
      expect(getUserStatus({})).toBe(USER_STATUS.OFFLINE);
    });
  });

  describe('getStatusLabel', () => {
    it('returns Hebrew label for ACTIVE status', () => {
      expect(getStatusLabel(USER_STATUS.ACTIVE)).toBe('פעיל');
    });

    it('returns Hebrew label for CONNECTED status', () => {
      expect(getStatusLabel(USER_STATUS.CONNECTED)).toBe('מחובר');
    });

    it('returns Hebrew label for OFFLINE status', () => {
      expect(getStatusLabel(USER_STATUS.OFFLINE)).toBe('לא מחובר');
    });

    it('returns "לא ידוע" for unknown status', () => {
      expect(getStatusLabel('unknown')).toBe('לא ידוע');
      expect(getStatusLabel(null)).toBe('לא ידוע');
      expect(getStatusLabel(undefined)).toBe('לא ידוע');
    });
  });

  describe('getStatusColor', () => {
    it('returns "success" for ACTIVE status', () => {
      expect(getStatusColor(USER_STATUS.ACTIVE)).toBe('success');
    });

    it('returns "processing" for CONNECTED status', () => {
      expect(getStatusColor(USER_STATUS.CONNECTED)).toBe('processing');
    });

    it('returns "default" for OFFLINE status', () => {
      expect(getStatusColor(USER_STATUS.OFFLINE)).toBe('default');
    });

    it('returns "default" for unknown status', () => {
      expect(getStatusColor('unknown')).toBe('default');
      expect(getStatusColor(null)).toBe('default');
      expect(getStatusColor(undefined)).toBe('default');
    });
  });
});


