/**
 * Animated Button Component
 * Lightweight button with CSS-only animations for smooth 60fps
 */

import { memo } from 'react';
import './AnimatedButton.css';

const AnimatedButton = memo(({
  children,
  onClick,
  variant = 'primary', // primary, secondary, ghost, glow, warning
  size = 'large',
  icon,
  loading = false,
  disabled = false,
  fullWidth = false,
  style = {},
  ...props
}) => {
  const classes = [
    'animated-btn',
    `animated-btn--${variant}`,
    `animated-btn--${size}`,
    fullWidth && 'animated-btn--full',
    disabled && 'animated-btn--disabled',
    loading && 'animated-btn--loading',
  ].filter(Boolean).join(' ');

  return (
    <button
      className={classes}
      onClick={disabled || loading ? undefined : onClick}
      disabled={disabled}
      style={style}
      {...props}
    >
      {loading && (
        <span className="animated-btn__spinner" />
      )}
      {!loading && icon && (
        <span className="animated-btn__icon">{icon}</span>
      )}
      <span className="animated-btn__text">{children}</span>
    </button>
  );
});

AnimatedButton.displayName = 'AnimatedButton';

export default AnimatedButton;
