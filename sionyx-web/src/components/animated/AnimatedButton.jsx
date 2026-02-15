/**
 * Animated Button Component
 * Premium button with magnetic effect, ripple, and spring physics
 */

import { useRef, useState, useCallback, memo } from 'react';
import { motion, useSpring, useTransform } from 'framer-motion';

const AnimatedButton = memo(
  ({
    children,
    onClick,
    variant = 'primary', // primary, secondary, ghost, glow
    size = 'large',
    icon,
    loading = false,
    disabled = false,
    fullWidth = false,
    magnetic = true,
    style = {},
    ...props
  }) => {
    const buttonRef = useRef(null);
    const [isHovered, setIsHovered] = useState(false);
    const [ripples, setRipples] = useState([]);

    // Spring physics for smooth movement
    const x = useSpring(0, { stiffness: 150, damping: 15 });
    const y = useSpring(0, { stiffness: 150, damping: 15 });
    const scale = useSpring(1, { stiffness: 400, damping: 25 });

    // Glow intensity based on hover
    const glowOpacity = useTransform(scale, [1, 1.05], [0.3, 0.8]);

    const handleMouseMove = useCallback(
      e => {
        if (!magnetic || !buttonRef.current || disabled) return;

        const rect = buttonRef.current.getBoundingClientRect();
        const centerX = rect.left + rect.width / 2;
        const centerY = rect.top + rect.height / 2;

        const distX = e.clientX - centerX;
        const distY = e.clientY - centerY;

        x.set(distX * 0.2);
        y.set(distY * 0.2);
      },
      [magnetic, disabled, x, y]
    );

    const handleMouseEnter = useCallback(() => {
      if (disabled) return;
      setIsHovered(true);
      scale.set(1.05);
    }, [disabled, scale]);

    const handleMouseLeave = useCallback(() => {
      setIsHovered(false);
      x.set(0);
      y.set(0);
      scale.set(1);
    }, [x, y, scale]);

    const handleClick = useCallback(
      e => {
        if (disabled || loading) return;

        // Create ripple effect
        const rect = buttonRef.current.getBoundingClientRect();
        const rippleX = e.clientX - rect.left;
        const rippleY = e.clientY - rect.top;
        const rippleId = Date.now();

        setRipples(prev => [...prev, { id: rippleId, x: rippleX, y: rippleY }]);

        // Remove ripple after animation
        setTimeout(() => {
          setRipples(prev => prev.filter(r => r.id !== rippleId));
        }, 600);

        // Quick scale feedback
        scale.set(0.95);
        setTimeout(() => scale.set(1.05), 100);

        onClick?.(e);
      },
      [disabled, loading, onClick, scale]
    );

    // Variant styles
    const variants = {
      primary: {
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        color: 'white',
        border: 'none',
        glowColor: 'rgba(102, 126, 234, 0.6)',
      },
      secondary: {
        background: 'rgba(255, 255, 255, 0.1)',
        color: 'white',
        border: '1px solid rgba(255, 255, 255, 0.3)',
        glowColor: 'rgba(255, 255, 255, 0.3)',
      },
      ghost: {
        background: 'transparent',
        color: 'white',
        border: '2px solid rgba(255, 255, 255, 0.5)',
        glowColor: 'rgba(255, 255, 255, 0.2)',
      },
      glow: {
        background: 'linear-gradient(135deg, #52c41a 0%, #73d13d 100%)',
        color: 'white',
        border: 'none',
        glowColor: 'rgba(82, 196, 26, 0.6)',
      },
      warning: {
        background: 'linear-gradient(135deg, #faad14 0%, #ffc53d 100%)',
        color: '#1a1a2e',
        border: 'none',
        glowColor: 'rgba(250, 173, 20, 0.6)',
      },
    };

    const currentVariant = variants[variant] || variants.primary;

    // Size styles
    const sizes = {
      small: { height: 40, padding: '0 20px', fontSize: 14, borderRadius: 20 },
      medium: { height: 48, padding: '0 28px', fontSize: 16, borderRadius: 24 },
      large: { height: 56, padding: '0 36px', fontSize: 18, borderRadius: 28 },
    };

    const currentSize = sizes[size] || sizes.large;

    return (
      <motion.button
        ref={buttonRef}
        style={{
          position: 'relative',
          display: 'inline-flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 10,
          cursor: disabled ? 'not-allowed' : 'pointer',
          overflow: 'hidden',
          fontWeight: 'bold',
          fontFamily: 'inherit',
          opacity: disabled ? 0.5 : 1,
          width: fullWidth ? '100%' : 'auto',
          ...currentSize,
          ...currentVariant,
          x,
          y,
          scale,
          ...style,
        }}
        onMouseMove={handleMouseMove}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        onClick={handleClick}
        whileTap={{ scale: 0.95 }}
        {...props}
      >
        {/* Glow Effect */}
        <motion.div
          style={{
            position: 'absolute',
            inset: -2,
            borderRadius: currentSize.borderRadius + 2,
            background: currentVariant.glowColor,
            filter: 'blur(15px)',
            opacity: isHovered ? 0.8 : 0.3,
            zIndex: -1,
          }}
          animate={{
            opacity: isHovered ? 0.8 : 0.3,
            scale: isHovered ? 1.1 : 1,
          }}
          transition={{ duration: 0.3 }}
        />

        {/* Shimmer Effect */}
        <motion.div
          style={{
            position: 'absolute',
            top: 0,
            left: '-100%',
            width: '100%',
            height: '100%',
            background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent)',
            zIndex: 1,
          }}
          animate={isHovered ? { left: '100%' } : { left: '-100%' }}
          transition={{ duration: 0.6, ease: 'easeInOut' }}
        />

        {/* Ripple Effects */}
        {ripples.map(ripple => (
          <motion.span
            key={ripple.id}
            initial={{ scale: 0, opacity: 0.5 }}
            animate={{ scale: 4, opacity: 0 }}
            transition={{ duration: 0.6, ease: 'easeOut' }}
            style={{
              position: 'absolute',
              left: ripple.x,
              top: ripple.y,
              width: 20,
              height: 20,
              marginLeft: -10,
              marginTop: -10,
              borderRadius: '50%',
              background: 'rgba(255, 255, 255, 0.4)',
              pointerEvents: 'none',
            }}
          />
        ))}

        {/* Loading Spinner */}
        {loading && (
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
            style={{
              width: 20,
              height: 20,
              border: '2px solid transparent',
              borderTopColor: 'currentColor',
              borderRadius: '50%',
            }}
          />
        )}

        {/* Icon */}
        {!loading && icon && (
          <motion.span animate={{ rotate: isHovered ? 360 : 0 }} transition={{ duration: 0.5 }}>
            {icon}
          </motion.span>
        )}

        {/* Content */}
        <span style={{ position: 'relative', zIndex: 2 }}>{children}</span>
      </motion.button>
    );
  }
);

AnimatedButton.displayName = 'AnimatedButton';

export default AnimatedButton;
