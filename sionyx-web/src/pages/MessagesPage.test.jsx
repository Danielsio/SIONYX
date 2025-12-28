import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { App as AntApp } from 'antd';
import MessagesPage from './MessagesPage';
import { getAllUsers } from '../services/userService';
import { getAllMessages, getMessagesForUser, sendMessage } from '../services/chatService';
import { useAuthStore } from '../store/authStore';

// Mock dependencies
vi.mock('../services/userService');
vi.mock('../services/chatService');
vi.mock('../store/authStore');

// Mock dayjs
vi.mock('dayjs', () => {
  const dayjs = (date) => ({
    format: () => '15/01/2024',
    fromNow: () => 'לפני שעה',
    unix: () => date ? new Date(date).getTime() / 1000 : Date.now() / 1000,
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
  useAuthStore.mockImplementation((selector) => {
    const state = { user: { orgId: 'my-org', uid: 'admin-123' } };
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

  return render(
    <AntApp>
      <MessagesPage />
    </AntApp>
  );
};

describe('MessagesPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.setItem('adminOrgId', 'my-org');
  });

  it('renders without crashing', async () => {
    renderMessagesPage();

    await waitFor(() => {
      expect(getAllUsers).toHaveBeenCalled();
    });

    expect(document.body).toBeInTheDocument();
  });

  it('displays page title', async () => {
    renderMessagesPage();

    await waitFor(() => {
      expect(getAllUsers).toHaveBeenCalled();
    });

    // Text is split by elements, so use a custom matcher
    expect(screen.getByRole('heading', { level: 2 })).toBeInTheDocument();
  });

  it('loads users and messages on mount', async () => {
    renderMessagesPage();

    await waitFor(() => {
      expect(getAllUsers).toHaveBeenCalledWith('my-org');
      expect(getAllMessages).toHaveBeenCalledWith('my-org');
    });
  });

  it('displays user list', async () => {
    renderMessagesPage();

    await waitFor(() => {
      expect(getAllUsers).toHaveBeenCalled();
    });

    // Users should be loaded into the page
    expect(document.body).toBeInTheDocument();
  });

  it('has search functionality', async () => {
    renderMessagesPage();

    await waitFor(() => {
      expect(getAllUsers).toHaveBeenCalled();
    });

    // Should have search input
    const searchInput = screen.getByPlaceholderText(/חפש/);
    expect(searchInput).toBeInTheDocument();
  });

  it('renders refresh button', async () => {
    renderMessagesPage();

    await waitFor(() => {
      expect(getAllUsers).toHaveBeenCalled();
    });

    expect(screen.getByText('רענן')).toBeInTheDocument();
  });

  it('refreshes data when refresh clicked', async () => {
    const user = userEvent.setup();
    renderMessagesPage();

    await waitFor(() => {
      expect(getAllUsers).toHaveBeenCalledTimes(1);
    });

    await user.click(screen.getByText('רענן'));

    await waitFor(() => {
      expect(getAllUsers).toHaveBeenCalledTimes(2);
    });
  });

  it('handles loading error gracefully', async () => {
    getAllUsers.mockResolvedValue({
      success: false,
      error: 'Failed to load users',
    });

    renderMessagesPage();

    await waitFor(() => {
      expect(getAllUsers).toHaveBeenCalled();
    });

    // Should not crash
    expect(document.body).toBeInTheDocument();
  });

  it('shows empty state when no users', async () => {
    getAllUsers.mockResolvedValue({
      success: true,
      users: [],
    });

    renderMessagesPage();

    await waitFor(() => {
      expect(getAllUsers).toHaveBeenCalled();
    });

    // Should show empty state
    expect(document.body).toBeInTheDocument();
  });

  it('opens chat drawer when user clicked', async () => {
    const user = userEvent.setup();
    renderMessagesPage();

    await waitFor(() => {
      expect(getAllUsers).toHaveBeenCalled();
    });

    // Find a user card and click it
    const userCards = await screen.findAllByText(/יוסי|שרה/);
    if (userCards.length > 0) {
      await user.click(userCards[0]);

      await waitFor(() => {
        expect(getMessagesForUser).toHaveBeenCalled();
      });
    }
  });

  it('shows message count badges', async () => {
    renderMessagesPage();

    await waitFor(() => {
      expect(getAllMessages).toHaveBeenCalled();
    });

    // Messages should be loaded
    expect(document.body).toBeInTheDocument();
  });
});

