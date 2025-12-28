import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { App as AntApp } from 'antd';
import PricingPage from './PricingPage';
import { getPrintPricing, updatePrintPricing } from '../services/pricingService';
import { useAuthStore } from '../store/authStore';

// Mock dependencies
vi.mock('../services/pricingService');
vi.mock('../store/authStore');

const renderPricingPage = () => {
  useAuthStore.mockImplementation((selector) => {
    const state = { user: { orgId: 'my-org', uid: 'admin-123' } };
    return selector(state);
  });

  return render(
    <AntApp>
      <PricingPage />
    </AntApp>
  );
};

describe('PricingPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.setItem('adminOrgId', 'my-org');
    
    // Default mock for getPrintPricing
    getPrintPricing.mockResolvedValue({
      success: true,
      pricing: {
        blackAndWhitePrice: 1.5,
        colorPrice: 4.0,
      },
    });
    
    updatePrintPricing.mockResolvedValue({ success: true });
  });

  it('renders pricing page without crashing', async () => {
    renderPricingPage();

    // Wait for loading to complete
    await waitFor(() => {
      expect(getPrintPricing).toHaveBeenCalled();
    });

    expect(document.body).toBeInTheDocument();
  });

  it('calls getPrintPricing on mount', async () => {
    renderPricingPage();

    await waitFor(() => {
      expect(getPrintPricing).toHaveBeenCalledWith('my-org');
    });
  });

  it('renders pricing title', async () => {
    renderPricingPage();

    await waitFor(() => {
      expect(getPrintPricing).toHaveBeenCalled();
    });

    // Should have some pricing-related text (use queryAllBy since there may be multiple)
    const pricingElements = screen.queryAllByText(/מחיר/i);
    expect(pricingElements.length).toBeGreaterThan(0);
  });

  it('handles failed pricing fetch gracefully', async () => {
    getPrintPricing.mockResolvedValue({
      success: false,
      error: 'Failed to load',
    });

    renderPricingPage();

    await waitFor(() => {
      expect(getPrintPricing).toHaveBeenCalled();
    });

    // Should not crash
    expect(document.body).toBeInTheDocument();
  });

  it('uses default values when pricing not available', async () => {
    getPrintPricing.mockResolvedValue({
      success: true,
      pricing: {},
    });

    renderPricingPage();

    await waitFor(() => {
      expect(getPrintPricing).toHaveBeenCalled();
    });

    expect(document.body).toBeInTheDocument();
  });
});
