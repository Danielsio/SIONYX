import { Card, Descriptions, Typography } from 'antd';
import { UserOutlined, PhoneOutlined, SettingOutlined } from '@ant-design/icons';
import { useSupervisorAuthStore } from '../store/supervisorAuthStore';

const { Title } = Typography;

const SupervisorSettingsPage = () => {
  const supervisor = useSupervisorAuthStore(state => state.supervisor);

  const orgCount = supervisor?.orgIds?.length || 0;

  return (
    <div style={{ direction: 'rtl', maxWidth: 600, margin: '0 auto' }}>
      <Title level={3} style={{ marginBottom: 24 }}>
        <SettingOutlined style={{ marginLeft: 8 }} />
        הגדרות
      </Title>

      <Card
        size='small'
        title='פרופיל מפקח'
        styles={{ body: { padding: 0 } }}
      >
        <Descriptions column={1} bordered size='small'>
          <Descriptions.Item
            label={<><UserOutlined style={{ marginLeft: 8 }} />שם</>}
          >
            {supervisor?.name || '-'}
          </Descriptions.Item>
          <Descriptions.Item
            label={<><PhoneOutlined style={{ marginLeft: 8 }} />טלפון</>}
          >
            {supervisor?.phone || '-'}
          </Descriptions.Item>
          <Descriptions.Item label='ארגונים בפיקוח'>
            {orgCount}
          </Descriptions.Item>
          <Descriptions.Item label='תאריך יצירה'>
            {supervisor?.createdAt
              ? new Date(supervisor.createdAt).toLocaleDateString('he-IL')
              : '-'}
          </Descriptions.Item>
        </Descriptions>
      </Card>
    </div>
  );
};

export default SupervisorSettingsPage;
