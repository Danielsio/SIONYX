/**
 * Animated Card Component
 * Premium card with 3D tilt, glow effects, and entrance animations
 */

import { useRef, useState, memo } from 'react';
import { motion, useMotionValue, useSpring, useTransform } from 'framer-motion';

const AnimatedCard = memo(
  ({
    children,
    onClick,
    variant = 'default', // default, glass, gradient, glow
    tilt = true,
    glow = true,
    entrance = true,
    delay = 0,
    style = {},
    className = '',
    ...props
  }) => {
    const cardRef = useRef(null);
    const [isHovered, setIsHovered] = useState(false);

    // Motion values for 3D tilt
    const mouseX = useMotionValue(0);
    const mouseY = useMotionValue(0);

    // Spring physics for smooth movement
    const rotateX = useSpring(useTransform(mouseY, [-0.5, 0.5], [10, -10]), {
      stiffness: 300,
      damping: 30,
    });
    const rotateY = useSpring(useTransform(mouseX, [-0.5, 0.5], [-10, 10]), {
      stiffness: 300,
      damping: 30,
    });

    // Glow position
    const glowX = useSpring(useTransform(mouseX, [-0.5, 0.5], [0, 100]), {
      stiffness: 300,
      damping: 30,
    });
    const glowY = useSpring(useTransform(mouseY, [-0.5, 0.5], [0, 100]), {
      stiffness: 300,
      damping: 30,
    });

    const handleMouseMove = e => {
      if (!tilt || !cardRef.current) return;

      const rect = cardRef.current.getBoundingClientRect();
      const centerX = rect.left + rect.width / 2;
      const centerY = rect.top + rect.height / 2;

      const normalizedX = (e.clientX - centerX) / (rect.width / 2);
      const normalizedY = (e.clientY - centerY) / (rect.height / 2);

      mouseX.set(normalizedX * 0.5);
      mouseY.set(normalizedY * 0.5);
    };

    const handleMouseLeave = () => {
      mouseX.set(0);
      mouseY.set(0);
      setIsHovered(false);
    };

    // Variant styles
    const variants = {
      default: {
        background: 'rgba(255, 255, 255, 0.05)',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        backdropFilter: 'blur(20px)',
      },
      glass: {
        background: 'rgba(255, 255, 255, 0.08)',
        border: '1px solid rgba(255, 255, 255, 0.15)',
        backdropFilter: 'blur(30px)',
      },
      gradient: {
        background: 'linear-gradient(145deg, rgba(94, 129, 244, 0.2), rgba(118, 75, 162, 0.2))',
        border: '1px solid rgba(94, 129, 244, 0.3)',
        backdropFilter: 'blur(20px)',
      },
      glow: {
        background: 'linear-gradient(145deg, rgba(94, 129, 244, 0.95), rgba(118, 75, 162, 0.95))',
        border: 'none',
        backdropFilter: 'none',
      },
    };

    const currentVariant = variants[variant] || variants.default;

    // Entrance animation variants
    const entranceVariants = {
      hidden: {
        opacity: 0,
        y: 60,
        scale: 0.95,
      },
      visible: {
        opacity: 1,
        y: 0,
        scale: 1,
        transition: {
          duration: 0.6,
          delay,
          ease: [0.25, 0.46, 0.45, 0.94],
        },
      },
    };

    return (
      <motion.div
        ref={cardRef}
        className={className}
        initial={entrance ? 'hidden' : false}
        whileInView={entrance ? 'visible' : false}
        viewport={{ once: true, amount: 0.2 }}
        variants={entrance ? entranceVariants : undefined}
        style={{
          position: 'relative',
          borderRadius: 20,
          overflow: 'hidden',
          cursor: onClick ? 'pointer' : 'default',
          transformStyle: 'preserve-3d',
          perspective: 1000,
          rotateX: tilt ? rotateX : 0,
          rotateY: tilt ? rotateY : 0,
          ...currentVariant,
          ...style,
        }}
        onMouseMove={handleMouseMove}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={handleMouseLeave}
        onClick={onClick}
        whileHover={{
          y: -8,
          boxShadow: '0 25px 50px rgba(0, 0, 0, 0.4)',
          transition: { duration: 0.3 },
        }}
        {...props}
      >
        {/* Glow Effect */}
        {glow && (
          <motion.div
            style={{
              position: 'absolute',
              inset: -1,
              borderRadius: 21,
              background:
                variant === 'glow'
                  ? 'linear-gradient(145deg, rgba(94, 129, 244, 0.8), rgba(118, 75, 162, 0.8))'
                  : 'rgba(94, 129, 244, 0.3)',
              filter: 'blur(20px)',
              opacity: isHovered ? 0.8 : 0,
              zIndex: -1,
              transition: 'opacity 0.3s ease',
            }}
          />
        )}

        {/* Spotlight Effect */}
        {isHovered && glow && (
          <motion.div
            style={{
              position: 'absolute',
              width: 200,
              height: 200,
              borderRadius: '50%',
              background: 'radial-gradient(circle, rgba(255,255,255,0.15) 0%, transparent 70%)',
              x: glowX,
              y: glowY,
              transform: 'translate(-50%, -50%)',
              pointerEvents: 'none',
            }}
          />
        )}

        {/* Border Gradient Animation */}
        <motion.div
          style={{
            position: 'absolute',
            inset: 0,
            borderRadius: 20,
            padding: 1,
            background: isHovered
              ? 'linear-gradient(135deg, rgba(94, 129, 244, 0.5), rgba(236, 72, 153, 0.5), rgba(94, 129, 244, 0.5))'
              : 'transparent',
            WebkitMask: 'linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0)',
            WebkitMaskComposite: 'xor',
            maskComposite: 'exclude',
            opacity: isHovered ? 1 : 0,
            transition: 'opacity 0.3s ease',
          }}
        />

        {/* Content */}
        <div style={{ position: 'relative', zIndex: 1 }}>{children}</div>
      </motion.div>
    );
  }
);

AnimatedCard.displayName = 'AnimatedCard';

export default AnimatedCard;
