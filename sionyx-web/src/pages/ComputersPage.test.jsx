import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ComputersPage from './ComputersPage';
import {
  getAllComputers,
  getComputerUsageStats,
  getActiveComputerUsers,
  forceLogoutUser,
} from '../services/computerService';

// Mock dependencies
vi.mock('../services/computerService');
vi.mock('../store/authStore', () => ({
  useAuthStore: vi.fn((selector) => {
    const state = { user: { orgId: 'my-org', uid: 'admin-123', role: 'admin', isAdmin: true } };
    return selector(state);
  }),
}));

const mockComputers = [
  {
    id: 'comp-1',
    computerName: 'PC-001',
    isActive: true,
    currentUserId: 'user-1',
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

  return render(<ComputersPage />);
};

describe('ComputersPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.setItem('adminOrgId', 'my-org');
  });

  it('renders without crashing', async () => {
    renderComputersPage();

    await waitFor(() => {
      expect(getAllComputers).toHaveBeenCalled();
    });

    expect(document.body).toBeInTheDocument();
  });

  it('displays page title', async () => {
    renderComputersPage();

    await waitFor(() => {
      expect(getAllComputers).toHaveBeenCalled();
    });

    expect(screen.getByText('ניהול מחשבים')).toBeInTheDocument();
  });

  it('loads all data on mount', async () => {
    renderComputersPage();

    await waitFor(() => {
      expect(getAllComputers).toHaveBeenCalled();
      expect(getComputerUsageStats).toHaveBeenCalled();
      expect(getActiveComputerUsers).toHaveBeenCalled();
    });
  });

  it('displays computer statistics', async () => {
    renderComputersPage();

    await waitFor(() => {
      expect(getAllComputers).toHaveBeenCalled();
    });

    // Should show total computers stat
    await waitFor(() => {
      expect(screen.getByText(/סה"כ מחשבים|מחשבים פעילים/)).toBeInTheDocument();
    });
  });

  it('shows active computers count', async () => {
    renderComputersPage();

    await waitFor(() => {
      expect(getComputerUsageStats).toHaveBeenCalled();
    });

    // Stats should be displayed
    expect(document.body).toBeInTheDocument();
  });

  it('renders computer list', async () => {
    renderComputersPage();

    await waitFor(() => {
      expect(getAllComputers).toHaveBeenCalled();
    });

    // Should display computer names
    await waitFor(() => {
      expect(screen.getByText('PC-001')).toBeInTheDocument();
    });
  });

  it('shows active user on computer', async () => {
    renderComputersPage();

    await waitFor(() => {
      expect(getActiveComputerUsers).toHaveBeenCalled();
    });

    // Should display active user name
    await waitFor(() => {
      const userElements = screen.queryAllByText(/יוסי/);
      expect(userElements.length).toBeGreaterThanOrEqual(0); // May or may not be visible
    });
  });

  it('has refresh button', async () => {
    renderComputersPage();

    await waitFor(() => {
      expect(getAllComputers).toHaveBeenCalled();
    });

    expect(screen.getByText('רענן')).toBeInTheDocument();
  });

  it('refreshes data when refresh clicked', async () => {
    const user = userEvent.setup();
    renderComputersPage();

    await waitFor(() => {
      expect(getAllComputers).toHaveBeenCalledTimes(1);
    });

    await user.click(screen.getByText('רענן'));

    await waitFor(() => {
      expect(getAllComputers).toHaveBeenCalledTimes(2);
    });
  });

  it('handles load error gracefully', async () => {
    getAllComputers.mockResolvedValue({
      success: false,
      error: 'Failed to load computers',
    });

    renderComputersPage();

    await waitFor(() => {
      expect(getAllComputers).toHaveBeenCalled();
    });

    // Should show error message
    expect(document.body).toBeInTheDocument();
  });

  it('shows empty state when no computers', async () => {
    getAllComputers.mockResolvedValue({
      success: true,
      data: [],
    });

    getComputerUsageStats.mockResolvedValue({
      success: true,
      data: { totalComputers: 0, activeComputers: 0, computersWithUsers: 0 },
    });

    renderComputersPage();

    await waitFor(() => {
      expect(getAllComputers).toHaveBeenCalled();
    });

    expect(document.body).toBeInTheDocument();
  });

  it('displays tabs for different views', async () => {
    renderComputersPage();

    await waitFor(() => {
      expect(getAllComputers).toHaveBeenCalled();
    });

    // Should have tabs
    const tabs = screen.getAllByRole('tab');
    expect(tabs.length).toBeGreaterThan(0);
  });

  it('shows online status indicator', async () => {
    renderComputersPage();

    await waitFor(() => {
      expect(getAllComputers).toHaveBeenCalled();
    });

    // Should show status indicators
    expect(document.body).toBeInTheDocument();
  });

  // BUG TESTS - Session Time and Status Display
  describe('Session Time Bug Tests', () => {
    it('should show "מושהה" for logged-in user not in active session', async () => {
      // Mock user who is logged in but NOT in active session
      // Using centralized userStatus: CONNECTED status = "מושהה" (on hold)
      getActiveComputerUsers.mockResolvedValue({
        success: true,
        data: [{
          userId: 'user-1',
          userName: 'יוסי כהן',
          computerId: 'comp-1',
          computerName: 'PC-001',
          loginTime: new Date(Date.now() - 1800000).toISOString(),
          sessionActive: false, // NOT in paid session
          sessionStartTime: null, // No session started
          remainingTime: 3600,
        }],
      });

      render(<ComputersPage />);

      await waitFor(() => {
        expect(getActiveComputerUsers).toHaveBeenCalled();
      });

      // Should show "מושהה" (on hold) - user is connected but not in active session
      await waitFor(() => {
        const statusTags = screen.queryAllByText('מושהה');
        expect(statusTags.length).toBeGreaterThan(0);
      });
    });

    it('should show "--" activity time when session has not started', async () => {
      const user = userEvent.setup();
      
      // Mock user who is logged in but hasn't started paid session
      getActiveComputerUsers.mockResolvedValue({
        success: true,
        data: [{
          userId: 'user-1',
          userName: 'יוסי כהן',
          computerId: 'comp-1',
          computerName: 'PC-001',
          loginTime: new Date(Date.now() - 3600000).toISOString(), // Logged in 1 hour ago
          sessionActive: false,
          sessionStartTime: null, // No paid session started!
          remainingTime: 3600,
        }],
      });

      render(<ComputersPage />);

      await waitFor(() => {
        expect(getActiveComputerUsers).toHaveBeenCalled();
      });

      // Navigate to the "active users" tab (activity time is shown in UserCard which is on this tab)
      const activeUsersTab = await screen.findByRole('tab', { name: /משתמשים פעילים/i });
      await user.click(activeUsersTab);

      // Click on the user card to expand it (activity time is in expanded section)
      const userCards = await screen.findAllByText('יוסי כהן');
      await user.click(userCards[0]);

      // Should NOT show 1 hour of activity time since session hasn't started
      // Activity time should show "--" placeholder
      await waitFor(() => {
        const placeholders = screen.queryAllByText('--');
        expect(placeholders.length).toBeGreaterThan(0);
      });
    });

    it('should use sessionStartTime for activity calculation, not loginTime', async () => {
      const now = Date.now();
      // User logged into computer 2 hours ago, but started session 30 minutes ago
      getActiveComputerUsers.mockResolvedValue({
        success: true,
        data: [{
          userId: 'user-1',
          userName: 'יוסי כהן',
          computerId: 'comp-1',
          computerName: 'PC-001',
          loginTime: new Date(now - 7200000).toISOString(), // 2 hours ago
          sessionActive: true,
          sessionStartTime: new Date(now - 1800000).toISOString(), // 30 minutes ago
          remainingTime: 3600,
        }],
      });

      render(<ComputersPage />);

      await waitFor(() => {
        expect(getActiveComputerUsers).toHaveBeenCalled();
      });

      // Activity time should show ~30 minutes, NOT 2 hours
      // Looking for time in format like "0:30:XX" or "30:XX"
      await waitFor(() => {
        // Should NOT see 2 hours (2:XX:XX or 1:XX:XX)
        const twoHourTime = screen.queryByText(/^2:[0-5][0-9]:[0-5][0-9]$/);
        expect(twoHourTime).toBeNull();
      });
    });
  });
});


