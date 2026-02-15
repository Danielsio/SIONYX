import { describe, it, expect, vi, beforeEach } from 'vitest';
import {
  registerOrganization,
  getOrganizationMetadata,
  getOrganizationStats,
} from './organizationService';
import { database, functions } from '../config/firebase';
import { ref, get } from 'firebase/database';
import { httpsCallable } from 'firebase/functions';

// Mock Firebase
vi.mock('../config/firebase', () => ({
  database: {},
  functions: {},
}));

vi.mock('firebase/database', () => ({
  ref: vi.fn(),
  get: vi.fn(),
}));

vi.mock('firebase/functions', () => ({
  httpsCallable: vi.fn(),
}));

describe('organizationService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('registerOrganization', () => {
    it('should call Cloud Function with organization data', async () => {
      const mockCall = vi.fn().mockResolvedValue({
        data: { success: true, orgId: 'new-org-123' },
      });
      httpsCallable.mockReturnValue(mockCall);

      const orgData = {
        organizationName: 'Test Org',
        adminEmail: 'admin@test.com',
        adminPassword: 'password123',
      };

      const result = await registerOrganization(orgData);

      expect(httpsCallable).toHaveBeenCalledWith(functions, 'registerOrganization');
      expect(mockCall).toHaveBeenCalledWith(orgData);
      expect(result).toEqual({ success: true, orgId: 'new-org-123' });
    });

    it('should handle Cloud Function error with code', async () => {
      const mockError = new Error('Permission denied');
      mockError.code = 'permission-denied';
      const mockCall = vi.fn().mockRejectedValue(mockError);
      httpsCallable.mockReturnValue(mockCall);

      const result = await registerOrganization({});

      expect(result.success).toBe(false);
      expect(result.error).toBe('Permission denied');
    });

    it('should handle generic Cloud Function error', async () => {
      const mockCall = vi.fn().mockRejectedValue(new Error('Network error'));
      httpsCallable.mockReturnValue(mockCall);

      const result = await registerOrganization({});

      expect(result.success).toBe(false);
      expect(result.error).toContain('Failed to register');
    });
  });

  describe('getOrganizationMetadata', () => {
    it('should return organization metadata when found', async () => {
      const mockMetadata = {
        organizationName: 'Test Org',
        nedarim_mosad_id: btoa(JSON.stringify('12345')),
        nedarim_api_valid: btoa(JSON.stringify('api-key')),
      };

      const mockSnapshot = {
        exists: () => true,
        val: () => mockMetadata,
      };

      ref.mockReturnValue('mock-ref');
      get.mockResolvedValue(mockSnapshot);

      const result = await getOrganizationMetadata('test-org');

      expect(ref).toHaveBeenCalledWith(database, 'organizations/test-org/metadata');
      expect(result.success).toBe(true);
      expect(result.metadata.organizationName).toBe('Test Org');
    });

    it('should return error when organization not found', async () => {
      const mockSnapshot = {
        exists: () => false,
      };

      ref.mockReturnValue('mock-ref');
      get.mockResolvedValue(mockSnapshot);

      const result = await getOrganizationMetadata('non-existent-org');

      expect(result.success).toBe(false);
      expect(result.error).toBe('Organization not found');
    });

    it('should handle database error', async () => {
      ref.mockReturnValue('mock-ref');
      get.mockRejectedValue(new Error('Database error'));

      const result = await getOrganizationMetadata('test-org');

      expect(result.success).toBe(false);
      expect(result.error).toContain('Failed to get organization metadata');
    });
  });

  describe('getOrganizationStats', () => {
    it('should return organization statistics', async () => {
      const mockUsersSnapshot = {
        exists: () => true,
        val: () => ({
          'user-1': { name: 'User 1' },
          'user-2': { name: 'User 2' },
        }),
      };

      const mockPackagesSnapshot = {
        exists: () => true,
        val: () => ({
          'pkg-1': { name: 'Package 1' },
        }),
      };

      const mockPurchasesSnapshot = {
        exists: () => true,
        val: () => ({
          'purchase-1': { status: 'completed', amount: 100, minutes: 60 },
          'purchase-2': { status: 'completed', amount: 50, minutes: 30 },
          'purchase-3': { status: 'pending', amount: 75, minutes: 45 },
        }),
      };

      ref.mockReturnValue('mock-ref');
      get
        .mockResolvedValueOnce(mockUsersSnapshot)
        .mockResolvedValueOnce(mockPackagesSnapshot)
        .mockResolvedValueOnce(mockPurchasesSnapshot);

      const result = await getOrganizationStats('test-org');

      expect(result.success).toBe(true);
      expect(result.stats.usersCount).toBe(2);
      expect(result.stats.packagesCount).toBe(1);
      expect(result.stats.purchasesCount).toBe(3);
      expect(result.stats.totalRevenue).toBe(150); // Only completed purchases
      expect(result.stats.totalTimeMinutes).toBe(135); // All purchases
    });

    it('should return zeros when no data exists', async () => {
      const mockEmptySnapshot = {
        exists: () => false,
        val: () => null,
      };

      ref.mockReturnValue('mock-ref');
      get.mockResolvedValue(mockEmptySnapshot);

      const result = await getOrganizationStats('empty-org');

      expect(result.success).toBe(true);
      expect(result.stats.usersCount).toBe(0);
      expect(result.stats.packagesCount).toBe(0);
      expect(result.stats.purchasesCount).toBe(0);
      expect(result.stats.totalRevenue).toBe(0);
    });

    it('should handle database error', async () => {
      ref.mockReturnValue('mock-ref');
      get.mockRejectedValue(new Error('Database error'));

      const result = await getOrganizationStats('test-org');

      expect(result.success).toBe(false);
      expect(result.error).toContain('Failed to get organization statistics');
    });
  });
});
