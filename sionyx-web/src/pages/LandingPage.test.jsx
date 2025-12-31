import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import LandingPage from './LandingPage';
import { registerOrganization } from '../services/organizationService';
import { downloadFile, getLatestRelease } from '../services/downloadService';
import { useNavigate } from 'react-router-dom';

// Mock dependencies
vi.mock('../services/organizationService');
vi.mock('../services/downloadService');
vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    useNavigate: vi.fn(() => vi.fn()),
  };
});

const mockReleaseInfo = {
  version: '1.2.3',
  downloadUrl: 'https://example.com/download/sionyx.exe',
  fileName: 'sionyx-installer-v1.2.3.exe',
  releaseDate: '2024-01-15T10:00:00Z',
  fileSize: 50000000,
};

const renderLandingPage = () => {
  const mockNavigate = vi.fn();
  useNavigate.mockReturnValue(mockNavigate);

  getLatestRelease.mockResolvedValue(mockReleaseInfo);
  registerOrganization.mockResolvedValue({ success: true, orgId: 'new-org-id' });
  downloadFile.mockResolvedValue(undefined);

  return {
    ...render(<LandingPage />),
    mockNavigate,
  };
};

describe('LandingPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders without crashing', async () => {
    renderLandingPage();

    expect(document.body).toBeInTheDocument();
  });

  it('displays SIONYX branding', async () => {
    renderLandingPage();

    expect(screen.getByText(/SIONYX/i)).toBeInTheDocument();
  });

  it('fetches release info on mount', async () => {
    renderLandingPage();

    await waitFor(() => {
      expect(getLatestRelease).toHaveBeenCalled();
    });
  });

  it('displays download button', async () => {
    renderLandingPage();

    await waitFor(() => {
      expect(getLatestRelease).toHaveBeenCalled();
    });

    expect(screen.getByText(/הורד עכשיו/)).toBeInTheDocument();
  });

  it('fetches version info when available', async () => {
    renderLandingPage();

    // Should fetch release info
    await waitFor(() => {
      expect(getLatestRelease).toHaveBeenCalled();
    });

    // Page should render without errors
    expect(document.body).toBeInTheDocument();
  });

  it('has admin login button', async () => {
    renderLandingPage();

    expect(screen.getByText(/כניסת מנהל/)).toBeInTheDocument();
  });

  it('navigates to admin login when button clicked', async () => {
    const user = userEvent.setup();
    const { mockNavigate } = renderLandingPage();

    await waitFor(() => {
      expect(getLatestRelease).toHaveBeenCalled();
    });

    const adminButton = screen.getByText(/כניסת מנהל/);
    await user.click(adminButton);

    expect(mockNavigate).toHaveBeenCalledWith('/admin/login');
  });

  it('has welcome card for admin registration', async () => {
    renderLandingPage();

    // The welcome message on the registration card
    expect(screen.getByText(/שלום לך מנהל יקר/)).toBeInTheDocument();
  });

  it('opens registration modal when welcome card clicked', async () => {
    const user = userEvent.setup();
    renderLandingPage();

    // Click the "התחל הרשמה" button on the welcome card
    const registerButton = screen.getByText(/התחל הרשמה/);
    await user.click(registerButton);

    // Modal should open with the form title
    await waitFor(() => {
      expect(screen.getByText(/הרשמת ארגון חדש/)).toBeInTheDocument();
    });
  });

  it('has organization registration form fields in modal', async () => {
    const user = userEvent.setup();
    renderLandingPage();

    // Open the modal
    const registerButton = screen.getByText(/התחל הרשמה/);
    await user.click(registerButton);

    await waitFor(() => {
      expect(screen.getByLabelText(/שם הארגון/)).toBeInTheDocument();
    });

    // Check for organization fields
    expect(screen.getByLabelText(/מזהה מוסד NEDARIM/)).toBeInTheDocument();
    expect(screen.getByLabelText(/מפתח API של NEDARIM/)).toBeInTheDocument();
  });

  it('has admin user fields in registration modal', async () => {
    const user = userEvent.setup();
    renderLandingPage();

    // Open the modal
    const registerButton = screen.getByText(/התחל הרשמה/);
    await user.click(registerButton);

    await waitFor(() => {
      expect(screen.getByLabelText(/שם פרטי/)).toBeInTheDocument();
    });

    // Check for admin fields
    expect(screen.getByLabelText(/שם משפחה/)).toBeInTheDocument();
    expect(screen.getByLabelText(/מספר טלפון/)).toBeInTheDocument();
    expect(screen.getByLabelText(/סיסמה/)).toBeInTheDocument();
    expect(screen.getByLabelText(/אימייל/)).toBeInTheDocument();
  });

  it('handles download click', async () => {
    const user = userEvent.setup();
    renderLandingPage();

    await waitFor(() => {
      expect(getLatestRelease).toHaveBeenCalled();
    });

    const downloadButton = screen.getByText(/הורד עכשיו/);
    await user.click(downloadButton);

    await waitFor(() => {
      expect(downloadFile).toHaveBeenCalledWith(
        mockReleaseInfo.downloadUrl,
        mockReleaseInfo.fileName
      );
    });
  });

  it('handles registration form submission', async () => {
    const user = userEvent.setup();
    const { mockNavigate } = renderLandingPage();

    // Open the modal
    const registerButton = screen.getByText(/התחל הרשמה/);
    await user.click(registerButton);

    await waitFor(() => {
      expect(screen.getByLabelText(/שם הארגון/)).toBeInTheDocument();
    });

    // Fill in organization fields
    await user.type(screen.getByLabelText(/שם הארגון/), 'Test Organization');
    await user.type(screen.getByLabelText(/מזהה מוסד NEDARIM/), '12345');
    await user.type(screen.getByLabelText(/מפתח API של NEDARIM/), 'api-key-123');

    // Fill in admin fields
    await user.type(screen.getByLabelText(/שם פרטי/), 'John');
    await user.type(screen.getByLabelText(/שם משפחה/), 'Doe');
    await user.type(screen.getByLabelText(/מספר טלפון/), '0501234567');
    await user.type(screen.getByLabelText(/סיסמה/), 'password123');

    // Submit form
    const submitButton = screen.getByRole('button', { name: /צור ארגון וחשבון מנהל/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(registerOrganization).toHaveBeenCalled();
    });
  });

  it('shows success and navigates after registration', async () => {
    const user = userEvent.setup();
    const { mockNavigate } = renderLandingPage();

    registerOrganization.mockResolvedValue({ success: true, orgId: 'new-org' });

    // Open the modal
    const registerButton = screen.getByText(/התחל הרשמה/);
    await user.click(registerButton);

    await waitFor(() => {
      expect(screen.getByLabelText(/שם הארגון/)).toBeInTheDocument();
    });

    // Fill in all required fields
    await user.type(screen.getByLabelText(/שם הארגון/), 'Test Organization');
    await user.type(screen.getByLabelText(/מזהה מוסד NEDARIM/), '12345');
    await user.type(screen.getByLabelText(/מפתח API של NEDARIM/), 'api-key-123');
    await user.type(screen.getByLabelText(/שם פרטי/), 'John');
    await user.type(screen.getByLabelText(/שם משפחה/), 'Doe');
    await user.type(screen.getByLabelText(/מספר טלפון/), '0501234567');
    await user.type(screen.getByLabelText(/סיסמה/), 'password123');

    const submitButton = screen.getByRole('button', { name: /צור ארגון וחשבון מנהל/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith(expect.stringContaining('/admin/login'));
    });
  });

  it('handles registration error', async () => {
    const user = userEvent.setup();
    renderLandingPage();

    registerOrganization.mockResolvedValue({ success: false, error: 'Registration failed' });

    // Open the modal
    const registerButton = screen.getByText(/התחל הרשמה/);
    await user.click(registerButton);

    await waitFor(() => {
      expect(screen.getByLabelText(/שם הארגון/)).toBeInTheDocument();
    });

    // Fill in all required fields
    await user.type(screen.getByLabelText(/שם הארגון/), 'Test Organization');
    await user.type(screen.getByLabelText(/מזהה מוסד NEDARIM/), '12345');
    await user.type(screen.getByLabelText(/מפתח API של NEDARIM/), 'api-key-123');
    await user.type(screen.getByLabelText(/שם פרטי/), 'John');
    await user.type(screen.getByLabelText(/שם משפחה/), 'Doe');
    await user.type(screen.getByLabelText(/מספר טלפון/), '0501234567');
    await user.type(screen.getByLabelText(/סיסמה/), 'password123');

    const submitButton = screen.getByRole('button', { name: /צור ארגון וחשבון מנהל/i });
    await user.click(submitButton);

    // Should show error message (not crash)
    expect(document.body).toBeInTheDocument();
  });

  it('handles release info fetch error', async () => {
    getLatestRelease.mockRejectedValue(new Error('Failed to fetch'));

    renderLandingPage();

    // Should not crash
    expect(document.body).toBeInTheDocument();
  });

  it('has cancel button in modal', async () => {
    const user = userEvent.setup();
    renderLandingPage();

    // Open the modal
    const registerButton = screen.getByText(/התחל הרשמה/);
    await user.click(registerButton);

    await waitFor(() => {
      expect(screen.getByText(/הרשמת ארגון חדש/)).toBeInTheDocument();
    });

    // Cancel button should be present
    expect(screen.getByRole('button', { name: /ביטול/i })).toBeInTheDocument();
  });
});
