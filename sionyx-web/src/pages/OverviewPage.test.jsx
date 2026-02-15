import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { App as AntApp } from 'antd';
import OverviewPage from './OverviewPage';
import { getOrganizationStats } from '../services/organizationService';
import { getPrintPricing } from '../services/pricingService';
import { getAllUsers } from '../services/userService';
import { useAuthStore } from '../store/authStore';
import { useDataStore } from '../store/dataStore';

// Mock dependencies
vi.mock('../services/organizationService');
vi.mock('../services/pricingService');
vi.mock('../services/userService');
vi.mock('../store/authStore');
vi.mock('../store/dataStore');
const mockUseOrgId = vi.fn(() => 'my-org');
vi.mock('../hooks/useOrgId', () => ({
  useOrgId: (...args) => mockUseOrgId(...args),
}));

const renderOverviewPage = () => {
  const mockSetStats = vi.fn();

  useAuthStore.mockImplementation(selector => {
    const state = {
      user: {
        orgId: 'my-org',
        uid: 'admin-123',
        displayName: 'Admin User',
        email: 'admin@test.com',
      },
    };
    return selector(state);
  });

  useDataStore.mockImplementation(selector => {
    const state = {
      stats: {
        usersCount: 10,
        packagesCount: 5,
        purchasesCount: 50,
        totalRevenue: 1500.0,
        totalTimeMinutes: 5000,
      },
      setStats: mockSetStats,
    };
    return selector ? selector(state) : state;
  });

  return {
    ...render(
      <AntApp>
        <OverviewPage />
      </AntApp>
    ),
    mockSetStats,
  };
};

describe('OverviewPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.setItem('adminOrgId', 'my-org');

    // Default mocks
    getOrganizationStats.mockResolvedValue({
      success: true,
      stats: {
        usersCount: 10,
        packagesCount: 5,
        purchasesCount: 50,
        totalRevenue: 1500.0,
        totalTimeMinutes: 5000,
      },
    });

    getPrintPricing.mockResolvedValue({
      success: true,
      pricing: {
        blackAndWhitePrice: 1.0,
        colorPrice: 3.0,
      },
    });

    getAllUsers.mockResolvedValue({
      success: true,
      users: [],
    });
  });

  it('renders overview page without crashing', async () => {
    renderOverviewPage();

    await waitFor(() => {
      expect(getOrganizationStats).toHaveBeenCalled();
    });

    expect(document.body).toBeInTheDocument();
  });

  it('loads organization stats on mount', async () => {
    renderOverviewPage();

    await waitFor(() => {
      expect(getOrganizationStats).toHaveBeenCalledWith('my-org');
    });
  });

  it('loads print pricing on mount', async () => {
    renderOverviewPage();

    await waitFor(() => {
      expect(getPrintPricing).toHaveBeenCalledWith('my-org');
    });
  });

  it('loads users on mount', async () => {
    renderOverviewPage();

    await waitFor(() => {
      expect(getAllUsers).toHaveBeenCalledWith('my-org');
    });
  });

  it('displays overview title after loading', async () => {
    renderOverviewPage();

    await waitFor(
      () => {
        expect(screen.queryByRole('status')).not.toBeInTheDocument();
      },
      { timeout: 2000 }
    );

    expect(screen.getByText(/סקירה/)).toBeInTheDocument();
  });

  it('handles failed stats fetch gracefully', async () => {
    getOrganizationStats.mockResolvedValue({
      success: false,
      error: 'Failed to load',
    });

    renderOverviewPage();

    await waitFor(() => {
      expect(getOrganizationStats).toHaveBeenCalled();
    });

    // Should not crash
    expect(document.body).toBeInTheDocument();
  });

  it('shows statistics cards after loading', async () => {
    renderOverviewPage();

    await waitFor(
      () => {
        expect(screen.queryByRole('status')).not.toBeInTheDocument();
      },
      { timeout: 2000 }
    );

    // Should show at least one statistic label (use queryAllBy for multiple matches)
    const statsLabels = [/משתמשים/, /חבילות/, /רכישות/, /הכנסות/];
    const foundLabel = statsLabels.some(label => screen.queryAllByText(label).length > 0);
    expect(foundLabel).toBe(true);
  });

  it('reloads data when orgId changes from null to a value', async () => {
    // Start with null orgId
    mockUseOrgId.mockReturnValue(null);

    useAuthStore.mockImplementation(selector => {
      const state = {
        user: { orgId: null, uid: 'admin-123', displayName: 'Admin', email: 'admin@test.com' },
      };
      return selector(state);
    });

    useDataStore.mockImplementation(selector => {
      const state = {
        stats: {},
        setStats: vi.fn(),
      };
      return selector ? selector(state) : state;
    });

    const { rerender } = render(
      <AntApp>
        <OverviewPage />
      </AntApp>
    );

    // With null orgId, services should NOT be called (guard returns early)
    await new Promise(r => setTimeout(r, 50));
    expect(getOrganizationStats).not.toHaveBeenCalled();

    // Now orgId becomes available
    mockUseOrgId.mockReturnValue('my-org');

    rerender(
      <AntApp>
        <OverviewPage />
      </AntApp>
    );

    // After rerender with valid orgId, effect should re-run and services should be called
    await waitFor(() => {
      expect(getOrganizationStats).toHaveBeenCalledWith('my-org');
    });
  });
});
