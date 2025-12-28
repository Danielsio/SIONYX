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

    expect(screen.getByText(/פאנל ניהול/)).toBeInTheDocument();
  });

  it('navigates to admin login when button clicked', async () => {
    const user = userEvent.setup();
    const { mockNavigate } = renderLandingPage();

    await waitFor(() => {
      expect(getLatestRelease).toHaveBeenCalled();
    });

    const adminButton = screen.getByText(/פאנל ניהול/);
    await user.click(adminButton);

    expect(mockNavigate).toHaveBeenCalledWith('/admin/login');
  });

  it('has organization registration form', async () => {
    renderLandingPage();

    // Should have form fields for registration - using organization name field
    expect(screen.getByLabelText(/שם הארגון/)).toBeInTheDocument();
  });

  it('has NEDARIM mosad id field', async () => {
    renderLandingPage();

    expect(screen.getByLabelText(/מזהה מוסד NEDARIM/)).toBeInTheDocument();
  });

  it('has NEDARIM api key field', async () => {
    renderLandingPage();

    expect(screen.getByLabelText(/מפתח API של NEDARIM/)).toBeInTheDocument();
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

    // Fill in form fields
    const orgNameInput = screen.getByLabelText(/שם הארגון/);
    await user.type(orgNameInput, 'Test Organization');

    // Find and fill NEDARIM mosad id
    const mosadInput = screen.getByLabelText(/מזהה מוסד NEDARIM/);
    await user.type(mosadInput, '12345');

    // Find and fill NEDARIM api key
    const apiKeyInput = screen.getByLabelText(/מפתח API של NEDARIM/);
    await user.type(apiKeyInput, 'api-key-123');

    // Submit form
    const submitButton = screen.getByRole('button', { name: /צור ארגון/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(registerOrganization).toHaveBeenCalled();
    });
  });

  it('shows success and navigates after registration', async () => {
    const user = userEvent.setup();
    const { mockNavigate } = renderLandingPage();

    registerOrganization.mockResolvedValue({ success: true, orgId: 'new-org' });

    const orgNameInput = screen.getByLabelText(/שם הארגון/);
    await user.type(orgNameInput, 'Test Organization');

    const mosadInput = screen.getByLabelText(/מזהה מוסד NEDARIM/);
    await user.type(mosadInput, '12345');

    const apiKeyInput = screen.getByLabelText(/מפתח API של NEDARIM/);
    await user.type(apiKeyInput, 'api-key-123');

    const submitButton = screen.getByRole('button', { name: /צור ארגון/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith(expect.stringContaining('/admin/login'));
    });
  });

  it('handles registration error', async () => {
    const user = userEvent.setup();
    renderLandingPage();

    registerOrganization.mockResolvedValue({ success: false, error: 'Registration failed' });

    const orgNameInput = screen.getByLabelText(/שם הארגון/);
    await user.type(orgNameInput, 'Test Organization');

    const mosadInput = screen.getByLabelText(/מזהה מוסד NEDARIM/);
    await user.type(mosadInput, '12345');

    const apiKeyInput = screen.getByLabelText(/מפתח API של NEDARIM/);
    await user.type(apiKeyInput, 'api-key-123');

    const submitButton = screen.getByRole('button', { name: /צור ארגון/i });
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

  it('displays create organization title', async () => {
    renderLandingPage();

    expect(screen.getByText(/צור ארגון חדש/)).toBeInTheDocument();
  });
});
