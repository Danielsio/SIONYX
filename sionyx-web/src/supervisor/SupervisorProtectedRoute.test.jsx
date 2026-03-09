import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import SupervisorProtectedRoute from './SupervisorProtectedRoute';
import { useSupervisorAuthStore } from './store/supervisorAuthStore';

vi.mock('./store/supervisorAuthStore');

describe('SupervisorProtectedRoute', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const mockAuthState = (isAuthenticated, isLoading = false) => {
    useSupervisorAuthStore.mockImplementation(selector => {
      const state = { isAuthenticated, isLoading };
      return selector(state);
    });
  };

  it('renders children when authenticated', () => {
    mockAuthState(true);

    render(
      <MemoryRouter>
        <SupervisorProtectedRoute>
          <div data-testid='protected-content'>Protected Content</div>
        </SupervisorProtectedRoute>
      </MemoryRouter>
    );

    expect(screen.getByTestId('protected-content')).toBeInTheDocument();
    expect(screen.getByText('Protected Content')).toBeInTheDocument();
  });

  it('redirects to /supervisor/login when not authenticated', () => {
    mockAuthState(false);

    render(
      <MemoryRouter initialEntries={['/supervisor/dashboard']}>
        <Routes>
          <Route path='/supervisor/login' element={<div data-testid='login-page'>Login Page</div>} />
          <Route
            path='*'
            element={
              <SupervisorProtectedRoute>
                <div data-testid='protected-content'>Protected Content</div>
              </SupervisorProtectedRoute>
            }
          />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
    expect(screen.getByTestId('login-page')).toBeInTheDocument();
    expect(screen.getByText('Login Page')).toBeInTheDocument();
  });

  it('shows spinner when loading', () => {
    mockAuthState(false, true);

    const { container } = render(
      <MemoryRouter>
        <SupervisorProtectedRoute>
          <div data-testid='protected-content'>Protected Content</div>
        </SupervisorProtectedRoute>
      </MemoryRouter>
    );

    expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
    expect(container.querySelector('.ant-spin')).toBeInTheDocument();
  });
});
