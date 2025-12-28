import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ref, get, set, update, remove, push } from 'firebase/database';
import {
  getAllPackages,
  createPackage,
  updatePackage,
  deletePackage,
  calculateFinalPrice,
} from './packageService';

vi.mock('firebase/database');
vi.mock('../config/firebase', () => ({
  database: {},
}));

describe('packageService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('getAllPackages', () => {
    it('returns empty array if no packages exist', async () => {
      get.mockResolvedValue({
        exists: () => false,
      });

      const result = await getAllPackages('my-org');

      expect(result.success).toBe(true);
      expect(result.packages).toEqual([]);
    });

    it('returns packages sorted by creation date (newest first)', async () => {
      get.mockResolvedValue({
        exists: () => true,
        val: () => ({
          'pkg-1': { name: 'Basic', createdAt: '2024-01-01' },
          'pkg-2': { name: 'Premium', createdAt: '2024-06-01' },
          'pkg-3': { name: 'Standard', createdAt: '2024-03-01' },
        }),
      });

      const result = await getAllPackages('my-org');

      expect(result.success).toBe(true);
      expect(result.packages).toHaveLength(3);
      expect(result.packages[0].name).toBe('Premium'); // June - newest
      expect(result.packages[1].name).toBe('Standard'); // March
      expect(result.packages[2].name).toBe('Basic'); // Jan - oldest
    });

    it('includes id in each package object', async () => {
      get.mockResolvedValue({
        exists: () => true,
        val: () => ({
          'pkg-123': { name: 'Test Package' },
        }),
      });

      const result = await getAllPackages('my-org');

      expect(result.packages[0].id).toBe('pkg-123');
    });

    it('handles database error', async () => {
      get.mockRejectedValue(new Error('Database error'));

      const result = await getAllPackages('my-org');

      expect(result.success).toBe(false);
      expect(result.error).toBe('Database error');
      expect(result.packages).toEqual([]);
    });
  });

  describe('createPackage', () => {
    it('creates package successfully', async () => {
      push.mockReturnValue({ key: 'new-pkg-id' });
      set.mockResolvedValue();

      const result = await createPackage('my-org', {
        name: 'New Package',
        price: 50,
        timeMinutes: 120,
      });

      expect(result.success).toBe(true);
      expect(result.packageId).toBe('new-pkg-id');
    });

    it('adds timestamps to package', async () => {
      push.mockReturnValue({ key: 'new-pkg-id' });
      set.mockResolvedValue();

      await createPackage('my-org', { name: 'Test' });

      const setCall = set.mock.calls[0][1];
      expect(setCall.createdAt).toBeDefined();
      expect(setCall.updatedAt).toBeDefined();
    });

    it('handles database error', async () => {
      push.mockReturnValue({ key: 'new-pkg-id' });
      set.mockRejectedValue(new Error('Write failed'));

      const result = await createPackage('my-org', { name: 'Test' });

      expect(result.success).toBe(false);
      expect(result.error).toBe('Write failed');
    });
  });

  describe('updatePackage', () => {
    it('updates package successfully', async () => {
      update.mockResolvedValue();

      const result = await updatePackage('my-org', 'pkg-123', {
        name: 'Updated Name',
        price: 75,
      });

      expect(result.success).toBe(true);
    });

    it('adds updatedAt timestamp', async () => {
      update.mockResolvedValue();

      await updatePackage('my-org', 'pkg-123', { name: 'Updated' });

      const updateCall = update.mock.calls[0][1];
      expect(updateCall.updatedAt).toBeDefined();
    });

    it('handles database error', async () => {
      update.mockRejectedValue(new Error('Update failed'));

      const result = await updatePackage('my-org', 'pkg-123', { name: 'Test' });

      expect(result.success).toBe(false);
      expect(result.error).toBe('Update failed');
    });
  });

  describe('deletePackage', () => {
    it('deletes package successfully', async () => {
      remove.mockResolvedValue();

      const result = await deletePackage('my-org', 'pkg-123');

      expect(result.success).toBe(true);
      expect(remove).toHaveBeenCalled();
    });

    it('handles database error', async () => {
      remove.mockRejectedValue(new Error('Delete failed'));

      const result = await deletePackage('my-org', 'pkg-123');

      expect(result.success).toBe(false);
      expect(result.error).toBe('Delete failed');
    });
  });

  describe('calculateFinalPrice', () => {
    it('returns original price when no discount', () => {
      const result = calculateFinalPrice(100, 0);

      expect(result.originalPrice).toBe(100);
      expect(result.discountPercent).toBe(0);
      expect(result.finalPrice).toBe(100);
      expect(result.savings).toBe(0);
    });

    it('returns original price when discount is null', () => {
      const result = calculateFinalPrice(100, null);

      expect(result.finalPrice).toBe(100);
      expect(result.discountPercent).toBe(0);
    });

    it('returns original price when discount is undefined', () => {
      const result = calculateFinalPrice(100);

      expect(result.finalPrice).toBe(100);
    });

    it('calculates 10% discount correctly', () => {
      const result = calculateFinalPrice(100, 10);

      expect(result.originalPrice).toBe(100);
      expect(result.discountPercent).toBe(10);
      expect(result.finalPrice).toBe(90);
      expect(result.savings).toBe(10);
    });

    it('calculates 25% discount correctly', () => {
      const result = calculateFinalPrice(200, 25);

      expect(result.finalPrice).toBe(150);
      expect(result.savings).toBe(50);
    });

    it('calculates 50% discount correctly', () => {
      const result = calculateFinalPrice(80, 50);

      expect(result.finalPrice).toBe(40);
      expect(result.savings).toBe(40);
    });

    it('handles decimal prices', () => {
      const result = calculateFinalPrice(99.99, 15);

      expect(result.originalPrice).toBe(99.99);
      expect(result.finalPrice).toBe(84.99); // Rounded to 2 decimals
    });

    it('handles 100% discount', () => {
      const result = calculateFinalPrice(100, 100);

      expect(result.finalPrice).toBe(0);
      expect(result.savings).toBe(100);
    });
  });
});


