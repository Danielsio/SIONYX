import { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Input,
  Select,
  DatePicker,
  Space,
  Typography,
  Modal,
  Form,
  App,
  Tag,
  Tooltip,
  Badge,
  Row,
  Col,
  Statistic,
  Divider,
} from 'antd';
import {
  MessageOutlined,
  SendOutlined,
  UserOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  EyeOutlined,
  FilterOutlined,
  ClearOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { useAuthStore } from '../store/authStore';
import { getAllUsers } from '../services/userService';
import {
  getAllMessages,
  getMessagesForUser,
  sendMessage,
  isUserActive,
} from '../services/chatService';

const { Title, Text } = Typography;
const { TextArea } = Input;
const { RangePicker } = DatePicker;

const MessagesPage = () => {
  const [messages, setMessages] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [messageModalVisible, setMessageModalVisible] = useState(false);
  const [messageForm] = Form.useForm();
  const [filters, setFilters] = useState({
    user: null,
    dateRange: null,
    status: null,
  });
  const [stats, setStats] = useState({
    total: 0,
    unread: 0,
    today: 0,
  });

  const { user } = useAuthStore();
  const { message } = App.useApp();

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    loadMessages();
  }, [filters]);

  const loadData = async () => {
    setLoading(true);
    try {
      // Load users
      const usersResult = await getAllUsers(user.orgId);
      if (usersResult.success) {
        setUsers(usersResult.users);
      }

      // Load messages
      await loadMessages();
    } catch (error) {
      console.error('Error loading data:', error);
      message.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const loadMessages = async () => {
    try {
      let result;

      if (filters.user) {
        result = await getMessagesForUser(user.orgId, filters.user);
      } else {
        result = await getAllMessages(user.orgId);
      }

      if (result.success) {
        let filteredMessages = result.messages;

        // Apply date filter
        if (filters.dateRange && filters.dateRange.length === 2) {
          const [start, end] = filters.dateRange;
          filteredMessages = filteredMessages.filter(msg => {
            const msgDate = dayjs(msg.timestamp);
            return msgDate.isAfter(start.startOf('day')) && msgDate.isBefore(end.endOf('day'));
          });
        }

        // Apply status filter
        if (filters.status !== null) {
          filteredMessages = filteredMessages.filter(msg =>
            filters.status ? !msg.read : msg.read
          );
        }

        setMessages(filteredMessages);
        updateStats(filteredMessages);
      }
    } catch (error) {
      console.error('Error loading messages:', error);
      antMessage.error('Failed to load messages');
    }
  };

  const updateStats = messages => {
    const now = dayjs();
    const today = messages.filter(msg => dayjs(msg.timestamp).isSame(now, 'day'));

    setStats({
      total: messages.length,
      unread: messages.filter(msg => !msg.read).length,
      today: today.length,
    });
  };

  const handleSendMessage = async values => {
    try {
      const { toUserId, message: messageText } = values;

      const result = await sendMessage(user.orgId, toUserId, messageText, user.uid);

      if (result.success) {
        message.success('Message sent successfully');
        setMessageModalVisible(false);
        messageForm.resetFields();
        loadMessages();
      } else {
        message.error(result.error || 'Failed to send message');
      }
    } catch (error) {
      console.error('Error sending message:', error);
      message.error('Failed to send message');
    }
  };

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({
      ...prev,
      [key]: value,
    }));
  };

  const clearFilters = () => {
    setFilters({
      user: null,
      dateRange: null,
      status: null,
    });
  };

  const getUserName = userId => {
    const user = users.find(u => u.uid === userId);
    return user ? `${user.firstName} ${user.lastName}` : 'Unknown User';
  };

  const getUserPhone = userId => {
    const user = users.find(u => u.uid === userId);
    return user ? user.phoneNumber : 'Unknown';
  };

  const columns = [
    {
      title: 'משתמש',
      dataIndex: 'toUserId',
      key: 'user',
      render: userId => {
        const user = users.find(u => u.uid === userId);
        const isActive = user ? isUserActive(user.lastSeen) : false;

        return (
          <Space>
            <UserOutlined />
            <div>
              <div>{getUserName(userId)}</div>
              <Text type='secondary' style={{ fontSize: '12px' }}>
                {getUserPhone(userId)}
              </Text>
            </div>
            {isActive && (
              <Tag color='green' size='small'>
                פעיל
              </Tag>
            )}
          </Space>
        );
      },
    },
    {
      title: 'הודעה',
      dataIndex: 'message',
      key: 'message',
      ellipsis: true,
      render: text => (
        <Tooltip title={text}>
          <Text>{text}</Text>
        </Tooltip>
      ),
    },
    {
      title: 'סטטוס',
      dataIndex: 'read',
      key: 'status',
      render: (read, record) => (
        <Space>
          {read ? (
            <Tag color='green' icon={<CheckCircleOutlined />}>
              נקרא
            </Tag>
          ) : (
            <Tag color='orange' icon={<ClockCircleOutlined />}>
              לא נקרא
            </Tag>
          )}
          {read && record.readAt && (
            <Text type='secondary' style={{ fontSize: '12px' }}>
              {dayjs(record.readAt).format('HH:mm')}
            </Text>
          )}
        </Space>
      ),
    },
    {
      title: 'נשלח',
      dataIndex: 'timestamp',
      key: 'timestamp',
      render: timestamp => (
        <Space direction='vertical' size={0}>
          <Text>{dayjs(timestamp).format('DD/MM/YYYY')}</Text>
          <Text type='secondary' style={{ fontSize: '12px' }}>
            {dayjs(timestamp).format('HH:mm:ss')}
          </Text>
        </Space>
      ),
      sorter: (a, b) => dayjs(a.timestamp).unix() - dayjs(b.timestamp).unix(),
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      {/* Header */}
      <div style={{ marginBottom: '24px' }}>
        <Title level={2} style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '12px' }}>
          <MessageOutlined />
          הודעות
        </Title>
        <Text type='secondary'>שלח הודעות למשתמשים וצפה בהיסטוריית ההודעות</Text>
      </div>

      {/* Stats Cards */}
      <Row gutter={16} style={{ marginBottom: '24px' }}>
        <Col span={8}>
          <Card>
            <Statistic title='סך הכל הודעות' value={stats.total} prefix={<MessageOutlined />} />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title='הודעות לא נקראו'
              value={stats.unread}
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title='הודעות היום'
              value={stats.today}
              prefix={<SendOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Filters and Actions */}
      <Card style={{ marginBottom: '24px' }}>
        <Row gutter={16} align='middle'>
          <Col flex='auto'>
            <Space wrap>
              <Select
                placeholder='סנן לפי משתמש'
                style={{ width: 200 }}
                value={filters.user}
                onChange={value => handleFilterChange('user', value)}
                allowClear
              >
                {users.map(user => (
                  <Select.Option key={user.uid} value={user.uid}>
                    {user.firstName} {user.lastName} ({user.phoneNumber})
                  </Select.Option>
                ))}
              </Select>

              <RangePicker
                placeholder={['תאריך התחלה', 'תאריך סיום']}
                value={filters.dateRange}
                onChange={dates => handleFilterChange('dateRange', dates)}
              />

              <Select
                placeholder='סנן לפי סטטוס'
                style={{ width: 120 }}
                value={filters.status}
                onChange={value => handleFilterChange('status', value)}
                allowClear
              >
                <Select.Option value={true}>נקרא</Select.Option>
                <Select.Option value={false}>לא נקרא</Select.Option>
              </Select>

              <Button icon={<ClearOutlined />} onClick={clearFilters}>
                נקה מסננים
              </Button>
            </Space>
          </Col>

          <Col>
            <Button
              type='primary'
              icon={<SendOutlined />}
              onClick={() => setMessageModalVisible(true)}
            >
              שלח הודעה
            </Button>
          </Col>
        </Row>
      </Card>

      {/* Messages Table */}
      <Card>
        <Table
          columns={columns}
          dataSource={messages}
          rowKey='id'
          loading={loading}
          pagination={{
            pageSize: 20,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `${range[0]}-${range[1]} of ${total} messages`,
          }}
          scroll={{ x: 800 }}
        />
      </Card>

      {/* Send Message Modal */}
      <Modal
        title='שלח הודעה'
        open={messageModalVisible}
        onCancel={() => {
          setMessageModalVisible(false);
          messageForm.resetFields();
        }}
        footer={null}
        width={600}
        dir='rtl'
      >
        <Form form={messageForm} layout='vertical' onFinish={handleSendMessage} dir='rtl'>
          <Form.Item
            name='toUserId'
            label='שלח למשתמש'
            rules={[{ required: true, message: 'אנא בחר משתמש' }]}
          >
            <Select
              placeholder='בחר משתמש'
              showSearch
              filterOption={(input, option) =>
                option.children.toLowerCase().indexOf(input.toLowerCase()) >= 0
              }
              style={{ textAlign: 'right' }}
            >
              {users.map(user => (
                <Select.Option key={user.uid} value={user.uid}>
                  {user.firstName} {user.lastName} ({user.phoneNumber})
                </Select.Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name='message'
            label='הודעה'
            rules={[
              { required: true, message: 'אנא הכנס הודעה' },
              { max: 500, message: 'ההודעה חייבת להיות פחות מ-500 תווים' },
            ]}
          >
            <TextArea
              rows={4}
              placeholder='הכנס את ההודעה שלך כאן...'
              showCount
              maxLength={500}
              style={{ textAlign: 'right', direction: 'rtl' }}
            />
          </Form.Item>

          <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
            <Space>
              <Button onClick={() => setMessageModalVisible(false)}>ביטול</Button>
              <Button type='primary' htmlType='submit' icon={<SendOutlined />}>
                שלח הודעה
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default MessagesPage;
