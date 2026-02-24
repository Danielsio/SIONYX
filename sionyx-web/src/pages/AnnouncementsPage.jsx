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
  Dropdown,
  Tooltip,
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  ReloadOutlined,
  NotificationOutlined,
  MoreOutlined,
  CheckCircleOutlined,
  PauseCircleOutlined,
  InfoCircleOutlined,
  WarningOutlined,
  GiftOutlined,
  SoundOutlined,
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

const AnnouncementsPage = () => {
  const [announcements, setAnnouncements] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
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
    form.setFieldsValue({ type: 'info', active: true });
    setModalVisible(true);
  };

  const handleEdit = item => {
    setEditingItem(item);
    form.setFieldsValue({
      title: item.title,
      body: item.body,
      type: item.type || 'info',
      active: item.active !== false,
    });
    setModalVisible(true);
  };

  const handleDelete = async item => {
    if (!orgId) return;
    const result = await deleteAnnouncement(orgId, item.id);
    if (result.success) {
      message.success('ההודעה נמחקה בהצלחה');
      setAnnouncements(prev => prev.filter(a => a.id !== item.id));
    } else {
      message.error(result.error || 'נכשל במחיקת ההודעה');
    }
  };

  const handleToggleActive = async item => {
    if (!orgId) return;
    const newActive = !item.active;
    const result = await toggleAnnouncementActive(orgId, item.id, newActive);
    if (result.success) {
      message.success(newActive ? 'ההודעה הופעלה' : 'ההודעה הושהתה');
      setAnnouncements(prev =>
        prev.map(a => (a.id === item.id ? { ...a, active: newActive } : a))
      );
    } else {
      message.error(result.error || 'נכשל בעדכון סטטוס');
    }
  };

  const handleModalOk = async () => {
    try {
      const values = await form.validateFields();
      if (!orgId) {
        message.error('מזהה ארגון לא נמצא.');
        return;
      }

      if (editingItem) {
        const result = await updateAnnouncement(orgId, editingItem.id, values);
        if (result.success) {
          message.success('ההודעה עודכנה בהצלחה');
          setAnnouncements(prev =>
            prev.map(a => (a.id === editingItem.id ? { ...a, ...values } : a))
          );
          setModalVisible(false);
        } else {
          message.error(result.error || 'נכשל בעדכון ההודעה');
        }
      } else {
        const result = await createAnnouncement(orgId, values);
        if (result.success) {
          message.success('ההודעה נוצרה בהצלחה');
          await loadAnnouncements();
          setModalVisible(false);
        } else {
          message.error(result.error || 'נכשל ביצירת ההודעה');
        }
      }
    } catch (error) {
      logger.error('Validation failed:', error);
    }
  };

  const activeCount = announcements.filter(a => a.active).length;

  const AnnouncementCard = ({ item }) => {
    console.log('[Announcements] rendering card:', item.title, 'id:', item.id);
    const config = TYPE_CONFIG[item.type] || TYPE_CONFIG.info;

    const menuItems = [
      { key: 'edit', icon: <EditOutlined />, label: 'ערוך' },
      {
        key: 'toggle',
        icon: item.active ? <PauseCircleOutlined /> : <CheckCircleOutlined />,
        label: item.active ? 'השהה' : 'הפעל',
      },
      { type: 'divider' },
      { key: 'delete', icon: <DeleteOutlined />, label: 'מחק', danger: true },
    ];

    const onMenuClick = ({ key }) => {
      console.log('[Announcements] menu clicked, key:', key, 'item:', item.title);
      if (key === 'edit') handleEdit(item);
      else if (key === 'toggle') handleToggleActive(item);
      else if (key === 'delete') {
        Modal.confirm({
          title: 'מחק הודעה',
          content: `האם אתה בטוח שברצונך למחוק את "${item.title}"?`,
          okText: 'מחק',
          cancelText: 'ביטול',
          okType: 'danger',
          onOk: () => handleDelete(item),
        });
      }
    };

    const onOpenChange = (open) => {
      console.log('[Announcements] dropdown openChange:', open, 'item:', item.title);
    };

    return (
      <Card
        hoverable
        style={{
          borderRadius: 16,
          height: '100%',
          opacity: item.active ? 1 : 0.6,
          borderColor: item.active ? config.border : '#e8ecf4',
          borderWidth: 1.5,
        }}
        styles={{ body: { padding: 0 } }}
      >
        {/* Header bar */}
        <div
          style={{
            background: config.bg,
            borderBottom: `2px solid ${config.border}`,
            padding: '16px 20px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <Space>
            <span style={{ fontSize: 22 }}>{config.icon}</span>
            <Tag color={config.tagColor}>{config.label}</Tag>
            {!item.active && <Tag color='default'>מושהה</Tag>}
          </Space>
          <Dropdown
            menu={{ items: menuItems, onClick: onMenuClick }}
            trigger={['click']}
            onOpenChange={onOpenChange}
          >
            <Button
              type='text'
              icon={<MoreOutlined />}
              size='small'
              style={{ color: config.color }}
              onClick={(e) => {
                console.log('[Announcements] button clicked for:', item.title);
                e.stopPropagation();
              }}
            />
          </Dropdown>
        </div>

        {/* Body */}
        <div style={{ padding: '20px 20px 16px' }}>
          <Title level={5} style={{ margin: '0 0 8px' }}>
            {item.title}
          </Title>
          <Paragraph
            type='secondary'
            ellipsis={{ rows: 3 }}
            style={{ margin: '0 0 16px', minHeight: 60 }}
          >
            {item.body || 'אין תוכן נוסף'}
          </Paragraph>
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              borderTop: '1px solid #f0f0f0',
              paddingTop: 12,
            }}
          >
            <Text type='secondary' style={{ fontSize: 12 }}>
              {item.createdAt ? dayjs(item.createdAt).format('DD/MM/YYYY HH:mm') : ''}
            </Text>
            <Tooltip title={item.active ? 'פעיל - מוצג בקיוסק' : 'מושהה - לא מוצג'}>
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
        </div>
      </Card>
    );
  };

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

      {/* Grid */}
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
            <Empty
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              description='אין הודעות מערכת'
            >
              <Button type='primary' icon={<PlusOutlined />} onClick={handleCreate}>
                צור הודעה ראשונה
              </Button>
            </Empty>
          </Card>
        </motion.div>
      ) : (
        <motion.div variants={itemVariants}>
          <Row gutter={[16, 16]}>
            {announcements.map(item => (
              <Col key={item.id} xs={24} sm={12} lg={8}>
                <AnnouncementCard item={item} />
              </Col>
            ))}
          </Row>
        </motion.div>
      )}

      {/* Create/Edit Modal */}
      <Modal
        title={editingItem ? 'ערוך הודעה' : 'הודעת מערכת חדשה'}
        open={modalVisible}
        onOk={handleModalOk}
        onCancel={() => setModalVisible(false)}
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
        </Form>
      </Modal>
    </motion.div>
  );
};

export default AnnouncementsPage;
