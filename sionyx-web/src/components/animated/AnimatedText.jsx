/**
 * Animated Text Components
 * Lightweight CSS-based text effects
 */

import { memo } from 'react';
import './AnimatedText.css';

// Gradient text with optional animation
export const GradientText = memo(({
  children,
  gradient = 'linear-gradient(135deg, #667eea, #764ba2, #ec4899)',
  animate = false,
  className = '',
  style = {},
}) => {
  return (
    <span
      className={`gradient-text ${animate ? 'gradient-text--animated' : ''} ${className}`}
      style={{
        background: gradient,
        ...style,
      }}
    >
      {children}
    </span>
  );
});

GradientText.displayName = 'GradientText';

// Glowing text effect
export const GlowingText = memo(({
  children,
  color = '#667eea',
  className = '',
  style = {},
}) => {
  return (
    <span
      className={`glowing-text ${className}`}
      style={{
        '--glow-color': color,
        ...style,
      }}
    >
      {children}
    </span>
  );
});

GlowingText.displayName = 'GlowingText';

// Default export
const AnimatedText = GradientText;
export default AnimatedText;
