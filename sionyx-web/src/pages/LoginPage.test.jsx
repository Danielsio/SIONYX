import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { ConfigProvider, App as AntApp } from 'antd';
import LoginPage from './LoginPage';
import { signInAdmin } from '../services/authService';
import { useAuthStore } from '../store/authStore';

// Mock dependencies
vi.mock('../services/authService');
vi.mock('../store/authStore');

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

const renderLoginPage = () => {
  const mockSetUser = vi.fn();
  useAuthStore.mockImplementation((selector) => {
    const state = { setUser: mockSetUser };
    return selector(state);
  });

  return {
    ...render(
      <MemoryRouter>
        <ConfigProvider>
          <AntApp>
            <LoginPage />
          </AntApp>
        </ConfigProvider>
      </MemoryRouter>
    ),
    mockSetUser,
  };
};

describe('LoginPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders login form', () => {
    renderLoginPage();

    expect(screen.getByText('SIONYX מנהל')).toBeInTheDocument();
  });

  it('renders org ID input field', () => {
    renderLoginPage();

    expect(screen.getByLabelText(/מזהה ארגון/)).toBeInTheDocument();
  });

  it('renders phone input field', () => {
    renderLoginPage();

    expect(screen.getByLabelText(/מספר טלפון/)).toBeInTheDocument();
  });

  it('renders password input field', () => {
    renderLoginPage();

    expect(screen.getByLabelText(/סיסמה/)).toBeInTheDocument();
  });

  it('renders submit button', () => {
    renderLoginPage();

    expect(screen.getByRole('button', { name: /התחבר/ })).toBeInTheDocument();
  });

  it('calls signInAdmin on form submit with valid data', async () => {
    const user = userEvent.setup();
    signInAdmin.mockResolvedValue({ success: true, user: { uid: '123' } });
    
    renderLoginPage();

    await user.type(screen.getByLabelText(/מזהה ארגון/), 'my-org');
    await user.type(screen.getByLabelText(/מספר טלפון/), '1234567890');
    await user.type(screen.getByLabelText(/סיסמה/), 'password');
    
    await user.click(screen.getByRole('button', { name: /התחבר/ }));

    await waitFor(() => {
      expect(signInAdmin).toHaveBeenCalledWith('1234567890', 'password', 'my-org');
    });
  });

  it('navigates to admin on successful login', async () => {
    const user = userEvent.setup();
    signInAdmin.mockResolvedValue({ success: true, user: { uid: '123' } });
    
    renderLoginPage();

    await user.type(screen.getByLabelText(/מזהה ארגון/), 'my-org');
    await user.type(screen.getByLabelText(/מספר טלפון/), '1234567890');
    await user.type(screen.getByLabelText(/סיסמה/), 'password');
    
    await user.click(screen.getByRole('button', { name: /התחבר/ }));

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/admin');
    });
  });

  it('sets user in store on successful login', async () => {
    const user = userEvent.setup();
    const mockUser = { uid: '123', orgId: 'my-org' };
    signInAdmin.mockResolvedValue({ success: true, user: mockUser });
    
    const { mockSetUser } = renderLoginPage();

    await user.type(screen.getByLabelText(/מזהה ארגון/), 'my-org');
    await user.type(screen.getByLabelText(/מספר טלפון/), '1234567890');
    await user.type(screen.getByLabelText(/סיסמה/), 'password');
    
    await user.click(screen.getByRole('button', { name: /התחבר/ }));

    await waitFor(() => {
      expect(mockSetUser).toHaveBeenCalledWith(mockUser);
    });
  });

  it('does not navigate on failed login', async () => {
    const user = userEvent.setup();
    signInAdmin.mockResolvedValue({ 
      success: false, 
      error: 'Invalid credentials' 
    });
    
    renderLoginPage();

    await user.type(screen.getByLabelText(/מזהה ארגון/), 'my-org');
    await user.type(screen.getByLabelText(/מספר טלפון/), '1234567890');
    await user.type(screen.getByLabelText(/סיסמה/), 'wrong');
    
    await user.click(screen.getByRole('button', { name: /התחבר/ }));

    await waitFor(() => {
      expect(signInAdmin).toHaveBeenCalled();
    });

    // Should not navigate on failure
    expect(mockNavigate).not.toHaveBeenCalledWith('/admin');
  });

  it('renders help text about org ID', () => {
    renderLoginPage();

    expect(screen.getByText(/איפה למצוא את מזהה הארגון שלך/)).toBeInTheDocument();
  });
});
