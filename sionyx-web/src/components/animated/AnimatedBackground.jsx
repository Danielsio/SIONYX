/**
 * Animated Background Component
 * Creates an immersive, dynamic background with floating orbs and gradient mesh
 */

import { useEffect, useRef, memo } from 'react';
import { motion } from 'framer-motion';
import gsap from 'gsap';

// Floating Orb Component
const FloatingOrb = memo(({ 
  size = 300, 
  color = 'rgba(94, 129, 244, 0.15)', 
  initialX = 0, 
  initialY = 0,
  duration = 20,
  delay = 0,
}) => {
  const orbRef = useRef(null);

  useEffect(() => {
    if (!orbRef.current) return;

    // Create complex floating path
    const tl = gsap.timeline({ repeat: -1, delay });
    
    tl.to(orbRef.current, {
      x: `+=${Math.random() * 200 - 100}`,
      y: `+=${Math.random() * 200 - 100}`,
      scale: 1 + Math.random() * 0.3,
      duration: duration / 3,
      ease: 'sine.inOut',
    })
    .to(orbRef.current, {
      x: `+=${Math.random() * 200 - 100}`,
      y: `+=${Math.random() * 200 - 100}`,
      scale: 1 - Math.random() * 0.2,
      duration: duration / 3,
      ease: 'sine.inOut',
    })
    .to(orbRef.current, {
      x: initialX,
      y: initialY,
      scale: 1,
      duration: duration / 3,
      ease: 'sine.inOut',
    });

    return () => tl.kill();
  }, [duration, delay, initialX, initialY]);

  return (
    <div
      ref={orbRef}
      style={{
        position: 'absolute',
        width: size,
        height: size,
        borderRadius: '50%',
        background: `radial-gradient(circle, ${color} 0%, transparent 70%)`,
        filter: 'blur(40px)',
        pointerEvents: 'none',
        left: initialX,
        top: initialY,
        willChange: 'transform',
      }}
    />
  );
});

FloatingOrb.displayName = 'FloatingOrb';

// Particle Field Component
const ParticleField = memo(({ count = 50 }) => {
  const canvasRef = useRef(null);
  const particlesRef = useRef([]);
  const mouseRef = useRef({ x: 0, y: 0 });
  const animationRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    
    const resizeCanvas = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    // Initialize particles
    particlesRef.current = Array.from({ length: count }, () => ({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      vx: (Math.random() - 0.5) * 0.5,
      vy: (Math.random() - 0.5) * 0.5,
      size: Math.random() * 2 + 1,
      opacity: Math.random() * 0.5 + 0.2,
    }));

    const handleMouseMove = (e) => {
      mouseRef.current = { x: e.clientX, y: e.clientY };
    };
    window.addEventListener('mousemove', handleMouseMove);

    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      particlesRef.current.forEach((particle) => {
        // Mouse attraction
        const dx = mouseRef.current.x - particle.x;
        const dy = mouseRef.current.y - particle.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        
        if (dist < 200) {
          const force = (200 - dist) / 200 * 0.02;
          particle.vx += dx * force * 0.01;
          particle.vy += dy * force * 0.01;
        }

        // Update position
        particle.x += particle.vx;
        particle.y += particle.vy;

        // Bounce off edges
        if (particle.x < 0 || particle.x > canvas.width) particle.vx *= -1;
        if (particle.y < 0 || particle.y > canvas.height) particle.vy *= -1;

        // Damping
        particle.vx *= 0.99;
        particle.vy *= 0.99;

        // Draw particle
        ctx.beginPath();
        ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(147, 168, 255, ${particle.opacity})`;
        ctx.fill();
      });

      // Draw connections
      particlesRef.current.forEach((p1, i) => {
        particlesRef.current.slice(i + 1).forEach((p2) => {
          const dx = p1.x - p2.x;
          const dy = p1.y - p2.y;
          const dist = Math.sqrt(dx * dx + dy * dy);

          if (dist < 150) {
            ctx.beginPath();
            ctx.moveTo(p1.x, p1.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.strokeStyle = `rgba(147, 168, 255, ${0.1 * (1 - dist / 150)})`;
            ctx.stroke();
          }
        });
      });

      animationRef.current = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      window.removeEventListener('resize', resizeCanvas);
      window.removeEventListener('mousemove', handleMouseMove);
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [count]);

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
      {/* Base Gradient */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 2 }}
        style={{
          position: 'absolute',
          inset: 0,
          background: 'linear-gradient(135deg, #0a0a1a 0%, #1a1a3e 25%, #16213e 50%, #0f3460 75%, #0a192f 100%)',
        }}
      />

      {/* Animated Gradient Overlay */}
      <motion.div
        animate={{
          background: [
            'radial-gradient(ellipse at 20% 20%, rgba(94, 129, 244, 0.15) 0%, transparent 50%)',
            'radial-gradient(ellipse at 80% 80%, rgba(94, 129, 244, 0.15) 0%, transparent 50%)',
            'radial-gradient(ellipse at 50% 50%, rgba(94, 129, 244, 0.15) 0%, transparent 50%)',
            'radial-gradient(ellipse at 20% 20%, rgba(94, 129, 244, 0.15) 0%, transparent 50%)',
          ],
        }}
        transition={{
          duration: 15,
          repeat: Infinity,
          ease: 'easeInOut',
        }}
        style={{
          position: 'absolute',
          inset: 0,
        }}
      />

      {/* Floating Orbs */}
      <FloatingOrb 
        size={500} 
        color="rgba(94, 129, 244, 0.12)" 
        initialX={-100} 
        initialY={-100}
        duration={25}
      />
      <FloatingOrb 
        size={400} 
        color="rgba(236, 72, 153, 0.08)" 
        initialX="70%" 
        initialY="20%"
        duration={20}
        delay={2}
      />
      <FloatingOrb 
        size={350} 
        color="rgba(118, 75, 162, 0.1)" 
        initialX="30%" 
        initialY="60%"
        duration={22}
        delay={4}
      />
      <FloatingOrb 
        size={300} 
        color="rgba(82, 196, 26, 0.06)" 
        initialX="80%" 
        initialY="70%"
        duration={18}
        delay={1}
      />

      {/* Particle Field */}
      <ParticleField count={40} />

      {/* Noise Texture Overlay */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          opacity: 0.03,
          backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E")`,
        }}
      />

      {/* Vignette */}
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
