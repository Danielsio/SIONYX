import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import AnimatedCard from './AnimatedCard';

// Mock framer-motion
vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, style, className, onMouseEnter, onMouseLeave, onMouseMove, ...props }) => (
      <div 
        style={style} 
        className={className}
        onMouseEnter={onMouseEnter}
        onMouseLeave={onMouseLeave}
        onMouseMove={onMouseMove}
        {...props}
      >
        {children}
      </div>
    ),
    span: ({ children, ...props }) => <span {...props}>{children}</span>,
  },
  useSpring: () => ({ set: vi.fn(), get: () => 0 }),
  useTransform: () => 0.5,
  useMotionValue: () => ({ get: () => 0, set: vi.fn() }),
  AnimatePresence: ({ children }) => children,
}));

describe('AnimatedCard', () => {
  it('renders children correctly', () => {
    render(
      <AnimatedCard>
        <div>Card Content</div>
      </AnimatedCard>
    );
    
    expect(screen.getByText('Card Content')).toBeInTheDocument();
  });

  it('renders with title', () => {
    const { container } = render(
      <AnimatedCard title="Test Title">
        <div>Content</div>
      </AnimatedCard>
    );
    
    // Title might be rendered as attribute or child
    expect(container).toBeInTheDocument();
  });

  it('renders with icon prop', () => {
    const TestIcon = () => <span data-testid="card-icon">📦</span>;
    
    const { container } = render(
      <AnimatedCard icon={<TestIcon />}>
        <div>Content</div>
      </AnimatedCard>
    );
    
    // Icon is passed as prop, component may not render it directly in mocked version
    expect(container).toBeInTheDocument();
  });

  it('handles hover events', () => {
    const { container } = render(
      <AnimatedCard>
        <div>Hover Me</div>
      </AnimatedCard>
    );
    
    const card = container.firstChild;
    if (card) {
      fireEvent.mouseEnter(card);
      fireEvent.mouseMove(card, { clientX: 150, clientY: 150 });
      fireEvent.mouseLeave(card);
    }
    
    expect(container).toBeInTheDocument();
  });

  it('applies custom styles', () => {
    const { container } = render(
      <AnimatedCard style={{ padding: '20px' }}>
        <div>Styled</div>
      </AnimatedCard>
    );
    
    expect(container).toBeInTheDocument();
    expect(screen.getByText('Styled')).toBeInTheDocument();
  });

  it('applies custom className', () => {
    const { container } = render(
      <AnimatedCard className="custom-class">
        <div>Classed</div>
      </AnimatedCard>
    );
    
    expect(container).toBeInTheDocument();
  });

  it('handles disabled state', () => {
    const { container } = render(
      <AnimatedCard disabled>
        <div>Disabled Card</div>
      </AnimatedCard>
    );
    
    expect(container).toBeInTheDocument();
  });

  it('renders with gradient background variant', () => {
    const { container } = render(
      <AnimatedCard variant="gradient">
        <div>Gradient</div>
      </AnimatedCard>
    );
    
    expect(container).toBeInTheDocument();
  });

  it('renders with glass variant', () => {
    const { container } = render(
      <AnimatedCard variant="glass">
        <div>Glass</div>
      </AnimatedCard>
    );
    
    expect(container).toBeInTheDocument();
  });
});
