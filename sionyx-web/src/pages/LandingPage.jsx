/**
 * SIONYX Landing Page
 * Lightweight animations for smooth 60fps performance
 */

import { useState, useCallback, useEffect, memo } from 'react';
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

import { registerOrganization } from '../services/organizationService';
import { downloadFile, getLatestRelease, formatVersion } from '../services/downloadService';
import {
  AnimatedBackground,
  AnimatedButton,
  AnimatedCard,
  GlowingText,
  GradientText,
} from '../components/animated';

import './LandingPage.css';

const { Title, Paragraph, Text } = Typography;

// ============================================
// Hero Section Component
// ============================================
const HeroSection = memo(({ onRegisterClick, onAdminLogin }) => {
  return (
    <section className="hero">
      {/* Admin Button */}
      <div className="hero__admin-btn">
        <AnimatedButton
          variant="secondary"
          size="medium"
          icon={<CrownOutlined />}
          onClick={onAdminLogin}
        >
          כניסת מנהל
        </AnimatedButton>
      </div>

      {/* Main Title */}
      <div className="hero__title-wrapper">
        <h1 className="hero__title">SIONYX</h1>
      </div>

      {/* Subtitle */}
      <p className="hero__subtitle">
        <GradientText animate gradient="linear-gradient(90deg, #a5b4fc, #818cf8, #c4b5fd, #a5b4fc)">
          פתרון מתקדם לניהול זמן מחשבים ואישורי הדפסה
        </GradientText>
      </p>

      {/* CTA Button */}
      <div className="hero__cta">
        <AnimatedButton
          variant="primary"
          size="large"
          icon={<RocketOutlined />}
          onClick={onRegisterClick}
          style={{ padding: '0 50px' }}
        >
          התחל עכשיו
        </AnimatedButton>
      </div>

      {/* Scroll Indicator */}
      <div className="hero__scroll-indicator">
        <Text style={{ color: 'rgba(255,255,255,0.5)', fontSize: 14 }}>גלול למטה</Text>
        <div className="hero__scroll-mouse">
          <div className="hero__scroll-wheel" />
        </div>
      </div>
    </section>
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
    <section className="features">
      <div className="features__header">
        <Title level={2} style={{ color: 'white', fontSize: 'clamp(2rem, 5vw, 3rem)', margin: 0 }}>
          <GlowingText color="#667eea">
            למה SIONYX?
          </GlowingText>
        </Title>
      </div>

      <Row gutter={[30, 30]} justify="center" align="middle" className="features__grid">
        {features.map((feature, index) => (
          <Col xs={24} sm={12} md={8} key={index}>
            <AnimatedCard
              variant="glass"
              delay={index * 0.1}
              style={{ height: '100%', padding: '40px 30px', textAlign: 'center' }}
            >
              <div
                className="features__icon"
                style={{ color: feature.color }}
              >
                {feature.icon}
              </div>
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
    <section className="actions">
      <Row gutter={[30, 30]} justify="center" align="top" className="actions__grid">
        {/* Registration Card */}
        <Col xs={24} lg={20}>
          <AnimatedCard
            variant="glow"
            onClick={onRegisterClick}
            delay={0}
            style={{
              padding: '60px 40px',
              textAlign: 'center',
              cursor: 'pointer',
            }}
          >
            <div className="actions__icon actions__icon--animated">
              <UserAddOutlined style={{ fontSize: 64, color: 'white' }} />
            </div>
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
        <Col xs={24} sm={24} md={12} lg={10}>
          <AnimatedCard
            variant="glass"
            delay={0.1}
            style={{ height: '100%', padding: '40px 30px', textAlign: 'center' }}
          >
            <div className="actions__icon" style={{ color: '#52c41a' }}>
              <RocketOutlined style={{ fontSize: 56 }} />
            </div>
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
        <Col xs={24} sm={24} md={12} lg={10}>
          <AnimatedCard
            variant="glass"
            delay={0.15}
            style={{ height: '100%', padding: '40px 30px', textAlign: 'center' }}
          >
            <div className="actions__icon actions__icon--spin" style={{ color: '#faad14' }}>
              <SettingOutlined style={{ fontSize: 56 }} />
            </div>
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
          <TeamOutlined style={{ fontSize: '2.5rem', color: '#667eea', marginBottom: 10 }} />
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
        <div className="form-section form-section--blue">
          <div className="form-section__header">
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
        </div>

        {/* Admin User Section */}
        <div className="form-section form-section--orange">
          <div className="form-section__header">
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
        </div>

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
    <div className="landing">
      {/* Animated Background */}
      <AnimatedBackground />

      {/* Content */}
      <div className="landing__content">
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
        <footer className="landing__footer">
          <Text style={{ color: 'rgba(255,255,255,0.5)' }}>
            © 2026 SIONYX. כל הזכויות שמורות.
          </Text>
        </footer>
      </div>

      {/* Registration Modal */}
      {showRegistrationModal && (
        <RegistrationModal
          open={showRegistrationModal}
          onClose={closeRegistrationModal}
          onSubmit={handleRegistration}
          loading={loading}
          form={registrationForm}
        />
      )}
    </div>
  );
});

LandingPage.displayName = 'LandingPage';

export default LandingPage;
