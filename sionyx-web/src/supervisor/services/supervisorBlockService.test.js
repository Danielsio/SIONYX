import { describe, it, expect, vi, beforeEach } from 'vitest';
import { httpsCallable } from 'firebase/functions';
import { ref, get } from 'firebase/database';
import { blockUser, unblockUser, getBlockedUsers } from './supervisorBlockService';
import { auth } from '../../config/firebase';

vi.mock('firebase/functions');
vi.mock('firebase/database');
vi.mock('../../config/firebase', () => ({
  auth: { currentUser: { uid: 'sup-1' } },
  database: {},
  functions: {},
}));

describe('supervisorBlockService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    auth.currentUser = { uid: 'sup-1' };
  });

  describe('blockUser', () => {
    it('calls httpsCallable correctly', async () => {
      const mockFn = vi.fn().mockResolvedValue({ data: { success: true } });
      httpsCallable.mockReturnValue(mockFn);

      await blockUser('1234567890', 'Spam', 'John Doe');

      expect(httpsCallable).toHaveBeenCalledWith(expect.anything(), 'blockUser');
      expect(mockFn).toHaveBeenCalledWith({
        phone: '1234567890',
        reason: 'Spam',
        userName: 'John Doe',
      });
    });

    it('returns result data on success', async () => {
      const mockFn = vi.fn().mockResolvedValue({ data: { success: true } });
      httpsCallable.mockReturnValue(mockFn);

      const result = await blockUser('1234567890', 'Spam', 'John');

      expect(result).toEqual({ success: true });
    });

    it('returns error on failure', async () => {
      const mockFn = vi.fn().mockRejectedValue(new Error('Block failed'));
      httpsCallable.mockReturnValue(mockFn);

      const result = await blockUser('1234567890', 'Spam', 'John');

      expect(result).toEqual({ success: false, error: 'Block failed' });
    });
  });

  describe('unblockUser', () => {
    it('calls httpsCallable correctly', async () => {
      const mockFn = vi.fn().mockResolvedValue({ data: { success: true } });
      httpsCallable.mockReturnValue(mockFn);

      await unblockUser('1234567890');

      expect(httpsCallable).toHaveBeenCalledWith(expect.anything(), 'unblockUser');
      expect(mockFn).toHaveBeenCalledWith({ phone: '1234567890' });
    });

    it('returns result data on success', async () => {
      const mockFn = vi.fn().mockResolvedValue({ data: { success: true } });
      httpsCallable.mockReturnValue(mockFn);

      const result = await unblockUser('1234567890');

      expect(result).toEqual({ success: true });
    });
  });

  describe('getBlockedUsers', () => {
    it('returns empty when no blocked users', async () => {
      get.mockResolvedValue({ exists: () => false });

      const result = await getBlockedUsers();

      expect(result.success).toBe(true);
      expect(result.blockedUsers).toEqual([]);
    });

    it('returns blocked users when they exist', async () => {
      get.mockResolvedValue({
        exists: () => true,
        val: () => ({
          '1234567890': { reason: 'Spam', blockedAt: 1000 },
          '0987654321': { reason: 'Abuse', blockedAt: 2000 },
        }),
      });

      const result = await getBlockedUsers();

      expect(result.success).toBe(true);
      expect(result.blockedUsers).toHaveLength(2);
      expect(result.blockedUsers).toEqual(
        expect.arrayContaining([
          expect.objectContaining({ phone: '1234567890', reason: 'Spam', blockedAt: 1000 }),
          expect.objectContaining({ phone: '0987654321', reason: 'Abuse', blockedAt: 2000 }),
        ])
      );
    });

    it('returns error when not authenticated', async () => {
      auth.currentUser = null;

      const result = await getBlockedUsers();

      expect(result.success).toBe(false);
      expect(result.error).toBe('Not authenticated');
      expect(result.blockedUsers).toEqual([]);
    });

    it('sorts blocked users by blockedAt descending', async () => {
      get.mockResolvedValue({
        exists: () => true,
        val: () => ({
          '111': { blockedAt: 1000 },
          '222': { blockedAt: 3000 },
          '333': { blockedAt: 2000 },
        }),
      });

      const result = await getBlockedUsers();

      expect(result.success).toBe(true);
      expect(result.blockedUsers[0].phone).toBe('222');
      expect(result.blockedUsers[1].phone).toBe('333');
      expect(result.blockedUsers[2].phone).toBe('111');
    });
  });
});
