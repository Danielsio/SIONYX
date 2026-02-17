import { useState, useEffect, useRef } from 'react';
import {
  Card,
  Button,
  Input,
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
  Tooltip,
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
  cleanupOldMessages,
} from '../services/chatService';
import { logger } from '../utils/logger';

dayjs.extend(relativeTime);
dayjs.locale('he');

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;

// ── Design tokens ──────────────────────────────────────────
const tokens = {
  primary: '#667eea',
  primaryDark: '#5a6fd6',
  gradientPrimary: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
  gradientGreen: 'linear-gradient(135deg, #52c41a, #73d13d)',
  bubbleBg: '#f0f2ff',
  chatBg: '#fafbfc',
  surfaceBorder: '#eef0f4',
  textPrimary: '#1a1a2e',
  textSecondary: '#8492a6',
  radius: 14,
  radiusSm: 10,
};

// ── MessagesPage ───────────────────────────────────────────
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
    if (user?.orgId) {
      cleanupOldMessages(user.orgId).catch(() => {});
    }
  }, []);

  useEffect(() => {
    if (chatVisible && chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [userMessages, chatVisible]);

  const loadData = async () => {
    if (!user?.orgId) return;
    setLoading(true);
    try {
      const [usersResult, messagesResult] = await Promise.all([
        getAllUsers(user.orgId),
        getAllMessages(user.orgId),
      ]);

      if (usersResult.success) setUsers(usersResult.users);
      if (messagesResult.success) setMessages(messagesResult.messages);
    } catch (error) {
      logger.error('Error loading data:', error);
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
        const sorted = [...result.messages].sort(
          (a, b) => dayjs(a.timestamp).unix() - dayjs(b.timestamp).unix()
        );
        setUserMessages(sorted);
      }
    } catch (error) {
      logger.error('Error loading chat:', error);
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
        const msgResult = await getMessagesForUser(user.orgId, selectedUser.uid);
        if (msgResult.success) {
          const sorted = [...msgResult.messages].sort(
            (a, b) => dayjs(a.timestamp).unix() - dayjs(b.timestamp).unix()
          );
          setUserMessages(sorted);
        }
        loadData();
        message.success('הודעה נשלחה');
      } else {
        message.error('שגיאה בשליחה');
      }
    } catch (error) {
      logger.error('Error sending:', error);
      message.error('שגיאה בשליחה');
    } finally {
      setSending(false);
    }
  };

  // ── Conversation summaries ─────────────────────────────
  const getUserConversations = () => {
    const userMap = new Map();
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

  const filteredConversations = conversations.filter(
    conv =>
      conv.userName.toLowerCase().includes(searchText.toLowerCase()) ||
      conv.userPhone.includes(searchText)
  );

  const usersWithoutMessages = users.filter(u => !conversations.find(c => c.userId === u.uid));

  // ── Helper: get user initials ──────────────────────────
  const getInitials = name => {
    if (!name) return '?';
    const parts = name.trim().split(' ');
    return parts.length >= 2 ? `${parts[0][0]}${parts[1][0]}` : parts[0][0];
  };

  // ── Conversation list item ─────────────────────────────
  const ConversationCard = ({ conv }) => (
    <div
      role="button"
      tabIndex={0}
      onClick={() => conv.userInfo && openChat(conv.userInfo)}
      onKeyDown={e => e.key === 'Enter' && conv.userInfo && openChat(conv.userInfo)}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 14,
        padding: '14px 18px',
        borderRadius: tokens.radiusSm,
        cursor: 'pointer',
        transition: 'background 0.2s',
        borderBottom: `1px solid ${tokens.surfaceBorder}`,
        background: conv.unreadCount > 0 ? 'rgba(102, 126, 234, 0.04)' : 'transparent',
      }}
      onMouseEnter={e => (e.currentTarget.style.background = 'rgba(102, 126, 234, 0.06)')}
      onMouseLeave={e =>
        (e.currentTarget.style.background =
          conv.unreadCount > 0 ? 'rgba(102, 126, 234, 0.04)' : 'transparent')
      }
    >
      {/* Avatar */}
      <Badge count={conv.unreadCount} size="small" offset={[-2, 2]}>
        <Avatar
          size={46}
          style={{
            background: conv.isActive ? tokens.gradientGreen : tokens.gradientPrimary,
            fontSize: 16,
            fontWeight: 600,
          }}
        >
          {getInitials(conv.userName)}
        </Avatar>
      </Badge>

      {/* Content */}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'baseline',
            marginBottom: 2,
          }}
        >
          <Text
            strong={conv.unreadCount > 0}
            style={{
              fontSize: 14,
              color: tokens.textPrimary,
              fontWeight: conv.unreadCount > 0 ? 600 : 500,
            }}
          >
            {conv.userName}
          </Text>
          <Text style={{ fontSize: 11, color: tokens.textSecondary, flexShrink: 0, marginRight: 8 }}>
            {conv.latestTimestamp?.fromNow()}
          </Text>
        </div>
        <Paragraph
          ellipsis={{ rows: 1 }}
          style={{
            margin: 0,
            fontSize: 13,
            color: conv.unreadCount > 0 ? tokens.textPrimary : tokens.textSecondary,
            fontWeight: conv.unreadCount > 0 ? 500 : 400,
            lineHeight: 1.4,
          }}
        >
          {conv.latestMessage || 'אין הודעות'}
        </Paragraph>
      </div>
    </div>
  );

  // ── Quick user avatar card ─────────────────────────────
  const UserQuickCard = ({ userItem }) => {
    const active = isUserActive(userItem.lastSeen);
    const name = `${userItem.firstName} ${userItem.lastName || ''}`.trim();

    return (
      <Tooltip title={name} placement="top">
        <div
          role="button"
          tabIndex={0}
          onClick={() => openChat(userItem)}
          onKeyDown={e => e.key === 'Enter' && openChat(userItem)}
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 8,
            padding: '14px 8px',
            borderRadius: tokens.radiusSm,
            cursor: 'pointer',
            transition: 'background 0.2s, transform 0.15s',
          }}
          onMouseEnter={e => {
            e.currentTarget.style.background = 'rgba(102, 126, 234, 0.06)';
            e.currentTarget.style.transform = 'translateY(-1px)';
          }}
          onMouseLeave={e => {
            e.currentTarget.style.background = 'transparent';
            e.currentTarget.style.transform = 'none';
          }}
        >
          <Badge dot={active} offset={[-4, 4]} color="#52c41a">
            <Avatar
              size={42}
              style={{
                background: active ? tokens.gradientGreen : tokens.gradientPrimary,
                fontSize: 15,
                fontWeight: 600,
              }}
            >
              {getInitials(name)}
            </Avatar>
          </Badge>
          <Text
            style={{
              fontSize: 12,
              color: tokens.textPrimary,
              fontWeight: 500,
              maxWidth: 72,
              textAlign: 'center',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
            }}
          >
            {userItem.firstName}
          </Text>
        </div>
      </Tooltip>
    );
  };

  // ── Stat pill ──────────────────────────────────────────
  const StatPill = ({ value, label, color }) => (
    <div style={{ textAlign: 'center', flex: 1 }}>
      <div style={{ fontSize: 22, fontWeight: 700, color, lineHeight: 1.2 }}>{value}</div>
      <div style={{ fontSize: 12, color: tokens.textSecondary, fontWeight: 500, marginTop: 2 }}>
        {label}
      </div>
    </div>
  );

  // ═════════════════════════ RENDER ═════════════════════════
  return (
    <div style={{ direction: 'rtl' }}>
      {/* ── Page Header ──────────────────────────────────── */}
      <div
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
          <Title
            level={2}
            style={{
              margin: 0,
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              fontSize: 22,
              fontWeight: 700,
              color: tokens.textPrimary,
            }}
          >
            <MessageOutlined style={{ color: tokens.primary }} />
            הודעות
            {totalUnread > 0 && (
              <Badge
                count={totalUnread}
                style={{
                  background: tokens.primary,
                  boxShadow: 'none',
                  fontWeight: 600,
                  fontSize: 12,
                }}
              />
            )}
          </Title>
          <Text style={{ color: tokens.textSecondary, fontSize: 14 }}>
            שלח הודעות למשתמשים וצפה בשיחות
          </Text>
        </div>
        <Button
          icon={<ReloadOutlined />}
          onClick={loadData}
          loading={loading}
          style={{ borderRadius: tokens.radiusSm }}
        >
          רענן
        </Button>
      </div>

      {/* ── Content ──────────────────────────────────────── */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: 80 }}>
          <Spin size="large" />
        </div>
      ) : (
        <Row gutter={[20, 20]}>
          {/* ── Conversations List ────────────────────────── */}
          <Col xs={24} lg={16}>
            <Card
              title={
                <span style={{ fontSize: 15, fontWeight: 600, color: tokens.textPrimary }}>
                  <MessageOutlined style={{ color: tokens.primary, marginLeft: 8 }} />
                  שיחות ({conversations.length})
                </span>
              }
              extra={
                <Input
                  placeholder="חפש משתמש..."
                  prefix={<SearchOutlined style={{ color: tokens.textSecondary }} />}
                  value={searchText}
                  onChange={e => setSearchText(e.target.value)}
                  style={{ width: 200, borderRadius: tokens.radiusSm }}
                  allowClear
                />
              }
              styles={{
                header: {
                  borderBottom: `1px solid ${tokens.surfaceBorder}`,
                  padding: '14px 20px',
                },
                body: {
                  padding: 0,
                  maxHeight: 'calc(100vh - 280px)',
                  overflowY: 'auto',
                },
              }}
              style={{ borderRadius: tokens.radius, border: `1px solid ${tokens.surfaceBorder}` }}
            >
              {filteredConversations.length === 0 ? (
                <Empty
                  description="אין שיחות"
                  image={Empty.PRESENTED_IMAGE_SIMPLE}
                  style={{ padding: '48px 0' }}
                />
              ) : (
                filteredConversations.map(conv => (
                  <ConversationCard key={conv.userId} conv={conv} />
                ))
              )}
            </Card>
          </Col>

          {/* ── Sidebar ──────────────────────────────────── */}
          <Col xs={24} lg={8}>
            {/* Quick access */}
            <Card
              title={
                <span style={{ fontSize: 15, fontWeight: 600, color: tokens.textPrimary }}>
                  <UserOutlined style={{ color: tokens.primary, marginLeft: 8 }} />
                  שלח הודעה חדשה
                </span>
              }
              styles={{
                header: {
                  borderBottom: `1px solid ${tokens.surfaceBorder}`,
                  padding: '14px 20px',
                },
                body: { padding: 12 },
              }}
              style={{ borderRadius: tokens.radius, border: `1px solid ${tokens.surfaceBorder}` }}
            >
              {usersWithoutMessages.length === 0 && conversations.length === 0 ? (
                <Empty description="אין משתמשים" image={Empty.PRESENTED_IMAGE_SIMPLE} />
              ) : (
                <Row gutter={[4, 4]}>
                  {users.slice(0, 12).map(userItem => (
                    <Col key={userItem.uid} span={8}>
                      <UserQuickCard userItem={userItem} />
                    </Col>
                  ))}
                </Row>
              )}
            </Card>

            {/* Stats */}
            <Card
              style={{
                marginTop: 16,
                borderRadius: tokens.radius,
                border: `1px solid ${tokens.surfaceBorder}`,
              }}
              styles={{ body: { padding: '20px 16px' } }}
            >
              <div style={{ display: 'flex', gap: 8 }}>
                <StatPill value={messages.length} label="סך הכל" color={tokens.primary} />
                <div
                  style={{ width: 1, background: tokens.surfaceBorder, alignSelf: 'stretch' }}
                />
                <StatPill value={totalUnread} label="לא נקראו" color="#faad14" />
                <div
                  style={{ width: 1, background: tokens.surfaceBorder, alignSelf: 'stretch' }}
                />
                <StatPill value={conversations.length} label="שיחות" color="#52c41a" />
              </div>
            </Card>
          </Col>
        </Row>
      )}

      {/* ═══════════════ Chat Drawer ═══════════════════════ */}
      <Drawer
        title={
          selectedUser && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <Badge
                dot={isUserActive(selectedUser.lastSeen)}
                offset={[-4, 4]}
                color="#52c41a"
              >
                <Avatar
                  size={40}
                  style={{
                    background: isUserActive(selectedUser.lastSeen)
                      ? tokens.gradientGreen
                      : tokens.gradientPrimary,
                    fontSize: 15,
                    fontWeight: 600,
                  }}
                >
                  {getInitials(`${selectedUser.firstName} ${selectedUser.lastName}`)}
                </Avatar>
              </Badge>
              <div>
                <div
                  style={{
                    fontSize: 15,
                    fontWeight: 600,
                    color: tokens.textPrimary,
                    lineHeight: 1.3,
                  }}
                >
                  {selectedUser.firstName} {selectedUser.lastName}
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <Text style={{ fontSize: 12, color: tokens.textSecondary }}>
                    {selectedUser.phoneNumber}
                  </Text>
                  {isUserActive(selectedUser.lastSeen) && (
                    <Tag
                      color="green"
                      style={{
                        borderRadius: 10,
                        fontSize: 11,
                        lineHeight: '18px',
                        padding: '0 8px',
                        margin: 0,
                      }}
                    >
                      פעיל
                    </Tag>
                  )}
                </div>
              </div>
            </div>
          )
        }
        placement="left"
        width={Math.min(460, window.innerWidth - 20)}
        onClose={() => {
          setChatVisible(false);
          setSelectedUser(null);
          setUserMessages([]);
        }}
        open={chatVisible}
        styles={{
          header: {
            borderBottom: `1px solid ${tokens.surfaceBorder}`,
            padding: '16px 20px',
          },
          body: {
            padding: 0,
            display: 'flex',
            flexDirection: 'column',
            height: 'calc(100% - 55px)',
          },
        }}
      >
        {/* ── Messages Area ──────────────────────────────── */}
        <div
          style={{
            flex: 1,
            overflowY: 'auto',
            padding: '20px 18px',
            background: tokens.chatBg,
          }}
        >
          {loadingChat ? (
            <div style={{ textAlign: 'center', padding: 48 }}>
              <Spin />
            </div>
          ) : userMessages.length === 0 ? (
            <Empty
              description="אין הודעות עדיין"
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              style={{ marginTop: 48 }}
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
                      <div
                        style={{
                          textAlign: 'center',
                          margin: '20px 0 16px',
                        }}
                      >
                        <span
                          style={{
                            display: 'inline-block',
                            fontSize: 11,
                            fontWeight: 500,
                            color: tokens.textSecondary,
                            background: 'rgba(0,0,0,0.04)',
                            padding: '4px 14px',
                            borderRadius: 12,
                          }}
                        >
                          {dayjs(msg.timestamp).format('DD MMMM YYYY')}
                        </span>
                      </div>
                    )}

                    {/* Message bubble */}
                    <div
                      style={{
                        display: 'flex',
                        justifyContent: 'flex-start',
                        marginBottom: 10,
                      }}
                    >
                      <div
                        style={{
                          maxWidth: '78%',
                          background: tokens.gradientPrimary,
                          color: '#fff',
                          padding: '11px 16px',
                          borderRadius: '18px 18px 6px 18px',
                          boxShadow: '0 2px 12px rgba(102, 126, 234, 0.2)',
                        }}
                      >
                        <div
                          style={{
                            fontSize: 14,
                            lineHeight: 1.6,
                            fontWeight: 400,
                            letterSpacing: '0.01em',
                          }}
                        >
                          {msg.message}
                        </div>
                        <div
                          style={{
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'flex-end',
                            gap: 5,
                            marginTop: 5,
                            fontSize: 10,
                            opacity: 0.75,
                          }}
                        >
                          <span>{dayjs(msg.timestamp).format('HH:mm')}</span>
                          {msg.read ? (
                            <CheckCircleOutlined style={{ fontSize: 11, color: '#a3f0b5' }} />
                          ) : (
                            <ClockCircleOutlined style={{ fontSize: 11 }} />
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

        {/* ── Message Input ──────────────────────────────── */}
        <div
          style={{
            padding: '12px 16px',
            borderTop: `1px solid ${tokens.surfaceBorder}`,
            background: '#fff',
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'flex-end',
              gap: 10,
              background: '#f7f8fa',
              borderRadius: 22,
              padding: '6px 6px 6px 16px',
              border: '1px solid #e8eaed',
              transition: 'border-color 0.2s',
            }}
          >
            <TextArea
              value={newMessage}
              onChange={e => setNewMessage(e.target.value)}
              placeholder="הקלד הודעה..."
              autoSize={{ minRows: 1, maxRows: 4 }}
              onPressEnter={e => {
                if (!e.shiftKey) {
                  e.preventDefault();
                  handleSendMessage();
                }
              }}
              variant="borderless"
              style={{
                flex: 1,
                resize: 'none',
                fontSize: 14,
                background: 'transparent',
                padding: '4px 0',
              }}
            />
            <Button
              type="primary"
              shape="circle"
              icon={<SendOutlined style={{ fontSize: 16 }} />}
              onClick={handleSendMessage}
              loading={sending}
              disabled={!newMessage.trim()}
              size="middle"
              style={{
                width: 36,
                height: 36,
                minWidth: 36,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                background: newMessage.trim() ? tokens.primary : '#d9d9d9',
                border: 'none',
                boxShadow: newMessage.trim()
                  ? '0 2px 8px rgba(102, 126, 234, 0.3)'
                  : 'none',
                transition: 'all 0.2s',
                flexShrink: 0,
              }}
            />
          </div>
        </div>
      </Drawer>
    </div>
  );
};

export default MessagesPage;
