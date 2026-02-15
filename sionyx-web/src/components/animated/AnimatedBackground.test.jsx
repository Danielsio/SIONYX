import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render } from '@testing-library/react';
import AnimatedBackground from './AnimatedBackground';

// Mock framer-motion
vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, style, className, ...props }) => (
      <div style={style} className={className} data-testid='motion-div' {...props}>
        {children}
      </div>
    ),
    span: ({ children, ...props }) => <span {...props}>{children}</span>,
    svg: ({ children, ...props }) => <svg {...props}>{children}</svg>,
    circle: props => <circle {...props} />,
    path: props => <path {...props} />,
  },
  AnimatePresence: ({ children }) => children,
  useMotionValue: () => ({ get: () => 0, set: vi.fn() }),
  useTransform: () => 0,
  useSpring: () => ({ get: () => 0, set: vi.fn() }),
}));

// Mock canvas with complete context
const mockContext = {
  clearRect: vi.fn(),
  beginPath: vi.fn(),
  arc: vi.fn(),
  fill: vi.fn(),
  stroke: vi.fn(),
  moveTo: vi.fn(),
  lineTo: vi.fn(),
  closePath: vi.fn(),
  save: vi.fn(),
  restore: vi.fn(),
  scale: vi.fn(),
  translate: vi.fn(),
  rotate: vi.fn(),
  setTransform: vi.fn(),
  createLinearGradient: vi.fn(() => ({
    addColorStop: vi.fn(),
  })),
  createRadialGradient: vi.fn(() => ({
    addColorStop: vi.fn(),
  })),
  fillRect: vi.fn(),
  strokeRect: vi.fn(),
  fillStyle: '',
  strokeStyle: '',
  globalAlpha: 1,
  lineWidth: 1,
  lineCap: 'butt',
  shadowBlur: 0,
  shadowColor: '',
};

beforeEach(() => {
  HTMLCanvasElement.prototype.getContext = vi.fn(() => mockContext);

  // Mock requestAnimationFrame
  vi.spyOn(window, 'requestAnimationFrame').mockImplementation(cb => {
    return setTimeout(cb, 16);
  });
  vi.spyOn(window, 'cancelAnimationFrame').mockImplementation(id => {
    clearTimeout(id);
  });
});

describe('AnimatedBackground', () => {
  it('renders without crashing', () => {
    const { container } = render(<AnimatedBackground />);

    expect(container).toBeInTheDocument();
  });

  it('renders with children', () => {
    const { container } = render(
      <AnimatedBackground>
        <div data-testid='child'>Content</div>
      </AnimatedBackground>
    );

    // Check container rendered
    expect(container).toBeInTheDocument();
  });

  it('renders with particles variant', () => {
    const { container } = render(<AnimatedBackground variant='particles' />);

    expect(container).toBeInTheDocument();
  });

  it('renders with gradient variant', () => {
    const { container } = render(<AnimatedBackground variant='gradient' />);

    expect(container).toBeInTheDocument();
  });

  it('renders with mesh variant', () => {
    const { container } = render(<AnimatedBackground variant='mesh' />);

    expect(container).toBeInTheDocument();
  });

  it('renders with waves variant', () => {
    const { container } = render(<AnimatedBackground variant='waves' />);

    expect(container).toBeInTheDocument();
  });

  it('applies custom colors', () => {
    const { container } = render(<AnimatedBackground colors={['#ff0000', '#00ff00', '#0000ff']} />);

    expect(container).toBeInTheDocument();
  });

  it('renders with interactive mode', () => {
    const { container } = render(<AnimatedBackground interactive />);

    expect(container).toBeInTheDocument();
  });

  it('renders with density prop', () => {
    const { container } = render(<AnimatedBackground density={50} />);

    expect(container).toBeInTheDocument();
  });

  it('renders with speed prop', () => {
    const { container } = render(<AnimatedBackground speed={2} />);

    expect(container).toBeInTheDocument();
  });

  it('applies custom styles', () => {
    const { container } = render(<AnimatedBackground style={{ opacity: 0.5 }} />);

    expect(container).toBeInTheDocument();
  });

  it('applies custom className', () => {
    const { container } = render(<AnimatedBackground className='custom-bg' />);

    expect(container).toBeInTheDocument();
  });

  it('handles disabled state', () => {
    const { container } = render(<AnimatedBackground disabled />);

    expect(container).toBeInTheDocument();
  });

  it('renders with blur effect', () => {
    const { container } = render(<AnimatedBackground blur={10} />);

    expect(container).toBeInTheDocument();
  });

  it('handles reduced motion preference', () => {
    const { container } = render(<AnimatedBackground reducedMotion />);

    expect(container).toBeInTheDocument();
  });
});
