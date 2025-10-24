import { useState, useEffect, useCallback, useMemo, memo } from 'react';
import { 
  Card, 
  Button, 
  Form, 
  Input, 
  Typography, 
  Row, 
  Col, 
  Space, 
  Divider,
  message,
  Spin,
  Tabs,
  Progress
} from 'antd';
import { 
  RocketOutlined, 
  DownloadOutlined, 
  SettingOutlined,
  TeamOutlined,
  SecurityScanOutlined,
  CloudOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  GlobalOutlined,
  UserAddOutlined,
  LoginOutlined,
  CrownOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { registerOrganization, validateOrganization } from '../services/organizationService';
import { getLatestRelease, downloadFile } from '../services/downloadService';

const { Title, Paragraph, Text } = Typography;

const LandingPage = () => {
  const [registrationForm] = Form.useForm();
  const [validationForm] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [showDownload, setShowDownload] = useState(false);
  const [downloadLoading, setDownloadLoading] = useState(false);
  const [isVisible, setIsVisible] = useState(false);
  const [activeTab, setActiveTab] = useState('register');
  const [validatedOrg, setValidatedOrg] = useState(null);
  const [progress, setProgress] = useState(0);
  const navigate = useNavigate();

  useEffect(() => {
    setIsVisible(true);
    // Simulate progress animation - optimized
    const timer = setInterval(() => {
      setProgress(prev => {
        if (prev >= 100) {
          clearInterval(timer);
          return 100;
        }
        return prev + 5; // Faster animation
      });
    }, 30); // Reduced interval
    return () => clearInterval(timer);
  }, []);

  const handleAdminLogin = useCallback(() => {
    navigate('/admin');
  }, [navigate]);

  const handleOrganizationRegister = useCallback(async (values) => {
    setLoading(true);
    try {
      const result = await registerOrganization(values);
      if (result.success) {
        message.success({
          content: 'הארגון נרשם בהצלחה! 🎉',
          style: { direction: 'rtl' }
        });
        registrationForm.resetFields();
        setShowDownload(true);
        setValidatedOrg({ 
          orgId: result.orgId, 
          organizationName: values.organizationName 
        });
      } else {
        message.error({
          content: result.error || 'שגיאה ברישום הארגון',
          style: { direction: 'rtl' }
        });
      }
    } catch (error) {
      message.error({
        content: 'שגיאה ברישום הארגון',
        style: { direction: 'rtl' }
      });
      console.error('Registration error:', error);
    } finally {
      setLoading(false);
    }
  }, [registrationForm]);

  const handleOrganizationValidate = useCallback(async (values) => {
    setLoading(true);
    try {
      const result = await validateOrganization(values.organizationName);
      if (result.success) {
        message.success({
          content: 'הארגון אומת בהצלחה! ✅',
          style: { direction: 'rtl' }
        });
        validationForm.resetFields();
        setShowDownload(true);
        setValidatedOrg({ 
          orgId: result.orgId, 
          organizationName: result.organizationName 
        });
      } else {
        message.error({
          content: result.error || 'שגיאה באימות הארגון',
          style: { direction: 'rtl' }
        });
      }
    } catch (error) {
      message.error({
        content: 'שגיאה באימות הארגון',
        style: { direction: 'rtl' }
      });
      console.error('Validation error:', error);
    } finally {
      setLoading(false);
    }
  }, [validationForm]);

  const handleDownload = useCallback(async () => {
    setDownloadLoading(true);
    try {
      const releaseInfo = await getLatestRelease();
      await downloadFile(releaseInfo.downloadUrl, releaseInfo.fileName);
      message.success({
        content: 'ההורדה החלה בהצלחה! 🚀',
        style: { direction: 'rtl' }
      });
    } catch (error) {
      message.error({
        content: 'שגיאה בהורדה',
        style: { direction: 'rtl' }
      });
      console.error('Download error:', error);
    } finally {
      setDownloadLoading(false);
    }
  }, []);

  const handleGoToDownloadPage = useCallback(() => {
    navigate('/download');
  }, [navigate]);

  const handleTabChange = useCallback((key) => {
    setActiveTab(key);
    setShowDownload(false);
    setValidatedOrg(null);
    registrationForm.resetFields();
    validationForm.resetFields();
  }, [registrationForm, validationForm]);

  const renderRegistrationForm = () => (
    <div style={{ direction: 'rtl' }}>
                <Form
        form={registrationForm}
                  layout="vertical"
                  onFinish={handleOrganizationRegister}
                  size="large"
                >
                  <Form.Item
                    name="organizationName"
          label={<Text style={{ fontWeight: 700, color: '#1a1a1a', fontSize: '16px' }}>שם הארגון</Text>}
                    rules={[
                      { required: true, message: 'אנא הזן את שם הארגון' },
                      { min: 2, message: 'שם הארגון חייב להכיל לפחות 2 תווים' }
                    ]}
                  >
                    <Input 
                      placeholder="הזן את שם הארגון" 
                      style={{
              height: '56px',
              borderRadius: '16px',
              border: '2px solid #e1e8ed',
                        fontSize: '16px',
              fontWeight: 500,
              transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
              boxShadow: '0 2px 8px rgba(0,0,0,0.04)',
              textAlign: 'right'
                      }}
                      onFocus={(e) => {
                        e.target.style.borderColor = '#667eea';
              e.target.style.boxShadow = '0 0 0 4px rgba(102, 126, 234, 0.1)';
              e.target.style.transform = 'translateY(-2px)';
                      }}
                      onBlur={(e) => {
              e.target.style.borderColor = '#e1e8ed';
              e.target.style.boxShadow = '0 2px 8px rgba(0,0,0,0.04)';
              e.target.style.transform = 'translateY(0)';
                      }}
                    />
                  </Form.Item>

                  <Form.Item
                    name="nedarimMosadId"
          label={<Text style={{ fontWeight: 700, color: '#1a1a1a', fontSize: '16px' }}>מזהה מוסד נדרים</Text>}
                    rules={[
            { required: true, message: 'אנא הזן את מזהה המוסד' }
                    ]}
                  >
                    <Input 
                      placeholder="הזן את מזהה המוסד" 
                      style={{
              height: '56px',
              borderRadius: '16px',
              border: '2px solid #e1e8ed',
                        fontSize: '16px',
              fontWeight: 500,
              transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
              boxShadow: '0 2px 8px rgba(0,0,0,0.04)',
              textAlign: 'right'
                      }}
                      onFocus={(e) => {
                        e.target.style.borderColor = '#667eea';
              e.target.style.boxShadow = '0 0 0 4px rgba(102, 126, 234, 0.1)';
              e.target.style.transform = 'translateY(-2px)';
                      }}
                      onBlur={(e) => {
              e.target.style.borderColor = '#e1e8ed';
              e.target.style.boxShadow = '0 2px 8px rgba(0,0,0,0.04)';
              e.target.style.transform = 'translateY(0)';
                      }}
                    />
                  </Form.Item>

                  <Form.Item
                    name="nedarimApiValid"
          label={<Text style={{ fontWeight: 700, color: '#1a1a1a', fontSize: '16px' }}>מפתח API נדרים</Text>}
                    rules={[
            { required: true, message: 'אנא הזן את מפתח ה-API' }
                    ]}
                  >
          <Input 
                      placeholder="הזן את מפתח ה-API" 
                      style={{
              height: '56px',
              borderRadius: '16px',
              border: '2px solid #e1e8ed',
                        fontSize: '16px',
              fontWeight: 500,
              transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
              boxShadow: '0 2px 8px rgba(0,0,0,0.04)',
              textAlign: 'right'
                      }}
                      onFocus={(e) => {
                        e.target.style.borderColor = '#667eea';
              e.target.style.boxShadow = '0 0 0 4px rgba(102, 126, 234, 0.1)';
              e.target.style.transform = 'translateY(-2px)';
                      }}
                      onBlur={(e) => {
              e.target.style.borderColor = '#e1e8ed';
              e.target.style.boxShadow = '0 2px 8px rgba(0,0,0,0.04)';
              e.target.style.transform = 'translateY(0)';
                      }}
                    />
                  </Form.Item>

                  <Form.Item style={{ marginBottom: 0, textAlign: 'center' }}>
                    <Button 
                      type="primary" 
                      htmlType="submit"
                      size="large"
                      loading={loading}
                      style={{ 
                        width: '100%',
              height: '64px',
              fontSize: '18px',
              fontWeight: 700,
              borderRadius: '20px',
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              border: 'none',
              boxShadow: '0 8px 32px rgba(102, 126, 234, 0.4)',
              transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
              textTransform: 'none'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = 'translateY(-4px)';
              e.currentTarget.style.boxShadow = '0 12px 40px rgba(102, 126, 234, 0.6)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = 'translateY(0)';
              e.currentTarget.style.boxShadow = '0 8px 32px rgba(102, 126, 234, 0.4)';
            }}
          >
            {loading ? <Spin size="small" /> : <><UserAddOutlined /> הרשם ארגון חדש</>}
          </Button>
        </Form.Item>
      </Form>
    </div>
  );

  const renderValidationForm = () => (
    <div style={{ direction: 'rtl' }}>
      <Form
        form={validationForm}
        layout="vertical"
        onFinish={handleOrganizationValidate}
        size="large"
      >
        <Form.Item
          name="organizationName"
          label={<Text style={{ fontWeight: 700, color: '#1a1a1a', fontSize: '16px' }}>שם הארגון הקיים</Text>}
          rules={[
            { required: true, message: 'אנא הזן את שם הארגון' },
            { min: 2, message: 'שם הארגון חייב להכיל לפחות 2 תווים' }
          ]}
        >
          <Input 
            placeholder="הזן את שם הארגון הקיים" 
            style={{
                        height: '56px',
              borderRadius: '16px',
              border: '2px solid #e1e8ed',
                        fontSize: '16px',
              fontWeight: 500,
              transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
              boxShadow: '0 2px 8px rgba(0,0,0,0.04)',
              textAlign: 'right'
            }}
            onFocus={(e) => {
              e.target.style.borderColor = '#667eea';
              e.target.style.boxShadow = '0 0 0 4px rgba(102, 126, 234, 0.1)';
              e.target.style.transform = 'translateY(-2px)';
            }}
            onBlur={(e) => {
              e.target.style.borderColor = '#e1e8ed';
              e.target.style.boxShadow = '0 2px 8px rgba(0,0,0,0.04)';
              e.target.style.transform = 'translateY(0)';
            }}
          />
        </Form.Item>

        <Form.Item style={{ marginBottom: 0, textAlign: 'center' }}>
          <Button 
            type="primary" 
            htmlType="submit"
            size="large"
            loading={loading}
            style={{ 
              width: '100%',
              height: '64px',
              fontSize: '18px',
              fontWeight: 700,
              borderRadius: '20px',
              background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
                        border: 'none',
              boxShadow: '0 8px 32px rgba(240, 147, 251, 0.4)',
              transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
              textTransform: 'none'
                      }}
                      onMouseEnter={(e) => {
              e.currentTarget.style.transform = 'translateY(-4px)';
              e.currentTarget.style.boxShadow = '0 12px 40px rgba(240, 147, 251, 0.6)';
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.transform = 'translateY(0)';
              e.currentTarget.style.boxShadow = '0 8px 32px rgba(240, 147, 251, 0.4)';
                      }}
                    >
            {loading ? <Spin size="small" /> : <><LoginOutlined /> אמת ארגון קיים</>}
                    </Button>
                  </Form.Item>
                </Form>
    </div>
  );

  const renderDownloadSection = () => (
    <div style={{
      textAlign: 'center',
      padding: '48px 32px',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      borderRadius: '32px',
      color: 'white',
      marginTop: '32px',
      position: 'relative',
      overflow: 'hidden',
      direction: 'rtl'
    }}>
      {/* Animated background elements */}
      <div style={{
        position: 'absolute',
        top: '-50%',
        left: '-50%',
        width: '200%',
        height: '200%',
        background: 'radial-gradient(circle, rgba(255,255,255,0.1) 1px, transparent 1px)',
        backgroundSize: '20px 20px',
        animation: 'float 20s infinite linear',
        zIndex: 1
      }} />
      
      <div style={{ position: 'relative', zIndex: 2 }}>
                    <div style={{ 
          display: 'inline-flex',
          alignItems: 'center',
          justifyContent: 'center',
          width: '80px',
          height: '80px',
          background: 'rgba(255, 255, 255, 0.2)',
          borderRadius: '50%',
                      marginBottom: '24px',
          backdropFilter: 'blur(20px)',
          border: '2px solid rgba(255, 255, 255, 0.3)',
          animation: 'pulse 2s infinite'
        }}>
          <CheckCircleOutlined style={{ fontSize: '40px', color: '#4ade80' }} />
                    </div>
        
        <Title level={2} style={{ 
          color: 'white', 
          marginBottom: '16px',
          fontSize: '2.5rem',
          fontWeight: 800,
          textShadow: '0 4px 20px rgba(0, 0, 0, 0.3)'
        }}>
          {validatedOrg ? `ברוכים הבאים, ${validatedOrg.organizationName}!` : 'הארגון נרשם בהצלחה!'}
        </Title>
        
        <Paragraph style={{ 
          color: 'rgba(255, 255, 255, 0.9)', 
          marginBottom: '32px',
          fontSize: '1.2rem',
          fontWeight: 500
        }}>
          כעת תוכלו להוריד את התוכנה ולהתחיל להשתמש בשירות המתקדם שלנו
        </Paragraph>
                    
                    <Button 
                      type="primary" 
                      size="large"
                      loading={downloadLoading}
                      onClick={handleDownload}
                      style={{ 
            height: '64px',
            fontSize: '18px',
            fontWeight: 700,
            borderRadius: '20px',
            background: 'rgba(255, 255, 255, 0.2)',
            border: '2px solid rgba(255, 255, 255, 0.3)',
            color: 'white',
            backdropFilter: 'blur(20px)',
            transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
            padding: '0 32px'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = 'rgba(255, 255, 255, 0.3)';
            e.currentTarget.style.transform = 'translateY(-4px)';
            e.currentTarget.style.boxShadow = '0 12px 40px rgba(255, 255, 255, 0.2)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = 'rgba(255, 255, 255, 0.2)';
            e.currentTarget.style.transform = 'translateY(0)';
            e.currentTarget.style.boxShadow = 'none';
          }}
        >
          {downloadLoading ? <Spin size="small" /> : <><DownloadOutlined /> הורד תוכנה עכשיו</>}
        </Button>
      </div>
    </div>
  );

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%)',
      padding: '0',
      position: 'relative',
      overflow: 'hidden',
      direction: 'rtl'
    }}>
      {/* Optimized background elements */}
      <div style={{
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        background: `
          radial-gradient(circle at 20% 80%, rgba(120, 119, 198, 0.2) 0%, transparent 50%),
          radial-gradient(circle at 80% 20%, rgba(255, 119, 198, 0.2) 0%, transparent 50%)
        `,
        zIndex: 1,
        willChange: 'transform',
        transform: 'translateZ(0)'
      }} />

      {/* Content */}
      <div style={{ position: 'relative', zIndex: 3, padding: '40px 20px' }}>
        <Row justify="center" align="middle" style={{ minHeight: '100vh' }}>
          <Col xs={24} lg={20} xl={16}>
            <div style={{
              opacity: isVisible ? 1 : 0,
              transform: isVisible ? 'translate3d(0, 0, 0)' : 'translate3d(0, 20px, 0)',
              transition: 'opacity 0.6s ease-out, transform 0.6s ease-out',
              willChange: 'opacity, transform'
            }}>
              {/* Header */}
              <div style={{ textAlign: 'center', marginBottom: '80px' }}>
                <div style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  width: '120px',
                  height: '120px',
                  background: 'rgba(255, 255, 255, 0.15)',
                  borderRadius: '50%',
                  marginBottom: '32px',
                  backdropFilter: 'blur(30px)',
                  border: '3px solid rgba(255, 255, 255, 0.2)',
                  animation: 'pulse 3s infinite',
                  boxShadow: '0 20px 60px rgba(0, 0, 0, 0.2)'
                }}>
                  <RocketOutlined style={{ fontSize: '48px', color: 'white' }} />
                </div>
                
                <Title level={1} style={{ 
                  color: 'white', 
                  marginBottom: '24px',
                  fontSize: '4rem',
                  fontWeight: 900,
                  textShadow: '0 8px 32px rgba(0, 0, 0, 0.3)',
                  letterSpacing: '-0.02em'
                }}>
                  SIONYX
                </Title>
                
                <Paragraph style={{ 
                  color: 'rgba(255, 255, 255, 0.95)', 
                  fontSize: '1.4rem',
                  marginBottom: '48px',
                  maxWidth: '700px',
                  margin: '0 auto 48px',
                  fontWeight: 500,
                  lineHeight: 1.6
                }}>
                  פתרון מתקדם לניהול זמן מחשבים ואישורי הדפסה
                  <br />
                  בחרו את האפשרות המתאימה לכם
                </Paragraph>

                {/* Progress indicator */}
                <div style={{ marginBottom: '32px' }}>
                  <Progress 
                    percent={progress} 
                    showInfo={false}
                    strokeColor={{
                      '0%': '#4ade80',
                      '100%': '#22c55e',
                    }}
                    style={{ maxWidth: '300px', margin: '0 auto' }}
                  />
                </div>

                {/* Action Buttons */}
                <Space size="large" style={{ marginBottom: '40px' }}>
                  <Button 
                    type="text" 
                    onClick={handleAdminLogin}
                    style={{ 
                      color: 'rgba(255, 255, 255, 0.9)',
                      fontSize: '16px',
                      fontWeight: 600,
                      padding: '12px 24px',
                      borderRadius: '12px',
                      background: 'rgba(255, 255, 255, 0.1)',
                      backdropFilter: 'blur(10px)',
                      border: '1px solid rgba(255, 255, 255, 0.2)',
                      transition: 'all 0.3s ease'
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.background = 'rgba(255, 255, 255, 0.2)';
                      e.currentTarget.style.transform = 'translateY(-2px)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.background = 'rgba(255, 255, 255, 0.1)';
                      e.currentTarget.style.transform = 'translateY(0)';
                    }}
                  >
                    <SettingOutlined /> כניסה למנהל
                  </Button>
                  
                  <Button 
                    type="text" 
                    onClick={handleGoToDownloadPage}
                    style={{ 
                      color: 'rgba(255, 255, 255, 0.9)',
                      fontSize: '16px',
                      fontWeight: 600,
                      padding: '12px 24px',
                      borderRadius: '12px',
                      background: 'rgba(255, 255, 255, 0.1)',
                      backdropFilter: 'blur(10px)',
                      border: '1px solid rgba(255, 255, 255, 0.2)',
                      transition: 'all 0.3s ease'
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.background = 'rgba(255, 255, 255, 0.2)';
                      e.currentTarget.style.transform = 'translateY(-2px)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.background = 'rgba(255, 255, 255, 0.1)';
                      e.currentTarget.style.transform = 'translateY(0)';
                    }}
                  >
                    <DownloadOutlined /> הורדה ישירה
                  </Button>
                </Space>
              </div>

              {/* Main Content */}
              <Row gutter={[48, 48]} align="stretch">
                {/* Organization Forms */}
                <Col xs={24} lg={12}>
                  <div style={{
                    opacity: isVisible ? 1 : 0,
                    transform: isVisible ? 'translate3d(0, 0, 0)' : 'translate3d(-30px, 0, 0)',
                    transition: 'opacity 0.5s ease-out 0.2s, transform 0.5s ease-out 0.2s',
                    willChange: 'opacity, transform'
                  }}>
                    <Card 
                      style={{ 
                        height: '100%',
                        borderRadius: '32px',
                        boxShadow: '0 32px 80px rgba(0,0,0,0.12)',
                        background: 'rgba(255, 255, 255, 0.98)',
                        backdropFilter: 'blur(30px)',
                        border: '1px solid rgba(255, 255, 255, 0.2)',
                        overflow: 'hidden',
                        position: 'relative'
                      }}
                      styles={{ body: { padding: '56px' } }}
                    >
                      {/* Decorative gradient overlay */}
                      <div style={{
                        position: 'absolute',
                        top: 0,
                        left: 0,
                        right: 0,
                        height: '6px',
                        background: 'linear-gradient(90deg, #667eea, #764ba2, #f093fb)',
                        borderRadius: '32px 32px 0 0'
                      }} />

                      <div style={{ textAlign: 'center', marginBottom: '40px' }}>
                        <div style={{
                          display: 'inline-flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                          width: '80px',
                          height: '80px',
                          background: 'linear-gradient(135deg, #667eea, #764ba2)',
                          borderRadius: '50%',
                          marginBottom: '24px',
                          boxShadow: '0 12px 32px rgba(102, 126, 234, 0.3)'
                        }}>
                          <TeamOutlined style={{ fontSize: '32px', color: 'white' }} />
                        </div>
                        
                        <Title level={2} style={{ color: '#1a1a1a', marginBottom: '12px', fontSize: '2rem', fontWeight: 800 }}>
                          ניהול ארגון
                        </Title>
                        
                        <Paragraph style={{ color: '#6b7280', marginBottom: '0', fontSize: '1.1rem', fontWeight: 500 }}>
                          הרשמה חדשה או אימות ארגון קיים
                        </Paragraph>
                      </div>

                      <Tabs
                        activeKey={activeTab}
                        onChange={handleTabChange}
                        items={[
                          {
                            key: 'register',
                            label: (
                              <span style={{ fontSize: '16px', fontWeight: 600 }}>
                                <UserAddOutlined style={{ marginLeft: '8px' }} />
                                הרשמה חדשה
                              </span>
                            ),
                            children: renderRegistrationForm()
                          },
                          {
                            key: 'validate',
                            label: (
                              <span style={{ fontSize: '16px', fontWeight: 600 }}>
                                <LoginOutlined style={{ marginLeft: '8px' }} />
                                ארגון קיים
                              </span>
                            ),
                            children: renderValidationForm()
                          }
                        ]}
                        style={{ marginTop: '24px' }}
                        tabBarStyle={{ 
                          marginBottom: '32px',
                          borderBottom: '2px solid #f1f5f9'
                        }}
                      />

                      <Divider style={{ margin: '40px 0', borderColor: '#e2e8f0' }} />

                      {/* Features List */}
                      <div style={{ textAlign: 'center' }}>
                        <Space direction="vertical" size="large" style={{ width: '100%' }}>
                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '12px' }}>
                            <CheckCircleOutlined style={{ color: '#22c55e', fontSize: '20px' }} />
                            <Text style={{ fontSize: '16px', color: '#374151', fontWeight: 600 }}>ניהול זמן מחשבים מתקדם</Text>
                          </div>
                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '12px' }}>
                            <CheckCircleOutlined style={{ color: '#22c55e', fontSize: '20px' }} />
                            <Text style={{ fontSize: '16px', color: '#374151', fontWeight: 600 }}>מערכת אישורי הדפסה</Text>
                          </div>
                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '12px' }}>
                            <CheckCircleOutlined style={{ color: '#22c55e', fontSize: '20px' }} />
                            <Text style={{ fontSize: '16px', color: '#374151', fontWeight: 600 }}>דשבורד ניהול מתקדם</Text>
                          </div>
                        </Space>
                    </div>
                    </Card>
                  </div>
                </Col>

                {/* Features & Download */}
                <Col xs={24} lg={12}>
                  <div style={{
                    opacity: isVisible ? 1 : 0,
                    transform: isVisible ? 'translate3d(0, 0, 0)' : 'translate3d(30px, 0, 0)',
                    transition: 'opacity 0.5s ease-out 0.3s, transform 0.5s ease-out 0.3s',
                    willChange: 'opacity, transform'
                  }}>
                    {showDownload ? (
                      renderDownloadSection()
                    ) : (
                      <Card 
                        style={{ 
                          height: '100%',
                          borderRadius: '32px',
                          boxShadow: '0 32px 80px rgba(0,0,0,0.12)',
                          background: 'rgba(255, 255, 255, 0.98)',
                          backdropFilter: 'blur(30px)',
                          border: '1px solid rgba(255, 255, 255, 0.2)',
                          overflow: 'hidden',
                          position: 'relative'
                        }}
                        styles={{ body: { padding: '56px' } }}
                      >
                        {/* Decorative gradient overlay */}
                        <div style={{
                          position: 'absolute',
                          top: 0,
                          left: 0,
                          right: 0,
                          height: '6px',
                          background: 'linear-gradient(90deg, #f093fb, #f5576c)',
                          borderRadius: '32px 32px 0 0'
                        }} />

                        <div style={{ textAlign: 'center', marginBottom: '40px' }}>
                          <div style={{
                            display: 'inline-flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                            width: '80px',
                            height: '80px',
                            background: 'linear-gradient(135deg, #f093fb, #f5576c)',
                            borderRadius: '50%',
                            marginBottom: '24px',
                            boxShadow: '0 12px 32px rgba(240, 147, 251, 0.3)'
                          }}>
                            <DownloadOutlined style={{ fontSize: '32px', color: 'white' }} />
                          </div>
                          
                          <Title level={2} style={{ color: '#1a1a1a', marginBottom: '12px', fontSize: '2rem', fontWeight: 800 }}>
                            הורדת התוכנה
                          </Title>
                          
                          <Paragraph style={{ color: '#6b7280', marginBottom: '0', fontSize: '1.1rem', fontWeight: 500 }}>
                            לאחר הרישום או האימות, תוכלו להוריד את התוכנה
                          </Paragraph>
                        </div>

                        {/* Features Grid */}
                        <Row gutter={[20, 20]} style={{ marginBottom: '40px' }}>
                          <Col span={12}>
                            <div style={{ 
                              textAlign: 'center', 
                              padding: '24px 16px',
                              background: 'linear-gradient(135deg, #f8fafc, #e2e8f0)',
                              borderRadius: '20px',
                              border: '1px solid #e2e8f0',
                              transition: 'all 0.3s ease'
                            }}>
                              <SecurityScanOutlined style={{ fontSize: '28px', color: '#667eea', marginBottom: '12px' }} />
                              <Text style={{ display: 'block', fontWeight: 700, color: '#1a1a1a', fontSize: '16px', marginBottom: '4px' }}>אבטחה מתקדמת</Text>
                              <Text style={{ fontSize: '14px', color: '#6b7280', fontWeight: 500 }}>הצפנה מלאה</Text>
                            </div>
                          </Col>
                          <Col span={12}>
                            <div style={{ 
                              textAlign: 'center', 
                              padding: '24px 16px',
                              background: 'linear-gradient(135deg, #f8fafc, #e2e8f0)',
                              borderRadius: '20px',
                              border: '1px solid #e2e8f0',
                              transition: 'all 0.3s ease'
                            }}>
                              <CloudOutlined style={{ fontSize: '28px', color: '#667eea', marginBottom: '12px' }} />
                              <Text style={{ display: 'block', fontWeight: 700, color: '#1a1a1a', fontSize: '16px', marginBottom: '4px' }}>ענן מאובטח</Text>
                              <Text style={{ fontSize: '14px', color: '#6b7280', fontWeight: 500 }}>סנכרון אוטומטי</Text>
                            </div>
                          </Col>
                          <Col span={12}>
                            <div style={{ 
                              textAlign: 'center', 
                              padding: '24px 16px',
                              background: 'linear-gradient(135deg, #f8fafc, #e2e8f0)',
                              borderRadius: '20px',
                              border: '1px solid #e2e8f0',
                              transition: 'all 0.3s ease'
                            }}>
                              <ClockCircleOutlined style={{ fontSize: '28px', color: '#667eea', marginBottom: '12px' }} />
                              <Text style={{ display: 'block', fontWeight: 700, color: '#1a1a1a', fontSize: '16px', marginBottom: '4px' }}>ניהול זמן</Text>
                              <Text style={{ fontSize: '14px', color: '#6b7280', fontWeight: 500 }}>מעקב מדויק</Text>
                            </div>
                          </Col>
                          <Col span={12}>
                            <div style={{ 
                              textAlign: 'center', 
                              padding: '24px 16px',
                              background: 'linear-gradient(135deg, #f8fafc, #e2e8f0)',
                              borderRadius: '20px',
                              border: '1px solid #e2e8f0',
                              transition: 'all 0.3s ease'
                            }}>
                              <GlobalOutlined style={{ fontSize: '28px', color: '#667eea', marginBottom: '12px' }} />
                              <Text style={{ display: 'block', fontWeight: 700, color: '#1a1a1a', fontSize: '16px', marginBottom: '4px' }}>גישה מרחוק</Text>
                              <Text style={{ fontSize: '14px', color: '#6b7280', fontWeight: 500 }}>מכל מקום</Text>
                            </div>
                          </Col>
                        </Row>

                        <div style={{
                          background: 'linear-gradient(135deg, #667eea, #764ba2)',
                          borderRadius: '24px',
                          padding: '32px',
                          textAlign: 'center',
                          border: 'none',
                          position: 'relative',
                          overflow: 'hidden'
                        }}>
                          <div style={{
                            position: 'absolute',
                            top: 0,
                            left: 0,
                            right: 0,
                            bottom: 0,
                            background: 'radial-gradient(circle, rgba(255,255,255,0.1) 1px, transparent 1px)',
                            backgroundSize: '20px 20px',
                            animation: 'float 15s infinite linear'
                          }} />
                          <div style={{ position: 'relative', zIndex: 2 }}>
                            <CrownOutlined style={{ fontSize: '32px', color: 'white', marginBottom: '16px' }} />
                            <Text style={{ color: 'white', fontWeight: 700, fontSize: '18px', display: 'block' }}>
                              בחרו את האפשרות המתאימה בצד ימין
                            </Text>
                            <Text style={{ color: 'rgba(255, 255, 255, 0.8)', fontSize: '14px', marginTop: '8px', display: 'block' }}>
                              התחילו את המסע שלכם עם SIONYX
                    </Text>
                          </div>
                        </div>
                      </Card>
                    )}
                  </div>
                </Col>
              </Row>
            </div>
          </Col>
        </Row>
      </div>

    </div>
  );
};

export default memo(LandingPage);