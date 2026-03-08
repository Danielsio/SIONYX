import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Form, Input, Button, Card, Typography, Alert, App } from 'antd';
import { PhoneOutlined, LockOutlined } from '@ant-design/icons';
import { signInSupervisor } from '../services/supervisorAuthService';
import { useSupervisorAuthStore } from '../store/supervisorAuthStore';

const { Title, Text } = Typography;

const SupervisorLoginPage = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();
  const setSupervisor = useSupervisorAuthStore(state => state.setSupervisor);
  const { message } = App.useApp();

  const onFinish = async values => {
    setLoading(true);
    setError(null);

    const result = await signInSupervisor(values.phone, values.password);

    if (result.success) {
      setSupervisor(result.supervisor);
      message.success('התחברת בהצלחה');
      navigate('/supervisor');
    } else {
      setError(result.error);
      message.error(result.error);
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
        background: 'linear-gradient(135deg, #1a1030 0%, #0f0a1f 50%, #1a1030 100%)',
        padding: '20px',
        direction: 'rtl',
      }}
    >
      <Card
        style={{
          width: '100%',
          maxWidth: 450,
          borderRadius: 16,
          boxShadow: '0 10px 40px rgba(0,0,0,0.4)',
          border: '1px solid rgba(99, 102, 241, 0.2)',
        }}
      >
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <Title level={2} style={{ marginBottom: 8 }}>
            כניסת מפקח
          </Title>
          <Text type='secondary'>ממשק ניהול מפקחים</Text>
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

        <Form name='supervisor-login' onFinish={onFinish} layout='vertical' size='large'>
          <Form.Item
            name='phone'
            label='מספר טלפון'
            rules={[
              { required: true, message: 'אנא הזן את מספר הטלפון שלך' },
              {
                pattern: /^[\d\s\-+()]+$/,
                message: 'אנא הזן מספר טלפון תקין',
              },
            ]}
          >
            <Input
              prefix={<PhoneOutlined />}
              placeholder='למשל, 1234567890'
              autoComplete='tel'
            />
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
              block
              style={{
                height: 45,
                fontSize: 16,
                background: 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)',
                border: 'none',
              }}
            >
              התחבר
            </Button>
          </Form.Item>
        </Form>

        <div style={{ textAlign: 'center', marginTop: 24 }}>
          <Text type='secondary' style={{ fontSize: 12 }}>
            ממשק מפקחים – גישה מלאה לארגונים בפיקוח
          </Text>
        </div>
      </Card>
    </div>
  );
};

export default SupervisorLoginPage;
