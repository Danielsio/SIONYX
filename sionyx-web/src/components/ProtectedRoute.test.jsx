import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import ProtectedRoute from './ProtectedRoute';
import { useAuthStore } from '../store/authStore';

// Mock the auth store
vi.mock('../store/authStore', () => ({
  useAuthStore: vi.fn(),
}));

describe('ProtectedRoute', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const renderWithRouter = (
    isAuthenticated,
    initialRoute = '/protected',
    { isLoading = false, user = null } = {}
  ) => {
    useAuthStore.mockImplementation(selector => {
      const state = { isAuthenticated, isLoading, user };
      return selector(state);
    });

    return render(
      <MemoryRouter initialEntries={[initialRoute]}>
        <Routes>
          <Route path='/admin/login' element={<div data-testid='login-page'>Login Page</div>} />
          <Route
            path='/protected'
            element={
              <ProtectedRoute>
                <div data-testid='protected-content'>Protected Content</div>
              </ProtectedRoute>
            }
          />
        </Routes>
      </MemoryRouter>
    );
  };

  it('renders children when authenticated and user is admin', () => {
    renderWithRouter(true, '/protected', {
      isLoading: false,
      user: { isAdmin: true, role: 'admin' },
    });

    expect(screen.getByTestId('protected-content')).toBeInTheDocument();
    expect(screen.queryByTestId('login-page')).not.toBeInTheDocument();
  });

  it('redirects to /admin/login when not authenticated', () => {
    renderWithRouter(false, '/protected', { isLoading: false, user: null });

    expect(screen.getByTestId('login-page')).toBeInTheDocument();
    expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
  });

  it('shows loading spinner when isLoading', () => {
    const { container } = renderWithRouter(true, '/protected', {
      isLoading: true,
      user: { isAdmin: true, role: 'admin' },
    });

    expect(container.querySelector('.ant-spin')).toBeInTheDocument();
    expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
    expect(screen.queryByTestId('login-page')).not.toBeInTheDocument();
  });

  it('redirects when authenticated but user is not admin', () => {
    renderWithRouter(true, '/protected', {
      isLoading: false,
      user: { role: 'user', isAdmin: false },
    });

    expect(screen.getByTestId('login-page')).toBeInTheDocument();
    expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
  });

  it('uses selector to get isAuthenticated from store', () => {
    renderWithRouter(true, '/protected', {
      isLoading: false,
      user: { isAdmin: true, role: 'admin' },
    });

    expect(useAuthStore).toHaveBeenCalled();
    // Verify it's using a selector function
    expect(typeof useAuthStore.mock.calls[0][0]).toBe('function');
  });
});
