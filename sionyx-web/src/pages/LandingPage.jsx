import { useState, useCallback, useEffect, memo } from 'react';
import {
  Card,
  Button,
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
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { registerOrganization } from '../services/organizationService';
import { downloadFile, getLatestRelease, formatVersion } from '../services/downloadService';

const { Title, Paragraph, Text } = Typography;

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
        // Navigate to admin login with the new org ID
        navigate(`/admin/login?orgId=${result.orgId}`);
      } else {
        message.error(result.error || 'שגיאה ביצירת הארגון');
      }
    } catch (error) {
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

  // Input style for consistency
  const inputStyle = {
    textAlign: 'right',
    height: '48px',
    fontSize: '15px',
    borderRadius: '10px',
  };

  const labelStyle = { fontSize: '14px', fontWeight: '600', color: '#333' };

  return (
    <div 
      style={{ 
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)',
        direction: 'rtl',
        textAlign: 'right',
        padding: '20px',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Decorative background elements */}
      <div style={{
        position: 'absolute',
        top: '-50%',
        right: '-20%',
        width: '80%',
        height: '150%',
        background: 'radial-gradient(ellipse, rgba(94, 129, 244, 0.15) 0%, transparent 70%)',
        pointerEvents: 'none',
      }} />
      <div style={{
        position: 'absolute',
        bottom: '-30%',
        left: '-10%',
        width: '60%',
        height: '100%',
        background: 'radial-gradient(ellipse, rgba(236, 72, 153, 0.1) 0%, transparent 60%)',
        pointerEvents: 'none',
      }} />

      {/* Admin Login Button - Top Left */}
      <Button
        type="primary"
        icon={<CrownOutlined />}
        onClick={handleAdminLogin}
        style={{
          position: 'absolute',
          top: '20px',
          left: '20px',
          height: '50px',
          padding: '0 25px',
          fontSize: '16px',
          fontWeight: 'bold',
          borderRadius: '25px',
          backgroundColor: 'rgba(255,255,255,0.1)',
          borderColor: 'rgba(255,255,255,0.3)',
          color: 'white',
          boxShadow: '0 4px 20px rgba(0,0,0,0.3)',
          backdropFilter: 'blur(10px)',
          zIndex: 10,
        }}
      >
        כניסת מנהל
      </Button>

      <div style={{ maxWidth: '1100px', margin: '0 auto', position: 'relative', zIndex: 1 }}>
        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: '50px', marginTop: '60px' }}>
          <Title 
            level={1} 
            style={{ 
              color: 'white', 
              fontSize: '5rem', 
              fontWeight: '800',
              marginBottom: '20px',
              textShadow: '0 4px 30px rgba(94, 129, 244, 0.5)',
              letterSpacing: '8px',
              fontFamily: "'Segoe UI', sans-serif",
            }}
          >
            SIONYX
          </Title>
          <Paragraph 
            style={{ 
              color: 'rgba(255,255,255,0.85)', 
              fontSize: '1.3rem', 
              margin: '0 auto 30px',
              maxWidth: '600px',
              fontWeight: '300',
              lineHeight: '1.8',
            }}
          >
            פתרון מתקדם לניהול זמן מחשבים ואישורי הדפסה
          </Paragraph>
        </div>

        {/* Main Welcome Card for Admin Registration */}
        <div style={{ textAlign: 'center', marginBottom: '50px' }}>
          <Card
            hoverable
            onClick={openRegistrationModal}
            style={{
              maxWidth: '550px',
              margin: '0 auto',
              borderRadius: '24px',
              background: 'linear-gradient(145deg, rgba(94, 129, 244, 0.95), rgba(118, 75, 162, 0.95))',
              border: 'none',
              boxShadow: '0 20px 60px rgba(94, 129, 244, 0.4)',
              cursor: 'pointer',
              transition: 'all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275)',
              overflow: 'hidden',
            }}
            styles={{ body: { padding: '50px 40px' } }}
          >
            <UserAddOutlined style={{ 
              fontSize: '4rem', 
              color: 'white', 
              marginBottom: '25px',
              filter: 'drop-shadow(0 4px 10px rgba(0,0,0,0.2))',
            }} />
            <Title level={2} style={{ 
              color: 'white', 
              marginBottom: '15px',
              fontSize: '2rem',
              fontWeight: '700',
            }}>
              שלום לך מנהל יקר
            </Title>
            <Paragraph style={{ 
              color: 'rgba(255,255,255,0.9)', 
              fontSize: '1.15rem',
              marginBottom: '30px',
              lineHeight: '1.7',
            }}>
              הירשם כאן ליצירת ארגון חדש וחשבון מנהל
            </Paragraph>
            <Button
              type="primary"
              size="large"
              icon={<TeamOutlined />}
              style={{
                height: '55px',
                padding: '0 40px',
                fontSize: '18px',
                fontWeight: 'bold',
                borderRadius: '28px',
                backgroundColor: 'white',
                borderColor: 'white',
                color: '#667eea',
                boxShadow: '0 8px 30px rgba(0,0,0,0.25)',
              }}
            >
              התחל הרשמה
            </Button>
          </Card>
        </div>

        <Row gutter={[30, 30]} justify="center">
          {/* Download Section */}
          <Col xs={24} md={12}>
            <Card
              style={{
                borderRadius: '20px',
                boxShadow: '0 15px 40px rgba(0,0,0,0.3)',
                border: '1px solid rgba(255,255,255,0.1)',
                background: 'rgba(255,255,255,0.05)',
                backdropFilter: 'blur(20px)',
                height: '100%',
              }}
              styles={{ body: { padding: '40px 30px', textAlign: 'center' } }}
            >
              <RocketOutlined style={{ fontSize: '3.5rem', marginBottom: '20px', color: '#52c41a' }} />
              <Title level={3} style={{ color: 'white', marginBottom: '15px' }}>
                הורדת התוכנה
              </Title>
              {releaseInfo?.version && releaseInfo.version !== 'Latest' && (
                <Tag 
                  color="green" 
                  style={{ 
                    marginBottom: '15px',
                    fontWeight: 'bold',
                    fontSize: '13px',
                    padding: '4px 12px',
                  }}
                >
                  {formatVersion(releaseInfo)}
                </Tag>
              )}
              <Paragraph style={{ 
                color: 'rgba(255,255,255,0.75)', 
                marginBottom: '25px', 
                fontSize: '1rem',
              }}>
                הורידו את התוכנה להתקנה על מחשבי הארגון
              </Paragraph>
              
              <Button
                type="primary"
                size="large"
                icon={<DownloadOutlined />}
                loading={downloadLoading}
                onClick={handleDirectDownload}
                style={{
                  height: '55px',
                  width: '100%',
                  fontSize: '17px',
                  fontWeight: 'bold',
                  borderRadius: '28px',
                  background: 'linear-gradient(135deg, #52c41a 0%, #73d13d 100%)',
                  border: 'none',
                  boxShadow: '0 8px 25px rgba(82, 196, 26, 0.4)',
                }}
              >
                {downloadLoading ? 'מוריד...' : 'הורד עכשיו'}
              </Button>
            </Card>
          </Col>

          {/* Already Registered Section */}
          <Col xs={24} md={12}>
            <Card
              style={{
                borderRadius: '20px',
                boxShadow: '0 15px 40px rgba(0,0,0,0.3)',
                border: '1px solid rgba(255,255,255,0.1)',
                background: 'rgba(255,255,255,0.05)',
                backdropFilter: 'blur(20px)',
                height: '100%',
              }}
              styles={{ body: { padding: '40px 30px', textAlign: 'center' } }}
            >
              <SettingOutlined style={{ fontSize: '3.5rem', marginBottom: '20px', color: '#faad14' }} />
              <Title level={3} style={{ color: 'white', marginBottom: '15px' }}>
                כבר רשום?
              </Title>
              <Paragraph style={{ 
                color: 'rgba(255,255,255,0.75)', 
                marginBottom: '25px', 
                fontSize: '1rem',
              }}>
                היכנס לפאנל הניהול לצפייה בנתונים וניהול המשתמשים
              </Paragraph>
              
              <Button
                size="large"
                icon={<CrownOutlined />}
                onClick={handleAdminLogin}
                style={{
                  height: '55px',
                  width: '100%',
                  fontSize: '17px',
                  fontWeight: 'bold',
                  borderRadius: '28px',
                  background: 'linear-gradient(135deg, #faad14 0%, #ffc53d 100%)',
                  border: 'none',
                  color: '#1a1a2e',
                  boxShadow: '0 8px 25px rgba(250, 173, 20, 0.4)',
                }}
              >
                כניסה לפאנל ניהול
              </Button>
            </Card>
          </Col>
        </Row>
      </div>

      {/* Registration Modal */}
      <Modal
        open={showRegistrationModal}
        onCancel={closeRegistrationModal}
        footer={null}
        width={700}
        centered
        styles={{ 
          body: { padding: '30px 40px', direction: 'rtl' },
          header: { textAlign: 'center' },
        }}
        title={
          <div style={{ textAlign: 'center', paddingTop: '10px' }}>
            <TeamOutlined style={{ fontSize: '2.5rem', color: '#667eea', marginBottom: '10px' }} />
            <Title level={3} style={{ margin: 0, color: '#333' }}>הרשמת ארגון חדש</Title>
            <Text type="secondary">מלא את כל הפרטים ליצירת ארגון וחשבון מנהל</Text>
          </div>
        }
      >
        <Form
          form={registrationForm}
          onFinish={handleRegistration}
          layout="vertical"
          size="large"
          style={{ marginTop: '20px' }}
        >
          {/* Organization Details Section */}
          <div style={{ 
            background: 'linear-gradient(135deg, #f8f9ff 0%, #f0f4ff 100%)', 
            padding: '25px', 
            borderRadius: '16px',
            marginBottom: '25px',
            border: '1px solid #e8ecff',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: '20px' }}>
              <BankOutlined style={{ fontSize: '1.5rem', color: '#667eea', marginLeft: '10px' }} />
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
                  rules={[
                    { required: true, message: 'נא להזין מזהה מוסד' },
                  ]}
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
                  rules={[
                    { required: true, message: 'נא להזין מפתח API' },
                  ]}
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
          <div style={{ 
            background: 'linear-gradient(135deg, #fff8f0 0%, #fff4e8 100%)', 
            padding: '25px', 
            borderRadius: '16px',
            marginBottom: '25px',
            border: '1px solid #ffe8d4',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: '20px' }}>
              <CrownOutlined style={{ fontSize: '1.5rem', color: '#fa8c16', marginLeft: '10px' }} />
              <Title level={5} style={{ margin: 0, color: '#333' }}>פרטי המנהל הראשי</Title>
            </div>

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name="adminFirstName"
                  label={<span style={labelStyle}>שם פרטי</span>}
                  rules={[{ required: true, message: 'נא להזין שם פרטי' }]}
                >
                  <Input 
                    placeholder="שם פרטי"
                    style={inputStyle}
                  />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="adminLastName"
                  label={<span style={labelStyle}>שם משפחה</span>}
                  rules={[{ required: true, message: 'נא להזין שם משפחה' }]}
                >
                  <Input 
                    placeholder="שם משפחה"
                    style={inputStyle}
                  />
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
              rules={[
                { type: 'email', message: 'כתובת אימייל לא תקינה' }
              ]}
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
              <Button
                size="large"
                onClick={closeRegistrationModal}
                style={{
                  height: '50px',
                  padding: '0 30px',
                  fontSize: '16px',
                  borderRadius: '25px',
                }}
              >
                ביטול
              </Button>
              <Button
                type="primary"
                htmlType="submit"
                loading={loading}
                size="large"
                icon={<TeamOutlined />}
                style={{
                  height: '50px',
                  padding: '0 40px',
                  fontSize: '16px',
                  fontWeight: 'bold',
                  borderRadius: '25px',
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  border: 'none',
                  boxShadow: '0 6px 20px rgba(102, 126, 234, 0.4)',
                }}
              >
                {loading ? 'יוצר ארגון...' : 'צור ארגון וחשבון מנהל'}
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
});

LandingPage.displayName = 'LandingPage';

export default LandingPage;
