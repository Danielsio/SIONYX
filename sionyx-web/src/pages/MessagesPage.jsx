import { useState, useEffect, useRef } from 'react';
import {
  Card,
  Button,
  Input,
  Space,
  Typography,
  App,
  Tag,
  Badge,
  Row,
  Col,
  Avatar,
  Drawer,
  Empty,
  Spin,
  Divider,
} from 'antd';
import {
  MessageOutlined,
  SendOutlined,
  UserOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  SearchOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import 'dayjs/locale/he';
import { useAuthStore } from '../store/authStore';
import { getAllUsers } from '../services/userService';
import {
  getAllMessages,
  getMessagesForUser,
  sendMessage,
  isUserActive,
} from '../services/chatService';

dayjs.extend(relativeTime);
dayjs.locale('he');

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;

const MessagesPage = () => {
  const [messages, setMessages] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchText, setSearchText] = useState('');
  const [selectedUser, setSelectedUser] = useState(null);
  const [chatVisible, setChatVisible] = useState(false);
  const [userMessages, setUserMessages] = useState([]);
  const [loadingChat, setLoadingChat] = useState(false);
  const [newMessage, setNewMessage] = useState('');
  const [sending, setSending] = useState(false);
  const chatEndRef = useRef(null);

  const { user } = useAuthStore();
  const { message } = App.useApp();

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    if (chatVisible && chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [userMessages, chatVisible]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [usersResult, messagesResult] = await Promise.all([
        getAllUsers(user.orgId),
        getAllMessages(user.orgId),
      ]);

      if (usersResult.success) {
        setUsers(usersResult.users);
      }
      if (messagesResult.success) {
        setMessages(messagesResult.messages);
      }
    } catch (error) {
      console.error('Error loading data:', error);
      message.error('שגיאה בטעינת הנתונים');
    } finally {
      setLoading(false);
    }
  };

  const openChat = async userItem => {
    setSelectedUser(userItem);
    setChatVisible(true);
    setLoadingChat(true);

    try {
      const result = await getMessagesForUser(user.orgId, userItem.uid);
      if (result.success) {
        // Sort messages by timestamp (oldest first for chat display)
        const sorted = [...result.messages].sort(
          (a, b) => dayjs(a.timestamp).unix() - dayjs(b.timestamp).unix()
        );
        setUserMessages(sorted);
      }
    } catch (error) {
      console.error('Error loading chat:', error);
      message.error('שגיאה בטעינת ההודעות');
    } finally {
      setLoadingChat(false);
    }
  };

  const handleSendMessage = async () => {
    if (!newMessage.trim() || !selectedUser) return;

    setSending(true);
    try {
      const result = await sendMessage(user.orgId, selectedUser.uid, newMessage.trim(), user.uid);
      if (result.success) {
        setNewMessage('');
        // Reload messages for this user
        const msgResult = await getMessagesForUser(user.orgId, selectedUser.uid);
        if (msgResult.success) {
          const sorted = [...msgResult.messages].sort(
            (a, b) => dayjs(a.timestamp).unix() - dayjs(b.timestamp).unix()
          );
          setUserMessages(sorted);
        }
        // Also reload all messages for the list
        loadData();
        message.success('הודעה נשלחה');
      } else {
        message.error('שגיאה בשליחה');
      }
    } catch (error) {
      console.error('Error sending:', error);
      message.error('שגיאה בשליחה');
    } finally {
      setSending(false);
    }
  };

  // Get user conversation summaries
  const getUserConversations = () => {
    const userMap = new Map();

    // Group messages by user
    messages.forEach(msg => {
      const userId = msg.toUserId;
      if (!userMap.has(userId)) {
        userMap.set(userId, {
          userId,
          messages: [],
          unreadCount: 0,
          latestMessage: null,
          latestTimestamp: null,
        });
      }
      const userData = userMap.get(userId);
      userData.messages.push(msg);
      if (!msg.read) userData.unreadCount++;
      
      const msgTime = dayjs(msg.timestamp);
      if (!userData.latestTimestamp || msgTime.isAfter(userData.latestTimestamp)) {
        userData.latestTimestamp = msgTime;
        userData.latestMessage = msg.message;
      }
    });

    // Convert to array and add user details
    return Array.from(userMap.values())
      .map(conv => {
        const userInfo = users.find(u => u.uid === conv.userId);
        return {
          ...conv,
          userName: userInfo ? `${userInfo.firstName} ${userInfo.lastName}` : 'משתמש לא ידוע',
          userPhone: userInfo?.phoneNumber || '',
          isActive: userInfo ? isUserActive(userInfo.lastSeen) : false,
          userInfo,
        };
      })
      .sort((a, b) => (b.latestTimestamp?.unix() || 0) - (a.latestTimestamp?.unix() || 0));
  };

  const conversations = getUserConversations();
  const totalUnread = conversations.reduce((sum, c) => sum + c.unreadCount, 0);

  // Filter conversations by search
  const filteredConversations = conversations.filter(conv =>
    conv.userName.toLowerCase().includes(searchText.toLowerCase()) ||
    conv.userPhone.includes(searchText)
  );

  // Users without messages (for quick access)
  const usersWithoutMessages = users.filter(
    u => !conversations.find(c => c.userId === u.uid)
  );

  const ConversationCard = ({ conv }) => (
    <Card
      hoverable
      onClick={() => conv.userInfo && openChat(conv.userInfo)}
      style={{
        borderRadius: 12,
        marginBottom: 12,
        cursor: 'pointer',
        borderRight: conv.unreadCount > 0 ? '4px solid #1890ff' : 'none',
      }}
      styles={{ body: { padding: 16 } }}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12 }}>
        <Badge count={conv.unreadCount} offset={[-4, 4]}>
          <Avatar
            size={48}
            style={{
              background: conv.isActive
                ? 'linear-gradient(135deg, #52c41a, #73d13d)'
                : 'linear-gradient(135deg, #667eea, #764ba2)',
            }}
            icon={<UserOutlined />}
          />
        </Badge>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Text strong style={{ fontSize: 15 }}>
              {conv.userName}
            </Text>
            <Text type='secondary' style={{ fontSize: 11 }}>
              {conv.latestTimestamp?.fromNow()}
            </Text>
          </div>
          <Text type='secondary' style={{ fontSize: 12 }}>
            {conv.userPhone}
          </Text>
          <Paragraph
            ellipsis={{ rows: 1 }}
            style={{ margin: '4px 0 0', fontSize: 13, color: '#666' }}
          >
            {conv.latestMessage || 'אין הודעות'}
          </Paragraph>
        </div>
      </div>
    </Card>
  );

  const UserQuickCard = ({ userItem }) => (
    <Card
      hoverable
      size='small'
      onClick={() => openChat(userItem)}
      style={{ borderRadius: 8, textAlign: 'center' }}
      styles={{ body: { padding: 12 } }}
    >
      <Avatar
        size={40}
        style={{
          background: isUserActive(userItem.lastSeen)
            ? 'linear-gradient(135deg, #52c41a, #73d13d)'
            : '#d9d9d9',
        }}
        icon={<UserOutlined />}
      />
      <div style={{ marginTop: 8 }}>
        <Text strong style={{ fontSize: 12, display: 'block' }} ellipsis>
          {userItem.firstName}
        </Text>
      </div>
    </Card>
  );

  return (
    <div style={{ direction: 'rtl' }}>
      {/* Header */}
      <div
        className='page-header'
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: 12,
          marginBottom: 20,
        }}
      >
        <div>
          <Title level={2} style={{ margin: 0, display: 'flex', alignItems: 'center', gap: 12 }}>
            <MessageOutlined />
            הודעות
            {totalUnread > 0 && (
              <Badge count={totalUnread} style={{ marginRight: 8 }} />
            )}
          </Title>
          <Text type='secondary'>שלח הודעות למשתמשים וצפה בשיחות</Text>
        </div>
        <Button icon={<ReloadOutlined />} onClick={loadData} loading={loading}>
          רענן
        </Button>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: 60 }}>
          <Spin size='large' />
        </div>
      ) : (
        <Row gutter={[16, 16]}>
          {/* Main Conversations List */}
          <Col xs={24} lg={16}>
            <Card
              title={
                <Space>
                  <MessageOutlined />
                  <span>שיחות ({conversations.length})</span>
                </Space>
              }
              extra={
                <Input
                  placeholder='חפש משתמש...'
                  prefix={<SearchOutlined />}
                  value={searchText}
                  onChange={e => setSearchText(e.target.value)}
                  style={{ width: 180 }}
                  allowClear
                />
              }
              styles={{ body: { padding: 16, maxHeight: 'calc(100vh - 280px)', overflowY: 'auto' } }}
            >
              {filteredConversations.length === 0 ? (
                <Empty description='אין שיחות' image={Empty.PRESENTED_IMAGE_SIMPLE} />
              ) : (
                filteredConversations.map(conv => (
                  <ConversationCard key={conv.userId} conv={conv} />
                ))
              )}
            </Card>
          </Col>

          {/* Quick Access to Users */}
          <Col xs={24} lg={8}>
            <Card
              title={
                <Space>
                  <UserOutlined />
                  <span>שלח הודעה חדשה</span>
                </Space>
              }
              styles={{ body: { padding: 12 } }}
            >
              {usersWithoutMessages.length === 0 && conversations.length === 0 ? (
                <Empty description='אין משתמשים' image={Empty.PRESENTED_IMAGE_SIMPLE} />
              ) : (
                <Row gutter={[8, 8]}>
                  {users.slice(0, 12).map(userItem => (
                    <Col key={userItem.uid} span={8}>
                      <UserQuickCard userItem={userItem} />
                    </Col>
                  ))}
                </Row>
              )}
            </Card>

            {/* Stats Card */}
            <Card style={{ marginTop: 16 }}>
              <Row gutter={16}>
                <Col span={8} style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: 24, fontWeight: 'bold', color: '#1890ff' }}>
                    {messages.length}
                  </div>
                  <Text type='secondary' style={{ fontSize: 12 }}>סך הכל</Text>
                </Col>
                <Col span={8} style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: 24, fontWeight: 'bold', color: '#faad14' }}>
                    {totalUnread}
                  </div>
                  <Text type='secondary' style={{ fontSize: 12 }}>לא נקראו</Text>
                </Col>
                <Col span={8} style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: 24, fontWeight: 'bold', color: '#52c41a' }}>
                    {conversations.length}
                  </div>
                  <Text type='secondary' style={{ fontSize: 12 }}>שיחות</Text>
                </Col>
              </Row>
            </Card>
          </Col>
        </Row>
      )}

      {/* Chat Drawer */}
      <Drawer
        title={
          selectedUser && (
            <Space>
              <Avatar
                style={{
                  background: isUserActive(selectedUser.lastSeen)
                    ? 'linear-gradient(135deg, #52c41a, #73d13d)'
                    : 'linear-gradient(135deg, #667eea, #764ba2)',
                }}
                icon={<UserOutlined />}
              />
              <div>
                <div style={{ fontWeight: 'bold' }}>
                  {selectedUser.firstName} {selectedUser.lastName}
                </div>
                <Text type='secondary' style={{ fontSize: 12 }}>
                  {selectedUser.phoneNumber}
                  {isUserActive(selectedUser.lastSeen) && (
                    <Tag color='green' style={{ marginRight: 8 }}>מחובר</Tag>
                  )}
                </Text>
              </div>
            </Space>
          )
        }
        placement='left'
        width={Math.min(450, window.innerWidth - 20)}
        onClose={() => {
          setChatVisible(false);
          setSelectedUser(null);
          setUserMessages([]);
        }}
        open={chatVisible}
        styles={{
          body: {
            padding: 0,
            display: 'flex',
            flexDirection: 'column',
            height: 'calc(100% - 55px)',
          },
        }}
      >
        {/* Messages Area */}
        <div
          style={{
            flex: 1,
            overflowY: 'auto',
            padding: 16,
            background: '#f5f5f5',
          }}
        >
          {loadingChat ? (
            <div style={{ textAlign: 'center', padding: 40 }}>
              <Spin />
            </div>
          ) : userMessages.length === 0 ? (
            <Empty
              description='אין הודעות עדיין'
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              style={{ marginTop: 40 }}
            />
          ) : (
            <>
              {userMessages.map((msg, index) => {
                const showDate =
                  index === 0 ||
                  !dayjs(msg.timestamp).isSame(dayjs(userMessages[index - 1].timestamp), 'day');

                return (
                  <div key={msg.id}>
                    {showDate && (
                      <Divider style={{ fontSize: 11, color: '#999' }}>
                        {dayjs(msg.timestamp).format('DD MMMM YYYY')}
                      </Divider>
                    )}
                    <div
                      style={{
                        display: 'flex',
                        justifyContent: 'flex-start',
                        marginBottom: 12,
                      }}
                    >
                      <div
                        style={{
                          maxWidth: '80%',
                          background: 'linear-gradient(135deg, #667eea, #764ba2)',
                          color: '#fff',
                          padding: '10px 14px',
                          borderRadius: '16px 16px 4px 16px',
                          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                        }}
                      >
                        <div style={{ fontSize: 14, lineHeight: 1.5 }}>{msg.message}</div>
                        <div
                          style={{
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'flex-end',
                            gap: 4,
                            marginTop: 4,
                            fontSize: 10,
                            opacity: 0.8,
                          }}
                        >
                          <span>{dayjs(msg.timestamp).format('HH:mm')}</span>
                          {msg.read ? (
                            <CheckCircleOutlined style={{ color: '#73d13d' }} />
                          ) : (
                            <ClockCircleOutlined />
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
              <div ref={chatEndRef} />
            </>
          )}
        </div>

        {/* Message Input */}
        <div
          style={{
            padding: 12,
            borderTop: '1px solid #f0f0f0',
            background: '#fff',
          }}
        >
          <Space.Compact style={{ width: '100%' }}>
            <TextArea
              value={newMessage}
              onChange={e => setNewMessage(e.target.value)}
              placeholder='הקלד הודעה...'
              autoSize={{ minRows: 1, maxRows: 4 }}
              onPressEnter={e => {
                if (!e.shiftKey) {
                  e.preventDefault();
                  handleSendMessage();
                }
              }}
              style={{
                borderRadius: '20px 0 0 20px',
                resize: 'none',
              }}
            />
            <Button
              type='primary'
              icon={<SendOutlined />}
              onClick={handleSendMessage}
              loading={sending}
              disabled={!newMessage.trim()}
              style={{
                borderRadius: '0 20px 20px 0',
                height: 'auto',
                minHeight: 40,
              }}
            />
          </Space.Compact>
        </div>
      </Drawer>
    </div>
  );
};

export default MessagesPage;
