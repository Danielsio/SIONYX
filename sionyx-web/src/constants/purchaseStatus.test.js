import { describe, it, expect } from 'vitest';
import {
  PURCHASE_STATUS,
  PURCHASE_STATUS_LABELS,
  PURCHASE_STATUS_COLORS,
  getStatusLabel,
  getStatusColor,
  isFinalStatus,
} from './purchaseStatus';

describe('purchaseStatus constants', () => {
  describe('PURCHASE_STATUS enum', () => {
    it('has correct status values', () => {
      expect(PURCHASE_STATUS.PENDING).toBe('pending');
      expect(PURCHASE_STATUS.COMPLETED).toBe('completed');
      expect(PURCHASE_STATUS.FAILED).toBe('failed');
    });

    it('has exactly 3 status types', () => {
      expect(Object.keys(PURCHASE_STATUS)).toHaveLength(3);
    });
  });

  describe('PURCHASE_STATUS_LABELS', () => {
    it('has Hebrew labels for all statuses', () => {
      expect(PURCHASE_STATUS_LABELS[PURCHASE_STATUS.PENDING]).toBe('ממתין');
      expect(PURCHASE_STATUS_LABELS[PURCHASE_STATUS.COMPLETED]).toBe('הושלם');
      expect(PURCHASE_STATUS_LABELS[PURCHASE_STATUS.FAILED]).toBe('נכשל');
    });

    it('has labels for all defined statuses', () => {
      Object.values(PURCHASE_STATUS).forEach(status => {
        expect(PURCHASE_STATUS_LABELS[status]).toBeDefined();
      });
    });
  });

  describe('PURCHASE_STATUS_COLORS', () => {
    it('has correct colors for all statuses', () => {
      expect(PURCHASE_STATUS_COLORS[PURCHASE_STATUS.PENDING]).toBe('processing');
      expect(PURCHASE_STATUS_COLORS[PURCHASE_STATUS.COMPLETED]).toBe('success');
      expect(PURCHASE_STATUS_COLORS[PURCHASE_STATUS.FAILED]).toBe('error');
    });

    it('has colors for all defined statuses', () => {
      Object.values(PURCHASE_STATUS).forEach(status => {
        expect(PURCHASE_STATUS_COLORS[status]).toBeDefined();
      });
    });
  });

  describe('getStatusLabel', () => {
    it('returns Hebrew label for PENDING status', () => {
      expect(getStatusLabel(PURCHASE_STATUS.PENDING)).toBe('ממתין');
      expect(getStatusLabel('pending')).toBe('ממתין');
    });

    it('returns Hebrew label for COMPLETED status', () => {
      expect(getStatusLabel(PURCHASE_STATUS.COMPLETED)).toBe('הושלם');
      expect(getStatusLabel('completed')).toBe('הושלם');
    });

    it('returns Hebrew label for FAILED status', () => {
      expect(getStatusLabel(PURCHASE_STATUS.FAILED)).toBe('נכשל');
      expect(getStatusLabel('failed')).toBe('נכשל');
    });

    it('returns the input for unknown status', () => {
      expect(getStatusLabel('unknown')).toBe('unknown');
      expect(getStatusLabel('custom-status')).toBe('custom-status');
    });

    it('handles null/undefined by returning them', () => {
      expect(getStatusLabel(null)).toBe(null);
      expect(getStatusLabel(undefined)).toBe(undefined);
    });
  });

  describe('getStatusColor', () => {
    it('returns "processing" for PENDING status', () => {
      expect(getStatusColor(PURCHASE_STATUS.PENDING)).toBe('processing');
      expect(getStatusColor('pending')).toBe('processing');
    });

    it('returns "success" for COMPLETED status', () => {
      expect(getStatusColor(PURCHASE_STATUS.COMPLETED)).toBe('success');
      expect(getStatusColor('completed')).toBe('success');
    });

    it('returns "error" for FAILED status', () => {
      expect(getStatusColor(PURCHASE_STATUS.FAILED)).toBe('error');
      expect(getStatusColor('failed')).toBe('error');
    });

    it('returns "default" for unknown status', () => {
      expect(getStatusColor('unknown')).toBe('default');
      expect(getStatusColor(null)).toBe('default');
      expect(getStatusColor(undefined)).toBe('default');
    });
  });

  describe('isFinalStatus', () => {
    it('returns true for COMPLETED status', () => {
      expect(isFinalStatus(PURCHASE_STATUS.COMPLETED)).toBe(true);
      expect(isFinalStatus('completed')).toBe(true);
    });

    it('returns true for FAILED status', () => {
      expect(isFinalStatus(PURCHASE_STATUS.FAILED)).toBe(true);
      expect(isFinalStatus('failed')).toBe(true);
    });

    it('returns false for PENDING status', () => {
      expect(isFinalStatus(PURCHASE_STATUS.PENDING)).toBe(false);
      expect(isFinalStatus('pending')).toBe(false);
    });

    it('returns false for unknown status', () => {
      expect(isFinalStatus('unknown')).toBe(false);
      expect(isFinalStatus(null)).toBe(false);
      expect(isFinalStatus(undefined)).toBe(false);
    });
  });
});

