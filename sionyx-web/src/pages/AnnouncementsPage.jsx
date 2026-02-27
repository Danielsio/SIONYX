import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import {
  Card,
  Button,
  Space,
  Typography,
  Modal,
  Form,
  Input,
  Select,
  Switch,
  App,
  Tag,
  Row,
  Col,
  Empty,
  Skeleton,
  Tooltip,
  DatePicker,
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  ReloadOutlined,
  NotificationOutlined,
  CheckCircleOutlined,
  PauseCircleOutlined,
  InfoCircleOutlined,
  WarningOutlined,
  GiftOutlined,
  EyeOutlined,
  CloseOutlined,
} from '@ant-design/icons';
import { useOrgId } from '../hooks/useOrgId';
import {
  getAllAnnouncements,
  createAnnouncement,
  updateAnnouncement,
  deleteAnnouncement,
  toggleAnnouncementActive,
} from '../services/announcementService';
import dayjs from 'dayjs';
import { logger } from '../utils/logger';

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;

const containerVariants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.08 } },
};
const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.4, ease: [0.25, 0.46, 0.45, 0.94] },
  },
};

const TYPE_CONFIG = {
  info: {
    label: 'מידע',
    color: '#3B82F6',
    bg: '#EFF6FF',
    border: '#BFDBFE',
    icon: <InfoCircleOutlined />,
    tagColor: 'blue',
  },
  success: {
    label: 'הצלחה',
    color: '#10B981',
    bg: '#F0FDF4',
    border: '#BBF7D0',
    icon: <CheckCircleOutlined />,
    tagColor: 'green',
  },
  warning: {
    label: 'אזהרה',
    color: '#F59E0B',
    bg: '#FFFBEB',
    border: '#FDE68A',
    icon: <WarningOutlined />,
    tagColor: 'orange',
  },
  promotion: {
    label: 'מבצע',
    color: '#8B5CF6',
    bg: '#F5F3FF',
    border: '#DDD6FE',
    icon: <GiftOutlined />,
    tagColor: 'purple',
  },
};

const getScheduleStatus = item => {
  if (!item.active) return { tag: 'מושהה', color: 'default' };
  const now = dayjs();
  const start = item.startDate ? dayjs(item.startDate) : null;
  const end = item.endDate ? dayjs(item.endDate) : null;
  if (start && now.isBefore(start)) return { tag: 'מתוזמן', color: 'blue' };
  if (end && now.isAfter(end)) return { tag: 'פג תוקף', color: 'red' };
  return { tag: 'פעיל', color: 'green' };
};

const AnnouncementsPage = () => {
  const [announcements, setAnnouncements] = useState([]);
  const [loading, setLoading] = useState(true);
  const [toggling, setToggling] = useState({});
  const [formModalVisible, setFormModalVisible] = useState(false);
  const [viewModalVisible, setViewModalVisible] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [viewingItem, setViewingItem] = useState(null);
  const [form] = Form.useForm();
  const { message } = App.useApp();
  const orgId = useOrgId();

  useEffect(() => {
    loadAnnouncements();
  }, [orgId]);

  const loadAnnouncements = async () => {
    setLoading(true);
    if (!orgId) {
      message.error('מזהה ארגון לא נמצא. אנא התחבר שוב.');
      setLoading(false);
      return;
    }
    const result = await getAllAnnouncements(orgId);
    if (result.success) {
      setAnnouncements(result.announcements);
    } else {
      message.error(result.error || 'נכשל בטעינת הודעות מערכת');
    }
    setLoading(false);
  };

  const handleCreate = () => {
    setEditingItem(null);
    form.resetFields();
    form.setFieldsValue({ type: 'info', active: true, startDate: null, endDate: null });
    setFormModalVisible(true);
  };

  const handleEdit = item => {
    setEditingItem(item);
    form.setFieldsValue({
      title: item.title,
      body: item.body,
      type: item.type || 'info',
      active: item.active !== false,
      startDate: item.startDate ? dayjs(item.startDate) : null,
      endDate: item.endDate ? dayjs(item.endDate) : null,
    });
    setViewModalVisible(false);
    setFormModalVisible(true);
  };

  const handleDelete = async item => {
    if (!orgId) return;
    const result = await deleteAnnouncement(orgId, item.id);
    if (result.success) {
      message.success('ההודעה נמחקה בהצלחה');
      setAnnouncements(prev => prev.filter(a => a.id !== item.id));
      setViewModalVisible(false);
    } else {
      message.error(result.error || 'נכשל במחיקת ההודעה');
    }
  };

  const handleToggleActive = async item => {
    if (!orgId || toggling[item.id]) return;
    setToggling(prev => ({ ...prev, [item.id]: true }));
    const newActive = !item.active;
    try {
      const result = await toggleAnnouncementActive(orgId, item.id, newActive);
      if (result.success) {
        message.success(newActive ? 'ההודעה הופעלה' : 'ההודעה הושהתה');
        const updated = { ...item, active: newActive };
        setAnnouncements(prev => prev.map(a => (a.id === item.id ? updated : a)));
        if (viewingItem?.id === item.id) setViewingItem(updated);
      } else {
        message.error(result.error || 'נכשל בעדכון סטטוס');
      }
    } finally {
      setToggling(prev => ({ ...prev, [item.id]: false }));
    }
  };

  const handleFormSubmit = async () => {
    try {
      const values = await form.validateFields();
      if (!orgId) {
        message.error('מזהה ארגון לא נמצא.');
        return;
      }

      const payload = {
        ...values,
        startDate: values.startDate ? values.startDate.toISOString() : null,
        endDate: values.endDate ? values.endDate.toISOString() : null,
      };
      if (editingItem) {
        const result = await updateAnnouncement(orgId, editingItem.id, payload);
        if (result.success) {
          message.success('ההודעה עודכנה בהצלחה');
          setAnnouncements(prev =>
            prev.map(a =>
              a.id === editingItem.id ? { ...a, ...payload } : a
            )
          );
          setFormModalVisible(false);
        } else {
          message.error(result.error || 'נכשל בעדכון ההודעה');
        }
      } else {
        const result = await createAnnouncement(orgId, payload);
        if (result.success) {
          message.success('ההודעה נוצרה בהצלחה');
          await loadAnnouncements();
          setFormModalVisible(false);
        } else {
          message.error(result.error || 'נכשל ביצירת ההודעה');
        }
      }
    } catch (error) {
      logger.error('Validation failed:', error);
    }
  };

  const handleView = item => {
    setViewingItem(item);
    setViewModalVisible(true);
  };

  const confirmDelete = item => {
    Modal.confirm({
      title: 'מחק הודעה',
      content: `האם אתה בטוח שברצונך למחוק את "${item.title}"?`,
      okText: 'מחק',
      cancelText: 'ביטול',
      okType: 'danger',
      onOk: () => handleDelete(item),
    });
  };

  const activeCount = announcements.filter(a => a.active).length;

  return (
    <motion.div
      style={{ direction: 'rtl' }}
      variants={containerVariants}
      initial='hidden'
      animate='visible'
    >
      {/* Header */}
      <motion.div
        variants={itemVariants}
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: 12,
          marginBottom: 24,
        }}
      >
        <div>
          <Title level={2} style={{ margin: 0, display: 'flex', alignItems: 'center', gap: 12 }}>
            <NotificationOutlined />
            הודעות מערכת
          </Title>
          <Text type='secondary'>
            נהל הודעות גלובליות שיוצגו למשתמשים בקיוסק ({activeCount} פעילות)
          </Text>
        </div>
        <Space wrap>
          <Button icon={<ReloadOutlined />} onClick={loadAnnouncements} loading={loading}>
            רענן
          </Button>
          <Button type='primary' icon={<PlusOutlined />} onClick={handleCreate}>
            הודעה חדשה
          </Button>
        </Space>
      </motion.div>

      {/* Cards Grid */}
      {loading ? (
        <motion.div variants={itemVariants}>
          <Row gutter={[16, 16]}>
            {[1, 2, 3].map(i => (
              <Col key={i} xs={24} sm={12} lg={8}>
                <Card style={{ borderRadius: 16 }}>
                  <Skeleton active paragraph={{ rows: 4 }} />
                </Card>
              </Col>
            ))}
          </Row>
        </motion.div>
      ) : announcements.length === 0 ? (
        <motion.div variants={itemVariants}>
          <Card style={{ borderRadius: 16 }}>
            <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description='אין הודעות מערכת'>
              <Button type='primary' icon={<PlusOutlined />} onClick={handleCreate}>
                צור הודעה ראשונה
              </Button>
            </Empty>
          </Card>
        </motion.div>
      ) : (
        <motion.div variants={itemVariants}>
          <Row gutter={[16, 16]}>
            {announcements.map(item => {
              const config = TYPE_CONFIG[item.type] || TYPE_CONFIG.info;
              return (
                <Col key={item.id} xs={24} sm={12} lg={8}>
                  <Card
                    onClick={() => handleView(item)}
                    style={{
                      borderRadius: 16,
                      height: '100%',
                      cursor: 'pointer',
                      opacity: item.active ? 1 : 0.6,
                      borderColor: item.active ? config.border : '#e8ecf4',
                      borderWidth: 1.5,
                      transition: 'box-shadow 0.2s, transform 0.2s',
                    }}
                    styles={{ body: { padding: 0 } }}
                    onMouseEnter={e => {
                      e.currentTarget.style.boxShadow = '0 8px 24px rgba(0,0,0,0.1)';
                      e.currentTarget.style.transform = 'translateY(-2px)';
                    }}
                    onMouseLeave={e => {
                      e.currentTarget.style.boxShadow = 'none';
                      e.currentTarget.style.transform = 'translateY(0)';
                    }}
                  >
                    {/* Header */}
                    <div
                      style={{
                        background: config.bg,
                        borderBottom: `2px solid ${config.border}`,
                        padding: '14px 20px',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                      }}
                    >
                      <Space wrap>
                        <span style={{ fontSize: 20, color: config.color }}>{config.icon}</span>
                        <Tag color={config.tagColor}>{config.label}</Tag>
                        <Tag color={getScheduleStatus(item).color}>{getScheduleStatus(item).tag}</Tag>
                      </Space>
                      <Tooltip title={item.active ? 'פעיל' : 'מושהה'}>
                        <div
                          style={{
                            width: 10,
                            height: 10,
                            borderRadius: '50%',
                            background: item.active ? '#10b981' : '#94a3b8',
                            boxShadow: item.active ? '0 0 0 3px rgba(16,185,129,0.2)' : 'none',
                          }}
                        />
                      </Tooltip>
                    </div>

                    {/* Body */}
                    <div style={{ padding: '18px 20px 16px' }}>
                      <Title level={5} style={{ margin: '0 0 8px' }}>
                        {item.title}
                      </Title>
                      <Paragraph
                        type='secondary'
                        ellipsis={{ rows: 2 }}
                        style={{ margin: '0 0 12px', minHeight: 44 }}
                      >
                        {item.body || 'אין תוכן נוסף'}
                      </Paragraph>
                      <Text type='secondary' style={{ fontSize: 12 }}>
                        {item.createdAt ? dayjs(item.createdAt).format('DD/MM/YYYY HH:mm') : ''}
                      </Text>
                      {(item.startDate || item.endDate) && (
                        <div style={{ marginTop: 8, fontSize: 12, color: '#8c8c8c' }}>
                          {item.startDate && (
                            <span>מ־{dayjs(item.startDate).format('DD/MM/YYYY')}</span>
                          )}
                          {item.startDate && item.endDate && ' — '}
                          {item.endDate && (
                            <span>עד {dayjs(item.endDate).format('DD/MM/YYYY')}</span>
                          )}
                        </div>
                      )}
                    </div>
                  </Card>
                </Col>
              );
            })}
          </Row>
        </motion.div>
      )}

      {/* View/Detail Modal */}
      <Modal
        title={null}
        open={viewModalVisible}
        onCancel={() => setViewModalVisible(false)}
        footer={null}
        width={Math.min(520, window.innerWidth - 32)}
      >
        {viewingItem && (() => {
          const config = TYPE_CONFIG[viewingItem.type] || TYPE_CONFIG.info;
          return (
            <div style={{ direction: 'rtl' }}>
              {/* Type & Status */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16, flexWrap: 'wrap' }}>
                <span style={{ fontSize: 24, color: config.color }}>{config.icon}</span>
                <Tag color={config.tagColor} style={{ fontSize: 13 }}>{config.label}</Tag>
                <Tag color={getScheduleStatus(viewingItem).color} style={{ fontSize: 13 }}>
                  {getScheduleStatus(viewingItem).tag}
                </Tag>
              </div>

              {/* Title */}
              <Title level={3} style={{ margin: '0 0 12px' }}>
                {viewingItem.title}
              </Title>

              {/* Body */}
              <Paragraph style={{ fontSize: 15, lineHeight: 1.8, whiteSpace: 'pre-wrap', marginBottom: 16 }}>
                {viewingItem.body || 'אין תוכן נוסף'}
              </Paragraph>

              {/* Date & Schedule */}
              <div style={{ fontSize: 13, color: '#8c8c8c' }}>
                <div>נוצר: {viewingItem.createdAt ? dayjs(viewingItem.createdAt).format('DD/MM/YYYY HH:mm') : 'לא ידוע'}</div>
                {(viewingItem.startDate || viewingItem.endDate) && (
                  <div style={{ marginTop: 8 }}>
                    לוח זמנים: {viewingItem.startDate ? dayjs(viewingItem.startDate).format('DD/MM/YYYY') : 'ללא הגבלה'} — {viewingItem.endDate ? dayjs(viewingItem.endDate).format('DD/MM/YYYY') : 'ללא הגבלה'}
                  </div>
                )}
              </div>

              {/* Action Buttons */}
              <div
                style={{
                  display: 'flex',
                  gap: 8,
                  marginTop: 24,
                  paddingTop: 16,
                  borderTop: '1px solid #f0f0f0',
                  flexWrap: 'wrap',
                }}
              >
                <Button icon={<EditOutlined />} onClick={() => handleEdit(viewingItem)}>
                  ערוך
                </Button>
                <Button
                  icon={viewingItem.active ? <PauseCircleOutlined /> : <CheckCircleOutlined />}
                  onClick={() => handleToggleActive(viewingItem)}
                  loading={toggling[viewingItem?.id]}
                >
                  {viewingItem.active ? 'השהה' : 'הפעל'}
                </Button>
                <Button danger icon={<DeleteOutlined />} onClick={() => confirmDelete(viewingItem)}>
                  מחק
                </Button>
              </div>
            </div>
          );
        })()}
      </Modal>

      {/* Create/Edit Form Modal */}
      <Modal
        title={editingItem ? 'ערוך הודעה' : 'הודעת מערכת חדשה'}
        open={formModalVisible}
        onOk={handleFormSubmit}
        onCancel={() => setFormModalVisible(false)}
        okText={editingItem ? 'עדכן' : 'צור'}
        cancelText='ביטול'
        width={Math.min(560, window.innerWidth - 32)}
      >
        <Form form={form} layout='vertical' style={{ marginTop: 24 }}>
          <Form.Item
            name='title'
            label='כותרת'
            rules={[
              { required: true, message: 'אנא הזן כותרת' },
              { max: 200, message: 'כותרת עד 200 תווים' },
            ]}
          >
            <Input placeholder='למשל: מבצע חדש! 100₪ = 200₪ הדפסות' />
          </Form.Item>

          <Form.Item
            name='body'
            label='תוכן ההודעה'
            rules={[{ max: 1000, message: 'תוכן עד 1000 תווים' }]}
          >
            <TextArea
              rows={4}
              placeholder='פרטים נוספים על ההודעה...'
              showCount
              maxLength={1000}
            />
          </Form.Item>

          <Row gutter={16}>
            <Col xs={24} sm={12}>
              <Form.Item
                name='type'
                label='סוג הודעה'
                rules={[{ required: true, message: 'בחר סוג' }]}
              >
                <Select
                  options={Object.entries(TYPE_CONFIG).map(([value, cfg]) => ({
                    value,
                    label: (
                      <Space>
                        {cfg.icon}
                        {cfg.label}
                      </Space>
                    ),
                  }))}
                />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item name='active' label='סטטוס' valuePropName='checked'>
                <Switch checkedChildren='פעיל' unCheckedChildren='מושהה' />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col xs={24} sm={12}>
              <Form.Item name='startDate' label='תאריך התחלה'>
                <DatePicker style={{ width: '100%' }} format="DD/MM/YYYY" allowClear />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item name='endDate' label='תאריך סיום'>
                <DatePicker style={{ width: '100%' }} format="DD/MM/YYYY" allowClear />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>
    </motion.div>
  );
};

export default AnnouncementsPage;
