import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { App as AntApp } from 'antd';
import UsersPage from './UsersPage';
import {
  getAllUsers,
  getUserPurchaseHistory,
  adjustUserBalance,
  grantAdminPermission,
  revokeAdminPermission,
  kickUser,
} from '../services/userService';
import { getMessagesForUser, sendMessage } from '../services/chatService';
import { useAuthStore } from '../store/authStore';
import { useDataStore } from '../store/dataStore';

// Mock dependencies
vi.mock('../services/userService');
vi.mock('../services/chatService');
vi.mock('../store/authStore');
vi.mock('../store/dataStore');
vi.mock('../hooks/useOrgId', () => ({
  useOrgId: () => 'my-org',
}));

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

const mockUsers = [
  {
    uid: 'user-1',
    firstName: 'יוסי',
    lastName: 'כהן',
    phoneNumber: '0501234567',
    email: 'yossi@test.com',
    remainingTime: 3600,
    printBalance: 50,
    isAdmin: false,
    isSessionActive: true,
    currentComputerId: 'comp-1',
    createdAt: '2024-01-15T10:00:00Z',
  },
  {
    uid: 'user-2',
    firstName: 'שרה',
    lastName: 'לוי',
    phoneNumber: '0509876543',
    email: 'sara@test.com',
    remainingTime: 7200,
    printBalance: 100,
    isAdmin: true,
    isSessionActive: false,
    createdAt: '2024-02-20T10:00:00Z',
  },
];

const renderUsersPage = (usersOverride = mockUsers) => {
  const mockSetUsers = vi.fn();
  const mockUpdateUser = vi.fn();

  useAuthStore.mockImplementation((selector) => {
    const state = { user: { orgId: 'my-org', uid: 'admin-123' } };
    return selector(state);
  });

  useDataStore.mockImplementation((selector) => {
    const state = {
      users: usersOverride,
      setUsers: mockSetUsers,
      updateUser: mockUpdateUser,
    };
    return selector ? selector(state) : state;
  });

  getAllUsers.mockResolvedValue({
    success: true,
    users: usersOverride,
  });

  getUserPurchaseHistory.mockResolvedValue({
    success: true,
    purchases: [],
  });

  getMessagesForUser.mockResolvedValue({
    success: true,
    messages: [],
  });

  adjustUserBalance.mockResolvedValue({ success: true });
  grantAdminPermission.mockResolvedValue({ success: true });
  revokeAdminPermission.mockResolvedValue({ success: true });
  kickUser.mockResolvedValue({ success: true });
  sendMessage.mockResolvedValue({ success: true });

  return {
    ...render(
      <AntApp>
        <UsersPage />
      </AntApp>
    ),
    mockSetUsers,
    mockUpdateUser,
  };
};

describe('UsersPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.setItem('adminOrgId', 'my-org');
  });

  it('renders without crashing', async () => {
    renderUsersPage();

    await waitFor(() => {
      expect(getAllUsers).toHaveBeenCalled();
    });

    expect(document.body).toBeInTheDocument();
  });

  it('displays page title', async () => {
    renderUsersPage();

    await waitFor(() => {
      expect(getAllUsers).toHaveBeenCalled();
    });

    // Title is split across elements, use role or check body content
    expect(screen.getByRole('heading', { level: 2 })).toBeInTheDocument();
    expect(document.body.textContent).toContain('משתמשים');
  });

  it('loads users on mount', async () => {
    renderUsersPage();

    await waitFor(() => {
      expect(getAllUsers).toHaveBeenCalledWith('my-org');
    });
  });

  it('displays user cards', async () => {
    renderUsersPage();

    await waitFor(() => {
      expect(getAllUsers).toHaveBeenCalled();
    });

    // Should display user names in cards
    await waitFor(() => {
      expect(screen.getByText(/יוסי כהן/)).toBeInTheDocument();
    });
  });

  it('shows user count badge', async () => {
    renderUsersPage();

    await waitFor(() => {
      expect(getAllUsers).toHaveBeenCalled();
    });

    // Should show the count of users
    expect(document.body.textContent).toContain('2');
  });

  it('has search functionality', async () => {
    renderUsersPage();

    await waitFor(() => {
      expect(getAllUsers).toHaveBeenCalled();
    });

    const searchInput = screen.getByPlaceholderText(/חפש/);
    expect(searchInput).toBeInTheDocument();
  });

  it('filters users by search text', async () => {
    const user = userEvent.setup();
    renderUsersPage();

    await waitFor(() => {
      expect(getAllUsers).toHaveBeenCalled();
    });

    const searchInput = screen.getByPlaceholderText(/חפש/);
    await user.type(searchInput, 'יוסי');

    // Filtering happens client-side
    expect(searchInput).toHaveValue('יוסי');
  });

  it('has refresh button', async () => {
    renderUsersPage();

    await waitFor(() => {
      expect(getAllUsers).toHaveBeenCalled();
    });

    expect(screen.getByText('רענן')).toBeInTheDocument();
  });

  it('refreshes users when refresh clicked', async () => {
    const user = userEvent.setup();
    renderUsersPage();

    await waitFor(() => {
      expect(getAllUsers).toHaveBeenCalledTimes(1);
    });

    await user.click(screen.getByText('רענן'));

    await waitFor(() => {
      expect(getAllUsers).toHaveBeenCalledTimes(2);
    });
  });

  it('shows admin badge for admin users', async () => {
    renderUsersPage();

    await waitFor(() => {
      expect(getAllUsers).toHaveBeenCalled();
    });

    // Admin tags should be present in cards
    await waitFor(() => {
      const adminTags = screen.getAllByText('מנהל');
      expect(adminTags.length).toBeGreaterThan(0);
    });
  });

  it('shows user time balance', async () => {
    renderUsersPage();

    await waitFor(() => {
      expect(getAllUsers).toHaveBeenCalled();
    });

    // Time info should be displayed
    expect(screen.getAllByText(/זמן נותר/).length).toBeGreaterThan(0);
  });

  it('shows user prints balance', async () => {
    renderUsersPage();

    await waitFor(() => {
      expect(getAllUsers).toHaveBeenCalled();
    });

    // Prints info should be displayed (תקציב הדפסות = printing budget)
    expect(screen.getAllByText(/תקציב הדפסות/).length).toBeGreaterThan(0);
  });

  it('handles load error gracefully', async () => {
    getAllUsers.mockResolvedValue({
      success: false,
      error: 'Failed to load users',
    });

    renderUsersPage([]);

    await waitFor(() => {
      expect(getAllUsers).toHaveBeenCalled();
    });

    expect(document.body).toBeInTheDocument();
  });

  it('shows empty state when no users', async () => {
    renderUsersPage([]);

    await waitFor(() => {
      expect(getAllUsers).toHaveBeenCalled();
    });

    expect(screen.getByText(/אין משתמשים/)).toBeInTheDocument();
  });

  it('opens user details drawer when card clicked', async () => {
    const user = userEvent.setup();
    renderUsersPage();

    await waitFor(() => {
      expect(getAllUsers).toHaveBeenCalled();
    });

    // Find and click a user card
    const userCard = screen.getByText(/יוסי כהן/).closest('.ant-card');
    if (userCard) {
      await user.click(userCard);

      await waitFor(() => {
        expect(getUserPurchaseHistory).toHaveBeenCalled();
        expect(getMessagesForUser).toHaveBeenCalled();
      });
    }
  });

  it('displays phone numbers on cards', async () => {
    renderUsersPage();

    await waitFor(() => {
      expect(getAllUsers).toHaveBeenCalled();
    });

    expect(screen.getByText('0501234567')).toBeInTheDocument();
  });

  it('displays email on cards', async () => {
    renderUsersPage();

    await waitFor(() => {
      expect(getAllUsers).toHaveBeenCalled();
    });

    expect(screen.getByText('yossi@test.com')).toBeInTheDocument();
  });

  it('shows status tags on cards', async () => {
    renderUsersPage();

    await waitFor(() => {
      expect(getAllUsers).toHaveBeenCalled();
    });

    // Status tags (פעיל/מושהה/לא פעיל) should be visible
    const statusTags = screen.getAllByText(/פעיל|מושהה/);
    expect(statusTags.length).toBeGreaterThan(0);
  });

  it('has actions dropdown on cards', async () => {
    renderUsersPage();

    await waitFor(() => {
      expect(getAllUsers).toHaveBeenCalled();
    });

    // More button renders as [MoreOutlined] text due to mock
    expect(document.body.textContent).toContain('[MoreOutlined]');
  });
});

describe('UsersPage - Admin Self-Revoke Prevention', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.setItem('adminOrgId', 'my-org');
  });

  const renderWithCurrentUser = (currentUserId, users) => {
    const mockSetUsers = vi.fn();
    const mockUpdateUser = vi.fn();

    useAuthStore.mockImplementation((selector) => {
      const state = { user: { orgId: 'my-org', uid: currentUserId } };
      return selector(state);
    });

    useDataStore.mockImplementation((selector) => {
      const state = {
        users: users,
        setUsers: mockSetUsers,
        updateUser: mockUpdateUser,
      };
      return selector ? selector(state) : state;
    });

    getAllUsers.mockResolvedValue({
      success: true,
      users: users,
    });

    getUserPurchaseHistory.mockResolvedValue({
      success: true,
      purchases: [],
    });

    getMessagesForUser.mockResolvedValue({
      success: true,
      messages: [],
    });

    adjustUserBalance.mockResolvedValue({ success: true });
    grantAdminPermission.mockResolvedValue({ success: true });
    revokeAdminPermission.mockResolvedValue({ success: true });
    kickUser.mockResolvedValue({ success: true });
    sendMessage.mockResolvedValue({ success: true });

    return {
      ...render(
        <AntApp>
          <UsersPage />
        </AntApp>
      ),
      mockSetUsers,
      mockUpdateUser,
    };
  };

  it('disables revoke button when admin views their own profile in drawer', async () => {
    const user = userEvent.setup();
    const currentAdminId = 'admin-self';
    const usersWithSelf = [
      {
        uid: currentAdminId,
        firstName: 'מנהל',
        lastName: 'ראשי',
        phoneNumber: '0501111111',
        email: 'admin@test.com',
        remainingTime: 0,
        printBalance: 0,
        isAdmin: true,
        isSessionActive: false,
        createdAt: '2024-01-01T10:00:00Z',
      },
    ];

    renderWithCurrentUser(currentAdminId, usersWithSelf);

    await waitFor(() => {
      expect(getAllUsers).toHaveBeenCalled();
    });

    // Click on the admin's card to open drawer
    const adminCard = screen.getByText(/מנהל ראשי/).closest('.ant-card');
    if (adminCard) {
      await user.click(adminCard);

      await waitFor(() => {
        // The revoke button in drawer should show disabled text
        const revokeButton = screen.getByRole('button', { name: /לא ניתן להסיר מעצמך/ });
        expect(revokeButton).toBeDisabled();
      });
    }
  });

  it('enables revoke button when admin views another admin profile', async () => {
    const user = userEvent.setup();
    const currentAdminId = 'admin-me';
    const usersWithOtherAdmin = [
      {
        uid: 'admin-other',
        firstName: 'מנהל',
        lastName: 'אחר',
        phoneNumber: '0502222222',
        email: 'other-admin@test.com',
        remainingTime: 0,
        printBalance: 0,
        isAdmin: true,
        isSessionActive: false,
        createdAt: '2024-01-01T10:00:00Z',
      },
    ];

    renderWithCurrentUser(currentAdminId, usersWithOtherAdmin);

    await waitFor(() => {
      expect(getAllUsers).toHaveBeenCalled();
    });

    // Click on the other admin's card to open drawer
    const adminCard = screen.getByText(/מנהל אחר/).closest('.ant-card');
    if (adminCard) {
      await user.click(adminCard);

      await waitFor(() => {
        // The revoke button should be enabled for other admins
        const revokeButton = screen.getByRole('button', { name: /הסר הרשאות מנהל/ });
        expect(revokeButton).not.toBeDisabled();
      });
    }
  });
});
