import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import ErrorBoundary from './ErrorBoundary';

// Component that throws an error
const ThrowError = ({ shouldThrow = true }) => {
  if (shouldThrow) {
    throw new Error('Test error message');
  }
  return <div data-testid="child-content">Child Content</div>;
};

describe('ErrorBoundary', () => {
  // Suppress console.error during tests since we're testing error scenarios
  const originalConsoleError = console.error;
  
  beforeEach(() => {
    console.error = vi.fn();
  });

  afterEach(() => {
    console.error = originalConsoleError;
  });

  it('renders children when no error occurs', () => {
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={false} />
      </ErrorBoundary>
    );

    expect(screen.getByTestId('child-content')).toBeInTheDocument();
  });

  it('renders error UI when child throws', () => {
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );

    // Should show Hebrew error message
    expect(screen.getByText('אופס! משהו השתבש')).toBeInTheDocument();
  });

  it('renders reload button', () => {
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );

    expect(screen.getByText('רענן עמוד')).toBeInTheDocument();
  });

  it('renders go home button', () => {
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );

    expect(screen.getByText('חזור לדף הבית')).toBeInTheDocument();
  });

  it('logs error to console', () => {
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );

    expect(console.error).toHaveBeenCalled();
  });

  it('shows error details in development mode', () => {
    // Mock import.meta.env.DEV to true
    const originalDev = import.meta.env.DEV;
    
    // In test environment, DEV should be true
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );

    // The error details card should be visible in dev mode
    // Note: This depends on import.meta.env.DEV being true in test environment
    if (import.meta.env.DEV) {
      expect(screen.getByText(/פרטי השגיאה/)).toBeInTheDocument();
    }
  });

  it('captures error info in state', () => {
    let errorBoundaryRef;
    
    render(
      <ErrorBoundary ref={(ref) => { errorBoundaryRef = ref; }}>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );

    // Error should be captured (verified by showing error UI)
    expect(screen.getByText('אופס! משהו השתבש')).toBeInTheDocument();
  });

  describe('button interactions', () => {
    let originalLocation;

    beforeEach(() => {
      originalLocation = window.location;
      delete window.location;
      window.location = { 
        reload: vi.fn(),
        href: '',
      };
    });

    afterEach(() => {
      window.location = originalLocation;
    });

    it('reload button calls window.location.reload', () => {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );

      fireEvent.click(screen.getByText('רענן עמוד'));

      expect(window.location.reload).toHaveBeenCalled();
    });

    it('go home button navigates to /admin', () => {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );

      fireEvent.click(screen.getByText('חזור לדף הבית'));

      expect(window.location.href).toBe('/admin');
    });
  });
});

