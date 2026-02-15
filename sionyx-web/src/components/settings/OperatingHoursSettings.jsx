import { useEffect, useState } from 'react';
import {
  Card,
  Form,
  Switch,
  TimePicker,
  InputNumber,
  Radio,
  Button,
  Space,
  Typography,
  Row,
  Col,
  Alert,
  App,
  Descriptions,
  Tag,
} from 'antd';
import {
  ClockCircleOutlined,
  SaveOutlined,
  ReloadOutlined,
  InfoCircleOutlined,
  WarningOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { getOperatingHours, updateOperatingHours, DEFAULT_OPERATING_HOURS } from '../../services/settingsService';
import { useOrgId } from '../../hooks/useOrgId';
import { logger } from '../../utils/logger';

const { Text, Title } = Typography;

const OperatingHoursSettings = () => {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [form] = Form.useForm();
  const [settings, setSettings] = useState({ ...DEFAULT_OPERATING_HOURS });
  const enabled = Form.useWatch('enabled', form);

  const { message } = App.useApp();
  const orgId = useOrgId();

  useEffect(() => {
    loadSettings();
  }, [orgId]);

  const loadSettings = async () => {
    setLoading(true);

    if (!orgId) {
      message.error('מזהה ארגון לא נמצא. אנא התחבר שוב.');
      setLoading(false);
      return;
    }

    const result = await getOperatingHours(orgId);

    if (result.success) {
      setSettings(result.operatingHours);
      form.setFieldsValue({
        enabled: result.operatingHours.enabled,
        startTime: dayjs(result.operatingHours.startTime, 'HH:mm'),
        endTime: dayjs(result.operatingHours.endTime, 'HH:mm'),
        gracePeriodMinutes: result.operatingHours.gracePeriodMinutes,
        graceBehavior: result.operatingHours.graceBehavior,
      });
    } else {
      message.error(result.error || 'נכשל בטעינת ההגדרות');
    }

    setLoading(false);
  };

  const handleSave = async () => {
    try {
      const values = await form.validateFields();

      if (!orgId) {
        message.error('מזהה ארגון לא נמצא. אנא התחבר שוב.');
        return;
      }

      setSaving(true);

      const dataToSave = {
        enabled: values.enabled,
        startTime: values.startTime.format('HH:mm'),
        endTime: values.endTime.format('HH:mm'),
        gracePeriodMinutes: values.gracePeriodMinutes,
        graceBehavior: values.graceBehavior,
      };

      const result = await updateOperatingHours(orgId, dataToSave);

      if (result.success) {
        message.success('שעות הפעילות עודכנו בהצלחה');
        setSettings(dataToSave);
      } else {
        message.error(result.error || 'נכשל בעדכון ההגדרות');
      }
    } catch (error) {
      logger.error('Validation failed:', error);
    } finally {
      setSaving(false);
    }
  };

  const handleReset = () => {
    form.setFieldsValue({
      enabled: settings.enabled,
      startTime: dayjs(settings.startTime, 'HH:mm'),
      endTime: dayjs(settings.endTime, 'HH:mm'),
      gracePeriodMinutes: settings.gracePeriodMinutes,
      graceBehavior: settings.graceBehavior,
    });
  };

  return (
    <Space direction='vertical' size='large' style={{ width: '100%' }}>
      {/* Info Alert */}
      <Alert
        message='הגדרות מפקח בלבד'
        description='הגדרות אלו קובעות מתי משתמשים יכולים להשתמש במערכת. שינויים משפיעים על כל המשתמשים בארגון.'
        type='warning'
        icon={<WarningOutlined />}
        showIcon
      />

      <Row gutter={[24, 24]}>
        {/* Current Settings Overview */}
        <Col xs={24} lg={10}>
          <Card
            title='מצב נוכחי'
            extra={
              <Button icon={<ReloadOutlined />} onClick={loadSettings} loading={loading} size='small'>
                רענן
              </Button>
            }
          >
            <Descriptions column={1} size='small'>
              <Descriptions.Item label='סטטוס'>
                {settings.enabled ? (
                  <Tag color='green'>מופעל</Tag>
                ) : (
                  <Tag color='default'>מושבת</Tag>
                )}
              </Descriptions.Item>
              {settings.enabled && (
                <>
                  <Descriptions.Item label='שעות פעילות'>
                    {settings.startTime} - {settings.endTime}
                  </Descriptions.Item>
                  <Descriptions.Item label='זמן התראה'>
                    {settings.gracePeriodMinutes} דקות לפני סגירה
                  </Descriptions.Item>
                  <Descriptions.Item label='התנהגות בסיום'>
                    {settings.graceBehavior === 'graceful' ? 'סיום רגיל' : 'סגירה מיידית'}
                  </Descriptions.Item>
                </>
              )}
            </Descriptions>
          </Card>

          {/* Explanation Card */}
          <Card title='הסבר' style={{ marginTop: 16 }}>
            <Space direction='vertical' size='small'>
              <Text>
                <strong>שעות פעילות:</strong> בשעות אלו משתמשים יכולים להתחיל שימוש במחשב.
              </Text>
              <Text>
                <strong>זמן התראה:</strong> כמה דקות לפני סיום שעות הפעילות תוצג התראה למשתמשים.
              </Text>
              <Text>
                <strong>סיום רגיל:</strong> השימוש מסתיים בצורה מסודרת, הזמן נשמר.
              </Text>
              <Text>
                <strong>סגירה מיידית:</strong> תוכנות נסגרות באופן מיידי והמשתמש מתנתק.
              </Text>
            </Space>
          </Card>
        </Col>

        {/* Settings Form */}
        <Col xs={24} lg={14}>
          <Card title='עדכן הגדרות' extra={<ClockCircleOutlined />}>
            <Form
              form={form}
              layout='vertical'
              onFinish={handleSave}
              initialValues={{
                enabled: settings.enabled,
                startTime: dayjs(settings.startTime, 'HH:mm'),
                endTime: dayjs(settings.endTime, 'HH:mm'),
                gracePeriodMinutes: settings.gracePeriodMinutes,
                graceBehavior: settings.graceBehavior,
              }}
            >
              <Form.Item
                name='enabled'
                label='הפעל הגבלת שעות פעילות'
                valuePropName='checked'
              >
                <Switch checkedChildren='מופעל' unCheckedChildren='מושבת' />
              </Form.Item>

              <Row gutter={16}>
                <Col xs={24} sm={12}>
                  <Form.Item
                    name='startTime'
                    label='שעת התחלה'
                    rules={[{ required: enabled, message: 'נא לבחור שעת התחלה' }]}
                  >
                    <TimePicker
                      format='HH:mm'
                      style={{ width: '100%' }}
                      placeholder='06:00'
                      disabled={!enabled}
                      minuteStep={15}
                    />
                  </Form.Item>
                </Col>
                <Col xs={24} sm={12}>
                  <Form.Item
                    name='endTime'
                    label='שעת סיום'
                    rules={[{ required: enabled, message: 'נא לבחור שעת סיום' }]}
                  >
                    <TimePicker
                      format='HH:mm'
                      style={{ width: '100%' }}
                      placeholder='00:00'
                      disabled={!enabled}
                      minuteStep={15}
                    />
                  </Form.Item>
                </Col>
              </Row>

              <Form.Item
                name='gracePeriodMinutes'
                label='זמן התראה לפני סגירה (דקות)'
                rules={[
                  { required: enabled, message: 'נא להזין זמן התראה' },
                  { type: 'number', min: 1, max: 30, message: 'זמן התראה חייב להיות בין 1-30 דקות' },
                ]}
              >
                <InputNumber
                  style={{ width: '100%' }}
                  min={1}
                  max={30}
                  placeholder='5'
                  disabled={!enabled}
                  addonAfter='דקות'
                />
              </Form.Item>

              <Form.Item
                name='graceBehavior'
                label='התנהגות בסיום שעות הפעילות'
                rules={[{ required: enabled, message: 'נא לבחור התנהגות' }]}
              >
                <Radio.Group disabled={!enabled}>
                  <Space direction='vertical'>
                    <Radio value='graceful'>
                      <Text>סיום רגיל</Text>
                      <br />
                      <Text type='secondary' style={{ fontSize: 12 }}>
                        השימוש מסתיים בצורה מסודרת, הזמן שנותר נשמר
                      </Text>
                    </Radio>
                    <Radio value='force'>
                      <Text>סגירה מיידית</Text>
                      <br />
                      <Text type='secondary' style={{ fontSize: 12 }}>
                        כל התוכנות נסגרות והמשתמש מתנתק מיד
                      </Text>
                    </Radio>
                  </Space>
                </Radio.Group>
              </Form.Item>

              <Form.Item>
                <Space>
                  <Button
                    type='primary'
                    htmlType='submit'
                    icon={<SaveOutlined />}
                    loading={saving}
                    disabled={loading}
                  >
                    שמור שינויים
                  </Button>
                  <Button onClick={handleReset} disabled={loading}>
                    איפוס
                  </Button>
                </Space>
              </Form.Item>
            </Form>
          </Card>
        </Col>
      </Row>
    </Space>
  );
};

export default OperatingHoursSettings;
