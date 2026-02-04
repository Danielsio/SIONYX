import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { App as AntApp } from 'antd';
import SettingsPage from './SettingsPage';
import { useAuthStore } from '../store/authStore';
import { getPrintPricing } from '../services/pricingService';
import { getOperatingHours } from '../services/settingsService';

vi.mock('../store/authStore');
vi.mock('../services/pricingService');
vi.mock('../services/settingsService');
vi.mock('../hooks/useOrgId', () => ({
  useOrgId: () => 'my-org',
}));

describe('SettingsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.setItem('adminOrgId', 'my-org');

    // Default mock returns
    getPrintPricing.mockResolvedValue({
      success: true,
      pricing: { blackAndWhitePrice: 1.0, colorPrice: 3.0 },
    });

    getOperatingHours.mockResolvedValue({
      success: true,
      operatingHours: {
        enabled: false,
        startTime: '06:00',
        endTime: '00:00',
        gracePeriodMinutes: 5,
        graceBehavior: 'graceful',
      },
    });
  });

  const mockUser = (role, isAdmin = false) => {
    useAuthStore.mockImplementation(selector => {
      const state = { user: { orgId: 'my-org', uid: 'user-123', role, isAdmin } };
      return selector(state);
    });
  };

  it('renders page title', async () => {
    mockUser('admin');

    render(
      <AntApp>
        <SettingsPage />
      </AntApp>
    );

    expect(screen.getByRole('heading', { level: 2 })).toBeInTheDocument();
  });

  it('shows pricing tab for admin', async () => {
    mockUser('admin');

    render(
      <AntApp>
        <SettingsPage />
      </AntApp>
    );

    expect(screen.getByText(/תמחור הדפסות/)).toBeInTheDocument();
  });

  it('does not show operating hours tab for admin', async () => {
    mockUser('admin');

    render(
      <AntApp>
        <SettingsPage />
      </AntApp>
    );

    expect(screen.queryByText(/שעות פעילות/)).not.toBeInTheDocument();
  });

  it('shows operating hours tab for supervisor', async () => {
    mockUser('supervisor');

    render(
      <AntApp>
        <SettingsPage />
      </AntApp>
    );

    expect(screen.getByText(/שעות פעילות/)).toBeInTheDocument();
  });

  it('shows both tabs for supervisor', async () => {
    mockUser('supervisor');

    render(
      <AntApp>
        <SettingsPage />
      </AntApp>
    );

    expect(screen.getByText(/תמחור הדפסות/)).toBeInTheDocument();
    expect(screen.getByText(/שעות פעילות/)).toBeInTheDocument();
  });

  it('shows role display name for supervisor', async () => {
    mockUser('supervisor');

    render(
      <AntApp>
        <SettingsPage />
      </AntApp>
    );

    expect(screen.getByText(/מפקח/)).toBeInTheDocument();
  });

  it('loads pricing settings on mount', async () => {
    mockUser('admin');

    render(
      <AntApp>
        <SettingsPage />
      </AntApp>
    );

    await waitFor(() => {
      expect(getPrintPricing).toHaveBeenCalledWith('my-org');
    });
  });

  it('works with legacy isAdmin field', async () => {
    useAuthStore.mockImplementation(selector => {
      const state = { user: { orgId: 'my-org', uid: 'user-123', isAdmin: true } };
      return selector(state);
    });

    render(
      <AntApp>
        <SettingsPage />
      </AntApp>
    );

    expect(screen.getByText(/תמחור הדפסות/)).toBeInTheDocument();
    // Admin via isAdmin should not see supervisor tabs
    expect(screen.queryByText(/שעות פעילות/)).not.toBeInTheDocument();
  });
});
