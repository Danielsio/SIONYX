import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useSupervisorAuthStore } from './supervisorAuthStore';

const localStorageMock = {
  store: {},
  getItem: vi.fn(key => localStorageMock.store[key] || null),
  setItem: vi.fn((key, value) => {
    localStorageMock.store[key] = String(value);
  }),
  removeItem: vi.fn(key => {
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

describe('supervisorAuthStore', () => {
  beforeEach(() => {
    useSupervisorAuthStore.setState({
      supervisor: null,
      isAuthenticated: false,
      isLoading: false,
    });
    localStorageMock.clear();
    vi.clearAllMocks();
  });

  describe('initial state', () => {
    it('has null supervisor initially', () => {
      const state = useSupervisorAuthStore.getState();
      expect(state.supervisor).toBeNull();
    });

    it('is not authenticated initially', () => {
      const state = useSupervisorAuthStore.getState();
      expect(state.isAuthenticated).toBe(false);
    });

    it('is not loading initially', () => {
      const state = useSupervisorAuthStore.getState();
      expect(state.isLoading).toBe(false);
    });
  });

  describe('setSupervisor', () => {
    it('sets supervisor and marks authenticated', () => {
      const mockSupervisor = {
        uid: 'sup-1',
        phone: '1234567890',
        name: 'Test Supervisor',
        orgIds: ['org-1'],
      };

      useSupervisorAuthStore.getState().setSupervisor(mockSupervisor);

      const state = useSupervisorAuthStore.getState();
      expect(state.supervisor).toEqual(mockSupervisor);
      expect(state.isAuthenticated).toBe(true);
    });

    it('clears authentication when supervisor is null', () => {
      useSupervisorAuthStore.getState().setSupervisor({
        uid: 'sup-1',
        orgIds: ['org-1'],
      });
      expect(useSupervisorAuthStore.getState().isAuthenticated).toBe(true);

      useSupervisorAuthStore.getState().setSupervisor(null);

      const state = useSupervisorAuthStore.getState();
      expect(state.supervisor).toBeNull();
      expect(state.isAuthenticated).toBe(false);
    });
  });

  describe('setLoading', () => {
    it('sets loading to true', () => {
      useSupervisorAuthStore.getState().setLoading(true);
      expect(useSupervisorAuthStore.getState().isLoading).toBe(true);
    });

    it('sets loading to false', () => {
      useSupervisorAuthStore.getState().setLoading(true);
      useSupervisorAuthStore.getState().setLoading(false);
      expect(useSupervisorAuthStore.getState().isLoading).toBe(false);
    });
  });

  describe('logout', () => {
    it('clears state', () => {
      useSupervisorAuthStore.getState().setSupervisor({
        uid: 'sup-1',
        orgIds: ['org-1'],
      });
      expect(useSupervisorAuthStore.getState().isAuthenticated).toBe(true);

      useSupervisorAuthStore.getState().logout();

      const state = useSupervisorAuthStore.getState();
      expect(state.supervisor).toBeNull();
      expect(state.isAuthenticated).toBe(false);
    });

    it('works even if already logged out', () => {
      useSupervisorAuthStore.getState().logout();

      const state = useSupervisorAuthStore.getState();
      expect(state.supervisor).toBeNull();
      expect(state.isAuthenticated).toBe(false);
    });
  });

  describe('getOrgIds', () => {
    it('returns supervisor orgIds when available', () => {
      useSupervisorAuthStore.getState().setSupervisor({
        uid: 'sup-1',
        orgIds: ['org-1', 'org-2'],
      });

      const orgIds = useSupervisorAuthStore.getState().getOrgIds();
      expect(orgIds).toEqual(['org-1', 'org-2']);
    });

    it('returns empty array when supervisor is null', () => {
      const orgIds = useSupervisorAuthStore.getState().getOrgIds();
      expect(orgIds).toEqual([]);
    });

    it('returns empty array when supervisor has no orgIds', () => {
      useSupervisorAuthStore.getState().setSupervisor({
        uid: 'sup-1',
        orgIds: undefined,
      });

      const orgIds = useSupervisorAuthStore.getState().getOrgIds();
      expect(orgIds).toEqual([]);
    });
  });
});
