import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { App as AntApp } from 'antd';
import PricingSettings from './PricingSettings';
import { getPrintPricing, updatePrintPricing } from '../../services/pricingService';

vi.mock('../../services/pricingService');
vi.mock('../../hooks/useOrgId', () => ({
  useOrgId: () => 'my-org',
}));

describe('PricingSettings', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.setItem('adminOrgId', 'my-org');

    getPrintPricing.mockResolvedValue({
      success: true,
      pricing: { blackAndWhitePrice: 1.0, colorPrice: 3.0 },
    });

    updatePrintPricing.mockResolvedValue({ success: true });
  });

  it('renders pricing form', async () => {
    render(
      <AntApp>
        <PricingSettings />
      </AntApp>
    );

    await waitFor(() => {
      expect(getPrintPricing).toHaveBeenCalled();
    });

    expect(screen.getByText('מחיר הדפסה שחור-לבן (₪)')).toBeInTheDocument();
    expect(screen.getByText('מחיר הדפסה צבעונית (₪)')).toBeInTheDocument();
  });

  it('loads and displays current pricing', async () => {
    render(
      <AntApp>
        <PricingSettings />
      </AntApp>
    );

    await waitFor(() => {
      expect(getPrintPricing).toHaveBeenCalledWith('my-org');
    });

    // Check statistics display
    expect(screen.getByText('הדפסה שחור-לבן')).toBeInTheDocument();
    expect(screen.getByText('הדפסה צבעונית')).toBeInTheDocument();
  });

  it('shows info alert', async () => {
    render(
      <AntApp>
        <PricingSettings />
      </AntApp>
    );

    expect(screen.getByText('מידע חשוב')).toBeInTheDocument();
  });

  it('has refresh button', async () => {
    render(
      <AntApp>
        <PricingSettings />
      </AntApp>
    );

    await waitFor(() => {
      expect(getPrintPricing).toHaveBeenCalled();
    });

    expect(screen.getByText('רענן')).toBeInTheDocument();
  });

  it('refreshes pricing when refresh clicked', async () => {
    const user = userEvent.setup();

    render(
      <AntApp>
        <PricingSettings />
      </AntApp>
    );

    await waitFor(() => {
      expect(getPrintPricing).toHaveBeenCalledTimes(1);
    });

    await user.click(screen.getByText('רענן'));

    await waitFor(() => {
      expect(getPrintPricing).toHaveBeenCalledTimes(2);
    });
  });

  it('has save and reset buttons', async () => {
    render(
      <AntApp>
        <PricingSettings />
      </AntApp>
    );

    await waitFor(() => {
      expect(getPrintPricing).toHaveBeenCalled();
    });

    expect(screen.getByText('שמור שינויים')).toBeInTheDocument();
    expect(screen.getByText('איפוס')).toBeInTheDocument();
  });

  it('handles load error', async () => {
    getPrintPricing.mockResolvedValue({
      success: false,
      error: 'Failed to load',
    });

    render(
      <AntApp>
        <PricingSettings />
      </AntApp>
    );

    await waitFor(() => {
      expect(getPrintPricing).toHaveBeenCalled();
    });

    // Should not crash
    expect(screen.getByText('מחירים נוכחיים')).toBeInTheDocument();
  });

  it('does not crash when blackAndWhitePrice is 0 (division by zero)', async () => {
    getPrintPricing.mockResolvedValue({
      success: true,
      pricing: { blackAndWhitePrice: 0, colorPrice: 3.0 },
    });

    render(
      <AntApp>
        <PricingSettings />
      </AntApp>
    );

    await waitFor(() => {
      expect(getPrintPricing).toHaveBeenCalled();
    });

    // Should not show Infinity or NaN in the ratio display
    const body = document.body.textContent;
    expect(body).not.toContain('Infinity');
    expect(body).not.toContain('NaN');
  });
});
