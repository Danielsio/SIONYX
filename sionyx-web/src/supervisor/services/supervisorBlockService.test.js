import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ref, get, set, remove, update } from 'firebase/database';
import { blockUser, unblockUser, getBlockedUsers } from './supervisorBlockService';
import { auth } from '../../config/firebase';

vi.mock('firebase/database');
vi.mock('../../config/firebase', () => ({
  auth: { currentUser: { uid: 'sup-1' } },
  database: {},
}));
vi.mock('../store/supervisorAuthStore', () => ({
  useSupervisorAuthStore: {
    getState: () => ({
      getOrgIds: () => ['org-1', 'org-2'],
    }),
  },
}));

describe('supervisorBlockService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    auth.currentUser = { uid: 'sup-1' };
    ref.mockReturnValue('mockRef');
    set.mockResolvedValue();
    remove.mockResolvedValue();
    update.mockResolvedValue();
  });

  describe('blockUser', () => {
    it('writes to blockedUsers and updates matching users across orgs', async () => {
      const getCalls = [];
      get.mockImplementation(refVal => {
        getCalls.push(refVal);
        return Promise.resolve({
          exists: () => true,
          val: () => ({
            user1: { phoneNumber: '123-456-7890', name: 'John' },
            user2: { phoneNumber: '999-999-9999', name: 'Jane' },
          }),
        });
      });

      const result = await blockUser('123-456-7890', 'Spam', 'John');

      expect(result.success).toBe(true);
      expect(result.blockedCount).toBe(2);
      expect(set).toHaveBeenCalledTimes(1);
      expect(update).toHaveBeenCalledTimes(2);
    });

    it('returns error when not authenticated', async () => {
      auth.currentUser = null;

      const result = await blockUser('1234567890', 'Spam', 'John');

      expect(result.success).toBe(false);
      expect(result.error).toBe('Not authenticated');
    });

    it('returns error for invalid phone', async () => {
      const result = await blockUser('---', 'Spam', 'John');

      expect(result.success).toBe(false);
      expect(result.error).toBe('Invalid phone number');
    });
  });

  describe('unblockUser', () => {
    it('removes from blockedUsers and clears blocked flag on matching users', async () => {
      get.mockResolvedValue({
        exists: () => true,
        val: () => ({
          user1: { phoneNumber: '1234567890', name: 'John' },
        }),
      });

      const result = await unblockUser('1234567890');

      expect(result.success).toBe(true);
      expect(result.unblockedCount).toBe(2);
      expect(remove).toHaveBeenCalledTimes(1);
      expect(update).toHaveBeenCalledTimes(2);
    });

    it('returns error when not authenticated', async () => {
      auth.currentUser = null;

      const result = await unblockUser('1234567890');

      expect(result.success).toBe(false);
      expect(result.error).toBe('Not authenticated');
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
