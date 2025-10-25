import { create } from 'zustand';

export const useDataStore = create(set => ({
  users: [],
  packages: [],
  stats: null,

  setUsers: users => set({ users }),
  setPackages: packages => set({ packages }),
  setStats: stats => set({ stats }),

  addPackage: newPackage =>
    set(state => ({
      packages: [newPackage, ...state.packages],
    })),

  updatePackage: (packageId, updates) =>
    set(state => ({
      packages: state.packages.map(pkg => (pkg.id === packageId ? { ...pkg, ...updates } : pkg)),
    })),

  removePackage: packageId =>
    set(state => ({
      packages: state.packages.filter(pkg => pkg.id !== packageId),
    })),

  updateUser: (userId, updates) =>
    set(state => ({
      users: state.users.map(user => (user.uid === userId ? { ...user, ...updates } : user)),
    })),
}));
