import { useState, useEffect } from 'react';
import { Form, Input, Switch, Button, App, Alert, Space, Image, Typography } from 'antd';
import { PictureOutlined } from '@ant-design/icons';
import { getKioskBranding, updateKioskBranding } from '../../services/settingsService';
import { useOrgId } from '../../hooks/useOrgId';

const { Text } = Typography;

/**
 * Kiosk login-screen background. An admin pastes an image URL and toggles it on;
 * the kiosk shows it behind the login card and live-refreshes via kioskRefreshAt.
 * (Direct image upload needs scoped Storage rules — a follow-up; a URL works now.)
 */
const KioskDesignSettings = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [previewUrl, setPreviewUrl] = useState('');
  const { message } = App.useApp();
  const orgId = useOrgId();

  useEffect(() => {
    if (!orgId) return;
    setLoading(true);
    getKioskBranding(orgId).then(res => {
      if (res.success) {
        form.setFieldsValue({
          backgroundUrl: res.branding.backgroundUrl,
          backgroundEnabled: res.branding.backgroundEnabled,
        });
        setPreviewUrl(res.branding.backgroundUrl);
      }
      setLoading(false);
    });
  }, [orgId, form]);

  const handleSave = async values => {
    setSaving(true);
    const res = await updateKioskBranding(orgId, {
      backgroundUrl: values.backgroundUrl,
      backgroundEnabled: values.backgroundEnabled,
    });
    if (res.success) {
      message.success('העיצוב נשמר. הקיוסקים יתעדכנו בקרוב.');
      setPreviewUrl((values.backgroundUrl || '').trim());
    } else {
      message.error(res.error);
    }
    setSaving(false);
  };

  return (
    <Space direction='vertical' size='middle' style={{ width: '100%', maxWidth: 560 }}>
      <Alert
        type='info'
        showIcon
        icon={<PictureOutlined />}
        message='תמונת רקע למסך הכניסה של הקיוסק. הדבק כתובת תמונה (http/https) והפעל. הקיוסקים יתעדכנו אוטומטית.'
      />
      <Form form={form} layout='vertical' onFinish={handleSave} disabled={loading}>
        <Form.Item label='הצג רקע מותאם' name='backgroundEnabled' valuePropName='checked'>
          <Switch />
        </Form.Item>
        <Form.Item
          label='כתובת תמונת הרקע'
          name='backgroundUrl'
          rules={[
            {
              pattern: /^https?:\/\/.+/i,
              message: 'הכתובת חייבת להתחיל ב-http:// או https://',
            },
          ]}
        >
          <Input
            placeholder='https://example.com/background.jpg'
            onChange={e => setPreviewUrl(e.target.value.trim())}
            allowClear
          />
        </Form.Item>
        {previewUrl && /^https?:\/\/.+/i.test(previewUrl) && (
          <Form.Item label='תצוגה מקדימה'>
            <Image
              src={previewUrl}
              alt='תצוגה מקדימה של רקע הקיוסק'
              style={{ maxHeight: 180, borderRadius: 8, objectFit: 'cover' }}
              fallback='data:image/svg+xml;charset=UTF-8,%3Csvg xmlns="http://www.w3.org/2000/svg" width="200" height="120"%3E%3Crect width="200" height="120" fill="%23f0f0f0"/%3E%3Ctext x="100" y="60" text-anchor="middle" fill="%23999"%3Eno image%3C/text%3E%3C/svg%3E'
            />
            <div>
              <Text type='secondary' style={{ fontSize: 12 }}>
                אם התמונה לא נטענת כאן, גם הקיוסק לא יציג אותה.
              </Text>
            </div>
          </Form.Item>
        )}
        <Form.Item style={{ marginBottom: 0 }}>
          <Button type='primary' htmlType='submit' loading={saving}>
            שמור עיצוב
          </Button>
        </Form.Item>
      </Form>
    </Space>
  );
};

export default KioskDesignSettings;
