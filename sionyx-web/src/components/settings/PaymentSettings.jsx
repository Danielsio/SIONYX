import { useState, useEffect } from 'react';
import { Form, Switch, Button, App, Alert, Space } from 'antd';
import { CreditCardOutlined } from '@ant-design/icons';
import { getPaymentSettings, updatePaymentSettings } from '../../services/settingsService';
import { useOrgId } from '../../hooks/useOrgId';

/**
 * Payment options. `saveCardEnabled` controls whether the kiosk offers the
 * saved-card ("keva") one-click flow. The gateway password is never handled
 * here — it lives server-side only (the Worker charges saved cards).
 */
const PaymentSettings = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const { message } = App.useApp();
  const orgId = useOrgId();

  useEffect(() => {
    if (!orgId) return;
    setLoading(true);
    getPaymentSettings(orgId).then(res => {
      if (res.success) form.setFieldsValue({ saveCardEnabled: res.payment.saveCardEnabled });
      setLoading(false);
    });
  }, [orgId, form]);

  const handleSave = async values => {
    if (!orgId) return;
    setSaving(true);
    const res = await updatePaymentSettings(orgId, {
      saveCardEnabled: !!values.saveCardEnabled,
    });
    if (res.success) {
      message.success('הגדרות התשלום נשמרו בהצלחה');
    } else {
      message.error(res.error || 'שגיאה בשמירה');
    }
    setSaving(false);
  };

  return (
    <Space direction='vertical' size='middle' style={{ width: '100%', maxWidth: 520 }}>
      <Alert
        type='info'
        showIcon
        icon={<CreditCardOutlined />}
        message='כשהאפשרות פעילה, לקוחות יכולים לשמור כרטיס ולשלם בלחיצה אחת ברכישה הבאה. פרטי הכרטיס נשמרים אצל חברת הסליקה — לא אצלנו.'
      />
      <Form form={form} layout='horizontal' onFinish={handleSave}>
        <Form.Item
          label='אפשר שמירת כרטיס (תשלום בלחיצה אחת)'
          name='saveCardEnabled'
          valuePropName='checked'
        >
          <Switch disabled={loading} />
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

export default PaymentSettings;
