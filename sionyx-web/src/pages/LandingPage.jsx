import { useState, useEffect } from 'react';
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
  Badge,
  Tabs
} from 'antd';
import { 
  RocketOutlined, 
  DownloadOutlined, 
  SettingOutlined,
  TeamOutlined,
  SecurityScanOutlined,
  CloudOutlined,
  CheckCircleOutlined,
  StarOutlined,
  ArrowRightOutlined,
  SafetyOutlined,
  ClockCircleOutlined,
  GlobalOutlined,
  UserAddOutlined,
  LoginOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { registerOrganization, validateOrganization } from '../services/organizationService';
import { downloadSoftware } from '../services/downloadService';

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
  const navigate = useNavigate();

  useEffect(() => {
    setIsVisible(true);
  }, []);

  const handleAdminLogin = () => {
    navigate('/admin');
  };

  const handleOrganizationRegister = async (values) => {
    setLoading(true);
    try {
      const result = await registerOrganization(values);
      if (result.success) {
        message.success('הארגון נרשם בהצלחה!');
        registrationForm.resetFields();
        setShowDownload(true);
        setValidatedOrg({ 
          orgId: result.orgId, 
          organizationName: values.organizationName 
        });
      } else {
        message.error(result.error || 'שגיאה ברישום הארגון');
      }
    } catch (error) {
      message.error('שגיאה ברישום הארגון');
      console.error('Registration error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleOrganizationValidate = async (values) => {
    setLoading(true);
    try {
      const result = await validateOrganization(values.organizationName);
      if (result.success) {
        message.success('הארגון אומת בהצלחה!');
        validationForm.resetFields();
        setShowDownload(true);
        setValidatedOrg({ 
          orgId: result.orgId, 
          organizationName: result.organizationName 
        });
      } else {
        message.error(result.error || 'שגיאה באימות הארגון');
      }
    } catch (error) {
      message.error('שגיאה באימות הארגון');
      console.error('Validation error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async () => {
    setDownloadLoading(true);
    try {
      await downloadSoftware();
      message.success('ההורדה החלה בהצלחה!');
    } catch (error) {
      message.error('שגיאה בהורדה');
      console.error('Download error:', error);
    } finally {
      setDownloadLoading(false);
    }
  };

  const handleTabChange = (key) => {
    setActiveTab(key);
    setShowDownload(false);
    setValidatedOrg(null);
    registrationForm.resetFields();
    validationForm.resetFields();
  };

  const renderRegistrationForm = () => (
    <Form
      form={registrationForm}
      layout="vertical"
      onFinish={handleOrganizationRegister}
      size="large"
    >
      <Form.Item
        name="organizationName"
        label={<Text style={{ fontWeight: 600, color: '#2c3e50' }}>שם הארגון</Text>}
        rules={[
          { required: true, message: 'אנא הזן את שם הארגון' },
          { min: 2, message: 'שם הארגון חייב להכיל לפחות 2 תווים' }
        ]}
      >
        <Input 
          placeholder="הזן את שם הארגון" 
          style={{
            height: '48px',
            borderRadius: '12px',
            border: '2px solid #e8e8e8',
            fontSize: '16px',
            transition: 'all 0.3s ease'
          }}
          onFocus={(e) => {
            e.target.style.borderColor = '#667eea';
            e.target.style.boxShadow = '0 0 0 3px rgba(102, 126, 234, 0.1)';
          }}
          onBlur={(e) => {
            e.target.style.borderColor = '#e8e8e8';
            e.target.style.boxShadow = 'none';
          }}
        />
      </Form.Item>

      <Form.Item
        name="nedarimMosadId"
        label={<Text style={{ fontWeight: 600, color: '#2c3e50' }}>מזהה מוסד נדרים</Text>}
        rules={[
          { required: true, message: 'אנא הזן את מזהה המוסד' }
        ]}
      >
        <Input 
          placeholder="הזן את מזהה המוסד" 
          style={{
            height: '48px',
            borderRadius: '12px',
            border: '2px solid #e8e8e8',
            fontSize: '16px',
            transition: 'all 0.3s ease'
          }}
          onFocus={(e) => {
            e.target.style.borderColor = '#667eea';
            e.target.style.boxShadow = '0 0 0 3px rgba(102, 126, 234, 0.1)';
          }}
          onBlur={(e) => {
            e.target.style.borderColor = '#e8e8e8';
            e.target.style.boxShadow = 'none';
          }}
        />
      </Form.Item>

      <Form.Item
        name="nedarimApiValid"
        label={<Text style={{ fontWeight: 600, color: '#2c3e50' }}>מפתח API נדרים</Text>}
        rules={[
          { required: true, message: 'אנא הזן את מפתח ה-API' }
        ]}
      >
        <Input 
          placeholder="הזן את מפתח ה-API" 
          style={{
            height: '48px',
            borderRadius: '12px',
            border: '2px solid #e8e8e8',
            fontSize: '16px',
            transition: 'all 0.3s ease'
          }}
          onFocus={(e) => {
            e.target.style.borderColor = '#667eea';
            e.target.style.boxShadow = '0 0 0 3px rgba(102, 126, 234, 0.1)';
          }}
          onBlur={(e) => {
            e.target.style.borderColor = '#e8e8e8';
            e.target.style.boxShadow = 'none';
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
            height: '56px',
            fontSize: '16px',
            fontWeight: 600,
            borderRadius: '16px',
            background: 'linear-gradient(135deg, #f093fb, #f5576c)',
            border: 'none',
            boxShadow: '0 8px 24px rgba(240, 147, 251, 0.4)',
            transition: 'all 0.3s ease'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.transform = 'translateY(-2px)';
            e.currentTarget.style.boxShadow = '0 12px 32px rgba(240, 147, 251, 0.5)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = 'translateY(0)';
            e.currentTarget.style.boxShadow = '0 8px 24px rgba(240, 147, 251, 0.4)';
          }}
        >
          {loading ? <Spin size="small" /> : 'הרשם ארגון חדש'}
        </Button>
      </Form.Item>
    </Form>
  );

  const renderValidationForm = () => (
    <Form
      form={validationForm}
      layout="vertical"
      onFinish={handleOrganizationValidate}
      size="large"
    >
      <Form.Item
        name="organizationName"
        label={<Text style={{ fontWeight: 600, color: '#2c3e50' }}>שם הארגון הקיים</Text>}
        rules={[
          { required: true, message: 'אנא הזן את שם הארגון' },
          { min: 2, message: 'שם הארגון חייב להכיל לפחות 2 תווים' }
        ]}
      >
        <Input 
          placeholder="הזן את שם הארגון הקיים" 
          style={{
            height: '48px',
            borderRadius: '12px',
            border: '2px solid #e8e8e8',
            fontSize: '16px',
            transition: 'all 0.3s ease'
          }}
          onFocus={(e) => {
            e.target.style.borderColor = '#667eea';
            e.target.style.boxShadow = '0 0 0 3px rgba(102, 126, 234, 0.1)';
          }}
          onBlur={(e) => {
            e.target.style.borderColor = '#e8e8e8';
            e.target.style.boxShadow = 'none';
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
            height: '56px',
            fontSize: '16px',
            fontWeight: 600,
            borderRadius: '16px',
            background: 'linear-gradient(135deg, #667eea, #764ba2)',
            border: 'none',
            boxShadow: '0 8px 24px rgba(102, 126, 234, 0.4)',
            transition: 'all 0.3s ease'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.transform = 'translateY(-2px)';
            e.currentTarget.style.boxShadow = '0 12px 32px rgba(102, 126, 234, 0.5)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = 'translateY(0)';
            e.currentTarget.style.boxShadow = '0 8px 24px rgba(102, 126, 234, 0.4)';
          }}
        >
          {loading ? <Spin size="small" /> : 'אמת ארגון קיים'}
        </Button>
      </Form.Item>
    </Form>
  );

  const renderDownloadSection = () => (
    <div style={{
      textAlign: 'center',
      padding: '32px',
      background: 'linear-gradient(135deg, #667eea, #764ba2)',
      borderRadius: '20px',
      color: 'white',
      marginTop: '24px'
    }}>
      <CheckCircleOutlined style={{ fontSize: '48px', marginBottom: '16px', color: '#4ade80' }} />
      <Title level={3} style={{ color: 'white', marginBottom: '8px' }}>
        {validatedOrg ? `ברוכים הבאים, ${validatedOrg.organizationName}!` : 'הארגון נרשם בהצלחה!'}
      </Title>
      <Paragraph style={{ color: 'rgba(255, 255, 255, 0.9)', marginBottom: '24px' }}>
        כעת תוכלו להוריד את התוכנה ולהתחיל להשתמש בשירות
      </Paragraph>
      <Button 
        type="primary" 
        size="large"
        loading={downloadLoading}
        onClick={handleDownload}
        style={{
          height: '56px',
          fontSize: '16px',
          fontWeight: 600,
          borderRadius: '16px',
          background: 'rgba(255, 255, 255, 0.2)',
          border: '2px solid rgba(255, 255, 255, 0.3)',
          color: 'white',
          backdropFilter: 'blur(10px)',
          transition: 'all 0.3s ease'
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.background = 'rgba(255, 255, 255, 0.3)';
          e.currentTarget.style.transform = 'translateY(-2px)';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.background = 'rgba(255, 255, 255, 0.2)';
          e.currentTarget.style.transform = 'translateY(0)';
        }}
      >
        {downloadLoading ? <Spin size="small" /> : <><DownloadOutlined /> הורד תוכנה</>}
      </Button>
    </div>
  );

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      padding: '0',
      position: 'relative',
      overflow: 'hidden'
    }}>
      {/* Background Pattern */}
      <div style={{
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        background: `
          radial-gradient(circle at 20% 80%, rgba(120, 119, 198, 0.3) 0%, transparent 50%),
          radial-gradient(circle at 80% 20%, rgba(255, 119, 198, 0.3) 0%, transparent 50%),
          radial-gradient(circle at 40% 40%, rgba(120, 219, 255, 0.2) 0%, transparent 50%)
        `,
        zIndex: 1
      }} />

      {/* Content */}
      <div style={{ position: 'relative', zIndex: 2, padding: '40px 20px' }}>
        <Row justify="center" align="middle" style={{ minHeight: '100vh' }}>
          <Col xs={24} lg={20} xl={16}>
            <div style={{
              opacity: isVisible ? 1 : 0,
              transform: isVisible ? 'translateY(0)' : 'translateY(30px)',
              transition: 'all 0.8s cubic-bezier(0.4, 0, 0.2, 1)'
            }}>
              {/* Header */}
              <div style={{ textAlign: 'center', marginBottom: '60px' }}>
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
                  border: '2px solid rgba(255, 255, 255, 0.3)'
                }}>
                  <RocketOutlined style={{ fontSize: '32px', color: 'white' }} />
                </div>
                
                <Title level={1} style={{ 
                  color: 'white', 
                  marginBottom: '16px',
                  fontSize: '3rem',
                  fontWeight: 700,
                  textShadow: '0 4px 20px rgba(0, 0, 0, 0.3)'
                }}>
                  SIONYX
                </Title>
                
                <Paragraph style={{ 
                  color: 'rgba(255, 255, 255, 0.9)', 
                  fontSize: '1.2rem',
                  marginBottom: '40px',
                  maxWidth: '600px',
                  margin: '0 auto 40px'
                }}>
                  פתרון מתקדם לניהול זמן מחשבים ואישורי הדפסה
                  <br />
                  בחרו את האפשרות המתאימה לכם
                </Paragraph>

                {/* Admin Login Button */}
                <Button 
                  type="text" 
                  onClick={handleAdminLogin}
                  style={{ 
                    color: 'rgba(255, 255, 255, 0.8)',
                    fontSize: '16px',
                    marginBottom: '40px'
                  }}
                >
                  <SettingOutlined /> כניסה למנהל
                </Button>
              </div>

              {/* Main Content */}
              <Row gutter={[32, 32]} align="stretch">
                {/* Organization Forms */}
                <Col xs={24} lg={12}>
                  <div style={{
                    opacity: isVisible ? 1 : 0,
                    transform: isVisible ? 'translateX(0)' : 'translateX(-50px)',
                    transition: 'all 0.8s cubic-bezier(0.4, 0, 0.2, 1) 0.2s'
                  }}>
                    <Card 
                      style={{ 
                        height: '100%',
                        borderRadius: '24px',
                        boxShadow: '0 20px 60px rgba(0,0,0,0.15)',
                        background: 'rgba(255, 255, 255, 0.95)',
                        backdropFilter: 'blur(20px)',
                        border: '1px solid rgba(255, 255, 255, 0.3)',
                        overflow: 'hidden',
                        position: 'relative'
                      }}
                      styles={{ body: { padding: '48px' } }}
                    >
                      {/* Decorative gradient overlay */}
                      <div style={{
                        position: 'absolute',
                        top: 0,
                        left: 0,
                        right: 0,
                        height: '4px',
                        background: 'linear-gradient(90deg, #667eea, #764ba2, #f093fb)'
                      }} />

                      <div style={{ textAlign: 'center', marginBottom: '32px' }}>
                        <div style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          width: '60px',
                          height: '60px',
                          background: 'linear-gradient(135deg, #667eea, #764ba2)',
                          borderRadius: '50%',
                          marginBottom: '16px'
                        }}>
                          <TeamOutlined style={{ fontSize: '24px', color: 'white' }} />
                        </div>
                        
                        <Title level={3} style={{ color: '#2c3e50', marginBottom: '8px' }}>
                          ניהול ארגון
                        </Title>
                        
                        <Paragraph style={{ color: '#7f8c8d', marginBottom: '0' }}>
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
                              <span>
                                <UserAddOutlined />
                                הרשמה חדשה
                              </span>
                            ),
                            children: renderRegistrationForm()
                          },
                          {
                            key: 'validate',
                            label: (
                              <span>
                                <LoginOutlined />
                                ארגון קיים
                              </span>
                            ),
                            children: renderValidationForm()
                          }
                        ]}
                        style={{ marginTop: '16px' }}
                      />

                      <Divider style={{ margin: '32px 0' }} />

                      {/* Features List */}
                      <div style={{ textAlign: 'center' }}>
                        <Space direction="vertical" size="small" style={{ width: '100%' }}>
                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
                            <CheckCircleOutlined style={{ color: '#52c41a' }} />
                            <Text style={{ fontSize: '14px', color: '#666' }}>ניהול זמן מחשבים מתקדם</Text>
                          </div>
                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
                            <CheckCircleOutlined style={{ color: '#52c41a' }} />
                            <Text style={{ fontSize: '14px', color: '#666' }}>מערכת אישורי הדפסה</Text>
                          </div>
                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
                            <CheckCircleOutlined style={{ color: '#52c41a' }} />
                            <Text style={{ fontSize: '14px', color: '#666' }}>דשבורד ניהול מתקדם</Text>
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
                    transform: isVisible ? 'translateX(0)' : 'translateX(50px)',
                    transition: 'all 0.8s cubic-bezier(0.4, 0, 0.2, 1) 0.4s'
                  }}>
                    {showDownload ? (
                      renderDownloadSection()
                    ) : (
                      <Card 
                        style={{ 
                          height: '100%',
                          borderRadius: '24px',
                          boxShadow: '0 20px 60px rgba(0,0,0,0.15)',
                          background: 'rgba(255, 255, 255, 0.95)',
                          backdropFilter: 'blur(20px)',
                          border: '1px solid rgba(255, 255, 255, 0.3)',
                          overflow: 'hidden',
                          position: 'relative'
                        }}
                        styles={{ body: { padding: '48px' } }}
                      >
                        {/* Decorative gradient overlay */}
                        <div style={{
                          position: 'absolute',
                          top: 0,
                          left: 0,
                          right: 0,
                          height: '4px',
                          background: 'linear-gradient(90deg, #f093fb, #f5576c)'
                        }} />

                        <div style={{ textAlign: 'center', marginBottom: '32px' }}>
                          <div style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            width: '60px',
                            height: '60px',
                            background: 'linear-gradient(135deg, #f093fb, #f5576c)',
                            borderRadius: '50%',
                            marginBottom: '16px'
                          }}>
                            <DownloadOutlined style={{ fontSize: '24px', color: 'white' }} />
                          </div>
                          
                          <Title level={3} style={{ color: '#2c3e50', marginBottom: '8px' }}>
                            הורדת התוכנה
                          </Title>
                          
                          <Paragraph style={{ color: '#7f8c8d', marginBottom: '0' }}>
                            לאחר הרישום או האימות, תוכלו להוריד את התוכנה
                          </Paragraph>
                        </div>

                        {/* Features Grid */}
                        <Row gutter={[16, 16]} style={{ marginBottom: '32px' }}>
                          <Col span={12}>
                            <div style={{ textAlign: 'center', padding: '16px' }}>
                              <SecurityScanOutlined style={{ fontSize: '24px', color: '#667eea', marginBottom: '8px' }} />
                              <Text style={{ display: 'block', fontWeight: 600, color: '#2c3e50' }}>אבטחה מתקדמת</Text>
                              <Text style={{ fontSize: '12px', color: '#7f8c8d' }}>הצפנה מלאה</Text>
                            </div>
                          </Col>
                          <Col span={12}>
                            <div style={{ textAlign: 'center', padding: '16px' }}>
                              <CloudOutlined style={{ fontSize: '24px', color: '#667eea', marginBottom: '8px' }} />
                              <Text style={{ display: 'block', fontWeight: 600, color: '#2c3e50' }}>ענן מאובטח</Text>
                              <Text style={{ fontSize: '12px', color: '#7f8c8d' }}>סנכרון אוטומטי</Text>
                            </div>
                          </Col>
                          <Col span={12}>
                            <div style={{ textAlign: 'center', padding: '16px' }}>
                              <ClockCircleOutlined style={{ fontSize: '24px', color: '#667eea', marginBottom: '8px' }} />
                              <Text style={{ display: 'block', fontWeight: 600, color: '#2c3e50' }}>ניהול זמן</Text>
                              <Text style={{ fontSize: '12px', color: '#7f8c8d' }}>מעקב מדויק</Text>
                            </div>
                          </Col>
                          <Col span={12}>
                            <div style={{ textAlign: 'center', padding: '16px' }}>
                              <GlobalOutlined style={{ fontSize: '24px', color: '#667eea', marginBottom: '8px' }} />
                              <Text style={{ display: 'block', fontWeight: 600, color: '#2c3e50' }}>גישה מרחוק</Text>
                              <Text style={{ fontSize: '12px', color: '#7f8c8d' }}>מכל מקום</Text>
                            </div>
                          </Col>
                        </Row>

                        <div style={{
                          background: 'linear-gradient(135deg, #f8f9ff, #e8f2ff)',
                          borderRadius: '16px',
                          padding: '24px',
                          textAlign: 'center',
                          border: '1px solid #e1e8ff'
                        }}>
                          <Text style={{ color: '#667eea', fontWeight: 600 }}>
                            בחרו את האפשרות המתאימה בצד שמאל
                          </Text>
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

export default LandingPage;