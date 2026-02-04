import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useAuthStore } from './authStore';

// Mock localStorage for persist middleware
const localStorageMock = {
  store: {},
  getItem: vi.fn((key) => localStorageMock.store[key] || null),
  setItem: vi.fn((key, value) => {
    localStorageMock.store[key] = String(value);
  }),
  removeItem: vi.fn((key) => {
    delete localStorageMock.store[key];
  }),
  clear: vi.fn(() => {
    localStorageMock.store = {};
  }),
};

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
  writable: true,
});

describe('authStore', () => {
  beforeEach(() => {
    // Reset store to initial state before each test
    useAuthStore.setState({
      user: null,
      isAuthenticated: false,
      isLoading: false,
    });
    localStorageMock.clear();
    vi.clearAllMocks();
  });

  describe('initial state', () => {
    it('has null user initially', () => {
      const state = useAuthStore.getState();
      expect(state.user).toBeNull();
    });

    it('is not authenticated initially', () => {
      const state = useAuthStore.getState();
      expect(state.isAuthenticated).toBe(false);
    });

    it('is not loading initially', () => {
      const state = useAuthStore.getState();
      expect(state.isLoading).toBe(false);
    });
  });

  describe('setUser', () => {
    it('sets user and marks as authenticated', () => {
      const mockUser = {
        uid: 'user-123',
        orgId: 'org-abc',
        displayName: 'Test User',
      };

      useAuthStore.getState().setUser(mockUser);

      const state = useAuthStore.getState();
      expect(state.user).toEqual(mockUser);
      expect(state.isAuthenticated).toBe(true);
    });

    it('clears authentication when user is null', () => {
      // First set a user
      useAuthStore.getState().setUser({ uid: 'user-123' });
      expect(useAuthStore.getState().isAuthenticated).toBe(true);

      // Then clear it
      useAuthStore.getState().setUser(null);

      const state = useAuthStore.getState();
      expect(state.user).toBeNull();
      expect(state.isAuthenticated).toBe(false);
    });

    it('clears authentication when user is undefined', () => {
      useAuthStore.getState().setUser({ uid: 'user-123' });
      useAuthStore.getState().setUser(undefined);

      const state = useAuthStore.getState();
      expect(state.user).toBeUndefined();
      expect(state.isAuthenticated).toBe(false);
    });
  });

  describe('setLoading', () => {
    it('sets loading to true', () => {
      useAuthStore.getState().setLoading(true);
      expect(useAuthStore.getState().isLoading).toBe(true);
    });

    it('sets loading to false', () => {
      useAuthStore.getState().setLoading(true);
      useAuthStore.getState().setLoading(false);
      expect(useAuthStore.getState().isLoading).toBe(false);
    });
  });

  describe('logout', () => {
    it('clears user and sets isAuthenticated to false', () => {
      // First login
      useAuthStore.getState().setUser({
        uid: 'user-123',
        orgId: 'org-abc',
      });
      expect(useAuthStore.getState().isAuthenticated).toBe(true);

      // Then logout
      useAuthStore.getState().logout();

      const state = useAuthStore.getState();
      expect(state.user).toBeNull();
      expect(state.isAuthenticated).toBe(false);
    });

    it('works even if already logged out', () => {
      useAuthStore.getState().logout();

      const state = useAuthStore.getState();
      expect(state.user).toBeNull();
      expect(state.isAuthenticated).toBe(false);
    });
  });

  describe('getOrgId', () => {
    it('returns orgId from user if available', () => {
      useAuthStore.getState().setUser({
        uid: 'user-123',
        orgId: 'my-organization',
      });

      const orgId = useAuthStore.getState().getOrgId();
      expect(orgId).toBe('my-organization');
    });

    it('falls back to localStorage if user has no orgId', () => {
      localStorageMock.store['adminOrgId'] = 'stored-org-id';
      
      useAuthStore.getState().setUser({
        uid: 'user-123',
        // No orgId
      });

      const orgId = useAuthStore.getState().getOrgId();
      expect(orgId).toBe('stored-org-id');
    });

    it('returns localStorage value if user is null', () => {
      localStorageMock.store['adminOrgId'] = 'stored-org-id';

      const orgId = useAuthStore.getState().getOrgId();
      expect(orgId).toBe('stored-org-id');
    });

    it('returns null if no orgId anywhere', () => {
      const orgId = useAuthStore.getState().getOrgId();
      expect(orgId).toBeNull();
    });

    it('prefers user orgId over localStorage', () => {
      localStorageMock.store['adminOrgId'] = 'stored-org-id';
      
      useAuthStore.getState().setUser({
        uid: 'user-123',
        orgId: 'user-org-id',
      });

      const orgId = useAuthStore.getState().getOrgId();
      expect(orgId).toBe('user-org-id');
    });
  });

  describe('selector usage', () => {
    it('can select individual properties', () => {
      useAuthStore.getState().setUser({ uid: 'user-123', orgId: 'org-abc' });

      // Simulate how components use selectors
      const isAuthenticated = useAuthStore.getState().isAuthenticated;
      const user = useAuthStore.getState().user;

      expect(isAuthenticated).toBe(true);
      expect(user.uid).toBe('user-123');
    });
  });

  describe('role helpers', () => {
    describe('getRole', () => {
      it('returns user role from role field', () => {
        useAuthStore.getState().setUser({ uid: 'u1', role: 'admin' });
        expect(useAuthStore.getState().getRole()).toBe('admin');
      });

      it('returns supervisor role', () => {
        useAuthStore.getState().setUser({ uid: 'u1', role: 'supervisor' });
        expect(useAuthStore.getState().getRole()).toBe('supervisor');
      });

      it('falls back to isAdmin when no role field', () => {
        useAuthStore.getState().setUser({ uid: 'u1', isAdmin: true });
        expect(useAuthStore.getState().getRole()).toBe('admin');
      });

      it('returns user when no role and not admin', () => {
        useAuthStore.getState().setUser({ uid: 'u1' });
        expect(useAuthStore.getState().getRole()).toBe('user');
      });

      it('returns user when user is null', () => {
        expect(useAuthStore.getState().getRole()).toBe('user');
      });
    });

    describe('hasRole', () => {
      it('returns true when user has required role', () => {
        useAuthStore.getState().setUser({ uid: 'u1', role: 'admin' });
        expect(useAuthStore.getState().hasRole('admin')).toBe(true);
        expect(useAuthStore.getState().hasRole('user')).toBe(true);
      });

      it('returns false when user lacks required role', () => {
        useAuthStore.getState().setUser({ uid: 'u1', role: 'user' });
        expect(useAuthStore.getState().hasRole('admin')).toBe(false);
      });

      it('supervisor has all roles', () => {
        useAuthStore.getState().setUser({ uid: 'u1', role: 'supervisor' });
        expect(useAuthStore.getState().hasRole('supervisor')).toBe(true);
        expect(useAuthStore.getState().hasRole('admin')).toBe(true);
        expect(useAuthStore.getState().hasRole('user')).toBe(true);
      });
    });

    describe('isAdminOrAbove', () => {
      it('returns true for admin', () => {
        useAuthStore.getState().setUser({ uid: 'u1', role: 'admin' });
        expect(useAuthStore.getState().isAdminOrAbove()).toBe(true);
      });

      it('returns true for supervisor', () => {
        useAuthStore.getState().setUser({ uid: 'u1', role: 'supervisor' });
        expect(useAuthStore.getState().isAdminOrAbove()).toBe(true);
      });

      it('returns false for regular user', () => {
        useAuthStore.getState().setUser({ uid: 'u1', role: 'user' });
        expect(useAuthStore.getState().isAdminOrAbove()).toBe(false);
      });

      it('works with legacy isAdmin field', () => {
        useAuthStore.getState().setUser({ uid: 'u1', isAdmin: true });
        expect(useAuthStore.getState().isAdminOrAbove()).toBe(true);
      });
    });

    describe('isSupervisor', () => {
      it('returns true for supervisor', () => {
        useAuthStore.getState().setUser({ uid: 'u1', role: 'supervisor' });
        expect(useAuthStore.getState().isSupervisor()).toBe(true);
      });

      it('returns false for admin', () => {
        useAuthStore.getState().setUser({ uid: 'u1', role: 'admin' });
        expect(useAuthStore.getState().isSupervisor()).toBe(false);
      });

      it('returns false for regular user', () => {
        useAuthStore.getState().setUser({ uid: 'u1', role: 'user' });
        expect(useAuthStore.getState().isSupervisor()).toBe(false);
      });
    });
  });
});


