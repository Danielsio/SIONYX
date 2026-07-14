import { useState, useEffect } from 'react';
import { Form, Input, Button, App, Alert, Space } from 'antd';
import { MessageOutlined } from '@ant-design/icons';
import { getDisplayName, updateDisplayName } from '../../services/settingsService';
import { useOrgId } from '../../hooks/useOrgId';

/**
 * The name the kiosk shows as the sender of admin messages. Without it the
 * kiosk falls back to a generic "מנהל".
 */
const DisplayNameSettings = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const { message } = App.useApp();
  const orgId = useOrgId();

  useEffect(() => {
    if (!orgId) return;
    setLoading(true);
    getDisplayName(orgId).then(res => {
      if (res.success) form.setFieldsValue({ displayName: res.displayName });
      setLoading(false);
    });
  }, [orgId, form]);

  const handleSave = async values => {
    if (!orgId) return;
    setSaving(true);
    const res = await updateDisplayName(orgId, values.displayName || '');
    if (res.success) {
      message.success('השם נשמר בהצלחה');
    } else {
      message.error(res.error || 'שגיאה בשמירה');
    }
    setSaving(false);
  };

  return (
    <Space direction='vertical' size='middle' style={{ width: '100%', maxWidth: 480 }}>
      <Alert
        type='info'
        showIcon
        icon={<MessageOutlined />}
        message='השם שיוצג ללקוחות בקיוסק כשהם מקבלים ממך הודעה. ללא שם, יוצג "מנהל".'
      />
      <Form form={form} layout='vertical' onFinish={handleSave}>
        <Form.Item
          label='שם לתצוגה בהודעות'
          name='displayName'
          rules={[{ max: 40, message: 'עד 40 תווים' }]}
        >
          <Input placeholder='לדוגמה: הדפסות המרכז' maxLength={40} disabled={loading} />
        </Form.Item>
        <Form.Item style={{ marginBottom: 0 }}>
          <Button type='primary' htmlType='submit' loading={saving} disabled={loading}>
            שמור
          </Button>
        </Form.Item>
      </Form>
    </Space>
  );
};

export default DisplayNameSettings;
