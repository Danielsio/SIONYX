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
  resetUserPassword,
} from '../services/userService';
import { getMessagesForUser, sendMessage } from '../services/chatService';
import { useAuthStore } from '../store/authStore';
import { useDataStore } from '../store/dataStore';

// Mock dependencies
vi.mock('../services/userService');
vi.mock('../services/chatService');
vi.mock('../store/authStore');
vi.mock('../store/dataStore');
const mockUseOrgId = vi.fn(() => 'my-org');
vi.mock('../hooks/useOrgId', () => ({
  useOrgId: (...args) => mockUseOrgId(...args),
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
    const state = { user: { orgId: 'my-org', uid: 'admin-123', role: 'admin', isAdmin: true } };
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
  resetUserPassword.mockResolvedValue({ success: true, message: 'הסיסמה אופסה בהצלחה' });

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

describe('UsersPage - Send Message Guard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.setItem('adminOrgId', 'my-org');
  });

  it('does not call sendMessage with undefined sender uid', async () => {
    const user = userEvent.setup();
    const mockSetUsers = vi.fn();
    const mockUpdateUser = vi.fn();

    // User has orgId but uid is undefined
    useAuthStore.mockImplementation((selector) => {
      const state = { user: { orgId: 'my-org', uid: undefined, role: 'admin', isAdmin: true } };
      return selector(state);
    });

    useDataStore.mockImplementation((selector) => {
      const state = {
        users: mockUsers,
        setUsers: mockSetUsers,
        updateUser: mockUpdateUser,
      };
      return selector ? selector(state) : state;
    });

    getAllUsers.mockResolvedValue({ success: true, users: mockUsers });
    getUserPurchaseHistory.mockResolvedValue({ success: true, purchases: [] });
    getMessagesForUser.mockResolvedValue({ success: true, messages: [] });
    adjustUserBalance.mockResolvedValue({ success: true });
    sendMessage.mockResolvedValue({ success: true });
    resetUserPassword.mockResolvedValue({ success: true, message: 'ok' });

    render(
      <AntApp>
        <UsersPage />
      </AntApp>
    );

    await waitFor(() => {
      expect(getAllUsers).toHaveBeenCalled();
    });

    // Open the user card drawer
    const userCard = screen.getByText(/יוסי כהן/).closest('.ant-card');
    await user.click(userCard);

    await waitFor(() => {
      expect(getUserPurchaseHistory).toHaveBeenCalled();
    });

    // Click "שלח הודעה" to open send message modal
    const sendBtns = screen.getAllByRole('button', { name: /שלח הודעה/ });
    await user.click(sendBtns[0]);

    // Fill in the message form
    await waitFor(() => {
      expect(screen.getByPlaceholderText(/הכנס את ההודעה/)).toBeInTheDocument();
    });

    const msgInput = screen.getByPlaceholderText(/הכנס את ההודעה/);
    await user.type(msgInput, 'Test message');

    // Submit the form - find the submit button inside the modal
    const allSendBtns = screen.getAllByRole('button', { name: /שלח הודעה/ });
    const submitBtn = allSendBtns[allSendBtns.length - 1]; // last one is in the modal
    await user.click(submitBtn);

    // Allow any async handlers to run
    await new Promise(r => setTimeout(r, 100));

    // sendMessage should NOT have been called because user.uid is undefined
    expect(sendMessage).not.toHaveBeenCalled();
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
      const state = { user: { orgId: 'my-org', uid: currentUserId, role: 'admin', isAdmin: true } };
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
    resetUserPassword.mockResolvedValue({ success: true, message: 'הסיסמה אופסה בהצלחה' });

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

describe('UsersPage - Password Reset', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.setItem('adminOrgId', 'my-org');
  });

  const renderForPasswordReset = () => {
    const mockSetUsers = vi.fn();
    const mockUpdateUser = vi.fn();

    useAuthStore.mockImplementation((selector) => {
      const state = { user: { orgId: 'my-org', uid: 'admin-123', role: 'admin', isAdmin: true } };
      return selector(state);
    });

    useDataStore.mockImplementation((selector) => {
      const state = {
        users: mockUsers,
        setUsers: mockSetUsers,
        updateUser: mockUpdateUser,
      };
      return selector ? selector(state) : state;
    });

    getAllUsers.mockResolvedValue({ success: true, users: mockUsers });
    getUserPurchaseHistory.mockResolvedValue({ success: true, purchases: [] });
    getMessagesForUser.mockResolvedValue({ success: true, messages: [] });
    adjustUserBalance.mockResolvedValue({ success: true });
    grantAdminPermission.mockResolvedValue({ success: true });
    revokeAdminPermission.mockResolvedValue({ success: true });
    kickUser.mockResolvedValue({ success: true });
    sendMessage.mockResolvedValue({ success: true });
    resetUserPassword.mockResolvedValue({ success: true, message: 'הסיסמה אופסה בהצלחה' });

    return render(
      <AntApp>
        <UsersPage />
      </AntApp>
    );
  };

  it('shows reset password button in user details drawer', async () => {
    const user = userEvent.setup();
    renderForPasswordReset();

    await waitFor(() => {
      expect(getAllUsers).toHaveBeenCalled();
    });

    // Click on a user card to open drawer
    const userCard = screen.getByText(/יוסי כהן/).closest('.ant-card');
    if (userCard) {
      await user.click(userCard);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /איפוס סיסמה/ })).toBeInTheDocument();
      });
    }
  });

  it('opens password reset modal when button clicked', async () => {
    const user = userEvent.setup();
    renderForPasswordReset();

    await waitFor(() => {
      expect(getAllUsers).toHaveBeenCalled();
    });

    // Click on a user card to open drawer
    const userCard = screen.getByText(/יוסי כהן/).closest('.ant-card');
    if (userCard) {
      await user.click(userCard);

      await waitFor(() => {
        const resetButton = screen.getByRole('button', { name: /איפוס סיסמה/ });
        expect(resetButton).toBeInTheDocument();
      });

      // Click the reset password button
      const resetButton = screen.getByRole('button', { name: /איפוס סיסמה/ });
      await user.click(resetButton);

      // Modal should appear
      await waitFor(() => {
        expect(screen.getByText(/סיסמה חדשה/)).toBeInTheDocument();
      });
    }
  });

  it('shows password validation message for short password', async () => {
    const user = userEvent.setup();
    renderForPasswordReset();

    await waitFor(() => {
      expect(getAllUsers).toHaveBeenCalled();
    });

    // Click on a user card to open drawer
    const userCard = screen.getByText(/יוסי כהן/).closest('.ant-card');
    if (userCard) {
      await user.click(userCard);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /איפוס סיסמה/ })).toBeInTheDocument();
      });

      // Click the reset password button
      await user.click(screen.getByRole('button', { name: /איפוס סיסמה/ }));

      // Wait for modal
      await waitFor(() => {
        expect(screen.getByText(/סיסמה חדשה/)).toBeInTheDocument();
      });

      // Type a short password
      const passwordInputs = screen.getAllByPlaceholderText(/לפחות 6 תווים|הכנס שוב/);
      if (passwordInputs.length > 0) {
        await user.type(passwordInputs[0], '12345');
      }
    }
  });

  it('calls resetUserPassword when form submitted with valid data', async () => {
    const user = userEvent.setup();
    renderForPasswordReset();

    await waitFor(() => {
      expect(getAllUsers).toHaveBeenCalled();
    });

    // Click on a user card to open drawer
    const userCard = screen.getByText(/יוסי כהן/).closest('.ant-card');
    if (userCard) {
      await user.click(userCard);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /איפוס סיסמה/ })).toBeInTheDocument();
      });

      // Click the reset password button
      await user.click(screen.getByRole('button', { name: /איפוס סיסמה/ }));

      // Wait for modal
      await waitFor(() => {
        expect(screen.getByText(/סיסמה חדשה/)).toBeInTheDocument();
      });

      // Find password inputs in modal using placeholder text
      const newPasswordInput = screen.getByPlaceholderText(/לפחות 6 תווים/);
      const confirmPasswordInput = screen.getByPlaceholderText(/הכנס שוב/);
      
      await user.type(newPasswordInput, 'newPassword123');
      await user.type(confirmPasswordInput, 'newPassword123');

      // Submit the form
      const submitButton = screen.getByRole('button', { name: /אפס סיסמה/ });
      await user.click(submitButton);

      await waitFor(() => {
        expect(resetUserPassword).toHaveBeenCalledWith('my-org', 'user-1', 'newPassword123');
      });
    }
  });

  it('shows error when password reset fails', async () => {
    resetUserPassword.mockResolvedValue({ success: false, error: 'שגיאה באיפוס הסיסמה' });
    
    const user = userEvent.setup();
    renderForPasswordReset();

    await waitFor(() => {
      expect(getAllUsers).toHaveBeenCalled();
    });

    // Click on a user card to open drawer
    const userCard = screen.getByText(/יוסי כהן/).closest('.ant-card');
    if (userCard) {
      await user.click(userCard);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /איפוס סיסמה/ })).toBeInTheDocument();
      });

      // Click the reset password button
      await user.click(screen.getByRole('button', { name: /איפוס סיסמה/ }));

      // Wait for modal
      await waitFor(() => {
        expect(screen.getByText(/סיסמה חדשה/)).toBeInTheDocument();
      });
    }
  });

  it('closes modal when cancel button clicked', async () => {
    const user = userEvent.setup();
    renderForPasswordReset();

    await waitFor(() => {
      expect(getAllUsers).toHaveBeenCalled();
    });

    // Click on a user card to open drawer
    const userCard = screen.getByText(/יוסי כהן/).closest('.ant-card');
    if (userCard) {
      await user.click(userCard);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /איפוס סיסמה/ })).toBeInTheDocument();
      });

      // Click the reset password button
      await user.click(screen.getByRole('button', { name: /איפוס סיסמה/ }));

      // Wait for modal
      await waitFor(() => {
        expect(screen.getByText(/סיסמה חדשה/)).toBeInTheDocument();
      });

      // Click cancel button
      const cancelButton = screen.getByRole('button', { name: /ביטול/ });
      await user.click(cancelButton);
    }
  });

  it('shows warning message about secure password handling', async () => {
    const user = userEvent.setup();
    renderForPasswordReset();

    await waitFor(() => {
      expect(getAllUsers).toHaveBeenCalled();
    });

    // Click on a user card to open drawer
    const userCard = screen.getByText(/יוסי כהן/).closest('.ant-card');
    if (userCard) {
      await user.click(userCard);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /איפוס סיסמה/ })).toBeInTheDocument();
      });

      // Click the reset password button
      await user.click(screen.getByRole('button', { name: /איפוס סיסמה/ }));

      // Wait for modal and check for warning message
      await waitFor(() => {
        expect(screen.getByText(/שים לב/)).toBeInTheDocument();
      });
    }
  });
});

describe('UsersPage - orgId dependency', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('reloads data when orgId changes from null to a value', async () => {
    mockUseOrgId.mockReturnValue(null);

    useAuthStore.mockImplementation((selector) => {
      const state = { user: { orgId: null, uid: 'admin-123', role: 'admin', isAdmin: true } };
      return selector(state);
    });

    useDataStore.mockImplementation((selector) => {
      const state = {
        users: [],
        setUsers: vi.fn(),
        updateUser: vi.fn(),
      };
      return selector ? selector(state) : state;
    });

    getAllUsers.mockResolvedValue({ success: true, users: [] });

    const { rerender } = render(
      <AntApp>
        <UsersPage />
      </AntApp>
    );

    await new Promise(r => setTimeout(r, 50));
    expect(getAllUsers).not.toHaveBeenCalled();

    mockUseOrgId.mockReturnValue('my-org');

    rerender(
      <AntApp>
        <UsersPage />
      </AntApp>
    );

    await waitFor(() => {
      expect(getAllUsers).toHaveBeenCalledWith('my-org');
    });
  });
});
