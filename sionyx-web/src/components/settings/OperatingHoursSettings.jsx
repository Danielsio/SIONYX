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
          <Tag color='default' style={{ margin: 0 }}>
            <CloseCircleOutlined /> סגור
          </Tag>
        )
      )}
    </div>
  );
};

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

const OperatingHoursSettings = () => {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [form] = Form.useForm();
  const [settings, setSettings] = useState({ ...DEFAULT_OPERATING_HOURS });
  const [schedule, setSchedule] = useState(DEFAULT_OPERATING_HOURS.schedule);
  const enabled = Form.useWatch('enabled', form);
  const isMobile = useIsMobile();

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
    <Space direction='vertical' size={isMobile ? 'middle' : 'large'} style={{ width: '100%' }}>
      <Alert
        message='הגדרות מפקח בלבד'
        description='הגדרות אלו קובעות מתי משתמשים יכולים להשתמש במערכת. שינויים משפיעים על כל המשתמשים בארגון.'
        type='warning'
        icon={<WarningOutlined />}
        showIcon
        style={{ fontSize: isMobile ? 12 : undefined }}
      />

      <Row gutter={[isMobile ? 0 : 24, 16]}>
        <Col xs={24} lg={10}>
          <Card
            title='הגדרות כלליות'
            extra={<ClockCircleOutlined />}
            styles={{ body: { padding: isMobile ? 16 : undefined } }}
          >
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

          {enabled && (
            <Card
              style={{ marginTop: 16 }}
              styles={{ body: { padding: isMobile ? 12 : undefined } }}
            >
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
                  return (
                    <div key={day.key} style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Text style={{ fontSize: isMobile ? 13 : undefined }}>{day.label}</Text>
                      <Text
                        type='secondary'
                        style={{ color: d?.open ? undefined : '#ef4444', fontSize: isMobile ? 13 : undefined }}
                      >
                        {d?.open ? `${d.startTime} - ${d.endTime}` : 'סגור'}
                      </Text>
                    </div>
                  );
                })}
              </Space>
            </Card>
          )}
        </Col>

        <Col xs={24} lg={14}>
          <Card
            title={
              <Space size={isMobile ? 4 : 8} wrap>
                <ClockCircleOutlined />
                <span>לוח שעות שבועי</span>
                {enabled && (
                  <Tag color='blue' style={{ margin: 0 }}>{openDaysCount}/7</Tag>
                )}
              </Space>
            }
            styles={{ body: { padding: isMobile ? '12px 8px' : undefined } }}
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

            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
              <Button
                type='primary'
                icon={<SaveOutlined />}
                loading={saving}
                disabled={loading}
                onClick={handleSave}
                style={{ flex: isMobile ? '1 1 100%' : undefined }}
              >
                שמור שינויים
              </Button>
              <Button
                onClick={handleReset}
                disabled={loading}
                style={{ flex: isMobile ? 1 : undefined }}
              >
                איפוס
              </Button>
              <Button
                icon={<ReloadOutlined />}
                onClick={loadSettings}
                loading={loading}
                style={{ flex: isMobile ? 1 : undefined }}
              >
                רענן
              </Button>
            </div>
          </Card>
        </Col>
      </Row>
    </Space>
  );
};

export default OperatingHoursSettings;
