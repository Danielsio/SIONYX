import { useState, useEffect } from 'react';
import { Card, Typography, Tabs, Space } from 'antd';
import {
  SettingOutlined,
  DollarOutlined,
  DownloadOutlined,
  MessageOutlined,
  CreditCardOutlined,
  LockOutlined,
  SafetyOutlined,
  PictureOutlined,
} from '@ant-design/icons';
import PricingSettings from '../components/settings/PricingSettings';
import DownloadsSettings from '../components/settings/DownloadsSettings';
import DisplayNameSettings from '../components/settings/DisplayNameSettings';
import PaymentSettings from '../components/settings/PaymentSettings';
import KioskPasswordSettings from '../components/settings/KioskPasswordSettings';
import PhoneVerificationSettings from '../components/settings/PhoneVerificationSettings';
import KioskDesignSettings from '../components/settings/KioskDesignSettings';

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
    {
      key: 'messages',
      label: (
        <span>
          <MessageOutlined />
          {' '}שם בהודעות
        </span>
      ),
      children: <DisplayNameSettings />,
    },
    {
      key: 'payment',
      label: (
        <span>
          <CreditCardOutlined />
          {' '}תשלומים
        </span>
      ),
      children: <PaymentSettings />,
    },
    {
      key: 'kioskPassword',
      label: (
        <span>
          <LockOutlined />
          {' '}סיסמת קיוסק
        </span>
      ),
      children: <KioskPasswordSettings />,
    },
    {
      key: 'phoneVerification',
      label: (
        <span>
          <SafetyOutlined />
          {' '}אימות טלפון
        </span>
      ),
      children: <PhoneVerificationSettings />,
    },
    {
      key: 'kioskDesign',
      label: (
        <span>
          <PictureOutlined />
          {' '}עיצוב קיוסק
        </span>
      ),
      children: <KioskDesignSettings />,
    },
    {
      key: 'downloads',
      label: (
        <span>
          <DownloadOutlined />
          {' '}הורדות
        </span>
      ),
      children: <DownloadsSettings />,
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
