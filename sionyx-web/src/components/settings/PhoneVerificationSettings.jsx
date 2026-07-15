import { useState, useEffect } from 'react';
import { Switch, App, Alert, Space, Spin, Typography } from 'antd';
import { SafetyOutlined } from '@ant-design/icons';
import {
  getPhoneVerificationSetting,
  setPhoneVerificationSetting,
} from '../../services/settingsService';
import { useOrgId } from '../../hooks/useOrgId';

const { Text } = Typography;

/**
 * Approval gate: when on, a user cannot start a kiosk session until an admin
 * marks their phone verified (from the Users page). No SMS is involved.
 */
const PhoneVerificationSettings = () => {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [enabled, setEnabled] = useState(false);
  const { message } = App.useApp();
  const orgId = useOrgId();

  useEffect(() => {
    if (!orgId) return;
    setLoading(true);
    getPhoneVerificationSetting(orgId).then(res => {
      if (res.success) setEnabled(res.requirePhoneVerification);
      setLoading(false);
    });
  }, [orgId]);

  const handleToggle = async value => {
    setSaving(true);
    const res = await setPhoneVerificationSetting(orgId, value);
    if (res.success) {
      setEnabled(value);
      message.success(
        value
          ? 'אימות טלפון נדרש. משתמשים חדשים יחכו לאישור מנהל.'
          : 'אימות טלפון בוטל. כל המשתמשים יכולים להתחיל הפעלה.'
      );
    } else {
      message.error(res.error || 'שגיאה בשמירה');
    }
    setSaving(false);
  };

  if (loading) return <Spin />;

  return (
    <Space direction='vertical' size='middle' style={{ width: '100%', maxWidth: 560 }}>
      <Alert
        type='info'
        showIcon
        icon={<SafetyOutlined />}
        message='כשהאפשרות פעילה, משתמש לא יוכל להתחיל הפעלה בקיוסק עד שמנהל יאשר את מספר הטלפון שלו (בעמוד המשתמשים). לא נשלחת הודעת SMS.'
      />
      <Space>
        <Switch checked={enabled} onChange={handleToggle} loading={saving} />
        <Text>{enabled ? 'נדרש אימות טלפון' : 'לא נדרש אימות טלפון'}</Text>
      </Space>
    </Space>
  );
};

export default PhoneVerificationSettings;
