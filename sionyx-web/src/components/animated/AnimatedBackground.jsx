/**
 * Animated Background Component
 * Balanced: Good looking CSS animations, no JavaScript overhead
 */

import { memo } from 'react';
import './AnimatedBackground.css';

const AnimatedBackground = memo(() => {
  return (
    <div className="animated-bg">
      {/* Base gradient */}
      <div className="animated-bg__base" />
      
      {/* Animated gradient mesh */}
      <div className="animated-bg__mesh" />
      
      {/* Floating orbs */}
      <div className="animated-bg__orb animated-bg__orb--1" />
      <div className="animated-bg__orb animated-bg__orb--2" />
      <div className="animated-bg__orb animated-bg__orb--3" />
      <div className="animated-bg__orb animated-bg__orb--4" />
      
      {/* Subtle grid pattern */}
      <div className="animated-bg__grid" />
      
      {/* Vignette */}
      <div className="animated-bg__vignette" />
    </div>
  );
});

AnimatedBackground.displayName = 'AnimatedBackground';

export default AnimatedBackground;
