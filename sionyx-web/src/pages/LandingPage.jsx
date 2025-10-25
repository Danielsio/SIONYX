import { useState, useCallback, memo } from 'react';
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
} from 'antd';
import {
  DownloadOutlined,
  SettingOutlined,
  TeamOutlined,
  RocketOutlined,
  CrownOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { registerOrganization } from '../services/organizationService';
import { downloadFile } from '../services/downloadService';

const { Title, Paragraph, Text } = Typography;

const LandingPage = memo(() => {
  const [registrationForm] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [downloadLoading, setDownloadLoading] = useState(false);
  const navigate = useNavigate();

  const handleRegistration = useCallback(async (values) => {
    setLoading(true);
    try {
      const result = await registerOrganization(values);
      if (result.success) {
        message.success('הארגון נוצר בהצלחה!');
        registrationForm.resetFields();
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
      
      // Get download URL from environment variable
      const downloadUrl = import.meta.env.VITE_INSTALLER_DOWNLOAD_URL;
      
      
      if (!downloadUrl) {
        const errorMsg = 'Download URL not configured. Please set VITE_INSTALLER_DOWNLOAD_URL in your environment variables.';
        console.error('DOWNLOAD ERROR:', errorMsg);
        throw new Error(errorMsg);
      }
      
      await downloadFile(downloadUrl, 'sionyx-installer.exe');
      message.success('ההורדה הושלמה בהצלחה!');
    } catch (error) {
      console.error('Download error:', error);
      message.error(error.message || 'שגיאה בהורדה. נסה שוב.');
    } finally {
      setDownloadLoading(false);
    }
  }, []);

  const handleAdminLogin = useCallback(() => {
    navigate('/admin/login');
  }, [navigate]);


  return (
    <div 
      style={{ 
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        direction: 'rtl',
        textAlign: 'right',
        padding: '20px',
        position: 'relative',
      }}
    >
      {/* Admin Button - Top Right */}
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
          backgroundColor: 'rgba(255,255,255,0.2)',
          borderColor: 'white',
          color: 'white',
          boxShadow: '0 4px 15px rgba(0,0,0,0.2)',
          backdropFilter: 'blur(10px)',
        }}
      >
        פאנל ניהול
      </Button>

      <div style={{ maxWidth: '1000px', margin: '0 auto' }}>
        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: '60px', marginTop: '40px' }}>
          <Title 
            level={1} 
            style={{ 
              color: 'white', 
              fontSize: '4.5rem', 
              fontWeight: 'bold',
              marginBottom: '20px',
              textShadow: '2px 2px 4px rgba(0,0,0,0.3)',
              background: 'linear-gradient(45deg, #fff, #f0f0f0)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}
          >
            SIONYX
          </Title>
          <Paragraph 
            style={{ 
              color: 'white', 
              fontSize: '1.4rem', 
              margin: '0 auto 40px',
              textShadow: '1px 1px 2px rgba(0,0,0,0.3)',
              maxWidth: '700px',
              fontWeight: '300',
            }}
          >
            פתרון מתקדם לניהול זמן מחשבים ואישורי הדפסה
          </Paragraph>
          
        </div>

        <Row gutter={[40, 40]} justify="center">
          {/* Registration Form */}
          <Col xs={24} lg={12}>
            <Card
              style={{
                borderRadius: '25px',
                boxShadow: '0 20px 40px rgba(0,0,0,0.15)',
                border: 'none',
                background: 'rgba(255,255,255,0.95)',
                backdropFilter: 'blur(10px)',
                height: '100%',
              }}
            >
              <div style={{ padding: '40px 30px' }}>
                <div style={{ textAlign: 'center', marginBottom: '40px' }}>
                  <TeamOutlined style={{ fontSize: '4rem', color: '#667eea', marginBottom: '20px' }} />
                  <Title level={2} style={{ marginBottom: '15px', color: '#333' }}>
                    צור ארגון חדש
                  </Title>
                  <Text type="secondary" style={{ fontSize: '16px' }}>
                    מלא את הפרטים הבאים ליצירת ארגון חדש
                  </Text>
                </div>

                <Form
                  form={registrationForm}
                  onFinish={handleRegistration}
                  layout="vertical"
                  size="large"
                >
                  <Form.Item
                    name="organizationName"
                    label={<span style={{ fontSize: '16px', fontWeight: '600' }}>שם הארגון</span>}
                    rules={[
                      { required: true, message: 'נא להזין שם ארגון' },
                      { min: 2, message: 'שם הארגון חייב להכיל לפחות 2 תווים' }
                    ]}
                  >
                    <Input 
                      placeholder="הזן את שם הארגון שלכם"
                      style={{ 
                        textAlign: 'right',
                        height: '50px',
                        fontSize: '16px',
                        borderRadius: '12px',
                      }}
                    />
                  </Form.Item>

                  <Form.Item
                    name="nedarimMosadId"
                    label={<span style={{ fontSize: '16px', fontWeight: '600' }}>מזהה מוסד NEDARIM</span>}
                    rules={[
                      { required: true, message: 'נא להזין מזהה מוסד NEDARIM' },
                      { min: 1, message: 'מזהה מוסד NEDARIM נדרש' }
                    ]}
                  >
                    <Input 
                      placeholder="הזן את מזהה המוסד שלכם מ-NEDARIM"
                      style={{ 
                        textAlign: 'right',
                        height: '50px',
                        fontSize: '16px',
                        borderRadius: '12px',
                      }}
                    />
                  </Form.Item>

                  <Form.Item
                    name="nedarimApiValid"
                    label={<span style={{ fontSize: '16px', fontWeight: '600' }}>מפתח API של NEDARIM</span>}
                    rules={[
                      { required: true, message: 'נא להזין מפתח API של NEDARIM' },
                      { min: 1, message: 'מפתח API של NEDARIM נדרש' }
                    ]}
                  >
                    <Input 
                      placeholder="הזן את מפתח ה-API שלכם מ-NEDARIM"
                      style={{ 
                        textAlign: 'right',
                        height: '50px',
                        fontSize: '16px',
                        borderRadius: '12px',
                      }}
                    />
                  </Form.Item>

                  <div style={{ 
                    marginTop: '20px', 
                    padding: '15px', 
                    backgroundColor: '#f8f9fa', 
                    borderRadius: '10px',
                    border: '1px solid #e9ecef',
                    textAlign: 'center'
                  }}>
                    <Text type="secondary" style={{ fontSize: '14px', lineHeight: '1.5' }}>
                      <strong>איפה למצוא את הפרטים?</strong><br/>
                      את פרטי NEDARIM תוכלו למצוא בחשבון שלכם במערכת NEDARIM<br/>
                      תחת "הגדרות" → "מפתחות API"
                    </Text>
                  </div>

                  <Form.Item style={{ marginBottom: 0, textAlign: 'center', marginTop: '30px' }}>
                    <Button
                      type="primary"
                      htmlType="submit"
                      loading={loading}
                      size="large"
                      style={{
                        width: '100%',
                        height: '60px',
                        fontSize: '18px',
                        fontWeight: 'bold',
                        borderRadius: '30px',
                        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                        border: 'none',
                        boxShadow: '0 8px 25px rgba(102, 126, 234, 0.4)',
                      }}
                    >
                      {loading ? 'יוצר ארגון...' : 'צור ארגון'}
                    </Button>
                  </Form.Item>
                </Form>
              </div>
            </Card>
          </Col>

          {/* Download Section */}
          <Col xs={24} lg={12}>
            <Card
              style={{
                borderRadius: '25px',
                boxShadow: '0 20px 40px rgba(0,0,0,0.15)',
                border: 'none',
                background: 'linear-gradient(135deg, #52c41a 0%, #73d13d 100%)',
                color: 'white',
                textAlign: 'center',
                height: '100%',
                display: 'flex',
                alignItems: 'center',
              }}
            >
              <div style={{ padding: '40px 30px', width: '100%' }}>
                <RocketOutlined style={{ fontSize: '4rem', marginBottom: '25px' }} />
                <Title level={2} style={{ color: 'white', marginBottom: '20px', fontSize: '2.2rem' }}>
                  הורדת התוכנה
                </Title>
                <Paragraph style={{ 
                  color: 'rgba(255,255,255,0.9)', 
                  marginBottom: '40px', 
                  fontSize: '1.2rem',
                  lineHeight: '1.6',
                }}>
                  הורידו את התוכנה ישירות ללא צורך באימות
                </Paragraph>
                
                <Space direction="vertical" size="large" style={{ width: '100%' }}>
                  <Button
                    type="primary"
                    size="large"
                    icon={<DownloadOutlined />}
                    loading={downloadLoading}
                    onClick={handleDirectDownload}
                    style={{
                      height: '60px',
                      width: '100%',
                      fontSize: '18px',
                      fontWeight: 'bold',
                      borderRadius: '30px',
                      backgroundColor: 'white',
                      borderColor: 'white',
                      color: '#52c41a',
                      boxShadow: '0 8px 25px rgba(0,0,0,0.2)',
                    }}
                  >
                    {downloadLoading ? 'מוריד...' : 'הורד עכשיו'}
                  </Button>
                  
                  <Button
                    size="large"
                    icon={<SettingOutlined />}
                    onClick={handleAdminLogin}
                    style={{
                      height: '50px',
                      width: '100%',
                      fontSize: '16px',
                      fontWeight: 'bold',
                      borderRadius: '25px',
                      backgroundColor: 'rgba(255,255,255,0.2)',
                      borderColor: 'white',
                      color: 'white',
                      boxShadow: '0 4px 15px rgba(0,0,0,0.2)',
                      backdropFilter: 'blur(10px)',
                    }}
                  >
                    כבר רשום? היכנס לכאן
                  </Button>
                </Space>
              </div>
            </Card>
          </Col>
        </Row>
      </div>
    </div>
  );
});

LandingPage.displayName = 'LandingPage';

export default LandingPage;