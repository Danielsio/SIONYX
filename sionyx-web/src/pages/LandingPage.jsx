import { useState } from 'react';
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
  Spin
} from 'antd';
import { 
  RocketOutlined, 
  DownloadOutlined, 
  SettingOutlined,
  TeamOutlined,
  SecurityScanOutlined,
  CloudOutlined
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
  const navigate = useNavigate();

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
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      direction: 'rtl'
    }}>
      {/* Header */}
      <div style={{ 
        padding: '20px 0', 
        textAlign: 'center',
        color: 'white'
      }}>
        <Title level={1} style={{ color: 'white', marginBottom: 0 }}>
          SIONYX
        </Title>
        <Paragraph style={{ color: 'rgba(255,255,255,0.8)', fontSize: '18px', marginBottom: 0 }}>
          פתרון ניהול זמן מתקדם לארגונים
        </Paragraph>
      </div>

      {/* Main Content */}
      <div style={{ padding: '40px 20px' }}>
        <Row justify="center" gutter={[40, 40]}>
          {/* Company Description */}
          <Col xs={24} lg={12}>
            <Card 
              style={{ 
                height: '100%',
                borderRadius: '12px',
                boxShadow: '0 8px 32px rgba(0,0,0,0.1)'
              }}
            >
              <Space direction="vertical" size="large" style={{ width: '100%' }}>
                <div style={{ textAlign: 'center' }}>
                  <RocketOutlined style={{ fontSize: '48px', color: '#667eea', marginBottom: '16px' }} />
                  <Title level={2}>ברוכים הבאים ל-SIONYX</Title>
                </div>
                
                <Paragraph style={{ fontSize: '16px', textAlign: 'center' }}>
                  SIONYX הוא פתרון ניהול זמן מתקדם המיועד לארגונים. המערכת מאפשרת ניהול יעיל של 
                  משאבי זמן, מעקב אחר פעילות משתמשים, ושליטה מלאה על השימוש במערכת.
                </Paragraph>

                <div>
                  <Title level={4}>תכונות עיקריות:</Title>
                  <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <TeamOutlined style={{ color: '#52c41a' }} />
                      <Text>ניהול משתמשים וארגונים</Text>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <SecurityScanOutlined style={{ color: '#1890ff' }} />
                      <Text>אבטחה מתקדמת ושליטה מלאה</Text>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <CloudOutlined style={{ color: '#722ed1' }} />
                      <Text>ניהול ענן וסנכרון בזמן אמת</Text>
                    </div>
                  </Space>
                </div>

                <Divider />

                <div style={{ textAlign: 'center' }}>
                  <Button 
                    type="primary" 
                    size="large"
                    icon={<SettingOutlined />}
                    onClick={handleAdminLogin}
                    style={{ 
                      height: '50px',
                      fontSize: '16px',
                      borderRadius: '8px'
                    }}
                  >
                    לוח בקרה למנהלים
                  </Button>
                </div>
              </Space>
            </Card>
          </Col>

          {/* Organization Registration */}
          <Col xs={24} lg={12}>
            <Card 
              title={
                <div style={{ textAlign: 'center' }}>
                  <TeamOutlined style={{ marginLeft: '8px' }} />
                  רישום ארגון חדש
                </div>
              }
              style={{ 
                height: '100%',
                borderRadius: '12px',
                boxShadow: '0 8px 32px rgba(0,0,0,0.1)'
              }}
            >
              <Form
                form={form}
                layout="vertical"
                onFinish={handleOrganizationRegister}
                size="large"
              >
                <Form.Item
                  name="organizationName"
                  label="שם הארגון"
                  rules={[
                    { required: true, message: 'אנא הזן את שם הארגון' },
                    { min: 2, message: 'שם הארגון חייב להכיל לפחות 2 תווים' }
                  ]}
                >
                  <Input placeholder="הזן את שם הארגון" />
                </Form.Item>

                <Form.Item
                  name="nedarimMosadId"
                  label="מזהה מוסד נדרים"
                  rules={[
                    { required: true, message: 'אנא הזן את מזהה המוסד' },
                    { min: 3, message: 'מזהה המוסד חייב להכיל לפחות 3 תווים' }
                  ]}
                >
                  <Input placeholder="הזן את מזהה המוסד" />
                </Form.Item>

                <Form.Item
                  name="nedarimApiValid"
                  label="מפתח API נדרים"
                  rules={[
                    { required: true, message: 'אנא הזן את מפתח ה-API' },
                    { min: 10, message: 'מפתח ה-API חייב להכיל לפחות 10 תווים' }
                  ]}
                >
                  <Input.Password placeholder="הזן את מפתח ה-API" />
                </Form.Item>

                <Form.Item style={{ marginBottom: 0, textAlign: 'center' }}>
                  <Button 
                    type="primary" 
                    htmlType="submit"
                    size="large"
                    loading={loading}
                    style={{ 
                      width: '100%',
                      height: '50px',
                      fontSize: '16px',
                      borderRadius: '8px'
                    }}
                  >
                    {loading ? <Spin size="small" /> : 'הרשם ארגון'}
                  </Button>
                </Form.Item>
              </Form>

              <Divider />

              {showDownload ? (
                <div style={{ textAlign: 'center' }}>
                  <div style={{ marginBottom: '16px' }}>
                    <Text type="success" style={{ fontSize: '16px' }}>
                      ✅ הארגון נרשם בהצלחה!
                    </Text>
                  </div>
                  <Button 
                    type="primary" 
                    size="large"
                    icon={<DownloadOutlined />}
                    loading={downloadLoading}
                    onClick={handleDownload}
                    style={{ 
                      height: '50px',
                      fontSize: '16px',
                      borderRadius: '8px',
                      background: '#52c41a',
                      borderColor: '#52c41a'
                    }}
                  >
                    {downloadLoading ? 'מוריד...' : 'הורד את התוכנה'}
                  </Button>
                  <div style={{ marginTop: '12px' }}>
                    <Text type="secondary" style={{ fontSize: '12px' }}>
                      לחץ על הכפתור כדי להוריד את תוכנת SIONYX
                    </Text>
                  </div>
                </div>
              ) : (
                <div style={{ textAlign: 'center' }}>
                  <Text type="secondary">
                    לאחר הרישום תקבלו קישור להורדת התוכנה
                  </Text>
                </div>
              )}
            </Card>
          </Col>
        </Row>
      </div>

      {/* Footer */}
      <div style={{ 
        textAlign: 'center', 
        padding: '40px 20px',
        color: 'rgba(255,255,255,0.8)'
      }}>
        <Text>© 2024 SIONYX. כל הזכויות שמורות.</Text>
      </div>
    </div>
  );
};

export default LandingPage;
