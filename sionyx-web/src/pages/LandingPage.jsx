/**
 * SIONYX Landing Page v2.0
 * Premium animated landing experience with immersive motion design
 * Enhanced with refined visuals, better typography, and polished animations
 */

import { useState, useCallback, useEffect, useRef, memo } from 'react';
import { motion, useScroll, useTransform, useSpring, AnimatePresence } from 'framer-motion';
import {
  Form,
  Input,
  Typography,
  Space,
  message,
  Row,
  Col,
  Tag,
  Divider,
  Modal,
} from 'antd';
import {
  DownloadOutlined,
  SettingOutlined,
  TeamOutlined,
  RocketOutlined,
  CrownOutlined,
  UserAddOutlined,
  PhoneOutlined,
  LockOutlined,
  MailOutlined,
  BankOutlined,
  KeyOutlined,
  SafetyOutlined,
  ThunderboltOutlined,
  SafetyCertificateOutlined,
  ClockCircleOutlined,
  DashboardOutlined,
  PrinterOutlined,
  CloudOutlined,
  MobileOutlined,
  ApiOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

import { registerOrganization } from '../services/organizationService';
import { downloadFile, getLatestRelease, formatVersion } from '../services/downloadService';
import {
  AnimatedBackground,
  AnimatedButton,
  AnimatedCard,
  GlowingText,
  GradientText,
} from '../components/animated';

gsap.registerPlugin(ScrollTrigger);

const { Title, Paragraph, Text } = Typography;

// Premium color palette
const colors = {
  primary: '#667eea',
  primaryLight: '#8b9df0',
  secondary: '#764ba2',
  accent: '#ec4899',
  success: '#10b981',
  warning: '#f59e0b',
  info: '#3b82f6',
  cyan: '#06b6d4',
  orange: '#f97316',
};

// ============================================
// Hero Section Component - Premium v2.0
// ============================================
const HeroSection = memo(({ onRegisterClick, onAdminLogin, onDownload, downloadLoading }) => {
  const heroRef = useRef(null);
  const subtitleRef = useRef(null);

  // Parallax effect on scroll
  const { scrollY } = useScroll();
  const y = useTransform(scrollY, [0, 500], [0, 100]);
  const opacity = useTransform(scrollY, [0, 400], [1, 0]);
  const scale = useTransform(scrollY, [0, 400], [1, 0.95]);

  // Subtitle GSAP animation
  useEffect(() => {
    const ctx = gsap.context(() => {
      if (subtitleRef.current) {
        gsap.fromTo(subtitleRef.current, 
          { opacity: 0, y: 20 },
          { opacity: 1, y: 0, duration: 0.8, delay: 0.6, ease: 'power3.out' }
        );
      }
    }, heroRef);
    return () => ctx.revert();
  }, []);

  return (
    <motion.section
      ref={heroRef}
      style={{
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        position: 'relative',
        y,
        opacity,
        scale,
        padding: '20px',
      }}
    >
      {/* Top Navigation Bar */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.8, duration: 0.5 }}
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          padding: '24px 40px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          zIndex: 100,
        }}
      >
        {/* Logo */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div
            style={{
              width: 42,
              height: 42,
              borderRadius: 12,
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 4px 20px rgba(102, 126, 234, 0.4)',
            }}
          >
            <span style={{ color: '#fff', fontSize: 18, fontWeight: 800 }}>S</span>
          </div>
          <span style={{ color: '#fff', fontSize: 20, fontWeight: 700, letterSpacing: 2 }}>
            SIONYX
          </span>
        </div>

        {/* Admin Button */}
        <AnimatedButton
          variant="ghost"
          size="medium"
          icon={<CrownOutlined />}
          onClick={onAdminLogin}
          style={{
            background: 'rgba(255,255,255,0.1)',
            backdropFilter: 'blur(10px)',
            border: '1px solid rgba(255,255,255,0.2)',
            color: '#fff',
          }}
        >
          כניסת מנהל
        </AnimatedButton>
      </motion.div>

      {/* Version Badge */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4, duration: 0.5 }}
        style={{ marginBottom: 24 }}
      >
        <Tag
          style={{
            background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.2) 0%, rgba(118, 75, 162, 0.2) 100%)',
            border: '1px solid rgba(102, 126, 234, 0.3)',
            borderRadius: 20,
            padding: '6px 16px',
            color: '#a5b4fc',
            fontSize: 13,
            fontWeight: 500,
          }}
        >
          <RocketOutlined style={{ marginLeft: 6 }} />
          גרסה 2.0 - חדש!
        </Tag>
      </motion.div>

      {/* Main Title */}
      <div style={{ textAlign: 'center', marginBottom: 20 }}>
        <h1
          style={{
            fontSize: 'clamp(3.5rem, 12vw, 8rem)',
            fontWeight: 900,
            color: 'white',
            margin: 0,
            letterSpacing: '0.12em',
            fontFamily: "'Inter', 'Segoe UI', sans-serif",
            direction: 'ltr',
            display: 'flex',
            justifyContent: 'center',
            lineHeight: 1,
          }}
        >
          {'SIONYX'.split('').map((letter, i) => (
            <motion.span
              key={i}
              initial={{ opacity: 0, y: 40, scale: 0.8 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              transition={{
                duration: 0.5,
                delay: 0.1 + i * 0.04,
                ease: [0.25, 0.46, 0.45, 0.94],
              }}
              style={{
                display: 'inline-block',
                textShadow: '0 0 80px rgba(102, 126, 234, 0.6)',
              }}
              whileHover={{
                scale: 1.1,
                color: colors.primary,
                transition: { duration: 0.2 },
              }}
            >
              {letter}
            </motion.span>
          ))}
        </h1>
      </div>

      {/* Tagline */}
      <motion.div
        ref={subtitleRef}
        style={{
          textAlign: 'center',
          marginBottom: 16,
        }}
      >
        <h2
          style={{
            fontSize: 'clamp(1.5rem, 4vw, 2.2rem)',
            fontWeight: 600,
            color: '#fff',
            margin: 0,
            lineHeight: 1.3,
          }}
        >
          ניהול זמן מחשבים והדפסות
        </h2>
      </motion.div>

      {/* Subtitle */}
      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.8, duration: 0.6 }}
        style={{
          fontSize: 'clamp(1rem, 2.5vw, 1.25rem)',
          color: 'rgba(255, 255, 255, 0.7)',
          maxWidth: 550,
          textAlign: 'center',
          lineHeight: 1.7,
          fontWeight: 400,
          marginBottom: 40,
          padding: '0 20px',
        }}
      >
        פתרון מקצועי לניהול זמני שימוש במחשבים, אישורי הדפסה ובקרת גישה למוסדות וארגונים
      </motion.p>

      {/* CTA Buttons */}
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 1, duration: 0.5 }}
        style={{ display: 'flex', gap: 16, flexWrap: 'wrap', justifyContent: 'center' }}
      >
        <AnimatedButton
          variant="primary"
          size="large"
          icon={<RocketOutlined />}
          onClick={onRegisterClick}
          style={{ 
            padding: '0 40px',
            height: 54,
            fontSize: 16,
            fontWeight: 600,
            boxShadow: '0 8px 30px rgba(102, 126, 234, 0.4)',
          }}
        >
          התחל עכשיו - חינם
        </AnimatedButton>
        <AnimatedButton
          variant="ghost"
          size="large"
          icon={<DownloadOutlined />}
          loading={downloadLoading}
          onClick={onDownload}
          style={{ 
            padding: '0 32px',
            height: 54,
            fontSize: 16,
            background: 'rgba(255,255,255,0.1)',
            border: '1px solid rgba(255,255,255,0.25)',
            color: '#fff',
          }}
        >
          {downloadLoading ? 'מוריד...' : 'הורד תוכנה'}
        </AnimatedButton>
      </motion.div>

      {/* Trust Badges */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1.4, duration: 0.5 }}
        style={{
          marginTop: 50,
          display: 'flex',
          gap: 32,
          flexWrap: 'wrap',
          justifyContent: 'center',
          alignItems: 'center',
        }}
      >
        {[
          { icon: <CheckCircleOutlined />, text: 'התקנה קלה' },
          { icon: <SafetyCertificateOutlined />, text: 'אבטחה מלאה' },
          { icon: <ThunderboltOutlined />, text: 'ביצועים מהירים' },
        ].map((badge, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 1.5 + i * 0.1 }}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              color: 'rgba(255,255,255,0.6)',
              fontSize: 14,
            }}
          >
            <span style={{ color: colors.success }}>{badge.icon}</span>
            {badge.text}
          </motion.div>
        ))}
      </motion.div>

      {/* Scroll Indicator */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 2 }}
        style={{
          position: 'absolute',
          bottom: 30,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 8,
        }}
      >
        <Text style={{ color: 'rgba(255,255,255,0.4)', fontSize: 13 }}>גלול למטה</Text>
        <motion.div
          animate={{ y: [0, 8, 0] }}
          transition={{ duration: 1.5, repeat: Infinity, ease: 'easeInOut' }}
          style={{
            width: 28,
            height: 44,
            border: '2px solid rgba(255,255,255,0.2)',
            borderRadius: 14,
            display: 'flex',
            justifyContent: 'center',
            paddingTop: 8,
          }}
        >
          <motion.div
            animate={{ y: [0, 12, 0], opacity: [1, 0.2, 1] }}
            transition={{ duration: 1.5, repeat: Infinity, ease: 'easeInOut' }}
            style={{
              width: 4,
              height: 8,
              background: 'rgba(255,255,255,0.5)',
              borderRadius: 2,
            }}
          />
        </motion.div>
      </motion.div>
    </motion.section>
  );
});

HeroSection.displayName = 'HeroSection';

// ============================================
// Premium Feature Card Component
// ============================================
const FeatureCard = memo(({ icon, title, description, color, delay = 0 }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-50px' }}
      transition={{ duration: 0.5, delay }}
      whileHover={{ y: -8, transition: { duration: 0.2 } }}
      style={{ height: '100%' }}
    >
      <div
        style={{
          height: '100%',
          padding: '32px 28px',
          background: 'rgba(255,255,255,0.03)',
          backdropFilter: 'blur(20px)',
          borderRadius: 20,
          border: '1px solid rgba(255,255,255,0.08)',
          display: 'flex',
          flexDirection: 'column',
          transition: 'all 0.3s ease',
          cursor: 'default',
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.background = 'rgba(255,255,255,0.06)';
          e.currentTarget.style.borderColor = `${color}40`;
          e.currentTarget.style.boxShadow = `0 20px 40px rgba(0,0,0,0.2), 0 0 60px ${color}15`;
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.background = 'rgba(255,255,255,0.03)';
          e.currentTarget.style.borderColor = 'rgba(255,255,255,0.08)';
          e.currentTarget.style.boxShadow = 'none';
        }}
      >
        {/* Icon Container */}
        <div
          style={{
            width: 64,
            height: 64,
            borderRadius: 16,
            background: `linear-gradient(135deg, ${color}20 0%, ${color}10 100%)`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            marginBottom: 24,
            border: `1px solid ${color}30`,
          }}
        >
          <span style={{ fontSize: 28, color }}>{icon}</span>
        </div>

        {/* Title */}
        <h3
          style={{
            color: '#fff',
            fontSize: 20,
            fontWeight: 600,
            margin: '0 0 12px 0',
            lineHeight: 1.3,
          }}
        >
          {title}
        </h3>

        {/* Description */}
        <p
          style={{
            color: 'rgba(255,255,255,0.6)',
            fontSize: 15,
            lineHeight: 1.7,
            margin: 0,
            flex: 1,
          }}
        >
          {description}
        </p>
      </div>
    </motion.div>
  );
});

FeatureCard.displayName = 'FeatureCard';

// ============================================
// Features Section Component - Premium v2.0
// ============================================
const FeaturesSection = memo(() => {
  const features = [
    {
      icon: <ClockCircleOutlined />,
      title: 'ניהול זמן חכם',
      description: 'שליטה מלאה בזמני השימוש במחשבים עם ממשק אינטואיטיבי. הגדר מגבלות יומיות, שבועיות או חודשיות.',
      color: colors.primary,
    },
    {
      icon: <PrinterOutlined />,
      title: 'בקרת הדפסות',
      description: 'ניהול אישורי הדפסה לכל משתמש. עקוב אחר כמויות הדפסה והגדר מכסות חכמות.',
      color: colors.orange,
    },
    {
      icon: <DashboardOutlined />,
      title: 'דשבורד מתקדם',
      description: 'סטטיסטיקות מפורטות ונתונים בזמן אמת על פעילות המשתמשים והמחשבים.',
      color: colors.cyan,
    },
    {
      icon: <TeamOutlined />,
      title: 'ניהול משתמשים',
      description: 'הוספה, עריכה וניהול משתמשים בקלות. הגדר הרשאות והקצאות לכל משתמש.',
      color: colors.success,
    },
    {
      icon: <SafetyCertificateOutlined />,
      title: 'אבטחה מתקדמת',
      description: 'הגנה על הארגון עם מערכת הרשאות חכמה, בקרות גישה והצפנת נתונים.',
      color: colors.secondary,
    },
    {
      icon: <CloudOutlined />,
      title: 'גיבוי ענן',
      description: 'כל הנתונים מגובים בענן באופן אוטומטי. גישה מכל מקום בכל זמן.',
      color: colors.info,
    },
  ];

  return (
    <section style={{ padding: '100px 20px', position: 'relative', zIndex: 1 }}>
      {/* Section Header */}
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.6 }}
        style={{ textAlign: 'center', marginBottom: 70, maxWidth: 700, margin: '0 auto 70px' }}
      >
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
        >
          <Tag
            style={{
              background: 'rgba(102, 126, 234, 0.15)',
              border: '1px solid rgba(102, 126, 234, 0.3)',
              borderRadius: 20,
              padding: '5px 14px',
              color: colors.primaryLight,
              fontSize: 13,
              fontWeight: 500,
              marginBottom: 20,
            }}
          >
            יתרונות המערכת
          </Tag>
        </motion.div>
        
        <Title 
          level={2} 
          style={{ 
            color: 'white', 
            fontSize: 'clamp(1.8rem, 4vw, 2.5rem)',
            fontWeight: 700,
            marginBottom: 16,
            lineHeight: 1.3,
          }}
        >
          כל מה שצריך לניהול יעיל
        </Title>
        
        <Paragraph 
          style={{ 
            color: 'rgba(255,255,255,0.6)', 
            fontSize: 'clamp(1rem, 2vw, 1.1rem)',
            margin: 0,
            lineHeight: 1.7,
          }}
        >
          מערכת SIONYX מספקת את כל הכלים הנדרשים לניהול זמני מחשב והדפסות בארגון שלך
        </Paragraph>
      </motion.div>

      {/* Features Grid */}
      <Row gutter={[24, 24]} justify="center" style={{ maxWidth: 1200, margin: '0 auto' }}>
        {features.map((feature, index) => (
          <Col xs={24} sm={12} lg={8} key={index}>
            <FeatureCard
              icon={feature.icon}
              title={feature.title}
              description={feature.description}
              color={feature.color}
              delay={index * 0.08}
            />
          </Col>
        ))}
      </Row>
    </section>
  );
});

FeaturesSection.displayName = 'FeaturesSection';

// ============================================
// Stats Section Component - Social Proof
// ============================================
const StatsSection = memo(() => {
  const stats = [
    { value: '50+', label: 'ארגונים פעילים', color: colors.primary },
    { value: '1,000+', label: 'משתמשים רשומים', color: colors.success },
    { value: '99.9%', label: 'זמינות שרת', color: colors.cyan },
    { value: '24/7', label: 'תמיכה טכנית', color: colors.warning },
  ];

  return (
    <section style={{ padding: '60px 20px', position: 'relative', zIndex: 1 }}>
      <div
        style={{
          maxWidth: 1000,
          margin: '0 auto',
          background: 'rgba(255,255,255,0.03)',
          backdropFilter: 'blur(20px)',
          borderRadius: 24,
          border: '1px solid rgba(255,255,255,0.08)',
          padding: '40px 20px',
        }}
      >
        <Row gutter={[20, 30]} justify="center" align="middle">
          {stats.map((stat, index) => (
            <Col xs={12} sm={6} key={index}>
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1, duration: 0.5 }}
                style={{ textAlign: 'center' }}
              >
                <div
                  style={{
                    fontSize: 'clamp(2rem, 5vw, 2.8rem)',
                    fontWeight: 800,
                    color: stat.color,
                    lineHeight: 1.2,
                    marginBottom: 8,
                  }}
                >
                  {stat.value}
                </div>
                <div
                  style={{
                    fontSize: 'clamp(0.8rem, 2vw, 0.95rem)',
                    color: 'rgba(255,255,255,0.6)',
                    fontWeight: 500,
                  }}
                >
                  {stat.label}
                </div>
              </motion.div>
            </Col>
          ))}
        </Row>
      </div>
    </section>
  );
});

StatsSection.displayName = 'StatsSection';

// ============================================
// Action Cards Section Component - Premium v2.0
// ============================================
const ActionCardsSection = memo(({ 
  onRegisterClick, 
  onAdminLogin, 
  onDownload, 
  downloadLoading, 
  releaseInfo 
}) => {
  return (
    <section style={{ padding: '80px 20px 100px', position: 'relative', zIndex: 1 }}>
      {/* Section Header */}
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.6 }}
        style={{ textAlign: 'center', marginBottom: 50 }}
      >
        <Title 
          level={2} 
          style={{ 
            color: 'white', 
            fontSize: 'clamp(1.8rem, 4vw, 2.5rem)',
            fontWeight: 700,
            marginBottom: 16,
          }}
        >
          מוכן להתחיל?
        </Title>
        <Paragraph 
          style={{ 
            color: 'rgba(255,255,255,0.6)', 
            fontSize: 'clamp(1rem, 2vw, 1.1rem)',
            margin: 0,
          }}
        >
          בחר את הפעולה המתאימה לך
        </Paragraph>
      </motion.div>

      <Row gutter={[24, 24]} justify="center" style={{ maxWidth: 1100, margin: '0 auto' }}>
        {/* Registration Card - Main CTA */}
        <Col xs={24}>
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
            whileHover={{ y: -4, transition: { duration: 0.2 } }}
          >
            <div
              onClick={onRegisterClick}
              style={{
                padding: 'clamp(40px, 6vw, 60px) clamp(24px, 4vw, 50px)',
                textAlign: 'center',
                cursor: 'pointer',
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                borderRadius: 24,
                boxShadow: '0 20px 60px rgba(102, 126, 234, 0.35)',
                position: 'relative',
                overflow: 'hidden',
              }}
            >
              {/* Decorative elements */}
              <div
                style={{
                  position: 'absolute',
                  top: -50,
                  right: -50,
                  width: 200,
                  height: 200,
                  borderRadius: '50%',
                  background: 'rgba(255,255,255,0.1)',
                }}
              />
              <div
                style={{
                  position: 'absolute',
                  bottom: -30,
                  left: -30,
                  width: 150,
                  height: 150,
                  borderRadius: '50%',
                  background: 'rgba(255,255,255,0.08)',
                }}
              />

              <div style={{ position: 'relative', zIndex: 1 }}>
                <motion.div
                  animate={{ scale: [1, 1.05, 1] }}
                  transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }}
                  style={{
                    width: 80,
                    height: 80,
                    borderRadius: 20,
                    background: 'rgba(255,255,255,0.2)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    margin: '0 auto 24px',
                  }}
                >
                  <UserAddOutlined style={{ fontSize: 40, color: '#fff' }} />
                </motion.div>

                <h2
                  style={{
                    color: 'white',
                    margin: '0 0 12px',
                    fontSize: 'clamp(1.5rem, 4vw, 2rem)',
                    fontWeight: 700,
                  }}
                >
                  רישום ארגון חדש
                </h2>
                
                <p
                  style={{
                    color: 'rgba(255,255,255,0.9)',
                    fontSize: 'clamp(1rem, 2vw, 1.1rem)',
                    marginBottom: 28,
                    maxWidth: 450,
                    margin: '0 auto 28px',
                    lineHeight: 1.6,
                  }}
                >
                  צור ארגון חדש וחשבון מנהל בכמה צעדים פשוטים
                </p>

                <AnimatedButton
                  variant="secondary"
                  size="large"
                  icon={<RocketOutlined />}
                  style={{ 
                    background: 'white', 
                    color: colors.primary,
                    border: 'none',
                    fontWeight: 600,
                    padding: '0 40px',
                    height: 52,
                  }}
                >
                  התחל עכשיו - חינם
                </AnimatedButton>
              </div>
            </div>
          </motion.div>
        </Col>

        {/* Download Card */}
        <Col xs={24} md={12}>
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.1, duration: 0.5 }}
            whileHover={{ y: -4, transition: { duration: 0.2 } }}
            style={{ height: '100%' }}
          >
            <div
              style={{
                height: '100%',
                padding: '36px 32px',
                textAlign: 'center',
                background: 'rgba(255,255,255,0.03)',
                backdropFilter: 'blur(20px)',
                borderRadius: 20,
                border: '1px solid rgba(255,255,255,0.08)',
                display: 'flex',
                flexDirection: 'column',
              }}
            >
              <div
                style={{
                  width: 64,
                  height: 64,
                  borderRadius: 16,
                  background: `linear-gradient(135deg, ${colors.success}20 0%, ${colors.success}10 100%)`,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  margin: '0 auto 20px',
                  border: `1px solid ${colors.success}30`,
                }}
              >
                <DownloadOutlined style={{ fontSize: 28, color: colors.success }} />
              </div>

              <h3 style={{ color: 'white', margin: '0 0 8px', fontSize: 22, fontWeight: 600 }}>
                הורדת התוכנה
              </h3>
              
              {releaseInfo?.version && releaseInfo.version !== 'Latest' && (
                <Tag 
                  style={{ 
                    alignSelf: 'center',
                    marginBottom: 12,
                    background: `${colors.success}15`,
                    border: `1px solid ${colors.success}30`,
                    color: colors.success,
                    borderRadius: 12,
                    padding: '3px 12px',
                    fontSize: 12,
                    fontWeight: 600,
                  }}
                >
                  {formatVersion(releaseInfo)}
                </Tag>
              )}
              
              <p style={{ color: 'rgba(255,255,255,0.6)', marginBottom: 24, flex: 1, fontSize: 15 }}>
                הורידו את התוכנה להתקנה על מחשבי הארגון
              </p>
              
              <AnimatedButton
                variant="glow"
                size="large"
                icon={<DownloadOutlined />}
                loading={downloadLoading}
                onClick={onDownload}
                fullWidth
                style={{
                  background: colors.success,
                  borderColor: colors.success,
                }}
              >
                {downloadLoading ? 'מוריד...' : 'הורד עכשיו'}
              </AnimatedButton>
            </div>
          </motion.div>
        </Col>

        {/* Already Registered Card */}
        <Col xs={24} md={12}>
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.2, duration: 0.5 }}
            whileHover={{ y: -4, transition: { duration: 0.2 } }}
            style={{ height: '100%' }}
          >
            <div
              style={{
                height: '100%',
                padding: '36px 32px',
                textAlign: 'center',
                background: 'rgba(255,255,255,0.03)',
                backdropFilter: 'blur(20px)',
                borderRadius: 20,
                border: '1px solid rgba(255,255,255,0.08)',
                display: 'flex',
                flexDirection: 'column',
              }}
            >
              <div
                style={{
                  width: 64,
                  height: 64,
                  borderRadius: 16,
                  background: `linear-gradient(135deg, ${colors.warning}20 0%, ${colors.warning}10 100%)`,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  margin: '0 auto 20px',
                  border: `1px solid ${colors.warning}30`,
                }}
              >
                <CrownOutlined style={{ fontSize: 28, color: colors.warning }} />
              </div>

              <h3 style={{ color: 'white', margin: '0 0 8px', fontSize: 22, fontWeight: 600 }}>
                כבר רשום?
              </h3>
              
              <p style={{ color: 'rgba(255,255,255,0.6)', marginBottom: 24, flex: 1, fontSize: 15 }}>
                היכנס לפאנל הניהול לצפייה בנתונים וניהול המשתמשים
              </p>
              
              <AnimatedButton
                variant="warning"
                size="large"
                icon={<CrownOutlined />}
                onClick={onAdminLogin}
                fullWidth
                style={{
                  background: colors.warning,
                  borderColor: colors.warning,
                }}
              >
                כניסה לפאנל ניהול
              </AnimatedButton>
            </div>
          </motion.div>
        </Col>
      </Row>
    </section>
  );
});

ActionCardsSection.displayName = 'ActionCardsSection';

// ============================================
// Registration Modal Component - Premium v2.0
// ============================================
const RegistrationModal = memo(({ 
  open, 
  onClose, 
  onSubmit, 
  loading, 
  form 
}) => {
  const inputStyle = {
    textAlign: 'right',
    height: 50,
    fontSize: 15,
    borderRadius: 12,
    width: '100%',
    border: '1.5px solid #e8e8e8',
    transition: 'all 0.2s ease',
  };

  const labelStyle = { 
    fontSize: 13, 
    fontWeight: 600, 
    color: '#444',
    marginBottom: 6,
  };

  const sectionStyle = {
    padding: 'clamp(20px, 4vw, 28px)',
    borderRadius: 18,
    marginBottom: 20,
  };

  return (
    <Modal
      open={open}
      onCancel={onClose}
      footer={null}
      width="95%"
      centered
      className="registration-modal"
      styles={{ 
        body: { 
          padding: 0, 
          direction: 'rtl',
          maxHeight: '85vh',
          overflowY: 'auto',
        },
        content: {
          maxWidth: 680,
          margin: '0 auto',
          borderRadius: 24,
          overflow: 'hidden',
        },
      }}
      title={null}
      closable={false}
    >
      {/* Custom Header */}
      <div
        style={{
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          padding: 'clamp(24px, 5vw, 36px) clamp(20px, 4vw, 32px)',
          textAlign: 'center',
          position: 'relative',
        }}
      >
        {/* Close Button */}
        <button
          onClick={onClose}
          style={{
            position: 'absolute',
            top: 16,
            left: 16,
            background: 'rgba(255,255,255,0.2)',
            border: 'none',
            borderRadius: 10,
            width: 36,
            height: 36,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#fff',
            fontSize: 18,
            transition: 'background 0.2s',
          }}
          onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.3)'}
          onMouseLeave={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.2)'}
        >
          ×
        </button>

        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ type: 'spring', stiffness: 200, delay: 0.1 }}
          style={{
            width: 72,
            height: 72,
            borderRadius: 18,
            background: 'rgba(255,255,255,0.2)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 16px',
          }}
        >
          <TeamOutlined style={{ fontSize: 36, color: '#fff' }} />
        </motion.div>
        
        <h2 style={{ color: '#fff', margin: '0 0 6px', fontSize: 'clamp(1.3rem, 4vw, 1.6rem)', fontWeight: 700 }}>
          הרשמת ארגון חדש
        </h2>
        <p style={{ color: 'rgba(255,255,255,0.85)', margin: 0, fontSize: 'clamp(0.9rem, 2.5vw, 1rem)' }}>
          מלא את הפרטים ליצירת ארגון וחשבון מנהל
        </p>
      </div>

      {/* Form Body */}
      <div style={{ padding: 'clamp(20px, 4vw, 32px)' }}>
        <Form
          form={form}
          onFinish={onSubmit}
          layout="vertical"
          size="large"
        >
          {/* Organization Details Section */}
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.15 }}
            style={{ 
              ...sectionStyle,
              background: 'linear-gradient(135deg, #f8f9ff 0%, #f2f5ff 100%)', 
              border: '1px solid #e4e9ff',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: 20 }}>
              <div
                style={{
                  width: 40,
                  height: 40,
                  borderRadius: 10,
                  background: `${colors.primary}15`,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  marginLeft: 12,
                }}
              >
                <BankOutlined style={{ fontSize: 20, color: colors.primary }} />
              </div>
              <div>
                <h4 style={{ margin: 0, color: '#333', fontSize: 16, fontWeight: 600 }}>פרטי הארגון</h4>
                <span style={{ fontSize: 12, color: '#888' }}>מידע בסיסי על הארגון</span>
              </div>
            </div>
            
            <Form.Item
              name="organizationName"
              label={<span style={labelStyle}>שם הארגון</span>}
              rules={[
                { required: true, message: 'נא להזין שם ארגון' },
                { min: 2, message: 'שם הארגון חייב להכיל לפחות 2 תווים' }
              ]}
            >
              <Input 
                prefix={<BankOutlined style={{ color: '#bfbfbf' }} />}
                placeholder="לדוגמה: ישיבת אור החיים"
                style={inputStyle}
              />
            </Form.Item>

            <Row gutter={[16, 0]}>
              <Col xs={24} sm={12}>
                <Form.Item
                  name="nedarimMosadId"
                  label={<span style={labelStyle}>מזהה מוסד NEDARIM</span>}
                  rules={[{ required: true, message: 'נא להזין מזהה מוסד' }]}
                >
                  <Input 
                    prefix={<KeyOutlined style={{ color: '#bfbfbf' }} />}
                    placeholder="מזהה המוסד"
                    style={inputStyle}
                  />
                </Form.Item>
              </Col>
              <Col xs={24} sm={12}>
                <Form.Item
                  name="nedarimApiValid"
                  label={<span style={labelStyle}>מפתח API של NEDARIM</span>}
                  rules={[{ required: true, message: 'נא להזין מפתח API' }]}
                >
                  <Input 
                    prefix={<SafetyOutlined style={{ color: '#bfbfbf' }} />}
                    placeholder="מפתח ה-API"
                    style={inputStyle}
                  />
                </Form.Item>
              </Col>
            </Row>
          </motion.div>

          {/* Admin User Section */}
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.25 }}
            style={{ 
              ...sectionStyle,
              background: 'linear-gradient(135deg, #fff9f0 0%, #fff5e6 100%)', 
              border: '1px solid #ffe4c4',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: 20 }}>
              <div
                style={{
                  width: 40,
                  height: 40,
                  borderRadius: 10,
                  background: `${colors.warning}15`,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  marginLeft: 12,
                }}
              >
                <CrownOutlined style={{ fontSize: 20, color: colors.warning }} />
              </div>
              <div>
                <h4 style={{ margin: 0, color: '#333', fontSize: 16, fontWeight: 600 }}>פרטי המנהל הראשי</h4>
                <span style={{ fontSize: 12, color: '#888' }}>יצירת חשבון מנהל לארגון</span>
              </div>
            </div>

            <Row gutter={[16, 0]}>
              <Col xs={24} sm={12}>
                <Form.Item
                  name="adminFirstName"
                  label={<span style={labelStyle}>שם פרטי</span>}
                  rules={[{ required: true, message: 'נא להזין שם פרטי' }]}
                >
                  <Input placeholder="שם פרטי" style={inputStyle} />
                </Form.Item>
              </Col>
              <Col xs={24} sm={12}>
                <Form.Item
                  name="adminLastName"
                  label={<span style={labelStyle}>שם משפחה</span>}
                  rules={[{ required: true, message: 'נא להזין שם משפחה' }]}
                >
                  <Input placeholder="שם משפחה" style={inputStyle} />
                </Form.Item>
              </Col>
            </Row>

            <Form.Item
              name="adminPhone"
              label={<span style={labelStyle}>מספר טלפון (ישמש להתחברות)</span>}
              rules={[
                { required: true, message: 'נא להזין מספר טלפון' },
                { pattern: /^0\d{9}$/, message: 'מספר טלפון לא תקין (10 ספרות)' }
              ]}
            >
              <Input 
                prefix={<PhoneOutlined style={{ color: '#bfbfbf' }} />}
                placeholder="0501234567"
                style={inputStyle}
                maxLength={10}
              />
            </Form.Item>

            <Form.Item
              name="adminPassword"
              label={<span style={labelStyle}>סיסמה</span>}
              rules={[
                { required: true, message: 'נא להזין סיסמה' },
                { min: 6, message: 'הסיסמה חייבת להכיל לפחות 6 תווים' }
              ]}
            >
              <Input.Password 
                prefix={<LockOutlined style={{ color: '#bfbfbf' }} />}
                placeholder="לפחות 6 תווים"
                style={inputStyle}
              />
            </Form.Item>

            <Form.Item
              name="adminEmail"
              label={<span style={labelStyle}>אימייל (אופציונלי)</span>}
              rules={[{ type: 'email', message: 'כתובת אימייל לא תקינה' }]}
              style={{ marginBottom: 0 }}
            >
              <Input 
                prefix={<MailOutlined style={{ color: '#bfbfbf' }} />}
                placeholder="admin@example.com"
                style={inputStyle}
              />
            </Form.Item>
          </motion.div>

          {/* Submit Buttons */}
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.35 }}
            style={{ 
              display: 'flex',
              gap: 12,
              justifyContent: 'center',
              flexWrap: 'wrap',
              paddingTop: 8,
            }}
          >
            <AnimatedButton
              variant="ghost"
              onClick={onClose}
              style={{ 
                color: '#666', 
                borderColor: '#ddd',
                background: '#fff',
                minWidth: 100,
                height: 48,
                borderRadius: 12,
              }}
            >
              ביטול
            </AnimatedButton>
            <AnimatedButton
              variant="primary"
              loading={loading}
              onClick={() => form.submit()}
              icon={<RocketOutlined />}
              style={{ 
                minWidth: 180,
                height: 48,
                borderRadius: 12,
                fontWeight: 600,
              }}
            >
              {loading ? 'יוצר ארגון...' : 'צור ארגון חדש'}
            </AnimatedButton>
          </motion.div>
        </Form>
      </div>
    </Modal>
  );
});

RegistrationModal.displayName = 'RegistrationModal';

// ============================================
// Main Landing Page Component
// ============================================
const LandingPage = memo(() => {
  const [registrationForm] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [downloadLoading, setDownloadLoading] = useState(false);
  const [releaseInfo, setReleaseInfo] = useState(null);
  const [showRegistrationModal, setShowRegistrationModal] = useState(false);
  const navigate = useNavigate();

  // Fetch latest release info on mount
  useEffect(() => {
    let mounted = true;
    const fetchReleaseInfo = async () => {
      try {
        const release = await getLatestRelease();
        if (mounted) setReleaseInfo(release);
      } catch (error) {
        if (mounted) console.warn('Could not fetch release info:', error);
      }
    };
    fetchReleaseInfo();
    return () => { mounted = false; };
  }, []);

  const handleRegistration = useCallback(async (values) => {
    setLoading(true);
    try {
      const result = await registerOrganization(values);
      if (result.success) {
        message.success('הארגון נוצר בהצלחה! כעת תוכל להתחבר עם פרטי המנהל');
        registrationForm.resetFields();
        setShowRegistrationModal(false);
        navigate(`/admin/login?orgId=${result.orgId}`);
      } else {
        message.error(result.error || 'שגיאה ביצירת הארגון');
      }
    } catch {
      message.error('שגיאה ביצירת הארגון');
    } finally {
      setLoading(false);
    }
  }, [registrationForm, navigate]);

  const handleDirectDownload = useCallback(async () => {
    try {
      setDownloadLoading(true);
      
      if (!releaseInfo?.downloadUrl) {
        throw new Error('לא נמצא קישור להורדה');
      }
      
      await downloadFile(releaseInfo.downloadUrl, releaseInfo.fileName);
      message.success('ההורדה הושלמה בהצלחה!');
    } catch (error) {
      console.error('Download error:', error);
      message.error(error.message || 'שגיאה בהורדה. נסה שוב.');
    } finally {
      setDownloadLoading(false);
    }
  }, [releaseInfo]);

  const handleAdminLogin = useCallback(() => {
    navigate('/admin/login');
  }, [navigate]);

  const openRegistrationModal = useCallback(() => {
    setShowRegistrationModal(true);
  }, []);

  const closeRegistrationModal = useCallback(() => {
    setShowRegistrationModal(false);
    registrationForm.resetFields();
  }, [registrationForm]);

  return (
    <div 
      style={{ 
        minHeight: '100vh',
        direction: 'rtl',
        textAlign: 'right',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Animated Background */}
      <AnimatedBackground />

      {/* Content */}
      <div style={{ position: 'relative', zIndex: 1 }}>
        {/* Hero Section */}
        <HeroSection 
          onRegisterClick={openRegistrationModal}
          onAdminLogin={handleAdminLogin}
          onDownload={handleDirectDownload}
          downloadLoading={downloadLoading}
        />

        {/* Features Section */}
        <FeaturesSection />

        {/* Stats Section - Social Proof */}
        <StatsSection />

        {/* Action Cards Section */}
        <ActionCardsSection
          onRegisterClick={openRegistrationModal}
          onAdminLogin={handleAdminLogin}
          onDownload={handleDirectDownload}
          downloadLoading={downloadLoading}
          releaseInfo={releaseInfo}
        />

        {/* Premium Footer */}
        <motion.footer
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          style={{
            padding: '60px 20px 40px',
            borderTop: '1px solid rgba(255,255,255,0.05)',
          }}
        >
          <div style={{ maxWidth: 1100, margin: '0 auto' }}>
            {/* Footer Top */}
            <Row gutter={[40, 40]} justify="space-between" align="top">
              {/* Brand */}
              <Col xs={24} md={8}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
                  <div
                    style={{
                      width: 44,
                      height: 44,
                      borderRadius: 12,
                      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                  >
                    <span style={{ color: '#fff', fontSize: 20, fontWeight: 800 }}>S</span>
                  </div>
                  <span style={{ color: '#fff', fontSize: 22, fontWeight: 700, letterSpacing: 2 }}>
                    SIONYX
                  </span>
                </div>
                <p style={{ color: 'rgba(255,255,255,0.5)', fontSize: 14, lineHeight: 1.7, margin: 0 }}>
                  פתרון מתקדם לניהול זמן מחשבים ואישורי הדפסה למוסדות וארגונים.
                </p>
              </Col>

              {/* Quick Links */}
              <Col xs={12} md={4}>
                <h4 style={{ color: '#fff', fontSize: 15, fontWeight: 600, marginBottom: 16 }}>
                  קישורים מהירים
                </h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                  {[
                    { label: 'דף הבית', action: () => window.scrollTo({ top: 0, behavior: 'smooth' }) },
                    { label: 'כניסת מנהל', action: handleAdminLogin },
                    { label: 'הרשמה', action: openRegistrationModal },
                  ].map((link, i) => (
                    <a
                      key={i}
                      onClick={link.action}
                      style={{
                        color: 'rgba(255,255,255,0.5)',
                        fontSize: 14,
                        cursor: 'pointer',
                        transition: 'color 0.2s',
                      }}
                      onMouseEnter={(e) => e.currentTarget.style.color = colors.primaryLight}
                      onMouseLeave={(e) => e.currentTarget.style.color = 'rgba(255,255,255,0.5)'}
                    >
                      {link.label}
                    </a>
                  ))}
                </div>
              </Col>

              {/* Contact */}
              <Col xs={12} md={4}>
                <h4 style={{ color: '#fff', fontSize: 15, fontWeight: 600, marginBottom: 16 }}>
                  יצירת קשר
                </h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                  <span style={{ color: 'rgba(255,255,255,0.5)', fontSize: 14 }}>
                    <MailOutlined style={{ marginLeft: 8 }} />
                    support@sionyx.co.il
                  </span>
                  <span style={{ color: 'rgba(255,255,255,0.5)', fontSize: 14 }}>
                    <PhoneOutlined style={{ marginLeft: 8 }} />
                    03-1234567
                  </span>
                </div>
              </Col>
            </Row>

            {/* Divider */}
            <div
              style={{
                height: 1,
                background: 'rgba(255,255,255,0.08)',
                margin: '40px 0 24px',
              }}
            />

            {/* Footer Bottom */}
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                flexWrap: 'wrap',
                gap: 16,
              }}
            >
              <Text style={{ color: 'rgba(255,255,255,0.4)', fontSize: 13 }}>
                © 2026 SIONYX. כל הזכויות שמורות.
              </Text>
              <div style={{ display: 'flex', gap: 20 }}>
                {['תנאי שימוש', 'מדיניות פרטיות'].map((item, i) => (
                  <a
                    key={i}
                    href="#"
                    style={{
                      color: 'rgba(255,255,255,0.4)',
                      fontSize: 13,
                      textDecoration: 'none',
                      transition: 'color 0.2s',
                    }}
                    onMouseEnter={(e) => e.currentTarget.style.color = 'rgba(255,255,255,0.7)'}
                    onMouseLeave={(e) => e.currentTarget.style.color = 'rgba(255,255,255,0.4)'}
                  >
                    {item}
                  </a>
                ))}
              </div>
            </div>
          </div>
        </motion.footer>
      </div>

      {/* Registration Modal */}
      <AnimatePresence>
        {showRegistrationModal && (
          <RegistrationModal
            open={showRegistrationModal}
            onClose={closeRegistrationModal}
            onSubmit={handleRegistration}
            loading={loading}
            form={registrationForm}
          />
        )}
      </AnimatePresence>
    </div>
  );
});

LandingPage.displayName = 'LandingPage';

export default LandingPage;
