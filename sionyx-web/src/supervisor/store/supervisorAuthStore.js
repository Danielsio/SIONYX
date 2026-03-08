import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export const useSupervisorAuthStore = create(
  persist(
    (set, get) => ({
      supervisor: null,
      isAuthenticated: false,
      isLoading: false,

      setSupervisor: supervisor =>
        set({
          supervisor,
          isAuthenticated: !!supervisor,
        }),

      setLoading: isLoading => set({ isLoading }),

      logout: () =>
        set({
          supervisor: null,
          isAuthenticated: false,
        }),

      getOrgIds: () => {
        const state = get();
        return state.supervisor?.orgIds || [];
      },
    }),
    {
      name: 'supervisor-auth-storage',
      partialize: state => ({
        supervisor: state.supervisor,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);
