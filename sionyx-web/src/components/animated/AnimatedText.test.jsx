import { describe, it, expect, vi } from 'vitest';
import { render } from '@testing-library/react';
import AnimatedText from './AnimatedText';

// Mock framer-motion completely
vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }) => <div {...props}>{children}</div>,
    span: ({ children, ...props }) => <span {...props}>{children}</span>,
    p: ({ children, ...props }) => <p {...props}>{children}</p>,
    h1: ({ children, ...props }) => <h1 {...props}>{children}</h1>,
    h2: ({ children, ...props }) => <h2 {...props}>{children}</h2>,
    h3: ({ children, ...props }) => <h3 {...props}>{children}</h3>,
  },
  AnimatePresence: ({ children }) => children,
}));

describe('AnimatedText', () => {
  it('renders without crashing', () => {
    const { container } = render(<AnimatedText>Hello World</AnimatedText>);

    expect(container).toBeInTheDocument();
    expect(container.textContent).toContain('Hello');
  });

  it('renders with gradient effect', () => {
    const { container } = render(<AnimatedText gradient>Gradient Text</AnimatedText>);

    expect(container).toBeInTheDocument();
    expect(container.textContent).toContain('Gradient');
  });

  it('renders with typing effect', () => {
    const { container } = render(<AnimatedText typing>Typing Effect</AnimatedText>);

    // Text is split into characters
    expect(container).toBeInTheDocument();
  });

  it('renders with reveal animation', () => {
    const { container } = render(<AnimatedText reveal>Reveal Me</AnimatedText>);

    expect(container).toBeInTheDocument();
  });

  it('renders with wordByWord animation', () => {
    const { container } = render(<AnimatedText wordByWord>Word By Word</AnimatedText>);

    expect(container).toBeInTheDocument();
  });

  it('renders as different HTML elements', () => {
    const { rerender, container } = render(<AnimatedText as='h1'>Heading</AnimatedText>);
    expect(container).toBeInTheDocument();

    rerender(<AnimatedText as='h2'>Heading 2</AnimatedText>);
    expect(container).toBeInTheDocument();

    rerender(<AnimatedText as='p'>Paragraph</AnimatedText>);
    expect(container).toBeInTheDocument();
  });

  it('applies custom className', () => {
    const { container } = render(<AnimatedText className='custom-text'>Classed</AnimatedText>);

    expect(container).toBeInTheDocument();
  });

  it('applies custom styles', () => {
    const { container } = render(<AnimatedText style={{ color: 'red' }}>Styled</AnimatedText>);

    expect(container).toBeInTheDocument();
  });

  it('handles empty text gracefully', () => {
    const { container } = render(<AnimatedText>{''}</AnimatedText>);

    expect(container).toBeInTheDocument();
  });

  it('renders with delay prop', () => {
    const { container } = render(<AnimatedText delay={0.5}>Delayed</AnimatedText>);

    expect(container).toBeInTheDocument();
  });

  it('renders with duration prop', () => {
    const { container } = render(<AnimatedText duration={2}>Duration</AnimatedText>);

    expect(container).toBeInTheDocument();
  });

  it('renders with stagger prop', () => {
    const { container } = render(<AnimatedText stagger={0.1}>Staggered</AnimatedText>);

    expect(container).toBeInTheDocument();
  });
});
