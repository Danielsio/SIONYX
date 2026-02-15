import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ref, get, update, remove } from 'firebase/database';
import {
  getAllComputers,
  getComputerUsageStats,
  getComputerById,
  updateComputer,
  deleteComputer,
  forceLogoutUser,
  getActiveComputerUsers,
} from './computerService';

vi.mock('firebase/database');
vi.mock('../config/firebase', () => ({
  database: {},
}));

// Mock auth store with admin user for access checks
vi.mock('../store/authStore', () => ({
  useAuthStore: {
    getState: () => ({
      user: { role: 'admin', isAdmin: true },
    }),
  },
}));

// Mock useOrgId hook to prevent auth store conflicts
vi.mock('../hooks/useOrgId', () => ({
  useOrgId: () => 'my-org',
  getOrgId: () => 'my-org',
}));

describe('computerService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    localStorage.setItem('adminOrgId', 'my-org');
  });

  describe('getAllComputers', () => {
    it('returns empty array if no computers exist', async () => {
      get.mockResolvedValue({
        exists: () => false,
      });

      const result = await getAllComputers();

      expect(result.success).toBe(true);
      expect(result.data).toEqual([]);
    });

    it('returns computers with id included', async () => {
      get.mockResolvedValue({
        exists: () => true,
        val: () => ({
          'comp-1': { computerName: 'PC-1', isActive: true },
          'comp-2': { computerName: 'PC-2', isActive: false },
        }),
      });

      const result = await getAllComputers();

      expect(result.success).toBe(true);
      expect(result.data).toHaveLength(2);
      expect(result.data[0].id).toBe('comp-1');
      expect(result.data[0].computerName).toBe('PC-1');
    });

    it('handles database error', async () => {
      get.mockRejectedValue(new Error('Database error'));

      const result = await getAllComputers();

      expect(result.success).toBe(false);
      expect(result.error).toBe('Failed to fetch computers');
    });
  });

  describe('getComputerById', () => {
    it('returns computer if found', async () => {
      get.mockResolvedValue({
        exists: () => true,
        val: () => ({ computerName: 'PC-1', isActive: true }),
      });

      const result = await getComputerById('comp-123');

      expect(result.success).toBe(true);
      expect(result.data.id).toBe('comp-123');
      expect(result.data.computerName).toBe('PC-1');
    });

    it('returns error if computer not found', async () => {
      get.mockResolvedValue({
        exists: () => false,
      });

      const result = await getComputerById('non-existent');

      expect(result.success).toBe(false);
      expect(result.error).toBe('Computer not found');
    });

    it('handles database error', async () => {
      get.mockRejectedValue(new Error('Database error'));

      const result = await getComputerById('comp-123');

      expect(result.success).toBe(false);
      expect(result.error).toBe('Failed to fetch computer');
    });
  });

  describe('updateComputer', () => {
    it('updates computer successfully', async () => {
      update.mockResolvedValue();

      const result = await updateComputer('comp-123', {
        computerName: 'Updated PC',
        location: 'Room 1',
      });

      expect(result.success).toBe(true);
      expect(update).toHaveBeenCalled();
    });

    it('adds updatedAt timestamp', async () => {
      update.mockResolvedValue();

      await updateComputer('comp-123', { computerName: 'Test' });

      const updateCall = update.mock.calls[0][1];
      expect(updateCall.updatedAt).toBeDefined();
    });

    it('handles database error', async () => {
      update.mockRejectedValue(new Error('Update failed'));

      const result = await updateComputer('comp-123', { computerName: 'Test' });

      expect(result.success).toBe(false);
      expect(result.error).toBe('Failed to update computer');
    });
  });

  describe('deleteComputer', () => {
    it('deletes computer successfully', async () => {
      remove.mockResolvedValue();

      const result = await deleteComputer('comp-123');

      expect(result.success).toBe(true);
      expect(remove).toHaveBeenCalled();
    });

    it('handles database error', async () => {
      remove.mockRejectedValue(new Error('Delete failed'));

      const result = await deleteComputer('comp-123');

      expect(result.success).toBe(false);
      expect(result.error).toBe('Failed to delete computer');
    });
  });

  describe('forceLogoutUser', () => {
    it('clears user and computer associations', async () => {
      update.mockResolvedValue();

      const result = await forceLogoutUser('user-123', 'comp-456');

      expect(result.success).toBe(true);
      // Should update both user and computer
      expect(update).toHaveBeenCalledTimes(2);
    });

    it('sets correct fields on user', async () => {
      update.mockResolvedValue();

      await forceLogoutUser('user-123', 'comp-456');

      // First call is for user
      const userUpdate = update.mock.calls[0][1];
      expect(userUpdate.currentComputerId).toBeNull();
      expect(userUpdate.currentComputerName).toBeNull();
      expect(userUpdate.isSessionActive).toBe(false);
      expect(userUpdate.lastComputerLogout).toBeDefined();
    });

    it('sets correct fields on computer', async () => {
      update.mockResolvedValue();

      await forceLogoutUser('user-123', 'comp-456');

      // Second call is for computer
      const computerUpdate = update.mock.calls[1][1];
      expect(computerUpdate.currentUserId).toBeNull();
      expect(computerUpdate.isActive).toBe(false);
      expect(computerUpdate.lastUserLogout).toBeDefined();
    });

    it('handles database error', async () => {
      update.mockRejectedValue(new Error('Update failed'));

      const result = await forceLogoutUser('user-123', 'comp-456');

      expect(result.success).toBe(false);
      expect(result.error).toBe('Failed to force logout user');
    });
  });

  describe('getComputerUsageStats', () => {
    it('returns stats with correct counts', async () => {
      // First call for computers
      get.mockResolvedValueOnce({
        exists: () => true,
        val: () => ({
          'comp-1': { computerName: 'PC-1', isActive: true, currentUserId: 'user-1' },
          'comp-2': { computerName: 'PC-2', isActive: false, currentUserId: null },
          'comp-3': { computerName: 'PC-3', isActive: true, currentUserId: 'user-2' },
        }),
      });
      // Second call for users
      get.mockResolvedValueOnce({
        exists: () => true,
        val: () => ({
          'user-1': { firstName: 'John', lastName: 'Doe' },
          'user-2': { firstName: 'Jane', lastName: 'Smith' },
        }),
      });

      const result = await getComputerUsageStats();

      expect(result.success).toBe(true);
      expect(result.data.totalComputers).toBe(3);
      expect(result.data.activeComputers).toBe(2);
      expect(result.data.computersWithUsers).toBe(2);
    });

    it('handles empty computers', async () => {
      get.mockResolvedValue({
        exists: () => false,
      });

      const result = await getComputerUsageStats();

      expect(result.success).toBe(true);
      expect(result.data.totalComputers).toBe(0);
    });
  });

  describe('getActiveComputerUsers - Session Time Bug Tests', () => {
    it('should return sessionStartTime for activity time, not loginTime', async () => {
      // Mock computers with a user
      get.mockResolvedValueOnce({
        exists: () => true,
        val: () => ({
          'comp-1': {
            computerName: 'PC-1',
            isActive: true,
            currentUserId: 'user-1',
            lastUserLogin: '2024-01-15T08:00:00Z', // When user logged into computer
          },
        }),
      });
      // Mock user data with session info
      get.mockResolvedValueOnce({
        exists: () => true,
        val: () => ({
          firstName: 'Test',
          lastName: 'User',
          phoneNumber: '0501234567',
          isSessionActive: true,
          sessionStartTime: '2024-01-15T10:00:00Z', // When paid session actually started
          remainingTime: 3600,
        }),
      });

      const result = await getActiveComputerUsers();

      expect(result.success).toBe(true);
      expect(result.data).toHaveLength(1);

      const activeUser = result.data[0];
      // BUG TEST: sessionStartTime should be returned, not loginTime
      expect(activeUser.sessionStartTime).toBe('2024-01-15T10:00:00Z');
    });

    it('should return null sessionStartTime when user has not started paid session', async () => {
      // Mock computers with a user who logged in but hasn't started session
      get.mockResolvedValueOnce({
        exists: () => true,
        val: () => ({
          'comp-1': {
            computerName: 'PC-1',
            isActive: true,
            currentUserId: 'user-1',
            lastUserLogin: '2024-01-15T08:00:00Z',
          },
        }),
      });
      // Mock user data - logged in but NO active session
      get.mockResolvedValueOnce({
        exists: () => true,
        val: () => ({
          firstName: 'Test',
          lastName: 'User',
          phoneNumber: '0501234567',
          isSessionActive: false, // NOT in active session
          sessionStartTime: null, // No session started
          remainingTime: 3600,
        }),
      });

      const result = await getActiveComputerUsers();

      expect(result.success).toBe(true);
      expect(result.data).toHaveLength(1);

      const activeUser = result.data[0];
      // Session start time should be null when not in active session
      expect(activeUser.sessionStartTime).toBeNull();
      expect(activeUser.sessionActive).toBe(false);
    });
  });
});
