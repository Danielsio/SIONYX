import { create } from 'zustand';

export const useNotificationStore = create((set, get) => ({
  notifications: [],
  unreadCount: 0,

  addNotification: notification =>
    set(state => ({
      notifications: [
        {
          id: Date.now().toString(),
          timestamp: new Date().toISOString(),
          read: false,
          ...notification,
        },
        ...state.notifications,
      ].slice(0, 50),
      unreadCount: state.unreadCount + 1,
    })),

  markAsRead: id =>
    set(state => {
      const target = state.notifications.find(n => n.id === id);
      const wasUnread = target && !target.read;
      return {
        notifications: state.notifications.map(n => (n.id === id ? { ...n, read: true } : n)),
        unreadCount: wasUnread ? Math.max(0, state.unreadCount - 1) : state.unreadCount,
      };
    }),

  markAllAsRead: () =>
    set(state => ({
      notifications: state.notifications.map(n => ({ ...n, read: true })),
      unreadCount: 0,
    })),

  clearAll: () => set({ notifications: [], unreadCount: 0 }),
}));
