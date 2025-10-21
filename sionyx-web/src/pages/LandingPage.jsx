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
  Badge
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
  GlobalOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { registerOrganization } from '../services/organizationService';
import { downloadSoftware } from '../services/downloadService';

const { Title, Paragraph, Text } = Typography;

const LandingPage = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [showDownload, setShowDownload] = useState(false);
  const [downloadLoading, setDownloadLoading] = useState(false);
  const [isVisible, setIsVisible] = useState(false);
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
        form.resetFields();
        setShowDownload(true);
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

  const handleDownload = async () => {
    setDownloadLoading(true);
    try {
      const result = await downloadSoftware();
      if (result.success) {
        message.success('ההורדה החלה בהצלחה!');
      } else {
        message.error(result.error || 'שגיאה בהורדת התוכנה');
      }
    } catch (error) {
      message.error('שגיאה בהורדת התוכנה');
      console.error('Download error:', error);
    } finally {
      setDownloadLoading(false);
    }
  };

  return (
    <div style={{ 
      minHeight: '100vh', 
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%)',
      direction: 'rtl',
      position: 'relative',
      overflow: 'hidden'
    }}>
      {/* Animated Background Elements */}
      <div style={{
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        background: `
          radial-gradient(circle at 20% 80%, rgba(120, 119, 198, 0.3) 0%, transparent 50%),
          radial-gradient(circle at 80% 20%, rgba(255, 119, 198, 0.3) 0%, transparent 50%),
          radial-gradient(circle at 40% 40%, rgba(120, 200, 255, 0.2) 0%, transparent 50%)
        `,
        animation: 'float 6s ease-in-out infinite'
      }} />
      
      {/* Header */}
      <div style={{ 
        padding: '40px 0 20px', 
        textAlign: 'center',
        color: 'white',
        position: 'relative',
        zIndex: 2
      }}>
        <div style={{
          opacity: isVisible ? 1 : 0,
          transform: isVisible ? 'translateY(0)' : 'translateY(-30px)',
          transition: 'all 0.8s cubic-bezier(0.4, 0, 0.2, 1)'
        }}>
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '12px',
            marginBottom: '16px',
            padding: '12px 24px',
            background: 'rgba(255, 255, 255, 0.1)',
            borderRadius: '50px',
            backdropFilter: 'blur(10px)',
            border: '1px solid rgba(255, 255, 255, 0.2)'
          }}>
            <StarOutlined style={{ color: '#ffd700', fontSize: '20px' }} />
            <Text style={{ color: 'white', fontSize: '16px', fontWeight: 500 }}>
              פתרון ניהול זמן מתקדם
            </Text>
          </div>
          
          <Title level={1} style={{ 
            color: 'white', 
            marginBottom: '8px',
            fontSize: '3.5rem',
            fontWeight: 700,
            background: 'linear-gradient(135deg, #ffffff 0%, #f0f0f0 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            textShadow: '0 4px 20px rgba(0,0,0,0.3)'
          }}>
            SIONYX
          </Title>
          
          <Paragraph style={{ 
            color: 'rgba(255,255,255,0.9)', 
            fontSize: '20px', 
            marginBottom: 0,
            maxWidth: '600px',
            margin: '0 auto',
            lineHeight: 1.6
          }}>
            ניהול זמן חכם ואינטליגנטי לארגונים מובילים
          </Paragraph>
        </div>
      </div>

      {/* Main Content */}
      <div style={{ 
        padding: '60px 20px',
        position: 'relative',
        zIndex: 2
      }}>
        <Row justify="center" gutter={[60, 40]}>
          {/* Company Description */}
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
                
                <Space direction="vertical" size="large" style={{ width: '100%' }}>
                  <div style={{ textAlign: 'center' }}>
                    <div style={{
                      width: '80px',
                      height: '80px',
                      borderRadius: '50%',
                      background: 'linear-gradient(135deg, #667eea, #764ba2)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      margin: '0 auto 24px',
                      boxShadow: '0 8px 32px rgba(102, 126, 234, 0.3)'
                    }}>
                      <RocketOutlined style={{ fontSize: '36px', color: 'white' }} />
                    </div>
                    <Title level={2} style={{ 
                      marginBottom: '16px',
                      fontSize: '2.2rem',
                      fontWeight: 700,
                      color: '#2c3e50'
                    }}>
                      ברוכים הבאים ל-SIONYX
                    </Title>
                  </div>
                  
                  <Paragraph style={{ 
                    fontSize: '18px', 
                    textAlign: 'center',
                    color: '#5a6c7d',
                    lineHeight: 1.7,
                    marginBottom: '32px'
                  }}>
                    SIONYX הוא פתרון ניהול זמן מתקדם המיועד לארגונים מובילים. 
                    המערכת מספקת כלים חכמים לניהול יעיל של משאבי זמן, 
                    מעקב מתקדם אחר פעילות משתמשים, ושליטה מלאה על השימוש במערכת.
                  </Paragraph>

                  <div>
                    <Title level={4} style={{ 
                      color: '#2c3e50',
                      marginBottom: '24px',
                      fontSize: '1.3rem',
                      fontWeight: 600
                    }}>
                      תכונות עיקריות:
                    </Title>
                    <Space direction="vertical" size="large" style={{ width: '100%' }}>
                      {[
                        { icon: <TeamOutlined />, text: 'ניהול משתמשים וארגונים', color: '#52c41a' },
                        { icon: <SafetyOutlined />, text: 'אבטחה מתקדמת ושליטה מלאה', color: '#1890ff' },
                        { icon: <CloudOutlined />, text: 'ניהול ענן וסנכרון בזמן אמת', color: '#722ed1' },
                        { icon: <ClockCircleOutlined />, text: 'דוחות זמן מפורטים ומדויקים', color: '#fa8c16' }
                      ].map((feature, index) => (
                        <div 
                          key={index}
                          style={{ 
                            display: 'flex', 
                            alignItems: 'center', 
                            gap: '16px',
                            padding: '16px',
                            borderRadius: '12px',
                            background: 'rgba(102, 126, 234, 0.05)',
                            border: '1px solid rgba(102, 126, 234, 0.1)',
                            transition: 'all 0.3s ease',
                            cursor: 'pointer'
                          }}
                          onMouseEnter={(e) => {
                            e.currentTarget.style.background = 'rgba(102, 126, 234, 0.1)';
                            e.currentTarget.style.transform = 'translateX(8px)';
                          }}
                          onMouseLeave={(e) => {
                            e.currentTarget.style.background = 'rgba(102, 126, 234, 0.05)';
                            e.currentTarget.style.transform = 'translateX(0)';
                          }}
                        >
                          <div style={{
                            width: '40px',
                            height: '40px',
                            borderRadius: '50%',
                            background: `${feature.color}15`,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            fontSize: '18px',
                            color: feature.color
                          }}>
                            {feature.icon}
                          </div>
                          <Text style={{ fontSize: '16px', fontWeight: 500, color: '#2c3e50' }}>
                            {feature.text}
                          </Text>
                        </div>
                      ))}
                    </Space>
                  </div>

                  <Divider style={{ margin: '32px 0' }} />

                  <div style={{ textAlign: 'center' }}>
                    <Button 
                      type="primary" 
                      size="large"
                      icon={<SettingOutlined />}
                      onClick={handleAdminLogin}
                      style={{ 
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
                      לוח בקרה למנהלים
                      <ArrowRightOutlined style={{ marginRight: '8px' }} />
                    </Button>
                  </div>
                </Space>
              </Card>
            </div>
          </Col>

          {/* Organization Registration */}
          <Col xs={24} lg={12}>
            <div style={{
              opacity: isVisible ? 1 : 0,
              transform: isVisible ? 'translateX(0)' : 'translateX(50px)',
              transition: 'all 0.8s cubic-bezier(0.4, 0, 0.2, 1) 0.4s'
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
                  background: 'linear-gradient(90deg, #f093fb, #f5576c, #4facfe)'
                }} />
                
                <div style={{ textAlign: 'center', marginBottom: '32px' }}>
                  <div style={{
                    width: '80px',
                    height: '80px',
                    borderRadius: '50%',
                    background: 'linear-gradient(135deg, #f093fb, #f5576c)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    margin: '0 auto 24px',
                    boxShadow: '0 8px 32px rgba(240, 147, 251, 0.3)'
                  }}>
                    <TeamOutlined style={{ fontSize: '36px', color: 'white' }} />
                  </div>
                  <Title level={2} style={{ 
                    marginBottom: '8px',
                    fontSize: '2.2rem',
                    fontWeight: 700,
                    color: '#2c3e50'
                  }}>
                    רישום ארגון חדש
                  </Title>
                  <Text style={{ color: '#5a6c7d', fontSize: '16px' }}>
                    התחל את המסע שלך עם SIONYX
                  </Text>
                </div>

                <Form
                  form={form}
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
                      { required: true, message: 'אנא הזן את מזהה המוסד' },
                      { min: 3, message: 'מזהה המוסד חייב להכיל לפחות 3 תווים' }
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
                      { required: true, message: 'אנא הזן את מפתח ה-API' },
                      { min: 10, message: 'מפתח ה-API חייב להכיל לפחות 10 תווים' }
                    ]}
                  >
                    <Input.Password 
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
                      {loading ? <Spin size="small" /> : 'הרשם ארגון'}
                    </Button>
                  </Form.Item>
                </Form>

                <Divider style={{ margin: '32px 0' }} />

                {showDownload ? (
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ 
                      marginBottom: '24px',
                      padding: '20px',
                      background: 'linear-gradient(135deg, #52c41a15, #73d13d15)',
                      borderRadius: '16px',
                      border: '1px solid #52c41a30'
                    }}>
                      <CheckCircleOutlined style={{ 
                        fontSize: '32px', 
                        color: '#52c41a',
                        marginBottom: '12px'
                      }} />
                      <div>
                        <Text style={{ 
                          fontSize: '18px', 
                          fontWeight: 600,
                          color: '#52c41a',
                          display: 'block',
                          marginBottom: '8px'
                        }}>
                          הארגון נרשם בהצלחה!
                        </Text>
                        <Text style={{ color: '#5a6c7d', fontSize: '14px' }}>
                          כעת תוכל להוריד את תוכנת SIONYX
                        </Text>
                      </div>
                    </div>
                    
                    <Button 
                      type="primary" 
                      size="large"
                      icon={<DownloadOutlined />}
                      loading={downloadLoading}
                      onClick={handleDownload}
                      style={{ 
                        height: '56px',
                        fontSize: '16px',
                        fontWeight: 600,
                        borderRadius: '16px',
                        background: 'linear-gradient(135deg, #52c41a, #73d13d)',
                        border: 'none',
                        boxShadow: '0 8px 24px rgba(82, 196, 26, 0.4)',
                        transition: 'all 0.3s ease'
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.transform = 'translateY(-2px)';
                        e.currentTarget.style.boxShadow = '0 12px 32px rgba(82, 196, 26, 0.5)';
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.transform = 'translateY(0)';
                        e.currentTarget.style.boxShadow = '0 8px 24px rgba(82, 196, 26, 0.4)';
                      }}
                    >
                      {downloadLoading ? 'מוריד...' : 'הורד את התוכנה'}
                    </Button>
                    
                    <div style={{ marginTop: '16px' }}>
                      <Text style={{ 
                        color: '#5a6c7d', 
                        fontSize: '14px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '8px'
                      }}>
                        <GlobalOutlined />
                        לחץ על הכפתור כדי להוריד את תוכנת SIONYX
                      </Text>
                    </div>
                  </div>
                ) : (
                  <div style={{ 
                    textAlign: 'center',
                    padding: '24px',
                    background: 'rgba(102, 126, 234, 0.05)',
                    borderRadius: '16px',
                    border: '1px solid rgba(102, 126, 234, 0.1)'
                  }}>
                    <Text style={{ 
                      color: '#5a6c7d', 
                      fontSize: '16px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: '8px'
                    }}>
                      <ClockCircleOutlined />
                      לאחר הרישום תקבלו קישור להורדת התוכנה
                    </Text>
                  </div>
                )}
              </Card>
            </div>
          </Col>
        </Row>
      </div>

      {/* Footer */}
      <div style={{ 
        textAlign: 'center', 
        padding: '60px 20px 40px',
        color: 'rgba(255,255,255,0.8)',
        position: 'relative',
        zIndex: 2
      }}>
        <div style={{
          opacity: isVisible ? 1 : 0,
          transform: isVisible ? 'translateY(0)' : 'translateY(30px)',
          transition: 'all 0.8s cubic-bezier(0.4, 0, 0.2, 1) 0.6s'
        }}>
          <Text style={{ fontSize: '16px' }}>
            © 2024 SIONYX. כל הזכויות שמורות.
          </Text>
        </div>
      </div>

    </div>
  );
};

export default LandingPage;
