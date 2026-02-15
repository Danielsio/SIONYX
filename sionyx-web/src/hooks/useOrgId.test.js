import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook } from '@testing-library/react';
import { useOrgId, getOrgId } from './useOrgId';
import { useAuthStore } from '../store/authStore';

vi.mock('../store/authStore');

describe('useOrgId', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('useOrgId hook', () => {
    it('returns orgId from auth store', () => {
      useAuthStore.mockImplementation(selector => {
        const state = {
          getOrgId: () => 'test-org-123',
        };
        return selector(state);
      });

      const { result } = renderHook(() => useOrgId());

      expect(result.current).toBe('test-org-123');
    });

    it('returns null when no orgId available', () => {
      useAuthStore.mockImplementation(selector => {
        const state = {
          getOrgId: () => null,
        };
        return selector(state);
      });

      const { result } = renderHook(() => useOrgId());

      expect(result.current).toBeNull();
    });

    it('returns undefined when getOrgId returns undefined', () => {
      useAuthStore.mockImplementation(selector => {
        const state = {
          getOrgId: () => undefined,
        };
        return selector(state);
      });

      const { result } = renderHook(() => useOrgId());

      expect(result.current).toBeUndefined();
    });
  });

  describe('getOrgId function', () => {
    it('returns orgId from auth store state', () => {
      useAuthStore.getState = vi.fn().mockReturnValue({
        getOrgId: () => 'static-org-456',
      });

      const result = getOrgId();

      expect(result).toBe('static-org-456');
    });

    it('returns null when no orgId in state', () => {
      useAuthStore.getState = vi.fn().mockReturnValue({
        getOrgId: () => null,
      });

      const result = getOrgId();

      expect(result).toBeNull();
    });
  });
});
