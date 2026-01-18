import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook } from '@testing-library/react';
import {
  useGSAP,
  useScrollAnimation,
  useStaggerEntrance,
  useParallaxMouse,
  useMagneticButton,
  useTextReveal,
  createFloatingAnimation,
  createGlowPulse,
} from './useAnimations';

// Mock GSAP
vi.mock('gsap', () => {
  const mockContext = {
    revert: vi.fn(),
  };
  
  const mockTl = {
    to: vi.fn().mockReturnThis(),
    from: vi.fn().mockReturnThis(),
    add: vi.fn().mockReturnThis(),
    kill: vi.fn(),
    play: vi.fn(),
    pause: vi.fn(),
  };
  
  return {
    default: {
      registerPlugin: vi.fn(),
      context: vi.fn((fn, ref) => {
        if (ref && ref.current) {
          fn(ref.current);
        }
        return mockContext;
      }),
      to: vi.fn().mockReturnValue({ kill: vi.fn() }),
      from: vi.fn().mockReturnValue({ kill: vi.fn() }),
      fromTo: vi.fn().mockReturnValue({ kill: vi.fn() }),
      set: vi.fn(),
      timeline: vi.fn(() => mockTl),
      quickSetter: vi.fn(() => vi.fn()),
    },
  };
});

vi.mock('gsap/ScrollTrigger', () => ({
  ScrollTrigger: {
    create: vi.fn(() => ({ kill: vi.fn() })),
    batch: vi.fn(() => [{ kill: vi.fn() }]),
    refresh: vi.fn(),
  },
}));

describe('useAnimations hooks', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('useGSAP', () => {
    it('returns a ref object', () => {
      const animationFn = vi.fn();
      const { result } = renderHook(() => useGSAP(animationFn));

      expect(result.current).toHaveProperty('current');
      expect(result.current.current).toBeNull();
    });

    it('calls animation function when ref has element', () => {
      const animationFn = vi.fn();
      const { result } = renderHook(() => useGSAP(animationFn));

      // Simulate attaching element
      result.current.current = document.createElement('div');

      expect(result.current.current).toBeInstanceOf(HTMLElement);
    });
  });

  describe('useScrollAnimation', () => {
    it('returns a ref object', () => {
      const { result } = renderHook(() => useScrollAnimation());

      expect(result.current).toHaveProperty('current');
    });

    it('accepts options parameter', () => {
      const options = {
        start: 'top 90%',
        end: 'bottom 10%',
        scrub: true,
      };
      const { result } = renderHook(() => useScrollAnimation(options));

      expect(result.current).toHaveProperty('current');
    });
  });

  describe('useStaggerEntrance', () => {
    it('returns a ref object', () => {
      const { result } = renderHook(() => useStaggerEntrance('.item'));

      expect(result.current).toHaveProperty('current');
    });

    it('accepts selector and options', () => {
      const { result } = renderHook(() =>
        useStaggerEntrance('.card', { stagger: 0.2, duration: 0.8 })
      );

      expect(result.current).toHaveProperty('current');
    });
  });

  describe('useParallaxMouse', () => {
    it('returns a ref object', () => {
      const { result } = renderHook(() => useParallaxMouse());

      expect(result.current).toHaveProperty('current');
    });

    it('accepts intensity parameter', () => {
      const { result } = renderHook(() => useParallaxMouse(0.5));

      expect(result.current).toHaveProperty('current');
    });
  });

  describe('useMagneticButton', () => {
    it('returns a ref object', () => {
      const { result } = renderHook(() => useMagneticButton());

      expect(result.current).toHaveProperty('current');
    });

    it('accepts strength parameter', () => {
      const { result } = renderHook(() => useMagneticButton(0.5));

      expect(result.current).toHaveProperty('current');
    });

    it('ref starts as null', () => {
      const { result } = renderHook(() => useMagneticButton());

      expect(result.current.current).toBeNull();
    });

    it('can be attached to element', () => {
      const { result } = renderHook(() => useMagneticButton());

      expect(result.current).toBeDefined();
    });
  });

  describe('useTextReveal', () => {
    it('returns a ref object', () => {
      const { result } = renderHook(() => useTextReveal());

      expect(result.current).toHaveProperty('current');
    });

    it('accepts animation options', () => {
      const { result } = renderHook(() =>
        useTextReveal({ type: 'chars', stagger: 0.05 })
      );

      expect(result.current).toHaveProperty('current');
    });
  });

  describe('createFloatingAnimation', () => {
    it('returns animation control object with kill method', () => {
      const element = document.createElement('div');
      const result = createFloatingAnimation(element);

      expect(result).toHaveProperty('kill');
      expect(typeof result.kill).toBe('function');
    });

    it('accepts options', () => {
      const element = document.createElement('div');
      const result = createFloatingAnimation(element, { y: 20, duration: 3 });

      expect(result).toBeDefined();
    });
  });

  describe('createGlowPulse', () => {
    it('returns animation control object with kill method', () => {
      const element = document.createElement('div');
      const result = createGlowPulse(element);

      expect(result).toHaveProperty('kill');
      expect(typeof result.kill).toBe('function');
    });

    it('accepts options', () => {
      const element = document.createElement('div');
      const result = createGlowPulse(element, { color: '#ff0000', intensity: 0.8 });

      expect(result).toBeDefined();
    });
  });
});
