import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Form, Input, Button, Card, Typography, message, Alert, Divider } from 'antd';
import { PhoneOutlined, LockOutlined, BankOutlined } from '@ant-design/icons';
import { signInAdmin } from '../services/authService';
import { useAuthStore } from '../store/authStore';

const { Title, Text } = Typography;

const LoginPage = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();
  const setUser = useAuthStore((state) => state.setUser);

  const onFinish = async (values) => {
    setLoading(true);
    setError(null);

    const result = await signInAdmin(values.phone, values.password, values.orgId);

    if (result.success) {
      setUser(result.user);
      message.success(`Welcome to ${values.orgId}!`);
      navigate('/');
    } else {
      setError(result.error);
      message.error(result.error);
    }

    setLoading(false);
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      padding: '20px'
    }}>
      <Card 
        style={{ 
          width: '100%', 
          maxWidth: 450,
          borderRadius: 12,
          boxShadow: '0 10px 40px rgba(0,0,0,0.2)'
        }}
      >
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <Title level={2} style={{ marginBottom: 8 }}>
            SIONYX Admin
          </Title>
          <Text type="secondary">
            Sign in to your admin dashboard
          </Text>
        </div>

        {error && (
          <Alert
            message={error}
            type="error"
            showIcon
            closable
            onClose={() => setError(null)}
            style={{ marginBottom: 24 }}
          />
        )}

        <Form
          name="login"
          onFinish={onFinish}
          layout="vertical"
          size="large"
        >
          <Form.Item
            name="orgId"
            label="Organization ID"
            rules={[
              { required: true, message: 'Please enter your organization ID' },
              { 
                pattern: /^[a-z0-9-]+$/, 
                message: 'Only lowercase letters, numbers, and hyphens allowed' 
              }
            ]}
            tooltip="Your organization ID from the .env file (e.g., my-org, tech-lab)"
          >
            <Input
              prefix={<BankOutlined />}
              placeholder="e.g., my-organization"
              autoComplete="organization"
            />
          </Form.Item>

          <Divider style={{ margin: '16px 0' }} />

          <Form.Item
            name="phone"
            label="Phone Number"
            rules={[
              { required: true, message: 'Please enter your phone number' },
              { 
                pattern: /^[\d\s\-\+\(\)]+$/, 
                message: 'Please enter a valid phone number' 
              }
            ]}
          >
            <Input
              prefix={<PhoneOutlined />}
              placeholder="e.g., 1234567890"
              autoComplete="tel"
            />
          </Form.Item>

          <Form.Item
            name="password"
            label="Password"
            rules={[
              { required: true, message: 'Please enter your password' }
            ]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="Password"
              autoComplete="current-password"
            />
          </Form.Item>

          <Form.Item style={{ marginBottom: 0 }}>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              block
              style={{ height: 45, fontSize: 16 }}
            >
              Sign In
            </Button>
          </Form.Item>
        </Form>

        <div style={{ marginTop: 24, padding: 16, background: '#f5f5f5', borderRadius: 8 }}>
          <Text type="secondary" style={{ fontSize: 13, display: 'block', marginBottom: 8 }}>
            <strong>Where to find your Organization ID:</strong>
          </Text>
          <Text type="secondary" style={{ fontSize: 12, display: 'block' }}>
            • Check your <code>.env</code> file: <code>ORG_ID=your-org-id</code>
          </Text>
          <Text type="secondary" style={{ fontSize: 12, display: 'block' }}>
            • Ask your system administrator
          </Text>
          <Text type="secondary" style={{ fontSize: 12, display: 'block', marginTop: 8 }}>
            Use the same phone and password as your desktop app.
          </Text>
        </div>

        <div style={{ textAlign: 'center', marginTop: 16 }}>
          <Text type="secondary" style={{ fontSize: 12 }}>
            Contact your organization administrator if you need help
          </Text>
        </div>
      </Card>
    </div>
  );
};

export default LoginPage;
