import { useEffect, useState } from 'react';
import {
  Card,
  Form,
  InputNumber,
  Button,
  Space,
  Typography,
  Row,
  Col,
  Statistic,
  Divider,
  Alert,
  App,
} from 'antd';
import {
  PrinterOutlined,
  DollarOutlined,
  SaveOutlined,
  ReloadOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons';
import { useAuthStore } from '../store/authStore';
import { getPrintPricing, updatePrintPricing } from '../services/pricingService';

const { Title, Text } = Typography;

const PricingPage = () => {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [form] = Form.useForm();
  const [pricing, setPricing] = useState({
    blackAndWhitePrice: 1.0,
    colorPrice: 3.0,
  });

  const user = useAuthStore(state => state.user);
  const { message } = App.useApp();

  useEffect(() => {
    loadPricing();
  }, []);

  const loadPricing = async () => {
    setLoading(true);

    // Get orgId from authenticated user
    const orgId = user?.orgId || localStorage.getItem('adminOrgId');

    if (!orgId) {
      message.error('מזהה ארגון לא נמצא. אנא התחבר שוב.');
      setLoading(false);
      return;
    }

    console.log('Loading pricing for organization:', orgId);

    const result = await getPrintPricing(orgId);

    if (result.success) {
      setPricing(result.pricing);
      form.setFieldsValue({
        blackAndWhitePrice: result.pricing.blackAndWhitePrice,
        colorPrice: result.pricing.colorPrice,
      });
    } else {
      message.error(result.error || 'נכשל בטעינת המחירים');
      console.error('Failed to load pricing:', result.error);
    }

    setLoading(false);
  };

  const handleSave = async () => {
    try {
      const values = await form.validateFields();

      // Get orgId
      const orgId = user?.orgId || localStorage.getItem('adminOrgId');

      console.log('Current user:', user);
      console.log('OrgId from user:', user?.orgId);
      console.log('OrgId from localStorage:', localStorage.getItem('adminOrgId'));
      console.log('Final orgId:', orgId);

      if (!orgId) {
        message.error('מזהה ארגון לא נמצא. אנא התחבר שוב.');
        return;
      }

      setSaving(true);

      console.log('Attempting to update pricing with values:', values);
      const result = await updatePrintPricing(orgId, values);

      if (result.success) {
        message.success('מחירי ההדפסה עודכנו בהצלחה');
        setPricing(values);
      } else {
        message.error(result.error || 'נכשל בעדכון המחירים');
        console.error('Failed to update pricing:', result.error);
      }
    } catch (error) {
      console.error('Validation failed:', error);
    } finally {
      setSaving(false);
    }
  };

  const handleReset = () => {
    form.setFieldsValue({
      blackAndWhitePrice: pricing.blackAndWhitePrice,
      colorPrice: pricing.colorPrice,
    });
  };

  return (
    <App>
      <div style={{ direction: 'rtl' }}>
        <Space direction='vertical' size='large' style={{ width: '100%' }}>
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <Title level={2} style={{ marginBottom: 8 }}>
              מחירי הדפסה
            </Title>
            <Text type='secondary'>נהל את מחירי ההדפסה השחור-לבן והצבעוניות בארגון שלך</Text>
          </div>
          <Button icon={<ReloadOutlined />} onClick={loadPricing} loading={loading}>
            רענן
          </Button>
        </div>

        {/* Info Alert */}
        <Alert
          message="מידע חשוב"
          description="מחירי ההדפסה משפיעים על כל המשתמשים בארגון. שינויים יכנסו לתוקף מיד לאחר השמירה."
          type="info"
          icon={<InfoCircleOutlined />}
          showIcon
        />

        <Row gutter={[24, 24]}>
          {/* Current Pricing Overview */}
          <Col xs={24} lg={12}>
            <Card title="מחירים נוכחיים" extra={<DollarOutlined />}>
              <Space direction="vertical" size="large" style={{ width: '100%' }}>
                <Row gutter={16}>
                  <Col span={12}>
                    <Statistic
                      title="הדפסה שחור-לבן"
                      value={pricing.blackAndWhitePrice}
                      prefix="₪"
                      precision={2}
                      valueStyle={{ color: '#1890ff' }}
                    />
                  </Col>
                  <Col span={12}>
                    <Statistic
                      title="הדפסה צבעונית"
                      value={pricing.colorPrice}
                      prefix="₪"
                      precision={2}
                      valueStyle={{ color: '#52c41a' }}
                    />
                  </Col>
                </Row>
                <Divider />
                <div style={{ textAlign: 'center' }}>
                  <Text type="secondary">
                    יחס מחירים: {pricing.colorPrice / pricing.blackAndWhitePrice}x
                  </Text>
                </div>
              </Space>
            </Card>
          </Col>

          {/* Pricing Form */}
          <Col xs={24} lg={12}>
            <Card title="עדכן מחירים" extra={<PrinterOutlined />}>
              <Form
                form={form}
                layout="vertical"
                onFinish={handleSave}
                initialValues={{
                  blackAndWhitePrice: pricing.blackAndWhitePrice,
                  colorPrice: pricing.colorPrice,
                }}
              >
                <Form.Item
                  name="blackAndWhitePrice"
                  label="מחיר הדפסה שחור-לבן (₪)"
                  rules={[
                    { required: true, message: 'נא להזין מחיר הדפסה שחור-לבן' },
                    { type: 'number', min: 0.01, message: 'המחיר חייב להיות גדול מ-0' },
                  ]}
                >
                  <InputNumber
                    style={{ width: '100%' }}
                    precision={2}
                    placeholder="1.00"
                    prefix="₪"
                    min={0.01}
                    step={0.01}
                  />
                </Form.Item>

                <Form.Item
                  name="colorPrice"
                  label="מחיר הדפסה צבעונית (₪)"
                  rules={[
                    { required: true, message: 'נא להזין מחיר הדפסה צבעונית' },
                    { type: 'number', min: 0.01, message: 'המחיר חייב להיות גדול מ-0' },
                  ]}
                >
                  <InputNumber
                    style={{ width: '100%' }}
                    precision={2}
                    placeholder="3.00"
                    prefix="₪"
                    min={0.01}
                    step={0.01}
                  />
                </Form.Item>

                <Form.Item>
                  <Space>
                    <Button
                      type="primary"
                      htmlType="submit"
                      icon={<SaveOutlined />}
                      loading={saving}
                      disabled={loading}
                    >
                      שמור שינויים
                    </Button>
                    <Button onClick={handleReset} disabled={loading}>
                      איפוס
                    </Button>
                  </Space>
                </Form.Item>
              </Form>
            </Card>
          </Col>
        </Row>

        {/* Additional Information */}
        <Card title="מידע נוסף">
          <Row gutter={[16, 16]}>
            <Col xs={24} sm={12}>
              <div>
                <Text strong>איך זה עובד:</Text>
                <br />
                <Text type="secondary">
                  המחירים נשמרים במטא-דאטה של הארגון ומשפיעים על כל המשתמשים.
                  המחירים נמדדים בשקלים (₪) לכל עמוד מודפס.
                </Text>
              </div>
            </Col>
            <Col xs={24} sm={12}>
              <div>
                <Text strong>המלצות:</Text>
                <br />
                <Text type="secondary">
                  • מחיר הדפסה צבעונית בדרך כלל גבוה יותר מהדפסה שחור-לבן
                  <br />
                  • שקול את עלויות ההדפסה הפיזיות בעת קביעת המחירים
                  <br />
                  • עדכן את המשתמשים על שינויי מחירים
                </Text>
              </div>
            </Col>
          </Row>
        </Card>
        </Space>
      </div>
    </App>
  );
};

export default PricingPage;
