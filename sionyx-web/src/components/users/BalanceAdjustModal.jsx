import { Modal, Space, Form, InputNumber, Typography } from 'antd';
import { EditOutlined, ClockCircleOutlined, PrinterOutlined } from '@ant-design/icons';

const { Text } = Typography;

/** Absolute-value balance editor; the page computes the delta and calls the Worker. */
const BalanceAdjustModal = ({ open, user, form, onOk, onCancel, confirmLoading }) => (
  <Modal
    title={
      <Space>
        <EditOutlined />
        <span>התאם יתרה</span>
      </Space>
    }
    open={open}
    onOk={onOk}
    onCancel={onCancel}
    confirmLoading={confirmLoading}
    okText='עדכן'
    cancelText='ביטול'
    width={500}
  >
    {user && (
      <Space direction='vertical' size='large' style={{ width: '100%' }}>
        <div>
          <Text strong>משתמש: </Text>
          <Text>{`${user.firstName} ${user.lastName}`}</Text>
        </div>

        <Form form={form} layout='vertical'>
          <Form.Item
            name='minutes'
            label='יתרת זמן (דקות)'
            tooltip='ערוך את סך הדקות שהמשתמש צריך לקבל'
            rules={[
              { required: true, message: 'אנא הכנס זמן' },
              { type: 'number', min: 0, message: 'הזמן לא יכול להיות שלילי' },
            ]}
          >
            <InputNumber
              style={{ width: '100%' }}
              placeholder='למשל, 120 (שעתיים)'
              prefix={<ClockCircleOutlined />}
              min={0}
            />
          </Form.Item>

          <Form.Item
            name='prints'
            label='יתרת הדפסות (₪)'
            tooltip='ערוך את סך תקציב ההדפסות בשקלים שהמשתמש צריך לקבל'
            rules={[
              { required: true, message: 'אנא הכנס הדפסות' },
              { type: 'number', min: 0, message: 'הדפסות לא יכולות להיות שליליות' },
            ]}
          >
            <InputNumber
              style={{ width: '100%' }}
              placeholder='למשל, 50'
              prefix={<PrinterOutlined />}
              min={0}
            />
          </Form.Item>
        </Form>

        <div
          style={{
            padding: '8px',
            backgroundColor: '#e6f7ff',
            borderRadius: '4px',
            border: '1px solid #91d5ff',
          }}
        >
          <Text type='secondary' style={{ fontSize: '12px' }}>
            💡 טיפ: הערכים הנוכחיים מוצגים. ערוך אותם כדי לקבוע את היתרה החדשה. תוכל להגדיל, להקטין
            או לקבוע כל ערך.
          </Text>
        </div>
      </Space>
    )}
  </Modal>
);

export default BalanceAdjustModal;
