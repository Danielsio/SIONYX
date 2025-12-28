import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import App from '../App';

// Mock the auth store
vi.mock('../store/authStore', () => ({
  useAuthStore: vi.fn((selector) => {
    const state = {
      user: null,
      isAuthenticated: false,
      isLoading: false,
      setUser: vi.fn(),
      setLoading: vi.fn(),
      logout: vi.fn(),
    };
    return selector ? selector(state) : state;
  }),
}));

// Mock the auth service
vi.mock('../services/authService', () => ({
  onAuthChange: vi.fn((callback) => {
    // Simulate unauthenticated state
    callback(null);
    return vi.fn(); // Return unsubscribe function
  }),
  getCurrentAdminData: vi.fn(),
  signInAdmin: vi.fn(),
  signOut: vi.fn(),
}));

// Mock lazy-loaded pages to avoid async loading issues in tests
vi.mock('../pages/LandingPage', () => ({
  default: () => <div data-testid="landing-page">Landing Page</div>,
}));

vi.mock('../pages/LoginPage', () => ({
  default: () => <div data-testid="login-page">Login Page</div>,
}));

vi.mock('../pages/OverviewPage', () => ({
  default: () => <div data-testid="overview-page">Overview Page</div>,
}));

vi.mock('../pages/UsersPage', () => ({
  default: () => <div data-testid="users-page">Users Page</div>,
}));

vi.mock('../pages/PackagesPage', () => ({
  default: () => <div data-testid="packages-page">Packages Page</div>,
}));

vi.mock('../pages/MessagesPage', () => ({
  default: () => <div data-testid="messages-page">Messages Page</div>,
}));

vi.mock('../pages/ComputersPage', () => ({
  default: () => <div data-testid="computers-page">Computers Page</div>,
}));

vi.mock('../pages/PricingPage', () => ({
  default: () => <div data-testid="pricing-page">Pricing Page</div>,
}));

describe('App', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders without crashing', () => {
    render(<App />);
    expect(document.body).toBeInTheDocument();
  });

  it('shows landing page on root route', async () => {
    render(<App />);
    
    // Wait for the landing page to appear (lazy loaded)
    const landingPage = await screen.findByTestId('landing-page');
    expect(landingPage).toBeInTheDocument();
  });

  it('shows login page on /admin/login route when not authenticated', async () => {
    // Create a custom App wrapper with MemoryRouter for controlled routing
    render(
      <MemoryRouter initialEntries={['/admin/login']}>
        <AppRoutes />
      </MemoryRouter>
    );
    
    // The login page should be rendered
    const loginPage = await screen.findByTestId('login-page');
    expect(loginPage).toBeInTheDocument();
  });
});

// Helper component that contains just the routes without the router
// This allows us to use MemoryRouter in tests
function AppRoutes() {
  const { useAuthStore } = require('../store/authStore');
  const { Routes, Route, Navigate } = require('react-router-dom');
  const { Suspense, lazy } = require('react');

  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  const LandingPage = lazy(() => import('../pages/LandingPage'));
  const LoginPage = lazy(() => import('../pages/LoginPage'));

  return (
    <Suspense fallback={<div>Loading...</div>}>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route
          path="/admin/login"
          element={isAuthenticated ? <Navigate to="/admin" replace /> : <LoginPage />}
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  );
}
