import { useState, useEffect, useCallback } from 'react';
import { Form, Input, Button, App, Alert, Space, Tag, Popconfirm } from 'antd';
import { LockOutlined } from '@ant-design/icons';
import { getExitPasswordStatus, setExitPassword } from '../../services/settingsService';
import { useOrgId } from '../../hooks/useOrgId';

/**
 * Sets the password that unlocks a kiosk's lockdown, for every kiosk in the org,
 * without reinstalling. The password is stored encrypted server-side and is
 * never readable from the database — this panel can only set it or clear it.
 */
const KioskPasswordSettings = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [clearing, setClearing] = useState(false);
  const [configured, setConfigured] = useState(false);
  const { message } = App.useApp();
  const orgId = useOrgId();

  const refresh = useCallback(async () => {
    if (!orgId) return;
    setLoading(true);
    const res = await getExitPasswordStatus(orgId);
    if (res.success) setConfigured(res.configured);
    setLoading(false);
  }, [orgId]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const handleSave = async values => {
    if (!orgId) return;
    if (values.password !== values.confirm) {
      message.error('הסיסמאות אינן תואמות');
      return;
    }
    setSaving(true);
    const res = await setExitPassword(orgId, values.password);
    if (res.success) {
      message.success('סיסמת היציאה עודכנה. הקיוסקים יקבלו אותה מיד.');
      form.resetFields();
      await refresh();
    } else {
      message.error(res.error);
    }
    setSaving(false);
  };

  const handleClear = async () => {
    setClearing(true);
    const res = await setExitPassword(orgId, '');
    if (res.success) {
      message.success('הסיסמה המרוחקת הוסרה. הקיוסקים חוזרים לסיסמה שהוגדרה בהתקנה.');
      await refresh();
    } else {
      message.error(res.error);
    }
    setClearing(false);
  };

  return (
    <Space direction='vertical' size='middle' style={{ width: '100%', maxWidth: 520 }}>
      <Alert
        type='warning'
        showIcon
        icon={<LockOutlined />}
        message='סיסמה זו פותחת את נעילת הקיוסק. היא נשמרת מוצפנת בשרת ואינה נחשפת לאף משתמש — גם לא דרך מסד הנתונים.'
      />

      <div>
        סטטוס:{' '}
        {loading ? (
          <Tag>טוען…</Tag>
        ) : configured ? (
          <Tag color='green'>מוגדרת סיסמה מרוחקת</Tag>
        ) : (
          <Tag color='default'>משתמשים בסיסמה שהוגדרה בהתקנה</Tag>
        )}
      </div>

      <Form form={form} layout='vertical' onFinish={handleSave}>
        <Form.Item
          label='סיסמת יציאה חדשה'
          name='password'
          rules={[
            { required: true, message: 'נא להזין סיסמה' },
            { min: 4, message: 'לפחות 4 תווים' },
          ]}
        >
          <Input.Password prefix={<LockOutlined />} placeholder='לפחות 4 תווים' />
        </Form.Item>
        <Form.Item
          label='אישור סיסמה'
          name='confirm'
          rules={[{ required: true, message: 'נא לאשר את הסיסמה' }]}
        >
          <Input.Password prefix={<LockOutlined />} placeholder='הזן שוב' />
        </Form.Item>
        <Form.Item style={{ marginBottom: 0 }}>
          <Space>
            <Button type='primary' htmlType='submit' loading={saving}>
              שמור סיסמה
            </Button>
            {configured && (
              <Popconfirm
                title='להסיר את הסיסמה המרוחקת?'
                description='הקיוסקים יחזרו לסיסמה שהוגדרה בהתקנה.'
                onConfirm={handleClear}
                okText='הסר'
                cancelText='ביטול'
              >
                <Button danger loading={clearing}>
                  הסר סיסמה מרוחקת
                </Button>
              </Popconfirm>
            )}
          </Space>
        </Form.Item>
      </Form>
    </Space>
  );
};

export default KioskPasswordSettings;
