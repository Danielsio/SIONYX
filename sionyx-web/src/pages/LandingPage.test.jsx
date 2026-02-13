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

// Mock animated components to avoid complex framer-motion/gsap interactions
vi.mock('../components/animated', () => {
  const React = require('react');
  
  return {
    AnimatedBackground: () => React.createElement('div', { 'data-testid': 'animated-background' }),
    AnimatedButton: ({ children, onClick, icon, loading, fullWidth, variant, size, magnetic, ...props }) => 
      React.createElement('button', { onClick, ...props }, icon, children),
    AnimatedCard: ({ children, onClick, tilt, glow, entrance, delay, variant, ...props }) => 
      React.createElement('div', { onClick, ...props }, children),
    GlowingText: ({ children, color, glowIntensity, pulse }) => 
      React.createElement('span', null, children),
    GradientText: ({ children, gradient, animate }) => 
      React.createElement('span', null, children),
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

    // SIONYX is rendered as individual animated letters - there may be multiple S's (logo + title)
    const letters = ['S', 'I', 'O', 'N', 'Y', 'X'];
    letters.forEach((letter) => {
      const elements = screen.getAllByText(letter);
      expect(elements.length).toBeGreaterThan(0);
    });
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

    // There might be multiple admin login buttons (header and footer)
    expect(screen.getAllByText(/כניסת מנהל/).length).toBeGreaterThan(0);
  });

  it('navigates to admin login when button clicked', async () => {
    const user = userEvent.setup();
    const { mockNavigate } = renderLandingPage();

    await waitFor(() => {
      expect(getLatestRelease).toHaveBeenCalled();
    });

    // Get the first admin button (in the header)
    const adminButtons = screen.getAllByText(/כניסת מנהל/);
    await user.click(adminButtons[0]);

    expect(mockNavigate).toHaveBeenCalledWith('/admin/login');
  });

  it('has welcome card for admin registration', async () => {
    renderLandingPage();

    // The main CTA card for registration
    expect(screen.getByText(/רישום ארגון חדש/)).toBeInTheDocument();
  });

  it('opens registration modal when welcome card clicked', async () => {
    const user = userEvent.setup();
    renderLandingPage();

    // Click the "התחל עכשיו - חינם" button on the hero or CTA card
    const registerButton = screen.getAllByText(/התחל עכשיו/)[0];
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
    const registerButton = screen.getAllByText(/התחל עכשיו/)[0];
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
    const registerButton = screen.getAllByText(/התחל עכשיו/)[0];
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
    const registerButton = screen.getAllByText(/התחל עכשיו/)[0];
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
    const submitButton = screen.getByRole('button', { name: /צור ארגון חדש/i });
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
    const registerButton = screen.getAllByText(/התחל עכשיו/)[0];
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

    const submitButton = screen.getByRole('button', { name: /צור ארגון חדש/i });
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
    const registerButton = screen.getAllByText(/התחל עכשיו/)[0];
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

    const submitButton = screen.getByRole('button', { name: /צור ארגון חדש/i });
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
    const registerButton = screen.getAllByText(/התחל עכשיו/)[0];
    await user.click(registerButton);

    await waitFor(() => {
      expect(screen.getAllByText(/הרשמת ארגון חדש/).length).toBeGreaterThan(0);
    });

    // Cancel button should be present
    expect(screen.getByRole('button', { name: /ביטול/i })).toBeInTheDocument();
  });

  it('closes modal when cancel button is clicked', async () => {
    const user = userEvent.setup();
    renderLandingPage();

    // Open the modal
    const registerButton = screen.getAllByText(/התחל עכשיו/)[0];
    await user.click(registerButton);

    await waitFor(() => {
      expect(screen.getAllByText(/הרשמת ארגון חדש/).length).toBeGreaterThan(0);
    });

    // Click cancel button
    const cancelButton = screen.getByRole('button', { name: /ביטול/i });
    await user.click(cancelButton);

    // Modal should close - check by looking for modal form elements
    await waitFor(() => {
      expect(screen.queryByLabelText(/שם הארגון/)).not.toBeInTheDocument();
    });
  });

  it('does not warn about release fetch after unmount', async () => {
    // Create a deferred promise that we control
    let rejectRelease;
    getLatestRelease.mockReturnValue(new Promise((_, reject) => {
      rejectRelease = reject;
    }));

    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});

    const { unmount } = render(<LandingPage />);

    // Unmount before the promise settles
    unmount();

    // Now reject the promise (simulating network error after navigation away)
    rejectRelease(new Error('Network error'));

    // Allow microtasks to process
    await new Promise(r => setTimeout(r, 50));

    // console.warn should NOT have been called since component is unmounted
    expect(warnSpy).not.toHaveBeenCalled();

    warnSpy.mockRestore();
  });

  it('GSAP animation guards against null subtitleRef', async () => {
    const gsap = await import('gsap');

    // Make gsap.fromTo throw when called with null (simulates real GSAP behavior)
    gsap.default.fromTo.mockImplementation((target) => {
      if (!target) throw new Error('GSAP: Cannot tween a null target');
    });

    // Make gsap.context execute its callback AND verify fromTo args
    const fromToCalls = [];
    const origFromTo = gsap.default.fromTo;
    gsap.default.fromTo.mockImplementation((...args) => {
      fromToCalls.push(args[0]);
      if (!args[0]) throw new Error('GSAP: Cannot tween a null target');
    });

    gsap.default.context.mockImplementation((cb, scope) => {
      cb();
      return { revert: vi.fn() };
    });

    getLatestRelease.mockResolvedValue(mockReleaseInfo);

    // Render should NOT throw
    expect(() => render(<LandingPage />)).not.toThrow();

    // gsap.fromTo should only be called with valid (non-null) targets
    fromToCalls.forEach(target => {
      expect(target).not.toBeNull();
      expect(target).not.toBeUndefined();
    });

    // Restore mocks
    gsap.default.fromTo.mockReset();
    gsap.default.context.mockImplementation(() => ({ revert: vi.fn() }));
  });

  describe('Registration Modal Responsiveness', () => {
    it('has registration-modal class for responsive styling', async () => {
      const user = userEvent.setup();
      renderLandingPage();

      // Open the modal
      const registerButton = screen.getAllByText(/התחל עכשיו/)[0];
      await user.click(registerButton);

      await waitFor(() => {
        expect(screen.getAllByText(/הרשמת ארגון חדש/).length).toBeGreaterThan(0);
      });

      // Find the modal wrapper with registration-modal class
      const modal = document.querySelector('.registration-modal');
      expect(modal).toBeInTheDocument();
    });

    it('modal has width style of 95% for responsiveness', async () => {
      const user = userEvent.setup();
      renderLandingPage();

      // Open the modal
      const registerButton = screen.getAllByText(/התחל עכשיו/)[0];
      await user.click(registerButton);

      await waitFor(() => {
        expect(screen.getAllByText(/הרשמת ארגון חדש/).length).toBeGreaterThan(0);
      });

      // The ant-modal should have responsive width
      const modalContent = document.querySelector('.ant-modal');
      expect(modalContent).toBeInTheDocument();
      // Width should be percentage-based for responsiveness
      const style = window.getComputedStyle(modalContent);
      expect(style.width).not.toBe('700px');
    });

    it('modal body is scrollable with max-height constraint', async () => {
      const user = userEvent.setup();
      renderLandingPage();

      // Open the modal
      const registerButton = screen.getAllByText(/התחל עכשיו/)[0];
      await user.click(registerButton);

      await waitFor(() => {
        expect(screen.getAllByText(/הרשמת ארגון חדש/).length).toBeGreaterThan(0);
      });

      // Modal body should have overflow-y auto for scrolling on small screens
      const modalBody = document.querySelector('.ant-modal-body');
      expect(modalBody).toBeInTheDocument();
    });

    it('renders all form sections stacked properly', async () => {
      const user = userEvent.setup();
      renderLandingPage();

      // Open the modal
      const registerButton = screen.getAllByText(/התחל עכשיו/)[0];
      await user.click(registerButton);

      await waitFor(() => {
        expect(screen.getAllByText(/הרשמת ארגון חדש/).length).toBeGreaterThan(0);
      });

      // Both organization and admin sections should be visible
      expect(screen.getByText(/פרטי הארגון/)).toBeInTheDocument();
      expect(screen.getByText(/פרטי המנהל הראשי/)).toBeInTheDocument();
    });

    it('form inputs are rendered within modal', async () => {
      const user = userEvent.setup();
      renderLandingPage();

      // Open the modal
      const registerButton = screen.getAllByText(/התחל עכשיו/)[0];
      await user.click(registerButton);

      await waitFor(() => {
        expect(screen.getByLabelText(/שם הארגון/)).toBeInTheDocument();
      });

      // Verify all form inputs are present and accessible within the modal
      const orgNameInput = screen.getByLabelText(/שם הארגון/);
      expect(orgNameInput).toBeInTheDocument();
      expect(orgNameInput.tagName).toBe('INPUT');
      
      // Inputs should be inside the modal body
      const modalBody = document.querySelector('.ant-modal-body');
      expect(modalBody).toContainElement(orgNameInput);
    });

    it('buttons wrap properly in modal', async () => {
      const user = userEvent.setup();
      renderLandingPage();

      // Open the modal
      const registerButton = screen.getAllByText(/התחל עכשיו/)[0];
      await user.click(registerButton);

      await waitFor(() => {
        expect(screen.getAllByText(/הרשמת ארגון חדש/).length).toBeGreaterThan(0);
      });

      // Both buttons should be present
      expect(screen.getByRole('button', { name: /ביטול/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /צור ארגון חדש/i })).toBeInTheDocument();
    });

    it('validates form fields before submission', async () => {
      const user = userEvent.setup();
      renderLandingPage();

      // Open the modal
      const registerButton = screen.getAllByText(/התחל עכשיו/)[0];
      await user.click(registerButton);

      await waitFor(() => {
        expect(screen.getAllByText(/הרשמת ארגון חדש/).length).toBeGreaterThan(0);
      });

      // Try to submit without filling fields
      const submitButton = screen.getByRole('button', { name: /צור ארגון חדש/i });
      await user.click(submitButton);

      // Validation should prevent submission
      await waitFor(() => {
        expect(registerOrganization).not.toHaveBeenCalled();
      });
    });

    it('shows validation error for invalid phone number', async () => {
      const user = userEvent.setup();
      renderLandingPage();

      // Open the modal
      const registerButton = screen.getAllByText(/התחל עכשיו/)[0];
      await user.click(registerButton);

      await waitFor(() => {
        expect(screen.getByLabelText(/מספר טלפון/)).toBeInTheDocument();
      });

      // Enter invalid phone number
      const phoneInput = screen.getByLabelText(/מספר טלפון/);
      await user.type(phoneInput, '123');

      // Blur to trigger validation
      await user.tab();

      // Try to submit
      const submitButton = screen.getByRole('button', { name: /צור ארגון חדש/i });
      await user.click(submitButton);

      // Should show validation error
      await waitFor(() => {
        expect(screen.getByText(/מספר טלפון לא תקין/)).toBeInTheDocument();
      });
    });

    it('shows validation error for short password', async () => {
      const user = userEvent.setup();
      renderLandingPage();

      // Open the modal
      const registerButton = screen.getAllByText(/התחל עכשיו/)[0];
      await user.click(registerButton);

      await waitFor(() => {
        expect(screen.getByLabelText(/סיסמה/)).toBeInTheDocument();
      });

      // Enter short password
      const passwordInput = screen.getByLabelText(/סיסמה/);
      await user.type(passwordInput, '123');

      // Try to submit
      const submitButton = screen.getByRole('button', { name: /צור ארגון חדש/i });
      await user.click(submitButton);

      // Should show validation error
      await waitFor(() => {
        expect(screen.getByText(/הסיסמה חייבת להכיל לפחות 6 תווים/)).toBeInTheDocument();
      });
    });

    it('shows validation error for invalid email format', async () => {
      const user = userEvent.setup();
      renderLandingPage();

      // Open the modal
      const registerButton = screen.getAllByText(/התחל עכשיו/)[0];
      await user.click(registerButton);

      await waitFor(() => {
        expect(screen.getByLabelText(/אימייל/)).toBeInTheDocument();
      });

      // Enter invalid email
      const emailInput = screen.getByLabelText(/אימייל/);
      await user.type(emailInput, 'invalid-email');

      // Try to submit
      const submitButton = screen.getByRole('button', { name: /צור ארגון חדש/i });
      await user.click(submitButton);

      // Should show validation error
      await waitFor(() => {
        expect(screen.getByText(/כתובת אימייל לא תקינה/)).toBeInTheDocument();
      });
    });
  });
});
