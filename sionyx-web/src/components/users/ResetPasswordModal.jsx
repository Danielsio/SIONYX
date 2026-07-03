import { Modal, Space, Form, Input, Typography } from 'antd';
import { LockOutlined } from '@ant-design/icons';

const { Text } = Typography;

const ResetPasswordModal = ({ open, user, form, onOk, onCancel, confirmLoading }) => (
  <Modal
    title={
      <Space>
        <LockOutlined />
        <span>איפוס סיסמה {user && `ל${user.firstName} ${user.lastName}`}</span>
      </Space>
    }
    open={open}
    onOk={onOk}
    onCancel={onCancel}
    confirmLoading={confirmLoading}
    okText='אפס סיסמה'
    cancelText='ביטול'
    width={450}
    dir='rtl'
  >
    {user && (
      <Space direction='vertical' size='large' style={{ width: '100%' }}>
        <div
          style={{
            padding: '12px',
            backgroundColor: '#fff7e6',
            borderRadius: '8px',
            border: '1px solid #ffd591',
          }}
        >
          <Text>
            <strong>שים לב:</strong> הסיסמה החדשה תיכנס לתוקף מיד. וודא שאתה מעביר את הסיסמה החדשה
            למשתמש בצורה מאובטחת.
          </Text>
        </div>

        <Form form={form} layout='vertical' dir='rtl'>
          <Form.Item
            name='newPassword'
            label='סיסמה חדשה'
            rules={[
              { required: true, message: 'אנא הכנס סיסמה חדשה' },
              { min: 6, message: 'הסיסמה חייבת להכיל לפחות 6 תווים' },
            ]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder='לפחות 6 תווים' />
          </Form.Item>

          <Form.Item
            name='confirmPassword'
            label='אשר סיסמה'
            rules={[
              { required: true, message: 'אנא אשר את הסיסמה' },
              { min: 6, message: 'הסיסמה חייבת להכיל לפחות 6 תווים' },
            ]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder='הכנס שוב את הסיסמה' />
          </Form.Item>
        </Form>
      </Space>
    )}
  </Modal>
);

export default ResetPasswordModal;
