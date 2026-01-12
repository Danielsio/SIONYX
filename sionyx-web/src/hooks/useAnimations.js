/**
 * Animation Hooks for SIONYX Landing Page
 * Premium motion utilities using GSAP and Framer Motion
 */

import { useEffect, useRef, useCallback } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

// Register GSAP plugins
gsap.registerPlugin(ScrollTrigger);

/**
 * Hook for GSAP animations with automatic cleanup
 */
export const useGSAP = (animationFn, deps = []) => {
  const elementRef = useRef(null);

  useEffect(() => {
    if (!elementRef.current) return;

    const ctx = gsap.context(() => {
      animationFn(elementRef.current);
    }, elementRef);

    return () => ctx.revert();
  }, deps);

  return elementRef;
};

/**
 * Hook for scroll-triggered animations
 */
export const useScrollAnimation = (options = {}) => {
  const elementRef = useRef(null);

  useEffect(() => {
    if (!elementRef.current) return;

    const {
      start = 'top 80%',
      end = 'bottom 20%',
      scrub = false,
      markers = false,
      onEnter,
      onLeave,
      animation,
    } = options;

    const trigger = ScrollTrigger.create({
      trigger: elementRef.current,
      start,
      end,
      scrub,
      markers,
      onEnter,
      onLeave,
      animation,
    });

    return () => trigger.kill();
  }, []);

  return elementRef;
};

/**
 * Hook for staggered entrance animations
 */
export const useStaggerEntrance = (selector, options = {}) => {
  const containerRef = useRef(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const {
      from = { opacity: 0, y: 60, scale: 0.95 },
      to = { opacity: 1, y: 0, scale: 1 },
      stagger = 0.1,
      duration = 0.6,
      ease = 'power3.out',
      scrollTrigger = true,
    } = options;

    const elements = containerRef.current.querySelectorAll(selector);
    if (!elements.length) return;

    const config = {
      ...from,
      stagger,
      duration,
      ease,
    };

    if (scrollTrigger) {
      config.scrollTrigger = {
        trigger: containerRef.current,
        start: 'top 80%',
        toggleActions: 'play none none reverse',
      };
    }

    gsap.set(elements, from);
    const tween = gsap.to(elements, { ...to, ...config });

    return () => tween.kill();
  }, [selector]);

  return containerRef;
};

/**
 * Hook for parallax effect on mouse move
 */
export const useParallaxMouse = (intensity = 0.1) => {
  const elementRef = useRef(null);
  const positionRef = useRef({ x: 0, y: 0 });

  useEffect(() => {
    if (!elementRef.current) return;

    const handleMouseMove = (e) => {
      const { clientX, clientY } = e;
      const { innerWidth, innerHeight } = window;
      
      // Calculate position relative to center (-1 to 1)
      const x = (clientX / innerWidth - 0.5) * 2;
      const y = (clientY / innerHeight - 0.5) * 2;

      positionRef.current = { x, y };

      gsap.to(elementRef.current, {
        x: x * intensity * 100,
        y: y * intensity * 100,
        duration: 0.5,
        ease: 'power2.out',
      });
    };

    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, [intensity]);

  return elementRef;
};

/**
 * Hook for magnetic button effect
 */
export const useMagneticButton = (strength = 0.3) => {
  const buttonRef = useRef(null);

  useEffect(() => {
    if (!buttonRef.current) return;

    const button = buttonRef.current;

    const handleMouseMove = (e) => {
      const rect = button.getBoundingClientRect();
      const centerX = rect.left + rect.width / 2;
      const centerY = rect.top + rect.height / 2;
      
      const distX = e.clientX - centerX;
      const distY = e.clientY - centerY;

      gsap.to(button, {
        x: distX * strength,
        y: distY * strength,
        duration: 0.3,
        ease: 'power2.out',
      });
    };

    const handleMouseLeave = () => {
      gsap.to(button, {
        x: 0,
        y: 0,
        duration: 0.5,
        ease: 'elastic.out(1, 0.3)',
      });
    };

    button.addEventListener('mousemove', handleMouseMove);
    button.addEventListener('mouseleave', handleMouseLeave);

    return () => {
      button.removeEventListener('mousemove', handleMouseMove);
      button.removeEventListener('mouseleave', handleMouseLeave);
    };
  }, [strength]);

  return buttonRef;
};

/**
 * Hook for text reveal animation (letter by letter)
 */
export const useTextReveal = (options = {}) => {
  const textRef = useRef(null);

  useEffect(() => {
    if (!textRef.current) return;

    const {
      duration = 0.05,
      stagger = 0.03,
      delay = 0,
      ease = 'power2.out',
    } = options;

    const text = textRef.current;
    const originalText = text.textContent;
    
    // Split text into spans
    text.innerHTML = originalText
      .split('')
      .map(char => `<span style="display:inline-block;opacity:0;transform:translateY(20px)">${char === ' ' ? '&nbsp;' : char}</span>`)
      .join('');

    const chars = text.querySelectorAll('span');

    gsap.to(chars, {
      opacity: 1,
      y: 0,
      duration,
      stagger,
      delay,
      ease,
    });
  }, []);

  return textRef;
};

/**
 * Create floating animation
 */
export const createFloatingAnimation = (element, options = {}) => {
  const {
    y = 20,
    duration = 3,
    ease = 'sine.inOut',
  } = options;

  return gsap.to(element, {
    y: `-=${y}`,
    duration,
    ease,
    yoyo: true,
    repeat: -1,
  });
};

/**
 * Create glow pulse animation
 */
export const createGlowPulse = (element, options = {}) => {
  const {
    intensity = 1.5,
    duration = 2,
    color = 'rgba(94, 129, 244, 0.6)',
  } = options;

  return gsap.to(element, {
    boxShadow: `0 0 ${30 * intensity}px ${10 * intensity}px ${color}`,
    duration,
    ease: 'sine.inOut',
    yoyo: true,
    repeat: -1,
  });
};

export default {
  useGSAP,
  useScrollAnimation,
  useStaggerEntrance,
  useParallaxMouse,
  useMagneticButton,
  useTextReveal,
  createFloatingAnimation,
  createGlowPulse,
};
