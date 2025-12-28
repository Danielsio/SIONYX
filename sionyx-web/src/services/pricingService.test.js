import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ref, get, update } from 'firebase/database';
import { getPrintPricing, updatePrintPricing } from './pricingService';

vi.mock('firebase/database');
vi.mock('../config/firebase', () => ({
  database: {},
}));

describe('pricingService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('getPrintPricing', () => {
    it('returns error if metadata not found', async () => {
      get.mockResolvedValue({
        exists: () => false,
      });

      const result = await getPrintPricing('my-org');

      expect(result.success).toBe(false);
      expect(result.error).toBe('Organization metadata not found');
    });

    it('returns pricing from metadata', async () => {
      get.mockResolvedValue({
        exists: () => true,
        val: () => ({
          blackAndWhitePrice: 1.5,
          colorPrice: 4.0,
        }),
      });

      const result = await getPrintPricing('my-org');

      expect(result.success).toBe(true);
      expect(result.pricing.blackAndWhitePrice).toBe(1.5);
      expect(result.pricing.colorPrice).toBe(4.0);
    });

    it('returns default pricing if not set in metadata', async () => {
      get.mockResolvedValue({
        exists: () => true,
        val: () => ({}), // No pricing fields
      });

      const result = await getPrintPricing('my-org');

      expect(result.success).toBe(true);
      expect(result.pricing.blackAndWhitePrice).toBe(1.0);
      expect(result.pricing.colorPrice).toBe(3.0);
    });

    it('handles database error', async () => {
      get.mockRejectedValue(new Error('Database error'));

      const result = await getPrintPricing('my-org');

      expect(result.success).toBe(false);
      expect(result.error).toBe('Failed to get print pricing');
    });
  });

  describe('updatePrintPricing', () => {
    it('returns error if blackAndWhitePrice is 0 or negative', async () => {
      const result = await updatePrintPricing('my-org', {
        blackAndWhitePrice: 0,
        colorPrice: 3.0,
      });

      expect(result.success).toBe(false);
      expect(result.error).toBe('Prices must be greater than 0');
    });

    it('returns error if colorPrice is 0 or negative', async () => {
      const result = await updatePrintPricing('my-org', {
        blackAndWhitePrice: 1.0,
        colorPrice: -1,
      });

      expect(result.success).toBe(false);
      expect(result.error).toBe('Prices must be greater than 0');
    });

    it('updates pricing successfully', async () => {
      update.mockResolvedValue();

      const result = await updatePrintPricing('my-org', {
        blackAndWhitePrice: 2.0,
        colorPrice: 5.0,
      });

      expect(result.success).toBe(true);
      expect(update).toHaveBeenCalled();
    });

    it('converts string prices to floats', async () => {
      update.mockResolvedValue();

      await updatePrintPricing('my-org', {
        blackAndWhitePrice: '1.5',
        colorPrice: '3.5',
      });

      const updateCall = update.mock.calls[0][1];
      expect(updateCall.blackAndWhitePrice).toBe(1.5);
      expect(updateCall.colorPrice).toBe(3.5);
    });

    it('handles database error', async () => {
      update.mockRejectedValue(new Error('Update failed'));

      const result = await updatePrintPricing('my-org', {
        blackAndWhitePrice: 1.0,
        colorPrice: 3.0,
      });

      expect(result.success).toBe(false);
      expect(result.error).toContain('Failed to update print pricing');
    });
  });
});


