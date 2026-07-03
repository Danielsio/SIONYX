import { Modal, Space, Form, Input, Button } from 'antd';
import { MessageOutlined, SendOutlined } from '@ant-design/icons';

/** Sends to one user, or to `bulkCount` filtered users when in bulk mode. */
const SendMessageModal = ({ open, onCancel, onFinish, form, sending, bulkCount, targetName }) => (
  <Modal
    title={
      <Space>
        <MessageOutlined />
        <span>
          {bulkCount != null
            ? `שלח הודעה ל-${bulkCount} משתמשים מסוננים`
            : `שלח הודעה ${targetName ? `ל${targetName}` : ''}`}
        </span>
      </Space>
    }
    open={open}
    onCancel={onCancel}
    footer={null}
    width={500}
    dir='rtl'
  >
    <Form form={form} layout='vertical' onFinish={onFinish} dir='rtl'>
      <Form.Item
        name='message'
        label='הודעה'
        rules={[
          { required: true, message: 'אנא הכנס הודעה' },
          { max: 500, message: 'ההודעה חייבת להיות פחות מ-500 תווים' },
        ]}
      >
        <Input.TextArea
          rows={4}
          placeholder='הכנס את ההודעה שלך כאן...'
          showCount
          maxLength={500}
          style={{ textAlign: 'right', direction: 'rtl' }}
        />
      </Form.Item>

      <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
        <Space>
          <Button onClick={onCancel}>ביטול</Button>
          <Button type='primary' htmlType='submit' icon={<SendOutlined />} loading={sending}>
            שלח הודעה
          </Button>
        </Space>
      </Form.Item>
    </Form>
  </Modal>
);

export default SendMessageModal;
