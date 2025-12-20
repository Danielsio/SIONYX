import { Component } from 'react';
import { Result, Button, Typography, Card } from 'antd';
import { ReloadOutlined, HomeOutlined, BugOutlined } from '@ant-design/icons';

const { Text, Paragraph } = Typography;

/**
 * Global Error Boundary Component
 * Catches JavaScript errors anywhere in the child component tree and displays a fallback UI
 */
class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error) {
    // Update state so the next render will show the fallback UI
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    // Log error to console for debugging
    console.error('Error Boundary caught an error:', error, errorInfo);
    
    this.setState({
      error,
      errorInfo,
    });

    // You can also log the error to an error reporting service here
    // logErrorToService(error, errorInfo);
  }

  handleReload = () => {
    window.location.reload();
  };

  handleGoHome = () => {
    window.location.href = '/admin';
  };

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  render() {
    if (this.state.hasError) {
      const isDev = import.meta.env.DEV;

      return (
        <div
          style={{
            minHeight: '100vh',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: '#f0f2f5',
            padding: '24px',
            direction: 'rtl',
          }}
        >
          <Card
            style={{
              maxWidth: 600,
              width: '100%',
              textAlign: 'center',
              boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
            }}
          >
            <Result
              status='error'
              title='אופס! משהו השתבש'
              subTitle='אירעה שגיאה בלתי צפויה. אנא נסה לרענן את העמוד או לחזור לדף הבית.'
              extra={[
                <Button
                  key='reload'
                  type='primary'
                  icon={<ReloadOutlined />}
                  onClick={this.handleReload}
                  size='large'
                >
                  רענן עמוד
                </Button>,
                <Button
                  key='home'
                  icon={<HomeOutlined />}
                  onClick={this.handleGoHome}
                  size='large'
                >
                  חזור לדף הבית
                </Button>,
              ]}
            />

            {/* Show error details in development mode */}
            {isDev && this.state.error && (
              <div style={{ marginTop: 24, textAlign: 'right' }}>
                <Card
                  size='small'
                  title={
                    <Text type='danger'>
                      <BugOutlined /> פרטי השגיאה (מצב פיתוח)
                    </Text>
                  }
                  style={{ background: '#fff2f0', border: '1px solid #ffccc7' }}
                >
                  <Paragraph
                    code
                    copyable
                    style={{
                      fontSize: 12,
                      maxHeight: 200,
                      overflow: 'auto',
                      whiteSpace: 'pre-wrap',
                      textAlign: 'left',
                      direction: 'ltr',
                    }}
                  >
                    {this.state.error.toString()}
                    {this.state.errorInfo?.componentStack}
                  </Paragraph>
                </Card>
              </div>
            )}
          </Card>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;



