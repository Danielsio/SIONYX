import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ref, onValue } from 'firebase/database';
import {
  subscribeToUsers,
  subscribeToMessages,
  subscribeToComputers,
  subscribeToAnnouncements,
} from './realtimeService';

vi.mock('firebase/database');
vi.mock('../config/firebase', () => ({ database: {} }));
vi.mock('../store/notificationStore', () => ({
  useNotificationStore: {
    getState: () => ({ addNotification: vi.fn() }),
  },
}));

describe('realtimeService', () => {
  let mockUnsubscribe;
  let onValueCallback;

  beforeEach(() => {
    vi.clearAllMocks();
    mockUnsubscribe = vi.fn();
    onValue.mockImplementation((refArg, callback, _errorCallback) => {
      onValueCallback = callback;
      return mockUnsubscribe;
    });
  });

  describe('subscribeToUsers', () => {
    it('calls onValue and returns unsubscribe', () => {
      const callback = vi.fn();
      const unsub = subscribeToUsers('org-1', callback);

      expect(ref).toHaveBeenCalledWith({}, 'organizations/org-1/users');
      expect(onValue).toHaveBeenCalled();
      expect(typeof unsub).toBe('function');

      unsub();
      expect(mockUnsubscribe).toHaveBeenCalled();
    });

    it('returns no-op when orgId is empty', () => {
      const callback = vi.fn();
      const unsub = subscribeToUsers('', callback);
      unsub();
      expect(onValue).not.toHaveBeenCalled();
    });

    it('calls callback with parsed user list when snapshot exists', () => {
      const callback = vi.fn();
      subscribeToUsers('org-1', callback);

      const snapshot = {
        exists: () => true,
        val: () => ({
          uid1: { firstName: 'John', lastName: 'Doe' },
          uid2: { firstName: 'Jane', lastName: 'Smith' },
        }),
      };
      onValueCallback(snapshot);

      expect(callback).toHaveBeenCalledWith([
        { uid: 'uid1', firstName: 'John', lastName: 'Doe' },
        { uid: 'uid2', firstName: 'Jane', lastName: 'Smith' },
      ]);
    });

    it('calls callback with empty array when snapshot does not exist', () => {
      const callback = vi.fn();
      subscribeToUsers('org-1', callback);

      const snapshot = { exists: () => false };
      onValueCallback(snapshot);

      expect(callback).toHaveBeenCalledWith([]);
    });
  });

  describe('subscribeToMessages', () => {
    it('calls onValue and returns unsubscribe', () => {
      const callback = vi.fn();
      const unsub = subscribeToMessages('org-1', callback);

      expect(ref).toHaveBeenCalledWith({}, 'organizations/org-1/messages');
      expect(onValue).toHaveBeenCalled();
      unsub();
      expect(mockUnsubscribe).toHaveBeenCalled();
    });

    it('returns no-op when orgId is empty', () => {
      const unsub = subscribeToMessages('', vi.fn());
      unsub();
      expect(onValue).not.toHaveBeenCalled();
    });

    it('calls callback with parsed message list when snapshot exists', () => {
      const callback = vi.fn();
      subscribeToMessages('org-1', callback);

      const snapshot = {
        exists: () => true,
        val: () => ({
          msg1: { text: 'Hello', from: 'user1' },
          msg2: { text: 'Hi', from: 'user2' },
        }),
      };
      onValueCallback(snapshot);

      expect(callback).toHaveBeenCalledWith([
        { id: 'msg1', text: 'Hello', from: 'user1' },
        { id: 'msg2', text: 'Hi', from: 'user2' },
      ]);
    });

    it('calls callback with empty array when snapshot does not exist', () => {
      const callback = vi.fn();
      subscribeToMessages('org-1', callback);

      const snapshot = { exists: () => false };
      onValueCallback(snapshot);

      expect(callback).toHaveBeenCalledWith([]);
    });
  });

  describe('subscribeToComputers', () => {
    it('calls onValue and returns unsubscribe', () => {
      const callback = vi.fn();
      const unsub = subscribeToComputers('org-1', callback);

      expect(ref).toHaveBeenCalledWith({}, 'organizations/org-1/computers');
      expect(onValue).toHaveBeenCalled();
      unsub();
      expect(mockUnsubscribe).toHaveBeenCalled();
    });

    it('returns no-op when orgId is empty', () => {
      const unsub = subscribeToComputers('', vi.fn());
      unsub();
      expect(onValue).not.toHaveBeenCalled();
    });

    it('calls callback with parsed computer list when snapshot exists', () => {
      const callback = vi.fn();
      subscribeToComputers('org-1', callback);

      const snapshot = {
        exists: () => true,
        val: () => ({
          comp1: { name: 'PC1', status: 'active' },
          comp2: { name: 'PC2', status: 'idle' },
        }),
      };
      onValueCallback(snapshot);

      expect(callback).toHaveBeenCalledWith([
        { id: 'comp1', name: 'PC1', status: 'active' },
        { id: 'comp2', name: 'PC2', status: 'idle' },
      ]);
    });

    it('calls callback with empty array when snapshot does not exist', () => {
      const callback = vi.fn();
      subscribeToComputers('org-1', callback);

      const snapshot = { exists: () => false };
      onValueCallback(snapshot);

      expect(callback).toHaveBeenCalledWith([]);
    });
  });

  describe('subscribeToAnnouncements', () => {
    it('calls onValue and returns unsubscribe', () => {
      const callback = vi.fn();
      const unsub = subscribeToAnnouncements('org-1', callback);

      expect(ref).toHaveBeenCalledWith({}, 'organizations/org-1/announcements');
      expect(onValue).toHaveBeenCalled();
      unsub();
      expect(mockUnsubscribe).toHaveBeenCalled();
    });

    it('returns no-op when orgId is empty', () => {
      const unsub = subscribeToAnnouncements('', vi.fn());
      unsub();
      expect(onValue).not.toHaveBeenCalled();
    });

    it('calls callback with parsed announcement list when snapshot exists', () => {
      const callback = vi.fn();
      subscribeToAnnouncements('org-1', callback);

      const snapshot = {
        exists: () => true,
        val: () => ({
          ann1: { title: 'Announcement 1', body: 'Body 1' },
          ann2: { title: 'Announcement 2', body: 'Body 2' },
        }),
      };
      onValueCallback(snapshot);

      expect(callback).toHaveBeenCalledWith([
        { id: 'ann1', title: 'Announcement 1', body: 'Body 1' },
        { id: 'ann2', title: 'Announcement 2', body: 'Body 2' },
      ]);
    });

    it('calls callback with empty array when snapshot does not exist', () => {
      const callback = vi.fn();
      subscribeToAnnouncements('org-1', callback);

      const snapshot = { exists: () => false };
      onValueCallback(snapshot);

      expect(callback).toHaveBeenCalledWith([]);
    });
  });
});
