import { Navigate } from 'react-router-dom';
import { Spin } from 'antd';
import { useSupervisorAuthStore } from './store/supervisorAuthStore';

const SupervisorProtectedRoute = ({ children }) => {
  const isAuthenticated = useSupervisorAuthStore(state => state.isAuthenticated);
  const isLoading = useSupervisorAuthStore(state => state.isLoading);

  if (isLoading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh' }}>
        <Spin size='large' />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to='/supervisor/login' replace />;
  }

  return children;
};

export default SupervisorProtectedRoute;
