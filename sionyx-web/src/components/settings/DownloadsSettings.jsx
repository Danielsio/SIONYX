import { useEffect, useState } from 'react';
import { Card, Typography, Space, Button, Row, Col, Alert, Skeleton, App as AntApp } from 'antd';
import {
  CloudDownloadOutlined,
  InfoCircleOutlined,
  FileOutlined,
  NumberOutlined,
  CalendarOutlined,
  HddOutlined,
} from '@ant-design/icons';
import { getLatestRelease, downloadFile, formatFileSize, formatReleaseDate, formatVersion } from '../../services/downloadService';
import { useOrgId } from '../../hooks/useOrgId';

const { Title, Text } = Typography;

const useIsMobile = (breakpoint = 768) => {
  const [isMobile, setIsMobile] = useState(() => window.innerWidth < breakpoint);

  useEffect(() => {
    const mq = window.matchMedia(`(max-width: ${breakpoint - 1}px)`);
    const handler = e => setIsMobile(e.matches);
    mq.addEventListener('change', handler);
    return () => mq.removeEventListener('change', handler);
  }, [breakpoint]);

  return isMobile;
};

const DownloadsSettings = () => {
  const [releaseInfo, setReleaseInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState(false);
  const isMobile = useIsMobile();
  const { message } = AntApp.useApp();
  const orgId = useOrgId();

  const loadReleaseInfo = async () => {
    setLoading(true);
    try {
      const info = await getLatestRelease();
      setReleaseInfo(info);
    } catch (error) {
      message.error(error.message || 'נכשל בטעינת פרטי ההורדה');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReleaseInfo();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handleDownload = async () => {
    if (!releaseInfo?.downloadUrl) {
      message.error('לא נמצא קישור להורדה');
      return;
    }

    setDownloading(true);
    try {
      await downloadFile(releaseInfo.downloadUrl, releaseInfo.fileName);
      message.success('ההורדה החלה בהצלחה');
    } catch (error) {
      message.error(error.message || 'שגיאה בהורדה. נסה שוב.');
    } finally {
      setDownloading(false);
    }
  };

  return (
    <Space direction='vertical' size={isMobile ? 'middle' : 'large'} style={{ width: '100%' }}>
      <Alert
        message='הורדת תוכנת SIONYX'
        description={
          <span>
            כאן ניתן להוריד את הגרסה העדכנית של תוכנת ה-SIONYX להתקנה על מחשבי הארגון.
            {' '}
            בעתיד זמינות ההורדה תותנה בסטטוס התשלום של הארגון ({orgId || 'ללא מזהה ארגון'}).
          </span>
        }
        type='info'
        icon={<InfoCircleOutlined />}
        showIcon
        style={{ fontSize: isMobile ? 12 : undefined }}
      />

      <Row gutter={[isMobile ? 0 : 24, 16]}>
        <Col xs={24} lg={14}>
          <Card
            title={
              <Space>
                <CloudDownloadOutlined />
                <span>גרסה אחרונה להורדה</span>
              </Space>
            }
            styles={{ body: { padding: isMobile ? 16 : undefined } }}
            extra={
              <Button size='small' onClick={loadReleaseInfo} disabled={downloading} loading={loading}>
                רענן
              </Button>
            }
          >
            {loading ? (
              <Skeleton active paragraph={{ rows: 3 }} />
            ) : releaseInfo ? (
              <Space direction='vertical' size='small' style={{ width: '100%' }}>
                <Title level={isMobile ? 5 : 4} style={{ marginBottom: 8 }}>
                  {formatVersion(releaseInfo)}
                </Title>

                <Row gutter={[12, 12]}>
                  <Col xs={24} sm={12}>
                    <Space>
                      <FileOutlined />
                      <Text type='secondary'>קובץ:</Text>
                      <Text>{releaseInfo.fileName}</Text>
                    </Space>
                  </Col>
                  <Col xs={24} sm={12}>
                    <Space>
                      <HddOutlined />
                      <Text type='secondary'>גודל:</Text>
                      <Text>{formatFileSize(releaseInfo.fileSize)}</Text>
                    </Space>
                  </Col>
                  <Col xs={24} sm={12}>
                    <Space>
                      <CalendarOutlined />
                      <Text type='secondary'>תאריך שחרור:</Text>
                      <Text>{formatReleaseDate(releaseInfo.releaseDate)}</Text>
                    </Space>
                  </Col>
                  {releaseInfo.buildNumber && (
                    <Col xs={24} sm={12}>
                      <Space>
                        <NumberOutlined />
                        <Text type='secondary'>Build #</Text>
                        <Text>{releaseInfo.buildNumber}</Text>
                      </Space>
                    </Col>
                  )}
                </Row>

                {Array.isArray(releaseInfo.changelog) && releaseInfo.changelog.length > 0 && (
                  <div style={{ marginTop: 12 }}>
                    <Text strong>מה חדש בגרסה זו:</Text>
                    <ul style={{ paddingRight: 20, marginTop: 4, marginBottom: 0 }}>
                      {releaseInfo.changelog.map((item, index) => (
                        <li key={index}>
                          <Text type='secondary'>{item}</Text>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                <Button
                  type='primary'
                  icon={<CloudDownloadOutlined />}
                  onClick={handleDownload}
                  loading={downloading}
                  disabled={loading || !releaseInfo?.downloadUrl}
                  style={{ marginTop: 12 }}
                >
                  הורד תוכנה
                </Button>
              </Space>
            ) : (
              <Alert
                type='error'
                showIcon
                message='נכשל בטעינת פרטי הגרסה'
                description='אנא נסה שוב מאוחר יותר או פנה לתמיכה.'
              />
            )}
          </Card>
        </Col>

        <Col xs={24} lg={10}>
          <Card
            title='הנחיות להטמעה'
            styles={{ body: { padding: isMobile ? 16 : undefined } }}
          >
            <Space direction='vertical' size='small'>
              <Text>
                • התקן את התוכנה על כל מחשב בעמדות השימוש.
              </Text>
              <Text>
                • ודא חיבור אינטרנט פעיל בעת ההתקנה והרצה הראשונה.
              </Text>
              <Text>
                • התחבר עם פרטי המנהל של הארגון כדי לסנכרן את המחשבים עם הפאנל.
              </Text>
              <Text type='secondary' style={{ fontSize: isMobile ? 12 : undefined }}>
                בעתיד נוסיף אימות אוטומטי של סטטוס התשלום של הארגון לפני הפעלת התוכנה.
              </Text>
            </Space>
          </Card>
        </Col>
      </Row>
    </Space>
  );
};

export default DownloadsSettings;

