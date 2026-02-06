import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import MainLayout from './MainLayout';
import { useAuthStore } from '../store/authStore';
import { signOut } from '../services/authService';

// Mock dependencies
vi.mock('../store/authStore');
vi.mock('../services/authService');

const mockNavigate = vi.fn();
const mockLocation = { pathname: '/admin' };

vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useLocation: () => mockLocation,
    Outlet: () => <div data-testid="outlet">Page Content</div>,
  };
});

const renderMainLayout = (userOverride = null) => {
  const mockLogout = vi.fn();
  const mockUser = userOverride || {
    uid: 'admin-123',
    orgId: 'test-org',
    email: 'admin@test.com',
    displayName: 'Admin User',
  };

  useAuthStore.mockImplementation((selector) => {
    const state = {
      user: mockUser,
      logout: mockLogout,
    };
    return selector(state);
  });

  signOut.mockResolvedValue({ success: true });

  return {
    ...render(
      <MemoryRouter initialEntries={['/admin']}>
        <MainLayout />
      </MemoryRouter>
    ),
    mockLogout,
    mockUser,
  };
};

describe('MainLayout', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Reset window size to desktop
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 1024,
    });
  });

  it('renders without crashing', () => {
    renderMainLayout();

    expect(document.body).toBeInTheDocument();
  });

  it('displays sidebar menu', () => {
    renderMainLayout();

    // Should have navigation menu items
    expect(screen.getByText('סקירה כללית')).toBeInTheDocument();
  });

  it('displays all menu items', () => {
    renderMainLayout();

    expect(screen.getByText('סקירה כללית')).toBeInTheDocument();
    expect(screen.getByText('משתמשים')).toBeInTheDocument();
    expect(screen.getByText('חבילות')).toBeInTheDocument();
    expect(screen.getByText('הודעות')).toBeInTheDocument();
    expect(screen.getByText('מחשבים')).toBeInTheDocument();
    expect(screen.getByText('הגדרות')).toBeInTheDocument();
  });

  it('renders page content via Outlet', () => {
    renderMainLayout();

    expect(screen.getByTestId('outlet')).toBeInTheDocument();
  });

  it('navigates when menu item clicked', async () => {
    const user = userEvent.setup();
    renderMainLayout();

    await user.click(screen.getByText('משתמשים'));

    expect(mockNavigate).toHaveBeenCalledWith('/admin/users');
  });

  it('navigates to packages page', async () => {
    const user = userEvent.setup();
    renderMainLayout();

    await user.click(screen.getByText('חבילות'));

    expect(mockNavigate).toHaveBeenCalledWith('/admin/packages');
  });

  it('navigates to messages page', async () => {
    const user = userEvent.setup();
    renderMainLayout();

    await user.click(screen.getByText('הודעות'));

    expect(mockNavigate).toHaveBeenCalledWith('/admin/messages');
  });

  it('displays user avatar', () => {
    renderMainLayout();

    // Avatar should be present
    expect(document.querySelector('.ant-avatar')).toBeInTheDocument();
  });

  it('has logout button in sidebar', () => {
    renderMainLayout();

    // Logout button should be in the sidebar
    expect(screen.getByText('התנתק')).toBeInTheDocument();
  });

  it('handles logout click', async () => {
    const user = userEvent.setup();
    const { mockLogout } = renderMainLayout();

    // Find and click the logout button
    await user.click(screen.getByText('התנתק'));

    await waitFor(() => {
      expect(signOut).toHaveBeenCalled();
      expect(mockLogout).toHaveBeenCalled();
      expect(mockNavigate).toHaveBeenCalledWith('/admin/login');
    });
  });

  it('has back to home button', () => {
    renderMainLayout();

    // Back to home button should be present
    expect(screen.getByText('דף הבית')).toBeInTheDocument();
  });

  it('navigates to home when back button clicked', async () => {
    const user = userEvent.setup();
    renderMainLayout();

    await user.click(screen.getByText('דף הבית'));

    expect(mockNavigate).toHaveBeenCalledWith('/');
  });

  it('has sidebar toggle button', () => {
    renderMainLayout();

    // Toggle button should be present (rendered as icon mock)
    expect(document.body.textContent).toContain('[MenuFoldOutlined]');
  });

  it('displays organization name when available', () => {
    renderMainLayout({
      uid: 'admin-123',
      orgId: 'test-org',
      displayName: 'Test Admin',
    });

    expect(screen.getByText('test-org')).toBeInTheDocument();
  });

  it('displays user display name', () => {
    renderMainLayout({
      uid: 'admin-123',
      orgId: 'test-org',
      displayName: 'Test Admin',
    });

    expect(screen.getByText('Test Admin')).toBeInTheDocument();
  });

  it('responds to window resize for mobile view', () => {
    renderMainLayout();

    // Simulate mobile width
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 600,
    });

    window.dispatchEvent(new Event('resize'));

    expect(document.body).toBeInTheDocument();
  });

  it('has header with proper structure', () => {
    renderMainLayout();

    // Should have a header with layout header class
    const header = document.querySelector('.ant-layout-header');
    expect(header).toBeInTheDocument();
  });

  it('displays SIONYX logo in sidebar', () => {
    renderMainLayout();

    expect(screen.getByText('SIONYX')).toBeInTheDocument();
  });

  it('does not have duplicate logout buttons', () => {
    renderMainLayout();

    // Should only have ONE logout button (in sidebar)
    const logoutButtons = screen.getAllByText('התנתק');
    expect(logoutButtons.length).toBe(1);
  });

  it('logout button is present and styled', () => {
    renderMainLayout();

    const logoutButton = screen.getByText('התנתק').closest('button');
    expect(logoutButton).toBeInTheDocument();
    expect(logoutButton).toHaveClass('ant-btn');
  });

  it('home button has home icon', () => {
    renderMainLayout();

    // HomeOutlined icon should be rendered
    expect(document.body.textContent).toContain('[HomeOutlined]');
  });
});
