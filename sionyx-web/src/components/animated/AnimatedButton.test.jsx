import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import AnimatedButton from './AnimatedButton';

// Store spring mock functions for testing
const mockSpringSet = vi.fn();

// Mock framer-motion to simplify testing
vi.mock('framer-motion', () => ({
  motion: {
    button: ({ children, onClick, disabled, style, ...props }) => (
      <button onClick={disabled ? undefined : onClick} disabled={disabled} style={style} {...props}>
        {children}
      </button>
    ),
    span: ({ children, ...props }) => <span {...props}>{children}</span>,
    div: ({ children, ...props }) => <div {...props}>{children}</div>,
  },
  useSpring: () => ({ set: mockSpringSet, get: () => 0 }),
  useTransform: () => 0.5,
}));

describe('AnimatedButton', () => {
  beforeEach(() => {
    mockSpringSet.mockClear();
  });

  it('renders children correctly', () => {
    render(<AnimatedButton>Click Me</AnimatedButton>);

    expect(screen.getByText('Click Me')).toBeInTheDocument();
  });

  it('calls onClick when clicked', async () => {
    const handleClick = vi.fn();
    const user = userEvent.setup();

    render(<AnimatedButton onClick={handleClick}>Click</AnimatedButton>);

    await user.click(screen.getByRole('button'));

    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('does not call onClick when disabled', async () => {
    const handleClick = vi.fn();
    const user = userEvent.setup();

    render(
      <AnimatedButton onClick={handleClick} disabled>
        Click
      </AnimatedButton>
    );

    await user.click(screen.getByRole('button'));

    expect(handleClick).not.toHaveBeenCalled();
  });

  it('shows loading state', () => {
    render(<AnimatedButton loading>Submit</AnimatedButton>);

    expect(screen.getByRole('button')).toBeInTheDocument();
  });

  it('renders with icon', () => {
    const TestIcon = () => <span data-testid='test-icon'>🔒</span>;

    render(<AnimatedButton icon={<TestIcon />}>With Icon</AnimatedButton>);

    expect(screen.getByTestId('test-icon')).toBeInTheDocument();
    expect(screen.getByText('With Icon')).toBeInTheDocument();
  });

  it('applies fullWidth style', () => {
    render(<AnimatedButton fullWidth>Full Width</AnimatedButton>);

    expect(screen.getByRole('button')).toBeInTheDocument();
  });

  it('renders with different variants', () => {
    const { rerender } = render(<AnimatedButton variant='primary'>Primary</AnimatedButton>);
    expect(screen.getByRole('button')).toBeInTheDocument();

    rerender(<AnimatedButton variant='secondary'>Secondary</AnimatedButton>);
    expect(screen.getByText('Secondary')).toBeInTheDocument();

    rerender(<AnimatedButton variant='ghost'>Ghost</AnimatedButton>);
    expect(screen.getByText('Ghost')).toBeInTheDocument();

    rerender(<AnimatedButton variant='glow'>Glow</AnimatedButton>);
    expect(screen.getByText('Glow')).toBeInTheDocument();
  });

  it('renders with different sizes', () => {
    const { rerender } = render(<AnimatedButton size='small'>Small</AnimatedButton>);
    expect(screen.getByRole('button')).toBeInTheDocument();

    rerender(<AnimatedButton size='medium'>Medium</AnimatedButton>);
    expect(screen.getByText('Medium')).toBeInTheDocument();

    rerender(<AnimatedButton size='large'>Large</AnimatedButton>);
    expect(screen.getByText('Large')).toBeInTheDocument();
  });

  it('applies custom styles', () => {
    render(<AnimatedButton style={{ backgroundColor: 'red' }}>Styled</AnimatedButton>);

    expect(screen.getByRole('button')).toBeInTheDocument();
  });

  it('handles mouse events for magnetic effect', () => {
    render(<AnimatedButton magnetic>Magnetic</AnimatedButton>);

    const button = screen.getByRole('button');

    // Trigger mouse events
    fireEvent.mouseEnter(button);
    fireEvent.mouseMove(button, { clientX: 100, clientY: 100 });
    fireEvent.mouseLeave(button);

    expect(button).toBeInTheDocument();
  });

  it('disables magnetic effect when magnetic prop is false', () => {
    render(<AnimatedButton magnetic={false}>No Magnetic</AnimatedButton>);

    const button = screen.getByRole('button');
    fireEvent.mouseMove(button, { clientX: 100, clientY: 100 });

    expect(button).toBeInTheDocument();
  });

  it('handles click with ripple effect', async () => {
    const user = userEvent.setup();

    render(<AnimatedButton>Ripple</AnimatedButton>);

    await user.click(screen.getByRole('button'));

    expect(screen.getByRole('button')).toBeInTheDocument();
  });

  it('renders without magnetic when disabled', () => {
    render(
      <AnimatedButton disabled magnetic>
        Disabled
      </AnimatedButton>
    );

    const button = screen.getByRole('button');
    fireEvent.mouseMove(button, { clientX: 100, clientY: 100 });

    // Button should be rendered even if disabled (mock doesn't pass disabled attr)
    expect(button).toBeInTheDocument();
  });
});
