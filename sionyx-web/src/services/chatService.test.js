import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ref, get, set, push, update, query, orderByChild, equalTo, onValue } from 'firebase/database';
import {
  sendMessage,
  getAllMessages,
  getMessagesForUser,
  getUnreadMessages,
  markMessageAsRead,
  listenToUserMessages,
  updateUserLastSeen,
  isUserActive,
} from './chatService';

vi.mock('firebase/database');
vi.mock('../config/firebase', () => ({
  database: {},
}));

describe('chatService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('sendMessage', () => {
    it('sends message successfully', async () => {
      push.mockReturnValue({ key: 'msg-123' });
      set.mockResolvedValue();

      const result = await sendMessage('my-org', 'user-123', 'Hello!', 'admin-456');

      expect(result.success).toBe(true);
      expect(result.messageId).toBe('msg-123');
      expect(result.message).toBeDefined();
    });

    it('trims message text', async () => {
      push.mockReturnValue({ key: 'msg-123' });
      set.mockResolvedValue();

      await sendMessage('my-org', 'user-123', '  Hello World!  ', 'admin-456');

      const setCall = set.mock.calls[0][1];
      expect(setCall.message).toBe('Hello World!');
    });

    it('includes all required fields', async () => {
      push.mockReturnValue({ key: 'msg-123' });
      set.mockResolvedValue();

      await sendMessage('my-org', 'user-123', 'Test', 'admin-456');

      const setCall = set.mock.calls[0][1];
      expect(setCall.id).toBe('msg-123');
      expect(setCall.fromAdminId).toBe('admin-456');
      expect(setCall.toUserId).toBe('user-123');
      expect(setCall.read).toBe(false);
      expect(setCall.timestamp).toBeDefined();
      expect(setCall.orgId).toBe('my-org');
    });

    it('handles database error', async () => {
      push.mockReturnValue({ key: 'msg-123' });
      set.mockRejectedValue(new Error('Write failed'));

      const result = await sendMessage('my-org', 'user-123', 'Test', 'admin-456');

      expect(result.success).toBe(false);
      expect(result.error).toBe('Write failed');
    });
  });

  describe('getAllMessages', () => {
    it('returns empty array if no messages exist', async () => {
      get.mockResolvedValue({
        exists: () => false,
      });

      const result = await getAllMessages('my-org');

      expect(result.success).toBe(true);
      expect(result.messages).toEqual([]);
    });

    it('returns messages sorted by timestamp (newest first)', async () => {
      get.mockResolvedValue({
        exists: () => true,
        val: () => ({
          'msg-1': { message: 'First', timestamp: '2024-01-01T10:00:00Z' },
          'msg-2': { message: 'Second', timestamp: '2024-06-01T10:00:00Z' },
        }),
      });

      const result = await getAllMessages('my-org');

      expect(result.success).toBe(true);
      expect(result.messages[0].message).toBe('Second'); // Newest
      expect(result.messages[1].message).toBe('First');
    });

    it('includes id in each message', async () => {
      get.mockResolvedValue({
        exists: () => true,
        val: () => ({
          'msg-123': { message: 'Test' },
        }),
      });

      const result = await getAllMessages('my-org');

      expect(result.messages[0].id).toBe('msg-123');
    });

    it('handles database error', async () => {
      get.mockRejectedValue(new Error('Database error'));

      const result = await getAllMessages('my-org');

      expect(result.success).toBe(false);
      expect(result.messages).toEqual([]);
    });
  });

  describe('getMessagesForUser', () => {
    it('returns empty array if no messages for user', async () => {
      get.mockResolvedValue({
        exists: () => false,
      });

      const result = await getMessagesForUser('my-org', 'user-123');

      expect(result.success).toBe(true);
      expect(result.messages).toEqual([]);
    });

    it('returns messages sorted by timestamp (newest first)', async () => {
      get.mockResolvedValue({
        exists: () => true,
        val: () => ({
          'msg-1': { message: 'Old', timestamp: '2024-01-01T10:00:00Z' },
          'msg-2': { message: 'New', timestamp: '2024-06-01T10:00:00Z' },
        }),
      });

      const result = await getMessagesForUser('my-org', 'user-123');

      expect(result.messages[0].message).toBe('New');
    });
  });

  describe('getUnreadMessages', () => {
    it('returns only unread messages', async () => {
      get.mockResolvedValue({
        exists: () => true,
        val: () => ({
          'msg-1': { message: 'Read', read: true, timestamp: '2024-01-01T10:00:00Z' },
          'msg-2': { message: 'Unread', read: false, timestamp: '2024-01-02T10:00:00Z' },
          'msg-3': { message: 'Also Unread', read: false, timestamp: '2024-01-03T10:00:00Z' },
        }),
      });

      const result = await getUnreadMessages('my-org', 'user-123');

      expect(result.success).toBe(true);
      expect(result.messages).toHaveLength(2);
      expect(result.messages.every(m => !m.read)).toBe(true);
    });

    it('returns messages sorted by timestamp (oldest first for display)', async () => {
      get.mockResolvedValue({
        exists: () => true,
        val: () => ({
          'msg-1': { message: 'New', read: false, timestamp: '2024-06-01T10:00:00Z' },
          'msg-2': { message: 'Old', read: false, timestamp: '2024-01-01T10:00:00Z' },
        }),
      });

      const result = await getUnreadMessages('my-org', 'user-123');

      expect(result.messages[0].message).toBe('Old'); // Oldest first
    });
  });

  describe('markMessageAsRead', () => {
    it('marks message as read successfully', async () => {
      update.mockResolvedValue();

      const result = await markMessageAsRead('my-org', 'msg-123');

      expect(result.success).toBe(true);
      const updateCall = update.mock.calls[0][1];
      expect(updateCall.read).toBe(true);
      expect(updateCall.readAt).toBeDefined();
    });

    it('handles database error', async () => {
      update.mockRejectedValue(new Error('Update failed'));

      const result = await markMessageAsRead('my-org', 'msg-123');

      expect(result.success).toBe(false);
    });
  });

  describe('listenToUserMessages', () => {
    it('sets up listener and returns unsubscribe function', () => {
      const mockUnsubscribe = vi.fn();
      onValue.mockReturnValue(mockUnsubscribe);

      const callback = vi.fn();
      const unsubscribe = listenToUserMessages('my-org', 'user-123', callback);

      expect(onValue).toHaveBeenCalled();
      expect(typeof unsubscribe).toBe('function');
    });

    it('calls callback with messages when data exists', () => {
      onValue.mockImplementation((queryRef, successCallback) => {
        successCallback({
          exists: () => true,
          val: () => ({
            'msg-1': { message: 'Test', timestamp: '2024-01-01T10:00:00Z' },
          }),
        });
        return vi.fn();
      });

      const callback = vi.fn();
      listenToUserMessages('my-org', 'user-123', callback);

      expect(callback).toHaveBeenCalledWith({
        success: true,
        messages: expect.arrayContaining([
          expect.objectContaining({ id: 'msg-1', message: 'Test' }),
        ]),
      });
    });

    it('calls callback with empty array when no data', () => {
      onValue.mockImplementation((queryRef, successCallback) => {
        successCallback({
          exists: () => false,
        });
        return vi.fn();
      });

      const callback = vi.fn();
      listenToUserMessages('my-org', 'user-123', callback);

      expect(callback).toHaveBeenCalledWith({
        success: true,
        messages: [],
      });
    });
  });

  describe('updateUserLastSeen', () => {
    it('updates last seen timestamp', async () => {
      update.mockResolvedValue();

      const result = await updateUserLastSeen('my-org', 'user-123');

      expect(result.success).toBe(true);
      const updateCall = update.mock.calls[0][1];
      expect(updateCall.lastSeen).toBeDefined();
    });

    it('handles database error', async () => {
      update.mockRejectedValue(new Error('Update failed'));

      const result = await updateUserLastSeen('my-org', 'user-123');

      expect(result.success).toBe(false);
    });
  });

  describe('isUserActive', () => {
    it('returns false for null lastSeen', () => {
      expect(isUserActive(null)).toBe(false);
    });

    it('returns false for undefined lastSeen', () => {
      expect(isUserActive(undefined)).toBe(false);
    });

    it('returns true if lastSeen within 5 minutes', () => {
      const recentTime = new Date(Date.now() - 2 * 60 * 1000).toISOString(); // 2 min ago
      expect(isUserActive(recentTime)).toBe(true);
    });

    it('returns false if lastSeen more than 5 minutes ago', () => {
      const oldTime = new Date(Date.now() - 10 * 60 * 1000).toISOString(); // 10 min ago
      expect(isUserActive(oldTime)).toBe(false);
    });

    it('returns true at exactly 5 minutes', () => {
      const fiveMinAgo = new Date(Date.now() - 5 * 60 * 1000).toISOString();
      expect(isUserActive(fiveMinAgo)).toBe(true);
    });
  });
});

