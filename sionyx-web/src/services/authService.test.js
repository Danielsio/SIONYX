import { describe, it, expect, vi, beforeEach } from 'vitest';
import {
  signInWithEmailAndPassword,
  signOut as firebaseSignOut,
  onAuthStateChanged,
} from 'firebase/auth';
import { ref, get, set } from 'firebase/database';
import { signInAdmin, signOut, getCurrentAdminData, onAuthChange } from './authService';
import { auth } from '../config/firebase';

// Mock firebase modules
vi.mock('firebase/auth');
vi.mock('firebase/database');
vi.mock('../config/firebase', () => ({
  auth: {
    currentUser: null,
  },
  database: {},
}));

describe('authService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  describe('signInAdmin', () => {
    it('returns error if orgId is empty', async () => {
      const result = await signInAdmin('1234567890', 'password', '');

      expect(result.success).toBe(false);
      expect(result.error).toBe('Organization ID is required');
    });

    it('returns error if orgId is whitespace only', async () => {
      const result = await signInAdmin('1234567890', 'password', '   ');

      expect(result.success).toBe(false);
      expect(result.error).toBe('Organization ID is required');
    });

    it('returns error if orgId has invalid characters', async () => {
      const result = await signInAdmin('1234567890', 'password', 'My Org!');

      expect(result.success).toBe(false);
      expect(result.error).toContain('Invalid Organization ID format');
    });

    it('accepts valid orgId with lowercase and hyphens', async () => {
      signInWithEmailAndPassword.mockResolvedValue({
        user: { uid: 'user-123' },
      });
      get.mockResolvedValue({
        exists: () => false,
      });

      const result = await signInAdmin('1234567890', 'password', 'my-org-123');

      // Should fail because user doesn't exist in org, but orgId validation passed
      expect(signInWithEmailAndPassword).toHaveBeenCalled();
    });

    it('converts phone to email format correctly', async () => {
      signInWithEmailAndPassword.mockResolvedValue({
        user: { uid: 'user-123' },
      });
      get.mockResolvedValue({ exists: () => false });

      await signInAdmin('123-456-7890', 'password', 'my-org');

      expect(signInWithEmailAndPassword).toHaveBeenCalledWith(
        expect.anything(),
        '1234567890@sionyx.app',
        'password'
      );
    });

    it('returns error if user not found in organization', async () => {
      signInWithEmailAndPassword.mockResolvedValue({
        user: { uid: 'user-123' },
      });
      get.mockResolvedValue({
        exists: () => false,
      });
      firebaseSignOut.mockResolvedValue();

      const result = await signInAdmin('1234567890', 'password', 'my-org');

      expect(result.success).toBe(false);
      expect(result.error).toContain('No account found in organization');
      expect(firebaseSignOut).toHaveBeenCalled();
    });

    it('returns error if user is not admin', async () => {
      signInWithEmailAndPassword.mockResolvedValue({
        user: { uid: 'user-123' },
      });
      get.mockResolvedValue({
        exists: () => true,
        val: () => ({ isAdmin: false, firstName: 'Test' }),
      });
      firebaseSignOut.mockResolvedValue();

      const result = await signInAdmin('1234567890', 'password', 'my-org');

      expect(result.success).toBe(false);
      expect(result.error).toContain('do not have administrator privileges');
      expect(firebaseSignOut).toHaveBeenCalled();
    });

    it('returns success for valid admin user', async () => {
      signInWithEmailAndPassword.mockResolvedValue({
        user: { uid: 'user-123' },
      });
      get.mockResolvedValue({
        exists: () => true,
        val: () => ({ isAdmin: true, firstName: 'Admin', lastName: 'User' }),
      });
      set.mockResolvedValue();

      const result = await signInAdmin('1234567890', 'password', 'my-org');

      expect(result.success).toBe(true);
      expect(result.user).toBeDefined();
      expect(result.user.uid).toBe('user-123');
      expect(result.user.orgId).toBe('my-org');
      expect(localStorage.getItem('adminOrgId')).toBe('my-org');
    });

    it('handles auth/invalid-credential error', async () => {
      signInWithEmailAndPassword.mockRejectedValue({
        code: 'auth/invalid-credential',
      });

      const result = await signInAdmin('1234567890', 'wrong', 'my-org');

      expect(result.success).toBe(false);
      expect(result.error).toBe('Invalid phone number or password');
    });

    it('handles auth/user-not-found error', async () => {
      signInWithEmailAndPassword.mockRejectedValue({
        code: 'auth/user-not-found',
      });

      const result = await signInAdmin('1234567890', 'password', 'my-org');

      expect(result.success).toBe(false);
      expect(result.error).toBe('No account found with this phone number');
    });

    it('handles auth/too-many-requests error', async () => {
      signInWithEmailAndPassword.mockRejectedValue({
        code: 'auth/too-many-requests',
      });

      const result = await signInAdmin('1234567890', 'password', 'my-org');

      expect(result.success).toBe(false);
      expect(result.error).toContain('Too many failed attempts');
    });

    it('handles network error', async () => {
      signInWithEmailAndPassword.mockRejectedValue({
        code: 'auth/network-request-failed',
      });

      const result = await signInAdmin('1234567890', 'password', 'my-org');

      expect(result.success).toBe(false);
      expect(result.error).toContain('Network error');
    });
  });

  describe('signOut', () => {
    it('signs out successfully and clears localStorage', async () => {
      localStorage.setItem('adminOrgId', 'my-org');
      firebaseSignOut.mockResolvedValue();

      const result = await signOut();

      expect(result.success).toBe(true);
      expect(firebaseSignOut).toHaveBeenCalled();
      expect(localStorage.getItem('adminOrgId')).toBeNull();
    });

    it('handles signOut error', async () => {
      firebaseSignOut.mockRejectedValue(new Error('Sign out failed'));

      const result = await signOut();

      expect(result.success).toBe(false);
      expect(result.error).toBe('Sign out failed');
    });
  });

  describe('getCurrentAdminData', () => {
    it('returns error if not authenticated', async () => {
      auth.currentUser = null;

      const result = await getCurrentAdminData();

      expect(result.success).toBe(false);
      expect(result.error).toBe('Not authenticated');
    });

    it('returns error if orgId not in localStorage', async () => {
      auth.currentUser = { uid: 'user-123' };
      localStorage.removeItem('adminOrgId');

      const result = await getCurrentAdminData();

      expect(result.success).toBe(false);
      expect(result.error).toContain('Organization ID not found');
    });

    it('returns error if user data not found', async () => {
      auth.currentUser = { uid: 'user-123' };
      localStorage.setItem('adminOrgId', 'my-org');
      get.mockResolvedValue({
        exists: () => false,
      });

      const result = await getCurrentAdminData();

      expect(result.success).toBe(false);
      expect(result.error).toBe('User data not found');
    });

    it('returns error if admin privileges revoked', async () => {
      auth.currentUser = { uid: 'user-123' };
      localStorage.setItem('adminOrgId', 'my-org');
      get.mockResolvedValue({
        exists: () => true,
        val: () => ({ isAdmin: false }),
      });

      const result = await getCurrentAdminData();

      expect(result.success).toBe(false);
      expect(result.error).toContain('Admin privileges revoked');
    });

    it('returns admin data successfully', async () => {
      auth.currentUser = { uid: 'user-123' };
      localStorage.setItem('adminOrgId', 'my-org');
      get.mockResolvedValue({
        exists: () => true,
        val: () => ({ isAdmin: true, firstName: 'Admin', lastName: 'User' }),
      });

      const result = await getCurrentAdminData();

      expect(result.success).toBe(true);
      expect(result.admin).toBeDefined();
      expect(result.admin.uid).toBe('user-123');
      expect(result.admin.orgId).toBe('my-org');
      expect(result.admin.isAdmin).toBe(true);
    });
  });

  describe('onAuthChange', () => {
    it('subscribes to auth state changes', () => {
      const mockCallback = vi.fn();
      const mockUnsubscribe = vi.fn();
      onAuthStateChanged.mockReturnValue(mockUnsubscribe);

      const unsubscribe = onAuthChange(mockCallback);

      expect(onAuthStateChanged).toHaveBeenCalledWith(auth, mockCallback);
      expect(unsubscribe).toBe(mockUnsubscribe);
    });
  });
});


