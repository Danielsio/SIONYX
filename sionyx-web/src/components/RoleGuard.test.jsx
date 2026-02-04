import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import RoleGuard from './RoleGuard';
import { useAuthStore } from '../store/authStore';
import { ROLES } from '../utils/roles';

vi.mock('../store/authStore');

describe('RoleGuard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const mockUser = role => {
    useAuthStore.mockImplementation(selector => {
      const state = { user: role ? { role } : null };
      return selector(state);
    });
  };

  it('renders children when user has required role', () => {
    mockUser('admin');

    render(
      <RoleGuard requiredRole={ROLES.ADMIN}>
        <div data-testid='protected-content'>Protected Content</div>
      </RoleGuard>
    );

    expect(screen.getByTestId('protected-content')).toBeInTheDocument();
  });

  it('renders children when user has higher role', () => {
    mockUser('supervisor');

    render(
      <RoleGuard requiredRole={ROLES.ADMIN}>
        <div data-testid='protected-content'>Protected Content</div>
      </RoleGuard>
    );

    expect(screen.getByTestId('protected-content')).toBeInTheDocument();
  });

  it('does not render children when user has lower role', () => {
    mockUser('user');

    render(
      <RoleGuard requiredRole={ROLES.ADMIN}>
        <div data-testid='protected-content'>Protected Content</div>
      </RoleGuard>
    );

    expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
  });

  it('renders fallback when user lacks permission', () => {
    mockUser('user');

    render(
      <RoleGuard 
        requiredRole={ROLES.SUPERVISOR} 
        fallback={<div data-testid='fallback'>Access Denied</div>}
      >
        <div data-testid='protected-content'>Protected Content</div>
      </RoleGuard>
    );

    expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
    expect(screen.getByTestId('fallback')).toBeInTheDocument();
  });

  it('renders null fallback by default', () => {
    mockUser('user');

    const { container } = render(
      <RoleGuard requiredRole={ROLES.ADMIN}>
        <div data-testid='protected-content'>Protected Content</div>
      </RoleGuard>
    );

    expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
    expect(container.firstChild).toBeNull();
  });

  it('handles null user', () => {
    mockUser(null);

    render(
      <RoleGuard requiredRole={ROLES.ADMIN}>
        <div data-testid='protected-content'>Protected Content</div>
      </RoleGuard>
    );

    expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
  });

  it('works with isAdmin fallback for backwards compatibility', () => {
    useAuthStore.mockImplementation(selector => {
      const state = { user: { isAdmin: true } };
      return selector(state);
    });

    render(
      <RoleGuard requiredRole={ROLES.ADMIN}>
        <div data-testid='protected-content'>Protected Content</div>
      </RoleGuard>
    );

    expect(screen.getByTestId('protected-content')).toBeInTheDocument();
  });

  it('restricts supervisor content from admin', () => {
    mockUser('admin');

    render(
      <RoleGuard requiredRole={ROLES.SUPERVISOR}>
        <div data-testid='supervisor-content'>Supervisor Only</div>
      </RoleGuard>
    );

    expect(screen.queryByTestId('supervisor-content')).not.toBeInTheDocument();
  });

  it('allows supervisor to see supervisor content', () => {
    mockUser('supervisor');

    render(
      <RoleGuard requiredRole={ROLES.SUPERVISOR}>
        <div data-testid='supervisor-content'>Supervisor Only</div>
      </RoleGuard>
    );

    expect(screen.getByTestId('supervisor-content')).toBeInTheDocument();
  });
});
