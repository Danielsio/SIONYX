/**
 * SIONYX Landing Page
 * Premium animated landing experience with immersive motion design
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

// ============================================
// Hero Section Component
// ============================================
const HeroSection = memo(({ onRegisterClick, onAdminLogin }) => {
  const heroRef = useRef(null);
  const titleRef = useRef(null);
  const subtitleRef = useRef(null);

  // Parallax effect on scroll
  const { scrollY } = useScroll();
  const y = useTransform(scrollY, [0, 500], [0, 150]);
  const opacity = useTransform(scrollY, [0, 300], [1, 0]);
  const scale = useTransform(scrollY, [0, 300], [1, 0.9]);

  // Mouse parallax
  const mouseX = useSpring(0, { stiffness: 50, damping: 20 });
  const mouseY = useSpring(0, { stiffness: 50, damping: 20 });

  useEffect(() => {
    const handleMouseMove = (e) => {
      const { clientX, clientY } = e;
      const { innerWidth, innerHeight } = window;
      mouseX.set((clientX / innerWidth - 0.5) * 30);
      mouseY.set((clientY / innerHeight - 0.5) * 30);
    };

    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, [mouseX, mouseY]);

  // GSAP entrance animation
  useEffect(() => {
    const ctx = gsap.context(() => {
      const tl = gsap.timeline();

      // Title animation - faster and more reliable
      const spans = titleRef.current?.querySelectorAll('span') || [];
      if (spans.length > 0) {
        tl.from(spans, {
          opacity: 0,
          y: 50,
          rotateX: -45,
          stagger: 0.05,
          duration: 0.6,
          ease: 'power3.out',
        });
      }

      // Subtitle animation
      tl.from(subtitleRef.current, {
        opacity: 0,
        y: 30,
        filter: 'blur(10px)',
        duration: 0.8,
        ease: 'power3.out',
      }, '-=0.3');

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
      {/* Admin Button */}
      <motion.div
        initial={{ opacity: 0, x: -50 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ delay: 1.5, duration: 0.5 }}
        style={{
          position: 'absolute',
          top: 30,
          left: 30,
          zIndex: 100,
        }}
      >
        <AnimatedButton
          variant="secondary"
          size="medium"
          icon={<CrownOutlined />}
          onClick={onAdminLogin}
        >
          כניסת מנהל
        </AnimatedButton>
      </motion.div>

      {/* Main Title */}
      <motion.div
        style={{
          x: mouseX,
          y: mouseY,
          textAlign: 'center',
          marginBottom: 30,
        }}
      >
        <h1
          ref={titleRef}
          style={{
            fontSize: 'clamp(4rem, 15vw, 10rem)',
            fontWeight: 900,
            color: 'white',
            margin: 0,
            letterSpacing: '0.15em',
            fontFamily: "'Segoe UI', 'Inter', sans-serif",
            perspective: 1000,
            direction: 'ltr', // Force LTR for brand name
            display: 'flex',
            justifyContent: 'center',
            unicodeBidi: 'bidi-override',
          }}
        >
          {'SIONYX'.split('').map((letter, i) => (
            <motion.span
              key={i}
              style={{
                display: 'inline-block',
                textShadow: '0 0 60px rgba(94, 129, 244, 0.8), 0 0 120px rgba(94, 129, 244, 0.4)',
              }}
              whileHover={{
                scale: 1.2,
                color: '#667eea',
                textShadow: '0 0 80px rgba(94, 129, 244, 1), 0 0 160px rgba(94, 129, 244, 0.6)',
              }}
              transition={{ type: 'spring', stiffness: 300 }}
            >
              {letter}
            </motion.span>
          ))}
        </h1>
      </motion.div>

      {/* Subtitle */}
      <motion.p
        ref={subtitleRef}
        style={{
          fontSize: 'clamp(1rem, 3vw, 1.5rem)',
          color: 'rgba(255, 255, 255, 0.85)',
          maxWidth: 600,
          textAlign: 'center',
          lineHeight: 1.8,
          fontWeight: 300,
          marginBottom: 50,
        }}
      >
        <GradientText animate gradient="linear-gradient(90deg, #a5b4fc, #818cf8, #c4b5fd, #a5b4fc)">
          פתרון מתקדם לניהול זמן מחשבים ואישורי הדפסה
        </GradientText>
      </motion.p>

      {/* CTA Button */}
      <motion.div
        initial={{ opacity: 0, y: 50 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 1.2, duration: 0.6 }}
      >
        <AnimatedButton
          variant="primary"
          size="large"
          icon={<RocketOutlined />}
          onClick={onRegisterClick}
          style={{ padding: '0 50px' }}
        >
          התחל עכשיו
        </AnimatedButton>
      </motion.div>

      {/* Scroll Indicator */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 2 }}
        style={{
          position: 'absolute',
          bottom: 40,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 10,
        }}
      >
        <Text style={{ color: 'rgba(255,255,255,0.5)', fontSize: 14 }}>גלול למטה</Text>
        <motion.div
          animate={{ y: [0, 10, 0] }}
          transition={{ duration: 1.5, repeat: Infinity }}
          style={{
            width: 30,
            height: 50,
            border: '2px solid rgba(255,255,255,0.3)',
            borderRadius: 15,
            display: 'flex',
            justifyContent: 'center',
            paddingTop: 8,
          }}
        >
          <motion.div
            animate={{ y: [0, 15, 0], opacity: [1, 0.3, 1] }}
            transition={{ duration: 1.5, repeat: Infinity }}
            style={{
              width: 6,
              height: 10,
              background: 'rgba(255,255,255,0.6)',
              borderRadius: 3,
            }}
          />
        </motion.div>
      </motion.div>
    </motion.section>
  );
});

HeroSection.displayName = 'HeroSection';

// ============================================
// Features Section Component
// ============================================
const FeaturesSection = memo(() => {
  const features = [
    {
      icon: <ClockCircleOutlined style={{ fontSize: 48 }} />,
      title: 'ניהול זמן חכם',
      description: 'שליטה מלאה בזמני השימוש במחשבים עם ממשק אינטואיטיבי',
      color: '#667eea',
    },
    {
      icon: <SafetyCertificateOutlined style={{ fontSize: 48 }} />,
      title: 'אבטחה מתקדמת',
      description: 'הגנה על הארגון עם מערכת הרשאות חכמה ובקרות גישה',
      color: '#52c41a',
    },
    {
      icon: <ThunderboltOutlined style={{ fontSize: 48 }} />,
      title: 'ביצועים מהירים',
      description: 'תוכנה קלה ויעילה שלא מעמיסה על המחשבים',
      color: '#faad14',
    },
  ];

  return (
    <section style={{ padding: '100px 20px', position: 'relative', zIndex: 1 }}>
      <motion.div
        initial={{ opacity: 0, y: 50 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.8 }}
        style={{ textAlign: 'center', marginBottom: 60 }}
      >
        <Title level={2} style={{ color: 'white', fontSize: 'clamp(2rem, 5vw, 3rem)' }}>
          <GlowingText color="#667eea" glowIntensity={0.5}>
            למה SIONYX?
          </GlowingText>
        </Title>
      </motion.div>

      <Row gutter={[30, 30]} justify="center" style={{ maxWidth: 1200, margin: '0 auto' }}>
        {features.map((feature, index) => (
          <Col xs={24} md={8} key={index}>
            <AnimatedCard
              variant="glass"
              delay={index * 0.15}
              style={{ height: '100%', padding: '40px 30px', textAlign: 'center' }}
            >
              <motion.div
                whileHover={{ scale: 1.1, rotate: 5 }}
                style={{
                  color: feature.color,
                  marginBottom: 20,
                  filter: `drop-shadow(0 0 20px ${feature.color})`,
                }}
              >
                {feature.icon}
              </motion.div>
              <Title level={4} style={{ color: 'white', marginBottom: 15 }}>
                {feature.title}
              </Title>
              <Paragraph style={{ color: 'rgba(255,255,255,0.7)', margin: 0, fontSize: 16 }}>
                {feature.description}
              </Paragraph>
            </AnimatedCard>
          </Col>
        ))}
      </Row>
    </section>
  );
});

FeaturesSection.displayName = 'FeaturesSection';

// ============================================
// Action Cards Section Component
// ============================================
const ActionCardsSection = memo(({ 
  onRegisterClick, 
  onAdminLogin, 
  onDownload, 
  downloadLoading, 
  releaseInfo 
}) => {
  return (
    <section style={{ padding: '80px 20px', position: 'relative', zIndex: 1 }}>
      <Row gutter={[30, 30]} justify="center" style={{ maxWidth: 1100, margin: '0 auto' }}>
        {/* Registration Card */}
        <Col xs={24} lg={24}>
          <AnimatedCard
            variant="glow"
            onClick={onRegisterClick}
            delay={0}
            style={{
              padding: '60px 40px',
              textAlign: 'center',
              cursor: 'pointer',
              boxShadow: '0 20px 60px rgba(94, 129, 244, 0.4)',
            }}
          >
            <motion.div
              animate={{ 
                rotate: [0, 5, -5, 0],
                scale: [1, 1.05, 1],
              }}
              transition={{ duration: 4, repeat: Infinity }}
            >
              <UserAddOutlined style={{ 
                fontSize: 64, 
                color: 'white',
                filter: 'drop-shadow(0 4px 20px rgba(0,0,0,0.3))',
              }} />
            </motion.div>
            <Title level={2} style={{ color: 'white', margin: '25px 0 15px', fontSize: 32 }}>
              שלום לך מנהל יקר
            </Title>
            <Paragraph style={{ 
              color: 'rgba(255,255,255,0.9)', 
              fontSize: 18, 
              marginBottom: 30,
              maxWidth: 500,
              margin: '0 auto 30px',
            }}>
              הירשם כאן ליצירת ארגון חדש וחשבון מנהל
            </Paragraph>
            <AnimatedButton
              variant="secondary"
              size="large"
              icon={<TeamOutlined />}
              style={{ 
                background: 'white', 
                color: '#667eea',
                border: 'none',
              }}
            >
              התחל הרשמה
            </AnimatedButton>
          </AnimatedCard>
        </Col>

        {/* Download Card */}
        <Col xs={24} md={12}>
          <AnimatedCard
            variant="glass"
            delay={0.2}
            style={{ height: '100%', padding: '40px 30px', textAlign: 'center' }}
          >
            <motion.div
              animate={{ y: [0, -10, 0] }}
              transition={{ duration: 2, repeat: Infinity }}
            >
              <RocketOutlined style={{ 
                fontSize: 56, 
                color: '#52c41a',
                filter: 'drop-shadow(0 0 20px rgba(82, 196, 26, 0.5))',
              }} />
            </motion.div>
            <Title level={3} style={{ color: 'white', marginTop: 20 }}>
              הורדת התוכנה
            </Title>
            {releaseInfo?.version && releaseInfo.version !== 'Latest' && (
              <Tag 
                color="green" 
                style={{ 
                  marginBottom: 15,
                  fontWeight: 'bold',
                  fontSize: 13,
                  padding: '4px 12px',
                }}
              >
                {formatVersion(releaseInfo)}
              </Tag>
            )}
            <Paragraph style={{ color: 'rgba(255,255,255,0.7)', marginBottom: 25 }}>
              הורידו את התוכנה להתקנה על מחשבי הארגון
            </Paragraph>
            <AnimatedButton
              variant="glow"
              size="large"
              icon={<DownloadOutlined />}
              loading={downloadLoading}
              onClick={onDownload}
              fullWidth
            >
              {downloadLoading ? 'מוריד...' : 'הורד עכשיו'}
            </AnimatedButton>
          </AnimatedCard>
        </Col>

        {/* Already Registered Card */}
        <Col xs={24} md={12}>
          <AnimatedCard
            variant="glass"
            delay={0.3}
            style={{ height: '100%', padding: '40px 30px', textAlign: 'center' }}
          >
            <motion.div
              animate={{ rotate: [0, 360] }}
              transition={{ duration: 8, repeat: Infinity, ease: 'linear' }}
            >
              <SettingOutlined style={{ 
                fontSize: 56, 
                color: '#faad14',
                filter: 'drop-shadow(0 0 20px rgba(250, 173, 20, 0.5))',
              }} />
            </motion.div>
            <Title level={3} style={{ color: 'white', marginTop: 20 }}>
              כבר רשום?
            </Title>
            <Paragraph style={{ color: 'rgba(255,255,255,0.7)', marginBottom: 25 }}>
              היכנס לפאנל הניהול לצפייה בנתונים וניהול המשתמשים
            </Paragraph>
            <AnimatedButton
              variant="warning"
              size="large"
              icon={<CrownOutlined />}
              onClick={onAdminLogin}
              fullWidth
            >
              כניסה לפאנל ניהול
            </AnimatedButton>
          </AnimatedCard>
        </Col>
      </Row>
    </section>
  );
});

ActionCardsSection.displayName = 'ActionCardsSection';

// ============================================
// Registration Modal Component
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
    height: 48,
    fontSize: 15,
    borderRadius: 10,
  };

  const labelStyle = { fontSize: 14, fontWeight: 600, color: '#333' };

  return (
    <Modal
      open={open}
      onCancel={onClose}
      footer={null}
      width={700}
      centered
      styles={{ 
        body: { padding: '30px 40px', direction: 'rtl' },
        header: { textAlign: 'center' },
      }}
      title={
        <div style={{ textAlign: 'center', paddingTop: 10 }}>
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: 'spring', stiffness: 200 }}
          >
            <TeamOutlined style={{ fontSize: '2.5rem', color: '#667eea', marginBottom: 10 }} />
          </motion.div>
          <Title level={3} style={{ margin: 0, color: '#333' }}>הרשמת ארגון חדש</Title>
          <Text type="secondary">מלא את כל הפרטים ליצירת ארגון וחשבון מנהל</Text>
        </div>
      }
    >
      <Form
        form={form}
        onFinish={onSubmit}
        layout="vertical"
        size="large"
        style={{ marginTop: 20 }}
      >
        {/* Organization Details Section */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.1 }}
          style={{ 
            background: 'linear-gradient(135deg, #f8f9ff 0%, #f0f4ff 100%)', 
            padding: 25, 
            borderRadius: 16,
            marginBottom: 25,
            border: '1px solid #e8ecff',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', marginBottom: 20 }}>
            <BankOutlined style={{ fontSize: '1.5rem', color: '#667eea', marginLeft: 10 }} />
            <Title level={5} style={{ margin: 0, color: '#333' }}>פרטי הארגון</Title>
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

          <Row gutter={16}>
            <Col span={12}>
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
            <Col span={12}>
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
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
          style={{ 
            background: 'linear-gradient(135deg, #fff8f0 0%, #fff4e8 100%)', 
            padding: 25, 
            borderRadius: 16,
            marginBottom: 25,
            border: '1px solid #ffe8d4',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', marginBottom: 20 }}>
            <CrownOutlined style={{ fontSize: '1.5rem', color: '#fa8c16', marginLeft: 10 }} />
            <Title level={5} style={{ margin: 0, color: '#333' }}>פרטי המנהל הראשי</Title>
          </div>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="adminFirstName"
                label={<span style={labelStyle}>שם פרטי</span>}
                rules={[{ required: true, message: 'נא להזין שם פרטי' }]}
              >
                <Input placeholder="שם פרטי" style={inputStyle} />
              </Form.Item>
            </Col>
            <Col span={12}>
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
          >
            <Input 
              prefix={<MailOutlined style={{ color: '#bfbfbf' }} />}
              placeholder="admin@example.com"
              style={inputStyle}
            />
          </Form.Item>
        </motion.div>

        <Divider style={{ margin: '25px 0' }} />

        <Form.Item style={{ marginBottom: 0, textAlign: 'center' }}>
          <Space size="middle">
            <AnimatedButton
              variant="ghost"
              onClick={onClose}
              style={{ 
                color: '#666', 
                borderColor: '#d9d9d9',
                background: 'white',
              }}
            >
              ביטול
            </AnimatedButton>
            <AnimatedButton
              variant="primary"
              loading={loading}
              onClick={() => form.submit()}
              icon={<TeamOutlined />}
            >
              {loading ? 'יוצר ארגון...' : 'צור ארגון וחשבון מנהל'}
            </AnimatedButton>
          </Space>
        </Form.Item>
      </Form>
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
    const fetchReleaseInfo = async () => {
      try {
        const release = await getLatestRelease();
        setReleaseInfo(release);
      } catch (error) {
        console.warn('Could not fetch release info:', error);
      }
    };
    fetchReleaseInfo();
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
        />

        {/* Features Section */}
        <FeaturesSection />

        {/* Action Cards Section */}
        <ActionCardsSection
          onRegisterClick={openRegistrationModal}
          onAdminLogin={handleAdminLogin}
          onDownload={handleDirectDownload}
          downloadLoading={downloadLoading}
          releaseInfo={releaseInfo}
        />

        {/* Footer */}
        <motion.footer
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          style={{
            textAlign: 'center',
            padding: '40px 20px 60px',
            color: 'rgba(255,255,255,0.5)',
          }}
        >
          <Text style={{ color: 'inherit' }}>
            © 2026 SIONYX. כל הזכויות שמורות.
          </Text>
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
