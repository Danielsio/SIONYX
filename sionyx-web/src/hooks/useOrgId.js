import { useAuthStore } from '../store/authStore';

/**
 * Hook to get the current organization ID.
 * 
 * Centralizes the pattern of getting orgId from user state
 * with localStorage fallback.
 * 
 * @returns {string|null} The organization ID or null if not available
 */
export const useOrgId = () => {
  return useAuthStore(state => state.getOrgId());
};

/**
 * Get orgId for use outside of React components (e.g., in services).
 * 
 * @returns {string|null} The organization ID or null if not available
 */
export const getOrgId = () => {
  return useAuthStore.getState().getOrgId();
};

