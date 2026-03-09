import { useEffect, useState } from 'react';
import {
  Card,
  Row,
  Col,
  Typography,
  Select,
  Input,
  Button,
  List,
  Tag,
  Empty,
  Spin,
  App,
  Badge,
  Space,
  theme,
} from 'antd';
import {
  SendOutlined,
  MessageOutlined,
  UserOutlined,
  BankOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import 'dayjs/locale/he';
import { getSupervisorOrgs, getOrgUsers } from '../services/supervisorOrgService';
import { getOrgMessages, sendSupervisorMessage } from '../services/supervisorMessageService';
import { useSupervisorAuthStore } from '../store/supervisorAuthStore';
import { getAuth } from 'firebase/auth';

dayjs.extend(relativeTime);
dayjs.locale('he');

const { Title, Text } = Typography;
const { TextArea } = Input;

const SupervisorMessagesPage = () => {
  const [orgs, setOrgs] = useState([]);
  const [selectedOrgId, setSelectedOrgId] = useState(null);
  const [users, setUsers] = useState([]);
  const [messages, setMessages] = useState([]);
  const [selectedUserId, setSelectedUserId] = useState(null);
  const [newMessage, setNewMessage] = useState('');
  const [loading, setLoading] = useState(true);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [sending, setSending] = useState(false);
  const { message: antMsg } = App.useApp();
  const { token } = theme.useToken();
  const supervisor = useSupervisorAuthStore(s => s.supervisor);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      const res = await getSupervisorOrgs();
      if (res.success) {
        const orgList = res.organizations || [];
        setOrgs(orgList);
        if (orgList.length === 1) setSelectedOrgId(orgList[0].orgId);
      }
      setLoading(false);
    };
    load();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!selectedOrgId) return;
    const load = async () => {
      setLoadingMessages(true);
      const [usersRes, msgsRes] = await Promise.all([
        getOrgUsers(selectedOrgId),
        getOrgMessages(selectedOrgId),
      ]);
      if (usersRes.success) setUsers(usersRes.users || []);
      if (msgsRes.success) setMessages(msgsRes.messages || []);
      setLoadingMessages(false);
    };
    load();
  }, [selectedOrgId]);

  const handleSend = async () => {
    if (!selectedOrgId || !selectedUserId || !newMessage.trim()) return;
    setSending(true);
    const auth = getAuth();
    const uid = auth.currentUser?.uid;
    const res = await sendSupervisorMessage(selectedOrgId, selectedUserId, newMessage, uid);
    if (res.success) {
      antMsg.success('ההודעה נשלחה');
      setNewMessage('');
      const msgsRes = await getOrgMessages(selectedOrgId);
      if (msgsRes.success) setMessages(msgsRes.messages || []);
    } else {
      antMsg.error(res.error || 'שגיאה בשליחה');
    }
    setSending(false);
  };

  const getUserName = userId => {
    const u = users.find(u => u.uid === userId);
    if (!u) return userId;
    return `${(u.firstName || '').trim()} ${(u.lastName || '').trim()}`.trim() || u.phone || userId;
  };

  const filteredMessages = selectedUserId
    ? messages.filter(m => m.toUserId === selectedUserId)
    : messages;

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: 80 }}>
        <Spin size='large' />
      </div>
    );
  }

  return (
    <div style={{ direction: 'rtl', maxWidth: 960, margin: '0 auto' }}>
      <Title level={3} style={{ marginBottom: 24 }}>
        <MessageOutlined style={{ marginLeft: 8 }} />
        הודעות
      </Title>

      <Row gutter={[12, 12]} style={{ marginBottom: 20 }}>
        <Col xs={24} sm={12}>
          <Select
            placeholder='בחר ארגון'
            value={selectedOrgId}
            onChange={val => { setSelectedOrgId(val); setSelectedUserId(null); }}
            style={{ width: '100%' }}
            suffixIcon={<BankOutlined />}
            options={orgs.map(o => ({ value: o.orgId, label: o.name || o.orgId }))}
          />
        </Col>
        <Col xs={24} sm={12}>
          <Select
            placeholder='סנן לפי משתמש'
            value={selectedUserId}
            onChange={setSelectedUserId}
            allowClear
            showSearch
            optionFilterProp='label'
            style={{ width: '100%' }}
            suffixIcon={<UserOutlined />}
            disabled={!selectedOrgId}
            options={users.map(u => ({
              value: u.uid,
              label: `${(u.firstName || '').trim()} ${(u.lastName || '').trim()}`.trim() || u.phone || u.uid,
            }))}
          />
        </Col>
      </Row>

      {selectedOrgId && (
        <Card
          size='small'
          title='שלח הודעה חדשה'
          style={{ marginBottom: 20 }}
          styles={{ body: { padding: 16 } }}
        >
          <Space.Compact style={{ width: '100%' }}>
            <Select
              placeholder='בחר נמען'
              value={selectedUserId}
              onChange={setSelectedUserId}
              showSearch
              optionFilterProp='label'
              style={{ width: '40%' }}
              options={users.map(u => ({
                value: u.uid,
                label: `${(u.firstName || '').trim()} ${(u.lastName || '').trim()}`.trim() || u.phone || u.uid,
              }))}
            />
            <TextArea
              value={newMessage}
              onChange={e => setNewMessage(e.target.value)}
              placeholder='הקלד הודעה...'
              autoSize={{ minRows: 1, maxRows: 3 }}
              disabled={!selectedUserId}
              style={{ width: '50%' }}
              onPressEnter={e => {
                if (!e.shiftKey) { e.preventDefault(); handleSend(); }
              }}
            />
            <Button
              type='primary'
              icon={<SendOutlined />}
              loading={sending}
              disabled={!selectedUserId || !newMessage.trim()}
              onClick={handleSend}
              style={{ width: '10%', minWidth: 48 }}
            />
          </Space.Compact>
        </Card>
      )}

      <Card
        size='small'
        title={
          <Space>
            <ClockCircleOutlined />
            <span>היסטוריית הודעות</span>
            <Badge count={filteredMessages.length} style={{ backgroundColor: token.colorPrimary }} />
          </Space>
        }
        styles={{ body: { padding: 0 } }}
      >
        {loadingMessages ? (
          <div style={{ padding: 40, textAlign: 'center' }}><Spin /></div>
        ) : filteredMessages.length === 0 ? (
          <Empty
            description={selectedOrgId ? 'אין הודעות' : 'בחר ארגון להצגת הודעות'}
            style={{ padding: 40 }}
          />
        ) : (
          <List
            dataSource={filteredMessages}
            renderItem={msg => (
              <List.Item
                style={{ padding: '12px 16px', borderBottom: `1px solid ${token.colorBorderSecondary}` }}
              >
                <div style={{ width: '100%' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                    <Space size={4}>
                      <UserOutlined style={{ color: token.colorTextTertiary }} />
                      <Text strong style={{ fontSize: 13 }}>
                        {getUserName(msg.toUserId)}
                      </Text>
                      {msg.fromSupervisor && (
                        <Tag color='blue' style={{ fontSize: 10, lineHeight: '16px', padding: '0 4px' }}>מפקח</Tag>
                      )}
                    </Space>
                    <Space size={8}>
                      {msg.read ? (
                        <CheckCircleOutlined style={{ color: token.colorSuccess, fontSize: 12 }} />
                      ) : (
                        <Badge status='processing' />
                      )}
                      <Text type='secondary' style={{ fontSize: 11 }}>
                        {dayjs(msg.timestamp).fromNow()}
                      </Text>
                    </Space>
                  </div>
                  <Text style={{ fontSize: 13 }}>{msg.message}</Text>
                </div>
              </List.Item>
            )}
          />
        )}
      </Card>
    </div>
  );
};

export default SupervisorMessagesPage;
