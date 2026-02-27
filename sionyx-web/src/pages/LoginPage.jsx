import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Form, Input, Button, Card, Typography, Alert, Divider, App } from 'antd';
import { PhoneOutlined, LockOutlined, BankOutlined } from '@ant-design/icons';
import { signInAdmin } from '../services/authService';
import { useAuthStore } from '../store/authStore';

const { Title, Text } = Typography;

const LoginPage = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [failedAttempts, setFailedAttempts] = useState(0);
  const [cooldown, setCooldown] = useState(0);
  const navigate = useNavigate();
  const setUser = useAuthStore(state => state.setUser);
  const { message } = App.useApp();

  useEffect(() => {
    if (cooldown <= 0) return;
    const t = setInterval(() => setCooldown(c => Math.max(0, c - 1)), 1000);
    return () => clearInterval(t);
  }, [cooldown]);

  const onFinish = async values => {
    if (cooldown > 0) return;
    setLoading(true);
    setError(null);

    const result = await signInAdmin(values.phone, values.password, values.orgId);

    if (result.success) {
      setUser(result.user);
      setFailedAttempts(0);
      message.success(`ברוך הבא ל-${values.orgId}!`);
      navigate('/admin');
    } else {
      setError(result.error);
      message.error(result.error);
      setFailedAttempts(prev => {
        const next = prev + 1;
        if (next >= 3) setCooldown(30);
        return next;
      });
    }

    setLoading(false);
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        padding: '20px',
        direction: 'rtl',
      }}
    >
      <Card
        style={{
          width: '100%',
          maxWidth: 450,
          borderRadius: 16,
          boxShadow: '0 10px 40px rgba(0,0,0,0.2)',
        }}
      >
          <div style={{ textAlign: 'center', marginBottom: 32 }}>
            <Title level={2} style={{ marginBottom: 8 }}>
              SIONYX מנהל
            </Title>
            <Text type='secondary'>התחבר ללוח הבקרה של המנהל</Text>
          </div>

          {error && (
            <Alert
              message={error}
              type='error'
              showIcon
              closable
              onClose={() => setError(null)}
              style={{ marginBottom: 24 }}
            />
          )}

          <Form name='login' onFinish={onFinish} layout='vertical' size='large'>
            <Form.Item
              name='orgId'
              label='מזהה ארגון'
              rules={[
                { required: true, message: 'אנא הזן את מזהה הארגון שלך' },
                {
                  pattern: /^[a-z0-9-]+$/,
                  message: 'רק אותיות קטנות, מספרים ומקפים מותרים',
                },
              ]}
              tooltip='מזהה הארגון שלך מקובץ ה-.env (למשל, my-org, tech-lab)'
            >
              <Input
                prefix={<BankOutlined />}
                placeholder='למשל, my-organization'
                autoComplete='organization'
              />
            </Form.Item>

            <Divider style={{ margin: '16px 0' }} />

            <Form.Item
              name='phone'
              label='מספר טלפון'
              rules={[
                { required: true, message: 'אנא הזן את מספר הטלפון שלך' },
                {
                  pattern: /^[\d\s\-\+\(\)]+$/,
                  message: 'אנא הזן מספר טלפון תקין',
                },
              ]}
            >
              <Input prefix={<PhoneOutlined />} placeholder='למשל, 1234567890' autoComplete='tel' />
            </Form.Item>

            <Form.Item
              name='password'
              label='סיסמה'
              rules={[{ required: true, message: 'אנא הזן את הסיסמה שלך' }]}
            >
              <Input.Password
                prefix={<LockOutlined />}
                placeholder='סיסמה'
                autoComplete='current-password'
              />
            </Form.Item>

            <Form.Item style={{ marginBottom: 0 }}>
              <Button
                type='primary'
                htmlType='submit'
                loading={loading}
                disabled={cooldown > 0}
                block
                style={{ height: 45, fontSize: 16 }}
              >
                {cooldown > 0 ? `המתן ${cooldown} שניות` : 'התחבר'}
              </Button>
            </Form.Item>
          </Form>

          <div style={{ marginTop: 24, padding: 16, background: '#f5f5f5', borderRadius: 8 }}>
            <Text type='secondary' style={{ fontSize: 13, display: 'block', marginBottom: 8 }}>
              <strong>איפה למצוא את מזהה הארגון שלך:</strong>
            </Text>
            <Text type='secondary' style={{ fontSize: 12, display: 'block' }}>
              • בדוק את קובץ ה-<code>.env</code> שלך: <code>ORG_ID=your-org-id</code>
            </Text>
            <Text type='secondary' style={{ fontSize: 12, display: 'block' }}>
              • שאל את מנהל המערכת שלך
            </Text>
            <Text type='secondary' style={{ fontSize: 12, display: 'block', marginTop: 8 }}>
              השתמש באותו מספר טלפון וסיסמה כמו באפליקציית הדסקטופ.
            </Text>
          </div>

          <div style={{ textAlign: 'center', marginTop: 16 }}>
            <Text type='secondary' style={{ fontSize: 12 }}>
              פנה למנהל הארגון שלך אם אתה זקוק לעזרה
            </Text>
          </div>
        </Card>
    </div>
  );
};

export default LoginPage;
