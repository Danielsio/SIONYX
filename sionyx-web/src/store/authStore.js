import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import {
  getUserRole,
  hasRole as checkRole,
  isAdminOrAbove,
  isSupervisor,
  ROLES,
} from '../utils/roles.js';

export const useAuthStore = create(
  persist(
    (set, get) => ({
      user: null,
      isAuthenticated: false,
      isLoading: false,

      setUser: user =>
        set({
          user,
          isAuthenticated: !!user,
        }),

      setLoading: isLoading => set({ isLoading }),

      logout: () =>
        set({
          user: null,
          isAuthenticated: false,
        }),

      getOrgId: () => {
        const state = get();
        return state.user?.orgId || localStorage.getItem('adminOrgId');
      },

      // Role helpers
      getRole: () => getUserRole(get().user),

      hasRole: requiredRole => checkRole(get().user, requiredRole),

      isAdminOrAbove: () => isAdminOrAbove(get().user),

      isSupervisor: () => isSupervisor(get().user),
    }),
    {
      name: 'admin-auth-storage',
      partialize: state => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);
