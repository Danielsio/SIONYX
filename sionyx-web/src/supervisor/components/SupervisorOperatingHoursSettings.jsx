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
  DEFAULT_OPERATING_HOURS,
  DAYS_OF_WEEK,
} from '../../services/settingsService';
import { getOrgOperatingHours, updateOrgOperatingHours } from '../services/supervisorSettingsService';

const { Text } = Typography;

const DEFAULT_DAY = { open: true, startTime: '08:00', endTime: '22:00' };
const DEFAULT_FRIDAY = { open: true, startTime: '08:00', endTime: '14:00' };
const DEFAULT_SATURDAY = { open: false, startTime: '00:00', endTime: '00:00' };

const buildSchedule = schedule => {
  const result = {};
  for (const day of DAYS_OF_WEEK) {
    const defaults =
      day.key === 'friday' ? DEFAULT_FRIDAY : day.key === 'saturday' ? DEFAULT_SATURDAY : DEFAULT_DAY;
    result[day.key] = { ...defaults, ...(schedule?.[day.key] || {}) };
  }
  return result;
};

const DAY_COLORS = {
  sunday: '#3B82F6',
  monday: '#8B5CF6',
  tuesday: '#EC4899',
  wednesday: '#F59E0B',
  thursday: '#10B981',
  friday: '#F97316',
  saturday: '#6366F1',
};

const DayRow = ({ day, value, onChange, disabled, compact }) => {
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
        alignItems: compact ? 'flex-start' : 'center',
        flexDirection: compact ? 'column' : 'row',
        padding: compact ? '10px 12px' : '12px 16px',
        borderRadius: 12,
        background: disabled ? '#fafafa' : isOpen ? '#fafffe' : '#fafafa',
        border: `1px solid ${disabled ? '#f0f0f0' : isOpen ? '#e6f7f0' : '#f0f0f0'}`,
        gap: compact ? 8 : 12,
        opacity: disabled ? 0.5 : 1,
        transition: 'all 0.2s',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, width: compact ? '100%' : undefined }}>
        <div
          style={{
            width: 8,
            height: 8,
            borderRadius: '50%',
            background: isOpen && !disabled ? color : '#d1d5db',
            flexShrink: 0,
          }}
        />
        <Text strong style={{ fontSize: 14, minWidth: compact ? undefined : 55 }}>{day.label}</Text>
        <Switch
          size='small'
          checked={isOpen}
          onChange={handleToggle}
          disabled={disabled}
          checkedChildren='פתוח'
          unCheckedChildren='סגור'
          style={{ marginRight: 'auto' }}
        />
      </div>
      {isOpen ? (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, width: compact ? '100%' : undefined }}>
          <TimePicker
            format='HH:mm'
            value={dayjs(value?.startTime || '08:00', 'HH:mm')}
            onChange={t => handleTimeChange('startTime', t)}
            disabled={disabled}
            minuteStep={15}
            size='small'
            style={{ flex: compact ? 1 : undefined, width: compact ? undefined : 90 }}
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
            style={{ flex: compact ? 1 : undefined, width: compact ? undefined : 90 }}
            placeholder='סיום'
          />
        </div>
      ) : (
        !compact && (
          <span style={{ color: '#999' }}>
            <CloseCircleOutlined /> סגור
          </span>
        )
      )}
    </div>
  );
};

const SupervisorOperatingHoursSettings = ({ orgId }) => {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [form] = Form.useForm();
  const [settings, setSettings] = useState({ ...DEFAULT_OPERATING_HOURS });
  const [schedule, setSchedule] = useState(DEFAULT_OPERATING_HOURS.schedule);
  const enabled = Form.useWatch('enabled', form);
  const [isMobile, setIsMobile] = useState(() => window.innerWidth < 768);

  const { message } = App.useApp();

  useEffect(() => {
    const mq = window.matchMedia('(max-width: 767px)');
    const handler = e => setIsMobile(e.matches);
    mq.addEventListener('change', handler);
    return () => mq.removeEventListener('change', handler);
  }, []);

  const loadSettings = async () => {
    if (!orgId) return;
    setLoading(true);
    const result = await getOrgOperatingHours(orgId);
    if (result.success) {
      const oh = result.operatingHours || {};
      const merged = {
        ...DEFAULT_OPERATING_HOURS,
        ...oh,
        schedule: buildSchedule(oh.schedule),
      };
      setSettings(merged);
      setSchedule(merged.schedule);
      form.setFieldsValue({
        enabled: merged.enabled,
        gracePeriodMinutes: merged.gracePeriodMinutes,
        graceBehavior: merged.graceBehavior,
      });
    } else {
      message.error(result.error || 'נכשל בטעינת ההגדרות');
    }
    setLoading(false);
  };

  useEffect(() => {
    if (orgId) loadSettings();
  }, [orgId]);

  const handleSave = async () => {
    if (!orgId) return;
    try {
      const values = await form.validateFields();
      setSaving(true);
      const dataToSave = {
        enabled: values.enabled,
        gracePeriodMinutes: values.gracePeriodMinutes,
        graceBehavior: values.graceBehavior,
        schedule,
      };
      const result = await updateOrgOperatingHours(orgId, dataToSave);
      if (result?.success !== false) {
        message.success('שעות הפעילות עודכנו בהצלחה');
        setSettings({ ...dataToSave, schedule });
      } else {
        message.error(result?.error || 'נכשל בעדכון ההגדרות');
      }
    } catch {
      // validation failed
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

  const openDaysCount = Object.values(schedule).filter(d => d?.open).length;

  return (
    <Space direction='vertical' size={isMobile ? 'middle' : 'large'} style={{ width: '100%' }}>
      <Alert
        message='הגדרות מפקח'
        description='הגדרות שעות פעילות לארגון. שינויים משפיעים על כל המשתמשים בארגון.'
        type='warning'
        icon={<WarningOutlined />}
        showIcon
      />
      <Row gutter={[isMobile ? 0 : 24, 16]}>
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
            {enabled && (
              <div style={{ marginTop: 16 }}>
                <Text strong>
                  <CheckCircleOutlined style={{ color: '#10B981', marginLeft: 6 }} />
                  סיכום
                </Text>
                <Text type='secondary' style={{ display: 'block', marginTop: 4 }}>
                  {openDaysCount} ימים פעילים מתוך 7
                </Text>
              </div>
            )}
          </Card>
        </Col>
        <Col xs={24} lg={14}>
          <Card
            title={
              <Space wrap>
                <ClockCircleOutlined />
                <span>לוח שעות שבועי</span>
                {enabled && <span style={{ color: '#1890ff' }}>{openDaysCount}/7</span>}
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
                  compact={isMobile}
                />
              ))}
            </Space>
            <Divider style={{ margin: '16px 0 12px' }} />
            <Space wrap>
              <Button type='primary' icon={<SaveOutlined />} loading={saving} disabled={loading} onClick={handleSave}>
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

export default SupervisorOperatingHoursSettings;
