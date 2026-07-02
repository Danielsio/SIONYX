import { useEffect, useState } from 'react';

// Named responsive tiers shared by the shells (index.css media queries use the
// same cut points): mobile <768, tablet 768-1023, desktop 1024-1439, wide >=1440.
const getTier = width => {
  if (width < 768) return 'mobile';
  if (width < 1024) return 'tablet';
  if (width < 1440) return 'desktop';
  return 'wide';
};

const useBreakpoint = () => {
  const [tier, setTier] = useState(() =>
    getTier(typeof window !== 'undefined' ? window.innerWidth : 1280)
  );

  useEffect(() => {
    const onResize = () => setTier(getTier(window.innerWidth));
    onResize();
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  return {
    tier,
    isMobile: tier === 'mobile',
    isTablet: tier === 'tablet',
    isWide: tier === 'wide',
  };
};

export default useBreakpoint;
