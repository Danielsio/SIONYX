import { describe, it, expect } from 'vitest';
import {
  ROLES,
  ROLE_HIERARCHY,
  getUserRole,
  hasRole,
  isAdminOrAbove,
  getRoleDisplayName,
} from './roles';

describe('roles utility', () => {
  describe('ROLES constant', () => {
    it('has correct role values', () => {
      expect(ROLES.USER).toBe('user');
      expect(ROLES.ADMIN).toBe('admin');
    });

    it('does not contain supervisor (handled separately)', () => {
      expect(ROLES).not.toHaveProperty('SUPERVISOR');
    });
  });

  describe('ROLE_HIERARCHY', () => {
    it('has correct hierarchy order', () => {
      expect(ROLE_HIERARCHY[ROLES.USER]).toBeLessThan(ROLE_HIERARCHY[ROLES.ADMIN]);
    });
  });

  describe('getUserRole', () => {
    it('returns user role when no user', () => {
      expect(getUserRole(null)).toBe(ROLES.USER);
      expect(getUserRole(undefined)).toBe(ROLES.USER);
    });

    it('returns admin from role field', () => {
      expect(getUserRole({ role: 'admin' })).toBe('admin');
    });

    it('returns user for unknown role values', () => {
      expect(getUserRole({ role: 'supervisor' })).toBe('user');
      expect(getUserRole({ role: 'unknown' })).toBe('user');
    });

    it('falls back to isAdmin when role field missing', () => {
      expect(getUserRole({ isAdmin: true })).toBe(ROLES.ADMIN);
      expect(getUserRole({ isAdmin: false })).toBe(ROLES.USER);
    });

    it('returns user when no role and isAdmin is false', () => {
      expect(getUserRole({})).toBe(ROLES.USER);
      expect(getUserRole({ isAdmin: false })).toBe(ROLES.USER);
    });
  });

  describe('hasRole', () => {
    it('returns true when user has exact role', () => {
      expect(hasRole({ role: 'admin' }, ROLES.ADMIN)).toBe(true);
    });

    it('returns true when user has higher role', () => {
      expect(hasRole({ role: 'admin' }, ROLES.USER)).toBe(true);
    });

    it('returns false when user has lower role', () => {
      expect(hasRole({ role: 'user' }, ROLES.ADMIN)).toBe(false);
    });

    it('works with isAdmin fallback', () => {
      expect(hasRole({ isAdmin: true }, ROLES.ADMIN)).toBe(true);
      expect(hasRole({ isAdmin: true }, ROLES.USER)).toBe(true);
    });
  });

  describe('isAdminOrAbove', () => {
    it('returns true for admin', () => {
      expect(isAdminOrAbove({ role: 'admin' })).toBe(true);
      expect(isAdminOrAbove({ isAdmin: true })).toBe(true);
    });

    it('returns false for user', () => {
      expect(isAdminOrAbove({ role: 'user' })).toBe(false);
      expect(isAdminOrAbove(null)).toBe(false);
    });
  });

  describe('getRoleDisplayName', () => {
    it('returns Hebrew display names', () => {
      expect(getRoleDisplayName(ROLES.ADMIN)).toBe('מנהל');
      expect(getRoleDisplayName(ROLES.USER)).toBe('משתמש');
    });

    it('returns user for unknown roles', () => {
      expect(getRoleDisplayName('unknown')).toBe('משתמש');
      expect(getRoleDisplayName(null)).toBe('משתמש');
    });
  });
});
