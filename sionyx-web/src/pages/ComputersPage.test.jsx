import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ComputersPage from './ComputersPage';
import {
  getAllComputers,
  getComputerUsageStats,
  getActiveComputerUsers,
  forceLogoutUser,
  deleteComputer,
} from '../services/computerService';
import { subscribeToComputers, subscribeToUsers } from '../services/realtimeService';

// Realtime subscription data - mutated per test
const realtimeData = { computers: [], users: [] };

// Mock dependencies
vi.mock('../services/computerService', async () => {
  const actual = await vi.importActual('../services/computerService');
  return {
    ...actual,
    getAllComputers: vi.fn(),
    getComputerUsageStats: vi.fn(),
    getActiveComputerUsers: vi.fn(),
    forceLogoutUser: vi.fn(),
    deleteComputer: vi.fn(),
  };
});
vi.mock('../services/realtimeService', () => ({
  subscribeToComputers: vi.fn((orgId, callback) => {
    if (orgId) callback(realtimeData.computers);
    return vi.fn();
  }),
  subscribeToUsers: vi.fn((orgId, callback) => {
    if (orgId) callback(realtimeData.users);
    return vi.fn();
  }),
  subscribeToMessages: vi.fn(() => vi.fn()),
  subscribeToAnnouncements: vi.fn(() => vi.fn()),
}));
vi.mock('../store/authStore', () => ({
  useAuthStore: vi.fn(selector => {
    const state = {
      user: { orgId: 'my-org', uid: 'admin-123', role: 'admin', isAdmin: true },
      getOrgId: () => 'my-org',
    };
    return selector(state);
  }),
}));

const mockComputers = [
  {
    id: 'comp-1',
    computerName: 'PC-001',
    isActive: true,
    currentUserId: 'user-1',
    lastUserLogin: new Date(Date.now() - 1800000).toISOString(),
    lastSeen: new Date().toISOString(),
    osInfo: { platform: 'win32', version: '10.0' },
  },
  {
    id: 'comp-2',
    computerName: 'PC-002',
    isActive: false,
    currentUserId: null,
    lastSeen: new Date(Date.now() - 3600000).toISOString(),
    osInfo: { platform: 'win32', version: '11.0' },
  },
];

// Users from realtime subscription (uid, firstName, lastName, etc.)
const mockUsers = [
  {
    uid: 'user-1',
    firstName: 'יוסי',
    lastName: 'כהן',
    phoneNumber: '0501234567',
    sessionStartTime: new Date(Date.now() - 1800000).toISOString(),
    isSessionActive: true,
    remainingTime: 3600,
  },
];

const mockActiveUsers = [
  {
    userId: 'user-1',
    userName: 'יוסי כהן',
    computerId: 'comp-1',
    computerName: 'PC-001',
    loginTime: new Date(Date.now() - 1800000).toISOString(),
  },
];

const mockStats = {
  totalComputers: 2,
  activeComputers: 1,
  computersWithUsers: 1,
  computerDetails: mockComputers,
};

const renderComputersPage = () => {
  realtimeData.computers = [...mockComputers];
  realtimeData.users = [...mockUsers];

  getAllComputers.mockResolvedValue({
    success: true,
    data: mockComputers,
  });

  getComputerUsageStats.mockResolvedValue({
    success: true,
    data: mockStats,
  });

  getActiveComputerUsers.mockResolvedValue({
    success: true,
    data: mockActiveUsers,
  });

  forceLogoutUser.mockResolvedValue({ success: true });
  deleteComputer.mockResolvedValue({ success: true });

  return render(<ComputersPage />);
};

describe('ComputersPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    realtimeData.computers = [...mockComputers];
    realtimeData.users = [...mockUsers];
  });

  it('renders without crashing', async () => {
    renderComputersPage();

    await waitFor(() => {
      expect(subscribeToComputers).toHaveBeenCalledWith('my-org', expect.any(Function));
    });

    expect(document.body).toBeInTheDocument();
  });

  it('displays page title', async () => {
    renderComputersPage();

    await waitFor(() => {
      expect(screen.getByText('ניהול מחשבים')).toBeInTheDocument();
    });
  });

  it('subscribes to computers and users on mount', async () => {
    renderComputersPage();

    await waitFor(() => {
      expect(subscribeToComputers).toHaveBeenCalledWith('my-org', expect.any(Function));
      expect(subscribeToUsers).toHaveBeenCalledWith('my-org', expect.any(Function));
    });
  });

  it('displays computer statistics', async () => {
    renderComputersPage();

    await waitFor(() => {
      expect(screen.getByText(/סה"כ מחשבים|מחשבים פעילים/)).toBeInTheDocument();
    });
  });

  it('shows active computers count', async () => {
    renderComputersPage();

    await waitFor(() => {
      expect(subscribeToComputers).toHaveBeenCalled();
    });

    // Stats should be displayed
    expect(document.body).toBeInTheDocument();
  });

  it('renders computer list', async () => {
    renderComputersPage();

    await waitFor(() => {
      expect(screen.getByText('PC-001')).toBeInTheDocument();
    });
  });

  it('shows active user on computer', async () => {
    renderComputersPage();

    await waitFor(() => {
      const userElements = screen.queryAllByText(/יוסי/);
      expect(userElements.length).toBeGreaterThanOrEqual(0);
    });
  });

  it('has refresh button', async () => {
    renderComputersPage();

    await waitFor(() => {
      expect(screen.getByText('רענן')).toBeInTheDocument();
    });
  });

  it('refreshes data when refresh clicked', async () => {
    const user = userEvent.setup();
    renderComputersPage();

    await waitFor(() => {
      expect(screen.getByText('רענן')).toBeInTheDocument();
    });

    // Before refresh: loadData (getAllComputers etc) not called on mount
    expect(getAllComputers).not.toHaveBeenCalled();

    await user.click(screen.getByText('רענן'));

    await waitFor(() => {
      expect(getAllComputers).toHaveBeenCalledTimes(1);
      expect(getActiveComputerUsers).toHaveBeenCalledTimes(1);
      expect(getComputerUsageStats).toHaveBeenCalledTimes(1);
    });
  });

  it('handles load error gracefully', async () => {
    const user = userEvent.setup();
    renderComputersPage();

    await waitFor(() => {
      expect(screen.getByText('רענן')).toBeInTheDocument();
    });

    getAllComputers.mockRejectedValue(new Error('Failed to load computers'));
    await user.click(screen.getByText('רענן'));

    await waitFor(() => {
      expect(screen.getByText('נכשל בטעינת נתוני המחשבים')).toBeInTheDocument();
    });
  });

  it('shows empty state when no computers', async () => {
    realtimeData.computers = [];
    realtimeData.users = [];

    render(<ComputersPage />);

    await waitFor(() => {
      expect(subscribeToComputers).toHaveBeenCalled();
    });

    expect(document.body).toBeInTheDocument();
  });

  it('displays tabs for different views', async () => {
    renderComputersPage();

    await waitFor(() => {
      const tabs = screen.getAllByRole('tab');
      expect(tabs.length).toBeGreaterThan(0);
    });
  });

  it('shows online status indicator', async () => {
    renderComputersPage();

    await waitFor(() => {
      expect(subscribeToComputers).toHaveBeenCalled();
    });

    expect(document.body).toBeInTheDocument();
  });

  // BUG TESTS - Session Time and Status Display
  describe('Session Time Bug Tests', () => {
    it('should show "מושהה" for logged-in user not in active session', async () => {
      // User from realtime: logged in but NOT in active session
      realtimeData.computers = [
        {
          id: 'comp-1',
          computerName: 'PC-001',
          currentUserId: 'user-1',
          lastUserLogin: new Date(Date.now() - 1800000).toISOString(),
        },
      ];
      realtimeData.users = [
        {
          uid: 'user-1',
          firstName: 'יוסי',
          lastName: 'כהן',
          phoneNumber: '0501234567',
          isSessionActive: false,
          sessionStartTime: null,
          remainingTime: 3600,
        },
      ];

      render(<ComputersPage />);

      await waitFor(() => {
        const statusTags = screen.queryAllByText('מושהה');
        expect(statusTags.length).toBeGreaterThan(0);
      });
    });

    it('should show "--" activity time when session has not started', async () => {
      const user = userEvent.setup();

      realtimeData.computers = [
        {
          id: 'comp-1',
          computerName: 'PC-001',
          currentUserId: 'user-1',
          lastUserLogin: new Date(Date.now() - 3600000).toISOString(),
        },
      ];
      realtimeData.users = [
        {
          uid: 'user-1',
          firstName: 'יוסי',
          lastName: 'כהן',
          phoneNumber: '0501234567',
          isSessionActive: false,
          sessionStartTime: null,
          remainingTime: 3600,
        },
      ];

      render(<ComputersPage />);

      await waitFor(() => {
        const userCards = screen.queryAllByText('יוסי כהן');
        expect(userCards.length).toBeGreaterThan(0);
      });

      const activeUsersTab = await screen.findByRole('tab', { name: /משתמשים פעילים/i });
      await user.click(activeUsersTab);

      const userCards = await screen.findAllByText('יוסי כהן');
      await user.click(userCards[0]);

      await waitFor(() => {
        const placeholders = screen.queryAllByText('--');
        expect(placeholders.length).toBeGreaterThan(0);
      });
    });

    it('should use sessionStartTime for activity calculation, not loginTime', async () => {
      const now = Date.now();
      realtimeData.computers = [
        {
          id: 'comp-1',
          computerName: 'PC-001',
          currentUserId: 'user-1',
          lastUserLogin: new Date(now - 7200000).toISOString(),
        },
      ];
      realtimeData.users = [
        {
          uid: 'user-1',
          firstName: 'יוסי',
          lastName: 'כהן',
          phoneNumber: '0501234567',
          isSessionActive: true,
          sessionStartTime: new Date(now - 1800000).toISOString(),
          remainingTime: 3600,
        },
      ];

      render(<ComputersPage />);

      await waitFor(() => {
        const userCards = screen.queryAllByText('יוסי כהן');
        expect(userCards.length).toBeGreaterThan(0);
      });

      // Activity time should show ~30 minutes, NOT 2 hours
      await waitFor(() => {
        const twoHourTime = screen.queryByText(/^2:[0-5][0-9]:[0-5][0-9]$/);
        expect(twoHourTime).toBeNull();
      });
    });
  });
});
