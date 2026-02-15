/**
 * Animated Background Component
 * Creates an immersive, dynamic background with floating orbs and gradient mesh
 * Optimized for smooth 60fps on both desktop and mobile
 */

import { useEffect, useRef, memo, useState, useMemo } from 'react';
import { motion } from 'framer-motion';

// Detect if we should use reduced animations (large screens need lighter animations)
const usePerformanceMode = () => {
  const [mode, setMode] = useState('full');

  useEffect(() => {
    const checkPerformance = () => {
      const width = window.innerWidth;
      const height = window.innerHeight;
      const pixels = width * height;

      // Check for reduced motion preference
      const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      if (prefersReducedMotion) {
        setMode('minimal');
        return;
      }

      // Mobile devices (< 768px) - full animations work great
      if (width < 768) {
        setMode('full');
        return;
      }

      // Large screens (> 2M pixels like 1920x1080) - use optimized mode
      if (pixels > 2000000) {
        setMode('optimized');
        return;
      }

      setMode('full');
    };

    checkPerformance();
    window.addEventListener('resize', checkPerformance);
    return () => window.removeEventListener('resize', checkPerformance);
  }, []);

  return mode;
};

// Floating Orb Component - CSS animations instead of GSAP for better GPU acceleration
const FloatingOrb = memo(
  ({
    size = 300,
    color = 'rgba(94, 129, 244, 0.15)',
    initialX = 0,
    initialY = 0,
    duration = 20,
    delay = 0,
    reducedBlur = false,
  }) => {
    // Use CSS keyframe animation ID based on position for variety
    const animationName = useMemo(() => {
      const seed = typeof initialX === 'string' ? initialX.length : initialX;
      return `float-${seed % 3}`;
    }, [initialX]);

    return (
      <div
        style={{
          position: 'absolute',
          width: size,
          height: size,
          borderRadius: '50%',
          background: `radial-gradient(circle, ${color} 0%, transparent 70%)`,
          // Reduced blur for desktop performance - blur is VERY expensive
          filter: reducedBlur ? 'blur(20px)' : 'blur(40px)',
          pointerEvents: 'none',
          left: initialX,
          top: initialY,
          // Use CSS animation for GPU acceleration
          animation: `${animationName} ${duration}s ease-in-out ${delay}s infinite`,
          // GPU hints
          transform: 'translateZ(0)',
          willChange: 'transform',
        }}
      />
    );
  }
);

FloatingOrb.displayName = 'FloatingOrb';

// Optimized Particle Field Component
const ParticleField = memo(({ count = 50, enableConnections = true }) => {
  const canvasRef = useRef(null);
  const particlesRef = useRef([]);
  const mouseRef = useRef({ x: -1000, y: -1000 }); // Start off-screen
  const animationRef = useRef(null);
  const lastMouseUpdate = useRef(0);
  const frameCount = useRef(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d', { alpha: true });

    // Use device pixel ratio but cap it for performance
    const dpr = Math.min(window.devicePixelRatio || 1, 2);

    const resizeCanvas = () => {
      const width = window.innerWidth;
      const height = window.innerHeight;

      // Set display size
      canvas.style.width = width + 'px';
      canvas.style.height = height + 'px';

      // Set actual size in memory (scaled for retina but capped)
      canvas.width = width * dpr;
      canvas.height = height * dpr;

      // Scale context to match
      ctx.scale(dpr, dpr);

      // Reinitialize particles on resize
      particlesRef.current = Array.from({ length: count }, () => ({
        x: Math.random() * width,
        y: Math.random() * height,
        vx: (Math.random() - 0.5) * 0.3,
        vy: (Math.random() - 0.5) * 0.3,
        size: Math.random() * 2 + 1,
        opacity: Math.random() * 0.4 + 0.2,
      }));
    };

    resizeCanvas();

    // Debounced resize handler
    let resizeTimeout;
    const handleResize = () => {
      clearTimeout(resizeTimeout);
      resizeTimeout = setTimeout(resizeCanvas, 150);
    };
    window.addEventListener('resize', handleResize);

    // Throttled mouse handler - only update every 50ms
    const handleMouseMove = e => {
      const now = Date.now();
      if (now - lastMouseUpdate.current > 50) {
        mouseRef.current = { x: e.clientX, y: e.clientY };
        lastMouseUpdate.current = now;
      }
    };
    window.addEventListener('mousemove', handleMouseMove, { passive: true });

    const width = window.innerWidth;
    const height = window.innerHeight;

    const animate = () => {
      frameCount.current++;

      ctx.clearRect(0, 0, width, height);

      const particles = particlesRef.current;
      const mouseX = mouseRef.current.x;
      const mouseY = mouseRef.current.y;

      // Update and draw particles
      for (let i = 0; i < particles.length; i++) {
        const particle = particles[i];

        // Mouse attraction (simplified calculation)
        const dx = mouseX - particle.x;
        const dy = mouseY - particle.y;
        const distSq = dx * dx + dy * dy; // Avoid sqrt when possible

        if (distSq < 40000) {
          // 200^2
          const dist = Math.sqrt(distSq);
          const force = ((200 - dist) / 200) * 0.015;
          particle.vx += dx * force * 0.01;
          particle.vy += dy * force * 0.01;
        }

        // Update position
        particle.x += particle.vx;
        particle.y += particle.vy;

        // Wrap around edges (smoother than bouncing)
        if (particle.x < -10) particle.x = width + 10;
        if (particle.x > width + 10) particle.x = -10;
        if (particle.y < -10) particle.y = height + 10;
        if (particle.y > height + 10) particle.y = -10;

        // Damping
        particle.vx *= 0.99;
        particle.vy *= 0.99;

        // Draw particle
        ctx.beginPath();
        ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(147, 168, 255, ${particle.opacity})`;
        ctx.fill();
      }

      // Draw connections - ONLY every 2nd frame and with distance limit
      if (enableConnections && frameCount.current % 2 === 0) {
        ctx.lineWidth = 0.5;

        // Only check nearby particles (spatial optimization)
        for (let i = 0; i < particles.length; i++) {
          const p1 = particles[i];
          // Only check particles after current one, and limit checks
          for (let j = i + 1; j < Math.min(i + 10, particles.length); j++) {
            const p2 = particles[j];
            const dx = p1.x - p2.x;
            const dy = p1.y - p2.y;
            const distSq = dx * dx + dy * dy;

            if (distSq < 12100) {
              // 110^2 - reduced connection distance
              const dist = Math.sqrt(distSq);
              ctx.beginPath();
              ctx.moveTo(p1.x, p1.y);
              ctx.lineTo(p2.x, p2.y);
              ctx.strokeStyle = `rgba(147, 168, 255, ${0.08 * (1 - dist / 110)})`;
              ctx.stroke();
            }
          }
        }
      }

      animationRef.current = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      clearTimeout(resizeTimeout);
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('mousemove', handleMouseMove);
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [count, enableConnections]);

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        pointerEvents: 'none',
      }}
    />
  );
});

ParticleField.displayName = 'ParticleField';

// Main Animated Background Component
const AnimatedBackground = memo(() => {
  const performanceMode = usePerformanceMode();

  // Adjust settings based on performance mode
  const settings = useMemo(() => {
    switch (performanceMode) {
      case 'minimal':
        return {
          particleCount: 0,
          enableConnections: false,
          showOrbs: false,
          reducedBlur: true,
        };
      case 'optimized':
        return {
          particleCount: 25,
          enableConnections: false, // Connections are expensive
          showOrbs: true,
          reducedBlur: true,
        };
      case 'full':
      default:
        return {
          particleCount: 35,
          enableConnections: true,
          showOrbs: true,
          reducedBlur: false,
        };
    }
  }, [performanceMode]);

  return (
    <div
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        overflow: 'hidden',
        pointerEvents: 'none',
        zIndex: 0,
      }}
    >
      {/* CSS Keyframe animations for orbs - defined inline for simplicity */}
      <style>
        {`
          @keyframes float-0 {
            0%, 100% { transform: translate(0, 0) scale(1); }
            33% { transform: translate(30px, -40px) scale(1.05); }
            66% { transform: translate(-20px, 20px) scale(0.95); }
          }
          @keyframes float-1 {
            0%, 100% { transform: translate(0, 0) scale(1); }
            33% { transform: translate(-40px, 30px) scale(0.95); }
            66% { transform: translate(25px, -25px) scale(1.05); }
          }
          @keyframes float-2 {
            0%, 100% { transform: translate(0, 0) scale(1); }
            50% { transform: translate(35px, 35px) scale(1.03); }
          }
        `}
      </style>

      {/* Base Gradient - static, no animation needed */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'linear-gradient(135deg, #0a0a1a 0%, #1a1a3e 25%, #16213e 50%, #0f3460 75%, #0a192f 100%)',
        }}
      />

      {/* Animated Gradient Overlay - simplified animation */}
      <motion.div
        animate={{
          opacity: [0.8, 1, 0.8],
        }}
        transition={{
          duration: 8,
          repeat: Infinity,
          ease: 'easeInOut',
        }}
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'radial-gradient(ellipse at 30% 30%, rgba(94, 129, 244, 0.12) 0%, transparent 50%)',
        }}
      />

      {/* Floating Orbs - CSS animated */}
      {settings.showOrbs && (
        <>
          <FloatingOrb
            size={400}
            color='rgba(94, 129, 244, 0.1)'
            initialX={-50}
            initialY={-50}
            duration={20}
            reducedBlur={settings.reducedBlur}
          />
          <FloatingOrb
            size={350}
            color='rgba(236, 72, 153, 0.07)'
            initialX='65%'
            initialY='15%'
            duration={18}
            delay={1}
            reducedBlur={settings.reducedBlur}
          />
          <FloatingOrb
            size={300}
            color='rgba(118, 75, 162, 0.08)'
            initialX='25%'
            initialY='55%'
            duration={22}
            delay={2}
            reducedBlur={settings.reducedBlur}
          />
        </>
      )}

      {/* Particle Field - with performance-based settings */}
      {settings.particleCount > 0 && (
        <ParticleField
          count={settings.particleCount}
          enableConnections={settings.enableConnections}
        />
      )}

      {/* Vignette - static */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background: 'radial-gradient(ellipse at center, transparent 0%, rgba(0,0,0,0.4) 100%)',
        }}
      />
    </div>
  );
});

AnimatedBackground.displayName = 'AnimatedBackground';

export default AnimatedBackground;
