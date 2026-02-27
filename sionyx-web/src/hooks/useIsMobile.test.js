import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import useIsMobile from './useIsMobile';

describe('useIsMobile', () => {
  const originalInnerWidth = Object.getOwnPropertyDescriptor(window, 'innerWidth');

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    if (originalInnerWidth) {
      Object.defineProperty(window, 'innerWidth', originalInnerWidth);
    }
  });

  it('uses default breakpoint of 768', () => {
    Object.defineProperty(window, 'innerWidth', { value: 768, writable: true });
    const { result } = renderHook(() => useIsMobile());
    expect(result.current).toBe(false);
  });

  it('returns false when window.innerWidth >= 768', () => {
    Object.defineProperty(window, 'innerWidth', { value: 768, writable: true });
    const { result } = renderHook(() => useIsMobile());
    expect(result.current).toBe(false);

    Object.defineProperty(window, 'innerWidth', { value: 1024, writable: true });
    act(() => {
      window.dispatchEvent(new Event('resize'));
    });
    expect(result.current).toBe(false);
  });

  it('returns true when window.innerWidth < 768', () => {
    Object.defineProperty(window, 'innerWidth', { value: 767, writable: true });
    const { result } = renderHook(() => useIsMobile());
    expect(result.current).toBe(true);

    Object.defineProperty(window, 'innerWidth', { value: 320, writable: true });
    act(() => {
      window.dispatchEvent(new Event('resize'));
    });
    expect(result.current).toBe(true);
  });

  it('respects custom breakpoint', () => {
    Object.defineProperty(window, 'innerWidth', { value: 600, writable: true });
    const { result: result768 } = renderHook(() => useIsMobile(768));
    expect(result768.current).toBe(true);

    const { result: result500 } = renderHook(() => useIsMobile(500));
    expect(result500.current).toBe(false);
  });

  it('handles resize events and updates isMobile', () => {
    const addEventListenerSpy = vi.spyOn(window, 'addEventListener');
    const removeEventListenerSpy = vi.spyOn(window, 'removeEventListener');

    Object.defineProperty(window, 'innerWidth', { value: 1024, writable: true });
    const { result, unmount } = renderHook(() => useIsMobile());
    expect(result.current).toBe(false);

    expect(addEventListenerSpy).toHaveBeenCalledWith('resize', expect.any(Function));

    Object.defineProperty(window, 'innerWidth', { value: 400, writable: true });
    act(() => {
      window.dispatchEvent(new Event('resize'));
    });
    expect(result.current).toBe(true);

    unmount();
    expect(removeEventListenerSpy).toHaveBeenCalledWith('resize', expect.any(Function));

    addEventListenerSpy.mockRestore();
    removeEventListenerSpy.mockRestore();
  });
});
