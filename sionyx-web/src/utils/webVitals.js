import { onCLS, onFCP, onLCP, onTTFB, onINP } from 'web-vitals';

function logMetric({ name, value, rating }) {
  const color = rating === 'good' ? 'green' : rating === 'needs-improvement' ? 'orange' : 'red';
  console.log(
    `%c[Web Vitals] ${name}: ${Math.round(value)}ms (${rating})`,
    `color: ${color}; font-weight: bold`
  );
}

export function initWebVitals() {
  onCLS(logMetric);
  onFCP(logMetric);
  onLCP(logMetric);
  onTTFB(logMetric);
  onINP(logMetric);
}
