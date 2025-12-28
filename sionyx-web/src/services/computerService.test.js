import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ref, get, update, remove } from 'firebase/database';
import {
  getAllComputers,
  getComputerUsageStats,
  getComputerById,
  updateComputer,
  deleteComputer,
  forceLogoutUser,
} from './computerService';

vi.mock('firebase/database');
vi.mock('../config/firebase', () => ({
  database: {},
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
});


