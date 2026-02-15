import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ref, get, update } from 'firebase/database';
import { httpsCallable } from 'firebase/functions';
import {
  getAllUsers,
  getUserPurchaseHistory,
  adjustUserBalance,
  grantAdminPermission,
  revokeAdminPermission,
  kickUser,
  resetUserPassword,
} from './userService';

vi.mock('firebase/database');
vi.mock('firebase/functions');
vi.mock('../config/firebase', () => ({
  database: {},
  functions: {},
}));

// Mock auth store with admin user for access checks
vi.mock('../store/authStore', () => ({
  useAuthStore: {
    getState: () => ({
      user: { role: 'admin', isAdmin: true },
    }),
  },
}));

describe('userService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('getAllUsers', () => {
    it('returns empty array if no users exist', async () => {
      get.mockResolvedValue({
        exists: () => false,
      });

      const result = await getAllUsers('my-org');

      expect(result.success).toBe(true);
      expect(result.users).toEqual([]);
    });

    it('returns users sorted by creation date (newest first)', async () => {
      get.mockResolvedValue({
        exists: () => true,
        val: () => ({
          'user-1': { firstName: 'John', createdAt: '2024-01-01' },
          'user-2': { firstName: 'Jane', createdAt: '2024-06-01' },
          'user-3': { firstName: 'Bob', createdAt: '2024-03-01' },
        }),
      });

      const result = await getAllUsers('my-org');

      expect(result.success).toBe(true);
      expect(result.users).toHaveLength(3);
      expect(result.users[0].firstName).toBe('Jane'); // June - newest
      expect(result.users[1].firstName).toBe('Bob'); // March
      expect(result.users[2].firstName).toBe('John'); // Jan - oldest
    });

    it('includes uid in each user object', async () => {
      get.mockResolvedValue({
        exists: () => true,
        val: () => ({
          'uid-123': { firstName: 'Test' },
        }),
      });

      const result = await getAllUsers('my-org');

      expect(result.users[0].uid).toBe('uid-123');
    });

    it('handles database error', async () => {
      get.mockRejectedValue(new Error('Database error'));

      const result = await getAllUsers('my-org');

      expect(result.success).toBe(false);
      expect(result.error).toBe('Database error');
      expect(result.users).toEqual([]);
    });
  });

  describe('getUserPurchaseHistory', () => {
    it('returns empty array if no purchases exist', async () => {
      get.mockResolvedValue({
        exists: () => false,
      });

      const result = await getUserPurchaseHistory('my-org', 'user-123');

      expect(result.success).toBe(true);
      expect(result.purchases).toEqual([]);
    });

    it('filters purchases by userId', async () => {
      get.mockResolvedValue({
        exists: () => true,
        val: () => ({
          'purchase-1': { userId: 'user-123', amount: 50 },
          'purchase-2': { userId: 'user-456', amount: 100 },
          'purchase-3': { userId: 'user-123', amount: 75 },
        }),
      });

      const result = await getUserPurchaseHistory('my-org', 'user-123');

      expect(result.success).toBe(true);
      expect(result.purchases).toHaveLength(2);
      expect(result.purchases.every(p => p.userId === 'user-123')).toBe(true);
    });

    it('sorts purchases by date (newest first)', async () => {
      get.mockResolvedValue({
        exists: () => true,
        val: () => ({
          'purchase-1': { userId: 'user-123', createdAt: '2024-01-01' },
          'purchase-2': { userId: 'user-123', createdAt: '2024-06-01' },
        }),
      });

      const result = await getUserPurchaseHistory('my-org', 'user-123');

      expect(result.purchases[0].createdAt).toBe('2024-06-01');
    });
  });

  describe('adjustUserBalance', () => {
    it('returns error if user not found', async () => {
      get.mockResolvedValue({
        exists: () => false,
      });

      const result = await adjustUserBalance('my-org', 'user-123', {
        timeSeconds: 60,
      });

      expect(result.success).toBe(false);
      expect(result.error).toBe('User not found');
    });

    it('adds time correctly', async () => {
      get.mockResolvedValue({
        exists: () => true,
        val: () => ({ remainingTime: 100, printBalance: 10 }),
      });
      update.mockResolvedValue();

      const result = await adjustUserBalance('my-org', 'user-123', {
        timeSeconds: 60,
      });

      expect(result.success).toBe(true);
      expect(update).toHaveBeenCalled();
      const updateCall = update.mock.calls[0][1];
      expect(updateCall.remainingTime).toBe(160); // 100 + 60
    });

    it('adds prints correctly', async () => {
      get.mockResolvedValue({
        exists: () => true,
        val: () => ({ remainingTime: 100, printBalance: 10 }),
      });
      update.mockResolvedValue();

      const result = await adjustUserBalance('my-org', 'user-123', {
        prints: 5,
      });

      expect(result.success).toBe(true);
      const updateCall = update.mock.calls[0][1];
      expect(updateCall.printBalance).toBe(15); // 10 + 5
    });

    it('prevents negative time', async () => {
      get.mockResolvedValue({
        exists: () => true,
        val: () => ({ remainingTime: 30, printBalance: 10 }),
      });
      update.mockResolvedValue();

      await adjustUserBalance('my-org', 'user-123', {
        timeSeconds: -100,
      });

      const updateCall = update.mock.calls[0][1];
      expect(updateCall.remainingTime).toBe(0); // Not negative
    });

    it('prevents negative prints', async () => {
      get.mockResolvedValue({
        exists: () => true,
        val: () => ({ remainingTime: 100, printBalance: 5 }),
      });
      update.mockResolvedValue();

      await adjustUserBalance('my-org', 'user-123', {
        prints: -50,
      });

      const updateCall = update.mock.calls[0][1];
      expect(updateCall.printBalance).toBe(0); // Not negative
    });
  });

  describe('grantAdminPermission', () => {
    it('returns error if user not found', async () => {
      get.mockResolvedValue({
        exists: () => false,
      });

      const result = await grantAdminPermission('my-org', 'user-123');

      expect(result.success).toBe(false);
      expect(result.error).toBe('User not found');
    });

    it('grants admin permission successfully', async () => {
      get.mockResolvedValue({
        exists: () => true,
        val: () => ({ firstName: 'Test' }),
      });
      update.mockResolvedValue();

      const result = await grantAdminPermission('my-org', 'user-123');

      expect(result.success).toBe(true);
      const updateCall = update.mock.calls[0][1];
      expect(updateCall.isAdmin).toBe(true);
    });
  });

  describe('revokeAdminPermission', () => {
    it('returns error if user not found', async () => {
      get.mockResolvedValue({
        exists: () => false,
      });

      const result = await revokeAdminPermission('my-org', 'user-123');

      expect(result.success).toBe(false);
      expect(result.error).toBe('User not found');
    });

    it('revokes admin permission successfully', async () => {
      get.mockResolvedValue({
        exists: () => true,
        val: () => ({ isAdmin: true }),
      });
      update.mockResolvedValue();

      const result = await revokeAdminPermission('my-org', 'user-123');

      expect(result.success).toBe(true);
      const updateCall = update.mock.calls[0][1];
      expect(updateCall.isAdmin).toBe(false);
    });
  });

  describe('kickUser', () => {
    it('returns error if user not found', async () => {
      get.mockResolvedValue({
        exists: () => false,
      });

      const result = await kickUser('my-org', 'user-123');

      expect(result.success).toBe(false);
      expect(result.error).toBe('User not found');
    });

    it('returns error if user already kicked', async () => {
      get.mockResolvedValue({
        exists: () => true,
        val: () => ({ forceLogout: true }),
      });

      const result = await kickUser('my-org', 'user-123');

      expect(result.success).toBe(false);
      expect(result.error).toBe('User has already been kicked');
    });

    it('kicks user successfully', async () => {
      get.mockResolvedValue({
        exists: () => true,
        val: () => ({ forceLogout: false }),
      });
      update.mockResolvedValue();

      const result = await kickUser('my-org', 'user-123');

      expect(result.success).toBe(true);
      expect(update).toHaveBeenCalled();
      const updateCall = update.mock.calls[0][1];
      expect(updateCall.forceLogout).toBe(true);
    });

    it('also logs out from computer if user has one', async () => {
      get.mockResolvedValue({
        exists: () => true,
        val: () => ({ forceLogout: false, currentComputerId: 'comp-123' }),
      });
      update.mockResolvedValue();

      const result = await kickUser('my-org', 'user-123');

      expect(result.success).toBe(true);
      // Should have multiple update calls: user forceLogout, computer, user computer clear
      expect(update.mock.calls.length).toBeGreaterThan(1);
    });
  });

  describe('resetUserPassword', () => {
    it('calls the resetUserPassword cloud function', async () => {
      const mockCallable = vi.fn().mockResolvedValue({
        data: { success: true, message: 'הסיסמה אופסה בהצלחה' },
      });
      httpsCallable.mockReturnValue(mockCallable);

      const result = await resetUserPassword('my-org', 'user-123', 'newPassword123');

      expect(httpsCallable).toHaveBeenCalledWith(expect.anything(), 'resetUserPassword');
      expect(mockCallable).toHaveBeenCalledWith({
        orgId: 'my-org',
        userId: 'user-123',
        newPassword: 'newPassword123',
      });
      expect(result.success).toBe(true);
      expect(result.message).toBe('הסיסמה אופסה בהצלחה');
    });

    it('returns success with default message if no message in response', async () => {
      const mockCallable = vi.fn().mockResolvedValue({
        data: { success: true },
      });
      httpsCallable.mockReturnValue(mockCallable);

      const result = await resetUserPassword('my-org', 'user-123', 'newPassword123');

      expect(result.success).toBe(true);
      expect(result.message).toBe('הסיסמה אופסה בהצלחה');
    });

    it('handles cloud function error', async () => {
      const mockCallable = vi.fn().mockRejectedValue(new Error('Permission denied'));
      httpsCallable.mockReturnValue(mockCallable);

      const result = await resetUserPassword('my-org', 'user-123', 'newPassword123');

      expect(result.success).toBe(false);
      expect(result.error).toBe('Permission denied');
    });

    it('handles error without message', async () => {
      const mockCallable = vi.fn().mockRejectedValue({});
      httpsCallable.mockReturnValue(mockCallable);

      const result = await resetUserPassword('my-org', 'user-123', 'newPassword123');

      expect(result.success).toBe(false);
      expect(result.error).toBe('שגיאה באיפוס הסיסמה');
    });

    it('passes correct parameters to cloud function', async () => {
      const mockCallable = vi.fn().mockResolvedValue({ data: { success: true } });
      httpsCallable.mockReturnValue(mockCallable);

      await resetUserPassword('org-test', 'uid-abc', 'securePass!');

      expect(mockCallable).toHaveBeenCalledWith({
        orgId: 'org-test',
        userId: 'uid-abc',
        newPassword: 'securePass!',
      });
    });
  });
});
