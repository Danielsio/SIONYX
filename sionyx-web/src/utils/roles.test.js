import { describe, it, expect } from 'vitest';
import {
  ROLES,
  ROLE_HIERARCHY,
  getUserRole,
  hasRole,
  isAdminOrAbove,
  isSupervisor,
  getRoleDisplayName,
} from './roles';

describe('roles utility', () => {
  describe('ROLES constant', () => {
    it('has correct role values', () => {
      expect(ROLES.USER).toBe('user');
      expect(ROLES.ADMIN).toBe('admin');
      expect(ROLES.SUPERVISOR).toBe('supervisor');
    });
  });

  describe('ROLE_HIERARCHY', () => {
    it('has correct hierarchy order', () => {
      expect(ROLE_HIERARCHY[ROLES.USER]).toBeLessThan(ROLE_HIERARCHY[ROLES.ADMIN]);
      expect(ROLE_HIERARCHY[ROLES.ADMIN]).toBeLessThan(ROLE_HIERARCHY[ROLES.SUPERVISOR]);
    });
  });

  describe('getUserRole', () => {
    it('returns user role when no user', () => {
      expect(getUserRole(null)).toBe(ROLES.USER);
      expect(getUserRole(undefined)).toBe(ROLES.USER);
    });

    it('returns role from role field when present', () => {
      expect(getUserRole({ role: 'admin' })).toBe('admin');
      expect(getUserRole({ role: 'supervisor' })).toBe('supervisor');
      expect(getUserRole({ role: 'user' })).toBe('user');
    });

    it('falls back to isAdmin when role field missing', () => {
      expect(getUserRole({ isAdmin: true })).toBe(ROLES.ADMIN);
      expect(getUserRole({ isAdmin: false })).toBe(ROLES.USER);
    });

    it('prefers role field over isAdmin', () => {
      expect(getUserRole({ role: 'supervisor', isAdmin: true })).toBe('supervisor');
      expect(getUserRole({ role: 'user', isAdmin: true })).toBe('user');
    });

    it('returns user when no role and isAdmin is false', () => {
      expect(getUserRole({})).toBe(ROLES.USER);
      expect(getUserRole({ isAdmin: false })).toBe(ROLES.USER);
    });
  });

  describe('hasRole', () => {
    it('returns true when user has exact role', () => {
      expect(hasRole({ role: 'admin' }, ROLES.ADMIN)).toBe(true);
      expect(hasRole({ role: 'supervisor' }, ROLES.SUPERVISOR)).toBe(true);
    });

    it('returns true when user has higher role', () => {
      expect(hasRole({ role: 'supervisor' }, ROLES.ADMIN)).toBe(true);
      expect(hasRole({ role: 'supervisor' }, ROLES.USER)).toBe(true);
      expect(hasRole({ role: 'admin' }, ROLES.USER)).toBe(true);
    });

    it('returns false when user has lower role', () => {
      expect(hasRole({ role: 'user' }, ROLES.ADMIN)).toBe(false);
      expect(hasRole({ role: 'admin' }, ROLES.SUPERVISOR)).toBe(false);
    });

    it('works with isAdmin fallback', () => {
      expect(hasRole({ isAdmin: true }, ROLES.ADMIN)).toBe(true);
      expect(hasRole({ isAdmin: true }, ROLES.USER)).toBe(true);
      expect(hasRole({ isAdmin: true }, ROLES.SUPERVISOR)).toBe(false);
    });
  });

  describe('isAdminOrAbove', () => {
    it('returns true for admin', () => {
      expect(isAdminOrAbove({ role: 'admin' })).toBe(true);
      expect(isAdminOrAbove({ isAdmin: true })).toBe(true);
    });

    it('returns true for supervisor', () => {
      expect(isAdminOrAbove({ role: 'supervisor' })).toBe(true);
    });

    it('returns false for user', () => {
      expect(isAdminOrAbove({ role: 'user' })).toBe(false);
      expect(isAdminOrAbove(null)).toBe(false);
    });
  });

  describe('isSupervisor', () => {
    it('returns true only for supervisor', () => {
      expect(isSupervisor({ role: 'supervisor' })).toBe(true);
    });

    it('returns false for admin and user', () => {
      expect(isSupervisor({ role: 'admin' })).toBe(false);
      expect(isSupervisor({ role: 'user' })).toBe(false);
      expect(isSupervisor({ isAdmin: true })).toBe(false);
    });
  });

  describe('getRoleDisplayName', () => {
    it('returns Hebrew display names', () => {
      expect(getRoleDisplayName(ROLES.SUPERVISOR)).toBe('מפקח');
      expect(getRoleDisplayName(ROLES.ADMIN)).toBe('מנהל');
      expect(getRoleDisplayName(ROLES.USER)).toBe('משתמש');
    });

    it('returns user for unknown roles', () => {
      expect(getRoleDisplayName('unknown')).toBe('משתמש');
      expect(getRoleDisplayName(null)).toBe('משתמש');
    });
  });
});
