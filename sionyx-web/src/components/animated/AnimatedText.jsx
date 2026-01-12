/**
 * Animated Text Component
 * Premium text animations with letter-by-letter reveals, gradients, and effects
 */

import { memo, useMemo } from 'react';
import { motion } from 'framer-motion';

// Letter-by-letter animation component
const AnimatedLetters = memo(({ 
  text, 
  delay = 0, 
  stagger = 0.03,
  style = {},
  className = '',
}) => {
  const letters = useMemo(() => text.split(''), [text]);

  const container = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: stagger,
        delayChildren: delay,
      },
    },
  };

  const child = {
    hidden: {
      opacity: 0,
      y: 40,
      rotateX: -90,
    },
    visible: {
      opacity: 1,
      y: 0,
      rotateX: 0,
      transition: {
        type: 'spring',
        damping: 12,
        stiffness: 200,
      },
    },
  };

  return (
    <motion.span
      className={className}
      variants={container}
      initial="hidden"
      animate="visible"
      style={{ display: 'inline-flex', perspective: 500, ...style }}
    >
      {letters.map((letter, index) => (
        <motion.span
          key={index}
          variants={child}
          style={{
            display: 'inline-block',
            transformOrigin: 'bottom center',
          }}
        >
          {letter === ' ' ? '\u00A0' : letter}
        </motion.span>
      ))}
    </motion.span>
  );
});

AnimatedLetters.displayName = 'AnimatedLetters';

// Gradient text with animation
const GradientText = memo(({
  children,
  gradient = 'linear-gradient(135deg, #667eea 0%, #764ba2 50%, #ec4899 100%)',
  animate = true,
  style = {},
  className = '',
}) => {
  return (
    <motion.span
      className={className}
      style={{
        background: gradient,
        backgroundSize: animate ? '200% 200%' : '100% 100%',
        WebkitBackgroundClip: 'text',
        WebkitTextFillColor: 'transparent',
        backgroundClip: 'text',
        ...style,
      }}
      animate={animate ? {
        backgroundPosition: ['0% 50%', '100% 50%', '0% 50%'],
      } : undefined}
      transition={animate ? {
        duration: 5,
        repeat: Infinity,
        ease: 'linear',
      } : undefined}
    >
      {children}
    </motion.span>
  );
});

GradientText.displayName = 'GradientText';

// Glowing text effect
const GlowingText = memo(({
  children,
  color = '#667eea',
  glowIntensity = 1,
  pulse = true,
  style = {},
  className = '',
}) => {
  const glowStyle = useMemo(() => ({
    textShadow: `
      0 0 ${10 * glowIntensity}px ${color},
      0 0 ${20 * glowIntensity}px ${color},
      0 0 ${40 * glowIntensity}px ${color},
      0 0 ${80 * glowIntensity}px ${color}
    `,
    ...style,
  }), [color, glowIntensity, style]);

  if (!pulse) {
    return (
      <span className={className} style={glowStyle}>
        {children}
      </span>
    );
  }

  return (
    <motion.span
      className={className}
      style={style}
      animate={{
        textShadow: [
          `0 0 ${10 * glowIntensity}px ${color}, 0 0 ${20 * glowIntensity}px ${color}`,
          `0 0 ${20 * glowIntensity}px ${color}, 0 0 ${40 * glowIntensity}px ${color}, 0 0 ${60 * glowIntensity}px ${color}`,
          `0 0 ${10 * glowIntensity}px ${color}, 0 0 ${20 * glowIntensity}px ${color}`,
        ],
      }}
      transition={{
        duration: 2,
        repeat: Infinity,
        ease: 'easeInOut',
      }}
    >
      {children}
    </motion.span>
  );
});

GlowingText.displayName = 'GlowingText';

// Typewriter effect
const TypewriterText = memo(({
  text,
  delay = 0,
  speed = 0.05,
  cursor = true,
  onComplete,
  style = {},
  className = '',
}) => {
  const letters = useMemo(() => text.split(''), [text]);

  return (
    <span className={className} style={{ position: 'relative', ...style }}>
      {letters.map((letter, index) => (
        <motion.span
          key={index}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{
            duration: 0.01,
            delay: delay + index * speed,
          }}
          onAnimationComplete={index === letters.length - 1 ? onComplete : undefined}
        >
          {letter}
        </motion.span>
      ))}
      {cursor && (
        <motion.span
          animate={{ opacity: [1, 0, 1] }}
          transition={{ duration: 0.8, repeat: Infinity }}
          style={{ marginRight: 2 }}
        >
          |
        </motion.span>
      )}
    </span>
  );
});

TypewriterText.displayName = 'TypewriterText';

// Word-by-word reveal
const WordReveal = memo(({
  text,
  delay = 0,
  stagger = 0.1,
  style = {},
  className = '',
}) => {
  const words = useMemo(() => text.split(' '), [text]);

  const container = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: stagger,
        delayChildren: delay,
      },
    },
  };

  const child = {
    hidden: {
      opacity: 0,
      y: 20,
      filter: 'blur(10px)',
    },
    visible: {
      opacity: 1,
      y: 0,
      filter: 'blur(0px)',
      transition: {
        duration: 0.5,
        ease: [0.25, 0.46, 0.45, 0.94],
      },
    },
  };

  return (
    <motion.span
      className={className}
      variants={container}
      initial="hidden"
      animate="visible"
      style={{ display: 'inline-flex', flexWrap: 'wrap', gap: '0.3em', ...style }}
    >
      {words.map((word, index) => (
        <motion.span key={index} variants={child}>
          {word}
        </motion.span>
      ))}
    </motion.span>
  );
});

WordReveal.displayName = 'WordReveal';

// Main AnimatedText component with multiple modes
const AnimatedText = memo(({
  children,
  mode = 'letters', // letters, words, gradient, glow, typewriter
  as: Component = 'span',
  ...props
}) => {
  const text = typeof children === 'string' ? children : '';

  switch (mode) {
    case 'letters':
      return <AnimatedLetters text={text} {...props} />;
    case 'words':
      return <WordReveal text={text} {...props} />;
    case 'gradient':
      return <GradientText {...props}>{children}</GradientText>;
    case 'glow':
      return <GlowingText {...props}>{children}</GlowingText>;
    case 'typewriter':
      return <TypewriterText text={text} {...props} />;
    default:
      return <span {...props}>{children}</span>;
  }
});

AnimatedText.displayName = 'AnimatedText';

export default AnimatedText;
export { AnimatedLetters, GradientText, GlowingText, TypewriterText, WordReveal };
