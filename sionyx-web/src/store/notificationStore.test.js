import { describe, it, expect, beforeEach } from 'vitest';
import { useNotificationStore } from './notificationStore';

describe('notificationStore', () => {
  beforeEach(() => {
    useNotificationStore.getState().clearAll();
  });

  it('addNotification adds a notification with id, timestamp, read: false', () => {
    const { addNotification, notifications } = useNotificationStore.getState();
    addNotification({ type: 'message', message: 'Test notification' });

    const state = useNotificationStore.getState();
    expect(state.notifications).toHaveLength(1);
    expect(state.notifications[0]).toMatchObject({
      type: 'message',
      message: 'Test notification',
      read: false,
    });
    expect(state.notifications[0].id).toBeDefined();
    expect(state.notifications[0].timestamp).toBeDefined();
  });

  it('markAsRead marks a notification as read and decrements unreadCount', () => {
    const { addNotification, markAsRead } = useNotificationStore.getState();
    addNotification({ type: 'message', message: 'Test' });
    const id = useNotificationStore.getState().notifications[0].id;

    markAsRead(id);

    const state = useNotificationStore.getState();
    expect(state.notifications[0].read).toBe(true);
    expect(state.unreadCount).toBe(0);
  });

  it('markAsRead does not decrement unreadCount when notification already read', () => {
    const { addNotification, markAsRead } = useNotificationStore.getState();
    addNotification({ type: 'message', message: 'Test' });
    const id = useNotificationStore.getState().notifications[0].id;
    markAsRead(id);
    expect(useNotificationStore.getState().unreadCount).toBe(0);

    markAsRead(id);
    expect(useNotificationStore.getState().unreadCount).toBe(0);
  });

  it('markAllAsRead marks all notifications as read and sets unreadCount to 0', () => {
    const { addNotification, markAllAsRead } = useNotificationStore.getState();
    addNotification({ type: 'message', message: 'One' });
    addNotification({ type: 'user', message: 'Two' });
    expect(useNotificationStore.getState().unreadCount).toBe(2);

    markAllAsRead();

    const state = useNotificationStore.getState();
    expect(state.notifications.every(n => n.read)).toBe(true);
    expect(state.unreadCount).toBe(0);
  });

  it('clearAll removes all notifications and resets unreadCount', () => {
    const { addNotification, clearAll } = useNotificationStore.getState();
    addNotification({ type: 'message', message: 'Test' });
    expect(useNotificationStore.getState().notifications).toHaveLength(1);

    clearAll();

    const state = useNotificationStore.getState();
    expect(state.notifications).toEqual([]);
    expect(state.unreadCount).toBe(0);
  });

  it('unreadCount tracks unread notifications correctly', () => {
    const { addNotification, markAsRead } = useNotificationStore.getState();
    expect(useNotificationStore.getState().unreadCount).toBe(0);

    addNotification({ type: 'message', message: 'A' });
    expect(useNotificationStore.getState().unreadCount).toBe(1);

    addNotification({ type: 'message', message: 'B' });
    expect(useNotificationStore.getState().unreadCount).toBe(2);

    const idA = useNotificationStore.getState().notifications[0].id;
    markAsRead(idA);
    expect(useNotificationStore.getState().unreadCount).toBe(1);
  });

  it('notifications are capped at 50', () => {
    const { addNotification } = useNotificationStore.getState();
    for (let i = 0; i < 55; i++) {
      addNotification({ type: 'message', message: `Notification ${i}` });
    }

    const state = useNotificationStore.getState();
    expect(state.notifications).toHaveLength(50);
  });
});
