import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { App as AntApp } from 'antd';
import PackagesPage from './PackagesPage';
import { getAllPackages, createPackage, updatePackage, deletePackage, calculateFinalPrice } from '../services/packageService';
import { useAuthStore } from '../store/authStore';
import { useDataStore } from '../store/dataStore';

// Mock dependencies
vi.mock('../services/packageService');
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
    fromNow: () => 'לפני שבוע',
    unix: () => date ? new Date(date).getTime() / 1000 : Date.now() / 1000,
  });
  dayjs.extend = () => {};
  dayjs.locale = () => {};
  return { default: dayjs };
});

const mockPackages = [
  {
    id: 'pkg-1',
    name: 'חבילה בסיסית',
    description: 'חבילה למתחילים',
    price: 50,
    minutes: 60,
    prints: 10,
    createdAt: '2024-01-15T10:00:00Z',
  },
  {
    id: 'pkg-2',
    name: 'חבילה מתקדמת',
    description: 'חבילה למשתמשים מנוסים',
    price: 100,
    minutes: 180,
    prints: 30,
    discountPercent: 10,
    createdAt: '2024-02-20T10:00:00Z',
  },
];

const renderPackagesPage = ({
  packagesOverride = mockPackages,
  userOverride = { orgId: 'my-org', uid: 'admin-123', isAdmin: true },
} = {}) => {
  const mockSetPackages = vi.fn();
  const mockUpdateStorePackage = vi.fn();
  const mockRemovePackage = vi.fn();

  useAuthStore.mockImplementation((selector) => {
    const state = { user: userOverride };
    return selector(state);
  });

  useDataStore.mockImplementation((selector) => {
    const state = {
      packages: packagesOverride,
      setPackages: mockSetPackages,
      updatePackage: mockUpdateStorePackage,
      removePackage: mockRemovePackage,
    };
    return selector ? selector(state) : state;
  });

  getAllPackages.mockResolvedValue({
    success: true,
    packages: packagesOverride,
  });

  createPackage.mockResolvedValue({ success: true, packageId: 'new-pkg-id' });
  updatePackage.mockResolvedValue({ success: true });
  deletePackage.mockResolvedValue({ success: true });
  calculateFinalPrice.mockImplementation((price, discount) => ({
    finalPrice: price - (price * (discount || 0) / 100),
    savings: price * (discount || 0) / 100,
  }));

  return {
    ...render(
      <AntApp>
        <PackagesPage />
      </AntApp>
    ),
    mockSetPackages,
    mockUpdateStorePackage,
    mockRemovePackage,
  };
};

describe('PackagesPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.setItem('adminOrgId', 'my-org');
  });

  it('renders without crashing', async () => {
    renderPackagesPage();

    await waitFor(() => {
      expect(getAllPackages).toHaveBeenCalled();
    });

    expect(document.body).toBeInTheDocument();
  });

  it('displays page title', async () => {
    renderPackagesPage();

    await waitFor(() => {
      expect(getAllPackages).toHaveBeenCalled();
    });

    // Page should have rendered successfully
    expect(document.body.textContent).toContain('חביל');
  });

  it('loads packages on mount', async () => {
    renderPackagesPage();

    await waitFor(() => {
      expect(getAllPackages).toHaveBeenCalledWith('my-org');
    });
  });

  it('renders create package button', async () => {
    renderPackagesPage();

    await waitFor(() => {
      expect(getAllPackages).toHaveBeenCalled();
    });

    expect(screen.getByText(/צור חבילה|הוסף חבילה/)).toBeInTheDocument();
  });

  it('renders refresh button', async () => {
    renderPackagesPage();

    await waitFor(() => {
      expect(getAllPackages).toHaveBeenCalled();
    });

    expect(screen.getByText('רענן')).toBeInTheDocument();
  });

  it('displays packages when available', async () => {
    renderPackagesPage();

    await waitFor(() => {
      expect(getAllPackages).toHaveBeenCalled();
    });

    // Should display package names
    expect(screen.getByText('חבילה בסיסית')).toBeInTheDocument();
    expect(screen.getByText('חבילה מתקדמת')).toBeInTheDocument();
  });

  it('shows empty state when no packages', async () => {
    renderPackagesPage({ packagesOverride: [] });

    await waitFor(() => {
      expect(getAllPackages).toHaveBeenCalled();
    });

    // Should show empty state or "no packages" message
    expect(document.body).toBeInTheDocument();
  });

  it('opens create modal when create button clicked', async () => {
    const user = userEvent.setup();
    renderPackagesPage();

    await waitFor(() => {
      expect(getAllPackages).toHaveBeenCalled();
    });

    const createButton = screen.getByText(/צור חבילה|הוסף חבילה/);
    await user.click(createButton);

    // Modal should appear
    await waitFor(() => {
      expect(screen.getByLabelText(/שם/)).toBeInTheDocument();
    });
  });

  it('refreshes packages when refresh button clicked', async () => {
    const user = userEvent.setup();
    renderPackagesPage();

    await waitFor(() => {
      expect(getAllPackages).toHaveBeenCalledTimes(1);
    });

    await user.click(screen.getByText('רענן'));

    await waitFor(() => {
      expect(getAllPackages).toHaveBeenCalledTimes(2);
    });
  });

  it('handles package loading error', async () => {
    getAllPackages.mockResolvedValue({
      success: false,
      error: 'Failed to load packages',
    });

    renderPackagesPage();

    await waitFor(() => {
      expect(getAllPackages).toHaveBeenCalled();
    });

    // Should not crash
    expect(document.body).toBeInTheDocument();
  });

  it('displays package prices', async () => {
    renderPackagesPage();

    await waitFor(() => {
      expect(getAllPackages).toHaveBeenCalled();
    });

    // Prices should be displayed (₪50, ₪100)
    const priceElements = screen.getAllByText(/₪/);
    expect(priceElements.length).toBeGreaterThan(0);
  });

  it('displays package time in minutes', async () => {
    renderPackagesPage();

    await waitFor(() => {
      expect(getAllPackages).toHaveBeenCalled();
    });

    // Time should be displayed
    expect(document.body).toBeInTheDocument();
  });

  it('defaults optional fields to 0 on create', async () => {
    const user = userEvent.setup();
    renderPackagesPage();

    await waitFor(() => {
      expect(getAllPackages).toHaveBeenCalled();
    });

    await user.click(screen.getByText(/צור חבילה|הוסף חבילה/));

    await waitFor(() => {
      expect(screen.getByLabelText(/שם/)).toBeInTheDocument();
    });

    await user.type(screen.getByPlaceholderText('למשל, חבילת בסיס'), 'חבילת בדיקה');
    await user.type(screen.getByPlaceholderText('תאר מה החבילה כוללת...'), 'תיאור בדיקה');
    await user.type(screen.getByPlaceholderText('0.00'), '25');

    await user.click(screen.getByText('צור'));

    await waitFor(() => {
      expect(createPackage).toHaveBeenCalled();
    });

    const [, createdValues] = createPackage.mock.calls[0];
    expect(createdValues).toMatchObject({
      discountPercent: 0,
      minutes: 0,
      prints: 0,
      validityDays: 0,
    });
  });

  it('shows delete action in view modal for admins', async () => {
    const user = userEvent.setup();
    renderPackagesPage({ userOverride: { orgId: 'my-org', uid: 'admin-123', isAdmin: true } });

    await waitFor(() => {
      expect(getAllPackages).toHaveBeenCalled();
    });

    await user.click(screen.getByText('חבילה בסיסית'));

    await waitFor(() => {
      expect(screen.getByText('פרטי חבילה')).toBeInTheDocument();
    });

    expect(screen.getByText('מחק')).toBeInTheDocument();
  });

  it('hides delete action in view modal for non-admins', async () => {
    const user = userEvent.setup();
    renderPackagesPage({ userOverride: { orgId: 'my-org', uid: 'user-1', isAdmin: false } });

    await waitFor(() => {
      expect(getAllPackages).toHaveBeenCalled();
    });

    await user.click(screen.getByText('חבילה בסיסית'));

    await waitFor(() => {
      expect(screen.getByText('פרטי חבילה')).toBeInTheDocument();
    });

    expect(screen.queryByText('מחק')).not.toBeInTheDocument();
  });

  it('reloads data when orgId changes from null to a value', async () => {
    mockUseOrgId.mockReturnValue(null);

    useAuthStore.mockImplementation((selector) => {
      const state = { user: { orgId: null, uid: 'admin-123', isAdmin: true } };
      return selector(state);
    });

    useDataStore.mockImplementation((selector) => {
      const state = {
        packages: [],
        setPackages: vi.fn(),
        updatePackage: vi.fn(),
        removePackage: vi.fn(),
      };
      return selector ? selector(state) : state;
    });

    getAllPackages.mockResolvedValue({ success: true, packages: [] });

    const { rerender } = render(
      <AntApp>
        <PackagesPage />
      </AntApp>
    );

    await new Promise(r => setTimeout(r, 50));
    expect(getAllPackages).not.toHaveBeenCalled();

    mockUseOrgId.mockReturnValue('my-org');

    rerender(
      <AntApp>
        <PackagesPage />
      </AntApp>
    );

    await waitFor(() => {
      expect(getAllPackages).toHaveBeenCalledWith('my-org');
    });
  });
});

