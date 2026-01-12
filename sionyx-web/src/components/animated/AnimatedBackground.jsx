/**
 * Animated Background Component
 * Lightweight CSS-only background with gradient and subtle animation
 */

import { memo } from 'react';
import './AnimatedBackground.css';

const AnimatedBackground = memo(() => {
  return (
    <div className="animated-bg">
      {/* Base gradient */}
      <div className="animated-bg__base" />
      
      {/* Subtle animated gradient overlay */}
      <div className="animated-bg__overlay" />
      
      {/* Floating orbs - CSS only */}
      <div className="animated-bg__orb animated-bg__orb--1" />
      <div className="animated-bg__orb animated-bg__orb--2" />
      <div className="animated-bg__orb animated-bg__orb--3" />
      
      {/* Vignette */}
      <div className="animated-bg__vignette" />
    </div>
  );
});

AnimatedBackground.displayName = 'AnimatedBackground';

export default AnimatedBackground;
