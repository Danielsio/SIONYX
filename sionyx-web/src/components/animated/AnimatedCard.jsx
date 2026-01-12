/**
 * Animated Card Component
 * Lightweight card with CSS-only animations for smooth 60fps performance
 */

import { memo } from 'react';
import './AnimatedCard.css';

const AnimatedCard = memo(({
  children,
  onClick,
  variant = 'default', // default, glass, gradient, glow
  delay = 0,
  style = {},
  className = '',
  ...props
}) => {
  // Variant classes
  const variantClass = `animated-card--${variant}`;
  
  return (
    <div
      className={`animated-card ${variantClass} ${className}`}
      onClick={onClick}
      style={{
        animationDelay: `${delay}s`,
        ...style,
      }}
      {...props}
    >
      <div className="animated-card__content">
        {children}
      </div>
    </div>
  );
});

AnimatedCard.displayName = 'AnimatedCard';

export default AnimatedCard;
