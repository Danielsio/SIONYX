import { describe, it, expect, vi, beforeEach } from 'vitest';
import {
  signInWithEmailAndPassword,
  signOut as firebaseSignOut,
  onAuthStateChanged,
} from 'firebase/auth';
import { ref, get } from 'firebase/database';
import {
  signInSupervisor,
  signOutSupervisor,
  getCurrentSupervisorData,
  onSupervisorAuthChange,
} from './supervisorAuthService';
import { auth } from '../../config/firebase';

vi.mock('firebase/auth');
vi.mock('firebase/database');
vi.mock('../../config/firebase', () => ({
  auth: { currentUser: null },
  database: {},
}));

describe('supervisorAuthService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    auth.currentUser = null;
    localStorage.clear();
  });

  describe('signInSupervisor', () => {
    it('returns error on empty phone', async () => {
      const result = await signInSupervisor('', 'password');

      expect(result.success).toBe(false);
      expect(result.error).toBe('Phone and password are required');
    });

    it('returns error on empty password', async () => {
      const result = await signInSupervisor('1234567890', '');

      expect(result.success).toBe(false);
      expect(result.error).toBe('Phone and password are required');
    });

    it('returns error when user is not a supervisor', async () => {
      signInWithEmailAndPassword.mockResolvedValue({
        user: { uid: 'user-123' },
      });
      get.mockResolvedValue({ exists: () => false });
      firebaseSignOut.mockResolvedValue();

      const result = await signInSupervisor('1234567890', 'password');

      expect(result.success).toBe(false);
      expect(result.error).toBe('You do not have supervisor privileges.');
      expect(firebaseSignOut).toHaveBeenCalled();
    });

    it('returns success with supervisor data when valid', async () => {
      signInWithEmailAndPassword.mockResolvedValue({
        user: { uid: 'sup-1' },
      });
      get
        .mockResolvedValueOnce({
          exists: () => true,
          val: () => ({ name: 'Supervisor', email: 'sup@test.com' }),
        })
        .mockResolvedValueOnce({
          exists: () => true,
          val: () => ({ org1: true, org2: true }),
        });

      const result = await signInSupervisor('1234567890', 'password');

      expect(result.success).toBe(true);
      expect(result.supervisor).toEqual({
        uid: 'sup-1',
        phone: '1234567890',
        name: 'Supervisor',
        email: 'sup@test.com',
        orgIds: ['org1', 'org2'],
      });
      expect(localStorage.getItem('supervisorUid')).toBe('sup-1');
    });

    it('returns empty orgIds when organizations path does not exist', async () => {
      signInWithEmailAndPassword.mockResolvedValue({
        user: { uid: 'sup-1' },
      });
      get
        .mockResolvedValueOnce({
          exists: () => true,
          val: () => ({ name: 'Supervisor' }),
        })
        .mockResolvedValueOnce({ exists: () => false });

      const result = await signInSupervisor('1234567890', 'password');

      expect(result.success).toBe(true);
      expect(result.supervisor.orgIds).toEqual([]);
    });
  });

  describe('signOutSupervisor', () => {
    it('clears localStorage', async () => {
      localStorage.setItem('supervisorUid', 'sup-1');
      firebaseSignOut.mockResolvedValue();

      const result = await signOutSupervisor();

      expect(result.success).toBe(true);
      expect(firebaseSignOut).toHaveBeenCalled();
      expect(localStorage.getItem('supervisorUid')).toBeNull();
    });

    it('handles signOut error', async () => {
      firebaseSignOut.mockRejectedValue(new Error('Sign out failed'));

      const result = await signOutSupervisor();

      expect(result.success).toBe(false);
      expect(result.error).toBe('Sign out failed');
    });
  });

  describe('getCurrentSupervisorData', () => {
    it('returns error when not authenticated', async () => {
      auth.currentUser = null;

      const result = await getCurrentSupervisorData();

      expect(result.success).toBe(false);
      expect(result.error).toBe('Not authenticated');
    });

    it('returns supervisor data when authenticated', async () => {
      auth.currentUser = { uid: 'sup-1' };
      get
        .mockResolvedValueOnce({
          exists: () => true,
          val: () => ({
            name: 'Supervisor',
            email: 'sup@test.com',
            phone: '1234567890',
          }),
        })
        .mockResolvedValueOnce({
          exists: () => true,
          val: () => ({ org1: true }),
        });

      const result = await getCurrentSupervisorData();

      expect(result.success).toBe(true);
      expect(result.supervisor).toEqual({
        uid: 'sup-1',
        name: 'Supervisor',
        email: 'sup@test.com',
        phone: '1234567890',
        orgIds: ['org1'],
      });
    });

    it('returns error when supervisor data not found', async () => {
      auth.currentUser = { uid: 'sup-1' };
      get.mockResolvedValue({ exists: () => false });

      const result = await getCurrentSupervisorData();

      expect(result.success).toBe(false);
      expect(result.error).toBe('Supervisor data not found');
    });
  });

  describe('onSupervisorAuthChange', () => {
    it('subscribes to auth state changes', () => {
      const mockCallback = vi.fn();
      const mockUnsubscribe = vi.fn();
      onAuthStateChanged.mockReturnValue(mockUnsubscribe);

      const unsubscribe = onSupervisorAuthChange(mockCallback);

      expect(onAuthStateChanged).toHaveBeenCalledWith(auth, mockCallback);
      expect(unsubscribe).toBe(mockUnsubscribe);
    });
  });
});
