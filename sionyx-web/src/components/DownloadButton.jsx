import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { Button, Card, Spin, message, Progress, Typography, Space, Divider } from 'antd';
import { DownloadOutlined, InfoCircleOutlined, CheckCircleOutlined } from '@ant-design/icons';
import { 
  getLatestRelease, 
  downloadFile, 
  downloadFileWithProgress,
  formatFileSize, 
  formatReleaseDate 
} from '../services/downloadService';

const { Title, Text, Paragraph } = Typography;

/**
 * Download Button Component
 * ========================
 * A comprehensive download component for SIONYX executables
 */
const DownloadButton = ({ 
  showDetails = true, 
  size = 'large', 
  type = 'primary',
  onDownloadStart,
  onDownloadComplete,
  onDownloadError 
}) => {
  const [loading, setLoading] = useState(false);
  const [releaseInfo, setReleaseInfo] = useState(null);
  const [downloadProgress, setDownloadProgress] = useState(0);
  const [isDownloading, setIsDownloading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadReleaseInfo();
  }, []);

  const loadReleaseInfo = useCallback(async () => {
    try {
      setLoading(true);
      const info = await getLatestRelease();
      setReleaseInfo(info);
      setError(null);
    } catch (err) {
      console.error('Failed to load release info:', err);
      setError('Failed to load release information');
    } finally {
      setLoading(false);
    }
  }, []);

  const handleDownload = useCallback(async () => {
    if (!releaseInfo) return;

    try {
      setIsDownloading(true);
      setDownloadProgress(0);
      setError(null);

      if (onDownloadStart) {
        onDownloadStart(releaseInfo);
      }

      // Use progress tracking if file size is available
      if (releaseInfo.fileSize > 0) {
        await downloadFileWithProgress(
          releaseInfo.downloadUrl,
          releaseInfo.fileName,
          (loaded, total) => {
            const progress = (loaded / total) * 100;
            setDownloadProgress(progress);
          }
        );
      } else {
        await downloadFile(releaseInfo.downloadUrl, releaseInfo.fileName);
      }

      message.success('Download completed successfully!');
      
      if (onDownloadComplete) {
        onDownloadComplete(releaseInfo);
      }

    } catch (err) {
      console.error('Download failed:', err);
      const errorMessage = err.message || 'Download failed. Please try again.';
      setError(errorMessage);
      message.error(errorMessage);
      
      if (onDownloadError) {
        onDownloadError(err);
      }
    } finally {
      setIsDownloading(false);
      setDownloadProgress(0);
    }
  }, [releaseInfo, onDownloadStart, onDownloadComplete, onDownloadError]);

  const handleRetry = useCallback(() => {
    setError(null);
    loadReleaseInfo();
  }, [loadReleaseInfo]);

  // Memoize formatted values for better performance
  const formattedFileSize = useMemo(() => 
    releaseInfo ? formatFileSize(releaseInfo.fileSize) : '0 B', 
    [releaseInfo?.fileSize]
  );

  const formattedReleaseDate = useMemo(() => 
    releaseInfo ? formatReleaseDate(releaseInfo.releaseDate) : 'Unknown', 
    [releaseInfo?.releaseDate]
  );

  if (loading) {
    return (
      <Card style={{ textAlign: 'center', padding: '20px' }}>
        <Spin size="large" />
        <div style={{ marginTop: '16px' }}>
          <Text>Loading release information...</Text>
        </div>
      </Card>
    );
  }

  if (error && !releaseInfo) {
    return (
      <Card style={{ textAlign: 'center', padding: '20px' }}>
        <InfoCircleOutlined style={{ fontSize: '24px', color: '#ff4d4f', marginBottom: '16px' }} />
        <div style={{ marginBottom: '16px' }}>
          <Text type="danger">{error}</Text>
        </div>
        <Button onClick={handleRetry} type="primary">
          Retry
        </Button>
      </Card>
    );
  }

  if (!releaseInfo) {
    return null;
  }

  return (
    <Card 
      style={{ 
        maxWidth: 500, 
        margin: '0 auto',
        boxShadow: '0 4px 12px rgba(0,0,0,0.1)'
      }}
    >
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        {/* Header */}
        <div style={{ textAlign: 'center' }}>
          <Title level={3} style={{ margin: 0, color: '#1890ff' }}>
            Download SIONYX
          </Title>
          <Text type="secondary">
            Version {releaseInfo.version}
          </Text>
        </div>

        {/* Download Button */}
        <div style={{ textAlign: 'center' }}>
          <Button
            type={type}
            size={size}
            icon={<DownloadOutlined />}
            loading={isDownloading}
            onClick={handleDownload}
            disabled={isDownloading}
            style={{ 
              minWidth: 200,
              height: 50,
              fontSize: '16px',
              fontWeight: 'bold'
            }}
          >
            {isDownloading ? 'Downloading...' : 'Download Now'}
          </Button>
        </div>

        {/* Progress Bar */}
        {isDownloading && (
          <div>
            <Progress 
              percent={Math.round(downloadProgress)} 
              status="active"
              strokeColor={{
                '0%': '#108ee9',
                '100%': '#87d068',
              }}
            />
            <Text type="secondary" style={{ fontSize: '12px' }}>
              {Math.round(downloadProgress)}% complete
            </Text>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div style={{ textAlign: 'center' }}>
            <Text type="danger">{error}</Text>
            <br />
            <Button size="small" onClick={handleRetry} style={{ marginTop: '8px' }}>
              Try Again
            </Button>
          </div>
        )}

        {/* Release Details */}
        {showDetails && (
          <>
            <Divider style={{ margin: '16px 0' }} />
            <div>
              <Space direction="vertical" size="small" style={{ width: '100%' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Text strong>File Size:</Text>
                  <Text>{formattedFileSize}</Text>
                </div>
                
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Text strong>Release Date:</Text>
                  <Text>{formattedReleaseDate}</Text>
                </div>
                
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Text strong>File Name:</Text>
                  <Text code>{releaseInfo.fileName}</Text>
                </div>
              </Space>
            </div>
          </>
        )}

        {/* Instructions */}
        <div style={{ textAlign: 'center' }}>
          <Paragraph style={{ margin: 0, fontSize: '12px', color: '#666' }}>
            <CheckCircleOutlined style={{ color: '#52c41a', marginRight: '4px' }} />
            Safe download from Firebase Storage
          </Paragraph>
        </div>
      </Space>
    </Card>
  );
};

export default DownloadButton;
