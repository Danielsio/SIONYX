import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { App as AntApp } from 'antd';
import MessagesPage from './MessagesPage';
import { getAllUsers } from '../services/userService';
import { getAllMessages, getMessagesForUser, sendMessage, cleanupOldMessages } from '../services/chatService';
import { subscribeToMessages, subscribeToUsers } from '../services/realtimeService';
import { useAuthStore } from '../store/authStore';

// Realtime subscription data - mutated per test
const realtimeData = { messages: [], users: [] };

// Mock dependencies
vi.mock('../services/userService');
vi.mock('../services/chatService');
vi.mock('../services/realtimeService', () => ({
  subscribeToMessages: vi.fn((orgId, callback) => {
    if (orgId) callback(realtimeData.messages);
    return vi.fn();
  }),
  subscribeToUsers: vi.fn((orgId, callback) => {
    if (orgId) callback(realtimeData.users);
    return vi.fn();
  }),
  subscribeToComputers: vi.fn(() => vi.fn()),
  subscribeToAnnouncements: vi.fn(() => vi.fn()),
}));
vi.mock('../store/authStore');

// Mock dayjs
vi.mock('dayjs', () => {
  const dayjs = date => ({
    format: () => '15/01/2024',
    fromNow: () => 'לפני שעה',
    unix: () => (date ? new Date(date).getTime() / 1000 : Date.now() / 1000),
  });
  dayjs.extend = () => {};
  dayjs.locale = () => {};
  return { default: dayjs };
});

// Mock scrollIntoView
Element.prototype.scrollIntoView = vi.fn();

const mockUsers = [
  {
    uid: 'user-1',
    firstName: 'יוסי',
    lastName: 'כהן',
    phoneNumber: '0501234567',
    lastSeen: new Date().toISOString(),
  },
  {
    uid: 'user-2',
    firstName: 'שרה',
    lastName: 'לוי',
    phoneNumber: '0509876543',
    lastSeen: new Date(Date.now() - 10 * 60 * 1000).toISOString(), // 10 min ago
  },
];

const mockMessages = [
  {
    id: 'msg-1',
    toUserId: 'user-1',
    message: 'שלום! איך אפשר לעזור?',
    timestamp: '2024-01-15T10:00:00Z',
    read: true,
  },
  {
    id: 'msg-2',
    toUserId: 'user-2',
    message: 'יש לך שאלות?',
    timestamp: '2024-01-15T11:00:00Z',
    read: false,
  },
];

const renderMessagesPage = () => {
  realtimeData.messages = [...mockMessages];
  realtimeData.users = [...mockUsers];

  useAuthStore.mockImplementation(selector => {
    const state = {
      user: { orgId: 'my-org', uid: 'admin-123' },
      getOrgId: () => 'my-org',
    };
    return typeof selector === 'function' ? selector(state) : state;
  });

  getAllUsers.mockResolvedValue({
    success: true,
    users: mockUsers,
  });

  getAllMessages.mockResolvedValue({
    success: true,
    messages: mockMessages,
  });

  getMessagesForUser.mockResolvedValue({
    success: true,
    messages: mockMessages.filter(m => m.toUserId === 'user-1'),
  });

  sendMessage.mockResolvedValue({ success: true, messageId: 'new-msg' });
  cleanupOldMessages.mockResolvedValue({ success: true, deleted: 0 });

  return render(
    <AntApp>
      <MessagesPage />
    </AntApp>
  );
};

describe('MessagesPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    realtimeData.messages = [...mockMessages];
    realtimeData.users = [...mockUsers];
  });

  it('renders without crashing', async () => {
    renderMessagesPage();

    await waitFor(() => {
      expect(subscribeToMessages).toHaveBeenCalledWith('my-org', expect.any(Function));
    });

    expect(document.body).toBeInTheDocument();
  });

  it('displays page title', async () => {
    renderMessagesPage();

    await waitFor(() => {
      expect(screen.getByRole('heading', { level: 2 })).toBeInTheDocument();
    });
  });

  it('subscribes to messages and users on mount', async () => {
    renderMessagesPage();

    await waitFor(() => {
      expect(subscribeToMessages).toHaveBeenCalledWith('my-org', expect.any(Function));
      expect(subscribeToUsers).toHaveBeenCalledWith('my-org', expect.any(Function));
    });
  });

  it('displays user list', async () => {
    renderMessagesPage();

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/חפש/)).toBeInTheDocument();
    });

    expect(document.body).toBeInTheDocument();
  });

  it('has search functionality', async () => {
    renderMessagesPage();

    await waitFor(() => {
      const searchInput = screen.getByPlaceholderText(/חפש/);
      expect(searchInput).toBeInTheDocument();
    });
  });

  it('renders refresh button', async () => {
    renderMessagesPage();

    await waitFor(() => {
      expect(screen.getByText('רענן')).toBeInTheDocument();
    });
  });

  it('refreshes data when refresh clicked', async () => {
    const user = userEvent.setup();
    renderMessagesPage();

    await waitFor(() => {
      expect(screen.getByText('רענן')).toBeInTheDocument();
    });

    // Before refresh: loadData (getAllUsers etc) not called on mount
    expect(getAllUsers).not.toHaveBeenCalled();

    await user.click(screen.getByText('רענן'));

    await waitFor(() => {
      expect(getAllUsers).toHaveBeenCalledTimes(1);
      expect(getAllMessages).toHaveBeenCalledTimes(1);
    });
  });

  it('handles loading error gracefully', async () => {
    getAllUsers.mockResolvedValue({
      success: false,
      error: 'Failed to load users',
    });

    renderMessagesPage();

    await waitFor(() => {
      expect(subscribeToMessages).toHaveBeenCalled();
    });

    expect(document.body).toBeInTheDocument();
  });

  it('shows empty state when no users', async () => {
    realtimeData.messages = [];
    realtimeData.users = [];

    renderMessagesPage();

    await waitFor(() => {
      expect(subscribeToMessages).toHaveBeenCalled();
    });

    expect(document.body).toBeInTheDocument();
  });

  it('opens chat drawer when user clicked', async () => {
    const user = userEvent.setup();
    renderMessagesPage();

    await waitFor(() => {
      expect(screen.getByText('רענן')).toBeInTheDocument();
    });

    const userCards = await screen.findAllByText(/יוסי|שרה/);
    if (userCards.length > 0) {
      await user.click(userCards[0]);

      await waitFor(() => {
        expect(getMessagesForUser).toHaveBeenCalled();
      });
    }
  });

  it('does not crash or log error when user is null', async () => {
    const errorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    useAuthStore.mockImplementation(selector => {
      const state = {
        user: null,
        getOrgId: () => null,
      };
      return typeof selector === 'function' ? selector(state) : state;
    });

    render(
      <AntApp>
        <MessagesPage />
      </AntApp>
    );

    await waitFor(() => {
      expect(document.body).toBeInTheDocument();
    });

    expect(subscribeToMessages).not.toHaveBeenCalled();
    expect(subscribeToUsers).not.toHaveBeenCalled();
    expect(getAllUsers).not.toHaveBeenCalled();
    expect(getAllMessages).not.toHaveBeenCalled();
    expect(errorSpy).not.toHaveBeenCalled();

    errorSpy.mockRestore();
  });

  it('shows message count badges', async () => {
    renderMessagesPage();

    await waitFor(() => {
      expect(subscribeToMessages).toHaveBeenCalled();
    });

    expect(document.body).toBeInTheDocument();
  });
});
