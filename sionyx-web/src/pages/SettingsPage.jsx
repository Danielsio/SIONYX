import { useState } from 'react';
import { Card, Typography, Tabs, Space } from 'antd';
import { SettingOutlined, DollarOutlined, ClockCircleOutlined } from '@ant-design/icons';
import { useAuthStore } from '../store/authStore';
import { hasRole, ROLES, getRoleDisplayName, getUserRole } from '../utils/roles';
import PricingSettings from '../components/settings/PricingSettings';
import OperatingHoursSettings from '../components/settings/OperatingHoursSettings';

const { Title, Text } = Typography;

const SettingsPage = () => {
  const user = useAuthStore(state => state.user);
  const userRole = getUserRole(user);
  const isSupervisor = hasRole(user, ROLES.SUPERVISOR);

  // Build tabs based on user role
  const tabs = [
    {
      key: 'pricing',
      label: (
        <span>
          <DollarOutlined />
          תמחור הדפסות
        </span>
      ),
      children: <PricingSettings />,
      // Available to admin+
    },
  ];

  // Supervisor-only tabs
  if (isSupervisor) {
    tabs.push({
      key: 'operatingHours',
      label: (
        <span>
          <ClockCircleOutlined />
          שעות פעילות
        </span>
      ),
      children: <OperatingHoursSettings />,
    });
  }

  return (
    <div style={{ direction: 'rtl' }}>
      <Space direction='vertical' size='large' style={{ width: '100%' }}>
        {/* Header */}
        <div
          className='page-header'
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: 12,
          }}
        >
          <div>
            <Title level={2} style={{ margin: 0, display: 'flex', alignItems: 'center', gap: 12 }}>
              <SettingOutlined />
              הגדרות
            </Title>
            <Text type='secondary'>
              נהל את הגדרות הארגון שלך
              {isSupervisor && (
                <Text type='secondary' style={{ marginRight: 8 }}>
                  • תפקיד: {getRoleDisplayName(userRole)}
                </Text>
              )}
            </Text>
          </div>
        </div>

        {/* Settings Tabs */}
        <Card>
          <Tabs
            defaultActiveKey='pricing'
            items={tabs}
            tabPosition='right'
            style={{ minHeight: 400 }}
          />
        </Card>
      </Space>
    </div>
  );
};

export default SettingsPage;
