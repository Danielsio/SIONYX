import { useState, useEffect } from 'react';
import { Card, Typography, Tabs, Space } from 'antd';
import { SettingOutlined, DollarOutlined } from '@ant-design/icons';
import PricingSettings from '../components/settings/PricingSettings';

const { Title, Text } = Typography;

const useIsMobile = (breakpoint = 768) => {
  const [isMobile, setIsMobile] = useState(() => window.innerWidth < breakpoint);

  useEffect(() => {
    const mq = window.matchMedia(`(max-width: ${breakpoint - 1}px)`);
    const handler = (e) => setIsMobile(e.matches);
    mq.addEventListener('change', handler);
    return () => mq.removeEventListener('change', handler);
  }, [breakpoint]);

  return isMobile;
};

const SettingsPage = () => {
  const isMobile = useIsMobile();

  const tabs = [
    {
      key: 'pricing',
      label: (
        <span>
          <DollarOutlined />
          {' '}תמחור הדפסות
        </span>
      ),
      children: <PricingSettings />,
    },
  ];

  return (
    <div style={{ direction: 'rtl' }}>
      <Space direction='vertical' size='large' style={{ width: '100%' }}>
        <div
          className='page-header'
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: 12,
            padding: isMobile ? '0 4px' : undefined,
          }}
        >
          <div>
            <Title
              level={isMobile ? 3 : 2}
              style={{ margin: 0, display: 'flex', alignItems: 'center', gap: 8 }}
            >
              <SettingOutlined />
              הגדרות
            </Title>
            <Text type='secondary' style={{ fontSize: isMobile ? 12 : 14 }}>
              נהל את הגדרות הארגון שלך
            </Text>
          </div>
        </div>

        <Card
          styles={{ body: { padding: isMobile ? '12px 8px' : undefined } }}
        >
          <Tabs
            defaultActiveKey='pricing'
            items={tabs}
            tabPosition={isMobile ? 'top' : 'right'}
            style={{ minHeight: isMobile ? undefined : 400 }}
          />
        </Card>
      </Space>
    </div>
  );
};

export default SettingsPage;
