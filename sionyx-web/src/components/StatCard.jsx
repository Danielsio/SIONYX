/**
 * StatCard Component
 * Consistent stat card pattern for dashboard statistics
 * Provides unified styling, iconography, and color signals
 */

import { Card, Statistic, Typography } from 'antd';
import { motion } from 'framer-motion';

const { Text } = Typography;

/**
 * StatCard variants:
 * - default: White card with subtle border
 * - filled: Colored background based on variant color
 * - outlined: White card with colored left border accent
 * - gradient: Gradient background header
 */

const StatCard = ({
  title,
  value,
  prefix,
  suffix,
  icon,
  variant = 'default', // default, filled, outlined, gradient
  color = 'primary', // primary, success, warning, error, info
  precision,
  formatter,
  loading = false,
  trend,
  trendValue,
  subtitle,
  onClick,
  style = {},
  delay = 0,
  ...props
}) => {
  // Color configurations
  const colorConfig = {
    primary: {
      main: '#667eea',
      light: 'rgba(102, 126, 234, 0.1)',
      gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    },
    success: {
      main: '#10b981',
      light: 'rgba(16, 185, 129, 0.1)',
      gradient: 'linear-gradient(135deg, #10b981 0%, #34d399 100%)',
    },
    warning: {
      main: '#f59e0b',
      light: 'rgba(245, 158, 11, 0.1)',
      gradient: 'linear-gradient(135deg, #f59e0b 0%, #fbbf24 100%)',
    },
    error: {
      main: '#ef4444',
      light: 'rgba(239, 68, 68, 0.1)',
      gradient: 'linear-gradient(135deg, #ef4444 0%, #f87171 100%)',
    },
    info: {
      main: '#3b82f6',
      light: 'rgba(59, 130, 246, 0.1)',
      gradient: 'linear-gradient(135deg, #3b82f6 0%, #60a5fa 100%)',
    },
  };

  const colors = colorConfig[color] || colorConfig.primary;

  // Get variant-specific styles
  const getVariantStyles = () => {
    switch (variant) {
      case 'filled':
        return {
          card: {
            background: colors.light,
            border: 'none',
          },
          icon: {
            background: 'rgba(255, 255, 255, 0.8)',
            color: colors.main,
          },
          value: {
            color: colors.main,
          },
        };
      case 'outlined':
        return {
          card: {
            borderRight: `4px solid ${colors.main}`,
            borderRadius: '12px',
          },
          icon: {
            background: colors.light,
            color: colors.main,
          },
          value: {
            color: colors.main,
          },
        };
      case 'gradient':
        return {
          card: {
            overflow: 'hidden',
            padding: 0,
          },
          header: {
            background: colors.gradient,
            padding: '16px 20px',
            color: '#fff',
          },
          icon: {
            background: 'rgba(255, 255, 255, 0.2)',
            color: '#fff',
          },
          value: {
            color: '#fff',
          },
        };
      default:
        return {
          card: {},
          icon: {
            background: colors.light,
            color: colors.main,
          },
          value: {
            color: colors.main,
          },
        };
    }
  };

  const variantStyles = getVariantStyles();

  // Trend indicator
  const renderTrend = () => {
    if (!trend || !trendValue) return null;

    const isPositive = trend === 'up';
    const trendColor = isPositive ? '#10b981' : '#ef4444';
    const trendIcon = isPositive ? '↑' : '↓';

    return (
      <Text
        style={{
          fontSize: 12,
          color: trendColor,
          fontWeight: 600,
          marginTop: 4,
          display: 'block',
        }}
      >
        {trendIcon} {trendValue}
      </Text>
    );
  };

  // Gradient variant has special layout
  if (variant === 'gradient') {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{
          duration: 0.4,
          delay,
          ease: [0.25, 0.46, 0.45, 0.94],
        }}
      >
        <Card
          variant='borderless'
          className='stat-card'
          onClick={onClick}
          style={{
            borderRadius: 16,
            overflow: 'hidden',
            cursor: onClick ? 'pointer' : 'default',
            ...style,
          }}
          styles={{ body: { padding: 0 } }}
          {...props}
        >
          <div style={variantStyles.header}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              {icon && (
                <div
                  style={{
                    width: 44,
                    height: 44,
                    borderRadius: 12,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: 20,
                    ...variantStyles.icon,
                  }}
                >
                  {icon}
                </div>
              )}
              <div style={{ flex: 1 }}>
                <Text style={{ color: 'rgba(255,255,255,0.8)', fontSize: 13, display: 'block' }}>
                  {title}
                </Text>
                <div style={{ fontSize: 28, fontWeight: 700, color: '#fff', lineHeight: 1.2 }}>
                  {prefix}
                  {typeof formatter === 'function' ? formatter(value) : value}
                  {suffix}
                </div>
                {renderTrend()}
              </div>
            </div>
          </div>
          {subtitle && (
            <div style={{ padding: '12px 20px', background: '#fff' }}>
              <Text type='secondary' style={{ fontSize: 12 }}>
                {subtitle}
              </Text>
            </div>
          )}
        </Card>
      </motion.div>
    );
  }

  // Default/Filled/Outlined variants
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{
        duration: 0.4,
        delay,
        ease: [0.25, 0.46, 0.45, 0.94],
      }}
    >
      <Card
        variant='borderless'
        className={`stat-card stat-card--${color}`}
        onClick={onClick}
        loading={loading}
        style={{
          borderRadius: 16,
          textAlign: 'center',
          cursor: onClick ? 'pointer' : 'default',
          height: '100%',
          ...variantStyles.card,
          ...style,
        }}
        styles={{
          body: {
            padding: '24px 20px',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 12,
          },
        }}
        {...props}
      >
        {icon && (
          <div
            style={{
              width: 52,
              height: 52,
              borderRadius: 14,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: 24,
              marginBottom: 4,
              ...variantStyles.icon,
            }}
          >
            {icon}
          </div>
        )}

        <Statistic
          title={title}
          value={value}
          prefix={prefix}
          suffix={suffix}
          precision={precision}
          formatter={formatter}
          valueStyle={{
            fontSize: 32,
            fontWeight: 700,
            lineHeight: 1.2,
            ...variantStyles.value,
          }}
        />

        {renderTrend()}

        {subtitle && (
          <Text type='secondary' style={{ fontSize: 12, marginTop: 4 }}>
            {subtitle}
          </Text>
        )}
      </Card>
    </motion.div>
  );
};

/**
 * MiniStatCard - Compact version for inline stats
 */
export const MiniStatCard = ({ label, value, icon, color = 'primary', style = {} }) => {
  const colorConfig = {
    primary: { bg: 'rgba(102, 126, 234, 0.1)', color: '#667eea' },
    success: { bg: 'rgba(16, 185, 129, 0.1)', color: '#10b981' },
    warning: { bg: 'rgba(245, 158, 11, 0.1)', color: '#f59e0b' },
    error: { bg: 'rgba(239, 68, 68, 0.1)', color: '#ef4444' },
    info: { bg: 'rgba(59, 130, 246, 0.1)', color: '#3b82f6' },
  };

  const colors = colorConfig[color] || colorConfig.primary;

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 12,
        padding: '14px 16px',
        background: colors.bg,
        borderRadius: 12,
        border: `1px solid ${colors.bg}`,
        ...style,
      }}
    >
      {icon && <div style={{ color: colors.color, fontSize: 20 }}>{icon}</div>}
      <div style={{ flex: 1 }}>
        <div style={{ color: colors.color, fontWeight: 700, fontSize: 18, lineHeight: 1.2 }}>
          {value}
        </div>
        <Text type='secondary' style={{ fontSize: 12 }}>
          {label}
        </Text>
      </div>
    </div>
  );
};

/**
 * InfoStatCard - For displaying key-value info with icon
 */
export const InfoStatCard = ({ title, children, icon, extra, style = {} }) => {
  return (
    <Card
      title={title}
      extra={extra}
      variant='borderless'
      style={{
        borderRadius: 16,
        height: '100%',
        ...style,
      }}
      styles={{
        header: {
          borderBottom: '1px solid #f0f0f0',
          padding: '16px 20px',
        },
        body: {
          padding: 20,
        },
      }}
    >
      {children}
    </Card>
  );
};

export default StatCard;
