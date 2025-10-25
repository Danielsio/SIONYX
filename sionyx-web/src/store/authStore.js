import { create } from 'zustand';
import { persist } from 'zustand/middleware';

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
