import { useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { Result, Spin, Alert, Button } from 'antd';
import { CallbackService } from '../services/callbackService';

/**
 * Nedarim Callback Component
 * Secret endpoint for handling Nedarim Plus payment callbacks
 * This replaces the Firebase function with a React-based solution
 * 
 * Note: This component handles both GET and POST requests:
 * - GET: Data comes via URL parameters
 * - POST: Data should be sent as JSON in request body (handled by server-side proxy)
 */
const NedarimCallback = () => {
  const location = useLocation();
  const [status, setStatus] = useState('processing'); // processing, success, error
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [paymentData, setPaymentData] = useState(null);

  useEffect(() => {
    const processCallback = async () => {
      try {
        // Get payment data from URL search params
        const urlParams = new URLSearchParams(location.search);
        const data = {};

        // Extract data from URL parameters
        for (const [key, value] of urlParams.entries()) {
          data[key] = value;
        }

        // Check if we have any data
        if (Object.keys(data).length === 0) {
          setStatus('error');
          setError('No payment data received. This endpoint expects payment data via URL parameters.');
          return;
        }

        setPaymentData(data);

        // Validate the callback request
        if (!CallbackService.validateCallbackRequest(data)) {
          setStatus('error');
          setError('Invalid payment data received. Missing required fields: TransactionId, Status');
          return;
        }

        console.log('Processing Nedarim callback with data:', data);

        // Process the callback
        const result = await CallbackService.processCallback(data);

        if (result.success) {
          setStatus('success');
          setMessage(result.message);
        } else {
          setStatus('error');
          setError(result.error);
        }
      } catch (err) {
        console.error('Callback processing error:', err);
        setStatus('error');
        setError(err.message || 'An unexpected error occurred while processing the payment callback');
      }
    };

    processCallback();
  }, [location.search]);

  const renderContent = () => {
    switch (status) {
      case 'processing':
        return (
          <div style={{ textAlign: 'center', padding: '50px' }}>
            <Spin size="large" />
            <p style={{ marginTop: '20px', fontSize: '16px' }}>
              Processing payment callback...
            </p>
          </div>
        );

      case 'success':
        return (
          <Result
            status="success"
            title="Payment Processed Successfully"
            subTitle={message}
            extra={[
              <Alert
                key="info"
                message="Callback processed successfully"
                description="The payment has been processed and the user account has been updated with the purchased credits."
                type="success"
                showIcon
                style={{ marginTop: '20px' }}
              />,
              paymentData && (
                <div key="details" style={{ marginTop: '20px', textAlign: 'left' }}>
                  <h4>Transaction Details:</h4>
                  <p><strong>Transaction ID:</strong> {paymentData.TransactionId}</p>
                  <p><strong>Status:</strong> {paymentData.Status}</p>
                  <p><strong>Amount:</strong> {paymentData.Amount}</p>
                  <p><strong>Purchase ID:</strong> {paymentData.Param1}</p>
                  <p><strong>Organization ID:</strong> {paymentData.Param2}</p>
                </div>
              )
            ]}
          />
        );

      case 'error':
        return (
          <Result
            status="error"
            title="Payment Processing Failed"
            subTitle={error}
            extra={[
              <Alert
                key="error"
                message="Callback processing failed"
                description="There was an error processing the payment callback. Please check the logs for more details."
                type="error"
                showIcon
                style={{ marginTop: '20px' }}
              />,
              paymentData && (
                <div key="details" style={{ marginTop: '20px', textAlign: 'left' }}>
                  <h4>Received Data:</h4>
                  <pre style={{ 
                    backgroundColor: '#f5f5f5', 
                    padding: '10px', 
                    borderRadius: '4px',
                    fontSize: '12px',
                    overflow: 'auto'
                  }}>
                    {JSON.stringify(paymentData, null, 2)}
                  </pre>
                </div>
              )
            ]}
          />
        );

      default:
        return null;
    }
  };

  return (
    <div style={{ 
      minHeight: '100vh', 
      display: 'flex', 
      alignItems: 'center', 
      justifyContent: 'center',
      backgroundColor: '#f5f5f5'
    }}>
      <div style={{ 
        maxWidth: '600px', 
        width: '100%', 
        padding: '20px',
        backgroundColor: 'white',
        borderRadius: '8px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
      }}>
        {renderContent()}
      </div>
    </div>
  );
};

export default NedarimCallback;
