import React, { useState, useEffect } from 'react';
import { Row, Col, Card, Typography, Space, Alert, Button, Divider } from 'antd';
import { 
  DownloadOutlined, 
  InfoCircleOutlined, 
  SafetyOutlined,
  RocketOutlined,
  CheckCircleOutlined
} from '@ant-design/icons';
import DownloadButton from '../components/DownloadButton';

const { Title, Paragraph, Text } = Typography;

/**
 * Download Page Component
 * ======================
 * Main download page for SIONYX application
 */
const DownloadPage = () => {
  const [downloadStats, setDownloadStats] = useState({
    totalDownloads: 0,
    lastDownload: null
  });

  useEffect(() => {
    // Load download statistics (you can implement this)
    loadDownloadStats();
  }, []);

  const loadDownloadStats = async () => {
    try {
      // This would typically fetch from your database
      // For now, we'll use mock data
      setDownloadStats({
        totalDownloads: 1234,
        lastDownload: new Date().toISOString()
      });
    } catch (error) {
      console.error('Failed to load download stats:', error);
    }
  };

  const handleDownloadStart = (releaseInfo) => {
    console.log('Download started:', releaseInfo);
    // You can track download events here
  };

  const handleDownloadComplete = (releaseInfo) => {
    console.log('Download completed:', releaseInfo);
    // Update download statistics
    setDownloadStats(prev => ({
      ...prev,
      totalDownloads: prev.totalDownloads + 1,
      lastDownload: new Date().toISOString()
    }));
  };

  const handleDownloadError = (error) => {
    console.error('Download error:', error);
    // Handle download errors
  };

  return (
    <div style={{ padding: '24px', maxWidth: 1200, margin: '0 auto' }}>
      {/* Header */}
      <div style={{ textAlign: 'center', marginBottom: '48px' }}>
        <Title level={1} style={{ color: '#1890ff', marginBottom: '16px' }}>
          <RocketOutlined style={{ marginRight: '12px' }} />
          Download SIONYX
        </Title>
        <Paragraph style={{ fontSize: '18px', color: '#666', maxWidth: 600, margin: '0 auto' }}>
          Get the latest version of SIONYX desktop application. 
          Easy installation with automatic setup wizard.
        </Paragraph>
      </div>

      <Row gutter={[24, 24]}>
        {/* Main Download Card */}
        <Col xs={24} lg={12}>
          <DownloadButton
            showDetails={true}
            size="large"
            type="primary"
            onDownloadStart={handleDownloadStart}
            onDownloadComplete={handleDownloadComplete}
            onDownloadError={handleDownloadError}
          />
        </Col>

        {/* Features and Info */}
        <Col xs={24} lg={12}>
          <Space direction="vertical" size="large" style={{ width: '100%' }}>
            {/* Features */}
            <Card title="What's Included" size="small">
              <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                <div>
                  <CheckCircleOutlined style={{ color: '#52c41a', marginRight: '8px' }} />
                  <Text strong>Standalone Executable</Text>
                  <br />
                  <Text type="secondary" style={{ marginLeft: '24px' }}>
                    No Python installation required
                  </Text>
                </div>
                
                <div>
                  <CheckCircleOutlined style={{ color: '#52c41a', marginRight: '8px' }} />
                  <Text strong>Setup Wizard</Text>
                  <br />
                  <Text type="secondary" style={{ marginLeft: '24px' }}>
                    Easy first-time configuration
                  </Text>
                </div>
                
                <div>
                  <CheckCircleOutlined style={{ color: '#52c41a', marginRight: '8px' }} />
                  <Text strong>Firebase Integration</Text>
                  <br />
                  <Text type="secondary" style={{ marginLeft: '24px' }}>
                    Automatic organization setup
                  </Text>
                </div>
                
                <div>
                  <CheckCircleOutlined style={{ color: '#52c41a', marginRight: '8px' }} />
                  <Text strong>Payment Gateway</Text>
                  <br />
                  <Text type="secondary" style={{ marginLeft: '24px' }}>
                    Pre-configured Nedarim Plus integration
                  </Text>
                </div>
              </Space>
            </Card>

            {/* System Requirements */}
            <Card title="System Requirements" size="small">
              <Space direction="vertical" size="small" style={{ width: '100%' }}>
                <div>
                  <Text strong>Operating System:</Text> Windows 10/11 (64-bit)
                </div>
                <div>
                  <Text strong>Memory:</Text> 4GB RAM minimum
                </div>
                <div>
                  <Text strong>Storage:</Text> 100MB free space
                </div>
                <div>
                  <Text strong>Network:</Text> Internet connection required
                </div>
              </Space>
            </Card>
          </Space>
        </Col>
      </Row>

      <Divider style={{ margin: '48px 0' }} />

      {/* Installation Instructions */}
      <Row gutter={[24, 24]}>
        <Col xs={24} lg={12}>
          <Card title="Installation Instructions" size="small">
            <Space direction="vertical" size="middle" style={{ width: '100%' }}>
              <div>
                <Text strong>1.</Text> Download the SIONYX installer
              </div>
              <div>
                <Text strong>2.</Text> Run the installer as Administrator
              </div>
              <div>
                <Text strong>3.</Text> Follow the installation wizard
              </div>
              <div>
                <Text strong>4.</Text> Complete the first-time setup
              </div>
              <div>
                <Text strong>5.</Text> Start using SIONYX!
              </div>
            </Space>
          </Card>
        </Col>

        <Col xs={24} lg={12}>
          <Card title="First-Time Setup" size="small">
            <Space direction="vertical" size="middle" style={{ width: '100%' }}>
              <div>
                <InfoCircleOutlined style={{ color: '#1890ff', marginRight: '8px' }} />
                <Text strong>Organization ID</Text>
                <br />
                <Text type="secondary" style={{ marginLeft: '24px' }}>
                  Unique identifier for your organization
                </Text>
              </div>
              
              <div>
                <InfoCircleOutlined style={{ color: '#1890ff', marginRight: '8px' }} />
                <Text strong>Firebase Credentials</Text>
                <br />
                <Text type="secondary" style={{ marginLeft: '24px' }}>
                  Your Firebase project configuration
                </Text>
              </div>
              
              <div>
                <InfoCircleOutlined style={{ color: '#1890ff', marginRight: '8px' }} />
                <Text strong>Payment Gateway</Text>
                <br />
                <Text type="secondary" style={{ marginLeft: '24px' }}>
                  Optional Nedarim Plus configuration
                </Text>
              </div>
            </Space>
          </Card>
        </Col>
      </Row>

      {/* Security Notice */}
      <Alert
        message="Security Notice"
        description={
          <div>
            <Text>
              SIONYX is downloaded from Firebase Storage and is digitally signed. 
              The application includes a built-in setup wizard that will guide you 
              through the configuration process securely.
            </Text>
            <br />
            <br />
            <Text strong>Note:</Text> Make sure to download SIONYX only from this official source.
          </div>
        }
        type="info"
        icon={<SafetyOutlined />}
        style={{ marginTop: '32px' }}
      />

      {/* Download Statistics */}
      {downloadStats.totalDownloads > 0 && (
        <Card 
          title="Download Statistics" 
          size="small" 
          style={{ marginTop: '24px', textAlign: 'center' }}
        >
          <Space size="large">
            <div>
              <Text strong style={{ fontSize: '24px', color: '#1890ff' }}>
                {downloadStats.totalDownloads.toLocaleString()}
              </Text>
              <br />
              <Text type="secondary">Total Downloads</Text>
            </div>
            <div>
              <Text strong style={{ fontSize: '24px', color: '#52c41a' }}>
                {downloadStats.lastDownload ? 'Latest' : 'N/A'}
              </Text>
              <br />
              <Text type="secondary">Release</Text>
            </div>
          </Space>
        </Card>
      )}
    </div>
  );
};

export default DownloadPage;
