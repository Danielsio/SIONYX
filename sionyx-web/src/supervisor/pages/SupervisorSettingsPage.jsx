import { Card, Descriptions, Typography } from 'antd';
import { UserOutlined, MailOutlined, PhoneOutlined } from '@ant-design/icons';
import { useSupervisorAuthStore } from '../store/supervisorAuthStore';

const { Title, Text } = Typography;

const SupervisorSettingsPage = () => {
  const supervisor = useSupervisorAuthStore(state => state.supervisor);

  return (
    <div style={{ direction: 'rtl' }}>
      <Title level={4} style={{ marginBottom: 24 }}>
        הגדרות מפקח
      </Title>

      <Card title='פרופיל מפקח' style={{ maxWidth: 500 }}>
        <Descriptions column={1} bordered size='small'>
          <Descriptions.Item
            label={<><UserOutlined style={{ marginLeft: 8 }} />שם</>}
          >
            {supervisor?.name || '-'}
          </Descriptions.Item>
          <Descriptions.Item
            label={<><MailOutlined style={{ marginLeft: 8 }} />אימייל</>}
          >
            {supervisor?.email || '-'}
          </Descriptions.Item>
          <Descriptions.Item
            label={<><PhoneOutlined style={{ marginLeft: 8 }} />טלפון</>}
          >
            {supervisor?.phone || '-'}
          </Descriptions.Item>
        </Descriptions>

        <div style={{ marginTop: 24 }}>
          <Text type='secondary'>הגדרות נוספות יופיעו כאן בעתיד.</Text>
        </div>
      </Card>
    </div>
  );
};

export default SupervisorSettingsPage;
