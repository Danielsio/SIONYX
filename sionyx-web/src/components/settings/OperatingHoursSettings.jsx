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
  Tag,
  Divider,
} from 'antd';
import {
  ClockCircleOutlined,
  SaveOutlined,
  ReloadOutlined,
  WarningOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import {
  getOperatingHours,
  updateOperatingHours,
  DEFAULT_OPERATING_HOURS,
  DAYS_OF_WEEK,
} from '../../services/settingsService';
import { useOrgId } from '../../hooks/useOrgId';
import { logger } from '../../utils/logger';

const { Text, Title } = Typography;

const DAY_COLORS = {
  sunday: '#3B82F6',
  monday: '#8B5CF6',
  tuesday: '#EC4899',
  wednesday: '#F59E0B',
  thursday: '#10B981',
  friday: '#F97316',
  saturday: '#6366F1',
};

const DayRow = ({ day, value, onChange, disabled }) => {
  const color = DAY_COLORS[day.key];
  const isOpen = value?.open ?? true;

  const handleToggle = checked => {
    onChange({ ...value, open: checked });
  };

  const handleTimeChange = (field, time) => {
    onChange({ ...value, [field]: time ? time.format('HH:mm') : value[field] });
  };

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        padding: '12px 16px',
        borderRadius: 12,
        background: disabled ? '#fafafa' : isOpen ? '#fafffe' : '#fafafa',
        border: `1px solid ${disabled ? '#f0f0f0' : isOpen ? '#e6f7f0' : '#f0f0f0'}`,
        gap: 12,
        flexWrap: 'wrap',
        opacity: disabled ? 0.5 : 1,
        transition: 'all 0.2s',
      }}
    >
      {/* Day label */}
      <div style={{ minWidth: 70, display: 'flex', alignItems: 'center', gap: 8 }}>
        <div
          style={{
            width: 8,
            height: 8,
            borderRadius: '50%',
            background: isOpen && !disabled ? color : '#d1d5db',
            flexShrink: 0,
          }}
        />
        <Text strong style={{ fontSize: 14 }}>{day.label}</Text>
      </div>

      {/* Open/Closed toggle */}
      <Switch
        size='small'
        checked={isOpen}
        onChange={handleToggle}
        disabled={disabled}
        checkedChildren='פתוח'
        unCheckedChildren='סגור'
      />

      {/* Time pickers */}
      {isOpen ? (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flex: 1, minWidth: 200 }}>
          <TimePicker
            format='HH:mm'
            value={dayjs(value?.startTime || '08:00', 'HH:mm')}
            onChange={t => handleTimeChange('startTime', t)}
            disabled={disabled}
            minuteStep={15}
            size='small'
            style={{ width: 90 }}
            placeholder='התחלה'
          />
          <Text type='secondary'>—</Text>
          <TimePicker
            format='HH:mm'
            value={dayjs(value?.endTime || '22:00', 'HH:mm')}
            onChange={t => handleTimeChange('endTime', t)}
            disabled={disabled}
            minuteStep={15}
            size='small'
            style={{ width: 90 }}
            placeholder='סיום'
          />
        </div>
      ) : (
        <Tag color='default' style={{ margin: 0 }}>
          <CloseCircleOutlined /> סגור
        </Tag>
      )}
    </div>
  );
};

const OperatingHoursSettings = () => {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [form] = Form.useForm();
  const [settings, setSettings] = useState({ ...DEFAULT_OPERATING_HOURS });
  const [schedule, setSchedule] = useState(DEFAULT_OPERATING_HOURS.schedule);
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
      const oh = result.operatingHours;
      setSettings(oh);
      setSchedule(oh.schedule);
      form.setFieldsValue({
        enabled: oh.enabled,
        gracePeriodMinutes: oh.gracePeriodMinutes,
        graceBehavior: oh.graceBehavior,
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
        message.error('מזהה ארגון לא נמצא.');
        return;
      }

      setSaving(true);

      const dataToSave = {
        enabled: values.enabled,
        gracePeriodMinutes: values.gracePeriodMinutes,
        graceBehavior: values.graceBehavior,
        schedule,
      };

      const result = await updateOperatingHours(orgId, dataToSave);

      if (result.success) {
        message.success('שעות הפעילות עודכנו בהצלחה');
        setSettings({ ...dataToSave, schedule });
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
    setSchedule(settings.schedule);
    form.setFieldsValue({
      enabled: settings.enabled,
      gracePeriodMinutes: settings.gracePeriodMinutes,
      graceBehavior: settings.graceBehavior,
    });
  };

  const handleDayChange = (dayKey, dayValue) => {
    setSchedule(prev => ({ ...prev, [dayKey]: dayValue }));
  };

  const openDaysCount = Object.values(schedule).filter(d => d.open).length;

  return (
    <Space direction='vertical' size='large' style={{ width: '100%' }}>
      <Alert
        message='הגדרות מפקח בלבד'
        description='הגדרות אלו קובעות מתי משתמשים יכולים להשתמש במערכת. שינויים משפיעים על כל המשתמשים בארגון.'
        type='warning'
        icon={<WarningOutlined />}
        showIcon
      />

      <Row gutter={[24, 24]}>
        {/* Left column: General settings */}
        <Col xs={24} lg={10}>
          <Card title='הגדרות כלליות' extra={<ClockCircleOutlined />}>
            <Form
              form={form}
              layout='vertical'
              initialValues={{
                enabled: settings.enabled,
                gracePeriodMinutes: settings.gracePeriodMinutes,
                graceBehavior: settings.graceBehavior,
              }}
            >
              <Form.Item name='enabled' label='הפעל הגבלת שעות פעילות' valuePropName='checked'>
                <Switch checkedChildren='מופעל' unCheckedChildren='מושבת' />
              </Form.Item>

              <Form.Item
                name='gracePeriodMinutes'
                label='זמן התראה לפני סגירה (דקות)'
                rules={[
                  { required: enabled, message: 'נא להזין זמן התראה' },
                  { type: 'number', min: 1, max: 30, message: '1-30 דקות' },
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
                        הזמן שנותר נשמר, המשתמש מתנתק בצורה מסודרת
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
            </Form>
          </Card>

          {/* Summary card */}
          {enabled && (
            <Card style={{ marginTop: 16 }}>
              <Space direction='vertical' size='small' style={{ width: '100%' }}>
                <Text strong>
                  <CheckCircleOutlined style={{ color: '#10B981', marginLeft: 6 }} />
                  סיכום
                </Text>
                <Text type='secondary'>
                  {openDaysCount} ימים פעילים מתוך 7
                </Text>
                {DAYS_OF_WEEK.map(day => {
                  const d = schedule[day.key];
                  return d?.open ? (
                    <div key={day.key} style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Text>{day.label}</Text>
                      <Text type='secondary'>{d.startTime} - {d.endTime}</Text>
                    </div>
                  ) : (
                    <div key={day.key} style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Text>{day.label}</Text>
                      <Text type='secondary' style={{ color: '#ef4444' }}>סגור</Text>
                    </div>
                  );
                })}
              </Space>
            </Card>
          )}
        </Col>

        {/* Right column: Weekly schedule */}
        <Col xs={24} lg={14}>
          <Card
            title={
              <Space>
                <ClockCircleOutlined />
                <span>לוח שעות שבועי</span>
                {enabled && (
                  <Tag color='blue'>{openDaysCount}/7 ימים פעילים</Tag>
                )}
              </Space>
            }
          >
            <Space direction='vertical' size={8} style={{ width: '100%' }}>
              {DAYS_OF_WEEK.map(day => (
                <DayRow
                  key={day.key}
                  day={day}
                  value={schedule[day.key]}
                  onChange={val => handleDayChange(day.key, val)}
                  disabled={!enabled}
                />
              ))}
            </Space>

            <Divider style={{ margin: '20px 0 16px' }} />

            <Space>
              <Button
                type='primary'
                icon={<SaveOutlined />}
                loading={saving}
                disabled={loading}
                onClick={handleSave}
              >
                שמור שינויים
              </Button>
              <Button onClick={handleReset} disabled={loading}>
                איפוס
              </Button>
              <Button icon={<ReloadOutlined />} onClick={loadSettings} loading={loading}>
                רענן
              </Button>
            </Space>
          </Card>
        </Col>
      </Row>
    </Space>
  );
};

export default OperatingHoursSettings;
