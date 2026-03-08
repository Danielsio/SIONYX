import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { App as AntApp } from 'antd';
import SettingsPage from './SettingsPage';
import { getPrintPricing } from '../services/pricingService';

vi.mock('../services/pricingService');
vi.mock('../hooks/useOrgId', () => ({
  useOrgId: () => 'my-org',
}));

describe('SettingsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.setItem('adminOrgId', 'my-org');

    getPrintPricing.mockResolvedValue({
      success: true,
      pricing: { blackAndWhitePrice: 1.0, colorPrice: 3.0 },
    });
  });

  it('renders page title', async () => {
    render(
      <AntApp>
        <SettingsPage />
      </AntApp>
    );

    expect(screen.getByRole('heading', { level: 2 })).toBeInTheDocument();
  });

  it('shows pricing tab', async () => {
    render(
      <AntApp>
        <SettingsPage />
      </AntApp>
    );

    expect(screen.getByText(/תמחור הדפסות/)).toBeInTheDocument();
  });

  it('does not show operating hours tab (moved to supervisor panel)', async () => {
    render(
      <AntApp>
        <SettingsPage />
      </AntApp>
    );

    expect(screen.queryByText(/שעות פעילות/)).not.toBeInTheDocument();
  });

  it('loads pricing settings on mount', async () => {
    render(
      <AntApp>
        <SettingsPage />
      </AntApp>
    );

    await waitFor(() => {
      expect(getPrintPricing).toHaveBeenCalledWith('my-org');
    });
  });
});
